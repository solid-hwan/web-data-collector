#!/usr/bin/env python3
"""Create only this package's isolated environment; use already-installed uv if needed."""
from pathlib import Path
import importlib.util
import shutil
import subprocess
import sys
import venv
root = Path(__file__).resolve().parent
location = root / '.venv'
python = location / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
if importlib.util.find_spec('ensurepip'):
    venv.EnvBuilder(with_pip=True).create(location)
    installer = [str(python), '-m', 'pip']
else:
    uv = shutil.which('uv')
    if not uv:
        raise SystemExit('Python ensurepip is absent and no existing uv executable was found. Supply a Python with venv support.')
    if not python.exists():
        subprocess.run([uv, 'venv', '--python', sys.executable, str(location)], check=True)
    installer = [uv, 'pip']
def install(*arguments):
    command = installer + ['install']
    if installer[0] != str(python):
        command += ['--python', str(python)]
    subprocess.run(command + list(arguments), check=True)
install('-r', str(root / 'requirements.lock'))
install('--no-build-isolation', '--no-deps', str(root))
