"""S06A runner for fresh, locally recorded databases on the approved endpoint.

No drop/reset operation is provided. Existing databases are never adopted.
Private source credentials are read without changing the source configuration.
"""
import argparse
import configparser
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import hashlib
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


REPO = Path(__file__).resolve().parents[1]
CORE = REPO.parent
STATE = REPO / '.local'
CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
# Cluster identity is rechecked against the maintenance catalog on every action.
ENDPOINT = {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
CLUSTER = '7694897083368259627'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_private(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
        handle.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'upgrade', 'probe', 'serve', 'export'])
    parser.add_argument('--db', required=True)
    parser.add_argument('--config', type=Path, default=CORE / 'odoo.conf')
    parser.add_argument('--port', type=int, default=18116)
    args = parser.parse_args()
    if not re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', args.db):
        parser.error('Database must be a new ydental_s06a_test_YYYYMMDDHHMMSS_8hex database')
    if not 18000 <= args.port <= 18999:
        parser.error('S06A HTTP port must be in the isolated range 18000..18999')
    source = configparser.ConfigParser(interpolation=None)
    if not source.read(args.config) or not source.has_section('options'):
        parser.error('Missing private source config')
    options = source['options']
    endpoint = {key: options.get(name) for key, name in (
        ('host', 'db_host'), ('port', 'db_port'), ('user', 'db_user'),
    )}
    if endpoint != ENDPOINT:
        parser.error('Endpoint is not the approved 127.0.0.1:5432/odoo; no connection attempted')
    if subprocess.check_output(['git', '-C', str(CORE), 'rev-parse', 'HEAD'], text=True).strip() != CORE_SHA:
        parser.error('Core SHA changed; no version switch allowed')
    tested_commit = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain', '--',
                               'ydental_queue', 'ydental_queue_test', 'scripts/s06a*', 'scripts/test_s06a_guard.py'], text=True):
        parser.error('Commit S06A implementation and verification scripts before running')
    run = STATE / args.db
    if run.is_symlink():
        parser.error('Symlink run directory refused')
    marker = run / 'database.json'
    creating = args.action == 'install'
    if creating and run.exists():
        parser.error('Run already exists; choose a fresh database, no overwrite')
    if not creating and (not marker.is_file() or marker.is_symlink()):
        parser.error('No local creation record; existing databases cannot be adopted')
    metadata = None if creating else json.loads(marker.read_text())
    if metadata and (metadata.get('database') != args.db or metadata.get('endpoint') != ENDPOINT
                     or metadata.get('cluster') != CLUSTER):
        parser.error('Creation record identity mismatch')
    if metadata and metadata.get('port') != args.port:
        parser.error('Port differs from creation record')
    if metadata and (not (run / 'odoo.conf').is_file() or (run / 'odoo.conf').is_symlink()
                     or digest(run / 'odoo.conf') != metadata.get('config_sha256')):
        parser.error('Runtime config changed; refusing to run')
    phone_dependency = STATE / 's04-deps/phonenumbers/__init__.py'
    if not phone_dependency.is_file():
        parser.error('Missing process-local phonenumbers dependency')
    deps = STATE / 's00-b-deps'
    env = os.environ.copy()
    env.update({
        'PATH': str(deps / 'wkhtmltox/usr/local/bin') + os.pathsep + env.get('PATH', ''),
        'FONTCONFIG_FILE': str(deps / 'fonts.conf'),
        'XDG_CACHE_HOME': str(deps / 'cache'),
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONPATH': str(STATE / 's04-deps'),
        'YDENTAL_S06A_RUN_DIR': str(run),
        'YDENTAL_S06A_HTTP_PORT': str(args.port),
    })
    if not all((deps / name).is_file() for name in (
        'fonts.conf', 'fonts/NotoSansCJKsc-Regular.otf', 'wkhtmltox/usr/local/bin/wkhtmltopdf',
    )):
        parser.error('Missing existing process-local PDF assets; dependency installation is not authorized')
    # Serialize this runner, including serve, so a module update cannot race a preview.
    STATE.mkdir(exist_ok=True, mode=0o700)
    with (STATE / ('s06a-runner-' + args.db + '.lock')).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another S06A action is running; no service stopped')
        if args.action in ('install', 'upgrade', 'serve'):
            with socket.socket() as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind(('127.0.0.1', args.port))
                except OSError:
                    parser.error('Port occupied; refusing to stop or reuse a service')
        connection = dict(endpoint, password=options.get('db_password'), connect_timeout=3)
        with closing(psycopg2.connect(dbname='postgres', **connection)) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute('SELECT system_identifier::text FROM pg_control_system()')
                if cursor.fetchone()[0] != CLUSTER:
                    parser.error('PostgreSQL cluster identity changed; refusing database operations')
                cursor.execute('SELECT oid FROM pg_database WHERE datname = %s', (args.db,))
                existing = cursor.fetchone()
                if creating:
                    if existing:
                        parser.error('Database already exists; no overwrite/adoption')
                    run.mkdir(mode=0o700)
                    cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(
                        sql.Identifier(args.db)), ('UTF8',))
                    cursor.execute('SELECT oid FROM pg_database WHERE datname = %s', (args.db,))
                    metadata = {
                        'database': args.db, 'oid': cursor.fetchone()[0], 'endpoint': ENDPOINT,
                        'cluster': CLUSTER, 'port': args.port, 'core': CORE_SHA,
                        'created_utc': datetime.now(timezone.utc).isoformat(),
                    }
                elif not existing or existing[0] != metadata['oid']:
                    parser.error('Database OID changed or absent; refusing to operate')
        runtime = configparser.ConfigParser(interpolation=None)
        runtime['options'] = {
            'db_host': ENDPOINT['host'], 'db_port': ENDPOINT['port'], 'db_user': ENDPOINT['user'],
            'db_password': options.get('db_password', ''),
            'db_name': args.db, 'dbfilter': '^' + args.db + '$',
            'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', REPO)),
            'data_dir': str(run / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(args.port),
            'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
            'admin_passwd': secrets.token_urlsafe(32),
            'smtp_server': '127.0.0.1', 'smtp_port': '1',
        }
        config = run / 'odoo.conf'
        if creating:
            import io
            output = io.StringIO()
            runtime.write(output)
            write_private(config, output.getvalue())
            metadata['config_sha256'] = digest(config)
            write_private(marker, json.dumps(metadata, indent=2) + '\n')
        network_source = REPO / 'scripts/s06a_network_policy.py'
        policy_dir = run / 'network-policy'
        if not policy_dir.exists():
            policy_dir.mkdir(mode=0o700)
            write_private(policy_dir / 'sitecustomize.py', network_source.read_text())
        if policy_dir.is_symlink() or (policy_dir / 'sitecustomize.py').is_symlink() or digest(
            policy_dir / 'sitecustomize.py'
        ) != digest(network_source):
            parser.error('Process egress policy differs; refusing to run')
        env['PYTHONPATH'] = str(policy_dir) + os.pathsep + env.get('PYTHONPATH', '')
        command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin')]
        if args.action == 'probe':
            command += ['shell', '-c', str(config), '--no-http']
            code = "import runpy; runpy.run_path(%r, init_globals={'env': env})" % str(REPO / 'scripts/s06a_probe.py')
        else:
            command += ['-c', str(config)]
            code = None
        if args.action in ('install', 'upgrade'):
            command += ['-i' if creating else '-u', 'ydental_queue,ydental_queue_test', '--load-language', 'en_US,zh_CN',
                        '--test-enable', '--test-tags', '/ydental_queue_test', '--stop-after-init']
            if creating:
                command += ['--with-demo']
        elif args.action == 'export':
            command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin'),
                       'i18n', 'export', '-c', str(config), '-o', str(run / 'ydental_queue.pot'),
                       'ydental_queue']
        if args.action == 'serve':
            print('Preview: http://127.0.0.1:%s/odoo; private access: %s' % (
                args.port, run / 'access.json'), flush=True)
            with (run / 'serve.log').open('a') as log:
                pid_path = run / 'serve.pid'
                if pid_path.exists():
                    parser.error('Preview PID record already exists; inspect it without stopping other services')
                process = subprocess.Popen(command, cwd=CORE, env=env, stdout=log, stderr=subprocess.STDOUT)
                write_private(pid_path, str(process.pid) + '\n')
                try:
                    return process.wait()
                finally:
                    if process.poll() is not None:
                        pid_path.unlink(missing_ok=True)
        log_path = run / (args.action + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.log')
        print('Action %s; database %s; private log %s' % (args.action, args.db, log_path), flush=True)
        with log_path.open('x') as log:
            result = subprocess.run(command, input=code, text=True, cwd=CORE, env=env,
                                    stdout=log, stderr=subprocess.STDOUT).returncode
        entry = {'action': args.action, 'exit_code': result, 'log': log_path.name,
                 'log_sha256': digest(log_path), 'time_utc': datetime.now(timezone.utc).isoformat(),
                 'tested_commit': tested_commit}
        if args.action in ('install', 'upgrade'):
            match = re.search(r'(\d+) failed, (\d+) error\(s\) of (\d+) tests', log_path.read_text())
            entry['tests'] = list(map(int, match.groups())) if match else None
            if not match or entry['tests'][:2] != [0, 0] or entry['tests'][2] < 10:
                result = result or 1
                entry['verification_exit'] = result
        if args.action == 'probe' and '"result": "PASS", "races":' not in log_path.read_text():
            result = result or 1
            entry['verification_exit'] = result
        with (run / 'actions.jsonl').open('a') as actions:
            actions.write(json.dumps(entry) + '\n')
        print(json.dumps(entry), flush=True)
        return result


if __name__ == '__main__':
    sys.exit(main())
