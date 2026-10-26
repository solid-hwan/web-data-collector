"""CLI stdout is machine-readable JSON; errors do not expose request contents."""
import argparse
import json
import sqlite3
from pathlib import Path
from .core import CollectorError, collect, load_records, verify_job
from .exporting import export_job, read_xlsx

def main(argv=None):
    parser = argparse.ArgumentParser(prog='web-data-collector', description='웹 데이터 수집기 0.3.0 — 웹 목록 수집과 Excel 저장')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('crawl', 'resume'):
        item = sub.add_parser(command)
        item.add_argument('--job', required=True, help='Job SQLite path')
        item.add_argument('--config', required=command == 'crawl', help='JSON config; resume checks exact hash if supplied')
    item = sub.add_parser('export')
    item.add_argument('--job', required=True)
    item.add_argument('--output', required=True)
    item.add_argument('--xlsx-mode', choices=('normal', 'write-only'), default='normal')
    item.add_argument('--sheet', default='Data')
    item = sub.add_parser('verify')
    item.add_argument('--job', required=True)
    item.add_argument('--xlsx', help='Reopen and compare exported XLSX to job')
    args = parser.parse_args(argv)
    try:
        if args.command in ('crawl', 'resume'):
            config = json.loads(Path(args.config).read_text(encoding='utf-8')) if args.config else None
            result = collect(args.job, config, resume=args.command == 'resume')
            code = 2 if result['status'] in ('blocked', 'failed', 'stopped') else 0
        elif args.command == 'export':
            result = export_job(args.job, args.output, mode=args.xlsx_mode, sheet=args.sheet)
            code = 0
        else:
            result = verify_job(args.job)
            if args.xlsx:
                result['xlsx_matches'] = read_xlsx(args.xlsx) == load_records(args.job)
                result['valid'] = result['valid'] and result['xlsx_matches']
            code = 0 if result['valid'] else 2
        print(json.dumps(result, ensure_ascii=False))
        return code
    except (CollectorError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        message = str(exc) if isinstance(exc, CollectorError) else type(exc).__name__
        print(json.dumps({'status': 'error', 'result': None, 'reason': message}, ensure_ascii=False))
        return 2
