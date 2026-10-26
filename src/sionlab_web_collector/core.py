"""Sequential collection with transactionally durable page queues."""
from __future__ import annotations
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

class CollectorError(Exception):
    pass

class Blocked(CollectorError):
    pass

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def config_hash(config):
    return hashlib.sha256(canonical(config).encode()).hexdigest()

def validate_config(config):
    if not isinstance(config, dict):
        raise CollectorError('config must be an object')
    if urlsplit(config.get('start_url', '')).scheme not in ('http', 'https'):
        raise CollectorError('start_url must use http or https')
    if not config.get('item_selector') or not isinstance(config.get('fields'), dict) or not config['fields']:
        raise CollectorError('item_selector and fields are required')
    keys = config.get('unique_key', [])
    if isinstance(keys, str):
        keys = [keys]
    if not keys or any(k not in config['fields'] for k in keys):
        raise CollectorError('unique_key must name configured fields')
    for name, field in config['fields'].items():
        if not name or not isinstance(field, dict) or not field.get('selector'):
            raise CollectorError('each field requires a name and selector')
        if field.get('normalize', 'text') not in ('text', 'decimal', 'integer', 'json', 'url'):
            raise CollectorError('unsupported field normalization')
    for name, default in [('max_pages', 2), ('max_items', 50)]:
        if type(config.get(name, default)) is not int or config.get(name, default) < 1:
            raise CollectorError(name + ' must be a positive integer')
    if config.get('concurrency', 1) != 1 or not 0 < config.get('requests_per_second', 1) <= 1:
        raise CollectorError('concurrency must be 1 and requests_per_second in (0,1]')
    if config.get('adapter', 'http') not in ('http', 'playwright'):
        raise CollectorError('adapter must be http or playwright')
    # Compile selectors before starting a persisted job.
    import soupsieve
    try:
        for selector in [config['item_selector'], config.get('next_selector')] + [f['selector'] for f in config['fields'].values()]:
            if selector and selector != ':self':
                soupsieve.compile(selector)
    except Exception as exc:
        raise CollectorError('invalid CSS selector') from exc
    return config

@contextmanager
def job_lock(path):
    """An OS lock, released automatically even on abrupt process death."""
    import fcntl
    lock = Path(str(path) + '.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+b') as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CollectorError('job_busy: another process holds this job') from exc
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

def connect(path):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS records (identity TEXT PRIMARY KEY, payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS pages (url TEXT PRIMARY KEY, item_count INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS rejected (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, reason TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS page_signatures (signature TEXT PRIMARY KEY, url TEXT NOT NULL);
    ''')
    return db

def get_meta(db, key, default=None):
    row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else default

def set_meta(db, key, value):
    db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', (key, canonical(value)))

def check_block(status, html):
    if status in (401, 403, 429):
        raise Blocked('http_' + str(status))
    if status >= 400:
        raise CollectorError('http_' + str(status))
    soup = BeautifulSoup(html, 'html.parser')
    if soup.select('[class*="captcha"], [id*="captcha"], iframe[src*="captcha"], input[type="password"]') or re.search(r'verify (?:that )?you are human|access denied|unusual traffic', soup.get_text(' ', strip=True), re.I):
        raise Blocked('captcha_or_login_or_access_challenge')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class HTTPAdapter:
    def fetch(self, url):
        try:
            with build_opener(NoRedirect()).open(Request(url, headers={'User-Agent': 'SIONLAB-Web-Collector/0.2.0'}), timeout=30) as response:
                data = response.read(10_000_001)
                if len(data) > 10_000_000:
                    raise CollectorError('page_too_large')
                html = data.decode(response.headers.get_content_charset() or 'utf-8', errors='replace')
                check_block(response.status, html)
                return html, response.url
        except HTTPError as exc:
            if 300 <= exc.code < 400:
                raise CollectorError('redirect_requires_review') from exc
            check_block(exc.code, '')
            raise CollectorError('http_error') from exc
        except (URLError, TimeoutError) as exc:
            raise CollectorError('network_error') from exc

class PlaywrightAdapter:
    """Fresh context and serial intercepted GETs; no login or evasion actions."""
    def __init__(self, requests_per_second=1, wait_selector=None):
        self.wait_selector = wait_selector
        self.interval = 1 / requests_per_second
        self.last_request = 0

    def fetch(self, url):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise CollectorError('optional_playwright_not_installed') from exc
        failure, pending_routes, active = [], [], [False]
        def route_request(route):
            pending_routes.append(route)
            if active[0]:
                return
            active[0] = True
            try:
                while pending_routes:
                    route_one(pending_routes.pop(0))
            finally:
                active[0] = False
        def route_one(route):
            request = route.request
            if failure or request.method != 'GET' or request.resource_type in ('image', 'media', 'font', 'stylesheet'):
                route.abort()
                return
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            # Newly arriving callbacks queue until this intercepted fetch completes.
            try:
                response = route.fetch(max_redirects=0, max_retries=0, timeout=30000)
                if response.status in (401, 403, 429):
                    failure.append(Blocked('http_' + str(response.status)))
                    route.abort()
                elif 300 <= response.status < 400:
                    failure.append(CollectorError('redirect_requires_review'))
                    route.abort()
                elif response.status >= 400:
                    failure.append(CollectorError('http_' + str(response.status)))
                    route.abort()
                else:
                    route.fulfill(response=response)
            except Exception:
                failure.append(CollectorError('browser_network_error'))
                route.abort()
        with sync_playwright() as engine:
            browser = engine.chromium.launch(headless=True)
            try:
                context = browser.new_context(service_workers='block')
                context.route('**/*', route_request)
                page = context.new_page()
                try:
                    response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                except Exception:
                    if failure:
                        raise failure[0]
                    raise CollectorError('browser_navigation_error') from None
                if failure:
                    raise failure[0]
                html = page.content()
                check_block(response.status if response else 500, html)
                if self.wait_selector:
                    try:
                        page.wait_for_selector(self.wait_selector, state='attached', timeout=30000)
                    except Exception:
                        if failure:
                            raise failure[0]
                        raise CollectorError('dynamic_items_not_ready') from None
                    if failure:
                        raise failure[0]
                    html = page.content()
                    check_block(response.status if response else 500, html)
                return html, page.url
            finally:
                browser.close()

def normalize(raw, kind, url):
    if kind == 'text':
        return ' '.join(raw.split())
    if kind == 'url':
        return urljoin(url, raw)
    if kind == 'json':
        return json.loads(raw)
    value = raw.strip().replace(',', '')
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError('nonfinite')
    if kind == 'integer' and number != number.to_integral_value():
        raise ValueError('fractional_integer')
    return format(number, 'f')  # Monetary precision never passes through float.

def parse_page(html, url, config):
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for item in soup.select(config['item_selector']):
        fields = {}
        for name, spec in config['fields'].items():
            node = item if spec['selector'] == ':self' else item.select_one(spec['selector'])
            raw = None if node is None else (node.get(spec['attribute']) if spec.get('attribute') else node.get_text())
            if raw is None or raw == '':
                fields[name] = {'raw': raw, 'normalized': None, 'missing_reason': 'element_or_attribute_missing' if raw is None else 'empty_text'}
            else:
                raw = str(raw)
                try:
                    fields[name] = {'raw': raw, 'normalized': normalize(raw, spec.get('normalize', 'text'), url), 'missing_reason': None}
                except (ValueError, InvalidOperation, TypeError):
                    fields[name] = {'raw': raw, 'normalized': None, 'missing_reason': 'normalization_failed'}
        keys = config['unique_key']
        keys = [keys] if isinstance(keys, str) else keys
        identity = [fields[key]['normalized'] for key in keys]
        rows.append({'identity': None if any(x is None for x in identity) else canonical(identity), 'source_url': url, 'fields': fields})
    next_node = soup.select_one(config['next_selector']) if config.get('next_selector') else None
    next_url = urljoin(url, next_node.get('href', '')) if next_node is not None and next_node.get('href') else None
    if next_url and urlsplit(next_url).scheme not in ('http', 'https'):
        raise CollectorError('unsupported_next_url')
    if next_url and urlsplit(next_url).netloc != urlsplit(config['start_url']).netloc:
        raise CollectorError('cross_origin_next_url')
    return rows, next_url

def status(db):
    return {'status': get_meta(db, 'status', 'new'), 'reason': get_meta(db, 'reason') or ('missing_unique_keys' if get_meta(db, 'missing_keys', 0) else None), 'total_count': None,
            'total_count_reason': 'website_has_no_verified_total_contract',
            'stored_count': db.execute('SELECT COUNT(*) FROM records').fetchone()[0],
            'read_count': get_meta(db, 'read_count', 0), 'duplicate_count': get_meta(db, 'duplicates', 0),
            'missing_key_count': get_meta(db, 'missing_keys', 0),
            'completed_pages': db.execute('SELECT COUNT(*) FROM pages').fetchone()[0],
            'next_url': get_meta(db, 'next_url'), 'pending_items': len((get_meta(db, 'pending') or {}).get('rows', [])),
            'partial': get_meta(db, 'status') != 'complete' or get_meta(db, 'missing_keys', 0) > 0}

def collect(path, config=None, *, resume=False, adapter=None, checkpoint_hook=None, sleep=time.sleep):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with job_lock(path):
        if resume and not path.exists():
            raise CollectorError('job_not_found')
        db = connect(path)
        try:
            previous = get_meta(db, 'config')
            if previous is not None:
                if config is not None and config_hash(validate_config(config)) != get_meta(db, 'config_hash'):
                    raise CollectorError('config_mismatch: use a different job for different conditions')
                if not resume:
                    raise CollectorError('job_exists: use resume')
                config = previous
            else:
                if resume:
                    raise CollectorError('job_not_initialized')
                validate_config(config)
                with db:
                    set_meta(db, 'config', config)
                    set_meta(db, 'config_hash', config_hash(config))
                    set_meta(db, 'next_url', config['start_url'])
            if get_meta(db, 'status') == 'complete':
                return status(db)
            adapter = adapter or (PlaywrightAdapter(config.get('requests_per_second', 1), config['item_selector']) if config.get('adapter') == 'playwright' else HTTPAdapter())
            used_pages, used_items = 0, 0
            max_pages, max_items = config.get('max_pages', 2), config.get('max_items', 50)
            while used_pages < max_pages and used_items < max_items:
                pending = get_meta(db, 'pending')
                url = get_meta(db, 'next_url')
                if not pending and not url:
                    with db:
                        set_meta(db, 'status', 'complete')
                        set_meta(db, 'reason', None)
                    break
                if not pending:
                    if db.execute('SELECT 1 FROM pages WHERE url=?', (url,)).fetchone():
                        with db:
                            set_meta(db, 'status', 'stopped')
                            set_meta(db, 'reason', 'pagination_cycle')
                        break
                    last_request = get_meta(db, 'last_request', 0)
                    sleep(max(0, 1 / config.get('requests_per_second', 1) - (time.time() - last_request)))
                    with db:
                        set_meta(db, 'last_request', time.time())
                    try:
                        html, final_url = adapter.fetch(url)
                        rows, following = parse_page(html, final_url, config)
                        if not rows:
                            raise CollectorError('no_items_matched: empty page requires review')
                        signature = hashlib.sha256(canonical([{'identity': row['identity'], 'fields': row['fields']} for row in rows]).encode()).hexdigest()
                        if db.execute('SELECT 1 FROM page_signatures WHERE signature=?', (signature,)).fetchone():
                            raise CollectorError('repeated_page_content')
                        pending = {'url': url, 'rows': rows, 'next_url': following, 'item_count': len(rows), 'signature': signature}
                    except Exception as exc:
                        reason = str(exc) if isinstance(exc, CollectorError) else 'adapter_or_parse_error'
                        with db:
                            set_meta(db, 'status', 'blocked' if isinstance(exc, Blocked) else 'failed')
                            set_meta(db, 'reason', reason)
                        break
                    used_pages += 1
                take = pending['rows'][:max_items-used_items]
                rest = pending['rows'][len(take):]
                with db:
                    duplicates, missing = get_meta(db, 'duplicates', 0), get_meta(db, 'missing_keys', 0)
                    for row in take:
                        if row['identity'] is None:
                            missing += 1
                            db.execute('INSERT INTO rejected(payload,reason) VALUES (?, ?)', (canonical(row), 'missing_unique_key'))
                        else:
                            cursor = db.execute('INSERT OR IGNORE INTO records VALUES (?, ?)', (row['identity'], canonical(row)))
                            duplicates += cursor.rowcount == 0
                    set_meta(db, 'duplicates', duplicates)
                    set_meta(db, 'missing_keys', missing)
                    set_meta(db, 'read_count', get_meta(db, 'read_count', 0) + len(take))
                    if rest:
                        set_meta(db, 'pending', {**pending, 'rows': rest})
                    else:
                        db.execute('INSERT INTO pages VALUES (?, ?)', (pending['url'], pending['item_count']))
                        if pending.get('signature'):
                            db.execute('INSERT INTO page_signatures VALUES (?, ?)', (pending['signature'], pending['url']))
                        set_meta(db, 'pending', None)
                        set_meta(db, 'next_url', pending['next_url'])
                    set_meta(db, 'status', 'partial' if rest or pending['next_url'] else 'complete')
                    set_meta(db, 'reason', 'run_limit' if rest or pending['next_url'] else None)
                    if checkpoint_hook:
                        checkpoint_hook('before_commit')
                if checkpoint_hook:
                    checkpoint_hook('after_commit')
                used_items += len(take)
                if not rest and not pending['next_url']:
                    break
            return status(db)
        finally:
            db.close()

def load_records(path):
    if not Path(path).is_file():
        raise CollectorError('job_not_found')
    with sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro', uri=True) as db:
        return [json.loads(row[0]) for row in db.execute('SELECT payload FROM records ORDER BY rowid')]

def verify_job(path):
    if not Path(path).is_file():
        raise CollectorError('job_not_found')
    with job_lock(path), sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro', uri=True) as db:
        result = status(db)
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        config = get_meta(db, 'config')
        valid = integrity == 'ok' and config is not None and config_hash(config) == get_meta(db, 'config_hash')
        valid = valid and result['read_count'] == result['stored_count'] + result['duplicate_count'] + result['missing_key_count']
        result.update({'valid': bool(valid), 'sqlite_integrity': integrity})
        return result
