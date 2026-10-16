"""Offline prerequisite evaluation of the one frozen W5 SQL snapshot.

No DB/HTTP/Odoo/browser imports. Raw medical content and credentials stay private.
"""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path

from lxml import etree
from passlib.context import CryptContext


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-13'
OUT = ROOT / 'docs/evidence/s10-p0-13'
TEXT_FIELDS = ('chief_complaint', 'history', 'findings', 'diagnosis',
               'treatment_plan', 'suggested_materials', 'follow_up')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_rows():
    snapshot = json.loads((PRIVATE / 'w5-private-rows.json').read_text())
    public = json.loads((OUT / 'source-before.json').read_text())
    assert hashlib.sha256((PRIVATE / 'w5-private-rows.json').read_bytes()).hexdigest() == public['private_snapshot_sha256']
    assert public['status'] == 'SOURCE_SNAPSHOT_MATCH_ELIGIBILITY_PENDING_OFFLINE_REVIEW'
    assert public['rolled_back'] and public['closed'] and not public['baseline_mismatches']
    return {t: [json.loads(r) for r in rs] for t, rs in snapshot['tables'].items()}


def credentials(tables):
    # Reuse the existing synthetic W3 doctor's identity; never change an account.
    fixture = json.loads((ROOT / '.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json').read_text())
    assert (fixture['database'], fixture['oid']) == ('ydental_s10_test_20261015060000_b6c7d8e9', 2100285)
    tree = ast.parse((ROOT / 'scripts/s10_e2e_w5_browser.py').read_text())
    values = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == 'fill' and n.args
        and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)
        and isinstance(n.func.value, ast.Call) and n.func.value.args
        and isinstance(n.func.value.args[0], ast.Constant)
        and n.func.value.args[0].value == '[name=password]']
    assert len(values) == 1
    user = next(r for r in tables['res_users'] if r['id'] == 7)
    assert fixture['roles']['doctor'] == user['login']
    assert CryptContext(schemes=['pbkdf2_sha512']).verify(values[0], user['password'])
    return user['login'], values[0]


def normalized(node):
    return [node.tag, dict(node.attrib), (node.text or '').strip(),
            [normalized(n) for n in node if isinstance(n.tag, str)], (node.tail or '').strip()]


def evaluate():
    t = source_rows()
    one = lambda table, ident: next(r for r in t[table] if r['id'] == ident)
    doc, user, store = one('ydental_clinical_document', 1), one('res_users', 7), one('ydental_access_store', 1)
    checks, facts = {}, {}
    def check(name, ok):
        checks[name] = bool(ok)
    check('doc_source_identity', (doc['ydental_patient_id'], doc['ydental_store_id'], store['company_id']) == (1, 1, 1))
    check('pending_v2_responsible7', (doc['state'], doc['ydental_version'], doc['ydental_responsible_id'], doc['ydental_author_id']) == ('pending', 2, 7, 7))
    content = doc['ydental_content']
    check('complete_nonempty_original_content', set(content) == set(TEXT_FIELDS) | {'teeth'}
          and all(isinstance(content[k], str) and len(content[k]) <= 10000 for k in TEXT_FIELDS)
          and any(content[k].strip() for k in TEXT_FIELDS) and content['teeth'] == [])
    versions = sorted((r for r in t['ydental_clinical_version'] if r['ydental_document_id'] == 1), key=lambda r: r['ydental_number'])
    check('original_versions1_2_same_content', len(versions) == 2 and [r['ydental_number'] for r in versions] == [1, 2]
          and all(r['ydental_content'] == content and r['ydental_author_id'] == 7 and r['ydental_store_id'] == r['ydental_patient_id'] == 1
                  and r['ydental_recorded_at'] and r['ydental_kind'] == 'save' for r in versions)
          and versions[1]['ydental_previous_id'] == versions[0]['id'])
    execution = one('ydental_queue_execution', doc['ydental_current_execution_id'])
    original = one('ydental_queue_execution', doc['ydental_execution_id'])
    task = one('ydental_intake_task', execution['ydental_task_id'])
    lease = one('ydental_queue_lease', execution['ydental_lease_id'])
    station = one('ydental_space_station', lease['ydental_station_id'])
    mapping = one('ydental_intake_mapping', task['ydental_mapping_id'])
    catalog = one('ydental_intake_catalog', mapping['ydental_catalog_id'])
    snapshot = execution['ydental_service_snapshot']
    check('original_current_execution_identity', doc['ydental_execution_id'] == doc['ydental_current_execution_id'] == 1
          and all(r['ydental_patient_id'] == r['ydental_store_id'] == 1 for r in (execution, original, task))
          and execution['state'] == 'handover' and execution['ydental_category'] == 'medical')
    check('handover_not_active_reception', not lease['ydental_active'] and lease['ydental_actor_id'] == 7
          and lease['ydental_store_id'] == station['ydental_store_id'] == 1)
    member = [r for r in t['ydental_access_membership'] if r['ydental_user_id'] == 7 and r['ydental_store_id'] == 1 and r['active']]
    check('one_active_membership', len(member) == 1 and member[0]['id'] == 5 and member[0]['ydental_employee_id'] == 3)
    member = member[0]
    employee = one('hr_employee', member['ydental_employee_id'])
    check('active_person_company_store_employee', user['active'] and not user['share'] and user['company_id'] == 1
          and store['active'] and employee['active'] and employee['user_id'] == 7 and employee['company_id'] == 1
          and {'cid': 1, 'user_id': 7} in t['res_company_users_rel'])
    levels = {r['ydental_category']: r['ydental_level'] for r in t['ydental_access_grant'] if r['ydental_membership_id'] == member['id']}
    check('medical_write_now', levels.get('medical') == 'write')
    active_caps = {r['id'] for r in t['ydental_access_capability'] if r['active']}
    caps = {r['ydental_access_capability_id'] for r in t['res_users_ydental_access_capability_rel'] if r['res_users_id'] == 7} & active_caps
    check('current_snapshot_capability', snapshot['capability_id'] in caps and snapshot['capability_id'] == catalog['ydental_capability_id'])
    check('qualification_satisfied_without_provider', snapshot['qualification'] == catalog['ydental_qualification'] == '')
    station_caps = {r['ydental_access_capability_id'] for r in t['ydental_space_station_add_rel'] if r['ydental_space_station_id'] == station['id']} & active_caps
    area = one('ydental_space_area', station['ydental_area_id'])
    floor = one('ydental_space_floor', station['ydental_floor_id'])
    check('source_station_capability_and_context', station['active'] and station['ydental_enabled'] and station['ydental_callable']
          and station['ydental_kind'] == 'care' and station_caps and station_caps <= caps
          and snapshot['capability_id'] in station_caps and area['active'] and floor['active']
          and mapping['active'] and catalog['active'] and mapping['ydental_area_id'] == snapshot['area_id']
          and mapping['ydental_execution_area_id'] == snapshot['execution_area_id'] == area['id'])
    check('no_document_editor_or_stale_metadata', not doc['ydental_editor_id'] and not doc['ydental_session_id']
          and not doc['ydental_editor_hash'] and not doc['ydental_connection_hash'] and not doc['ydental_editor_expires']
          and not doc['ydental_editor_lease_id'] and doc['ydental_session_revision'] == 0)
    check('current_patient_relation', any(r['ydental_patient_id'] == r['ydental_store_id'] == 1 and not r['ydental_superseded_by_id'] for r in t['ydental_patient_relation']))
    own_leases = {r['id'] for r in t['ydental_queue_lease'] if r['ydental_actor_id'] == 7}
    check('no_live_actor_execution_fence', not any(r['ydental_lease_id'] in own_leases and r['state'] in ('serving', 'verify') for r in t['ydental_queue_execution']))
    groups = {r['gid'] for r in t['res_groups_users_rel'] if r['uid'] == 7}
    while True:
        expanded = groups | {r['hid'] for r in t['res_groups_implied_rel'] if r['gid'] in groups}
        if expanded == groups:
            break
        groups = expanded
    group = lambda xmlid: next(r['res_id'] for r in t['ir_model_data'] if r['module'] + '.' + r['name'] == xmlid and r['model'] == 'res.groups')
    check('internal_ydental_group', {group('base.group_user'), group('ydental_base.ydental_base_group_user')} <= groups)
    modules = {r['name']: {'state': r['state'], 'version': r['latest_version'], 'write_date': r['write_date']} for r in t['ir_module_module']}
    old = json.loads((ROOT / 'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json').read_text())['target']
    module_sha = digest(modules)
    check('installed_module_seal', module_sha == old['module_meta_sha256'] and sum(r['state'] == 'installed' for r in modules.values()) == 92)
    view = next(r for r in t['ir_ui_view'] if r.get('key') == 'ydental_clinical.ydental_clinical_page')
    source = etree.parse(str(ROOT / 'ydental_clinical/views/ydental_clinical_templates.xml')).xpath('//template[@id="ydental_clinical_page"]')[0]
    installed = etree.fromstring(view['arch_db']['en_US'].encode())
    check('installed_clinical_qweb_matches_source', view['active'] and [normalized(n) for n in source] == [normalized(n) for n in installed])
    required_ids = {'open-document', 'confirm-document', 'release-document', 'server-version', 'clinical-result',
                    'terminal-uncertain-message', 'terminal-committed-message', 'text-state'}
    check('qweb_dom_and_zh_CN_present', all(required_ids <= set(etree.fromstring(arch.encode()).xpath('//@id')) for arch in view['arch_db'].values()) and 'zh_CN' in view['arch_db'])
    params = {r['key']: r['value'] for r in t['ir_config_parameter']}
    heartbeat, timeout = int(params['ydental_queue.heartbeat_seconds']), int(params['ydental_queue.timeout_seconds'])
    check('explicit_timeout_configuration', 1 <= heartbeat < timeout <= 86400)
    # Finite native authentication credential verification, offline only.
    credentials(t)
    check('existing_synthetic_doctor_credential_verified_offline', True)
    invoice = one('account_move', 1)
    check('invoice_posted740_residual0', invoice['state'] == 'posted' and invoice['amount_total'] == 740 and invoice['amount_residual'] == 0 and invoice['payment_state'] == 'paid' and invoice['company_id'] == 1)
    check('native_payments_partials_500_240', [r['amount'] for r in t['account_payment']] == [500, 240]
          and [r['amount'] for r in t['account_partial_reconcile']] == [500, 240]
          and all(r['debit_move_id'] == 5 and r['company_id'] == 1 for r in t['account_partial_reconcile']))
    fees = {r['id']: r for r in t['ydental_treatment_fee']}
    sources = t['ydental_settlement_source']
    check('same_source_fees_sources740', [r['ydental_amount'] for r in t['ydental_treatment_fee']] == [600, 80, 40, 20]
          and len(sources) == 4 and {r['id']: r['ydental_fee_id'] for r in sources} == {1: 4, 2: 3, 3: 2, 4: 1} and {r['ydental_fee_id'] for r in sources} == set(fees)
          and all(r['ydental_invoice_id'] == 1 and r['ydental_patient_id'] == r['ydental_store_id'] == 1
                  and r['ydental_original_amount'] == fees[r['ydental_fee_id']]['ydental_amount']
                  and one('account_move_line', r['ydental_line_id'])['move_id'] == 1 for r in sources))
    check('no_refund_close_print_job', not t['ydental_settlement_refund'] and not t['ydental_settlement_close'] and not t['ydental_print_job'])
    facts = {'document': {'id': 1, 'patient': 1, 'store': 1, 'company': 1, 'state': doc['state'], 'version': doc['ydental_version'],
                         'author': doc['ydental_author_id'], 'responsible': doc['ydental_responsible_id'],
                         'original_execution': doc['ydental_execution_id'], 'current_execution': doc['ydental_current_execution_id'],
                         'content_sha256': digest(content), 'editor_id': doc['ydental_editor_id']},
             'versions': [{'id': r['id'], 'number': r['ydental_number'], 'author': r['ydental_author_id'], 'kind': r['ydental_kind'],
                           'recorded_at': r['ydental_recorded_at'], 'content_sha256': digest(r['ydental_content']),
                           'row_sha256': digest(r)} for r in versions],
             'user': {'id': 7, 'active': user['active'], 'company': 1, 'store': 1, 'membership': member['id'],
                      'employee': employee['id'], 'medical': levels['medical'], 'active_capabilities': sorted(caps)},
             'execution': {'id': execution['id'], 'state': execution['state'], 'task': task['id'], 'lease': lease['id'],
                           'lease_active': lease['ydental_active'], 'station': station['id'], 'service_snapshot': snapshot},
             'module_meta_sha256': module_sha, 'installed_modules': 92, 'qweb_view': view['id'],
             'qweb_arch_sha256': {lang: hashlib.sha256(arch.encode()).hexdigest() for lang, arch in view['arch_db'].items()},
             'queue_heartbeat_seconds': heartbeat, 'editor_timeout_seconds': timeout,
             'explicit_source_fee_links': [{'source_id': r['id'], 'fee_id': r['ydental_fee_id'],
                 'invoice_id': r['ydental_invoice_id'], 'line_id': r['ydental_line_id'],
                 'amount': r['ydental_original_amount']} for r in sources]}
    result = {'status': 'ELIGIBILITY_AND_SOURCE_PASS' if all(checks.values()) else 'BLOCKED_PREFLIGHT',
              'checks': checks, 'failed': [k for k, v in checks.items() if not v], 'facts': facts,
              'execution_not_yet_enabled': True, 'evidence_level': 'current P0-13 first source snapshot', 'CREATE': 0, 'HTTP': 0, 'Firefox': 0, 'POST': 0}
    with (OUT / 'eligibility.json').open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'failed': result['failed']}))


if __name__ == '__main__':
    evaluate()
