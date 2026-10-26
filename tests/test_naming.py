"""신구 진입점의 작업 재개·Excel 복원 호환을 검증한다."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from web_data_collector import __version__
from sionlab_web_collector.core import collect, load_records
from sionlab_web_collector.exporting import export_job, read_xlsx


class Fixture:
    def fetch(self, url):
        return '<article><b>001</b><p>' + '한'*40000 + '</p></article><article><b>002</b><p>=수식아님</p></article>', url


class NamingTests(unittest.TestCase):
    def test_distribution_and_all_help_entrypoints(self):
        self.assertEqual(importlib.metadata.version('web-data-collector'), __version__)
        commands = [[sys.executable, '-m', m] for m in ('web_data_collector', 'sionlab_web_collector')]
        commands += [[str(Path(sys.executable).parent / n)] for n in ('web-data-collector', 'sionlab-web-collector')]
        helps = []
        for command in commands:
            result = subprocess.run(command + ['--help'], text=True, capture_output=True, check=True, timeout=10)
            self.assertIn('웹 데이터 수집기', result.stdout)
            helps.append(result.stdout)
        self.assertTrue(all(text == helps[0] for text in helps))

    def test_resume_saved_queue_and_restore_old_excel_with_new_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); job = root/'existing.sqlite'; old_excel = root/'old.xlsx'
            config = {'start_url': 'https://example.invalid/fixture', 'item_selector': 'article',
                'fields': {'id': {'selector': 'b'}, 'text': {'selector': 'p'}}, 'unique_key': 'id', 'max_items': 1}
            initial = collect(job, config, adapter=Fixture())
            self.assertEqual(initial['pending_items'], 1)
            export_job(job, old_excel)
            self.assertEqual(read_xlsx(old_excel), load_records(job))
            def run(command, *args):
                result = subprocess.run(command + list(args), text=True, capture_output=True, check=True, timeout=10)
                return json.loads(result.stdout)
            commands = [[sys.executable, '-m', m] for m in ('web_data_collector', 'sionlab_web_collector')]
            commands += [[str(Path(sys.executable).parent / n)] for n in ('web-data-collector', 'sionlab-web-collector')]
            before = [run(c, 'verify', '--job', str(job), '--xlsx', str(old_excel)) for c in commands]
            self.assertTrue(all(r['valid'] and r['xlsx_matches'] for r in before))
            resumed = run(commands[0], 'resume', '--job', str(job))
            self.assertEqual(resumed['stored_count'], 2)
            self.assertEqual(resumed['pending_items'], 0)
            for index, command in enumerate(commands):
                xlsx = root/f'new-{index}.xlsx'
                run(command, 'export', '--job', str(job), '--output', str(xlsx))
                self.assertEqual(read_xlsx(xlsx), load_records(job))
                self.assertTrue(run(command, 'verify', '--job', str(job), '--xlsx', str(xlsx))['xlsx_matches'])
