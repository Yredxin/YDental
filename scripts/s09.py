"""Guarded isolated S09 database runner. Never adopts, resets or deletes a database."""
import argparse
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

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
STATE = ROOT / '.local'
CLUSTER = '7694897083368259627'
CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
ENDPOINT = {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        stream.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'upgrade', 'integrate', 'serve', 'export', 'probe',
                                            'ui_seed', 'race', 'audit'])
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--tests', action='store_true')
    parser.add_argument('--upstream', action='store_true', help='Also execute S08-A/B/C native regression addons')
    parser.add_argument('--test-tags', help='A single explicit S09 post-install test selector for diagnosis')
    args = parser.parse_args()
    if not re.fullmatch(r'ydental_s09_test_[0-9]{14}_[0-9a-f]{8}', args.db) or not 18000 <= args.port <= 18999:
        parser.error('A new S09 database name and isolated port are required')
    if subprocess.check_output(['git', '-C', str(CORE / 'odoo'), 'rev-parse', 'HEAD'], text=True).strip() != CORE_SHA:
        parser.error('Core commit changed')
    source = configparser.ConfigParser(interpolation=None)
    if not source.read(CORE / 'odoo.conf'):
        parser.error('Private source config missing')
    options = source['options']
    if (options.get('db_host'), options.get('db_port'), options.get('db_user')) != ('127.0.0.1', '5432', 'odoo'):
        parser.error('PostgreSQL endpoint changed')
    run = STATE / args.db
    marker = run / 'database.json'
    creating = args.action == 'install'
    if run.is_symlink() or creating and run.exists() or not creating and (not marker.is_file() or marker.is_symlink()):
        parser.error('Creation marker absent, reused or unsafe')
    if run.exists() and list(run.glob('crash-*.json')):
        parser.error('Native crash evidence exists; all S09 Odoo actions are stopped pending review')
    if args.upstream and not args.tests:
        parser.error('--upstream requires --tests')
    if args.test_tags and (not args.tests or not re.fullmatch(
            r'/ydental_exam_test:TestExamination\.test_[a-z0-9_]+', args.test_tags)):
        parser.error('Only a single named S09 model test can be selected')
    if args.action == 'integrate' and not args.upstream:
        parser.error('integrate requires --upstream')
    if args.action in ('install', 'upgrade', 'integrate', 'serve'):
        with socket.socket() as sock:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('127.0.0.1', args.port))
            except OSError:
                parser.error('Dedicated port is occupied')
    endpoint = dict(host='127.0.0.1', port='5432', user='odoo', password=options.get('db_password'), connect_timeout=4)
    with closing(psycopg2.connect(dbname='postgres', **endpoint)) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute('SELECT system_identifier::text FROM pg_control_system()')
            if cursor.fetchone()[0] != CLUSTER:
                parser.error('PostgreSQL cluster changed')
            cursor.execute('SELECT oid FROM pg_database WHERE datname=%s', (args.db,))
            current = cursor.fetchone()
            if creating:
                if current:
                    parser.error('Database already exists')
                run.mkdir(mode=0o700)
                cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(args.db)), ('UTF8',))
                cursor.execute('SELECT oid FROM pg_database WHERE datname=%s', (args.db,))
                metadata = {'database': args.db, 'oid': cursor.fetchone()[0], 'cluster': CLUSTER,
                            'endpoint': ENDPOINT, 'port': args.port, 'core': CORE_SHA,
                            'created_utc': datetime.now(timezone.utc).isoformat()}
            else:
                metadata = json.loads(marker.read_text())
                if not current or metadata['oid'] != current[0] or metadata['cluster'] != CLUSTER or metadata['port'] != args.port:
                    parser.error('Database identity changed')
    if creating:
        runtime = configparser.ConfigParser(interpolation=None)
        runtime['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
            'db_password': options.get('db_password', ''), 'db_name': args.db,
            'dbfilter': '^' + args.db + '$',
            'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
            'data_dir': str(run / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(args.port),
            'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
            'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
        buffer = io.StringIO()
        runtime.write(buffer)
        private(run / 'odoo.conf', buffer.getvalue())
        metadata['config_sha256'] = sha(run / 'odoo.conf')
        private(marker, json.dumps(metadata, indent=2) + '\n')
    config = run / 'odoo.conf'
    if config.is_symlink() or sha(config) != metadata['config_sha256']:
        parser.error('Runtime config changed')
    deps = STATE / 's00-b-deps'
    policy = run / 'network-policy'
    policy.mkdir(exist_ok=True, mode=0o700)
    sitecustomize = policy / 'sitecustomize.py'
    policy_source = ROOT / 'scripts/s08c_network_policy.py'
    if not sitecustomize.exists():
        private(sitecustomize, policy_source.read_text())
    if sitecustomize.is_symlink() or sha(sitecustomize) != sha(policy_source):
        parser.error('Process egress policy changed')
    env = os.environ.copy()
    env.update({'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + env.get('PATH', ''),
        'FONTCONFIG_FILE': str(deps / 'fonts.conf'), 'XDG_CACHE_HOME': str(deps / 'cache'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONFAULTHANDLER': '1',
        'PYTHONPATH': str(policy) + os.pathsep + str(STATE / 's04-deps'),
        'YDENTAL_S08C_HTTP_PORT': str(args.port),
        'YDENTAL_S09_RUN_DIR': str(run),
        'PGOPTIONS': '-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
    command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin')]
    code = None
    if args.action in ('probe', 'ui_seed', 'race', 'audit'):
        command += ['shell', '-c', str(config), '--no-http']
        source = ROOT / ('scripts/s09_' + args.action + '.py')
        code = "import runpy; runpy.run_path(%r, init_globals={'env': env})" % str(source)
    elif args.action == 'export':
        command += ['i18n', 'export', '-c', str(config), '-o', str(run / 'ydental_exam.pot'), 'ydental_exam']
    else:
        command += ['-c', str(config)]
        if args.action in ('install', 'upgrade', 'integrate'):
            verification = ['ydental_exam_test']
            if args.upstream:
                verification += ['ydental_clinical_test', 'ydental_treatment_test', 'ydental_print_test']
            modules = ','.join(verification if creating else ['ydental_exam'] + verification) if args.tests else 'ydental_exam'
            if args.action == 'integrate':
                modules = 'ydental_clinical_test,ydental_treatment_test,ydental_print_test'
            command += ['-i' if creating or args.action == 'integrate' else '-u', modules,
                '--load-language', 'en_US,zh_CN', '--stop-after-init']
            if args.tests:
                command += ['--test-enable', '--test-tags', args.test_tags or ','.join('/' + module for module in verification)]
            if creating:
                command += ['--with-demo']
    log_path = run / (args.action + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.log')
    with log_path.open('x') as log:
        process = subprocess.Popen(command, cwd=CORE, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.PIPE if code else None, text=bool(code))
        if args.action == 'serve':
            private(run / 'serve.pid', str(process.pid) + '\n')
        if code:
            process.communicate(code)
            status = process.returncode
        else:
            status = process.wait()
    record = {'action': args.action, 'database': args.db, 'oid': metadata['oid'], 'port': args.port,
        'pid': process.pid, 'exit_code': status, 'signal': -status if status < 0 else None,
        'log': log_path.name, 'sha256': sha(log_path),
        'commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'time_utc': datetime.now(timezone.utc).isoformat()}
    with (run / 'actions.jsonl').open('a') as actions:
        actions.write(json.dumps(record) + '\n')
    if status < 0:
        private(run / ('crash-' + str(process.pid) + '.json'), json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    return status


if __name__ == '__main__':
    sys.exit(main())
