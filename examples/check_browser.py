#!/usr/bin/env python3
"""선택 브라우저의 지연된 JS 목록을 로컬 HTTP로 실제 검증한다."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
from sionlab_web_collector.core import collect, load_records


class Handler(BaseHTTPRequestHandler):
    requested = []

    def do_GET(self):
        self.requested.append((self.path, time.monotonic()))
        if self.path == '/items':
            body = '[{"id":"DYNAMIC-1","title":"동적 교육 공지"}]'
            mime = 'application/json; charset=utf-8'
        else:
            body = '''<!doctype html><meta charset="utf-8"><main></main>
<script>setTimeout(async () => {
  const rows = await (await fetch('/items')).json();
  for (const row of rows) {
    const node = document.createElement('article');
    node.innerHTML = '<b>' + row.id + '</b><span>' + row.title + '</span>';
    document.querySelector('main').appendChild(node);
  }
}, 250);</script>'''
            mime = 'text/html; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *_):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = {'start_url': f'http://127.0.0.1:{server.server_port}/',
                  'adapter': 'playwright', 'item_selector': 'article',
                  'fields': {'id': {'selector': 'b'}, 'title': {'selector': 'span'}},
                  'unique_key': 'id', 'max_pages': 1, 'max_items': 1}
        with tempfile.TemporaryDirectory(prefix='sionlab-dynamic-') as directory:
            job = Path(directory) / 'job.sqlite'
            result = collect(job, config)
            rows = load_records(job)
            assert result['status'] == 'complete', result
            assert len(rows) == 1 and rows[0]['fields']['title']['normalized'] == '동적 교육 공지', rows
            assert [v[0] for v in Handler.requested] == ['/', '/items'], Handler.requested
            interval = Handler.requested[1][1] - Handler.requested[0][1]
            assert interval >= 0.9, interval
            print(json.dumps({'status': 'pass', 'scope': 'local-real-chromium-delayed-javascript',
                              'stored_count': 1, 'http_requests': 2, 'external_requests': 0,
                              'request_interval_seconds': round(interval, 3)}, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    main()
