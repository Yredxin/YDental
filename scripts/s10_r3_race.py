"""Guard two Odoo shell actors on distinct PostgreSQL backends."""
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import psycopg2

ROOT = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
CORE = ROOT.parent
NAME = 'ydental_s10_test_20261014015000_a9d8e4c1'
RUN = ROOT / '.local' / NAME
CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
EXPECTED = os.environ['YDENTAL_S10_EXPECTED_SHA']
mode = sys.argv[1]
assert mode in ('approval', 'refund', 'reclassify')
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == EXPECTED
assert subprocess.check_output(['git', '-C', str(CORE / 'odoo'), 'rev-parse', 'HEAD'], text=True).strip() == CORE_SHA
marker = json.loads((RUN / 'database.json').read_text())
assert marker['database'] == NAME and marker['source_commit'] == EXPECTED
assert marker['config_sha256'] == hashlib.sha256((RUN / 'odoo.conf').read_bytes()).hexdigest()
assert not list(RUN.glob('crash-*.json'))
conf = configparser.ConfigParser(interpolation=None)
assert conf.read(RUN / 'odoo.conf')
with psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
        password=conf['options']['db_password'], dbname='postgres') as db:
    with db.cursor() as cursor:
        cursor.execute('SELECT oid FROM pg_database WHERE datname=%s', (NAME,))
        assert cursor.fetchone()[0] == marker['oid']
script = ROOT / 'scripts/s10_completion' / (
    'approval_race_actor.py' if mode == 'approval' else 'finance_race_actor.py')
assert script.is_file()
policy = ROOT / 'scripts/s08c_network_policy.py'
assert hashlib.sha256((RUN / 'network-policy/sitecustomize.py').read_bytes()).digest() == hashlib.sha256(policy.read_bytes()).digest()
deps = ROOT / '.local/s00-b-deps'
processes = {}
streams = {}
for actor in ('a', 'b'):
    log = RUN / ('race-' + mode + '-' + actor + '.log')
    assert not log.exists()
    stream = log.open('x')
    streams[actor] = stream
    environment = os.environ.copy()
    environment.update({'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + os.environ.get('PATH', ''),
        'FONTCONFIG_FILE': str(deps / 'fonts.conf'), 'XDG_CACHE_HOME': str(deps / 'cache'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONFAULTHANDLER': '1',
        'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
        'YDENTAL_S08C_HTTP_PORT': str(marker['port']), 'YDENTAL_S10_RUN_DIR': str(RUN),
        'YDENTAL_S10_ACTOR': actor, 'YDENTAL_S10_RACE_MODE': mode,
        'PGOPTIONS': '-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
    command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin'),
        'shell', '-c', str(RUN / 'odoo.conf'), '--no-http']
    process = subprocess.Popen(command, cwd=CORE, env=environment, stdin=subprocess.PIPE,
                               stdout=stream, stderr=subprocess.STDOUT, text=True)
    process.stdin.write(script.read_text())
    process.stdin.close()
    processes[actor] = (process, command, log)
started = time.monotonic()
while any(process.poll() is None for process, _, _ in processes.values()):
    crashed = [process for process, _, _ in processes.values()
               if process.poll() is not None and (process.returncode == 139 or process.returncode == -11)]
    if crashed:
        for process, _, _ in processes.values():
            if process.poll() is None:
                process.terminate()
        break
    if time.monotonic() - started > 180:
        for process, _, _ in processes.values():
            if process.poll() is None:
                process.terminate()
        break
    time.sleep(0.1)
for stream in streams.values():
    stream.close()
records = []
for actor, (process, command, log) in processes.items():
    process.wait()
    row = {'mode': mode, 'actor': actor, 'pid': process.pid,
        'exit_code': process.returncode, 'signal': -process.returncode if process.returncode < 0 else None,
        'database': NAME, 'oid': marker['oid'], 'command': command,
        'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
        'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
    records.append(row)
    if row['signal'] == 11 or row['exit_code'] == 139:
        (RUN / ('crash-' + str(process.pid) + '.json')).write_text(json.dumps(row) + '\n')
with (RUN / 'race-actions.jsonl').open('a') as output:
    for row in records:
        output.write(json.dumps(row) + '\n')
print(json.dumps(records), flush=True)
assert all(row['exit_code'] == 0 for row in records)
