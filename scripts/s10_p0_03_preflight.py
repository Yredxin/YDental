"""Read-only P0-03 provenance and fixed execution contract, before any CREATE."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import s10_p0_02_snapshot as r3
import s10_p0_03_control as c
import s10_p0_03_snapshot as s

os.umask(0o077)


def rows(table, database, condition='TRUE'):
    from psycopg2 import sql
    with s.connect(database) as conn, conn.cursor() as cur:
        query = sql.SQL('SELECT to_jsonb(t)::text FROM {} t WHERE ' + condition + ' ORDER BY id').format(sql.Identifier(table))
        cur.execute(query)
        return {x['id']: x for x in (json.loads(row[0]) for row in cur.fetchall())}


def differences(table):
    old, new = rows(table, r3.SOURCE), rows(table, s.SOURCE)
    assert set(old) <= set(new)
    return old, new, {i: new[i] for i in new if old.get(i) != new[i]}


def field_changes(table, expected_ids, expected_fields):
    old, new, diff = differences(table)
    assert set(diff) == set(expected_ids), (table, set(diff))
    report = {}
    for ident, value in diff.items():
        changed = c.changed(old.get(ident, {}), value)
        assert changed == set(expected_fields), (table, ident, changed)
        report[str(ident)] = {name: [old[ident].get(name), value.get(name)] for name in sorted(changed)}
    return report


def main():
    c.authority()
    assert not s.TARGET_RUN.exists(), 'P0-03 target directory already exists'
    dbs, active = s.identity()
    assert s.TARGET not in dbs and not active
    original = r3.snapshot(r3.SOURCE, business=True)
    source = c.capture(s.SOURCE, business=True)
    fixed = json.loads((c.ROOT / 'docs/evidence/s10-p0-02/blocked.json').read_text())
    assert source['managed']['tables'] == fixed['target']['current_snapshot']['tables']
    assert source['managed']['schema'] == fixed['target']['current_snapshot']['schema']
    assert source['managed']['filestore']['sha256'] == s.SOURCE_MANIFEST
    assert len(source['all']['signatures']) == 643
    # All source file pointers and checksums were verified by snapshot().
    assert len(source['managed']['filestore']['files']) == 194
    assert source['managed']['attachment_pointers'] == 1075
    assert source['managed']['business']['refund14'][:3] == ['requested', '5', '1']
    assert source['managed']['business']['close9'][0] == 'confirmed'
    assert set(source['managed']['business']['grants']) >= {(6, 1, 'settlement', 'write'),
        (6, 1, 'finance_approval', 'write'), (14, 3, 'settlement', 'write')}
    assert not any(g[0] == 10 and g[1] == 1 for g in source['managed']['business']['grants'])
    assert not any(g[0] == 14 and g[1] == 1 for g in source['managed']['business']['grants'])
    old_att, new_att, asset_rows = differences('ir_attachment')
    assert set(asset_rows) == {1072, 1073, 1074, 1075, 1076}
    assets = []
    pointed = set()
    for ident, row in sorted(asset_rows.items()):
        assert row['res_model'] == 'ir.ui.view' and row['res_id'] == 0
        assert row['type'] == 'binary' and row['public'] is True
        assert row['create_uid'] == row['write_uid'] == 1
        assert c.ASSET_PATTERN.fullmatch(row['url'])
        assert row['name'] == row['url'].rsplit('/', 1)[-1]
        fname = row['store_fname']; pointed.add(fname)
        raw = (s.SOURCE_RUN / 'data/filestore' / s.SOURCE / fname).read_bytes()
        assert len(raw) == row['file_size'] and hashlib.sha1(raw).hexdigest() == row['checksum']
        assert raw.startswith(b'wOF2' if row['mimetype'] == 'font/woff2' else b'\n/* ')
        assets.append({key: row[key] for key in ('id', 'res_model', 'res_id', 'name', 'url',
            'mimetype', 'type', 'checksum', 'store_fname', 'file_size', 'create_uid',
            'create_date', 'write_uid', 'write_date', 'public')})
    added = set(source['managed']['filestore']['files']) - set(original['filestore']['files'])
    assert added == pointed | {'checklist/' + x for x in pointed}
    files = []
    for name in sorted(added):
        raw = (s.SOURCE_RUN / 'data/filestore' / s.SOURCE / name).read_bytes()
        assert s.sha(raw) == source['managed']['filestore']['files'][name]
        if name.startswith('checklist/'):
            assert not raw and name[10:] in pointed
        files.append({'path': name, 'size': len(raw), 'sha256': s.sha(raw),
                      'header_hex': raw[:16].hex(), 'attachment_id': next(
                          (row['id'] for row in assets if row['store_fname'] == name), None),
                      'phase': 'ir.attachment._mark_for_gc zero-byte checklist' if name.startswith('checklist/') else
                               'assetsbundle.save_attachment persisted asset'})
    mail_old, mail_new, mail = differences('mail_message')
    assert set(mail) == {1832, 1833}
    for row in mail.values():
        assert row['model'] in ('res.users', 'hr.employee')
        assert row['res_id'] == (6 if row['model'] == 'res.users' else 2)
        assert row['message_type'] == 'tracking' and row['subtype_id'] == 2
        assert row['is_internal'] is True and row['author_id'] == 7
        assert row['create_uid'] == row['write_uid'] == 6
    with s.connect(s.SOURCE) as conn, conn.cursor() as cur:
        cur.execute('SELECT count(*) FROM mail_message_res_partner_rel WHERE mail_message_id IN (1832,1833)')
        assert cur.fetchone()[0] == 0
        cur.execute('SELECT e.id,e.user_id,e.current_version_id,e.resource_id,u.partner_id,p.tz '
                    'FROM hr_employee e JOIN res_users u ON u.id=e.user_id '
                    'JOIN res_partner p ON p.id=u.partner_id WHERE e.user_id IN (6,10,14) ORDER BY e.user_id')
        users = cur.fetchall()
    conn.close()
    assert users == [(2, 6, 2, 2, 7, 'UTC'), (6, 10, 6, 6, 11, None),
                     (10, 14, 10, 10, 16, None)]
    users_diff = field_changes('res_users', [6], ['write_uid', 'write_date'])
    partner_diff = field_changes('res_partner', [7], ['tz', 'write_uid', 'write_date'])
    employee_diff = field_changes('hr_employee', [2], ['write_uid', 'write_date'])
    version_diff = field_changes('hr_version', [2], ['last_modified_date', 'last_modified_uid', 'write_uid', 'write_date'])
    resource_diff = field_changes('resource_resource', [2], ['write_uid', 'write_date'])
    assert partner_diff['7']['tz'] == [None, 'UTC']
    audit_old, audit_new, audits = differences('ydental_access_audit')
    assert set(audits) == {2655, 2656, 2657}
    assert [(audits[i]['ydental_event'], audits[i]['ydental_source'], audits[i]['ydental_target_model'],
             audits[i]['ydental_target_id']) for i in sorted(audits)] == [
             ('login', 'native_authenticated_login', 'res.users', 6),
             ('login.scope', 'authenticated_session', 'ydental.access.session', 177),
             ('store.switch', 'interactive', 'ydental.access.session', 177)]
    session_old, session_new, sessions = differences('ydental_access_session')
    assert set(sessions) == {177}
    assert sessions[177]['ydental_user_id'] == 6 and sessions[177]['ydental_store_id'] == 1
    assert sessions[177]['ydental_revision'] == 1
    device_old, device_new, devices = differences('res_device_log')
    assert set(devices) == {1} and devices[1]['user_id'] == 6
    assert hashlib.sha256(devices[1]['session_identifier'].encode()).hexdigest() == sessions[177]['ydental_key_hash']
    log_old, log_new, user_logs = differences('res_users_log')
    assert set(user_logs) == {1} and user_logs[1]['create_uid'] == 6
    r3_all = c.all_tables(r3.SOURCE)['signatures']
    changed_tables = sorted(name for name in source['all']['signatures']
                            if source['all']['signatures'][name] != r3_all[name])
    assert all(source['all']['signatures'][name] == r3_all[name] for name in c.NO_MAIL_TABLES)
    src_hashes = c.authority()
    # Exact source implementations used to explain each observed write.
    core_paths = (
        'odoo/addons/base/models/ir_attachment.py', 'odoo/addons/base/models/assetsbundle.py',
        'odoo/addons/base/models/res_users.py', 'odoo/addons/base/models/res_device.py',
        'addons/hr/models/res_users.py', 'addons/hr/models/hr_employee.py',
        'addons/hr/models/resource.py', 'addons/mail/models/mail_thread.py',
        'addons/auth_signup/models/res_users.py',
    )
    source_hashes = {p: s.file_sha(c.CORE / p) for p in core_paths}
    scripts = {str(p.relative_to(c.ROOT)): s.file_sha(p) for p in c.SCRIPTS}
    cli = json.loads(subprocess.check_output([str(c.PYTHON), str(c.ROOT / 'scripts/s10_p0_03_cli_offline.py')], text=True))
    offline = json.loads(subprocess.check_output([str(c.PYTHON), str(c.ROOT / 'scripts/s10_p0_03_offline.py')], text=True))
    assert cli['status'] == 'REAL_CLI_PARSER_PASS' and offline['status'] == 'SIMULATED_PASS'
    assert offline['count'] == 30 and all(v == 'FAIL_CLOSED' for k,v in offline['cases'].items() if k != 'PASS')
    preflight = {
        'status': 'PREFLIGHT_PASS', 'authorization_comment': c.AUTH, 'head': s.HEAD,
        'core_head': s.CORE_HEAD, 'source_oid': s.SOURCE_OID, 'r3_oid': r3.SOURCE_OID,
        'source_name': s.SOURCE, 'source_marker_sha256': s.SOURCE_MARKER,
        'source_config_sha256': s.SOURCE_CONFIG, 'source_manifest_sha256': s.SOURCE_MANIFEST,
        'r3_name': r3.SOURCE, 'r3_marker_sha256': r3.SOURCE_MARKER,
        'r3_config_sha256': r3.SOURCE_CONFIG, 'r3_manifest_sha256': r3.SOURCE_MANIFEST,
        'target': s.TARGET, 'port': s.PORT, 'create_sql': f'CREATE DATABASE "{s.TARGET}" WITH TEMPLATE "{s.SOURCE}"',
        'http_argv': list(c.HTTP_ARGV), 'browser_argv': list(c.BROWSER_ARGV),
        'source_tables': source['managed']['tables'], 'source_all_signatures': source['all']['signatures'],
        'source_schema': source['managed']['schema'], 'source_module_count': len(source['managed']['modules']),
        'source_installed_count': sum(v['state']=='installed' for v in source['managed']['modules'].values()),
        'source_attachment_pointers': source['managed']['attachment_pointers'],
        'source_business': source['managed']['business'],
        'asset_attachments': assets, 'new_files': files,
        'mail_metadata': [{**{k: row.get(k) for k in ('id','model','res_id','message_type','subtype_id',
                         'author_id','create_uid','create_date','write_uid','write_date','is_internal')}
                          , 'body_sha256': s.sha((row.get('body') or '').encode()),
                          'tracked_transition': 'auth_signup.first_login.invited_to_confirmed'}
                          for row in mail.values()],
        'mail_recipients': 0, 'mail_mail_unchanged': True, 'mail_notification_unchanged': True,
        'login_field_diffs': {'res_users': users_diff, 'res_partner': partner_diff,
            'hr_employee': employee_diff, 'hr_version': version_diff, 'resource_resource': resource_diff},
        's01_audits': [{k: row.get(k) for k in ('id','ydental_event','ydental_source',
            'ydental_user_id','ydental_store_id','ydental_target_model','ydental_target_id','ydental_result')}
            for row in audits.values()],
        's01_session': {'id': 177, 'user_id': 6, 'store_id': 1, 'revision': 1,
            'device_key_matches': True},
        'other_login_logs': {'res_users_log_new': 1, 'res_device_log_new': 1,
            'orm_signaling_default_new': source['all']['signatures']['orm_signaling_default']['rows'] - r3_all['orm_signaling_default']['rows']},
        'r3_to_p002_changed_all_public_tables': changed_tables,
        'actor_relations': {str(uid): {'partner_id': ids[0], 'employee_id': ids[1],
            'version_id': ids[2], 'resource_id': ids[2]} for uid, ids in c.ACTORS.items()},
        'allowlist': {'assets_max': 10, 'asset_total_size_each_max': 3000000,
            'checklist_exact_match_zero_bytes': True, 'mail_tracking_max': 4,
            'res_users_log_max': 3, 'res_device_log_max': 3,
            's01_session_max': 3, 's01_audit_max': 11,
            'orm_signaling_default_max': 3,
            'allowed_tables': sorted(c.WEB_TABLES), 'all_other_643_tables_exact': True,
            'business_only_refund14_then_close9': True,
            'money_stock_account_acl_module_view_schema_exact': True},
        'product_hashes': src_hashes, 'odoo_generation_source_hashes': source_hashes,
        'scripts_sha256': scripts, 'offline': offline, 'cli': cli,
        'budgets': {'create': 1, 'upgrade_init_install_shell': 0, 'http': 1,
                    'firefox': 1, 'reject14': 1, 'unlock9': 1, 'denied_posts': 2,
                    'new_receipts_actual_refunds_credit_posts_stock': 0},
    }
    path = c.PREFLIGHT
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists()
    c.save_once(path, preflight)
    c.source_gate(original, source['managed'], source['all'])
    print(json.dumps({'status': 'PREFLIGHT_PASS', 'sha256': s.file_sha(path),
                      'asset_ids': sorted(asset_rows), 'new_file_count': len(files),
                      'mail_ids': sorted(mail), 'all_tables': len(source['all']['signatures']),
                      'simulated_count': offline['count'], 'target': s.TARGET}, ensure_ascii=False))


if __name__ == '__main__':
    main()
