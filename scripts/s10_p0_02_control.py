"""Single-use P0-02 clone, native update and bounded Web controller."""

import configparser
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import psycopg2
from psycopg2 import sql

from s10_p0_02_snapshot import (ALLOWED_VIEWS, CLUSTER, CORE, CORE_HEAD,
    HEAD, MONEY_TABLES, PORT, ROOT, SOURCE, SOURCE_CONFIG, SOURCE_MANIFEST,
    SOURCE_MARKER, SOURCE_OID, SOURCE_RUN, TARGET, TARGET_RUN, TOKEN_OLD,
    UPGRADE_EXCEPTIONS, WEB_EXCEPTIONS, connect, credentials, file_sha,
    identity, public, sha, snapshot)

os.umask(0o077)
AUTH = 6191214820
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
PYTHON = CORE / '.venv/bin/python'
ODOO = CORE / 'odoo-bin'
SCRIPTS = tuple(sorted((ROOT / 'scripts').glob('s10_p0_02_*.py')))
PRIVATE = ROOT / '.local' / 's10-p0-02'
PREFLIGHT = ROOT / 'docs/evidence/s10-p0-02/preflight.json'
CHECKPOINT = PRIVATE / 'checkpoint.json'
CONF = TARGET_RUN / 'odoo.conf'
UPGRADE_ARGV = (str(PYTHON), str(ODOO), '-c', str(CONF), '-u',
                'ydental_settlement', '--stop-after-init', '--no-http')
HTTP_ARGV = (str(PYTHON), str(ODOO), '-c', str(CONF))
BROWSER_ARGV = (str(PYTHON), str(ROOT / 'scripts/s10_p0_02_browser.py'))


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str,
                      separators=(',', ':'))


def save_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (compact(value) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert path.read_bytes() == data


def authority():
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT,
        text=True).strip() == BRANCH
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
        text=True).strip() == HEAD
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/'+BRANCH],
        cwd=ROOT, text=True).split()
    assert len(remote) == 2 and remote[0] == HEAD
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CORE,
        text=True).strip() == CORE_HEAD
    assert subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode == 0
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    assert file_sha(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG
    assert file_sha(SOURCE_RUN / 'database.json') == SOURCE_MARKER
    assert (ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml').is_file()
    actual = {path.name: file_sha(path) for path in (
        ROOT / 'ydental_settlement/controllers/settlement.py',
        ROOT / 'ydental_settlement/models/ydental_settlement_service.py',
        ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml')}
    expected = {'settlement.py':'bfa051971585369f1585d311cfc4553159d4a42ef23b3c54f35d77e53ab4caa2',
        'ydental_settlement_service.py':'1ea27012fd5500fc21891f9e652f4e694cb2e7cce844fa38d08b7f12beff8d2c',
        'ydental_settlement_templates.xml':'8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329'}
    assert actual == expected
    assert "post.get('output') == 'html'" in (
        ROOT / 'ydental_settlement/controllers/settlement.py').read_text()
    assert 'name="output" value="html"' in (
        ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml').read_text()
    return actual


def source_gate(before):
    assert before['database'] == SOURCE and before['oid'] == SOURCE_OID
    assert before['cluster'] == CLUSTER
    assert before['filestore']['count'] == 184
    assert before['filestore']['sha256'] == SOURCE_MANIFEST
    assert len(before['tables']) >= 38
    assert before['business']['refunds_count'] == 63
    assert before['business']['closes_count'] == 55
    assert before['views']['ydental_settlement.ydental_settlement_tokens']['languages']['en_US'] == {
        'sha256': TOKEN_OLD, 'has_output_html': False}
    assert set(ALLOWED_VIEWS) <= set(before['views'])
    assert before['modules']['ydental_settlement']['state'] == 'installed'
    assert before['modules']['ydental_settlement_test']['state'] == 'installed'
    assert sum(v['state']=='installed' for v in before['modules'].values()) == 92
    return True


def equal_clone(before, after):
    assert after['database'] == TARGET and after['oid'] != before['oid']
    for key in ('tables', 'protected_other_rows', 'schema', 'modules', 'views', 'view_rows', 'filestore',
                'attachment_pointers'):
        assert after[key] == before[key], ('clone_difference', key)
    return True


def diff_upgrade(before, after, source_after):
    assert source_after['database'] == SOURCE
    for key in ('tables', 'protected_other_rows', 'schema', 'modules', 'views', 'view_rows', 'filestore',
                'attachment_pointers'):
        assert source_after[key] == before[key], ('source_drift', key)
    assert after['schema'] == before['schema']
    assert set(after['tables']) == set(before['tables'])
    for name in before['tables']:
        if name not in UPGRADE_EXCEPTIONS:
            assert after['tables'][name] == before['tables'][name], ('upgrade_table_drift', name)
    assert after['filestore'] == before['filestore']
    assert after['protected_other_rows'] == before['protected_other_rows']
    assert after['attachment_pointers'] == before['attachment_pointers']
    assert set(after['modules']) == set(before['modules'])
    module_write_dates = {}
    for name in before['modules']:
        old = before['modules'][name]
        new = after['modules'][name]
        changed = {key for key in set(old)|set(new) if old.get(key) != new.get(key)}
        assert changed <= {'write_date'}, ('module_meta_drift', name, changed)
        if changed:
            module_write_dates[name] = {'old': old.get('write_date'), 'new': new.get('write_date')}
    allowed_module_dates = set(json.loads(PREFLIGHT.read_text())['module_write_date_candidates'])
    assert set(module_write_dates) <= allowed_module_dates, 'unbounded module write_date change'
    assert {name for name,row in after['modules'].items() if row['state']=='installed'} == {
        name for name,row in before['modules'].items() if row['state']=='installed'}
    assert set(after['views']) == set(before['views'])
    changed_views = {name for name in before['views'] if after['views'][name] != before['views'][name]}
    assert changed_views <= ALLOWED_VIEWS and 'ydental_settlement.ydental_settlement_tokens' in changed_views
    assert set(after['view_rows']) == set(before['view_rows'])
    changed_rows = {ident for ident in before['view_rows']
                    if after['view_rows'][ident] != before['view_rows'][ident]}
    assert {after['view_rows'][ident]['key'] for ident in changed_rows} == changed_views
    for ident in changed_rows:
        old = before['view_rows'][ident]; new = after['view_rows'][ident]
        changed_columns = {key for key in set(old)|set(new) if old.get(key) != new.get(key)}
        assert changed_columns <= {'arch_db','write_date','write_uid'}, ('view_fields',ident,changed_columns)
    tokens = after['views']['ydental_settlement.ydental_settlement_tokens']['languages']
    assert tokens and all(v['has_output_html'] for v in tokens.values())
    return {'module_write_dates': module_write_dates,
            'changed_views': sorted(changed_views),
            'token_languages': tokens}


def diff_web(before, after, *, refund_done=False, close_done=False):
    assert before['schema'] == after['schema']
    assert set(before['tables']) == set(after['tables'])
    for name in before['tables']:
        if name not in WEB_EXCEPTIONS:
            assert before['tables'][name] == after['tables'][name], ('web_table_drift', name)
    for name in MONEY_TABLES:
        assert before['tables'][name] == after['tables'][name], ('money_drift', name)
    assert before['modules'] == after['modules']
    assert before['views'] == after['views']
    assert before['view_rows'] == after['view_rows']
    assert before['filestore'] == after['filestore']
    assert before['attachment_pointers'] == after['attachment_pointers']
    assert before['protected_other_rows'] == after['protected_other_rows']
    if not refund_done:
        assert before['tables']['ydental_settlement_refund'] == after['tables']['ydental_settlement_refund']
    if not close_done:
        assert before['tables']['ydental_settlement_close'] == after['tables']['ydental_settlement_close']
    return True


def checkpoint():
    authority()
    pre = json.loads(PREFLIGHT.read_text())
    mark = json.loads(CHECKPOINT.read_text())
    assert mark['comment_id'] > AUTH and mark['preflight_sha256'] == file_sha(PREFLIGHT)
    assert mark['body_sha256'] and len(mark['body_sha256']) == 64
    assert pre['target'] == TARGET and pre['source']['oid'] == SOURCE_OID
    expected = pre['scripts_sha256']
    assert set(expected) == {str(path.relative_to(ROOT)) for path in SCRIPTS}
    assert all(file_sha(ROOT / name) == value for name,value in expected.items())
    assert pre['upgrade_argv'] == list(UPGRADE_ARGV)
    assert pre['http_argv'] == list(HTTP_ARGV)
    assert pre['browser_argv'] == list(BROWSER_ARGV)
    return mark


def private_env():
    env = os.environ.copy()
    env.update({'PYTHONFAULTHANDLER':'1', 'PYTHONDONTWRITEBYTECODE':'1',
        'PGAPPNAME':'s10_p0_02_bounded',
        'PYTHONPATH':str(TARGET_RUN/'network-policy')+os.pathsep+str(ROOT/'.local/s04-deps'),
        'YDENTAL_S10_RUN_DIR':str(TARGET_RUN),
        'YDENTAL_S08C_HTTP_PORT':str(PORT)})
    return env


def clone(before):
    checkpoint()
    rows, activity = identity()
    assert TARGET not in rows and activity == [] and not TARGET_RUN.exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    source_gate(before)
    assert snapshot(SOURCE, business=True)['tables'] == before['tables']
    TARGET_RUN.mkdir(mode=0o700)
    (TARGET_RUN/'network-policy').mkdir(mode=0o700)
    policy = ROOT/'scripts/s08c_network_policy.py'
    (TARGET_RUN/'network-policy/sitecustomize.py').write_bytes(policy.read_bytes())
    source_fs = SOURCE_RUN/'data/filestore'/SOURCE
    target_fs = TARGET_RUN/'data/filestore'/TARGET
    for filename, digest in before['filestore']['files'].items():
        source_path = source_fs/filename
        assert file_sha(source_path) == digest
        target_path = target_fs/filename
        target_path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with source_path.open('rb') as reader, os.fdopen(os.open(target_path,
                os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'wb') as writer:
            shutil.copyfileobj(reader,writer)
    save_once(PRIVATE/'create-attempt.json',{'source_oid':SOURCE_OID,'target':TARGET,
        'checkpoint':checkpoint()['comment_id'], 'utc':datetime.now(timezone.utc).isoformat()})
    conn = psycopg2.connect(dbname='postgres',**credentials())
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(
                sql.Identifier(TARGET), sql.Identifier(SOURCE)))
    finally:
        conn.close()
    rows,_ = identity()
    assert TARGET in rows and rows[TARGET] != SOURCE_OID
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo',
        'db_password':credentials()['password'],'db_name':TARGET,'dbfilter':'^'+TARGET+'$',
        'addons_path':','.join(str(path) for path in (CORE/'odoo/addons',CORE/'addons',ROOT)),
        'data_dir':str(TARGET_RUN/'data'),'http_interface':'127.0.0.1',
        'http_port':str(PORT),'list_db':'False','workers':'0','max_cron_threads':'0',
        'admin_passwd':secrets.token_urlsafe(32),'smtp_server':'127.0.0.1','smtp_port':'1'}
    output = io.StringIO(); config.write(output)
    with os.fdopen(os.open(CONF,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as f:
        f.write(output.getvalue())
    marker = {'database':TARGET,'oid':rows[TARGET],'source':SOURCE,'source_oid':SOURCE_OID,
        'cluster':CLUSTER,'head':HEAD,'core':CORE_HEAD,
        'source_marker_sha256':SOURCE_MARKER,'source_config_sha256':SOURCE_CONFIG,
        'source_filestore_manifest_sha256':SOURCE_MANIFEST,'config_sha256':file_sha(CONF),
        'scripts_sha256':json.loads(PREFLIGHT.read_text())['scripts_sha256'],
        'checkpoint_id':checkpoint()['comment_id']}
    save_once(TARGET_RUN/'database.json',marker)
    return rows[TARGET]


def verify_target():
    mark = json.loads((TARGET_RUN/'database.json').read_text())
    rows,_ = identity()
    assert mark['database'] == TARGET and rows[TARGET] == mark['oid']
    assert mark['source_oid'] == SOURCE_OID and mark['cluster'] == CLUSTER
    assert mark['head'] == HEAD and mark['core'] == CORE_HEAD
    assert mark['config_sha256'] == file_sha(CONF)
    assert mark['checkpoint_id'] == checkpoint()['comment_id']
    return rows[TARGET]


def run_upgrade():
    verify_target()
    save_once(PRIVATE/'upgrade-attempt.json',{'argv':UPGRADE_ARGV,'oid':verify_target()})
    with (TARGET_RUN/'upgrade.log').open('xb') as log:
        process = subprocess.Popen(UPGRADE_ARGV,cwd=ROOT,env=private_env(),
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            code = process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(); raise RuntimeError('upgrade timeout; STOP')
    save_once(PRIVATE/'upgrade-result.json',{'pid':process.pid,'returncode':code,
        'log_sha256':file_sha(TARGET_RUN/'upgrade.log')})
    assert code == 0, ('upgrade_exit',code)
    return code


def start_http():
    verify_target()
    save_once(PRIVATE/'http-attempt.json',{'argv':HTTP_ARGV,'oid':verify_target()})
    log = (TARGET_RUN/'http.log').open('xb')
    process = subprocess.Popen(HTTP_ARGV,cwd=ROOT,env=private_env(),
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    log.close()
    began = time.monotonic()
    while time.monotonic()-began < 180:
        assert process.poll() is None, ('http_early_exit',process.returncode)
        try:
            with urlopen('http://127.0.0.1:'+str(PORT)+'/web/login',timeout=3) as response:
                if response.status == 200:
                    return process
        except Exception:
            time.sleep(1)
    process.terminate(); process.wait(timeout=15)
    raise RuntimeError('HTTP readiness timeout; STOP')


def execute_pipeline(ops):
    """The exact stage graph used by both the real adapter and fault injection."""
    before = ops.source_readonly()
    ops.check_source(before)
    cloned = ops.clone_compare(before)
    updated = ops.upgrade_diff(before, cloned)
    try:
        ops.start_http()
        ops.browser_flow(updated)
    finally:
        ops.stop_http()
    return ops.readonly_final(before, updated)


class RealOps:
    def __init__(self):
        self.http = None

    def source_readonly(self):
        checkpoint()
        before = snapshot(SOURCE,business=True)
        save_once(PRIVATE/'source-before.json',before)
        return before

    def check_source(self,before):
        source_gate(before)
        assert public(before)['tables'] == json.loads(PREFLIGHT.read_text())['source']['tables']

    def clone_compare(self,before):
        clone(before)
        cloned = snapshot(TARGET,business=True)
        equal_clone(before,cloned)
        save_once(PRIVATE/'clone-snapshot.json',cloned)
        return cloned

    def upgrade_diff(self,before,cloned):
        run_upgrade()
        updated = snapshot(TARGET,business=True)
        source_after = snapshot(SOURCE,business=True)
        save_once(PRIVATE/'upgrade-snapshot.json',updated)
        diff = diff_upgrade(cloned,updated,source_after)
        save_once(PRIVATE/'upgrade-gate.json',diff)
        return updated

    def start_http(self):
        self.http = start_http()
        save_once(PRIVATE/'http-ready.json',{'pid':self.http.pid,'oid':verify_target()})

    def browser_flow(self,updated):
        save_once(PRIVATE/'browser-attempt.json',{'argv':BROWSER_ARGV,'oid':verify_target()})
        with (TARGET_RUN/'browser.log').open('xb') as log:
            browser = subprocess.Popen(BROWSER_ARGV,cwd=ROOT,env=private_env(),
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:
                code = browser.wait(timeout=1200)
            except subprocess.TimeoutExpired:
                browser.kill(); browser.wait(); raise RuntimeError('browser timeout; STOP')
        save_once(PRIVATE/'browser-result.json',{'pid':browser.pid,'returncode':code,
            'log_sha256':file_sha(TARGET_RUN/'browser.log')})
        assert code == 0, ('browser_exit',code)

    def stop_http(self):
        if self.http is None:
            return
        if self.http.poll() is None:
            self.http.terminate()
            try: self.http.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.http.kill(); self.http.wait()
        save_once(PRIVATE/'http-result.json',{'pid':self.http.pid,
            'returncode':self.http.returncode,'log_sha256':file_sha(TARGET_RUN/'http.log')})

    def readonly_final(self,before,updated):
        assert file_sha(SOURCE_RUN/'odoo.conf') == SOURCE_CONFIG
        assert file_sha(SOURCE_RUN/'database.json') == SOURCE_MARKER
        verify_target()
        final = snapshot(TARGET,business=True)
        source_final = snapshot(SOURCE,business=True)
        assert source_final['tables'] == before['tables']
        assert source_final['schema'] == before['schema']
        assert source_final['modules'] == before['modules']
        assert source_final['views'] == before['views']
        assert source_final['view_rows'] == before['view_rows']
        assert source_final['filestore'] == before['filestore']
        assert source_final['protected_other_rows'] == before['protected_other_rows']
        assert source_final['attachment_pointers'] == before['attachment_pointers']
        diff_web(updated,final,refund_done=True,close_done=True)
        save_once(PRIVATE/'final-snapshot.json',final)
        return final


def run():
    return execute_pipeline(RealOps())


if __name__ == '__main__':
    assert sys.argv[1:] == ['run']
    run()
