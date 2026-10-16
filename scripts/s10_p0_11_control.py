"""One-use P0-11 clone/HTTP controller and strict per-transaction comparator."""
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
import time

import psycopg2
from psycopg2 import sql

import s10_p0_11_readonly as ro


os.umask(0o077)
ROOT, PRIVATE, OUT = ro.ROOT, ro.PRIVATE, ro.OUT
CORE = ROOT.parent
NAME = 'ydental_s10_test_20261016_p011_a730c9e4'
PORT = 18311
RUN = ROOT / '.local' / NAME
CONF = RUN / 'odoo.conf'
PYTHON = CORE / '.venv/bin/python'
HTTP_ARGV = [str(PYTHON), str(CORE / 'odoo-bin'), '-c', str(CONF)]
BROWSER_ARGV = [str(PYTHON), str(ROOT / 'scripts/s10_p0_11_browser.py')]
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    ro.save(path, value)


def rows(snapshot):
    return {t: [json.loads(r) for r in raw] for t, raw in snapshot['tables'].items()}


def baseline():
    return ro.read(PRIVATE / 'w5-private-rows.json')


def credentials():
    conf = configparser.ConfigParser(interpolation=None)
    conf.read(ro.FOLDER / 'odoo.conf')
    return dict(host='127.0.0.1', port=5432, user='odoo', password=conf['options']['db_password'])


def snapshot(name):
    assert name in (ro.NAME, NAME)
    conn = psycopg2.connect(dbname=name, connect_timeout=5,
        options='-c statement_timeout=15000 -c lock_timeout=3000', **credentials())
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)
    try:
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only')
            assert cur.fetchone()[0] == 'on'
            cur.execute('SHOW transaction_isolation')
            assert cur.fetchone()[0] == 'repeatable read'
            cur.execute('SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),'
                        '(SELECT system_identifier::text FROM pg_control_system())')
            db, oid, cluster = cur.fetchone()
            assert db == name and cluster == ro.CLUSTER
            if name == ro.NAME:
                assert oid == ro.OID
                cur.execute('SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')
                assert not cur.fetchall()
            elif (RUN / 'database.json').exists():
                assert oid == ro.read(RUN / 'database.json')['oid']
            cur.execute("SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' "
                        "AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            catalog = {}
            for table, column in cur.fetchall():
                catalog.setdefault(table, []).append(column)
            assert catalog == baseline()['columns']
            tables, signatures = {}, {}
            for table in sorted(catalog):
                order = sql.Identifier('id') if 'id' in catalog[table] else sql.SQL('to_jsonb(t)::text')
                cur.execute(sql.SQL('SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {}').format(sql.Identifier(table), order))
                raw = [r[0] for r in cur.fetchall()]
                tables[table] = raw
                signatures[table] = {'rows': len(raw), 'sha256': sha(('\n'.join(raw) + '\n').encode())}
            return {'database': db, 'oid': oid, 'cluster': cluster, 'columns': catalog,
                    'tables': tables, 'signatures': signatures,
                    'transaction': 'READ ONLY / REPEATABLE READ', 'backend_pid': conn.get_backend_pid()}
    finally:
        conn.rollback()
        conn.close()


def checkpoint():
    ro.repository_gate()
    pre = ro.read(OUT / 'execution-preflight.json')
    ck = ro.read(OUT / 'execution-api-readback.json')
    assert ck['verbatim_equal'] and ck['authorization'] == ro.AUTH
    assert ck['preflight_sha256'] == sha((OUT / 'execution-preflight.json').read_bytes())
    for path, expected in pre['script_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected
    for path, expected in pre['static_source_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected
    assert ro.read(OUT / 'eligibility-corrected.json')['status'] == 'ELIGIBILITY_AND_SOURCE_PASS'
    live = json.loads(subprocess.check_output(['gh', 'api', f"repos/Yredxin/YDental/issues/comments/{ck['comment_id']}"]))
    assert live['body'] == ck['body'] and sha(live['body'].encode()) == ck['body_sha256']
    return ck


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
        assert changed(template, row) <= {'id', 'ydental_key_hash', 'create_date', 'write_date'}
        assert (row['ydental_user_id'], row['ydental_store_id'], row['ydental_revision']) == (7, 1, 1)
        assert row['create_uid'] == row['write_uid'] == 7
        assert any(sha(dev['session_identifier'].encode()) == row['ydental_key_hash'] for dev in devices)
    audit = append_only(a['ydental_access_audit'], b['ydental_access_audit'], 8)
    expected_events = ([] if not identity else ['login', 'login.scope', 'store.switch']) + ['clinical.view'] * gets
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


def capture_gate(phase, context):
    snap = snapshot(NAME)
    save(PRIVATE / ('snapshot-' + phase + '.json'), snap)
    result = gate(snap, phase, context)
    save(OUT / ('gate-' + phase + '.json'), result)
    return result


def filesystem_manifest(name):
    folder = (ro.FOLDER if name == ro.NAME else RUN) / 'data/filestore' / name
    files = {str(p.relative_to(folder)): sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
    assert all(not p.is_symlink() for p in folder.rglob('*'))
    return {'count': len(files), 'w_manifest_sha256': sha(''.join(k + '\t' + files[k] + '\n' for k in sorted(files)).encode())}


def clone():
    ck = checkpoint()
    assert not RUN.exists() and not (PRIVATE / 'create-intent.json').exists()
    ro.files_gate()
    before = snapshot(ro.NAME)
    assert before['tables'] == baseline()['tables']
    save(PRIVATE / 'source-before-create.json', before)
    conn = psycopg2.connect(dbname=ro.NAME, **credentials())
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT datname FROM pg_database WHERE datname=%s', (NAME,))
            assert not cur.fetchall()
    finally:
        conn.rollback()
        conn.close()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    RUN.mkdir(mode=0o700)
    (RUN / 'network-policy').mkdir(mode=0o700)
    (RUN / 'network-policy/sitecustomize.py').write_bytes((ROOT / 'scripts/s08c_network_policy.py').read_bytes())
    shutil.copytree(ro.FOLDER / 'data/filestore' / ro.NAME, RUN / 'data/filestore' / NAME)
    assert filesystem_manifest(NAME) == filesystem_manifest(ro.NAME)
    save(PRIVATE / 'create-intent.json', {'checkpoint': ck['comment_id'], 'target': NAME, 'source': ro.NAME,
        'source_oid': ro.OID, 'attempt': 1, 'utc': datetime.now(timezone.utc).isoformat()})
    conn = psycopg2.connect(dbname='postgres', **credentials())
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            assert conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(NAME), sql.Identifier(ro.NAME)))
    finally:
        conn.close()
    after = snapshot(NAME)
    assert after['oid'] != ro.OID and after['tables'] == before['tables']
    conf = configparser.ConfigParser(interpolation=None)
    conf['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
        'db_password': credentials()['password'], 'db_name': NAME, 'dbfilter': '^' + NAME + '$',
        'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
        'data_dir': str(RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
        'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
        'admin_passwd': secrets.token_urlsafe(32), 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    text = io.StringIO()
    conf.write(text)
    with CONF.open('x') as stream:
        stream.write(text.getvalue())
    save(RUN / 'database.json', {'database': NAME, 'oid': after['oid'], 'cluster': ro.CLUSTER, 'core': ro.CORE,
        'head': ro.BASE, 'source': ro.NAME, 'source_oid': ro.OID, 'source_marker_sha256': ro.MARKER_SHA,
        'source_config_sha256': ro.CONFIG_SHA, 'config_sha256': sha(CONF.read_bytes()), 'checkpoint_id': ck['comment_id']})
    save(PRIVATE / 'clone-before-http.json', after)
    save(OUT / 'clone.json', {'database': NAME, 'oid': after['oid'], 'source_oid': ro.OID,
        'all_643_tables_exact': True, 'initial_all_table_signatures': after['signatures'],
        'filestore': filesystem_manifest(NAME), 'config_sha256': sha(CONF.read_bytes()),
        'marker_sha256': sha((RUN / 'database.json').read_bytes()), 'CREATE': 1})


def env():
    e = os.environ.copy()
    e.update(PYTHONFAULTHANDLER='1', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(RUN / 'network-policy') + os.pathsep + str(ROOT / '.local/s04-deps'),
        YDENTAL_S08C_HTTP_PORT=str(PORT), PGAPPNAME='s10_p0_11_bounded')
    return e


def run():
    clone()
    process = None
    summary = {'authorization': ro.AUTH, 'status': 'BLOCKED', 'CREATE': 1, 'Odoo_HTTP': 0, 'Firefox': 0}
    try:
        save(PRIVATE / 'http-intent.json', {'argv': HTTP_ARGV, 'attempt': 1})
        with (RUN / 'http.log').open('xb') as log:
            process = subprocess.Popen(HTTP_ARGV, cwd=ROOT, env=env(), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        summary['Odoo_HTTP'] = 1
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
        save(PRIVATE / 'browser-intent.json', {'argv': BROWSER_ARGV, 'attempt': 1})
        with (RUN / 'browser.log').open('xb') as log:
            browser = subprocess.Popen(BROWSER_ARGV, cwd=ROOT, env=env(), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT)
            summary['Firefox'] = 1
            try:
                code = browser.wait(timeout=150)
            except subprocess.TimeoutExpired:
                browser.kill()
                browser.wait()
                raise AssertionError('BROWSER_TIMEOUT_NO_RETRY')
        summary['browser_driver_returncode'] = code
        log_text = (RUN / 'browser.log').read_text()
        launches = re.findall(r'<launched> pid=(\d+)', log_text)
        exits = re.findall(r'<process did exit: exitCode=(\S+), signal=(\S+)>', log_text)
        summary['firefox_engine_pids'] = [int(pid) for pid in launches]
        summary['firefox_engine_exits'] = [{'exit_code': ec, 'signal': sig} for ec, sig in exits]
        assert code == 0, 'BROWSER_BLOCKED'
        assert len(launches) == 1 and exits == [('0', 'null')], 'FIREFOX_EXIT_NOT_PROVED'
        summary['status'] = 'SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT'
    except Exception as error:
        summary.update(error_type=type(error).__name__, error_code=str(error) if isinstance(error, AssertionError) else 'PRIVATE_ERROR_DETAIL_RETAINED')
    finally:
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
        stopped = snapshot(NAME)
        save(PRIVATE / 'stopped-target.json', stopped)
        source = snapshot(ro.NAME)
        save(PRIVATE / 'stopped-source.json', source)
        summary['source_all_643_tables_unchanged'] = source['tables'] == baseline()['tables']
        summary['source_filestore_unchanged'] = filesystem_manifest(ro.NAME)['w_manifest_sha256'] == ro.MANIFEST_SHA
        summary['target_filestore_unchanged'] = filesystem_manifest(NAME) == filesystem_manifest(ro.NAME)
        ro.files_gate()
        if summary.get('odoo_returncode') != 0 or not all(summary[k] for k in (
                'source_all_643_tables_unchanged', 'source_filestore_unchanged', 'target_filestore_unchanged')):
            summary['status'] = 'BLOCKED'
        save(OUT / 'stopped-signatures.json', {'source_all_table_signatures': source['signatures'],
            'target_all_table_signatures': stopped['signatures'], 'source_readonly_unchanged': summary['source_all_643_tables_unchanged'],
            'source_filestore_unchanged': summary['source_filestore_unchanged'], 'target_filestore_unchanged': summary['target_filestore_unchanged']})
        save(OUT / 'execution-result.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    run()
