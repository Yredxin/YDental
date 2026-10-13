"""Guarded S10 D2 final synthetic database runner."""
import configparser
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys

import psycopg2
from psycopg2 import sql

ROOT = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
CORE = ROOT.parent
STATE = ROOT / '.local'
NAME = 'ydental_s10_test_20261013234419_c84e6d12'
RUN = STATE / NAME
PORT = 18231
CLUSTER = '7694897083368259627'
CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BASE_SHA = os.environ['YDENTAL_S10_EXPECTED_SHA']
CANARY = ROOT / 'scripts/s10_completion/f1_740.py'
POLICY_SOURCE = ROOT / 'scripts/s08c_network_policy.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def private(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        stream.write(data)

def identity(action):
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == BASE_SHA
    assert subprocess.check_output(['git', '-C', str(CORE / 'odoo'), 'rev-parse', 'HEAD'], text=True).strip() == CORE_SHA
    assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    source = configparser.ConfigParser(interpolation=None)
    assert source.read(CORE / 'odoo.conf')
    options = source['options']
    assert (options.get('db_host'), options.get('db_port'), options.get('db_user')) == ('127.0.0.1', '5432', 'odoo')
    endpoint = dict(host='127.0.0.1', port='5432', user='odoo', password=options['db_password'], connect_timeout=5)
    with closing(psycopg2.connect(dbname='postgres', **endpoint)) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT system_identifier::text FROM pg_control_system()')
            assert cur.fetchone()[0] == CLUSTER
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s', (NAME,))
            existing = cur.fetchone()
            if action == 'create':
                assert not RUN.exists() and existing is None
                RUN.mkdir(mode=0o700)
                cur.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(NAME)), ('UTF8',))
                cur.execute('SELECT oid FROM pg_database WHERE datname=%s', (NAME,))
                oid = cur.fetchone()[0]
            else:
                marker = json.loads((RUN / 'database.json').read_text())
                assert existing and existing[0] == marker['oid']
                assert marker['cluster'] == CLUSTER and marker['port'] == PORT
                oid = existing[0]
    if action == 'create':
        config = configparser.ConfigParser(interpolation=None)
        config['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
            'db_password': options['db_password'], 'db_name': NAME, 'dbfilter': '^' + NAME + '$',
            'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
            'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
            'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
            'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
        buffer = io.StringIO()
        config.write(buffer)
        private(RUN / 'odoo.conf', buffer.getvalue())
        marker = {'database': NAME, 'oid': oid, 'cluster': CLUSTER,
            'endpoint': {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'},
            'port': PORT, 'core': CORE_SHA, 'source_commit': BASE_SHA,
            'config_sha256': sha(RUN / 'odoo.conf'), 'canary_sha256': sha(CANARY),
            'created_utc': datetime.now(timezone.utc).isoformat()}
        private(RUN / 'database.json', json.dumps(marker, indent=2) + '\n')
        policy = RUN / 'network-policy'
        policy.mkdir(mode=0o700)
        private(policy / 'sitecustomize.py', POLICY_SOURCE.read_text())
    marker = json.loads((RUN / 'database.json').read_text())
    assert marker['database'] == NAME and marker['oid'] == oid
    assert sha(RUN / 'odoo.conf') == marker['config_sha256']
    assert CANARY.is_file()
    assert sha(RUN / 'network-policy/sitecustomize.py') == sha(POLICY_SOURCE)
    assert not list(RUN.glob('crash-*.json'))
    return marker, endpoint

def installed(endpoint):
    with closing(psycopg2.connect(dbname=NAME, **endpoint)) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT state FROM ir_module_module WHERE name='ydental_settlement'")
            row = cur.fetchone()
            return row and row[0] == 'installed'

def main(action):
    assert action in ('create', 'install', 'upgrade', 'shell')
    marker, endpoint = identity(action)
    if action == 'create':
        print(json.dumps(marker))
        return 0
    actions = RUN / 'actions.jsonl'
    previous = [json.loads(line) for line in actions.read_text().splitlines()] if actions.exists() else []
    assert len(previous) < 25
    if action == 'install':
        assert not previous
    else:
        assert previous and all(row['signal'] is None and row['exit_code'] != 139 for row in previous)
        assert installed(endpoint)
    deps = STATE / 's00-b-deps'
    environment = os.environ.copy()
    environment.update({'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + os.environ.get('PATH', ''),
        'FONTCONFIG_FILE': str(deps / 'fonts.conf'), 'XDG_CACHE_HOME': str(deps / 'cache'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONFAULTHANDLER': '1',
        'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(STATE / 's04-deps'),
        'YDENTAL_S08C_HTTP_PORT': str(PORT), 'YDENTAL_S10_RUN_DIR': str(RUN),
        'PGOPTIONS': '-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
    command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin')]
    if action in ('install', 'upgrade'):
        command += ['-c', str(RUN / 'odoo.conf'), '-i' if action == 'install' else '-u',
                    'ydental_settlement,ydental_settlement_test',
                    '--load-language', 'en_US,zh_CN', '--stop-after-init']
        stdin = None
    else:
        assert len(sys.argv) == 3
        name = sys.argv[2]
        assert name in ('f1_740', 'f5_270_200', 'f2_f3_refund_close', 'pending_board', 't09_trade', 'same_company_transfer', 'discount_waive', 'partial_refund', 'concurrency_prepare', 'quantity_correction', 'history_205', 'f6_cross_store')
        probe = ROOT / 'scripts/s10_completion' / (name + '.py')
        assert probe.is_file()
        command += ['shell', '-c', str(RUN / 'odoo.conf'), '--no-http']
        stdin = probe.read_text()
    log = RUN / (action + '-' + str(len(previous) + 1) + '.log')
    with log.open('x') as stream:
        child = subprocess.Popen(command, cwd=CORE, env=environment, stdin=subprocess.PIPE if stdin else None,
                                 stdout=stream, stderr=subprocess.STDOUT, text=stdin is not None)
        if stdin is None:
            child.wait()
        else:
            child.communicate(stdin)
    record = {'action': action, 'pid': child.pid, 'exit_code': child.returncode,
        'signal': -child.returncode if child.returncode < 0 else None,
        'database': NAME, 'oid': marker['oid'], 'port': PORT,
        'command': command, 'config_sha256': marker['config_sha256'],
        'probe_sha256': sha(probe) if action == 'shell' else None, 'log_sha256': sha(log),
        'log_bytes': log.stat().st_size, 'time_utc': datetime.now(timezone.utc).isoformat()}
    with actions.open('a') as stream:
        stream.write(json.dumps(record) + '\n')
    if child.returncode < 0 or child.returncode == 139:
        private(RUN / ('crash-' + str(child.pid) + '.json'), json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    return child.returncode

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
