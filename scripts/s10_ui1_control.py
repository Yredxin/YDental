"""Single use UI1 clone and bounded Odoo process controller.

Run only after the #34 UI1 checkpoint has been published and read back.
"""

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
import time
from urllib.request import urlopen

os.umask(0o077)
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261014044700_4f6a8d2c'
NAME = 'ydental_s10_test_20261015011000_a91c4d70'
SOURCE_RUN = ROOT / '.local' / SOURCE
RUN = ROOT / '.local' / NAME
PORT = 18269
BASE = 'd766b70b0a9c922c809248cdc87e76efa8d5bc23'
AUTH = 6173692695
CHECKPOINT = 6181951592
CLUSTER = '7694897083368259627'
SOURCE_MARKER_SHA = 'df8ff92d38499745b6ecfffaecb7eaff739ff29066c243b13b15b3a1bf99bb7b'
SOURCE_CONFIG_SHA = '582f73fdee28cac3d9f63d116bb934e0def3b19fa5ddb7e10c054ba1ef20cb43'
INDEX = ROOT / '.local/s10-native-20261014-6161077626-d14r1/details.json'
SHELL = ROOT / 'scripts/s10_ui1_prepare.py'
POLICY = ROOT / 'scripts/s08c_network_policy.py'
PYTHON = CORE / '.venv/bin/python'


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


def identity(expect_target=False):
    assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
    assert subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == BASE
    assert subprocess.check_output(['git', '-C', str(CORE), 'rev-parse', 'HEAD'], text=True).strip() == 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
    assert subprocess.check_output(['git', '-C', str(ROOT), 'hash-object', str(ROOT / 'ydental_settlement/models/ydental_settlement_service.py')], text=True).strip() == 'd4d4363ab2dfdd982606f464e5b66c240744fac6'
    assert digest(ROOT / 'ydental_inventory/models/ydental_inventory_service.py') == 'df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b'
    assert digest(SOURCE_RUN / 'database.json') == SOURCE_MARKER_SHA
    assert digest(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG_SHA
    expected = {x['relative']: x for x in json.loads(INDEX.read_text())['files']}
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    assert len(expected) == 124
    assert set(expected) == {str(p.relative_to(source_fs)) for p in source_fs.rglob('*') if p.is_file()}
    assert all(not (source_fs / rel).is_symlink() and digest(source_fs / rel) == item['sha256'] for rel, item in expected.items())
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
        for table in ('ydental_access_store', 'ydental_patient', 'ydental_treatment_fee',
                      'ydental_settlement_payment', 'ydental_settlement_refund', 'ydental_settlement_close',
                      'account_move', 'account_payment', 'mail_mail'):
            cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table)))
            assert cur.fetchone()[0] == 0, table
    conn.close()
    return ep, expected, oids.get(NAME)


def create():
    ep, expected, _ = identity(False)
    assert not RUN.exists()
    assert not (ROOT / '.local/s10-ui1-create-attempt.json').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    target_fs = RUN / 'data/filestore' / NAME
    target_fs.mkdir(parents=True, mode=0o700)
    exclusive(RUN / 'network-policy/sitecustomize.py', POLICY.read_text())
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    for rel, item in expected.items():
        target = target_fs / rel
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (source_fs / rel).open('rb') as src, os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as out:
            shutil.copyfileobj(src, out)
        assert digest(target) == item['sha256']
    exclusive(ROOT / '.local/s10-ui1-create-attempt.json', json.dumps({'name': NAME, 'auth': AUTH, 'checkpoint': CHECKPOINT, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    conn = psycopg2.connect(dbname='postgres', **ep)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(SOURCE)))
    finally:
        conn.close()
    _, _, oid = identity(True)
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
              'auth': AUTH, 'checkpoint': CHECKPOINT, 'base': BASE, 'port': PORT,
              'config_sha256': digest(RUN / 'odoo.conf'), 'policy_sha256': digest(RUN / 'network-policy/sitecustomize.py'),
              'shell_sha256': digest(SHELL)}
    exclusive(RUN / 'database.json', json.dumps(marker, indent=2) + '\n')
    print(json.dumps({'database': NAME, 'oid': oid, 'port': PORT}))


def target():
    _, _, oid = identity(True)
    marker = json.loads((RUN / 'database.json').read_text())
    assert marker['database'] == NAME and marker['oid'] == oid and marker['auth'] == AUTH
    assert marker['config_sha256'] == digest(RUN / 'odoo.conf')
    assert marker['policy_sha256'] == digest(RUN / 'network-policy/sitecustomize.py')
    assert marker['shell_sha256'] == digest(SHELL)
    return oid


def environment():
    e = os.environ.copy()
    e.update({'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
              'YDENTAL_S10_RUN_DIR': str(RUN), 'YDENTAL_S08C_HTTP_PORT': str(PORT),
              'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PGAPPNAME': 's10_ui1_single_registry'})
    return e


def bounded(command, log_name, attempt_name, timeout, stdin=None):
    oid = target()
    exclusive(RUN / attempt_name, json.dumps({'command': command, 'oid': oid, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    log = RUN / log_name
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environment(), stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        try:
            process.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=10)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': process.returncode,
              'signal11': process.returncode in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size}
    exclusive(RUN / (attempt_name + '.result'), json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if result['signal11'] or process.returncode:
        raise RuntimeError('Odoo process failed; STOP')


def prepare():
    command = [str(PYTHON), str(CORE / 'odoo-bin'), 'shell', '-c', str(RUN / 'odoo.conf'), '--no-http']
    stdin = "exec(compile(open('" + str(SHELL) + "').read(),'s10_ui1_prepare.py','exec'))\n"
    bounded(command, 'odoo-prepare.log', 'prepare-attempt.json', 600, stdin)


def upgrade():
    assert (RUN / 'baseline-proved.json').exists()
    command = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(RUN / 'odoo.conf'), '-u', 'ydental_settlement',
               '--stop-after-init', '--no-http', '--test-disable']
    bounded(command, 'odoo-upgrade.log', 'upgrade-attempt.json', 600)


def serve(stage):
    assert stage in ('before', 'after')
    if stage == 'before':
        assert not (RUN / 'upgrade-attempt.json').exists()
    else:
        assert (RUN / 'upgrade-attempt.json.result').exists()
    marker = RUN / ('http-' + stage + '.attempt.json')
    target()
    exclusive(marker, json.dumps({'stage': stage, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    command = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(RUN / 'odoo.conf')]
    log = RUN / ('odoo-http-' + stage + '.log')
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environment(), stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        exclusive(RUN / ('http-' + stage + '.pid'), str(process.pid) + '\n')
        try:
            code = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=10)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': code,
              'signal11': code in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size}
    exclusive(RUN / ('http-' + stage + '.result.json'), json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


def wait_http():
    target()
    start = time.monotonic()
    while time.monotonic() - start < 180:
        try:
            with urlopen('http://127.0.0.1:' + str(PORT) + '/web/login', timeout=3) as r:
                if r.status == 200:
                    print('HTTP_READY'); return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError('HTTP startup timeout; STOP')


def stop(stage):
    assert stage in ('before', 'after')
    pid = int((RUN / ('http-' + stage + '.pid')).read_text().strip())
    cmdline = Path('/proc/' + str(pid) + '/cmdline').read_bytes().split(b'\0')
    assert os.fsencode(str(RUN / 'odoo.conf')) in cmdline and os.fsencode(str(CORE / 'odoo-bin')) in cmdline
    os.kill(pid, signal.SIGINT)
    for _ in range(50):
        if (RUN / ('http-' + stage + '.result.json')).exists():
            result = json.loads((RUN / ('http-' + stage + '.result.json')).read_text())
            assert not result['signal11'], result
            print(json.dumps(result)); return
        time.sleep(.2)
    raise RuntimeError('HTTP process did not exit in 10 seconds; STOP')


if __name__ == '__main__':
    {'preflight': lambda: print(json.dumps({'status': 'SIMULATED_PASS', 'source_oid': 2100080})) if identity(False) else None,
     'create': create, 'prepare': prepare, 'upgrade': upgrade,
     'serve-before': lambda: serve('before'), 'serve-after': lambda: serve('after'),
     'wait-http': wait_http, 'stop-before': lambda: stop('before'), 'stop-after': lambda: stop('after')}[sys.argv[1]]()
