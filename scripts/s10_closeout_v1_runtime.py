"""Own-cursor native checkpoints; each predicate runs after complete evidence save."""
from collections import defaultdict
from types import CodeType
import os
import traceback
from pathlib import Path
import s10_closeout_v1_contract as c

COUNTS = defaultdict(int)


def failure_evidence(label, stage, error, obtained=None):
    """Save the primary exception before attempting any optional diagnostic read."""
    record = {'stage': stage, 'type': type(error).__name__, 'message': str(error),
              'traceback': ''.join(traceback.format_exception(error)), 'obtained': obtained or {},
              'snapshot_status': 'NOT_ATTEMPTED_NO_UID1_FLUSH'}
    path = c.PRIVATE / (label + '-primary-exception.json')
    try:
        c.save(path, record)
        c.save(c.OUT / (label + '-primary-exception-index.json'), {
            'stage': stage, 'type': type(error).__name__, 'private_file': str(path.relative_to(c.ROOT)),
            'sha256': c.sha(path.read_bytes()), 'snapshot_status': record['snapshot_status']})
    except BaseException as saving_error:
        # Never replace the business/flush/capture exception with a diagnostic failure.
        try: c.event('exception_save_unavailable', label=label, primary=type(error).__name__, secondary=type(saving_error).__name__)
        except BaseException: pass


def exception_snapshot(env, label, before):
    """Best effort only after the primary exception has been durably recorded."""
    try:
        after = snapshot(env)
        c.persist(label + '-exception', before, after, lambda a, b, d: {'exception_only_no_business_PASS': True})
    except BaseException as secondary:
        failure_evidence(label + '-secondary', 'exception_snapshot_unavailable', secondary,
                         {'before_saved': True, 'no_uid1_flush': True})


def key():
    import secrets
    return secrets.token_hex(16)


def bind(root, uid, store_id):
    access = root['ydental.access.service'].with_user(uid)
    session = access._session_for_key(key())
    bound = access._bind(session)
    bound._switch(store_id)
    # Flush the normal actor's writes before the uid1 read-only projection.
    # Odoo20 _write_multi supplies env.uid when an unchanged write_uid was not dirty.
    bound.env.flush_all()
    return bound._bind(session)


def snapshot(env):
    from odoo.orm.environments import Environment
    assert not any(env._field_dirty.values()), 'ACTOR_MUST_FLUSH_BEFORE_UID1_PROJECTION'
    assert not any(any(ids) for ids in env.transaction.tocompute.values()), 'ACTOR_PENDING_COMPUTE_BEFORE_PROJECTION'
    audit = Environment(env.cr, 1, {'lang': 'zh_CN'})
    fields = {'ydental.clinical.document': ['id', 'display_name', 'state', 'ydental_version'],
              'account.move': ['id', 'display_name', 'partner_id'],
              'stock.move': ['id', 'display_name', 'product_id']}
    display = {name: audit[name].search([], order='id').read(names) for name, names in fields.items()}
    assert not any(env._field_dirty.values()), 'READ_PROJECTION_MUST_NOT_DIRTY_STORED_FIELDS'
    result = c.capture(env.cr)
    result['display_projection'] = display
    result['display_fields'] = fields
    return result


def observe(env, label, call, predicate, actor_env=None):
    label = os.environ['YDENTAL_CLOSEOUT_ACTION'] + '-' + label
    COUNTS[label] += 1
    label += '-' + str(COUNTS[label])
    stage = 'before_snapshot'
    try:
        before = snapshot(env)
        c.save(c.PRIVATE / (label + '-intent-before.json'), before)
        c.event('native_action_intent', label=label)
        stage = 'business_call'
        value = call()
        stage = 'actor_flush'
        if actor_env is not None:
            actor_env.flush_all()
        stage = 'after_snapshot'
        after = snapshot(env)
        stage = 'persist_and_predicate'
        c.persist(label, before, after, predicate)
    except BaseException as error:
        failure_evidence(label, stage, error, {'before_saved': 'before' in locals(), 'after_acquired': 'after' in locals()})
        if stage in {'business_call', 'actor_flush'}:
            exception_snapshot(env, label, before)
        c.event('native_action_exception', label=label, error=type(error).__name__)
        raise
    c.event('native_action_returned', label=label)
    return value


def no_economics(before, after, changes):
    assert before['schema'] == after['schema']
    assert not [row for row in changes if row['economic']], 'UNEXPLAINED_ECONOMIC_CHANGE'
    return {'economic_storage_exact': True}


CORRECTION_TEXT = 'CLOSEOUT synthetic administrative wording correction only'


def heartbeat_gate(before, after, changes):
    no_economics(before, after, changes)
    seen = set()
    for row in changes:
        if row['table'] in {'ydental_patient_mutex', 'ydental_supply_mutex', 'ydental_intake_mutex', 'ydental_queue_mutex'}:
            assert row['physical_key'][2] == 1 and row['columns'] == ['ydental_revision']
            assert row['after'][0]['ydental_revision'] == row['before'][0]['ydental_revision'] + 1
            seen.add(row['table'])
        else:
            assert row['table'] == 'ydental_clinical_document' and row['physical_key'][2] == 1
            assert set(row['columns']) <= {'ydental_editor_expires', 'write_uid', 'write_date'}
            assert row['after'][0]['write_uid'] == 7
    assert len(seen) == 4
    return {'normal_editor_heartbeat_only': True, 'zero_new_versions_or_economic_events': True}


def document_gate(action, uid, document_id, session_id):
    def check(before, after, changes):
        no_economics(before, after, changes)
        expected_event = {'acquire': 'clinical.edit_acquire', 'confirm': 'clinical.confirm',
                          'correct': 'clinical.correct', 'release': 'clinical.edit_release'}[action]
        editor = {'ydental_editor_id', 'ydental_session_id', 'ydental_session_revision', 'ydental_connection_hash',
                  'ydental_editor_hash', 'ydental_editor_expires', 'ydental_editor_lease_id', 'write_date', 'write_uid'}
        allowed_doc = editor if action in {'acquire', 'release'} else {
            'ydental_content', 'ydental_version', 'ydental_saved_at', 'state', 'write_date', 'write_uid'}
        mutexes = {'ydental_patient_mutex', 'ydental_supply_mutex', 'ydental_intake_mutex', 'ydental_queue_mutex'}
        old_doc = next(row for row in before['tables']['ydental_clinical_document'] if row['id'] == document_id)
        new_doc = next(row for row in after['tables']['ydental_clinical_document'] if row['id'] == document_id)
        expected_content = dict(old_doc['ydental_content'])
        if action == 'correct':
            expected_content['chief_complaint'] = CORRECTION_TEXT
        assert new_doc['ydental_content'] == expected_content
        assert new_doc['ydental_version'] == old_doc['ydental_version'] + int(action in {'confirm', 'correct'})
        if action in {'confirm', 'correct'}:
            assert new_doc['state'] == 'confirmed'
        elif action == 'acquire':
            assert new_doc['ydental_editor_id'] == uid and new_doc['ydental_session_id'] == session_id
            assert new_doc['ydental_editor_hash'] and new_doc['ydental_connection_hash'] and new_doc['ydental_editor_expires']
        else:
            assert not any(new_doc[field] for field in editor - {'write_date', 'write_uid'})
        seen = set(); audit_count = 0; version_count = 0
        for row in changes:
            table = row['table']
            if table in mutexes:
                assert row['physical_key'][2] == 1 and row['columns'] == ['ydental_revision']
                assert row['after'][0]['ydental_revision'] == row['before'][0]['ydental_revision'] + 1
                seen.add(table)
            elif table == 'ydental_clinical_document':
                assert row['physical_key'][2] == document_id and set(row['columns']) <= allowed_doc
                assert row['after'][0]['write_uid'] == uid
            elif table == 'ydental_clinical_version':
                assert action in {'confirm', 'correct'} and row['before_count'] == 0 and row['after_count'] == 1
                version = row['after'][0]
                assert version['ydental_document_id'] == document_id and version['ydental_author_id'] == uid
                assert version['ydental_kind'] == action and version['ydental_content'] == expected_content
                assert version['ydental_number'] == new_doc['ydental_version']
                assert version['ydental_store_id'] == old_doc['ydental_store_id'] and version['ydental_patient_id'] == old_doc['ydental_patient_id']
                prior = max((v for v in before['tables']['ydental_clinical_version'] if v['ydental_document_id'] == document_id),
                            key=lambda v: v['ydental_number'])
                assert version['ydental_previous_id'] == prior['id'] and version['ydental_template'] == old_doc['ydental_template']
                if action == 'correct': assert version['ydental_reason'] == 'CLOSEOUT wording only, no economic action'
                version_count += 1
            elif table == 'ydental_access_audit':
                assert row['before_count'] == 0 and row['after_count'] == 1
                audit = row['after'][0]
                assert audit['ydental_event'] == expected_event and audit['ydental_target_id'] == document_id
                assert audit['ydental_user_id'] == uid and audit['ydental_store_id'] == 1
                audit_count += 1
            else:
                raise AssertionError(('UNEXPECTED_DOCUMENT_FIELD', table, row['columns']))
        assert seen == mutexes and audit_count == 1
        assert version_count == (1 if action in {'confirm', 'correct'} else 0)
        return {'all_economic_stored_facts_exact': True, 'mutex_exact_records_delta': {t + ':1': 1 for t in sorted(seen)},
                'audit_event': expected_event, 'new_versions': version_count}
    return check


def native_effects(cr):
    effects = []
    for callback in cr.postcommit._funcs:
        if getattr(callback, '__name__', '') != 'increase_partner_rank':
            continue
        assert callback.__code__.co_filename.endswith('/addons/account/models/partner.py')
        closure = dict(zip(callback.__code__.co_freevars, (cell.cell_contents for cell in callback.__closure__)))
        for ident, delta in closure['data'].items():
            effects.append({'id': ident, 'field': closure['field'], 'delta': delta, 'actor': closure['self'].env.uid})
    return effects


def committed_gate(effects):
    def check(before, after, changes):
        no_economics(before, after, changes)
        by_id = {}
        for effect in effects:
            group = by_id.setdefault(effect['id'], [])
            group.append(effect)
        for row in changes:
            if row['table'] == 'res_partner':
                group = by_id[row['physical_key'][2]]
                names = {effect['field'] for effect in group}
                assert names <= {'customer_rank', 'supplier_rank'}
                assert set(row['columns']) <= names | {'write_uid', 'write_date'}
                for name in names:
                    assert row['after'][0][name] == row['before'][0][name] + sum(e['delta'] for e in group if e['field'] == name)
                assert row['after'][0]['write_uid'] in {e['actor'] for e in group}
            elif row['table'].startswith('orm_signaling_'):
                assert row['before_count'] == 0 and row['after_count'] == 1
                assert set(row['after'][0]) == {'id', 'date', '__physical_table__', '__physical_oid__'}
            else:
                raise AssertionError(('COMMIT_READBACK_DRIFT', row['table'], row['columns']))
        for ident, group in by_id.items():
            a = next(row for row in before['tables']['res_partner'] if row['id'] == ident)
            b = next(row for row in after['tables']['res_partner'] if row['id'] == ident)
            for name in {e['field'] for e in group}:
                assert b[name] == a[name] + sum(e['delta'] for e in group if e['field'] == name)
        return {'exact_storage_except_captured_native_rank_and_append_signals': True, 'native_effects': effects}
    return check


def verify_facts(env):
    assert not any(env._field_dirty.values()), 'ACTOR_MUST_FLUSH_BEFORE_READONLY_FACT_CHECK'
    for move in env['account.move'].search([('state', '=', 'posted')]):
        assert move.company_id.currency_id.is_zero(sum(move.line_ids.mapped('balance')))
    for source in env['ydental.settlement.source'].search([]):
        fee, event, invoice = source.ydental_fee_id, source.ydental_fee_id.ydental_event_id, source.ydental_invoice_id
        assert source.ydental_store_id == fee.ydental_store_id == event.ydental_store_id
        assert source.ydental_patient_id == fee.ydental_patient_id == event.ydental_patient_id
        assert invoice.state == 'posted' and invoice.company_id == source.ydental_store_id.company_id
    for original in env['ydental.settlement.bill.original'].search([]):
        attachment = original.attachment_id
        assert c.sha(attachment.raw.content) == original.pdf_sha256 and not attachment.public and not attachment.access_token


def checkpoint(cr, root, label, marker=None):
    if c.current_freeze()['round']:
        label = 'r1-' + label
    verify_facts(root)
    effects = native_effects(cr)
    before = snapshot(root)
    c.save(c.PRIVATE / (label + '-precommit.json'), before)
    c.save(c.PRIVATE / (label + '-native-effects.json'), effects)
    if marker:
        c.save(c.PRIVATE / (label + '-pending-not-success.json'), marker)
    c.event('commit_intent', label=label)
    try:
        cr.commit()
    except BaseException as error:
        failure_evidence(label, 'commit_unknown', error, {'precommit_saved': True})
        c.event('commit_unknown', label=label, error=type(error).__name__)
        c.stop('UNKNOWN_COMMIT_RESULT')
        try: c.readonly(label + '-unknown-tail')
        except BaseException as secondary:
            failure_evidence(label + '-secondary', 'unknown_commit_tail_unavailable', secondary)
        raise
    c.event('commit_returned', label=label)
    after = c.readonly(label + '-committed')
    c.persist(label + '-readback', before, after, committed_gate(effects))
    if marker:
        for path, value in marker.items():
            c.save(c.RUN / path, value | {'database': c.NAME, 'oid': after['oid'], 'verified_checkpoint': label})
    c.save(c.OUT / (label + '-checkpoint.json'), {'commit_returned': True, 'independent_RO_RR': True,
                                               'marker_after_readback': sorted(marker or {}), 'native_effects': effects})
    root.invalidate_all()


def verify_loaded(root):
    specs = [('ydental.clinical.service', '_operate'), ('ydental.clinical.service', '_acquire'),
             ('ydental.clinical.service', '_append'), ('ydental.queue.service', '_locks'),
             ('ydental.intake.service', '_all_locks'), ('ydental.settlement.service', '_original_invoice'),
             ('ydental.settlement.service', '_bill_original_bytes'), ('ydental.settlement.service', '_refund_execute'),
             ('ir.binary', '_find_record')]
    evidence = []
    for model, name in specs:
        code = root[model].__getattribute__(name).__func__.__code__
        source = Path(code.co_filename)
        assert source.resolve().is_relative_to(c.ROOT), 'CUSTOM_ADDON_LOADED_FROM_WRONG_SOURCE'
        compiled = compile(source.read_bytes(), str(source), 'exec', dont_inherit=True)
        def find(parent):
            for value in parent.co_consts:
                if isinstance(value, CodeType):
                    if value.co_name == name and value.co_firstlineno == code.co_firstlineno:
                        return value
                    found = find(value)
                    if found:
                        return found
            return None
        expected = find(compiled)
        evidence.append({'model': model, 'method': name, 'file': str(source.relative_to(c.CORE_ROOT)),
                         'source_sha256': c.sha(source.read_bytes()), 'loaded_code_equals_fixed_compile': code == expected})
    c.save(c.OUT / (os.environ['YDENTAL_CLOSEOUT_ACTION'] + '-loaded-source.json'), evidence)
    assert all(row['loaded_code_equals_fixed_compile'] for row in evidence), 'LOADED_SOURCE_IDENTITY_MISMATCH'
