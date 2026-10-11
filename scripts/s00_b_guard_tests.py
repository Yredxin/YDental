"""Exercise real S00-B runner refusals without installing or deleting a database."""
import argparse
import configparser
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT.parent / '.venv/bin/python'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'ydental_s00b_test_[0-9]{14}_[a-f0-9]{8}', args.db):
        parser.error('Only a newly recorded S00-B test database is allowed')
    run = ROOT / '.local' / args.db
    marker = run / 'database.json'
    original = marker.read_bytes()
    metadata = json.loads(original)
    if metadata['database'] != args.db or metadata['endpoint'] != {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}:
        parser.error('Creation record mismatch')
    config = configparser.ConfigParser(interpolation=None)
    config.read(run / 'odoo.conf')
    options = config['options']
    for name, expected in [('db_host', '127.0.0.1'), ('db_port', '5432'), ('db_user', 'odoo')]:
        if options[name] != expected:
            parser.error('Runtime endpoint differs from approved endpoint')
    def catalog():
        with psycopg2.connect(dbname='postgres', host='127.0.0.1', port=5432,
                              user='odoo', password=options['db_password']) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT datname, oid FROM pg_database ORDER BY datname')
                return cursor.fetchall()
    before = catalog()
    results = []
    traces = run / 'guards'
    traces.mkdir(exist_ok=True)
    def rejected(case, runner_args, maintenance_connection=False):
        trace = traces / (case + '.connect.trace')
        command = ['strace', '-f', '-e', 'trace=connect', '-o', str(trace),
                   str(PYTHON), str(ROOT / 'scripts/s00_b.py'), *runner_args]
        result = subprocess.run(command, capture_output=True, text=True)
        connections = [line for line in trace.read_text().splitlines() if 'connect(' in line]
        inet = [line for line in connections if 'AF_INET' in line]
        assert result.returncode == 2, (case, result.returncode)
        if not maintenance_connection:
            assert not inet, (case, inet)
        else:
            assert all('sin_port=htons(5432)' in line and '127.0.0.1' in line for line in inet)
        results.append({'case': case, 'args': runner_args, 'exit_code': result.returncode,
                        'error': result.stderr.split('error:')[-1].strip(),
                        'inet_connect_syscalls': inet,
                        'scope': 'maintenance catalog only' if maintenance_connection else 'no INET connect syscall'})
    install = ['install', '--db', args.db, '--port', str(metadata['port'])]
    upgrade = ['upgrade', '--db', args.db, '--port', str(metadata['port'])]
    for case, name in [('business_name', 'odoo20_dev'), ('historical_name', 'ydental_p00_test_baseline02'),
                       ('injection_name', 'ydental_s00b_test_x;DROP DATABASE x')]:
        rejected(case, ['install', '--db', name])
    fresh = 'ydental_s00b_test_20990101000000_' + secrets.token_hex(4)
    rejected('missing_record', ['upgrade', '--db', fresh])
    wrong = traces / 'wrong-endpoint.conf'
    wrong.write_text('[options]\ndb_host=127.0.0.1\ndb_port=15432\ndb_user=odoo\n')
    wrong.chmod(0o600)
    rejected('wrong_endpoint', install + ['--config', str(wrong)])
    rejected('protected_port', install[:-1] + ['8069'])
    rejected('existing_run', install)
    changed = dict(metadata, oid=metadata['oid'] + 1)
    try:
        marker.write_text(json.dumps(changed))
        rejected('changed_oid', upgrade, maintenance_connection=True)
    finally:
        marker.write_bytes(original)
    try:
        marker.write_text(json.dumps(dict(metadata, cluster='wrong-cluster')))
        rejected('changed_cluster_record', upgrade)
    finally:
        marker.write_bytes(original)
    runtime = run / 'odoo.conf'
    saved = runtime.read_bytes()
    try:
        runtime.write_bytes(saved + b'\n# S00-B intentional tamper test\n')
        rejected('changed_config', upgrade)
    finally:
        runtime.write_bytes(saved)
    held = run.with_name(run.name + '-guard-held')
    if held.exists():
        raise RuntimeError('Held directory already exists; preserving it')
    try:
        run.rename(held)
        # Keep the trace directory outside the temporarily moved run directory.
        traces = held / 'guards'
        rejected('existing_database_without_local_record', install, maintenance_connection=True)
    finally:
        held.rename(run)
        traces = run / 'guards'
    link = ROOT / '.local' / fresh
    try:
        link.symlink_to(run, target_is_directory=True)
        rejected('symlink_run', ['upgrade', '--db', fresh])
    finally:
        link.unlink()
    with (ROOT / '.local/s00-b-runner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rejected('concurrent_action_lock', upgrade)
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1', 18080))
        occupied.listen()
        rejected('occupied_port', ['install', '--db', fresh, '--port', '18080'])
    after = catalog()
    assert before == after
    assert marker.read_bytes() == original and runtime.read_bytes() == saved
    output = {'database': args.db, 'cases': results, 'count': len(results), 'all_rejected': True,
              'catalog_before_equals_after': True, 'record_and_config_restored': True,
              'exit_code': 0, 'odoo_business_tests': 0}
    (ROOT / 'docs/evidence/s00-b/guards.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Guard refusal cases:', len(results), '; exit 0; catalog unchanged')


if __name__ == '__main__':
    main()
