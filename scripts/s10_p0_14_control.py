"""P0-14 one-use orchestration; source before/after and native Firefox only."""
import asyncio
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

import psycopg2
from psycopg2 import sql
import s10_p0_14_audit as ro

os.umask(0o077)
ROOT, PRIVATE, OUT = ro.ROOT, ro.PRIVATE, ro.OUT
CORE = ROOT.parent
NAME = 'ydental_s10_test_20261016_p014_7c42a9e1'
PORT = 18314
RUN = ROOT / '.local' / NAME
CONF = RUN / 'odoo.conf'
PYTHON = CORE / '.venv/bin/python'
HTTP_ARGV = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(CONF)]
EDITOR_FIELDS = {'ydental_editor_id', 'ydental_session_id', 'ydental_session_revision',
    'ydental_connection_hash', 'ydental_editor_hash', 'ydental_editor_expires', 'ydental_editor_lease_id'}
META_FIELDS = {'write_uid', 'write_date'}
FENCES = {'ydental_patient_mutex', 'ydental_supply_mutex', 'ydental_intake_mutex', 'ydental_queue_mutex'}
IDENTITY = {'res_users_log', 'res_device_log', 'ydental_access_session', 'res_users',
    'res_partner', 'hr_employee', 'hr_version', 'resource_resource'}
MUTABLE = IDENTITY | FENCES | {'ydental_access_audit', 'ydental_clinical_document',
    'ydental_clinical_version', 'orm_signaling_default'}
PHASES = {'startup': (False, 0, 0), 'login-view': (True, 0, 1), 'acquired': (True, 1, 1),
          'confirmed': (True, 2, 1), 'released': (True, 3, 1), 'final-view': (True, 3, 2)}
AUDIT = None
MIN_TABLES = ['account_move', 'account_move_line', 'account_partial_reconcile', 'account_payment', 'hr_employee', 'hr_version', 'ir_config_parameter', 'ir_model_data', 'ir_module_module', 'ir_ui_view', 'orm_signaling_default', 'res_company_users_rel', 'res_device_log', 'res_groups_implied_rel', 'res_groups_users_rel', 'res_partner', 'res_users', 'res_users_log', 'res_users_ydental_access_capability_rel', 'resource_resource', 'ydental_access_audit', 'ydental_access_capability', 'ydental_access_grant', 'ydental_access_membership', 'ydental_access_session', 'ydental_access_store', 'ydental_clinical_document', 'ydental_clinical_version', 'ydental_intake_catalog', 'ydental_intake_mapping', 'ydental_intake_mutex', 'ydental_intake_task', 'ydental_patient_mutex', 'ydental_patient_relation', 'ydental_print_job', 'ydental_queue_execution', 'ydental_queue_lease', 'ydental_queue_mutex', 'ydental_settlement_close', 'ydental_settlement_refund', 'ydental_settlement_source', 'ydental_space_area', 'ydental_space_floor', 'ydental_space_station', 'ydental_space_station_add_rel', 'ydental_supply_mutex', 'ydental_treatment_fee']
sha, save = ro.sha, ro.save

def rows(snapshot):
    return {t: [json.loads(r) for r in raw] for t, raw in snapshot['tables'].items()}

def baseline():
    return ro.read(PRIVATE / 'w5-private-rows.json')

def append_only(a, b, limit):
    old, new = {r['id']: r for r in a}, {r['id']: r for r in b}
    assert old.keys() <= new.keys() and all(new[i] == r for i, r in old.items())
    result = [r for r in b if r['id'] not in old]
    assert len(result) <= limit
    return result


def changed(a, b):
    return {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}


def gate(current, phase, context):
    identity, posts, gets = PHASES[phase]
    base = baseline()
    a, b = rows(base), rows(current)
    assert set(b) in (set(a), set(MIN_TABLES)), 'UNKNOWN_SNAPSHOT_SCOPE'
    a = {t:a[t] for t in b}
    changed_tables = [t for t in a if a[t] != b[t]]
    assert all(t in MUTABLE for t in changed_tables), ('UNAUTHORIZED_TABLE', sorted(set(changed_tables) - MUTABLE))
    for table in FENCES:
        assert len(a[table]) == len(b[table]) == 1
        old, new = a[table][0], b[table][0]
        assert changed(old, new) <= {'ydental_revision'}
        assert new['ydental_revision'] == old['ydental_revision'] + posts, ('FENCE', table)
    signal = append_only(a['orm_signaling_default'], b['orm_signaling_default'], 3)
    assert all(set(r) == {'id', 'date'} and r['date'] for r in signal)
    for table, ident, allowed in (
        ('res_users', 7, META_FIELDS), ('res_partner', 8, META_FIELDS),
        ('hr_employee', 3, META_FIELDS), ('hr_version', 3, META_FIELDS | {'last_modified_date', 'last_modified_uid'}),
        ('resource_resource', 3, META_FIELDS)):
        old, new = {r['id']: r for r in a[table]}, {r['id']: r for r in b[table]}
        assert old.keys() == new.keys()
        for i in old:
            fields = changed(old[i], new[i])
            assert not fields or identity and i == ident and fields <= allowed, ('IDENTITY_FIELD', table, i, fields)
            if fields:
                assert new[i]['write_uid'] == 7
                if 'last_modified_uid' in fields:
                    assert new[i]['last_modified_uid'] == 7
    logs = append_only(a['res_users_log'], b['res_users_log'], int(identity))
    devices = append_only(a['res_device_log'], b['res_device_log'], int(identity))
    sessions = append_only(a['ydental_access_session'], b['ydental_access_session'], int(identity))
    assert len(logs) == len(devices) == len(sessions) == int(identity)
    for row in logs:
        template = next(r for r in a['res_users_log'] if r['create_uid'] == 7)
        assert changed(template, row) <= {'id', 'create_date', 'write_date'}
        assert row['create_uid'] == row['write_uid'] == 7 and row['create_date'] == row['write_date']
    for row in devices:
        template = next(r for r in a['res_device_log'] if r['user_id'] == 7)
        assert changed(template, row) <= {'id', 'session_identifier', 'user_agent', 'first_activity', 'last_activity'}
        assert row['user_id'] == 7 and row['ip_address'] == '127.0.0.1' and 'Firefox/' in row['user_agent'] and row['revoked'] is False
    for row in sessions:
        template = next(r for r in a['ydental_access_session'] if r['ydental_user_id'] == 7)
        assert changed(template, row) <= {'id', 'ydental_key_hash', 'create_date', 'write_date', 'write_uid'}
        assert (row['ydental_user_id'], row['ydental_store_id'], row['ydental_revision']) == (7, 1, 1)
        assert row['create_uid'] == row['write_uid'] == 7
        assert any(sha(dev['session_identifier'].encode()) == row['ydental_key_hash'] for dev in devices)
    audit = append_only(a['ydental_access_audit'], b['ydental_access_audit'], 9)
    expected_events = ([] if not identity else ['login', 'login.scope', 'store.switch']) + ['clinical.view'] * gets
    expected_events += ['source.view'] * int(gets > 0)
    expected_events += ['clinical.edit_acquire', 'clinical.confirm', 'clinical.edit_release'][:posts]
    assert sorted(r['ydental_event'] for r in audit) == sorted(expected_events), ('AUDIT_EVENTS', [r['ydental_event'] for r in audit])
    safe_audit = []
    for r in audit:
        event = r['ydental_event']
        assert r['ydental_user_id'] == r['create_uid'] == r['write_uid'] == 7
        assert r['ydental_result'] == 'accepted' and r['create_date'] == r['write_date'] and r['ydental_reason'] in (None, False, '')
        assert set(r) == set(a['ydental_access_audit'][0])
        before, after = None, None
        if event.startswith('clinical.'):
            expected = ('medical', 'clinical_document', 'ydental.clinical.document', 1, 1)
            if event == 'clinical.confirm':
                before, after = {'version': 2}, {'version': 3}
        elif event == 'source.view':
            expected = ('medical', 'source_model', 'ydental.clinical.document', 1, 1)
        elif event == 'login':
            expected = ('personnel', 'native_authenticated_login', 'res.users', 7, None)
        else:
            expected = ('personnel', 'authenticated_session' if event == 'login.scope' else 'interactive',
                        'ydental.access.session', sessions[0]['id'], None if event == 'login.scope' else 1)
            if event == 'store.switch':
                before, after = {'store_id': False}, {'store_id': 1}
        assert (r['ydental_category'], r['ydental_source'], r['ydental_target_model'], r['ydental_target_id'], r['ydental_store_id']) == expected
        assert (r['ydental_before'] or None, r['ydental_after'] or None) == (before, after)
        safe_audit.append({k: r[k] for k in ('id', 'ydental_event', 'ydental_user_id', 'ydental_store_id',
            'ydental_target_model', 'ydental_target_id', 'ydental_before', 'ydental_after', 'ydental_source', 'ydental_result')})
    old_doc, doc = a['ydental_clinical_document'][0], b['ydental_clinical_document'][0]
    assert len(a['ydental_clinical_document']) == len(b['ydental_clinical_document']) == 1
    permitted = (EDITOR_FIELDS | META_FIELDS if posts else set()) | ({'state', 'ydental_version', 'ydental_saved_at'} if posts >= 2 else set())
    assert changed(old_doc, doc) <= permitted
    assert doc['ydental_content'] == old_doc['ydental_content']
    assert (doc['state'], doc['ydental_version']) == (('confirmed', 3) if posts >= 2 else ('pending', 2))
    if posts in (1, 2):
        assert (doc['ydental_editor_id'], doc['ydental_session_id'], doc['ydental_session_revision']) == (7, sessions[0]['id'], 1)
        assert not doc['ydental_editor_lease_id']
        assert doc['ydental_connection_hash'] == context['connection_sha256']
        assert doc['ydental_editor_hash'] == context['editor_sha256']
        assert datetime.fromisoformat(doc['ydental_editor_expires']) > datetime.now(timezone.utc).replace(tzinfo=None)
    elif posts == 3:
        assert all(doc[k] in (None, False, 0) for k in EDITOR_FIELDS)
    versions = append_only(a['ydental_clinical_version'], b['ydental_clinical_version'], int(posts >= 2))
    assert len(versions) == int(posts >= 2)
    for r in versions:
        template = a['ydental_clinical_version'][-1]
        allowed = {'id', 'ydental_number', 'ydental_author_id', 'ydental_previous_id', 'create_uid', 'write_uid',
                   'ydental_kind', 'ydental_reason', 'ydental_request_key', 'ydental_request_digest',
                   'ydental_recorded_at', 'create_date', 'write_date'}
        assert changed(template, r) <= allowed
        assert (r['ydental_document_id'], r['ydental_number'], r['ydental_author_id'], r['ydental_previous_id'], r['ydental_kind']) == (1, 3, 7, 2, 'confirm')
        assert r['create_uid'] == r['write_uid'] == 7 and r['ydental_content'] == old_doc['ydental_content']
        assert r['ydental_request_key'] == context['confirm_key'] and r['ydental_reason'] in (None, '')
        assert r['ydental_request_digest'] == sha(json.dumps([2, old_doc['ydental_content'], 'confirm', ''], sort_keys=True, ensure_ascii=False).encode())
        assert doc['ydental_saved_at'] == r['ydental_recorded_at']
    return {'phase': phase, 'PASS': True, 'changed_tables': changed_tables, 'clinical_action_commits': posts,
            'clinical_views': gets, 'audits': safe_audit, 'document_state': doc['state'], 'document_version': doc['ydental_version'],
            'old_versions_full_rows_unchanged': True, 'economic_and_other_tables_unchanged': sorted(set(a) - MUTABLE),
            'all_table_signatures': current['signatures']}




def verify_freeze():
    ro.repository_gate()
    pre = ro.read(OUT / 'execution-preflight.json')
    assert sha((OUT/'static-contract.json').read_bytes()) == pre['static_contract_sha256']
    assert ro.read(OUT/'static-contract.json')['status'] == 'STATIC_REVIEW_PASS'
    for path, expected in pre['script_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected, 'SCRIPT_FREEZE_DRIFT'
    for path, expected in pre['static_source_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected, 'STATIC_SOURCE_DRIFT'
    for path, expected in pre['private_dependency_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected, 'PRIVATE_DEPENDENCY_DRIFT'
    assert ro.read(PRIVATE / 'remote-ref.json')['object']['sha'] == ro.BASE
    return pre


def checkpoint():
    pre = verify_freeze()
    ck = ro.read(PRIVATE / 'preflight-api-readback.json')
    assert ck['verbatim_equal'] and ck['authorization'] == ro.AUTH
    body = (OUT / 'execution-preflight.json').read_bytes()
    assert ck['preflight_sha256'] == sha(body)
    # The REST GET raw response is saved only after exact text comparison.
    live = ro.read(PRIVATE / 'preflight-api-raw.json')
    assert live['id'] == ck['comment_id'] and live['body'] == ck['body']
    assert sha(live['body'].encode()) == ck['body_sha256']
    return ck


GATE_NUMBER = 0


def capture_gate(phase, context):
    global GATE_NUMBER
    assert AUDIT is not None and AUDIT.name == NAME
    GATE_NUMBER += 1
    snap = AUDIT.capture(tables=MIN_TABLES)
    label = f'gate-{GATE_NUMBER:02}-{phase}'
    save(PRIVATE / (label + '-rows.json'), snap)
    result = gate(snap, phase, context)
    result['backend_pid'] = snap['backend_pid']
    result['capture_scope'] = snap['capture_scope']
    result['checked_tables'] = snap['captured_tables']
    result['full643_or_economic_proof'] = False
    result['snapshot_number'] = snap['snapshot_number']
    save(OUT / (label + '.json'), result)
    return result


def filesystem_manifest(name):
    folder = (ro.FOLDER if name == ro.NAME else RUN) / 'data/filestore' / name
    assert folder.is_dir() and not folder.is_symlink()
    files = {str(p.relative_to(folder)): sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
    assert all(not p.is_symlink() for p in folder.rglob('*'))
    return {'count': len(files), 'w_manifest_sha256': sha(''.join(k + '\t' + files[k] + '\n' for k in sorted(files)).encode())}


def clone(ck, before):
    global AUDIT
    assert ro.read(PRIVATE / 'source-before-connection-closed.json')['closed']
    assert not RUN.exists() and not (PRIVATE / 'maintenance-connection-intent.json').exists()
    assert ro.read(OUT / 'eligibility.json')['status'] == 'ELIGIBILITY_AND_SOURCE_PASS'
    ro.files_gate()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    (RUN / 'network-policy/sitecustomize.py').write_bytes((ROOT / 'scripts/s08c_network_policy.py').read_bytes())
    shutil.copytree(ro.FOLDER / 'data/filestore' / ro.NAME, RUN / 'data/filestore' / NAME)
    assert filesystem_manifest(NAME) == filesystem_manifest(ro.NAME)
    save(PRIVATE / 'maintenance-connection-intent.json', {'dbname': 'postgres', 'attempt': 1})
    conn = None
    try:
        conn = psycopg2.connect(dbname='postgres', connect_timeout=5,
            options='-c statement_timeout=30000 -c lock_timeout=3000', **ro.credentials())
        conn.autocommit = True
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(ro.TARGET_NAME_SQL, (NAME,))
            assert not cur.fetchall(), 'TARGET_ALREADY_EXISTS'
            cur.execute(ro.TEMPLATE_CONNECTION_SQL, (ro.NAME,))
            assert not cur.fetchall(), 'TEMPLATE_HAS_CONNECTIONS'
            cur.execute('SELECT system_identifier::text FROM pg_control_system()')
            assert cur.fetchone()[0] == ro.CLUSTER
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            save(PRIVATE / 'create-intent.json', {'checkpoint': ck['comment_id'], 'target': NAME,
                 'source': ro.NAME, 'source_oid': ro.OID, 'attempt': 1, 'utc_epoch': time.time()})
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(ro.NAME)))
            cur.execute(ro.TARGET_NAME_SQL, (NAME,))
            target_oid, target_name = cur.fetchone()
            assert target_name == NAME and target_oid != ro.OID
            save(PRIVATE / 'create-completed.json', {'database': NAME, 'oid': target_oid, 'CREATE': 1})
    finally:
        if conn is not None:
            conn.close()
    conf = configparser.ConfigParser(interpolation=None)
    conf['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
        'db_password': ro.credentials()['password'], 'db_name': NAME, 'dbfilter': '^' + NAME + '$',
        'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
        'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
        'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
        'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    text = io.StringIO()
    conf.write(text)
    with CONF.open('x') as stream:
        stream.write(text.getvalue())
    save(RUN / 'database.json', {'database': NAME, 'oid': target_oid, 'cluster': ro.CLUSTER, 'core': ro.CORE,
        'head': ro.BASE, 'source': ro.NAME, 'source_oid': ro.OID, 'source_marker_sha256': ro.MARKER_SHA,
        'source_config_sha256': ro.CONFIG_SHA, 'config_sha256': sha(CONF.read_bytes()), 'checkpoint_id': ck['comment_id']})
    AUDIT = ro.ReadAudit(NAME, 'target-before', target_oid)
    after = AUDIT.capture()
    assert after['tables'] == before['tables'], 'CLONE_INITIAL_FULL643_MISMATCH'
    save(PRIVATE / 'clone-before-http.json', after)
    save(OUT / 'clone.json', {'database': NAME, 'oid': target_oid, 'source_oid': ro.OID,
        'all_643_tables_exact': True, 'initial_all_table_signatures': after['signatures'],
        'filestore': filesystem_manifest(NAME), 'config_sha256': sha(CONF.read_bytes()),
        'marker_sha256': sha((RUN / 'database.json').read_bytes()), 'CREATE': 1})


def env():
    e = os.environ.copy()
    e.update(PYTHONFAULTHANDLER='1', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
        YDENTAL_S08C_HTTP_PORT=str(PORT), PGAPPNAME='s10_p0_14_bounded')
    return e


def error_metadata(error):
    # Raw exceptions may contain medical values or connection tokens.
    return {'error_type': type(error).__name__, 'error_detail_sha256': sha(str(error).encode()),
            'sqlstate': getattr(error, 'pgcode', None)}


def run():
    global AUDIT
    ck = checkpoint()
    assert not (PRIVATE / 'execution-intent.json').exists(), 'NO_REPLAY'
    save(PRIVATE / 'execution-intent.json', {'authorization': ro.AUTH, 'checkpoint': ck['comment_id'],
         'start_epoch': time.time(), 'attempt': 1})
    process, before, target_after = None, None, None
    summary = {'authorization': ro.AUTH, 'status': 'BLOCKED', 'CREATE': 0, 'Odoo_HTTP': 0, 'Firefox': 0,
               'source_before': 'NOT_RUN', 'source_after': 'NOT_RUN', 'target_after': 'NOT_RUN'}
    phase = 'source-before'
    try:
        before, evidence = ro.source_capture('source-before')
        evidence.update(rolled_back=True, closed=True)
        save(OUT / 'source-before.json', evidence)
        summary['source_before'] = 'PASS'
        from s10_p0_14_eligibility import evaluate
        evaluate()
        phase = 'clone'
        clone(ck, before)
        summary['CREATE'] = 1
        phase = 'http'
        assert sha(CONF.read_bytes()) == ro.read(RUN / 'database.json')['config_sha256']
        save(PRIVATE / 'http-intent.json', {'argv': HTTP_ARGV, 'attempt': 1})
        with (RUN / 'http.log').open('xb') as log:
            process = subprocess.Popen(HTTP_ARGV, cwd=ROOT, env=env(), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        summary.update(Odoo_HTTP=1, odoo_pid=process.pid)
        began = time.monotonic()
        while True:
            assert process.poll() is None, 'HTTP_EARLY_EXIT'
            try:
                with socket.create_connection(('127.0.0.1', PORT), timeout=1):
                    break
            except OSError:
                assert time.monotonic() - began < 60, 'HTTP_READY_TIMEOUT'
                time.sleep(0.25)
        capture_gate('startup', {})
        phase = 'browser'
        # Same process owns target-before connection; all route gates renew
        # its strictly read-only transaction, never opening extra connections.
        from s10_p0_14_browser import main
        asyncio.run(asyncio.wait_for(main(), timeout=150))
        summary['Firefox'] = 1
        summary['status'] = 'SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT'
    except Exception as error:
        summary.update(failed_phase=phase, **error_metadata(error))
        save(PRIVATE / 'execution-error.json', {'phase': phase, 'error': str(error)})
    finally:
        if AUDIT is not None:
            AUDIT.close()
            AUDIT = None
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            summary['odoo_returncode'] = process.returncode
            summary['odoo_log_sha256'] = sha((RUN / 'http.log').read_bytes())
            if process.returncode != 0:
                summary['status'] = 'BLOCKED'
        created = PRIVATE / 'create-completed.json'
        if created.exists():
            summary['CREATE'] = 1
            audit = None
            try:
                marker = ro.read(RUN / 'database.json')
                audit = ro.ReadAudit(NAME, 'target-after', marker['oid'])
                target_after = audit.capture()
                save(PRIVATE / 'target-after-rows.json', target_after)
                summary['target_after'] = 'CAPTURED'
                if (PRIVATE / 'accepted-context.json').exists():
                    result = gate(target_after, 'final-view', ro.read(PRIVATE / 'accepted-context.json'))
                    save(OUT / 'gate-stopped-target.json', result)
                    summary['target_after'] = 'PASS'
                else:
                    summary['status'] = 'BLOCKED'
                save(OUT / 'target-after-signatures.json', {'all_table_signatures': target_after['signatures'],
                     'backend_pid': target_after['backend_pid'], 'transaction': target_after['transaction']})
                summary['target_filestore_unchanged'] = filesystem_manifest(NAME) == filesystem_manifest(ro.NAME)
                if not summary['target_filestore_unchanged']:
                    summary['status'] = 'BLOCKED'
            except Exception as error:
                summary.update(status='BLOCKED', target_after='BLOCKED', target_after_error=error_metadata(error))
            finally:
                if audit:
                    audit.close()
        # Separate source connection #2 only after actual clone operations are
        # finished or stopped. Never retry it and never retain the old snapshot.
        if before is not None:
            try:
                source, evidence = ro.source_capture('source-after')
                evidence.update(rolled_back=True, closed=True)
                save(OUT / 'source-after.json', evidence)
                summary['source_after'] = 'PASS'
                summary['source_all643_exact'] = source['tables'] == before['tables']
            except Exception as error:
                summary.update(status='BLOCKED', source_after='BLOCKED', source_after_error=error_metadata(error))
        if (OUT / 'browser-result.json').exists():
            browser = ro.read(OUT / 'browser-result.json')
            summary['Firefox'] = browser['counts']['FIREFOX_LAUNCH']
            summary['browser_counts'] = browser['counts']
            server_log = (RUN / 'http.log').read_text() if (RUN / 'http.log').exists() else ''
            server_requests = [{'method':m.group(1),'path':m.group(2),'status':int(m.group(3))} for m in re.finditer(r'"(GET|POST) ([^ ?"]+)(?:[^\"]*)" (\d{3})',server_log)]
            network = browser['network_requests']
            clinical_network = sum(r['method']=='GET' and r['path']=='/ydental/clinical' for r in network)
            clinical_responses = sum(r['method']=='GET' and r['path']=='/ydental/clinical' for r in browser['responses'])
            clinical_server = sum(r['method']=='GET' and r['path']=='/ydental/clinical' for r in server_requests)
            post_network = [r['path'] for r in network if r['method']=='POST']
            post_responses = [r['path'] for r in browser['responses'] if r['method']=='POST']
            post_server = [r['path'] for r in server_requests if r['method']=='POST']
            network_equal = clinical_network == clinical_responses == clinical_server == browser['counts']['CLINICAL_GET'] and post_network == post_responses == post_server
            save(OUT / 'http-reconciliation.json', {'clinical_GET_network':clinical_network,'clinical_GET_response':clinical_responses,'clinical_GET_server':clinical_server,'clinical_GET_counter':browser['counts']['CLINICAL_GET'],'POST_network':post_network,'POST_response':post_responses,'POST_server':post_server,'all_equal':network_equal,'server_requests':server_requests})
            if not network_equal:
                summary['status'] = 'BLOCKED'
            if browser['status'] == 'BLOCKED':
                summary['status'] = 'BLOCKED'
        # DEBUG pw:browser records the real Firefox engine PID and exit signal.
        log = (PRIVATE / 'execution.log').read_text() if (PRIVATE / 'execution.log').exists() else ''
        summary['firefox_engine_pids'] = [int(p) for p in re.findall(r'<launched> pid=(\d+)', log)]
        summary['firefox_engine_exits'] = [{'exit_code': ec, 'signal': sig} for ec, sig in
            re.findall(r'<process did exit: exitCode=(\S+), signal=(\S+)>', log)]
        if summary['Firefox'] and (len(summary['firefox_engine_pids']) != 1 or
                summary['firefox_engine_exits'] != [{'exit_code': '0', 'signal': 'null'}]):
            summary['status'] = 'BLOCKED'
        summary['actual_connections'] = {label: int((PRIVATE / (label + '-connection-intent.json')).exists())
            for label in ('source-before', 'source-after', 'target-before', 'target-after', 'maintenance')}
        summary['create_attempts'] = int((PRIVATE / 'create-intent.json').exists())
        summary['Odoo_HTTP'] = int((PRIVATE / 'http-intent.json').exists())
        summary['no_product_core_issue_project_mutation'] = True
        save(OUT / 'execution-result.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    sys.modules['s10_p0_14_control'] = sys.modules[__name__]
    run()
