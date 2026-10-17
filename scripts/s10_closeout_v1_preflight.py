"""Pure files only: provenance, full-row comparator counterexamples and freeze inputs."""
import ast
import builtins
import configparser
import copy
import io
import json
import os
from pathlib import Path
import secrets
import symtable
import sys
from unittest.mock import patch
import s10_closeout_v1_contract as c
from s10_closeout_v1_runtime import document_gate


def main():
    os.umask(0o077)
    c.PRIVATE.mkdir(mode=0o700, exist_ok=True); c.OUT.mkdir(parents=True, exist_ok=True)
    label_input = sys.argv[1] if len(sys.argv) > 1 else 'initial'
    if label_input.startswith('R1'):
        assert c.git('merge-base', c.BASE, 'HEAD') == c.BASE
        assert not c.git('diff', c.BASE, 'HEAD', '--', 'ydental_*')
    else:
        assert c.git('rev-parse', 'HEAD') == c.BASE
    assert c.git('branch', '--show-current') == c.BRANCH
    assert c.git('rev-parse', 'HEAD', cwd=c.CORE_ROOT) == c.CORE
    assert not c.git('status', '--porcelain', '--untracked-files=no', cwd=c.CORE_ROOT)
    private_manifest = c.read(c.ROOT / 'docs/evidence/s10-p0-21/private-evidence-manifest.json')['files']
    dependency_paths = ['.local/s10-p0-21/final-RO-rows.json'] + [str((c.SOURCE_RUN / name).relative_to(c.ROOT)) for name in ['b-chain.json', 'original.json', 'trade.json', 'database.json', 'odoo.conf']]
    dependency_sha = {}
    for path in dependency_paths:
        entry = next(row for row in private_manifest if row['path'] == path)
        digest = c.sha((c.ROOT / path).read_bytes()); assert digest == entry['sha256']
        dependency_sha[path] = digest
    snapshot = c.read(c.ROOT / '.local/s10-p0-21/final-RO-rows.json')
    assert len(snapshot['tables']) == 645 and snapshot['oid'] == c.SOURCE_OID
    marker = c.read(c.SOURCE_RUN / 'b-chain.json')
    doc = next(row for row in snapshot['tables']['ydental_clinical_document'] if row['id'] == marker['document_id'])
    assert doc['state'] == 'pending' and doc['ydental_version'] == 2 and doc['ydental_editor_id'] is None
    payment = next(row for row in snapshot['tables']['ydental_settlement_payment'] if row['id'] == marker['payment_first_id'])
    assert str(payment['ydental_amount']) == '350.00'
    scripts = sorted((c.ROOT / 'scripts').glob('s10_closeout_v1_*.py'))
    undefined = {}
    for path in scripts:
        raw = path.read_text(); compile(raw, str(path), 'exec')
        table = symtable.symtable(raw, str(path), 'exec')
        defined = {s.get_name() for s in table.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
        allowed = defined | set(dir(builtins)) | {'__file__', '__name__'}
        missing = set()
        def walk(scope):
            for symbol in scope.get_symbols():
                if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in allowed:
                    missing.add(symbol.get_name())
            for child in scope.get_children(): walk(child)
        walk(table); undefined[str(path.relative_to(c.ROOT))] = sorted(missing)
    assert not any(undefined.values()), undefined
    cases = ast.parse((c.ROOT / 'scripts/s10_closeout_v1_cases.py').read_text())
    assert not any(isinstance(node, ast.Constant) and type(node.value) is int and node.value == 500 for node in ast.walk(cases))
    assert not any(isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                   and node.value.id == 'slot' and isinstance(node.slice, ast.Constant)
                   and node.slice.value == 'version' for node in ast.walk(cases)), 'SLOT_RETURN_HAS_NO_VERSION'
    definitions = {n.name: n for n in cases.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert 'D_admission' in definitions
    setup_text = ast.get_source_segment((c.ROOT / 'scripts/s10_closeout_v1_cases.py').read_text(), definitions['T05_setup'])
    assert setup_text.index('D_admission(cr, root)') < setup_text.index("inherited_identity(root)")
    admission_text = ast.get_source_segment((c.ROOT / 'scripts/s10_closeout_v1_cases.py').read_text(), definitions['D_admission'])
    assert all(word in admission_text for word in ['_close_guard_any', '_close_guard', 'finance_approval', '_config', 'company_ids'])
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {'_unlock', 'sudo'} for n in ast.walk(definitions['D_admission']))
    clinical = ast.parse((c.ROOT / 'ydental_clinical/models/ydental_clinical_service.py').read_text())
    release = next(n for n in ast.walk(clinical) if isinstance(n, ast.FunctionDef) and n.name == '_release')
    returned = next(n.value for n in ast.walk(release) if isinstance(n, ast.Return))
    assert [n.value for n in returned.keys] == ['document_id']
    browser = (c.ROOT / 'scripts/s10_closeout_v1_browser.py').read_text()
    web = (c.ROOT / 'scripts/s10_closeout_v1_web.py').read_text()
    assert "window('pre')" in web and "owned_HTTP_stopped" in web and "window('post')" in web
    assert web.index("owned_HTTP_stopped']") < web.index("run_native('upgrade')")
    assert "same_key" in browser and "B-six-real-RPC-denials" in browser
    fields = {'doc': 'ydental_clinical_document', 'invoice': 'account_move', 'original': 'ydental_settlement_bill_original',
              'payment': 'ydental_settlement_payment', 'refund': 'ydental_settlement_refund',
              'catalog0': 'ydental_intake_catalog', 'old_mapping': 'ydental_intake_mapping',
              'station': 'ydental_space_station', 'area': 'ydental_space_area'}
    for node in ast.walk(cases):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in fields and node.attr.startswith('ydental_'):
            columns = {row['column'] for row in snapshot['schema'][fields[node.value.id]]}
            assert node.attr in columns, (node.value.id, node.attr, fields[node.value.id])
    # Deterministic positive and negative stored-field counterexamples, no native execution.
    selected = {'ydental_clinical_document', 'ydental_clinical_version', 'ydental_access_audit', 'account_move',
                'ydental_patient_mutex', 'ydental_supply_mutex', 'ydental_intake_mutex', 'ydental_queue_mutex'}
    before = {k: v for k, v in snapshot.items() if k != 'tables'}
    before['tables'] = {t: copy.deepcopy(snapshot['tables'][t]) for t in selected}
    after = copy.deepcopy(before)
    newdoc = next(row for row in after['tables']['ydental_clinical_document'] if row['id'] == doc['id'])
    newdoc.update(ydental_editor_id=7, ydental_session_id=999999, ydental_session_revision=1,
                  ydental_connection_hash='STATIC_ONLY', ydental_editor_hash='STATIC_ONLY',
                  ydental_editor_expires='2026-10-17T07:00:00', write_uid=7, write_date='2026-10-17T06:00:00')
    for t in selected:
        if t.endswith('_mutex'): after['tables'][t][0]['ydental_revision'] += 1
    audit = copy.deepcopy(before['tables']['ydental_access_audit'][0])
    audit.update(id=999999, ydental_event='clinical.edit_acquire', ydental_target_id=doc['id'], ydental_user_id=7, ydental_store_id=1)
    after['tables']['ydental_access_audit'].append(audit)
    gate = document_gate('acquire', 7, doc['id'], 999999)
    gate(before, after, c.diff(before, after)[0])
    lifecycle = copy.deepcopy(after)
    for action in ['confirm', 'correct', 'release']:
        previous = copy.deepcopy(lifecycle)
        target = next(row for row in lifecycle['tables']['ydental_clinical_document'] if row['id'] == doc['id'])
        for table in selected:
            if table.endswith('_mutex'): lifecycle['tables'][table][0]['ydental_revision'] += 1
        new_audit = copy.deepcopy(audit); new_audit['id'] += len(lifecycle['tables']['ydental_access_audit'])
        new_audit['ydental_event'] = 'clinical.' + ('edit_release' if action == 'release' else action)
        lifecycle['tables']['ydental_access_audit'].append(new_audit)
        if action == 'release':
            for field in ['ydental_editor_id', 'ydental_session_id', 'ydental_connection_hash', 'ydental_editor_hash',
                          'ydental_editor_expires', 'ydental_editor_lease_id']: target[field] = None
            target['ydental_session_revision'] = 0
        else:
            version = copy.deepcopy(max((row for row in lifecycle['tables']['ydental_clinical_version'] if row['ydental_document_id'] == doc['id']), key=lambda row: row['ydental_number']))
            version.update(id=max(row['id'] for row in lifecycle['tables']['ydental_clinical_version']) + 1,
                           ydental_previous_id=version['id'], ydental_number=target['ydental_version'] + 1,
                           ydental_kind=action, ydental_author_id=7, ydental_reason='CLOSEOUT wording only, no economic action')
            target['ydental_content'] = dict(target['ydental_content'])
            if action == 'correct': target['ydental_content']['chief_complaint'] = 'CLOSEOUT synthetic administrative wording correction only'
            target.update(state='confirmed', ydental_version=version['ydental_number'], ydental_saved_at='2026-10-17T06:01:00')
            version['ydental_content'] = dict(target['ydental_content'])
            lifecycle['tables']['ydental_clinical_version'].append(version)
        document_gate(action, 7, doc['id'], 999999)(previous, lifecycle, c.diff(previous, lifecycle)[0])
    rejected = []
    for label in ['stored_amount', 'patient_identity', 'mutex_delta2', 'audit_wrong_actor']:
        bad = copy.deepcopy(after)
        if label == 'stored_amount': bad['tables']['account_move'][0]['amount_total'] = '741.00'
        if label == 'patient_identity': next(r for r in bad['tables']['ydental_clinical_document'] if r['id'] == doc['id'])['ydental_patient_id'] = 2
        if label == 'mutex_delta2': bad['tables']['ydental_patient_mutex'][0]['ydental_revision'] += 1
        if label == 'audit_wrong_actor': bad['tables']['ydental_access_audit'][-1]['ydental_user_id'] = 8
        try: gate(before, bad, c.diff(before, bad)[0])
        except AssertionError: rejected.append(label)
        else: raise AssertionError('COUNTEREXAMPLE_ACCEPTED:' + label)
    from s10_closeout_v1_web import upgrade_gate, action_projections
    chosen = {'ir_actions', 'ir_act_window', 'ir_act_report_xml', 'ir_act_url', 'ir_act_server', 'ir_act_client',
              'ir_model_data', 'ir_module_module', 'ir_ui_view', 'ir_ui_menu', 'account_move'}
    meta = {k: v for k, v in snapshot.items() if k != 'tables'}
    meta['tables'] = {t: copy.deepcopy(snapshot['tables'][t]) for t in chosen}
    action_projections(meta)
    own_action = next(r['res_id'] for r in meta['tables']['ir_model_data']
                      if r['module'] == 'ydental_settlement' and r['model'] == 'ir.actions.act_url')
    changed = copy.deepcopy(meta)
    for table in ['ir_act_url', 'ir_actions']:
        row = next(r for r in changed['tables'][table] if r['__physical_table__'] == 'ir_act_url' and r['id'] == own_action)
        row['write_date'] = 'STATIC_ONLY_UTC'; row['write_uid'] = 1
    with patch.object(c, 'save', lambda *args: None):
        upgrade_gate(meta, changed, c.diff(meta, changed)[0])
        for label, table, field, value in [('upgrade_economic', 'account_move', 'amount_total', '999.00'),
                ('action_url_changed', 'ir_act_url', 'url', '/unsafe'),
                ('action_parent_inconsistent', 'ir_actions', 'name', {'en_US': 'wrong'})]:
            bad_meta = copy.deepcopy(changed)
            target = next(r for r in bad_meta['tables'][table] if (r['id'] == own_action if table != 'account_move' else r['id'] == 1))
            target[field] = value
            try: upgrade_gate(meta, bad_meta, c.diff(meta, bad_meta)[0])
            except AssertionError: rejected.append(label)
            else: raise AssertionError('METADATA_COUNTEREXAMPLE_ACCEPTED:' + label)
    duplicates = copy.deepcopy(meta)
    duplicates['tables']['ir_act_url'].append(copy.deepcopy(duplicates['tables']['ir_act_url'][0]))
    assert any(r['duplicate_key_preserved'] for r in c.diff(meta, duplicates)[0])
    rejected.append('duplicate_physical_key_preserved_not_silently_overwritten')
    for label, raw in [('unescaped_control', '{"a":"bad' + chr(31) + '"}'),
                       ('duplicate_json_key', '{"a":1,"a":2}'), ('truncated_JSON', '{"a":')]:
        target = c.PRIVATE / ('STATIC-' + label + '.txt')
        if not target.exists(): target.write_text(raw)
        try: c.read(target)
        except ValueError: rejected.append(label)
        else: raise AssertionError('INVALID_JSON_ACCEPTED:' + label)
    checkpoint_source = (c.ROOT / 'scripts/s10_closeout_v1_runtime.py').read_text().split('def checkpoint(')[1].split('def verify_loaded')[0]
    assert checkpoint_source.index('cr.commit()') < checkpoint_source.index("after = c.readonly(")
    assert checkpoint_source.index("'-committed')") < checkpoint_source.index('for path, value in marker.items()')
    rejected.append('marker_only_after_independent_commit_readback')
    label = sys.argv[1] if len(sys.argv) > 1 else 'initial'
    try: c.persist('STATIC-evidence-before-rejection-' + label, before, bad, gate)
    except AssertionError: pass
    else: raise AssertionError('PERSIST_MUST_REJECT')
    assert (c.PRIVATE / ('STATIC-evidence-before-rejection-' + label + '-full-diff.json')).exists()
    parser = configparser.ConfigParser(interpolation=None)
    parser['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
        'db_password': c.credentials()['password'], 'db_name': c.NAME, 'dbfilter': '^' + c.NAME + '$',
        'db_maxconn': '8', 'addons_path': ','.join(str(p) for p in [c.CORE_ROOT / 'odoo/addons', c.CORE_ROOT / 'addons', c.ROOT]),
        'data_dir': str(c.RUN / 'data'), 'http_interface': '127.0.0.1', 'http_port': str(c.PORT),
        'workers': '0', 'max_cron_threads': '0', 'list_db': 'False', 'admin_passwd': secrets.token_urlsafe(32),
        'log_handler': 'odoo.sql_db.connection:DEBUG', 'smtp_server': '127.0.0.1', 'smtp_port': '1'}
    buffer = io.StringIO(); parser.write(buffer)
    if not (c.PRIVATE / 'proposed-odoo.conf').exists():
        (c.PRIVATE / 'proposed-odoo.conf').open('x').write(buffer.getvalue())
    c.save(c.OUT / ('static-preflight-result-' + label + '.json'), {'exit_code': 0, 'pure_files_only': True,
        'old_evidence_not_rehashed_or_rewritten': True, 'source_private_dependencies_sha256': dependency_sha,
        'new_scripts_compile_and_symbols': undefined, 'no_stale_500': True, 'all_four_document_lifecycle_predicates': True,
        'real_catalog_field_handoffs_checked': True,
        'native_slot_return_contract': 'slot returns id/warning/policy, publish version read from actual returned record',
        'document_mutex_positive': 'four exact records +1 each',
        'deterministic_rejections': rejected, 'full_evidence_saved_before_rejection': True,
        'DB_CREATE_Odoo_HTTP_Firefox_used': 0, 'config_sha256': c.sha((c.PRIVATE / 'proposed-odoo.conf').read_bytes())})
    c.save(c.OUT / ('execution-contract-' + label + '.json'), {
        'authority': 'USER_DIRECT_S10_CLOSEOUT_PLAN_v1.1', 'source': c.SOURCE, 'source_oid': c.SOURCE_OID,
        'database': c.NAME, 'port': c.PORT, 'source_connections': 3 if (c.PRIVATE / 'source-budget-approval.json').exists() else 2, 'maintenance_connections': 1,
        'CREATE': 1, 'READ_ONLY_RR_total': 28, 'Odoo_processes': 6, 'max_native_pool': 8,
        'HTTP_total': 600, 'original_GET_total': 12, 'original_generation': 0,
        'PDF_new_refund_render': 2, 'permission_category_changes_max': 8, 'new_S01_audit_max': 500,
        'S10_upgrade': 1, 'repairs_max': 2, 'D_new_source': {'bill': 6, 'inbound': 6, 'refund_request': 2, 'outbound_max': 2},
        'D_actor': 5, 'D_distinct_approver': 6, 'doctor': 7, 'store': 1, 'company': 1, 'channel': 'cash',
        'D_date': 'actual current store local date, independently frozen before upstream and checked per action',
        'D_new_identity_or_expanded_permission': False, 'D_old_close_unlock': False,
        'R1_source_budget_exception_state': 'EXPLICITLY_APPROVED' if (c.PRIVATE / 'source-budget-approval.json').exists() else 'PENDING_NOT_IMPLEMENTED',
        'R1_actor_flush_before_uid1_projection': label_input.startswith('R1'),
        'R1_C_revoke_restore': 'same legal manager5 HTTP grant, not extra Odoo processes',
        'A_acquire_confirm_correct_release_each': 1, 'A_normal_editor_heartbeat_max': 3,
        'A_editor_timeout_unchanged': True, 'A_versions': [2, 3, 4],
        'B_MODEL_write_unlink': 6, 'B_RPC_write_unlink': 6,
        'C_permissions': ['reader8 settlement none->read->none', 'reader8 export write->none->write',
                          'rollback-only manager5 store2 settlement none->read', 'rollback-only manager41 store11 export none->write'],
        'D_client_response_loss': 1, 'D_verified_same_actor_key_payload_repeat': 1,
        'source_SQL': [c.IDENTITY, c.CATALOG, 'SHOW transaction_read_only', 'SHOW transaction_isolation',
            "SELECT t.tableoid::regclass::text,t.tableoid,to_jsonb(t)::text,encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') FROM public.<catalog-identifier> t ORDER BY <catalog-key>",
            'SELECT pid,state,application_name FROM pg_stat_activity WHERE datid=%s AND pid<>pg_backend_pid() ORDER BY pid', 'ROLLBACK'],
        'maintenance_SQL': ['SELECT oid,datname FROM pg_database ORDER BY oid', 'SELECT pid FROM pg_stat_activity WHERE datid=%s',
                            'CREATE DATABASE <frozen_identifier> TEMPLATE <frozen_source_identifier>', 'SELECT oid FROM pg_database WHERE datname=%s'],
        'full_capture_nodes': ['source-before', 'clone-initial', 'E-before-upgrade', 'E-after-upgrade', 'final-tail', 'source-final'],
        'per_action_capture': 'all stored ydental/account/stock/identity/permission/original/attachment facts; display separate',
        'evidence_first': True, 'independent_commit_readback_before_marker': True,
        'safety_refusal': 'STOP; no different tool, identity or entrypoint retry',
        'hard_stops': ['identity drift', 'raw digest or saved-byte mismatch', 'unknown economic outcome',
                       'unauthorized content', 'SIGSEGV', 'invalid fixture rollback', 'budget exceeded'],
        'S11_merge_deploy_Project_Issue_status': 0})
    print('CLOSEOUT_PURE_FILE_PREFLIGHT_PASS; DATABASE_ODOO_HTTP_FIREFOX0')


if __name__ == '__main__': main()
