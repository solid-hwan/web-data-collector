#!/usr/bin/env python3
"""Self-contained synthetic HTTP fixtures; outputs go only to --output."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from sionlab_web_collector.core import collect, load_records, verify_job
from sionlab_web_collector.exporting import export_job, read_xlsx

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    args.output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(source)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = {}
    try:
        for name in ('products', 'education'):
            config = json.loads((source / name / 'config.json').read_text())
            config['start_url'] = f'http://127.0.0.1:{server.server_port}/{name}/page1.html'
            target = args.output / name
            target.mkdir(parents=True, exist_ok=True)
            job = target / 'job.sqlite'
            result = collect(job, config)
            expected = json.loads((source / name / 'expected.json').read_text())
            for key, value in expected.items():
                if key != 'data_kind':
                    assert result[key] == value, (name, key, result[key], value)
            for suffix in ('.jsonl', '.csv', '.xlsx'):
                export_job(job, target / ('sample' + suffix))
            assert read_xlsx(target / 'sample.xlsx') == load_records(job)
            assert verify_job(job)['valid']
            results[name] = {'status': 'pass', 'data_kind': 'synthetic', 'rows': result['stored_count'], 'xlsx_exact_match': True}
        (args.output / 'verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(results, ensure_ascii=False))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

if __name__ == '__main__':
    main()
