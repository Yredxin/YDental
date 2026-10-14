import argparse
import configparser
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import psycopg2

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
assert not list(run.glob('crash-*.json')) and not list(run.glob('close-race-barrier-*.json'))
config = configparser.ConfigParser(interpolation=None)
assert config.read(run / 'odoo.conf')
script = (root / 'scripts/s10_completion/close_race_actor.py').read_text()
deps = root / '.local/s00-b-deps'
environment = os.environ.copy()
environment.update({'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + os.environ.get('PATH', ''),
    'PYTHONPATH': str(run / 'network-policy') + os.pathsep + str(root / '.local/s04-deps'),
    'YDENTAL_S10_RUN_DIR': str(run), 'YDENTAL_S08C_HTTP_PORT': str(marker['port']),
    'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
    'PGOPTIONS': '-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
children = []
for actor in ('a', 'b'):
    command = [str(core / '.venv/bin/python'), str(core / 'odoo-bin'),
        'shell', '-c', str(run / 'odoo.conf'), '--no-http']
    log = run / ('close-race-' + actor + '.log')
    output = log.open('x')
    child = subprocess.Popen(command, cwd=core, env=environment | {'YDENTAL_S10_ACTOR': actor},
        stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT, text=True)
    children.append((actor, child, output, log, command))
for _actor, child, _output, _log, _command in children:
    child.stdin.write(script)
    child.stdin.close()
for actor, child, output, log, command in children:
    try:
        child.wait(timeout=180)
    except subprocess.TimeoutExpired:
        child.terminate()
        child.wait(timeout=15)
    output.close()
    record = {'actor': actor, 'pid': child.pid, 'exit_code': child.returncode,
        'signal': -child.returncode if child.returncode < 0 else None,
        'command': command, 'script_sha256': hashlib.sha256(script.encode()).hexdigest(),
        'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
        'database': args.db, 'oid': marker['oid']}
    with (run / 'close-race-actions.jsonl').open('a') as stream:
        stream.write(json.dumps(record) + '\n')
    if child.returncode < 0 or child.returncode == 139:
        (run / ('crash-' + str(child.pid) + '.json')).write_text(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
assert all(child.returncode == 0 for _actor, child, *_rest in children)
a, b = (json.loads((run / ('close-race-actor-' + actor + '.json')).read_text()) for actor in ('a', 'b'))
assert a['backend_pid'] != b['backend_pid']
assert a['outcome'] == 'accepted' and b['outcome'] in ('accepted', 'rejected')
fixture = json.loads((run / 'close-race-fixture.json').read_text())
with psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
        password=config['options']['db_password'], dbname=args.db) as connection:
    connection.set_session(readonly=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*),max(ydental_gross) FROM ydental_settlement_close "
                       "WHERE ydental_store_id=%s AND ydental_business_date=%s "
                       "AND ydental_channel='card' AND ydental_state='confirmed'",
                       (fixture['store_id'], fixture['business_date']))
        close_count, gross = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM ydental_settlement_payment WHERE id=%s",
                       (b['result'].get('payment_id') or 0,))
        pay_count = cursor.fetchone()[0]
        cursor.execute('SELECT deadlocks FROM pg_stat_database WHERE datname=%s', (args.db,))
        deadlocks = cursor.fetchone()[0]
assert close_count == 1 and pay_count == (1 if b['outcome'] == 'accepted' else 0)
assert deadlocks == 0
print('S10_CLOSE_RACE_RESULT', json.dumps({'backend_pids': [a['backend_pid'], b['backend_pid']],
    'outcomes': [a['outcome'], b['outcome']], 'gross': float(gross),
    'payment_created': pay_count, 'deadlocks': deadlocks}), flush=True)
