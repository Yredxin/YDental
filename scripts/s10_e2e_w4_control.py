"""Single-use W4 clone, settlement-only update and Web payment controller."""

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

import psycopg2
from psycopg2 import sql

from s10_e2e_w4_snapshot import (AUTH, BASE, CLUSTER, CORE, CORE_HEAD, EXACT_TABLES,
    NAME, PORT, ROOT, RUN, SOURCE, SOURCE_OID, SOURCE_RUN, canonical, database_identity,
    digest, endpoint, filestore, money, source_audit, state, views, connect)

os.umask(0o077)
PYTHON = CORE / '.venv/bin/python'
SCRIPTS = tuple(sorted((ROOT / 'scripts').glob('s10_e2e_w4_*.py')))
POLICY = ROOT / 'scripts/s08c_network_policy.py'
PREFLIGHT = ROOT / 'docs/evidence/s10-e2e-w4/preflight.json'
CHECKPOINT = ROOT / '.local/s10-e2e-w4-checkpoint.json'
UPGRADE_ARGV = (str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(RUN / 'odoo.conf'),
                '-u', 'ydental_settlement', '--stop-after-init', '--no-http')
HTTP_ARGV = (str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(RUN / 'odoo.conf'))
BROWSER_ARGV = (str(PYTHON), str(ROOT / 'scripts/s10_e2e_w4_browser.py'))


def write_once(path, value):
    path = Path(path)
    if path.exists() or path.with_name(path.name + '.partial').exists():
        raise FileExistsError(path)
    payload = canonical(value) + '\n'
    partial = path.with_name(path.name + '.partial')
    with os.fdopen(os.open(partial, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        stream.write(payload)
        stream.flush(); os.fsync(stream.fileno())
    assert partial.read_text() == payload
    os.replace(partial, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def write_text_once(path, value):
    path = Path(path)
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        stream.write(value)
        stream.flush(); os.fsync(stream.fileno())


def file_identity():
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    remote = subprocess.check_output(['git', 'ls-remote', 'origin',
        'refs/heads/codex/s10-settlement-finance-r1-20261013'], cwd=ROOT, text=True).split()
    assert len(remote) == 2 and remote[0] == BASE
    assert subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode == 0
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CORE, text=True).strip() == CORE_HEAD
    assert subprocess.check_output(['git', 'hash-object', 'ydental_settlement/models/ydental_settlement_service.py'], cwd=ROOT, text=True).strip() == 'd4d4363ab2dfdd982606f464e5b66c240744fac6'
    expected = {
        'ydental_inventory/models/ydental_inventory_service.py': 'df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b',
        'ydental_settlement/controllers/settlement.py': 'bfa051971585369f1585d311cfc4553159d4a42ef23b3c54f35d77e53ab4caa2',
        'ydental_settlement/views/ydental_settlement_templates.xml': '8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329',
    }
    assert all(digest(ROOT / path) == value for path, value in expected.items())
    manifest = (ROOT / 'ydental_settlement/__manifest__.py').read_text()
    assert "'views/ydental_settlement_templates.xml'" in manifest
    assert 'name="output" value="html"' in (ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml').read_text()
    controller = (ROOT / 'ydental_settlement/controllers/settlement.py').read_text()
    assert "post.get('output') == 'html'" in controller and "mimetype == 'application/x-www-form-urlencoded'" in controller


def checkpoint():
    file_identity()
    preflight = json.loads(PREFLIGHT.read_text())
    marker = json.loads(CHECKPOINT.read_text())
    assert marker['comment_id'] > AUTH and marker['preflight_sha256'] == digest(PREFLIGHT)
    assert marker['body_sha256'] and len(marker['body_sha256']) == 64
    assert preflight['source']['oid'] == SOURCE_OID and preflight['target'] == NAME
    expected = preflight['scripts_sha256']
    assert sorted(expected) == [str(path.relative_to(ROOT)) for path in SCRIPTS]
    assert all(digest(ROOT / name) == value for name, value in expected.items())
    assert preflight['upgrade_argv'] == list(UPGRADE_ARGV)
    assert preflight['http_argv'] == list(HTTP_ARGV)
    assert preflight['browser_argv'] == list(BROWSER_ARGV)
    return marker


def private_environment():
    env = os.environ.copy()
    env.update({'PYTHONPATH': str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
                'YDENTAL_S10_RUN_DIR': str(RUN), 'YDENTAL_S08C_HTTP_PORT': str(PORT),
                'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                'PGAPPNAME': 's10_e2e_w4_bounded'})
    return env


def no_parallel_w4():
    output = subprocess.check_output(['ps', '-eo', 'pid=,args='], text=True)
    for line in output.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or int(fields[0]) == os.getpid():
            continue
        try:
            executable = os.path.basename(os.readlink('/proc/' + fields[0] + '/exe'))
        except (FileNotFoundError, PermissionError):
            continue
        if not executable.startswith('python'):
            continue
        command = fields[1]
        if (str(RUN / 'odoo.conf') in command or
                'scripts/s10_e2e_w4_browser.py' in command or
                'scripts/s10_e2e_w4_control.py execute' in command):
            raise RuntimeError('Parallel W4 Odoo, browser or execution process found; STOP')
    return True


def verify_target():
    rows, _ = database_identity()
    oid = rows.get(NAME)
    assert type(oid) is int and oid > 0 and oid != SOURCE_OID
    marker = json.loads((RUN / 'database.json').read_text())
    assert marker['database'] == NAME and marker['oid'] == oid
    assert marker['source'] == SOURCE and marker['source_oid'] == SOURCE_OID
    assert marker['cluster'] == CLUSTER and marker['base'] == BASE and marker['core'] == CORE_HEAD
    assert marker['config_sha256'] == digest(RUN / 'odoo.conf')
    assert marker['source_marker_sha256'] == digest(SOURCE_RUN / 'database.json')
    assert marker['source_config_sha256'] == digest(SOURCE_RUN / 'odoo.conf')
    assert marker['script_sha256'] == json.loads(PREFLIGHT.read_text())['scripts_sha256']
    checkpoint()
    return oid


def clone(source_before):
    checkpoint()
    no_parallel_w4()
    assert source_before['database'] == SOURCE and source_before['exact'] == source_audit()['exact']
    rows, activity = database_identity()
    assert NAME not in rows and activity == [] and not RUN.exists()
    assert not (ROOT / '.local/s10-e2e-w4-create-attempt.json').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    write_text_once(RUN / 'network-policy/sitecustomize.py', POLICY.read_text())
    source_fs = SOURCE_RUN / 'data/filestore' / SOURCE
    target_fs = RUN / 'data/filestore' / NAME
    target_fs.mkdir(parents=True, mode=0o700)
    for relative, expected in source_before['filestore']['files'].items():
        source_file = source_fs / relative
        assert digest(source_file) == expected
        target_file = target_fs / relative
        target_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with source_file.open('rb') as reader, os.fdopen(os.open(target_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as writer:
            shutil.copyfileobj(reader, writer)
        assert digest(target_file) == expected
    write_once(ROOT / '.local/s10-e2e-w4-create-attempt.json',
               {'source': SOURCE, 'source_oid': SOURCE_OID, 'target': NAME, 'auth': AUTH,
                'checkpoint': json.loads(CHECKPOINT.read_text())['comment_id'],
                'utc': datetime.now(timezone.utc).isoformat()})
    connection = psycopg2.connect(dbname='postgres', **endpoint())
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            assert connection.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cursor.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(SOURCE)))
    finally:
        connection.close()
    write_once(RUN / 'create-sql-committed.json', {'source_oid': SOURCE_OID, 'target': NAME})
    rows, _ = database_identity()
    oid = rows[NAME]
    assert oid != SOURCE_OID
    options = configparser.ConfigParser(interpolation=None)
    options['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
        'db_password': endpoint()['password'], 'db_name': NAME, 'dbfilter': '^' + NAME + '$',
        'addons_path': ','.join(str(path) for path in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
        'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
        'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
        'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    text = io.StringIO(); options.write(text)
    write_text_once(RUN / 'odoo.conf', text.getvalue())
    marker = {'database': NAME, 'oid': oid, 'source': SOURCE, 'source_oid': SOURCE_OID,
              'source_marker_sha256': digest(SOURCE_RUN / 'database.json'),
              'source_config_sha256': digest(SOURCE_RUN / 'odoo.conf'),
              'source_filestore_manifest_sha256': source_before['filestore']['manifest_sha256'],
              'cluster': CLUSTER, 'base': BASE, 'core': CORE_HEAD,
              'config_sha256': digest(RUN / 'odoo.conf'), 'auth': AUTH, 'port': PORT,
              'script_sha256': json.loads(PREFLIGHT.read_text())['scripts_sha256']}
    write_once(RUN / 'database.json', marker)
    assert verify_target() == oid
    write_once(RUN / 'create-complete.json', {'target': NAME, 'oid': oid})
    return oid


def before_snapshot(source_before):
    oid = verify_target()
    source_now = state(SOURCE)
    target_now = state(NAME)
    validate_clone(source_before, source_now, target_now)
    write_once(RUN / 'before-upgrade.json', {'oid': oid, 'exact': target_now['exact'],
        'money': target_now['money'], 'views': target_now['views'],
        'modules_sha256': hashlib.sha256(canonical(target_now['modules']).encode()).hexdigest(),
        'module_meta_sha256': hashlib.sha256(canonical(target_now['module_meta']).encode()).hexdigest(),
        'filestore_manifest_sha256': target_now['filestore']['manifest_sha256']})
    return target_now


def validate_clone(source_before, source_now, target_now):
    for key in ('exact', 'money', 'views', 'modules', 'module_meta'):
        assert source_now[key] == source_before[key] == target_now[key], ('clone_difference', key)
    for key in ('manifest_sha256', 'attachment_pointers_sha256'):
        assert source_now['filestore'][key] == source_before['filestore'][key] == target_now['filestore'][key]
    return True


def bounded(command, attempt, log_name, timeout):
    assert verify_target() > 0
    write_once(RUN / attempt, {'argv': list(command), 'utc': datetime.now(timezone.utc).isoformat()})
    log = RUN / log_name
    timed_out = False
    with os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as output:
        process = subprocess.Popen(command, cwd=CORE, env=private_environment(),
                                   stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGINT)
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=10)
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': code, 'timeout': timed_out,
              'signal11': code in (-11, 139) or 'Fatal Python error: Segmentation fault' in raw,
              'log_sha256': digest(log), 'log_bytes': log.stat().st_size,
              'oid': verify_target(), 'config_sha256': digest(RUN / 'odoo.conf')}
    write_once(RUN / (attempt + '.result'), result)
    if timed_out or result['signal11'] or code != 0:
        raise RuntimeError(f'{attempt} exited abnormally; STOP')
    return result


def upgrade():
    assert (RUN / 'before-upgrade.json').is_file()
    assert not (RUN / 'upgrade-attempt.json').exists()
    assert UPGRADE_ARGV[-4:] == ('-u', 'ydental_settlement', '--stop-after-init', '--no-http')
    return bounded(UPGRADE_ARGV, 'upgrade-attempt.json', 'odoo-upgrade.log', 1200)


def after_snapshot(before, source_before):
    assert json.loads((RUN / 'upgrade-attempt.json.result').read_text())['exit_code'] == 0
    target_now = state(NAME)
    source_now = state(SOURCE)
    validate_upgrade(before, source_before, target_now, source_now)
    write_once(RUN / 'after-upgrade.json', {'exact': target_now['exact'],
        'money': target_now['money'], 'views': target_now['views'],
        'settlement_module': target_now['module_meta']['ydental_settlement'],
        'module_meta_sha256': hashlib.sha256(canonical(target_now['module_meta']).encode()).hexdigest(),
        'filestore_manifest_sha256': target_now['filestore']['manifest_sha256']})
    return target_now


def validate_upgrade(before, source_before, target_now, source_now):
    assert source_now['exact'] == source_before['exact'] and source_now['money'] == source_before['money']
    assert source_now['views'] == source_before['views']
    assert source_now['module_meta'] == source_before['module_meta']
    assert source_now['filestore']['manifest_sha256'] == source_before['filestore']['manifest_sha256']
    assert target_now['exact'] == before['exact'], 'upgrade changed a frozen business/economic row'
    assert target_now['money'] == before['money']
    assert target_now['modules'] == before['modules'], 'upgrade changed installed module set'
    assert target_now['module_meta']['ydental_settlement']['state'] == 'installed'
    assert {key: value for key, value in target_now['module_meta'].items() if key != 'ydental_settlement'} == {
        key: value for key, value in before['module_meta'].items() if key != 'ydental_settlement'}, 'non-target module metadata changed'
    assert target_now['filestore']['manifest_sha256'] == before['filestore']['manifest_sha256']
    token = target_now['views']['ydental_settlement.ydental_settlement_tokens']
    assert token['en_US']['has_output_html'] is True
    assert all(view['has_output_html'] for view in token.values())
    assert target_now['views'] != before['views']
    return True


def start_http():
    assert (RUN / 'after-upgrade.json').is_file() and not (RUN / 'http-attempt.json').exists()
    verify_target()
    write_once(RUN / 'http-attempt.json', {'argv': list(HTTP_ARGV), 'utc': datetime.now(timezone.utc).isoformat()})
    log = RUN / 'odoo-http.log'
    output = os.fdopen(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w')
    try:
        process = subprocess.Popen(HTTP_ARGV, cwd=CORE, env=private_environment(),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            start_new_session=True)
    finally:
        output.close()
    write_once(RUN / 'http-pid.json', {'pid': process.pid, 'oid': verify_target()})
    started = time.monotonic()
    try:
        while time.monotonic() - started < 180:
            if process.poll() is not None:
                raise RuntimeError('HTTP Odoo exited during startup; STOP')
            try:
                with urlopen(f'http://127.0.0.1:{PORT}/web/login', timeout=3) as response:
                    if response.status == 200:
                        write_once(RUN / 'http-ready.json', {'pid': process.pid, 'startup_seconds': time.monotonic()-started})
                        return process, started
            except Exception:
                pass
            time.sleep(2)
        raise RuntimeError('HTTP startup exceeded 180 seconds; STOP')
    except BaseException:
        stop_http(process, started)
        raise


def stop_http(process, started):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
    try:
        code = process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        code = process.wait(timeout=10)
    log = RUN / 'odoo-http.log'
    raw = log.read_text(errors='replace')
    result = {'pid': process.pid, 'exit_code': code, 'seconds': time.monotonic()-started,
        'signal11': code in (-11,139) or 'Fatal Python error: Segmentation fault' in raw,
        'log_sha256': digest(log), 'log_bytes': log.stat().st_size}
    write_once(RUN / 'http-result.json', result)
    assert result['seconds'] <= 1200 and result['signal11'] is False and code in (0, -2, 130)
    return result


def browse():
    assert (RUN / 'http-ready.json').is_file() and not (RUN / 'browser-attempt.json').exists()
    return bounded(BROWSER_ARGV, 'browser-attempt.json', 'browser.log', 1200)


def final_audit(before, source_before):
    target = state(NAME)
    source = state(SOURCE)
    assert source['exact'] == source_before['exact'] and source['money'] == source_before['money']
    assert source['views'] == source_before['views'] and source['module_meta'] == source_before['module_meta']
    assert source['filestore']['manifest_sha256'] == source_before['filestore']['manifest_sha256']
    from s10_e2e_w4_browser import validate_audit_progress, validate_money
    validate_money(target['money'], (500,240), (240,0), before['money'])
    validate_audit_progress(before['money'], target['money'])
    from s10_e2e_w4_snapshot import STABLE_AFTER_PAYMENT
    assert all(target['exact'][table] == before['exact'][table] for table in STABLE_AFTER_PAYMENT)
    write_once(RUN / 'final-audit.json', {'money': target['money'], 'views': target['views'],
        'source_unchanged': True, 'stable_business_table_count': len(STABLE_AFTER_PAYMENT),
        'stable_business_sha256': hashlib.sha256(canonical({table: target['exact'][table] for table in STABLE_AFTER_PAYMENT}).encode()).hexdigest()})


def execute_pipeline(ops):
    """The same stage order is used by real and offline fault-injection adapters."""
    source = ops.source()
    ops.create(source)
    before = ops.before(source)
    ops.upgrade()
    ops.after(before, source)
    started = False
    try:
        ops.start()
        started = True
        ops.browser()
        ops.final(before, source)
    finally:
        if started or ops.http_started():
            ops.stop()


class RealOps:
    def __init__(self):
        self.process = None
        self.started = None

    def source(self):
        checkpoint()
        source_audit()
        return state(SOURCE)

    def create(self, source):
        clone(source)

    def before(self, source):
        return before_snapshot(source)

    def upgrade(self):
        upgrade()

    def after(self, before, source):
        after_snapshot(before, source)

    def start(self):
        self.process, self.started = start_http()

    def http_started(self):
        return self.process is not None

    def browser(self):
        browse()

    def final(self, before, source):
        final_audit(before, source)

    def stop(self):
        stop_http(self.process, self.started)


if __name__ == '__main__':
    assert sys.argv[1:] == ['execute']
    execute_pipeline(RealOps())
