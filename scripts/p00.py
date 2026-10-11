"""Run P00 exclusively on newly created, locally recorded test databases."""

import argparse
import configparser
from contextlib import closing
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
STATE = REPO / '.local'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'upgrade', 'test', 'evaluate', 'serve'])
    parser.add_argument('--db', required=True)
    parser.add_argument('--core', type=Path, default=REPO.parent)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--port', type=int, default=8079)
    args = parser.parse_args()
    if not re.fullmatch(r'ydental_p00_test_[a-z0-9_]{1,40}', args.db):
        parser.error('Database must match ydental_p00_test_[a-z0-9_]{1,40}')
    if not 1024 <= args.port <= 65535:
        parser.error('Choose an unprivileged HTTP port between 1024 and 65535')
    core = args.core.resolve()
    python = core / '.venv/bin/python'
    if not python.is_file() or not (core / 'odoo-bin').is_file():
        parser.error('Expected an existing Odoo checkout and .venv in --core')
    version = subprocess.check_output([str(python), str(core / 'odoo-bin'), '--version'], cwd=core, text=True)
    if version.strip() != 'Odoo Server 20.0':
        parser.error('Requires Odoo Server 20.0; no automatic version switch')
    source = configparser.ConfigParser(interpolation=None)
    if not source.read(args.config or core / 'odoo.conf'):
        parser.error('Missing private source config; copy config/odoo.conf.example and edit locally')
    options = source['options']
    db_options = {
        key: options[name] for key, name in {
            'host': 'db_host', 'port': 'db_port', 'user': 'db_user',
            'password': 'db_password', 'sslmode': 'db_sslmode',
        }.items() if options.get(name) and options[name] != 'False'
    }
    run_dir = STATE / args.db
    marker = run_dir / 'database.json'
    creating = args.action in ('install', 'evaluate')
    if creating and run_dir.exists():
        parser.error('Local run already exists; choose a new unique database name')
    if not creating and not marker.is_file():
        parser.error('Database has not been created by this runner; refusing to operate')
    if args.action in ('test', 'serve'):
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('127.0.0.1', args.port))
            except OSError:
                parser.error('HTTP port is occupied; choose another --port, leave services running')
    with closing(psycopg2.connect(dbname='postgres', **db_options)) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute('SELECT oid FROM pg_database WHERE datname = %s', (args.db,))
            existing = cursor.fetchone()
            if creating:
                if existing:
                    parser.error('Database already exists; refusing to initialize or overwrite it')
                run_dir.mkdir(parents=True, mode=0o700)
                cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(
                    sql.Identifier(args.db),
                ), ('UTF8',))
                cursor.execute('SELECT oid FROM pg_database WHERE datname = %s', (args.db,))
                database_oid = cursor.fetchone()[0]
                metadata = {
                    'database': args.db, 'oid': database_oid,
                    'endpoint': {key: db_options.get(key) for key in ('host', 'port', 'user')},
                    'kind': args.action,
                }
                marker.write_text(json.dumps(metadata, indent=2) + '\n')
            else:
                metadata = json.loads(marker.read_text())
                endpoint = {key: db_options.get(key) for key in ('host', 'port', 'user')}
                if (not existing or existing[0] != metadata['oid']
                        or metadata['database'] != args.db or metadata['endpoint'] != endpoint):
                    parser.error('Database identity changed; refusing to operate')
                if metadata['kind'] != 'install':
                    parser.error('Native evaluation database is not a YDental application database')
    runtime = configparser.ConfigParser(interpolation=None)
    runtime['options'] = {
        name: options[name] for name in (
            'db_host', 'db_port', 'db_user', 'db_password', 'db_sslmode',
        ) if options.get(name)
    }
    runtime['options'].update({
        'db_name': args.db, 'dbfilter': '^' + args.db + '$',
        'addons_path': str(core / 'addons') + ',' + str(REPO),
        'data_dir': str(run_dir / 'data'), 'http_interface': '127.0.0.1',
        'http_port': str(args.port), 'list_db': 'False', 'workers': '0',
        'max_cron_threads': '0', 'admin_passwd': secrets.token_urlsafe(32),
        'smtp_server': '127.0.0.1', 'smtp_port': '1',
    })
    config = run_dir / 'odoo.conf'
    with os.fdopen(os.open(config, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as handle:
        runtime.write(handle)
    command = [str(python), str(core / 'odoo-bin'), '-c', str(config)]
    if args.action == 'serve':
        print('Local access: http://127.0.0.1:%s/odoo (database %s)' % (args.port, args.db), flush=True)
        print('Private demo credentials: %s' % (run_dir / 'access.json'), flush=True)
        return subprocess.call(command, cwd=core)
    command += ['--stop-after-init']
    if args.action == 'install':
        command += ['-i', 'ydental_base', '--with-demo', '--no-http']
    elif args.action == 'evaluate':
        command += ['-i', 'hr,stock,account', '--no-http']
    elif args.action == 'upgrade':
        command += ['-u', 'ydental_base', '--no-http']
    else:
        command += ['-u', 'ydental_base', '--test-enable', '--test-tags', '/ydental_base']
    log = run_dir / (args.action + '.log')
    print('Database: %s; action: %s; private log: %s' % (args.db, args.action, log), flush=True)
    with log.open('w') as handle:
        result = subprocess.call(command, cwd=core, stdout=handle, stderr=subprocess.STDOUT)
    print('Odoo exit: %s' % result, flush=True)
    if args.action == 'test' and not result:
        summary = re.search(r'(\d+) failed, (\d+) error\(s\) of (\d+) tests', log.read_text())
        if not summary or tuple(map(int, summary.groups()[:2])) != (0, 0) or int(summary[3]) < 5:
            print('Missing or unsuccessful minimum test summary; inspect the private log', flush=True)
            return 1
        print('Verified minimum test summary: %s' % summary[0], flush=True)
    if result or args.action != 'install':
        return result
    access = {
        'login': 'ydental_p00_preview@example.invalid',
        'password': secrets.token_urlsafe(24),
    }
    access_path = run_dir / 'access.json'
    with os.fdopen(os.open(access_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
        json.dump(access, handle)
    # Provision only synthetic preview users in the database just created here.
    code = '''
import json
from pathlib import Path
from odoo import Command
access = json.loads(Path(%r).read_text())
env.ref('base.user_admin').write({'password': %r})
env['res.users'].with_context(no_reset_password=True).create({
    'name': 'YDental P00 Synthetic Preview',
    'login': access['login'], 'password': access['password'],
    'email': access['login'],
    'group_ids': [Command.set([env.ref('ydental_base.ydental_base_group_user').id])],
})
env.cr.commit()
''' % (str(access_path), secrets.token_urlsafe(32))
    with (run_dir / 'provision.log').open('w') as handle:
        result = subprocess.run(
            [str(python), str(core / 'odoo-bin'), 'shell', '-c', str(config), '--no-http'],
            cwd=core, input=code, text=True, stdout=handle, stderr=subprocess.STDOUT,
        ).returncode
    print('Synthetic preview provisioning exit: %s' % result, flush=True)
    return result


if __name__ == '__main__':
    sys.exit(main())
