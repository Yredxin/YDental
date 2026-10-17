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
import s10_p0_22_contract as c
from s10_p0_22_runtime import document_gate


def main():
    os.umask(0o077)
    c.PRIVATE.mkdir(mode=0o700, exist_ok=True); c.OUT.mkdir(parents=True, exist_ok=True)
    assert c.git('rev-parse', 'HEAD') == c.BASE
    assert c.git('branch', '--show-current') == c.BRANCH
    assert c.git('rev-parse', 'HEAD', cwd=c.CORE_ROOT) == c.CORE
    assert not c.git('status', '--porcelain', '--untracked-files=no', cwd=c.CORE_ROOT)
    old_manifest = c.read(c.ROOT / 'docs/evidence/s10-p0-21/file-sha256.json')
    for entry in old_manifest['files']:
        assert c.sha((c.ROOT / entry['path']).read_bytes()) == entry['sha256'], entry['path']
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
    scripts = sorted((c.ROOT / 'scripts').glob('s10_p0_22_*.py'))
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
    cases = ast.parse((c.ROOT / 'scripts/s10_p0_22_cases.py').read_text())
    assert not any(isinstance(node, ast.Constant) and type(node.value) is int and node.value == 500 for node in ast.walk(cases))
    assert not any(isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                   and node.value.id == 'slot' and isinstance(node.slice, ast.Constant)
                   and node.slice.value == 'version' for node in ast.walk(cases)), 'SLOT_RETURN_HAS_NO_VERSION'
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
                           ydental_kind=action, ydental_author_id=7, ydental_reason='P022 wording only, no economic action')
            target['ydental_content'] = dict(target['ydental_content'])
            if action == 'correct': target['ydental_content']['chief_complaint'] = 'P022 synthetic administrative wording correction only'
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
        'old_347_SHA256_all_equal': True, 'source_private_dependencies_sha256': dependency_sha,
        'new_scripts_compile_and_symbols': undefined, 'no_stale_500': True, 'all_four_document_lifecycle_predicates': True,
        'real_catalog_field_handoffs_checked': True,
        'native_slot_return_contract': 'slot returns id/warning/policy, publish version read from actual returned record',
        'document_mutex_positive': 'four exact records +1 each',
        'deterministic_rejections': rejected, 'full_evidence_saved_before_rejection': True,
        'DB_CREATE_Odoo_HTTP_Firefox_used': 0, 'config_sha256': c.sha((c.PRIVATE / 'proposed-odoo.conf').read_bytes())})
    print('P022_PURE_FILE_PREFLIGHT_PASS; DATABASE_ODOO_HTTP_FIREFOX0')


if __name__ == '__main__': main()
