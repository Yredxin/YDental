"""Freeze P0-13 using local files only; zero DB, HTTP, Firefox or business POST."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import s10_p0_13_control as c
import s10_p0_13_browser as browser


def projection(value):
    body = value['body']
    return {'id': value.get('id'), 'url': value.get('html_url', value.get('url')),
        'created_at': value.get('created_at'), 'updated_at': value.get('updated_at'),
        'characters': len(body), 'utf8_bytes': len(body.encode()), 'body_sha256': c.sha(body.encode()),
        'title': body.splitlines()[0]}


def main():
    os.umask(0o077)
    c.OUT.mkdir(parents=True, exist_ok=True)
    c.ro.repository_gate()
    assert not c.RUN.exists()
    assert not (c.PRIVATE / 'execution-intent.json').exists()
    issues = {str(n): c.ro.read(c.PRIVATE / f'issue{n}.json') for n in (23, 34, 35)}
    comments = {str(n): c.ro.read(c.PRIVATE / f'comments{n}-connector.json') for n in (23, 34)}
    assert len(comments['23']) == issues['23']['comments'] == 3
    assert len(comments['34']) == issues['34']['comments'] == 220
    assert comments['34'][-1]['id'] == c.ro.AUTH
    assert len({x['id'] for x in comments['34']}) == 220
    assert issues['34']['state'] == issues['35']['state'] == 'open' and issues['35']['comments'] == 0
    auth = next(x for x in comments['34'] if x['id'] == c.ro.AUTH)
    assert auth['body'] == c.ro.read(c.PRIVATE / 'authorize.json')['body']
    assert [x['id'] for x in comments['34'] if 'S10-P0-13' in x['body'].splitlines()[0]] == [c.ro.AUTH]
    c.save(c.OUT / 'github-start.json', {'captured_at': datetime.now(timezone.utc).isoformat(),
        'issues': {n: projection(v) | {'state': v['state'], 'comments': v['comments']} for n, v in issues.items()},
        'comments': {n: [projection(x) for x in xs] for n, xs in comments.items()},
        'authorization': c.ro.AUTH, 'authorization_body_sha256': c.sha(auth['body'].encode()),
        'all_available_comments_acquired': True, 'effective_current_authorization': c.ro.AUTH,
        'p012_ruling': 6211057301, 'p012_script_executed_or_ruling_reopened': False,
        'raw_comments_private_only': True})
    seal, _ = c.ro.files_gate()
    scripts = {str(p.relative_to(c.ROOT)): c.sha(p.read_bytes()) for p in sorted(c.ROOT.glob('scripts/s10_p0_13_*.py'))}
    for p in scripts:
        ast.parse((c.ROOT / p).read_text())
    oldplan = c.ro.read(c.ROOT / 'docs/evidence/s10-p0-11/execution-preflight.json')
    sources = {p: c.sha((c.ROOT / p).read_bytes()) for p in oldplan['static_source_sha256']}
    # Additional native authentication, frontend, and default-store dependencies.
    for p in ['ydental_access/controllers/access.py', 'ydental_clinical/models/ydental_access_service.py',
              'ydental_clinical/models/ydental_queue_service.py', 'ydental_clinical/models/ydental_clinical_document.py',
              'ydental_clinical/models/ydental_clinical_version.py', 'ydental_access/models/ydental_access_audit.py',
              '../odoo/addons/base/models/res_users.py', '../odoo/addons/base/models/res_device.py',
              '../addons/web/controllers/home.py', '../addons/web/views/webclient_templates.xml',
              'scripts/s10_e2e_w5_browser.py', 'docs/evidence/s10-p0-10/read-only-sql.json',
              'docs/evidence/s10-p0-11/read-only-sql.json', 'docs/evidence/s10-p0-11/execution-preflight.json',
              'docs/evidence/s10-p0-11/eligibility-corrected.json', 'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json']:
        sources[p] = c.sha((c.ROOT / p).read_bytes())
    js = (c.ROOT / 'ydental_clinical/static/src/document/document.js').read_text()
    assert 'if (saving || needsReconcile) { return; }' in js
    assert "await action('release', {document_id: documentId, editor_token: token})" in js
    assert "window.location.assign('/ydental/clinical?document_id=' + documentId)" in js
    assert 'saving = true;' in js and "operation !== 'save'" in js
    historical = c.ro.read(c.ROOT / '.local/s10-p0-11-6209310360/w5-private-rows.json')
    public = c.ro.read(c.ROOT / 'docs/evidence/s10-p0-11/read-only-sql.json')
    assert c.sha((c.ROOT / '.local/s10-p0-11-6209310360/w5-private-rows.json').read_bytes()) == public['private_snapshot_sha256']
    history = dict(historical, signatures=public['all_table_signatures'])
    original_baseline = c.baseline
    c.baseline = lambda: historical
    checks = []
    try:
        c.gate(history, 'startup', {})
        checks.append('historical_unchanged643_accepted_as_OFFLINE_FIXTURE_ONLY')
        for table, field, value in [('account_move', 'amount_total', 741), ('ydental_queue_mutex', 'ydental_revision', -1),
            ('ydental_clinical_version', 'ydental_kind', 'confirm'), ('ydental_access_audit', 'ydental_event', 'clinical.view')]:
            snap = deepcopy(history)
            row = json.loads(snap['tables'][table][0]);row[field] = value
            snap['tables'][table][0] = json.dumps(row)
            try:
                c.gate(snap, 'startup', {})
            except AssertionError:
                checks.append('offline_reject_' + table)
            else:
                raise AssertionError('unsafe_comparator_' + table)
    finally:
        c.baseline = original_baseline
    doc = c.rows(historical)['ydental_clinical_document'][0]
    context = {'connection_sha256': c.sha(b'A' * 64), 'editor_sha256': c.sha(b'B' * 43),
               'csrf_sha256': c.sha(b'offline-csrf'), 'old_keys': ['old-offline-key']}
    for op in ('acquire', 'confirm', 'release'):
        payload = {'document_id': 1}
        if op != 'acquire': payload['editor_token'] = 'B' * 43
        if op == 'confirm': payload.update(expected_version=2, content=doc['ydental_content'], key='new-offline-key-123456')
        form = {'operation': [op], 'payload': [json.dumps(payload)], 'revision': ['1'],
                'connection': ['A' * 64], 'csrf_token': ['offline-csrf']}
        assert browser.validate_action(form, context, doc)[0] == op
        checks.append('offline_accept_request_shape_' + op)
        for key, value in [('revision', ['2']), ('operation', ['heartbeat']), ('csrf_token', ['bad'])]:
            try:
                browser.validate_action(form | {key: value}, context, doc)
            except AssertionError:
                checks.append('offline_reject_' + op + '_' + key)
            else: raise AssertionError('unsafe_request_gate')
    catalog = public['columns']
    literals = sorted({n.value for p in scripts for n in ast.walk(ast.parse((c.ROOT / p).read_text()))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value.lstrip().upper().startswith(('SELECT ', 'SHOW ', 'CREATE DATABASE '))})
    selects = ['SELECT to_jsonb(t)::text FROM public."' + table + '" t ORDER BY ' +
        ('"id"' if 'id' in cols else 'to_jsonb(t)::text') for table, cols in sorted(catalog.items())]
    assert len(selects) == 643
    whitelist = deepcopy(oldplan['whitelist'])
    whitelist['new_row_fields'] = {
        'res_users_log': {'template': 'existing user7 row', 'different_fields': ['id', 'create_date', 'write_date'], 'create_uid': 7, 'write_uid': 7, 'dates_equal': True},
        'res_device_log': {'template': 'existing user7 row', 'different_fields': ['id','session_identifier','user_agent','first_activity','last_activity'], 'user_id':7, 'ip_address':'127.0.0.1','revoked':False,'user_agent_contains':'Firefox/'},
        'ydental_access_session': {'template': 'existing user7 row', 'different_fields':['id','ydental_key_hash','create_date','write_date'], 'user':7, 'store':1, 'revision':1,'key_hash':'SHA256 native SID prefix equals new device session identifier'},
        'ydental_clinical_version': {'template': 'version2', 'different_fields':['id','ydental_number','ydental_author_id','ydental_previous_id','create_uid','write_uid','ydental_kind','ydental_reason','ydental_request_key','ydental_request_digest','ydental_recorded_at','create_date','write_date'], 'document':1,'patient':1,'store':1,'number':3,'author':7,'previous':2,'kind':'confirm','content':'exact current source JSON','reason':'empty','key':'one native new UUID','digest':'SHA256 JSON [2, full original content, confirm, empty reason]','template_unchanged':True},
        'ydental_access_audit': {'schema':'exact existing audit fields; no extra fields','events':whitelist['audit']['allowed_events'],'actor_create_write':7,'result':'accepted','reason':'empty','dates_equal':True,'targets':'clinical -> doc1/store1/medical/clinical_document; login -> user7/no store/personnel/native_authenticated_login; login.scope -> new session/no store/personnel/authenticated_session; store.switch -> new session/store1/personnel/interactive','before_after':'confirm version2->3; switch false->store1; all others null'},
    }
    eligibility = c.ro.read(c.ROOT / 'docs/evidence/s10-p0-11/eligibility-corrected.json')
    locked = sorted(set(catalog) - c.MUTABLE)
    plan = {'authorization': c.ro.AUTH,'base':c.ro.BASE,'core':c.ro.CORE,'branch':c.ro.BRANCH,
        'source':c.ro.NAME,'source_oid':c.ro.OID,'source_seal':seal,'target':c.NAME,'http_port':c.PORT,
        'target_oid':'new, distinct from source; captured only once after CREATE', 'script_sha256':scripts,
        'static_source_sha256':sources,
        'private_dependency_sha256':{'.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json':c.sha((c.ROOT/'.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json').read_bytes())},'sql_literals':literals,'full643_literal_SELECT':selects,
        'create_literal':'CREATE DATABASE "'+c.NAME+'" WITH TEMPLATE "'+c.ro.NAME+'"',
        'sql_order':['source-before #1: BEGIN REPEATABLE READ READ ONLY; SHOW read_only before first SELECT; identity, connections, catalog,643 tables; ROLLBACK/CLOSE',
                     'offline current eligibility25 and seals; STOP on failure',
                     'one independent postgres maintenance connection: autocommit IDLE; target absent, no template sessions, cluster; CREATE once; target OID; CLOSE',
                     'target-before #1: initial643 exact; remain connected across native Web requests; each gate new READ ONLY/REPEATABLE READ transaction followed by ROLLBACK; no snapshot reused',
                     'native Odoo HTTP once / Firefox once; login, clinical GET, acquire, confirm, automatic release, final clinical GET',
                     'close target-before; stop exact own HTTP PID; target-after #2 fresh transaction643 and compare; ROLLBACK/CLOSE',
                     'source-after #2 fresh READ ONLY/REPEATABLE READ transaction643/seals/pointers versus actual source-before; ROLLBACK/CLOSE even on error; no third connection'],
        'target_audit_connection_policy':'before1 retained for per-request snapshots, after1 independent; no audit connection opens per action',
        'maximum_budget':{'SOURCE_BEFORE_CONNECTION':1,'SOURCE_AFTER_CONNECTION':1,'W5_CONNECTION_TOTAL':2,'TARGET_BEFORE_CONNECTION':1,'TARGET_AFTER_CONNECTION':1,'MAINTENANCE_CONNECTION':1,'CREATE':1,'ODOO_HTTP_LAUNCH':1,'FIREFOX_LAUNCH':1,'NATIVE_LOGIN_POST':1,'STORE_SWITCH_POST':0,'CLINICAL_GET':2,'ACQUIRE':1,'CONFIRM':1,'RELEASE':1,'HEARTBEAT':0,'OTHER_BUSINESS_POST':0,'PDF':0,'FUNDS_STOCK_WRITE':0,'HISTORICAL_REPLAY':0,'ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST':0,'DIRECT_BUSINESS_ORM':0,'SUDO':0},
        'actual_start_budget':'ALL_ZERO; file-only offline validation', 'http_argv':c.HTTP_ARGV,
        'executor_argv':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_13_control.py')],
        'firefox':'existing Playwright pw.firefox.launch headless True; one context; zh-CN / UTC /1440x1100; real engine launch/exit DEBUG log',
        'whitelist':whitelist,'locked_tables':locked, 'all_tables':sorted(catalog),
        'eligibility25':list(eligibility['checks']), 'current_eligibility':'NOT_RUN until checkpoint REST readback',
        'credentials':'existing synthetic doctor7 password from historical script AST and fixture login; current PBKDF2 verified offline after source snapshot; no update',
        'original_content':'current first source private snapshot doc1 full TEXT_FIELDS+teeth; DOM and real native confirm payload exactly equal; no form editing events',
        'native_routes':{'GET':['/web/login?redirect=/ydental/clinical%3Fdocument_id%3D1','/ydental/clinical?document_id=1'],'POST':['/web/login','/ydental/clinical/action acquire','/ydental/clinical/action confirm','/ydental/clinical/action release']},
        'native_auth':'user7 own login; CSRF/Origin/cookie, scope store1/revision1, native connection 32-128 alnum; controller binds SID and rechecks write permission/responsibility/qualifications, CAS2',
        'native_sudo_scope':'executor sudo0 / direct ORM0; existing unchanged server implementation internally uses fixed-model sudo behind real actor checks, no executor elevation',
        'GET_assets':'only existing source ir_attachment asset URLs, two native clinical static files, login, website translations zh_CN; unexpected request STOP',
        'heartbeat':'native timer unchanged; no holder/stored editor, acquire then immediate Confirm; saving=true while confirm/release gates wait; token null after automatic release; any observed heartbeat STOP before forwarding',
        'stop':'any identity/catalog/seal/eligibility drift, wrong response/403/409/timeout/disconnection/pageerror/extra POST/heartbeat/unknown or side-effect mismatch; no retry/key replacement/second clone',
        'privacy':'raw rows/credentials/CSRF/cookie/token/key/medical text/HTTP/screenshots in private700; public allowlist IDs/status/hash only',
        'historical_replay_prohibited':['refund14','close9','refund13 pagination/store3','W5 payments500/240','any prior clinical action'],
        'source_two_independent_connections_required':True,'historical_fixture_is_not_current_sql':True,
        'os_pg_docker_ipv6_security_special_work':False}
    c.save(c.OUT / 'offline-checks.json', {'status':'PASS','checks':checks,'count':len(checks), 'SQL_CREATE_HTTP_FIREFOX_POST':0, 'historical_fixture_only':True})
    c.save(c.OUT / 'execution-preflight.json', plan)
    print(json.dumps({'status':'OFFLINE_FREEZE_READY','checks':len(checks),'scripts':scripts,
                     'preflight_sha256':c.sha((c.OUT/'execution-preflight.json').read_bytes())}))


if __name__ == '__main__':
    main()
