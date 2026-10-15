"""Single use W1 clone and bounded Odoo process controller.

Run only after the #34 E2E-W1 checkpoint has been published and read back.
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
from s10_e2e_w1_contract import build_marker, check_fixed_adapter, validate_marker
from s10_e2e_w1_evidence import read_complete, write_once

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261014044700_4f6a8d2c'
NAME = 'ydental_s10_test_20261015051000_e2e1a7b4'
SOURCE_RUN = ROOT / '.local' / SOURCE
RUN = ROOT / '.local' / NAME
PORT = 18277
BASE = '7efa4e25583b667cc0de22d115b54d67d0d10a3b'
AUTH = 6184776579
CHECKPOINT = 'S10-E2E-W1'
CLUSTER = '7694897083368259627'
SOURCE_MARKER_SHA = 'df8ff92d38499745b6ecfffaecb7eaff739ff29066c243b13b15b3a1bf99bb7b'
SOURCE_CONFIG_SHA = '582f73fdee28cac3d9f63d116bb934e0def3b19fa5ddb7e10c054ba1ef20cb43'
INDEX = ROOT / '.local/s10-native-20261014-6161077626-d14r1/details.json'
SHELL = ROOT / 'scripts/s10_e2e_w1_prepare.py'
CONTROL = ROOT / 'scripts/s10_e2e_w1_control.py'
BROWSER = ROOT / 'scripts/s10_e2e_w1_browser.py'
CONTRACT = ROOT / 'scripts/s10_e2e_w1_contract.py'
ADAPTER = ROOT / 'ydental_settlement_test/__init__.py'
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


def core_head():
    actual = subprocess.check_output(['git', '-C', str(CORE), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
    return actual


def identity(expect_target=False):
    assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
    assert subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == BASE
    core_head()
    assert subprocess.check_output(['git', '-C', str(ROOT), 'hash-object', str(ROOT / 'ydental_settlement/models/ydental_settlement_service.py')], text=True).strip() == 'd4d4363ab2dfdd982606f464e5b66c240744fac6'
    assert digest(ROOT / 'ydental_inventory/models/ydental_inventory_service.py') == 'df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b'
    assert digest(SOURCE_RUN / 'database.json') == SOURCE_MARKER_SHA
    assert digest(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG_SHA
    index = json.loads(INDEX.read_text())
    expected = {x['relative']: x for x in index['files']}
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
        cur.execute("SELECT name FROM ir_module_module WHERE state='installed' ORDER BY name")
        # The frozen D1.4 file inventory predates installation of the fixed
        # synthetic S10 adapter; its exact 91 names plus that adapter are 92.
        assert sorted(row[0] for row in cur.fetchall()) == sorted(index['source_modules'] + ['ydental_settlement_test'])
        cur.execute("SELECT name,state FROM ir_module_module WHERE name IN ('ydental_settlement','ydental_settlement_test','ydental_treatment_test') ORDER BY name")
        assert cur.fetchall() == [('ydental_settlement', 'installed'), ('ydental_settlement_test', 'installed'), ('ydental_treatment_test', 'uninstalled')]
        for table in ('ydental_access_store', 'ydental_patient', 'ydental_intake_task',
                      'ydental_queue_entry', 'ydental_treatment_event', 'ydental_treatment_fee',
                      'ydental_exam_result', 'ydental_inventory_event', 'stock_move',
                      'ydental_settlement_source', 'ydental_settlement_receipt',
                      'ydental_settlement_payment', 'ydental_settlement_refund', 'ydental_settlement_close',
                      'account_move', 'account_payment', 'account_partial_reconcile', 'mail_mail'):
            cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table)))
            assert cur.fetchone()[0] == 0, table
        cur.execute('SELECT store_fname, checksum FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
        for rel, checksum in cur.fetchall():
            item = source_fs / rel
            assert item.is_file() and hashlib.sha1(item.read_bytes()).hexdigest() == checksum, rel
    conn.close()
    return ep, expected, oids.get(NAME)


def create():
    ep, expected, _ = identity(False)
    assert not RUN.exists()
    assert not (ROOT / '.local/s10-e2e-w1-create-attempt.json').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    target_fs = RUN / 'data/filestore' / NAME
    target_fs.mkdir(parents=True, mode=0o700)
    exclusive(RUN / 'network-policy/sitecustomize.py', POLICY.read_text())
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    for rel, item in expected.items():
        copied_file = target_fs / rel
        copied_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (source_fs / rel).open('rb') as src, os.fdopen(os.open(copied_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as out:
            shutil.copyfileobj(src, out)
        assert digest(copied_file) == item['sha256']
    exclusive(ROOT / '.local/s10-e2e-w1-create-attempt.json', json.dumps({'name': NAME, 'auth': AUTH, 'checkpoint': CHECKPOINT, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    conn = psycopg2.connect(dbname='postgres', **ep)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(SOURCE)))
    finally:
        conn.close()
    write_once(RUN / 'create-sql-committed.json', {'database': NAME, 'phase': 'CREATE_SUCCEEDED'})
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
    marker = build_marker(database=NAME, oid=oid, cluster=CLUSTER,
        actual_core=core_head(), config=RUN / 'odoo.conf', run=RUN,
        auth=AUTH, base=BASE, port=PORT, source=SOURCE, source_oid=2100080,
        policy=RUN / 'network-policy/sitecustomize.py', prepare=SHELL,
        control=CONTROL, browser=BROWSER, contract=CONTRACT)
    exclusive(RUN / 'database.json', json.dumps(marker, indent=2) + '\n')
    target()
    write_once(RUN / 'create-complete.json', {'database': NAME, 'oid': oid,
        'phase': 'VERIFIED', 'config_sha256': digest(RUN / 'odoo.conf')})
    print(json.dumps({'database': NAME, 'oid': oid, 'port': PORT}))


def target():
    creation = read_complete(RUN / 'create-sql-committed.json')
    assert creation == {'database': NAME, 'phase': 'CREATE_SUCCEEDED'}
    _, _, oid = identity(True)
    marker = json.loads((RUN / 'database.json').read_text())
    validate_marker(marker=marker, database=NAME, oid=oid, cluster=CLUSTER,
        actual_core=core_head(), config=RUN / 'odoo.conf', run=RUN,
        auth=AUTH, base=BASE, port=PORT, source=SOURCE, source_oid=2100080,
        policy=RUN / 'network-policy/sitecustomize.py', prepare=SHELL,
        control=CONTROL, browser=BROWSER, contract=CONTRACT)
    check_fixed_adapter(adapter_source=ADAPTER, run=RUN, database=NAME, oid=oid)
    return oid


def verified_target():
    oid = target()
    assert read_complete(RUN / 'create-complete.json') == {
        'database': NAME, 'oid': oid, 'phase': 'VERIFIED',
        'config_sha256': digest(RUN / 'odoo.conf')}
    return oid


def environment():
    e = os.environ.copy()
    e.update({'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
              'YDENTAL_S10_RUN_DIR': str(RUN), 'YDENTAL_S08C_HTTP_PORT': str(PORT),
              'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PGAPPNAME': 's10_e2e_w1_single_registry'})
    return e


def bounded(command, log_name, attempt_name, timeout, stdin=None):
    oid = verified_target()
    exclusive(RUN / attempt_name, json.dumps({'command': command, 'oid': oid, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    log = RUN / log_name
    timed_out = False
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environment(), stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        try:
            process.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=10)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': process.returncode, 'timed_out': timed_out,
              'oid': oid, 'config_sha256': digest(RUN / 'odoo.conf'),
              'signal11': process.returncode in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size}
    write_once(RUN / (attempt_name + '.result'), result)
    print(json.dumps(result))
    if result['signal11'] or timed_out or process.returncode:
        raise RuntimeError('Odoo process failed; STOP')


def successful_result(name, *, allowed_exits=(0,)):
    """A file's presence alone is never proof that a prior stage completed."""
    result = read_complete(RUN / name)
    oid = verified_target()
    assert result['oid'] == oid and result['config_sha256'] == digest(RUN / 'odoo.conf')
    assert result['exit_code'] in allowed_exits and result['signal11'] is False
    assert result['timed_out'] is False and result['log_bytes'] >= 0
    assert isinstance(result['log_sha256'], str) and len(result['log_sha256']) == 64
    return result


def prepare():
    verified_target()
    assert not (RUN / 'prepare-attempt.json').exists()
    command = [str(PYTHON), str(CORE / 'odoo-bin'), 'shell', '-c', str(RUN / 'odoo.conf'), '--no-http']
    stdin = "exec(compile(open('" + str(SHELL) + "').read(),'s10_e2e_w1_prepare.py','exec'))\n"
    bounded(command, 'odoo-prepare.log', 'prepare-attempt.json', 600, stdin)


def serve():
    successful_result('prepare-attempt.json.result')
    assert not (RUN / 'http.attempt.json').exists()
    marker = RUN / 'http.attempt.json'
    verified_target()
    exclusive(marker, json.dumps({'stage': 'W1_HTTP', 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    command = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(RUN / 'odoo.conf')]
    log = RUN / 'odoo-http.log'
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environment(), stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        exclusive(RUN / 'http.pid', str(process.pid) + '\n')
        timed_out = False
        try:
            code = process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGINT)
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=10)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': code, 'timed_out': timed_out,
              'oid': target(), 'config_sha256': digest(RUN / 'odoo.conf'),
              'signal11': code in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size}
    write_once(RUN / 'http.result.json', result)
    print(json.dumps(result), flush=True)


def wait_http():
    verified_target()
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


def stop():
    pid = int((RUN / 'http.pid').read_text().strip())
    cmdline = Path('/proc/' + str(pid) + '/cmdline').read_bytes().split(b'\0')
    assert os.fsencode(str(RUN / 'odoo.conf')) in cmdline and os.fsencode(str(CORE / 'odoo-bin')) in cmdline
    os.kill(pid, signal.SIGINT)
    for _ in range(50):
        if (RUN / 'http.result.json').exists():
            result = successful_result('http.result.json', allowed_exits=(0, -2, 130))
            print(json.dumps(result)); return
        time.sleep(.2)
    raise RuntimeError('HTTP process did not exit in 10 seconds; STOP')


COMMANDS = {
    'preflight': lambda: print(json.dumps({'status': 'SOURCE_READ_ONLY_PASS', 'source_oid': 2100080})) if identity(False) else None,
    'create': create, 'verify-target': lambda: print(json.dumps({'status': 'REAL_OID_MARKER_PASS', 'oid': verified_target()})),
    'prepare': prepare, 'serve': serve, 'wait-http': wait_http, 'stop': stop,
}


def dispatch(command):
    if command not in COMMANDS:
        raise ValueError('Unknown S10-E2E-W1 command')
    return COMMANDS[command]()


if __name__ == '__main__':
    dispatch(sys.argv[1])
