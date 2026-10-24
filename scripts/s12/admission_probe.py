#!/usr/bin/env python3
"""Read only the admitted synthetic target; never issue scope or start Odoo.

The explicit provider is read privately for its database object only. All DB
statements are SELECTs in one READ ONLY / REPEATABLE READ transaction. The
receipt records observed facts, not independent approval or business completion.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local' / 's12'
TARGET = 'ydental_s11_synth_20261023_01'
OID = 2171423
CLUSTER = '7694897083368259627'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s12-documents-reports-r1'
PLAN = 'YD-S12-DOCUMENTS-REPORTS-V1'


def read_provider(path):
    path = path.absolute()
    if path not in (ROOT / '.local/s11/new-target-runtime.json', PRIVATE / 'runtime.json'):
        raise RuntimeError('Only the explicitly authorized project DB provider is allowed.')
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or
            info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600):
        raise RuntimeError('The DB provider must be an owned regular mode-0600 file.')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'r') as stream:
        value = json.load(stream)
    database = value['database']
    expected = {'name': TARGET, 'expected_oid': OID,
                'expected_cluster_ref': CLUSTER, 'host': '127.0.0.1', 'port': 5432, 'user': TARGET}
    if any(database.get(key) != item for key, item in expected.items()):
        raise RuntimeError('Provider target identity differs from the authorized synthetic target.')
    if not isinstance(database.get('password'), str) or not database['password']:
        raise RuntimeError('The authorized private DB provider has no usable credential.')
    return database


def write_receipt(path, value):
    path = path.absolute()
    if PRIVATE not in path.parents or '..' in path.parts:
        raise RuntimeError('Output must be inside the S12 private record directory.')
    for directory in reversed([p for p in path.parents if PRIVATE == p or PRIVATE in p.parents]):
        directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise RuntimeError('S12 evidence directories must be owned and private.')
    raw = (json.dumps(value, indent=2, sort_keys=True, default=str) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def probe(provider, output, operator):
    result = {'plan_id': PLAN, 'status': 'INCOMPLETE_READONLY_PROBE', 'operator': operator,
              'started_at_utc': dt.datetime.now(dt.UTC).isoformat(),
              'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'provider_path': str(provider.relative_to(ROOT)),
              'candidate_commit': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
              'core_commit': git('-C', str(ROOT.parent), 'rev-parse', 'HEAD'),
              'independent_acceptance': False, 'database_write_performed': False,
              'other_database_connections_performed': False,
              'credentials_or_authentication_hashes_selected': False,
              'service_started': False, 'scope_issued': False}
    if result['branch'] != BRANCH or result['core_commit'] != CORE:
        raise RuntimeError('Current branch or locked Odoo core mismatch.')
    cfg = read_provider(provider)
    connection = None
    try:
        connection = psycopg2.connect(dbname=cfg['name'], host=cfg['host'], port=cfg['port'],
            user=cfg['user'], password=cfg['password'], connect_timeout=5,
            options='-c default_transaction_read_only=on -c statement_timeout=15000 -c TimeZone=UTC')
        connection.set_session(readonly=True, isolation_level='REPEATABLE READ')
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""SELECT current_database() AS name, current_user AS role,
                (SELECT oid FROM pg_database WHERE datname=current_database()) AS oid,
                (pg_control_system()).system_identifier::text AS cluster_ref,
                inet_server_addr()::text AS server_addr, inet_server_port() AS server_port,
                pg_backend_pid() AS backend_pid, current_setting('transaction_read_only') AS read_only,
                current_setting('transaction_isolation') AS isolation""")
            identity = dict(cursor.fetchone())
            result['identity'] = identity
            expected = {'name': TARGET, 'role': TARGET, 'oid': OID, 'cluster_ref': CLUSTER,
                        'server_port': 5432, 'read_only': 'on', 'isolation': 'repeatable read'}
            if any(identity.get(key) != value for key, value in expected.items()):
                raise RuntimeError('Live target identity or read-only transaction mismatch.')
            cursor.execute("""SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication,
                rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname=current_user""")
            role = dict(cursor.fetchone())
            result['role'] = role
            if any(role[key] for key in ('rolsuper', 'rolcreatedb', 'rolcreaterole', 'rolreplication', 'rolbypassrls')):
                raise RuntimeError('Runtime role has disallowed cluster privileges.')
            if not role['rolcanlogin']:
                raise RuntimeError('Runtime role cannot log in.')
            cursor.execute("""SELECT d.datname=current_database() AS owns_only_target,
                count(*) AS owned_database_count FROM pg_database d
                JOIN pg_roles r ON r.oid=d.datdba WHERE r.rolname=current_user
                GROUP BY d.datname=current_database()""")
            ownership = [dict(row) for row in cursor.fetchall()]
            result['database_ownership'] = ownership
            if ownership != [{'owns_only_target': True, 'owned_database_count': 1}]:
                raise RuntimeError('Runtime role owns databases outside the authorized target.')
            cursor.execute("""SELECT has_database_privilege(current_user,current_database(),'CONNECT') AS connect,
                has_database_privilege(current_user,current_database(),'CREATE') AS database_create,
                has_schema_privilege(current_user,'public','USAGE') AS schema_usage,
                has_schema_privilege(current_user,'public','CREATE') AS schema_create""")
            result['target_grants'] = dict(cursor.fetchone())
            cursor.execute("""SELECT count(*) AS object_count,
                count(*) FILTER (WHERE pg_has_role(current_user,c.relowner,'USAGE')) AS owned_or_owner_role_count
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='public' AND c.relkind IN ('r','p','S','v','m')""")
            result['target_object_ownership'] = dict(cursor.fetchone())
            cursor.execute("""SELECT id,company_id,ydental_timezone,active
                FROM ydental_access_store ORDER BY id""")
            result['stores'] = [dict(row) for row in cursor.fetchall()]
            cursor.execute('SELECT id FROM res_company ORDER BY id')
            result['company_ids'] = [row['id'] for row in cursor.fetchall()]
            cursor.execute("SELECT name,state,latest_version FROM ir_module_module WHERE state IN ('installed','to install','to upgrade','to remove') ORDER BY name")
            result['modules'] = [dict(row) for row in cursor.fetchall()]
            if any(row['state'] != 'installed' for row in result['modules']):
                raise RuntimeError('Target has pending native module actions.')
            cursor.execute('SELECT count(*) AS count FROM ir_mail_server')
            result['smtp_servers'] = cursor.fetchone()['count']
            cursor.execute("""SELECT id,ydental_store_id,ydental_enabled,ydental_channel_mode
                FROM ydental_followup_policy ORDER BY id""")
            result['notification_policies'] = [dict(row) for row in cursor.fetchall()]
            cursor.execute("""SELECT key, CASE WHEN key='ydental_followup_test.local_sink_enabled'
                THEN lower(COALESCE(value,'')) IN ('true','1','yes')
                ELSE COALESCE(value,'')<>'' END AS configured
                FROM ir_config_parameter WHERE key IN
                ('ydental_followup_test.local_sink_enabled','ydental_followup.callback_secret') ORDER BY key""")
            result['outbound_parameter_flags'] = [dict(row) for row in cursor.fetchall()]
            if (result['smtp_servers'] or
                    any(row['ydental_enabled'] or row['ydental_channel_mode'] != 'disabled'
                        for row in result['notification_policies']) or
                    any(row['configured'] for row in result['outbound_parameter_flags'])):
                raise RuntimeError('The disabled outbound boundary is not confirmed.')
            cursor.execute("""SELECT count(*) AS count FROM res_groups_users_rel rel
                JOIN ir_model_data d ON d.model='res.groups' AND d.res_id=rel.gid
                WHERE d.module='ydental_s11_clock_test'""")
            result['s11_clock_memberships_including_inactive'] = cursor.fetchone()['count']
            if result['s11_clock_memberships_including_inactive']:
                raise RuntimeError('Legacy session-clock membership is still present.')
        result['status'] = 'READONLY_TARGET_IDENTITY_AND_GRANTS_OBSERVED'
    except Exception as error:
        result['status'] = 'READONLY_PROBE_FAILED_NO_RUNTIME_ADMISSION'
        result['error_class'] = type(error).__name__
        # Database exception text may contain configuration; preserve only its
        # class and stable SQLSTATE, not arbitrary server/connection messages.
        result['sqlstate'] = getattr(error, 'pgcode', None)
        if isinstance(error, RuntimeError):
            result['safe_error'] = str(error)
    finally:
        if connection is not None:
            connection.rollback()
            result['rollback_idle'] = connection.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            connection.close()
            result['connection_closed'] = bool(connection.closed)
        result['finished_at_utc'] = dt.datetime.now(dt.UTC).isoformat()
    digest = write_receipt(output, result)
    print(json.dumps({'status': result['status'], 'output': str(output.relative_to(ROOT)),
                      'sha256': digest, 'identity': result.get('identity'), 'role': result.get('role'),
                      'error_class': result.get('error_class'), 'safe_error': result.get('safe_error')}, sort_keys=True))
    return 0 if result['status'] == 'READONLY_TARGET_IDENTITY_AND_GRANTS_OBSERVED' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--operator', required=True)
    args = parser.parse_args()
    return probe(args.provider.absolute(), args.output.absolute(), args.operator)


if __name__ == '__main__':
    raise SystemExit(main())
