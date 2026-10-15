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
from s10_ui1_r2_contract import build_marker, check_fixed_adapter, validate_marker
from s10_ui1_r2_evidence import read_complete, write_once

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261015014500_c72e6f91'
NAME = 'ydental_s10_test_20261015024000_d36e2b81'
SOURCE_RUN = ROOT / '.local' / SOURCE
RUN = ROOT / '.local' / NAME
PORT = 18272
BASE = 'c2a26eed14ecf2f3961539f607145a737596c1d6'
AUTH = 6182876575
CHECKPOINT = 'S10-UI1-R3'
CLUSTER = '7694897083368259627'
SOURCE_MARKER_SHA = 'c50e4e5dce1fbbdac86f6e01ea0b9c5df8a2d9565274ae7807c8ce49d47e9e11'
SOURCE_CONFIG_SHA = '3c0b70d5ed0d13346a7b3d009409c06dc73c73d8b210a6efbc8a44f6cea460ca'
SOURCE_FS_COUNT = 150
SOURCE_FS_SHA = 'abf18f3ab41a8db6c22e269b590fd5910cc1fc954f44cbda6bbffc317aa332db'
SHELL = ROOT / 'scripts/s10_ui1_r3_cli_parse.py'
CONTROL = ROOT / 'scripts/s10_ui1_r3_control.py'
BROWSER = ROOT / 'scripts/s10_ui1_r3_browser.py'
CONTRACT = ROOT / 'scripts/s10_ui1_r2_contract.py'
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


def source_files():
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    assert source_fs.is_dir() and not source_fs.is_symlink()
    files = {}
    for path in source_fs.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():
            files[str(path.relative_to(source_fs))] = {'sha256': digest(path)}
    raw = json.dumps(sorted((rel, item['sha256']) for rel, item in files.items()),
                     sort_keys=True, separators=(',', ':')).encode()
    assert len(files) == SOURCE_FS_COUNT and hashlib.sha256(raw).hexdigest() == SOURCE_FS_SHA
    return files


def finance_snapshot(dbname, ep):
    conn = psycopg2.connect(dbname=dbname, **ep)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            rows = {}
            for label, query in (
                ('fees', 'SELECT id,ydental_amount FROM ydental_treatment_fee ORDER BY id'),
                ('sources', 'SELECT id,ydental_fee_id,ydental_invoice_id FROM ydental_settlement_source ORDER BY id'),
                ('receipts', 'SELECT id,ydental_operation FROM ydental_settlement_receipt ORDER BY id'),
                ('moves', 'SELECT id,move_type,state,amount_total,amount_residual FROM account_move ORDER BY id'),
                ('payments', 'SELECT id FROM ydental_settlement_payment ORDER BY id'),
                ('refunds', 'SELECT id FROM ydental_settlement_refund ORDER BY id'),
                ('closes', 'SELECT id FROM ydental_settlement_close ORDER BY id'),
                ('native_payments', 'SELECT id FROM account_payment ORDER BY id'),
            ):
                cur.execute(query)
                rows[label] = cur.fetchall()
            cur.execute('SELECT count(*) FROM ydental_access_audit')
            rows['audit_count'] = cur.fetchone()[0]
            return rows
    finally:
        conn.close()


def assert_source_baseline(ep):
    from decimal import Decimal
    rows = finance_snapshot(SOURCE, ep)
    assert rows == {
        'fees': [(1, Decimal('100.00')), (2, Decimal('100.00'))],
        'sources': [(1, 1, 1)], 'receipts': [(1, 'bill')],
        'moves': [(1, 'out_invoice', 'posted', Decimal('100.00'), Decimal('100.00'))],
        'payments': [], 'refunds': [], 'closes': [], 'native_payments': [],
        'audit_count': 162,
    }
    return rows


def config_options(ep):
    return {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
            'db_password': ep['password'], 'db_name': NAME, 'dbfilter': '^' + NAME + '$',
            'addons_path': ','.join(str(x) for x in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
            'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1',
            'http_port': str(PORT), 'list_db': 'False', 'workers': '0',
            'max_cron_threads': '0', 'admin_passwd': secrets.token_urlsafe(32),
            'smtp_server': '127.0.0.1', 'smtp_port': '1'}


def argv(mode, config_path=None):
    assert mode in ('legacy_invalid', 'upgrade', 'http')
    path = str(config_path or RUN / 'odoo.conf')
    common = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', path, '-d', NAME]
    if mode == 'http':
        return common
    args = common + ['-u', 'ydental_settlement', '--stop-after-init', '--no-http']
    return args + (['--test-disable'] if mode == 'legacy_invalid' else [])


def cli_proof(mode):
    proof = read_complete(RUN / ('cli-' + mode + '.json'))
    assert proof['status'] == 'CLI_PARSE_PASS' and proof['mode'] == mode
    assert proof['argv'] == argv(mode) and proof['config_sha256'] == digest(RUN / 'odoo.conf')
    opts = proof['options']
    assert opts['db_name'] == [NAME] and opts['init'] == {}
    assert opts['update'] == ({'ydental_settlement': True} if mode == 'upgrade' else {})
    assert opts['test_enable'] is False and not opts['test_tags'] and not opts['test_file']
    assert opts['http_enable'] is (mode == 'http')
    assert opts['stop_after_init'] is (mode == 'upgrade')
    return proof


def identity(expect_target=False):
    assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
    assert subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == BASE
    core_head()
    assert subprocess.check_output(['git', '-C', str(ROOT), 'hash-object', str(ROOT / 'ydental_settlement/models/ydental_settlement_service.py')], text=True).strip() == 'd4d4363ab2dfdd982606f464e5b66c240744fac6'
    assert digest(ROOT / 'ydental_inventory/models/ydental_inventory_service.py') == 'df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b'
    assert digest(SOURCE_RUN / 'database.json') == SOURCE_MARKER_SHA
    assert digest(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG_SHA
    assert digest(ROOT / 'ydental_settlement/controllers/settlement.py') == 'bfa051971585369f1585d311cfc4553159d4a42ef23b3c54f35d77e53ab4caa2'
    assert digest(ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml') == '8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329'
    expected = source_files()
    ep = endpoint()
    conn = psycopg2.connect(dbname='postgres', **ep)
    conn.set_session(readonly=True)
    with conn.cursor() as cur:
        cur.execute('SELECT system_identifier::text FROM pg_control_system()')
        assert cur.fetchone()[0] == CLUSTER
        cur.execute('SELECT datname, oid FROM pg_database WHERE datname IN (%s,%s)', (SOURCE, NAME))
        oids = dict(cur.fetchall())
        assert oids[SOURCE] == 2100240 and (NAME in oids) == expect_target
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
        cur.execute('SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL')
        for rel, checksum in cur.fetchall():
            path = SOURCE_RUN / 'data/filestore' / SOURCE / rel
            assert rel in expected and path.is_file()
            assert not checksum or hashlib.sha1(path.read_bytes()).hexdigest() == checksum
    conn.close()
    assert_source_baseline(ep)
    return ep, expected, oids.get(NAME)


def create():
    ep, expected, _ = identity(False)
    assert not RUN.exists()
    assert not (ROOT / '.local/s10-ui1-r3-create-attempt.json').exists()
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
    exclusive(ROOT / '.local/s10-ui1-r3-create-attempt.json', json.dumps({'name': NAME, 'auth': AUTH, 'checkpoint': CHECKPOINT, 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
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
    cfg['options'] = config_options(ep)
    buffer = io.StringIO(); cfg.write(buffer)
    exclusive(RUN / 'odoo.conf', buffer.getvalue())
    marker = build_marker(database=NAME, oid=oid, cluster=CLUSTER,
        actual_core=core_head(), config=RUN / 'odoo.conf', run=RUN,
        auth=AUTH, base=BASE, port=PORT, source=SOURCE, source_oid=2100240,
        policy=RUN / 'network-policy/sitecustomize.py', prepare=SHELL,
        control=CONTROL, browser=BROWSER, contract=CONTRACT)
    exclusive(RUN / 'database.json', json.dumps(marker, indent=2) + '\n')
    target()
    fixture = json.loads((SOURCE_RUN / 'fixture.json').read_text())
    assert fixture['db'] == SOURCE and fixture['oid'] == 2100240
    fixture.update({'db': NAME, 'oid': oid,
                    'inherited_from': {'database': SOURCE, 'oid': 2100240,
                                       'fixture_sha256': digest(SOURCE_RUN / 'fixture.json')}})
    write_once(RUN / 'fixture.json', fixture)
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
        auth=AUTH, base=BASE, port=PORT, source=SOURCE, source_oid=2100240,
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
              'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PGAPPNAME': 's10_ui1_r3_single_registry'})
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


def inherited_baseline():
    oid = verified_target()
    ep = endpoint()
    original = assert_source_baseline(ep)
    cloned = finance_snapshot(NAME, ep)
    assert cloned == original and oid > 0
    return cloned


def qweb_loaded():
    ep = endpoint()
    conn = psycopg2.connect(dbname=NAME, **ep)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT key,arch_db::text FROM ir_ui_view WHERE key IN "
                        "('ydental_settlement.ydental_settlement_tokens',"
                        "'ydental_settlement.ydental_settlement_page')")
            views = dict(cur.fetchall())
            assert len(views) == 2
            assert 'name=\\\"output\\\"' in views['ydental_settlement.ydental_settlement_tokens']
            assert 'data-ui1-feedback' in views['ydental_settlement.ydental_settlement_page']
    finally:
        conn.close()
    return True


def upgrade():
    cli_proof('upgrade')
    inherited = inherited_baseline()
    write_once(RUN / 'finance-before-upgrade.json', inherited)
    bounded(argv('upgrade'), 'odoo-upgrade.log', 'upgrade-attempt.json', 600)
    successful_result('upgrade-attempt.json.result')
    assert finance_snapshot(NAME, endpoint()) == inherited
    assert qweb_loaded()
    write_once(RUN / 'upgrade-complete.json', {'oid': verified_target(),
        'phase': 'QWEB_AND_FINANCE_VERIFIED', 'config_sha256': digest(RUN / 'odoo.conf')})


def serve():
    successful_result('upgrade-attempt.json.result')
    assert read_complete(RUN / 'upgrade-complete.json') == {'oid': verified_target(),
        'phase': 'QWEB_AND_FINANCE_VERIFIED', 'config_sha256': digest(RUN / 'odoo.conf')}
    cli_proof('http')
    marker = RUN / 'http-after.attempt.json'
    verified_target()
    exclusive(marker, json.dumps({'stage': 'after', 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    command = argv('http')
    log = RUN / 'odoo-http-after.log'
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=environment(), stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        exclusive(RUN / 'http-after.pid', str(process.pid) + '\n')
        timed_out = False
        try:
            code = process.wait(timeout=1200)
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
    write_once(RUN / 'http-after.result.json', result)
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
    pid = int((RUN / 'http-after.pid').read_text().strip())
    cmdline = Path('/proc/' + str(pid) + '/cmdline').read_bytes().split(b'\0')
    assert os.fsencode(str(RUN / 'odoo.conf')) in cmdline and os.fsencode(str(CORE / 'odoo-bin')) in cmdline
    os.kill(pid, signal.SIGINT)
    for _ in range(50):
        if (RUN / 'http-after.result.json').exists():
            result = successful_result('http-after.result.json', allowed_exits=(0, -2, 130))
            print(json.dumps(result)); return
        time.sleep(.2)
    raise RuntimeError('HTTP process did not exit in 10 seconds; STOP')


COMMANDS = {
    'preflight': lambda: print(json.dumps({'status': 'SOURCE_READONLY_PASS', 'source_oid': 2100240})) if identity(False) else None,
    'create': create, 'verify-target': lambda: print(json.dumps({'status': 'REAL_OID_MARKER_PASS', 'oid': verified_target()})) if inherited_baseline() else None,
    'upgrade': upgrade, 'serve-after': serve, 'wait-http': wait_http, 'stop-after': stop,
}


def dispatch(command):
    if command not in COMMANDS:
        raise ValueError('Unknown UI1-R3 command')
    return COMMANDS[command]()


if __name__ == '__main__':
    dispatch(sys.argv[1])
