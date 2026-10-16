"""One-use P0-07 controller. All database inspection uses read-only connections."""

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

import s10_p0_07_snapshot as s

os.umask(0o077)
ROOT, CORE = s.ROOT, s.CORE
PRIVATE = ROOT / '.local/s10-p0-07-6206799419'
PREFLIGHT = ROOT / 'docs/evidence/s10-p0-07/preflight.json'
CHECKPOINT = PRIVATE / 'checkpoint.json'
CONF = s.TARGET_RUN / 'odoo.conf'
PYTHON = CORE / '.venv/bin/python'
HTTP_ARGV = (str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(CONF))
BROWSER_ARGV = (str(PYTHON), str(ROOT / 'scripts/s10_p0_07_browser.py'))
SCRIPTS = tuple(sorted((ROOT / 'scripts').glob('s10_p0_07_*.py')))
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6206799419
WEB_TABLES = frozenset({
    'ir_attachment', 'mail_message', 'res_users', 'res_partner', 'hr_employee',
    'hr_version', 'resource_resource', 'res_users_log', 'res_device_log',
    'ydental_access_audit', 'ydental_access_session', 'orm_signaling_default',
    'ydental_settlement_refund', 'ydental_settlement_close',
    'ydental_settlement_mutex', 'ydental_settlement_receipt',
})
ROW_TABLES = WEB_TABLES
WEB_TABLES = WEB_TABLES - {'ydental_settlement_refund','ydental_settlement_close','ydental_settlement_mutex','ydental_settlement_receipt'}
NO_MAIL_TABLES = ('mail_mail', 'mail_notification', 'mail_message_res_partner_rel')
ACTORS = {6: (7, 2, 2), 14: (16, 10, 10)}
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
    assert subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip() == 'https://github.com/Yredxin/YDental.git'
    assert subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode == 0
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    assert s.file_sha(s.SOURCE_RUN / 'odoo.conf') == s.SOURCE_CONFIG
    assert s.file_sha(s.SOURCE_RUN / 'database.json') == s.SOURCE_MARKER
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


def equivalent(a, b):
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def source_gate(observed):
    stopped = load_capture(ROOT / '.local/s10-p0-06/stopped-readonly.json')
    assert equivalent(observed['all'], stopped['all']), 'P006 full public tables or fields drift'
    assert equivalent({k:v for k,v in observed['managed'].items() if k != 'business'},
                      {k:v for k,v in stopped['managed'].items() if k != 'business'}), 'P006 managed drift'
    public = json.loads((ROOT/'docs/evidence/s10-p0-06/business-before-after.json').read_text())
    assert observed['all']['signatures'] == public['after_all_643_table_signatures']
    assert observed['managed']['tables'] == public['after_265_managed_table_signatures']
    m=observed['managed']; rows=observed['all']['rows']
    assert m['database']==s.SOURCE and m['oid']==s.SOURCE_OID and m['cluster']==s.CLUSTER
    assert len(m['tables'])==265 and len(observed['all']['signatures'])==643
    assert m['schema']['sha256']=='3e2c00487260472ad97ca84a68b7e4c1717364715df7e930ecba6ac766f70b1e'
    assert m['filestore']['count']==194 and m['filestore']['sha256']==s.SOURCE_MANIFEST
    assert m['attachment_pointers']==1075 and len(m['modules'])==702
    assert sum(v['state']=='installed' for v in m['modules'].values())==92
    assert m['business']['close9']==['unlocked','1','5','2026-07-15','card','1','0.00','0.00','0.00']
    assert rows['ydental_settlement_close'][9]['ydental_unlocked_by_id']==6
    assert rows['ydental_settlement_refund'][14]['ydental_state']=='rejected'
    assert rows['ydental_settlement_refund'][14]['ydental_approver_id']==6
    assert rows['ydental_access_audit'][2661]['ydental_event']=='settlement.refund.reject'
    assert rows['ydental_access_audit'][2689]['ydental_event']=='settlement.unlock'
    assert set(rows['ydental_settlement_mutex'])=={1}
    assert rows['ydental_settlement_mutex'][1]['ydental_revision']==244
    receipts=rows['ydental_settlement_receipt'];assert len(receipts)==243
    assert receipts[242]['ydental_operation']=='refund_reject'
    assert receipts[243]['ydental_operation']=='unlock'
    assert receipts[243]['ydental_result']=={'close_id':9,'state':'unlocked'}
    grants={tuple(x) for x in m['business']['grants']}
    assert {(6,1,'settlement','write'),(6,1,'finance_approval','write'),
            (14,3,'settlement','write'),(14,3,'finance_approval','write')}<=grants
    assert not any(x[0]==14 and x[1]==1 for x in grants)
    assert all(v['has_output_html'] for v in m['views']['ydental_settlement.ydental_settlement_tokens']['languages'].values())
    return True


def historical_activity_gate():
    names={'ydental_s10_test_20261014020300_8b6c1d4e':2056451,
           'ydental_s10_test_20261015_p002_6d84a2c1':2100311,
           'ydental_s10_test_20261016_p003_75c1e9b2':2100319,
           'ydental_s10_test_20261016_p004_9a6e37f2':2100320,s.SOURCE:s.SOURCE_OID}
    with s.connect('postgres') as conn,conn.cursor() as cur:
        cur.execute('SELECT datname,oid FROM pg_database WHERE datname IN %s',(tuple(names),))
        assert dict(cur.fetchall())==names
        cur.execute('SELECT datname,pid,state FROM pg_stat_activity WHERE datname IN %s',(tuple(names),))
        assert not cur.fetchall(),'historical database has active connections'
    return names


def clone_equal(before, after):
    assert after['managed']['database'] == s.TARGET and after['managed']['oid'] != s.SOURCE_OID
    for key in ('tables', 'schema', 'modules', 'views', 'view_rows', 'filestore', 'attachment_pointers'):
        assert after['managed'][key] == before['managed'][key], ('clone_drift', key)
    assert equivalent(after['all'],before['all']), 'all 643 public tables changed in clone'
    return True


def changed(a, b):
    return {key for key in set(a) | set(b) if a.get(key) != b.get(key)}


def append_only(old, new, max_new):
    assert set(old) <= set(new)
    assert all(old[i] == new[i] for i in old)
    ids = sorted(set(new) - set(old))
    assert len(ids) <= max_new
    return ids


def web_diff(before, after, *, gets=()):
    a,b=before['managed'],after['managed']
    for key in ('schema','modules','views','view_rows','protected_other_rows'):
        assert equivalent(a[key],b[key]),('protected_metadata',key)
    assert set(before['all']['signatures'])==set(after['all']['signatures'])
    for table in before['all']['signatures']:
        if table not in WEB_TABLES:
            assert before['all']['signatures'][table]==after['all']['signatures'][table],('unauthorized_table',table)
    for table in ('ydental_settlement_refund','ydental_settlement_close',
                  'ydental_settlement_mutex','ydental_settlement_receipt'):
        assert before['all']['signatures'][table]==after['all']['signatures'][table],('business_write',table)
        assert before['all']['rows'][table]==after['all']['rows'][table],('business_field',table)
    assert after['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision']==244
    assert after['all']['rows']['ydental_settlement_close'][9]['ydental_state']=='unlocked'
    assert all(a['tables'][t]==b['tables'][t] for t in s.MONEY_TABLES)
    assert all(before['all']['signatures'][t]==after['all']['signatures'][t] for t in NO_MAIL_TABLES)
    old_mutex=before['all']['rows']['ydental_settlement_mutex']
    new_mutex=after['all']['rows']['ydental_settlement_mutex']
    old_receipts=before['all']['rows']['ydental_settlement_receipt']
    new_receipts=after['all']['rows']['ydental_settlement_receipt']
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
    users = append_only(before['all']['rows']['res_users_log'], after['all']['rows']['res_users_log'], 2)
    assert len({after['all']['rows']['res_users_log'][i]['create_uid'] for i in users})==len(users)
    for ident in users:
        row = after['all']['rows']['res_users_log'][ident]
        assert row['create_uid'] in ACTORS and row['write_uid'] == row['create_uid']
        template = before['all']['rows']['res_users_log'][3 if row['create_uid']==6 else 5]
        assert changed(template,row) <= {'id','create_date','write_date'}
        assert row['create_date'] == row['write_date'] and row['create_date']
    devices = append_only(before['all']['rows']['res_device_log'], after['all']['rows']['res_device_log'], 2)
    assert len({after['all']['rows']['res_device_log'][i]['user_id'] for i in devices})==len(devices)
    for ident in devices:
        row = after['all']['rows']['res_device_log'][ident]
        assert row['user_id'] in ACTORS and row['ip_address'] == '127.0.0.1'
        assert 'Firefox/' in row['user_agent'] and row['revoked'] is False
        template = before['all']['rows']['res_device_log'][3 if row['user_id']==6 else 5]
        assert changed(template,row) <= {'id','session_identifier','user_agent','first_activity','last_activity'}
        assert row['first_activity'] and row['last_activity'] >= row['first_activity']
        assert row['session_identifier'] and len(row['session_identifier']) <= 128
    sessions = append_only(before['all']['rows']['ydental_access_session'], after['all']['rows']['ydental_access_session'], 2)
    assert len({after['all']['rows']['ydental_access_session'][i]['ydental_user_id'] for i in sessions})==len(sessions)
    for ident in sessions:
        row = after['all']['rows']['ydental_access_session'][ident]
        assert row['ydental_user_id'] in ACTORS
        assert row['ydental_store_id'] in (None, 1, 3)
        assert row['ydental_store_id'] in (None, 3 if row['ydental_user_id']==14 else 1)
        assert row['ydental_revision'] == (0 if row['ydental_store_id'] is None else 1)
        template=before['all']['rows']['ydental_access_session'][179 if row['ydental_user_id']==6 else 181]
        assert changed(template,row) <= {'id','ydental_key_hash','ydental_revision','ydental_store_id','create_date','write_date'}
        assert row['create_uid'] == row['write_uid'] == row['ydental_user_id']
        assert re.fullmatch('[0-9a-f]{64}',row['ydental_key_hash'])
        assert row['create_date'] and row['write_date'] >= row['create_date']
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
    # Both permitted actors already completed native onboarding in P004.
    messages = append_only(before['all']['rows']['mail_message'], after['all']['rows']['mail_message'], 0)
    audits = append_only(before['all']['rows']['ydental_access_audit'], after['all']['rows']['ydental_access_audit'], 10)
    bound = {}
    counts = {6: 0, 14: 0}
    for entry in gets:
        assert entry['actor'] in counts and entry['method'] == 'GET' and entry['status'] == 200
        assert entry['store'] == (3 if entry['actor'] == 14 else 1)
        assert entry['path'] == '/ydental/settlement'
        counts[entry['actor']] += 1
        assert counts[14] <= 1 and counts[6] <= 2 and sum(counts.values()) <= 3
        expected = [5,6,8,9] if entry['actor'] == 14 else []
        assert sorted(entry['invoice_ids']) == expected
        assert len(entry['audit_ids']) == len(expected) and len(set(entry['audit_ids'])) == len(expected)
        for ident, target in zip(entry['audit_ids'],entry['invoice_ids']):
            assert ident not in bound
            bound[ident] = (entry, target)
    seen_login = set()
    for ident in audits:
        row = after['all']['rows']['ydental_access_audit'][ident]
        event, uid = row['ydental_event'], row['ydental_user_id']
        assert uid in ACTORS and row['create_uid'] == row['write_uid'] == uid
        assert row['create_date'] and row['write_date'] == row['create_date']
        assert row['ydental_result'] == 'accepted'
        if event == 'settlement.invoice_view':
            assert ident in bound
            entry, target = bound[ident]
            template = before['all']['rows']['ydental_access_audit'][2671]
            assert changed(template,row) <= {'id','create_date','write_date','ydental_target_id'}
            assert uid == 14 and row['ydental_store_id'] == 3
            assert row['ydental_target_id'] == target and entry['actor'] == uid
        else:
            assert event in {'login', 'login.scope', 'store.switch'}
            assert (uid,event) not in seen_login
            seen_login.add((uid,event))
            template_id = {(6,'login'):2662,(6,'login.scope'):2663,(6,'store.switch'):2664,
                           (14,'login'):2668,(14,'login.scope'):2669,(14,'store.switch'):2670}[(uid,event)]
            template = before['all']['rows']['ydental_access_audit'][template_id]
            assert changed(template,row) <= {'id','create_date','write_date','ydental_target_id'}
            if event == 'login':
                assert row['ydental_target_id'] == uid
            else:
                sessions_after = after['all']['rows']['ydental_access_session']
                assert row['ydental_target_id'] not in before['all']['rows']['ydental_access_session']
                session = sessions_after[row['ydental_target_id']]
                assert session['ydental_user_id'] == uid
    new_read_ids = {i for i in audits if after['all']['rows']['ydental_access_audit'][i]['ydental_event']=='settlement.invoice_view'}
    assert new_read_ids == set(bound) - set(before['all']['rows']['ydental_access_audit'])
    accepted = [i for i in audits if after['all']['rows']['ydental_access_audit'][i]['ydental_event'] == 'settlement.unlock']
    assert not accepted
    signal_ids = append_only(before['all']['rows']['orm_signaling_default'],
                             after['all']['rows']['orm_signaling_default'], 3)
    assert all(set(after['all']['rows']['orm_signaling_default'][i]) == {'id', 'date'}
               for i in signal_ids)
    return {'new_asset_ids': attachments, 'new_files': sorted(newfiles), 'new_mail_ids': messages,
            'new_audit_ids': audits, 'unlock_audit_ids': accepted,
            'new_receipt_ids': sorted(set(new_receipts) - set(old_receipts)),
            'mutex_revision': new_mutex[1]['ydental_revision'],
            'new_session_ids': sessions, 'new_device_ids': devices,
            'invoice_view_audit_ids':sorted(new_read_ids), 'get_counts':counts}


def refund_sql(name,store,page):
    assert store in (1,3) and page in (1,2)
    with s.connect(name) as conn,conn.cursor() as cur:
        cur.execute('SELECT r.id,r.ydental_state,p.ydental_store_id,r.ydental_amount FROM ydental_settlement_refund r JOIN ydental_settlement_payment p ON p.id=r.ydental_payment_id WHERE p.ydental_store_id=%s ORDER BY r.id DESC',(store,))
        allrows=[{'id':i,'state':state,'store':st,'amount':str(amt),'position':idx+1,'page':idx//50+1} for idx,(i,state,st,amt) in enumerate(cur.fetchall())]
        cur.execute('SELECT name FROM ydental_access_store WHERE id=%s',(store,))
        store_name=cur.fetchone()[0]
    return {'store':store,'page':page,'store_name':store_name,'count':len(allrows),'rows':allrows[(page-1)*50:page*50]}


def workbench_facts(name):
    result={}
    with s.connect(name) as conn,conn.cursor() as cur:
        for store in (1,3):
            cur.execute("SELECT m.id FROM account_move m WHERE m.state='posted' AND m.move_type='out_invoice' AND m.amount_residual>0 AND m.company_id=(SELECT company_id FROM ydental_access_store WHERE id=%s) AND EXISTS(SELECT 1 FROM ydental_settlement_source t WHERE t.ydental_invoice_id=m.id AND t.ydental_store_id=%s) ORDER BY invoice_date,id LIMIT 50",(store,store))
            invoices=[r[0] for r in cur.fetchall()]
            assert invoices==([] if store==1 else [5,6,8,9])
            cur.execute("SELECT f.id FROM ydental_treatment_fee f JOIN ydental_treatment_event e ON e.id=f.ydental_event_id WHERE f.ydental_store_id=%s AND e.state='confirmed' AND NOT EXISTS(SELECT 1 FROM ydental_settlement_source t WHERE t.ydental_fee_id=f.id)",(store,))
            assert not cur.fetchall()
            cur.execute("SELECT id FROM ydental_treatment_event WHERE ydental_store_id=%s AND state='pending'",(store,))
            assert not cur.fetchall()
            result[str(store)]={'invoice_ids':invoices,'source_view_ids':[],'pending_event_view_ids':[]}
    return result


def checkpoint():
    authority()
    pre = json.loads(PREFLIGHT.read_text())
    mark = json.loads(CHECKPOINT.read_text())
    assert mark['comment_id'] > AUTH and mark['preflight_sha256'] == s.file_sha(PREFLIGHT)
    assert mark['body_sha256'] and len(mark['body_sha256']) == 64
    readback = json.loads((PRIVATE/'preflight-comment-readback.json').read_text())
    assert readback['id'] == mark['comment_id']
    assert readback['body'] == (PRIVATE/'preflight-comment.md').read_text()
    assert s.sha(readback['body'].encode()) == mark['body_sha256']
    assert pre['target'] == s.TARGET and pre['source']['oid'] == s.SOURCE_OID
    expected = pre['scripts_sha256']
    assert set(expected) == {str(p.relative_to(ROOT)) for p in SCRIPTS}
    assert all(s.file_sha(ROOT / p) == h for p, h in expected.items())
    assert s.file_sha(ROOT/'scripts/s08c_network_policy.py')==pre['network_policy_sha256']
    assert pre['http_argv'] == list(HTTP_ARGV) and pre['browser_argv'] == list(BROWSER_ARGV)
    return mark


def private_env():
    env = os.environ.copy()
    env.update({'PYTHONFAULTHANDLER': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                'PGAPPNAME': 's10_p0_07_bounded',
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
    assert equivalent(latest,before), 'source changed before CREATE'
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
        source_gate(before)
        historical_activity_gate()
        assert before['managed']['tables'] == json.loads(PREFLIGHT.read_text())['source_tables']

    def clone_compare(self, before):
        clone(before)
        after = capture(s.TARGET, business=True)
        clone_equal(before, after)
        save_once(PRIVATE / 'clone-snapshot.json', after)
        return after

    def start_http(self):
        self.started = time.monotonic()
        self.http = start_http()
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
        assert self.http.returncode==0
        assert json.loads((PRIVATE/'browser-result.json').read_text())['returncode']==0
        historical_activity_gate()
        verify_target()
        assert equivalent(capture(s.SOURCE, business=True),before)
        after = capture(s.TARGET, business=True)
        gate = web_diff(clone, after, gets=json.loads((PRIVATE/'get-bindings.json').read_text()))
        save_once(PRIVATE / 'final-snapshot.json', after)
        save_once(PRIVATE / 'final-gate.json', gate)
        return after


def run():
    return execute_pipeline(RealOps())


if __name__ == '__main__':
    assert sys.argv[1:] == ['run']
    run()
