"""One-use isolated database and one-process FC2 runner. Run only after #34 checkpoint."""

import configparser
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys

os.umask(0o077)
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261014044700_4f6a8d2c'
NAME = 'ydental_s10_test_20261014152000_fc2a7d31'
SOURCE_RUN = ROOT / '.local' / SOURCE
RUN = ROOT / '.local' / NAME
PORT = 18268
CLUSTER = '7694897083368259627'
BASE = '7ee2c5e091fa1d29bd01e493b07902d2827f4a35'
CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
AUTH = 6171419484
S07_SHA = 'df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b'
SOURCE_MARKER_SHA = 'df8ff92d38499745b6ecfffaecb7eaff739ff29066c243b13b15b3a1bf99bb7b'
SOURCE_CONFIG_SHA = '582f73fdee28cac3d9f63d116bb934e0def3b19fa5ddb7e10c054ba1ef20cb43'
INDEX = ROOT / '.local/s10-native-20261014-6161077626-d14r1/details.json'
POLICY = ROOT / 'scripts/s08c_network_policy.py'
SHELL = ROOT / 'scripts/s10_fc2_shell.py'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exclusive(path, data):
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def endpoint():
    cfg = configparser.ConfigParser(interpolation=None)
    assert cfg.read(CORE / 'odoo.conf')
    opts = cfg['options']
    assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
    return dict(host='127.0.0.1', port=5432, user='odoo', password=opts['db_password'], connect_timeout=5)


def preflight(expect_target=False):
    assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
    assert subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    # The script itself is uncommitted until evidence is finalized, so allow only its
    # own tracked addition and the companion FC2 script/report while HEAD stays fixed.
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == BASE
    assert subprocess.check_output(['git', '-C', str(CORE), 'rev-parse', 'HEAD'], text=True).strip() == CORE_SHA
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD:ydental_settlement/models/ydental_settlement_service.py'], text=True).strip() == 'd4d4363ab2dfdd982606f464e5b66c240744fac6'
    assert digest(ROOT / 'ydental_inventory/models/ydental_inventory_service.py') == S07_SHA
    assert digest(SOURCE_RUN / 'database.json') == SOURCE_MARKER_SHA
    assert digest(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG_SHA
    expected = {x['relative']: x for x in json.loads(INDEX.read_text())['files']}
    src = SOURCE_RUN / 'data/filestore' / SOURCE
    assert len(expected) == 124
    assert set(expected) == {str(p.relative_to(src)) for p in src.rglob('*') if p.is_file()}
    assert all(not (src / rel).is_symlink() and digest(src / rel) == item['sha256'] for rel, item in expected.items())
    ep = endpoint()
    conn = psycopg2.connect(dbname='postgres', **ep)
    conn.set_session(readonly=True)
    with conn.cursor() as cur:
        cur.execute('SELECT system_identifier::text FROM pg_control_system()')
        assert cur.fetchone()[0] == CLUSTER
        cur.execute('SELECT datname, oid FROM pg_database WHERE datname IN (%s,%s)', (SOURCE, NAME))
        oids = dict(cur.fetchall())
        assert oids[SOURCE] == 2100080 and (NAME in oids) == expect_target
        cur.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s', (SOURCE,))
        assert cur.fetchone()[0] == 0
    conn.close()
    conn = psycopg2.connect(dbname=SOURCE, **ep)
    conn.set_session(readonly=True)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM ir_module_module WHERE state='installed'")
        assert cur.fetchone()[0] == 92
        cur.execute("SELECT name,state FROM ir_module_module WHERE name IN ('ydental_settlement','ydental_settlement_test','ydental_treatment_test') ORDER BY name")
        assert cur.fetchall() == [('ydental_settlement', 'installed'), ('ydental_settlement_test', 'installed'), ('ydental_treatment_test', 'uninstalled')]
        for table in ('ydental_access_store', 'ydental_intake_price', 'ydental_inventory_config',
                      'ydental_patient', 'ydental_treatment_fee', 'account_move', 'account_payment',
                      'stock_move', 'mail_mail'):
            cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table)))
            assert cur.fetchone()[0] == 0, table
    conn.close()
    assert RUN.exists() == expect_target
    return ep, expected, oids.get(NAME)


def create():
    ep, expected, _ = preflight(False)
    assert not (ROOT / '.local/s10-fc2-create-attempt.json').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    (RUN / 'data/filestore' / NAME).mkdir(parents=True, mode=0o700)
    exclusive(RUN / 'network-policy/sitecustomize.py', POLICY.read_text())
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    target_fs = RUN / 'data/filestore' / NAME
    for rel, item in expected.items():
        target = target_fs / rel
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (source_fs / rel).open('rb') as inp, os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as out:
            shutil.copyfileobj(inp, out)
        assert digest(target) == item['sha256']
    exclusive(ROOT / '.local/s10-fc2-create-attempt.json', json.dumps({'name': NAME, 'auth': AUTH, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    conn = psycopg2.connect(dbname='postgres', **ep)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(SOURCE)))
    finally:
        conn.close()
    _, _, oid = preflight(True)
    cfg = configparser.ConfigParser(interpolation=None)
    cfg['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo', 'db_password': ep['password'],
        'db_name': NAME, 'dbfilter': '^' + NAME + '$',
        'addons_path': ','.join(str(x) for x in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
        'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
        'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
        'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    buffer = io.StringIO(); cfg.write(buffer)
    exclusive(RUN / 'odoo.conf', buffer.getvalue())
    marker = {'database': NAME, 'oid': oid, 'cluster': CLUSTER, 'source': SOURCE, 'source_oid': 2100080,
              'auth': AUTH, 'base': BASE, 'core': CORE_SHA, 'port': PORT,
              'config_sha256': digest(RUN / 'odoo.conf'), 'policy_sha256': digest(RUN / 'network-policy/sitecustomize.py'),
              'shell_sha256': digest(SHELL)}
    exclusive(RUN / 'database.json', json.dumps(marker, indent=2) + '\n')
    print(json.dumps({'database': NAME, 'oid': oid, 'config_sha256': marker['config_sha256'], 'marker_sha256': digest(RUN / 'database.json')}))


def run():
    ep, _, oid = preflight(True)
    marker = json.loads((RUN / 'database.json').read_text())
    assert marker == {'database': NAME, 'oid': oid, 'cluster': CLUSTER, 'source': SOURCE,
                      'source_oid': 2100080, 'auth': AUTH, 'base': BASE, 'core': CORE_SHA,
                      'port': PORT, 'config_sha256': digest(RUN / 'odoo.conf'),
                      'policy_sha256': digest(RUN / 'network-policy/sitecustomize.py'),
                      'shell_sha256': digest(SHELL)}
    assert not (RUN / 'run-attempt.json').exists()
    command = [str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin'), 'shell', '-c', str(RUN / 'odoo.conf'), '--no-http']
    exclusive(RUN / 'run-attempt.json', json.dumps({'command': command, 'oid': oid, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    environ = os.environ.copy()
    environ.update({'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
                    'YDENTAL_S10_RUN_DIR': str(RUN), 'YDENTAL_S08C_HTTP_PORT': str(PORT),
                    'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                    'PGAPPNAME': 's10_fc2_one_process'})
    log = RUN / 'odoo-fc2.log'
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environ, stdin=subprocess.PIPE,
                                   stdout=output, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        try:
            process.communicate("exec(compile(open('" + str(SHELL) + "').read(),'s10_fc2_shell.py','exec'))\n", timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=5)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': process.returncode, 'signal11': process.returncode in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size, 'database': NAME, 'oid': oid}
    exclusive(RUN / 'run-result.json', json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if result['signal11'] or process.returncode:
        raise RuntimeError('FC2 Odoo failed; STOP')


if __name__ == '__main__':
    {'preflight': lambda: print(json.dumps({'status': 'PASS', 'target': NAME, 'source_oid': 2100080, 'install': 0, 'upgrade': 0})) if preflight(False) else None,
     'create': create, 'run': run}[sys.argv[1]]()
