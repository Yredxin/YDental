"""One-use P0-04 controller. All database inspection uses read-only connections."""

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
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import psycopg2
from psycopg2 import sql

import s10_p0_02_snapshot as r3
import s10_p0_03_snapshot as p003
import s10_p0_04_snapshot as s

os.umask(0o077)
ROOT, CORE = s.ROOT, s.CORE
PRIVATE = ROOT / '.local/s10-p0-04'
PREFLIGHT = ROOT / 'docs/evidence/s10-p0-04/preflight.json'
CHECKPOINT = PRIVATE / 'checkpoint.json'
CONF = s.TARGET_RUN / 'odoo.conf'
PYTHON = CORE / '.venv/bin/python'
HTTP_ARGV = (str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(CONF))
BROWSER_ARGV = (str(PYTHON), str(ROOT / 'scripts/s10_p0_04_browser.py'))
SCRIPTS = tuple(sorted((ROOT / 'scripts').glob('s10_p0_04_*.py')))
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6205786507
WEB_TABLES = frozenset({
    'ir_attachment', 'mail_message', 'res_users', 'res_partner', 'hr_employee',
    'hr_version', 'resource_resource', 'res_users_log', 'res_device_log',
    'ydental_access_audit', 'ydental_access_session', 'orm_signaling_default',
    'ydental_settlement_refund', 'ydental_settlement_close',
    'ydental_settlement_mutex', 'ydental_settlement_receipt',
})
ROW_TABLES = WEB_TABLES
NO_MAIL_TABLES = ('mail_mail', 'mail_notification', 'mail_message_res_partner_rel')
ACTORS = {6: (7, 2, 2), 10: (11, 6, 6), 14: (16, 10, 10)}
ASSET_PATTERN = re.compile(r'^/web/assets/[0-9a-f]{7}/web\.[A-Za-z0-9_]+\.min\.(?:woff2|css|js)$')


def save_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, default=str) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert path.read_bytes() == data


def authority():
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == BRANCH
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == s.HEAD
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH], cwd=ROOT, text=True).split()
    assert len(remote) == 2 and remote[0] == s.HEAD
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CORE, text=True).strip() == s.CORE_HEAD
    assert subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode == 0
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    assert s.file_sha(s.SOURCE_RUN / 'odoo.conf') == s.SOURCE_CONFIG
    assert s.file_sha(s.SOURCE_RUN / 'database.json') == s.SOURCE_MARKER
    assert s.file_sha(p003.SOURCE_RUN / 'odoo.conf') == p003.SOURCE_CONFIG
    assert s.file_sha(p003.SOURCE_RUN / 'database.json') == p003.SOURCE_MARKER
    assert r3.file_sha(r3.SOURCE_RUN / 'odoo.conf') == r3.SOURCE_CONFIG
    assert r3.file_sha(r3.SOURCE_RUN / 'database.json') == r3.SOURCE_MARKER
    expected = {
        'ydental_settlement/controllers/settlement.py': 'bfa051971585369f1585d311cfc4553159d4a42ef23b3c54f35d77e53ab4caa2',
        'ydental_settlement/models/ydental_settlement_service.py': '1ea27012fd5500fc21891f9e652f4e694cb2e7cce844fa38d08b7f12beff8d2c',
        'ydental_settlement/views/ydental_settlement_templates.xml': '8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329',
    }
    assert {p: s.file_sha(ROOT / p) for p in expected} == expected
    return expected


def all_tables(name):
    with s.connect(name) as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        names = [row[0] for row in cur.fetchall()]
        signatures = {table: s.full_rows(cur, table) for table in names}
        rows = {}
        for table in ROW_TABLES:
            cur.execute(sql.SQL('SELECT to_jsonb(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
            rows[table] = {int(value['id']): value for (raw,) in cur.fetchall() for value in (json.loads(raw),)}
    return {'signatures': signatures, 'rows': rows}


def capture(name, *, business=False):
    return {'managed': s.snapshot(name, business=business), 'all': all_tables(name)}


def load_capture(path):
    result = json.loads(Path(path).read_text())
    result['all']['rows'] = {
        table: {int(i): row for i, row in rows.items()}
        for table, rows in result['all']['rows'].items()}
    return result


def source_gate(r3_now, p002_now, observed):
    old_r3 = json.loads((ROOT / '.local/s10-p0-02/source-before.json').read_text())
    for key in ('tables', 'schema', 'modules', 'views', 'view_rows', 'filestore', 'attachment_pointers'):
        assert r3_now[key] == old_r3[key], ('R3_drift', key)
    old_p002 = json.loads((ROOT / '.local/s10-p0-03/source-before.json').read_text())
    assert json.loads(json.dumps(p002_now, default=str)) == old_p002['managed'], 'P0-02 drift'
    stopped = load_capture(ROOT / '.local/s10-p0-03/stopped-readonly.json')
    assert observed['all']['signatures'] == stopped['all']['signatures'], 'P0-03 public tables drift'
    assert {k:observed['all']['rows'][k] for k in stopped['all']['rows']} == stopped['all']['rows'], 'P0-03 field rows drift'
    assert {k:v for k,v in observed['managed'].items() if k != 'business'} == {k:v for k,v in stopped['managed'].items() if k != 'business'}, 'P0-03 managed snapshot drift'
    source = observed['managed']
    assert source['database'] == s.SOURCE and source['oid'] == s.SOURCE_OID
    assert source['cluster'] == s.CLUSTER and len(source['tables']) == 265
    assert len(observed['all']['signatures']) == 643
    assert source['filestore']['count'] == 194 and source['filestore']['sha256'] == s.SOURCE_MANIFEST
    assert source['attachment_pointers'] == 1075
    assert len(source['modules']) == 702 and sum(v['state'] == 'installed' for v in source['modules'].values()) == 92
    assert source['business']['refund14'][:3] == ['rejected', '5', '1']
    assert source['business']['close9'][0] == 'confirmed' and source['business']['close9_latest'] == 9
    assert 14 in source['business']['refund_page2_ids'] and 9 in source['business']['close_page2_ids']
    assert observed['all']['rows']['ydental_settlement_refund'][14]['ydental_approver_id'] == 6
    assert observed['all']['rows']['ydental_settlement_close'][9]['ydental_state'] == 'confirmed'
    assert set(observed['all']['rows']['ydental_settlement_mutex']) == {1}
    assert observed['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision'] == 243
    receipts = observed['all']['rows']['ydental_settlement_receipt']
    assert len(receipts) == 242 and receipts[242]['ydental_operation'] == 'refund_reject'
    assert receipts[242]['ydental_actor_id'] == 6 and receipts[242]['ydental_store_id'] == 1
    assert receipts[242]['ydental_result'] == {'refund_id':14,'state':'rejected','actually_refunded':0,'credit_note_id':False}
    refund_intent = json.loads((ROOT / '.local/s10-p0-03/refund_reject-intent.json').read_text())
    assert receipts[242]['ydental_key'] and s.sha(receipts[242]['ydental_key'].encode()) == json.loads((ROOT/'docs/evidence/s10-p0-03/blocked.json').read_text())['hard_gate']['idempotent_command_receipt']['key_sha256']
    assert refund_intent['operation'] == 'refund_reject' and refund_intent['record'] == 14
    with s.connect(s.SOURCE) as conn, conn.cursor() as cur:
        cur.execute("SELECT model,res_id FROM ir_model_data WHERE module='ydental_settlement' AND name='ydental_settlement_mutex'")
        assert cur.fetchall() == [('ydental.settlement.mutex',1)]
    conn.close()
    assert all(x['has_output_html'] for x in source['views']['ydental_settlement.ydental_settlement_tokens']['languages'].values())
    with s.connect('postgres') as conn, conn.cursor() as cur:
        names = (r3.SOURCE, p003.SOURCE, s.SOURCE)
        cur.execute('SELECT datname,oid FROM pg_database WHERE datname IN %s', (names,))
        assert dict(cur.fetchall()) == {r3.SOURCE:r3.SOURCE_OID, p003.SOURCE:p003.SOURCE_OID, s.SOURCE:s.SOURCE_OID}
        cur.execute('SELECT datname,pid,state FROM pg_stat_activity WHERE datname IN %s AND pid<>pg_backend_pid()', (names,))
        assert not cur.fetchall(), 'historical source has live connection'
    assert observed['all']['signatures'] == json.loads(PREFLIGHT.read_text())['source_all_signatures']
    return True


def clone_equal(before, after):
    assert after['managed']['database'] == s.TARGET and after['managed']['oid'] != s.SOURCE_OID
    for key in ('tables', 'schema', 'modules', 'views', 'view_rows', 'filestore', 'attachment_pointers'):
        assert after['managed'][key] == before['managed'][key], ('clone_drift', key)
    assert after['all'] == before['all'], 'all 643 public tables changed in clone'
    return True


def changed(a, b):
    return {key for key in set(a) | set(b) if a.get(key) != b.get(key)}


def append_only(old, new, max_new):
    assert set(old) <= set(new)
    assert all(old[i] == new[i] for i in old)
    ids = sorted(set(new) - set(old))
    assert len(ids) <= max_new
    return ids


def web_diff(before, after, *, unlock=False, intent=None, denied_actor=None):
    a, b = before['managed'], after['managed']
    assert a['schema'] == b['schema']
    assert a['modules'] == b['modules'] and a['views'] == b['views'] and a['view_rows'] == b['view_rows']
    assert set(before['all']['signatures']) == set(after['all']['signatures'])
    for table in before['all']['signatures']:
        if table not in WEB_TABLES:
            assert before['all']['signatures'][table] == after['all']['signatures'][table], ('unauthorized_table', table)
    assert all(before['all']['signatures'][t] == after['all']['signatures'][t] for t in NO_MAIL_TABLES)
    assert all(a['tables'][t] == b['tables'][t] for t in s.MONEY_TABLES)
    assert a['protected_other_rows'] == b['protected_other_rows']
    for table, identifier, allowed in (
        ('ydental_settlement_refund', 14, set()),
        ('ydental_settlement_close', 9, {'ydental_state', 'ydental_unlocked_by_id', 'ydental_unlock_reason', 'ydental_unlocked_at', 'write_uid', 'write_date'} if unlock else set()),
    ):
        old, new = before['all']['rows'][table], after['all']['rows'][table]
        assert set(old) == set(new)
        for i in old:
            assert changed(old[i], new[i]) <= (allowed if i == identifier else set()), (table, i)
    assert b['business'] is None or b['business']['refund14'][0] == 'rejected'
    if unlock:
        assert intent and intent['operation'] == 'unlock' and intent['close_id'] == 9
        old_close, new_close = before['all']['rows']['ydental_settlement_close'][9], after['all']['rows']['ydental_settlement_close'][9]
        assert old_close['ydental_state'] == 'confirmed' and new_close['ydental_state'] == 'unlocked'
        assert new_close['ydental_unlocked_by_id'] == new_close['write_uid'] == 6
        assert new_close['ydental_unlock_reason'] == intent['reason'] and new_close['ydental_unlocked_at']
        assert new_close['write_date'] != old_close['write_date']
        assert old_close['ydental_store_id'] == 1 and old_close['ydental_cashier_id'] == 5
        assert old_close['ydental_business_date'] == '2026-07-15' and old_close['ydental_channel'] == 'card'
        assert old_close['ydental_cycle'] == 1 and old_close['ydental_gross'] == old_close['ydental_refunded'] == old_close['ydental_pending'] == 0
        assert old_close['ydental_confirmed_at'] == new_close['ydental_confirmed_at']
    else:
        assert intent is None
    old_mutex, new_mutex = before['all']['rows']['ydental_settlement_mutex'], after['all']['rows']['ydental_settlement_mutex']
    assert set(old_mutex) == set(new_mutex) == {1}
    assert old_mutex[1]['ydental_revision'] == (243 if unlock else new_mutex[1]['ydental_revision'])
    assert changed(old_mutex[1], new_mutex[1]) == ({'ydental_revision'} if unlock else set())
    if unlock:
        assert new_mutex[1]['ydental_revision'] == 244
    old_receipts, new_receipts = before['all']['rows']['ydental_settlement_receipt'], after['all']['rows']['ydental_settlement_receipt']
    assert set(old_receipts) <= set(new_receipts) and all(new_receipts[i] == row for i,row in old_receipts.items())
    new_ids = set(new_receipts) - set(old_receipts)
    assert len(new_ids) == (1 if unlock else 0)
    if unlock:
        receipt = new_receipts[new_ids.pop()]
        assert receipt['ydental_actor_id'] == receipt['create_uid'] == receipt['write_uid'] == 6
        assert receipt['ydental_store_id'] == 1 and receipt['ydental_operation'] == 'unlock'
        assert receipt['ydental_key'] == intent['key'] and intent['key']
        assert not any(row['ydental_actor_id'] == 6 and row['ydental_store_id'] == 1 and row['ydental_key'] == intent['key'] for row in old_receipts.values())
        payload = ['unlock', 1, {'close_id': 9, 'reason': intent['reason']}]
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        assert receipt['ydental_fingerprint'] == fingerprint
        assert receipt['ydental_result'] == {'close_id': 9, 'state': 'unlocked'}
    oldf, newf = a['filestore']['files'], b['filestore']['files']
    assert b['filestore']['count'] == len(newf)
    manifest = s.sha(b''.join((key + ' ' + newf[key] + '\n').encode() for key in sorted(newf)))
    assert b['filestore']['sha256'] == manifest
    assert all(newf.get(k) == v for k, v in oldf.items())
    newfiles = set(newf) - set(oldf)
    assert len(newfiles) <= 20
    attachments = append_only(before['all']['rows']['ir_attachment'], after['all']['rows']['ir_attachment'], 10)
    assert b['attachment_pointers'] == a['attachment_pointers'] + len(attachments)
    expected_files = set()
    for ident in attachments:
        row = after['all']['rows']['ir_attachment'][ident]
        template = before['all']['rows']['ir_attachment'][1075]
        assert changed(template, row) <= {'id', 'url', 'name', 'checksum', 'mimetype',
            'file_size', 'write_date', 'create_date', 'store_fname', 'index_content'}
        assert row['res_model'] == 'ir.ui.view' and row['res_id'] == 0
        assert row['type'] == 'binary' and row['public'] is True
        assert row['create_uid'] == row['write_uid'] == 1
        assert ASSET_PATTERN.fullmatch(row['url']) and row['name'] == row['url'].rsplit('/', 1)[-1]
        mime = {'woff2': 'font/woff2', 'js': 'application/javascript', 'css': 'text/css'}[row['name'].rsplit('.', 1)[-1]]
        assert row['mimetype'] == mime and 0 < row['file_size'] <= 3000000
        fname = row['store_fname']
        data = (s.TARGET_RUN / 'data/filestore' / s.TARGET / fname).read_bytes()
        assert len(data) == row['file_size'] and hashlib.sha1(data).hexdigest() == row['checksum']
        assert s.sha(data) == newf[fname]
        assert data.startswith(b'wOF2' if mime == 'font/woff2' else b'\n/* ')
        index_content = row.get('index_content')
        if index_content is not None:
            assert mime == 'text/css' and len(index_content.encode()) <= len(data)
            assert index_content[:40].encode() in data
        expected_files |= {fname, 'checklist/' + fname}
        marker = s.TARGET_RUN / 'data/filestore' / s.TARGET / ('checklist/' + fname)
        assert marker.stat().st_size == 0 and newf['checklist/' + fname] == s.sha(b'')
    assert newfiles == expected_files, ('unexpected_filestore', sorted(newfiles - expected_files))
    users = append_only(before['all']['rows']['res_users_log'], after['all']['rows']['res_users_log'], 3)
    for ident in users:
        row = after['all']['rows']['res_users_log'][ident]
        assert row['create_uid'] in ACTORS and row['write_uid'] == row['create_uid']
    devices = append_only(before['all']['rows']['res_device_log'], after['all']['rows']['res_device_log'], 3)
    for ident in devices:
        row = after['all']['rows']['res_device_log'][ident]
        assert row['user_id'] in ACTORS and row['ip_address'] == '127.0.0.1'
        assert 'Firefox/' in row['user_agent'] and row['revoked'] is False
    sessions = append_only(before['all']['rows']['ydental_access_session'], after['all']['rows']['ydental_access_session'], 3)
    for ident in sessions:
        row = after['all']['rows']['ydental_access_session'][ident]
        assert row['ydental_user_id'] in ACTORS
        assert row['ydental_store_id'] in (1, 3)
        assert row['ydental_revision'] in (0, 1)
        assert any(hashlib.sha256(dev['session_identifier'].encode()).hexdigest() == row['ydental_key_hash']
                   and dev['user_id'] == row['ydental_user_id'] for dev in after['all']['rows']['res_device_log'].values())
    for table, make_ids, permitted in (
        ('res_users', lambda uid, ids: uid, {'write_uid', 'write_date'}),
        ('res_partner', lambda uid, ids: ids[0], {'tz', 'write_uid', 'write_date'}),
        ('hr_employee', lambda uid, ids: ids[1], {'write_uid', 'write_date'}),
        ('hr_version', lambda uid, ids: ids[2], {'last_modified_date', 'last_modified_uid', 'write_uid', 'write_date'}),
        ('resource_resource', lambda uid, ids: ids[2], {'write_uid', 'write_date'}),
    ):
        old, new = before['all']['rows'][table], after['all']['rows'][table]
        assert set(old) == set(new)
        allow = {make_ids(uid, ids): uid for uid, ids in ACTORS.items()}
        for ident in old:
            fields = changed(old[ident], new[ident])
            assert not fields or (ident in allow and fields <= permitted), (table, ident, fields)
            if fields and 'tz' in fields:
                assert old[ident]['tz'] is None and new[ident]['tz'] == 'UTC'
            if fields and 'write_uid' in fields:
                assert new[ident]['write_uid'] == allow[ident]
            if fields and 'last_modified_uid' in fields:
                assert new[ident]['last_modified_uid'] == allow[ident]
    messages = append_only(before['all']['rows']['mail_message'], after['all']['rows']['mail_message'], 4)
    for ident in messages:
        row = after['all']['rows']['mail_message'][ident]
        uid = row['create_uid']
        assert uid in (10, 14) and row['write_uid'] == uid
        assert row['model'] in ('res.users', 'hr.employee')
        assert row['res_id'] == (uid if row['model'] == 'res.users' else ACTORS[uid][1])
        assert row['message_type'] == 'tracking' and row['subtype_id'] == 2
        assert row['author_id'] == ACTORS[uid][0] and row['is_internal'] is True
        assert '受邀' in (row.get('body') or '') and '已确认' in (row.get('body') or '')
        assert '<a ' not in row['body'] and 'http' not in row['body'].lower()
    audits = append_only(before['all']['rows']['ydental_access_audit'], after['all']['rows']['ydental_access_audit'], 11)
    for ident in audits:
        row = after['all']['rows']['ydental_access_audit'][ident]
        event, uid = row['ydental_event'], row['ydental_user_id']
        assert uid in ACTORS and row['create_uid'] == row['write_uid'] == uid
        assert event in {'login', 'login.scope', 'store.switch', 'settlement.unlock', 'settlement.action'}
        if event == 'settlement.unlock':
            assert unlock and uid == 6 and row['ydental_store_id'] == 1
            assert row['ydental_target_id'] == 9 and row['ydental_target_model'] == 'ydental.settlement.close'
            assert row['ydental_category'] == 'settlement' and row['ydental_result'] == 'accepted'
            assert row['ydental_source'] == 'confirmed_offline_transaction'
            assert row['ydental_reason'] == intent['reason'] and row['ydental_after'] == {'cycle': 1}
        elif event == 'settlement.action':
            assert denied_actor in (10,14) and uid == denied_actor
            assert row['ydental_result'] == 'denied' and row['ydental_target_id'] == 9
        else:
            assert row['ydental_category'] == 'personnel' and row['ydental_result'] == 'accepted'
            assert row['ydental_target_model'] == ('res.users' if event == 'login' else 'ydental.access.session')
            if event == 'login':
                assert row['ydental_target_id'] == uid and row['ydental_source'] == 'native_authenticated_login'
            else:
                assert row['ydental_target_id'] in after['all']['rows']['ydental_access_session']
    accepted = [i for i in audits if after['all']['rows']['ydental_access_audit'][i]['ydental_event'] == 'settlement.unlock']
    assert len(accepted) == (1 if unlock else 0)
    signal_ids = append_only(before['all']['rows']['orm_signaling_default'],
                             after['all']['rows']['orm_signaling_default'], 3)
    assert all(set(after['all']['rows']['orm_signaling_default'][i]) == {'id', 'date'}
               for i in signal_ids)
    return {'new_asset_ids': attachments, 'new_files': sorted(newfiles), 'new_mail_ids': messages,
            'new_audit_ids': audits, 'unlock_audit_ids': accepted,
            'new_receipt_ids': sorted(set(new_receipts) - set(old_receipts)),
            'mutex_revision': new_mutex[1]['ydental_revision'],
            'new_session_ids': sessions, 'new_device_ids': devices}


def checkpoint():
    authority()
    pre = json.loads(PREFLIGHT.read_text())
    mark = json.loads(CHECKPOINT.read_text())
    assert mark['comment_id'] > AUTH and mark['preflight_sha256'] == s.file_sha(PREFLIGHT)
    assert mark['body_sha256'] and len(mark['body_sha256']) == 64
    assert pre['target'] == s.TARGET and pre['source']['oid'] == s.SOURCE_OID
    expected = pre['scripts_sha256']
    assert set(expected) == {str(p.relative_to(ROOT)) for p in SCRIPTS}
    assert all(s.file_sha(ROOT / p) == h for p, h in expected.items())
    assert pre['http_argv'] == list(HTTP_ARGV) and pre['browser_argv'] == list(BROWSER_ARGV)
    return mark


def private_env():
    env = os.environ.copy()
    env.update({'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                'PGAPPNAME': 's10_p0_04_bounded',
                'PYTHONPATH': str(s.TARGET_RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
                'YDENTAL_S10_RUN_DIR': str(s.TARGET_RUN), 'YDENTAL_S08C_HTTP_PORT': str(s.PORT)})
    return env


def clone(before):
    checkpoint()
    rows, activity = s.identity()
    assert s.TARGET not in rows and not activity and not s.TARGET_RUN.exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', s.PORT))
    latest = capture(s.SOURCE, business=True)
    assert latest == before, 'source changed before CREATE'
    s.TARGET_RUN.mkdir(mode=0o700)
    (s.TARGET_RUN / 'network-policy').mkdir(mode=0o700)
    policy = ROOT / 'scripts/s08c_network_policy.py'
    (s.TARGET_RUN / 'network-policy/sitecustomize.py').write_bytes(policy.read_bytes())
    oldfs = s.SOURCE_RUN / 'data/filestore' / s.SOURCE
    newfs = s.TARGET_RUN / 'data/filestore' / s.TARGET
    for name, digest in before['managed']['filestore']['files'].items():
        assert s.file_sha(oldfs / name) == digest
        path = newfs / name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (oldfs / name).open('rb') as reader, os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as writer:
            shutil.copyfileobj(reader, writer)
    save_once(PRIVATE / 'create-attempt.json', {'source_oid': s.SOURCE_OID, 'target': s.TARGET,
                                                'checkpoint': checkpoint()['comment_id'],
                                                'utc': datetime.now(timezone.utc).isoformat()})
    conn = psycopg2.connect(dbname='postgres', **s.credentials())
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(s.TARGET), sql.Identifier(s.SOURCE)))
    finally:
        conn.close()
    rows, _ = s.identity()
    assert rows[s.TARGET] != s.SOURCE_OID
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
        'db_password': s.credentials()['password'], 'db_name': s.TARGET, 'dbfilter': '^' + s.TARGET + '$',
        'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
        'data_dir': str(s.TARGET_RUN / 'data'), 'http_interface': '127.0.0.1',
        'http_port': str(s.PORT), 'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
        'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    text = io.StringIO(); config.write(text)
    with os.fdopen(os.open(CONF, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        stream.write(text.getvalue())
    save_once(s.TARGET_RUN / 'database.json', {'database': s.TARGET, 'oid': rows[s.TARGET],
        'source': s.SOURCE, 'source_oid': s.SOURCE_OID, 'cluster': s.CLUSTER,
        'head': s.HEAD, 'core': s.CORE_HEAD, 'source_marker_sha256': s.SOURCE_MARKER,
        'source_config_sha256': s.SOURCE_CONFIG, 'source_filestore_manifest_sha256': s.SOURCE_MANIFEST,
        'config_sha256': s.file_sha(CONF), 'scripts_sha256': json.loads(PREFLIGHT.read_text())['scripts_sha256'],
        'checkpoint_id': checkpoint()['comment_id']})
    return rows[s.TARGET]


def verify_target():
    mark = json.loads((s.TARGET_RUN / 'database.json').read_text())
    rows, _ = s.identity()
    assert mark['database'] == s.TARGET and rows[s.TARGET] == mark['oid']
    assert mark['source_oid'] == s.SOURCE_OID and mark['cluster'] == s.CLUSTER
    assert mark['head'] == s.HEAD and mark['core'] == s.CORE_HEAD
    assert mark['config_sha256'] == s.file_sha(CONF)
    assert mark['checkpoint_id'] == checkpoint()['comment_id']
    return rows[s.TARGET]


def start_http():
    verify_target()
    save_once(PRIVATE / 'http-attempt.json', {'argv': HTTP_ARGV, 'oid': verify_target()})
    log = (s.TARGET_RUN / 'http.log').open('xb')
    process = subprocess.Popen(HTTP_ARGV, cwd=ROOT, env=private_env(), stdin=subprocess.DEVNULL,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    log.close()
    began = time.monotonic()
    while time.monotonic() - began < 180:
        assert process.poll() is None, ('http_early_exit', process.returncode)
        try:
            with urlopen(f'http://127.0.0.1:{s.PORT}/web/login', timeout=3) as response:
                if response.status == 200:
                    return process
        except Exception:
            time.sleep(1)
    process.terminate(); process.wait(timeout=15)
    raise RuntimeError('HTTP readiness timeout; STOP')


def execute_pipeline(ops):
    before = ops.source_readonly()
    ops.check_source(before)
    clone = ops.clone_compare(before)
    try:
        ops.start_http()
        ops.browser_flow(clone)
    finally:
        ops.stop_http()
    return ops.readonly_final(before, clone)


class RealOps:
    def __init__(self):
        self.http = None
        self.started = None

    def source_readonly(self):
        checkpoint()
        before = capture(s.SOURCE, business=True)
        save_once(PRIVATE / 'source-before.json', before)
        return before

    def check_source(self, before):
        source_gate(r3.snapshot(r3.SOURCE, business=True),
                    p003.snapshot(p003.SOURCE, business=True), before)
        assert before['managed']['tables'] == json.loads(PREFLIGHT.read_text())['source_tables']

    def clone_compare(self, before):
        clone(before)
        after = capture(s.TARGET, business=True)
        clone_equal(before, after)
        save_once(PRIVATE / 'clone-snapshot.json', after)
        return after

    def start_http(self):
        self.http = start_http()
        self.started = time.monotonic()
        save_once(PRIVATE / 'http-ready.json', {'pid': self.http.pid, 'oid': verify_target()})

    def browser_flow(self, clone):
        assert time.monotonic() - self.started < 1200
        save_once(PRIVATE / 'browser-attempt.json', {'argv': BROWSER_ARGV, 'oid': verify_target()})
        with (s.TARGET_RUN / 'browser.log').open('xb') as log:
            browser = subprocess.Popen(BROWSER_ARGV, cwd=ROOT, env=private_env(),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            try:
                code = browser.wait(timeout=min(1200, 1200 - (time.monotonic() - self.started)))
            except subprocess.TimeoutExpired:
                browser.kill(); browser.wait(); raise RuntimeError('browser timeout; STOP')
        save_once(PRIVATE / 'browser-result.json', {'pid': browser.pid, 'returncode': code,
                                                   'log_sha256': s.file_sha(s.TARGET_RUN / 'browser.log')})
        assert code == 0, ('browser_exit', code)

    def stop_http(self):
        if self.http is None:
            return
        if self.http.poll() is None:
            self.http.terminate()
            try: self.http.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.http.kill(); self.http.wait()
        save_once(PRIVATE / 'http-result.json', {'pid': self.http.pid,
                                                 'returncode': self.http.returncode,
                                                 'log_sha256': s.file_sha(s.TARGET_RUN / 'http.log')})
        # Preserve the committed state even when the browser stopped after a POST.
        try:
            observed = capture(s.TARGET, business=False)
            save_once(PRIVATE / 'stopped-readonly.json', observed)
        except Exception as error:
            save_once(PRIVATE / 'stopped-readonly-error.json', {'type': type(error).__name__,
                                                               'detail': str(error)[:300]})

    def readonly_final(self, before, clone):
        verify_target()
        assert capture(s.SOURCE, business=True) == before
        assert r3.snapshot(r3.SOURCE, business=True)['tables'] == json.loads((ROOT / '.local/s10-p0-02/source-before.json').read_text())['tables']
        after = capture(s.TARGET, business=True)
        intent = json.loads((PRIVATE/'unlock-user6-intent.json').read_text())
        gate = web_diff(clone, after, unlock=True, intent=intent)
        save_once(PRIVATE / 'final-snapshot.json', after)
        save_once(PRIVATE / 'final-gate.json', gate)
        return after


def run():
    return execute_pipeline(RealOps())


if __name__ == '__main__':
    assert sys.argv[1:] == ['run']
    run()
