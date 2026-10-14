import argparse
import configparser
import hashlib
import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

root = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
core = root.parent
parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
parser.add_argument('--sha', required=True)
args = parser.parse_args()
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', args.db)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == args.sha
run = root / '.local' / args.db
marker = json.loads((run / 'database.json').read_text())
assert marker['database'] == args.db and marker['cluster'] == '7694897083368259627'
assert marker['config_sha256'] == hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest()
assert not list(run.glob('crash-*.json'))
with socket.socket() as listener:
    listener.bind(('127.0.0.1', marker['port']))
config = configparser.ConfigParser(interpolation=None)
assert config.read(run / 'odoo.conf') and config['options']['db_name'] == args.db
deps = root / '.local/s00-b-deps'
environment = os.environ.copy()
environment.update({'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + os.environ.get('PATH', ''),
    'PYTHONPATH': str(run / 'network-policy') + os.pathsep + str(root / '.local/s04-deps'),
    'YDENTAL_S10_RUN_DIR': str(run), 'YDENTAL_S08C_HTTP_PORT': str(marker['port']),
    'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
    'FONTCONFIG_FILE': str(deps / 'fonts.conf'),
    'PGOPTIONS': '-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
command = [str(core / '.venv/bin/python'), str(core / 'odoo-bin'), '-c', str(run / 'odoo.conf')]
attempt = 1
while (run / f'preview-{attempt}.log').exists() or (run / f'firefox-{attempt}.log').exists():
    attempt += 1
preview_log = run / f'preview-{attempt}.log'
browser_log = run / f'firefox-{attempt}.log'
with preview_log.open('x') as stream:
    child = subprocess.Popen(command, cwd=root, env=environment,
                             stdout=stream, stderr=subprocess.STDOUT)
    browser_code = None
    try:
        for _ in range(120):
            if child.poll() is not None:
                raise AssertionError('Isolated Odoo preview exited before health check')
            try:
                with urlopen(f'http://127.0.0.1:{marker["port"]}/web/login', timeout=2) as response:
                    if response.status == 200:
                        break
            except (HTTPError, URLError, TimeoutError):
                pass
            time.sleep(1)
        else:
            raise AssertionError('Isolated Odoo preview did not become healthy')
        browser_command = [str(core / '.venv/bin/python'),
            str(root / 'scripts/s10_completion_browser.py'),
            '--db', args.db, '--port', str(marker['port']), '--pid', str(child.pid)]
        with browser_log.open('x') as browser_stream:
            browser = subprocess.run(browser_command, cwd=root, env=environment,
                                     stdout=browser_stream, stderr=subprocess.STDOUT, timeout=240)
            browser_code = browser.returncode
    finally:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=20)
record = {'database': args.db, 'oid': marker['oid'], 'preview_pid': child.pid,
    'preview_exit_code': child.returncode, 'preview_signal': -child.returncode if child.returncode < 0 else None,
    'browser_exit_code': browser_code, 'command': command,
    'preview_log_sha256': hashlib.sha256(preview_log.read_bytes()).hexdigest(),
    'browser_log_sha256': hashlib.sha256(browser_log.read_bytes()).hexdigest() if browser_log.exists() else None,
    'time_utc': datetime.now(timezone.utc).isoformat()}
(run / f'preview-result-{attempt}.json').write_text(json.dumps(record, indent=2) + '\n')
if child.returncode == -11 or child.returncode == 139:
    (run / ('crash-' + str(child.pid) + '.json')).write_text(json.dumps(record) + '\n')
print(json.dumps(record), flush=True)
assert browser_code == 0 and child.returncode in (0, -15)
