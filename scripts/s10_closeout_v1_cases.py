"""A/B/C native layers and only the one explicitly permitted new T05 source."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from odoo import api, fields
from odoo.exceptions import AccessError
import s10_closeout_v1_contract as c
from s10_closeout_v1_runtime import bind, checkpoint, document_gate, key, no_economics, observe, snapshot, CORRECTION_TEXT, heartbeat_gate

def chain():
    return c.read(c.SOURCE_RUN / 'b-chain.json')

def actor_result(service, result):
    """Flush using the actual already-authorized actor, never set write_uid manually."""
    service.env.flush_all()
    return result

def new_T05_action(root, label, service, operation, payload):
    baseline = c.read(c.PRIVATE / 'clone-initial-RO.json')
    protected = {t: {row['id'] for row in rows if 'id' in row} for t, rows in baseline['tables'].items()}

    def decide(before, after, changes):
        for row in changes:
            if row['economic'] and row['before_count']:
                ident = row['physical_key'][2]
                assert ident not in protected.get(row['table'], set()), ('COPIED_ECONOMIC_ROW_CHANGED', row['table'], ident)
        return {'only_new_T05_economic_source_may_change': True, 'business_PASS': False, 'final_native_invariants_and_commit_readback_required': True}
    return observe(root, 'D-' + label, lambda: actor_result(service, service._operate(operation, payload, key())), decide, actor_env=service.env)

def inherited_identity(root):
    f = chain()
    doc = root['ydental.clinical.document'].browse(f['document_id'])
    invoice = root['account.move'].browse(f['invoice_id'])
    source = root['ydental.settlement.source'].search([('ydental_invoice_id', '=', invoice.id)])
    original = root['ydental.settlement.bill.original'].browse(1)
    assert doc.ydental_patient_id.id == f['patient_id'] and doc.ydental_execution_id.id == f['execution_id']
    assert doc.ydental_responsible_id.id == f['doctor_id'] == 7
    assert set(source.ydental_fee_id.ids) == set(f['fee_ids']) and source.ydental_patient_id == doc.ydental_patient_id
    assert invoice.state == 'posted' and invoice.amount_total == 740 and (invoice.amount_residual == 0)
    assert original.invoice_id == invoice and original.patient_id == doc.ydental_patient_id
    assert original.pdf_sha256 == '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'
    return (f, doc, invoice, original)

def sessions_gate(before, after, changes):
    no_economics(before, after, changes)
    for row in changes:
        assert row['table'] in {'ydental_access_session', 'ydental_access_audit'}
        assert row['before_count'] == 0 and row['after_count'] == 1
        if row['table'] == 'ydental_access_audit':
            assert row['after'][0]['ydental_event'] in {'login.scope', 'store.switch'}
    return {'new_bound_ordinary_sessions_only': True}

def A(cr, root):
    f, doc, invoice, original = inherited_identity(root)
    assert doc.state == 'pending' and doc.ydental_version == 2 and (not doc.ydental_editor_id)
    access = observe(root, 'fresh-owner-scope', lambda: bind(root, f['doctor_id'], f['store_id']), sessions_gate)
    checkpoint(cr, root, 'A-owner-scope')
    clinical = access.env['ydental.queue.service']._bind_connection(key()).env['ydental.clinical.service']
    session_id = access._scope().id
    held = observe(root, 'acquire', lambda: actor_result(clinical, clinical._operate('acquire', {'document_id': doc.id})), document_gate('acquire', f['doctor_id'], doc.id, session_id), actor_env=clinical.env)
    checkpoint(cr, root, 'A-acquire')
    observe(root, 'editor-heartbeat-before-confirm', lambda: actor_result(clinical, clinical._operate('heartbeat', {'document_id': doc.id, 'editor_token': held['editor_token']})), heartbeat_gate, actor_env=clinical.env)
    confirmed = observe(root, 'confirm', lambda: actor_result(clinical, clinical._operate('confirm', {'document_id': doc.id, 'editor_token': held['editor_token'], 'expected_version': held['version'], 'content': held['content'], 'key': key()})), document_gate('confirm', f['doctor_id'], doc.id, session_id), actor_env=clinical.env)
    checkpoint(cr, root, 'A-confirm')
    observe(root, 'editor-heartbeat-before-correct', lambda: actor_result(clinical, clinical._operate('heartbeat', {'document_id': doc.id, 'editor_token': held['editor_token']})), heartbeat_gate, actor_env=clinical.env)
    content = dict(confirmed['content'], chief_complaint=CORRECTION_TEXT)
    corrected = observe(root, 'correct', lambda: actor_result(clinical, clinical._operate('correct', {'document_id': doc.id, 'editor_token': held['editor_token'], 'expected_version': confirmed['version'], 'content': content, 'key': key(), 'reason': 'CLOSEOUT wording only, no economic action'})), document_gate('correct', f['doctor_id'], doc.id, session_id), actor_env=clinical.env)
    checkpoint(cr, root, 'A-correct')
    observe(root, 'editor-heartbeat-before-release', lambda: actor_result(clinical, clinical._operate('heartbeat', {'document_id': doc.id, 'editor_token': held['editor_token']})), heartbeat_gate, actor_env=clinical.env)
    observe(root, 'release', lambda: actor_result(clinical, clinical._operate('release', {'document_id': doc.id, 'editor_token': held['editor_token']})), document_gate('release', f['doctor_id'], doc.id, session_id), actor_env=clinical.env)
    checkpoint(cr, root, 'A-release', {'A.json': {'patient_id': f['patient_id'], 'document_id': doc.id, 'invoice_id': invoice.id, 'original_id': original.id, 'original_sha256': original.pdf_sha256, 'confirmed_version': confirmed['version'], 'corrected_version': corrected['version']}})

def B(cr, root):
    f, doc, invoice, original = inherited_identity(root)
    payment = root['ydental.settlement.payment'].browse(f['payment_first_id'])
    source = root['ydental.settlement.source'].search([('ydental_invoice_id', '=', invoice.id), ('ydental_fee_id', '=', f['fee_ids'][0])])
    audit = root['ydental.access.audit'].search([('ydental_event', '=', 'settlement.pay'), ('ydental_target_id', '=', payment.id), ('ydental_target_model', '=', payment._name)], limit=1)
    assert Decimal(str(payment.ydental_amount)) == Decimal(c.read(c.ROOT / 'docs/evidence/s10-p0-21/final-facts-summary.json')['payment_amounts'][0])
    assert source.ydental_original_amount == source.ydental_fee_id.ydental_amount and audit.ydental_target_model == payment._name
    checked = []
    for record, values in [(source, {'ydental_original_amount': 1}), (payment, {'ydental_amount': 1}), (audit, {'ydental_reason': 'CLOSEOUT denied tampering'})]:
        for operation in ['write', 'unlink']:

            def call(record=record, values=values, operation=operation):
                try:
                    ordinary = record.with_user(f['manager_id'])
                    ordinary.write(values) if operation == 'write' else ordinary.unlink()
                except AccessError:
                    return True
                return False
            result = observe(root, record._name + '-' + operation, call, c.exact)
            assert result, 'ORDINARY_TAMPERING_ACCEPTED'
            checked.append({'layer': 'MODEL', 'model': record._name, 'id': record.id, 'operation': operation, 'denied': result})
    checkpoint(cr, root, 'B-six-denials')
    c.save(c.RUN / 'B-rpc-targets.json', {'targets': [{'model': rec._name, 'id': rec.id, 'values': values} for rec, values in [(source, {'ydental_original_amount': 1}), (payment, {'ydental_amount': 1}), (audit, {'ydental_reason': 'denied closeout tampering'})]]})
    c.save(c.OUT / 'B-six-model-denials.json', {'actual_first_payment_amount': payment.ydental_amount, 'checks': checked, 'real_RPC_claimed': False})

class Proxy:

    def __init__(self, record, **values):
        self.record, self.values = (record, values)

    def __getattr__(self, name):
        return self.values[name] if name in self.values else getattr(self.record, name)

class RollbackFixture(Exception):
    pass

def rollback_case(root, label, call, expected):
    before = snapshot(root)
    try:
        with root.cr.savepoint():
            try:
                value, error = (call(), None)
            except BaseException as caught:
                value, error = (None, caught)
            after = snapshot(root)
            if isinstance(value, tuple) and value and isinstance(value[0], bytes):
                (c.PRIVATE / ('C-' + label + '-unexpected-returned-bytes.bin')).write_bytes(value[0])
                c.save(c.OUT / ('C-' + label + '-unexpected-return-metadata.json'), {'bytes': len(value[0]), 'sha256': c.sha(value[0]), 'expected': expected})

            def decide(a, b, changes):
                assert error is None if expected == 'allow' else isinstance(error, AccessError), (label, type(error).__name__)
                if expected == 'allow':
                    assert value == '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'
                return {'layer': 'MODEL_WITH_ROLLBACK_FIXTURE', 'expected': expected, 'actual_error': type(error).__name__ if error else None, 'not_committed_financial_source': True}
            c.persist('C-' + label + '-inside-fixture', before, after, decide)
            raise RollbackFixture()
    except RollbackFixture:
        pass
    root.invalidate_all()
    c.persist('C-' + label + '-rollback', before, snapshot(root), c.exact)

def C(cr, root):
    f, doc, invoice, original = inherited_identity(root)
    access = bind(root, f['manager_id'], f['store_id'])
    service = access.env['ydental.settlement.service']
    sources = root['ydental.settlement.source'].search([('ydental_invoice_id', '=', invoice.id)], order='id')
    other_patient = root['ydental.patient'].browse(2)
    other_store = root['ydental.access.store'].browse(2)
    assert other_patient.exists() and other_patient != doc.ydental_patient_id
    assert other_store.company_id == invoice.company_id and other_store != sources[0].ydental_store_id
    cls = type(service)
    original_invoice = cls._invoice
    original_model = cls._model

    def cross_company():
        trade = c.read(c.SOURCE_RUN / 'trade.json')
        uid, sid = (trade['manager_id'], trade['target_store_id'])
        target = root['ydental.access.store'].browse(sid)
        assert target.company_id != invoice.company_id
        admin = bind(root, uid, sid).with_company(target.company_id)
        actor_result(admin, admin._grant(uid, sid, {'export': 'write'}))
        return admin.env['ydental.settlement.service']._bill_original_bytes(original.id)

    def wrong_store():
        other = bind(root, f['manager_id'], other_store.id)
        actor_result(other, other._grant(f['manager_id'], other_store.id, {'settlement': 'read'}))
        other._check('settlement', 'read')
        other._check('export', 'write')
        return other.env['ydental.settlement.service']._bill_original_bytes(original.id)
    rollback_case(root, 'actual-existing-wrong-store', wrong_store, 'deny')
    rollback_case(root, 'actual-existing-cross-company', cross_company, 'deny')

    def wrong_patient():
        rows = [Proxy(row, ydental_patient_id=other_patient) if i == 1 else row for i, row in enumerate(sources)]
        with patch.object(cls, '_invoice', lambda self, invoice_id, store: (invoice, rows)):
            return service._bill_original_bytes(original.id)
    rollback_case(root, 'projected-existing-wrong-patient', wrong_patient, 'deny')

    def mixed_store():
        rows = [Proxy(row, ydental_store_id=other_store) if i == 1 else row for i, row in enumerate(sources)]

        class SourceSearch:

            def search(self, domain):
                return rows

        def model(self, name):
            return SourceSearch() if name == 'source' else original_model(self, name)
        with patch.object(cls, '_model', model):
            return service._bill_original_bytes(original.id)
    rollback_case(root, 'projected-existing-same-company-mixed-store', mixed_store, 'deny')

    def legal_alias():
        patients = access.env['ydental.patient.service']
        created = actor_result(patients, patients._operate('create', {'values': {'name': 'CLOSEOUT rollback alias identity'}}, key()))
        alias = root['ydental.patient'].browse(created['id'])
        request = actor_result(patients, patients._operate('request_merge', {'source_id': alias.id, 'target_id': doc.ydental_patient_id.id, 'reason': 'CLOSEOUT controlled same-family alias fixture'}, key()))
        merged = actor_result(patients, patients._operate('confirm', {'request_id': request['id'], 'version': request['version'], 'reason': 'CLOSEOUT verified rollback-only identity fixture'}, key()))
        assert merged['result'] == 'accepted' and alias.ydental_merged_into_id == doc.ydental_patient_id
        rows = [Proxy(row, ydental_patient_id=alias) if i == 0 else row for i, row in enumerate(sources)]
        with patch.object(cls, '_invoice', lambda self, invoice_id, store: (invoice, rows)):
            raw, digest = service._bill_original_bytes(original.id)
            assert c.sha(raw) == digest
            return digest
    rollback_case(root, 'legal-merged-alias-projected-historical-source', legal_alias, 'allow')
    checkpoint(cr, root, 'C-model-fixtures')
    c.save(c.OUT / 'C-model-layer-summary.json', {'actual_cross_company_existing_source': True, 'wrong_patient_and_mixed_store': 'controlled source projections with actual existing IDs; no posted/original DML', 'alias': 'normal patient create/request/confirm plus projected historical alias source, all rolled back', 'all_fixture_rowsets_restored': True, 'RPC_and_HTTP': 'separate Web matrix, not these model calls'})

def prepare(cr, root):
    from odoo.tools.misc import limited_field_access_token, verify_limited_field_access_token
    from odoo.tools.image import image_process, image_guess_size_from_field_name
    f, doc, invoice, original = inherited_identity(root)
    access = bind(root, f['manager_id'], f['store_id'])
    initial_levels = access._levels(access._membership(f['reader_id'], f['store_id']))
    assert initial_levels['settlement'] == 'none' and initial_levels['export'] == 'write'
    c.save(c.PRIVATE / 'C-reader-initial-levels.json', initial_levels)
    actor_result(access, access._grant(f['reader_id'], f['store_id'], {'settlement': 'read'}))
    access.env.flush_all()
    old_reader = bind(root, f['reader_id'], f['store_id'])

    def old_binding_denied():
        actor_result(access, access._grant(f['reader_id'], f['store_id'], {'export': 'none'}))
        access.env.flush_all()
        return old_reader.env['ydental.settlement.service']._bill_original_bytes(original.id)
    rollback_case(root, 'old-binding-live-revocation', old_binding_denied, 'deny')
    attachment = original.attachment_id
    token = limited_field_access_token(attachment, 'raw', scope='binary')
    assert verify_limited_field_access_token(attachment, 'raw', token, scope='binary')
    raw = (c.CORE_ROOT / 'addons/web/static/img/placeholder.png').read_bytes()
    width, height = image_guess_size_from_field_name('raw')
    expected = image_process(raw, size=(width, height), crop=False)
    (c.PRIVATE / 'expected-native-placeholder.png').write_bytes(expected)
    login_reader = root['res.users'].browse(f['reader_id']).login
    c.save(c.PRIVATE / 'Web-secret.json', {'valid_raw_limited_token': token, 'reader_login': login_reader, 'manager_login': f['manager_login'], 'password': 's05-test-password', 'reader_id': f['reader_id'], 'frontdesk_login': f['frontdesk_login'], 'attachment_id': attachment.id, 'original_id': original.id, 'store_id': f['store_id'], 'invoice_id': invoice.id, 'original_sha256': original.pdf_sha256})
    checkpoint(cr, root, 'C-Web-preparation')
    c.save(c.OUT / 'valid-token-construction.json', {'fixed_source': 'odoo/tools/misc.py:1877-1934', 'scope': 'binary', 'field': 'raw', 'attachment_id': attachment.id, 'cryptographically_valid': True, 'stored_access_token_unchanged': not attachment.access_token, 'token_private_only': True, 'placeholder_core_sha256': c.sha(raw), 'native_expected_sha256': c.sha(expected), 'native_size': [width, height]})

def revoke(cr, root):
    f = chain()
    access = bind(root, f['manager_id'], f['store_id'])
    actor_result(access, access._grant(f['reader_id'], f['store_id'], {'export': 'none'}))
    access.env.flush_all()
    checkpoint(cr, root, 'C-live-export-revoked')

def T05_setup(cr, root):
    D_admission(cr, root)
    f, _doc, _invoice, _original = inherited_identity(root)
    manager = bind(root, f['manager_id'], f['store_id'])
    front = bind(root, f['frontdesk_id'], f['store_id'])
    doctor = bind(root, f['doctor_id'], f['store_id']).env['ydental.queue.service']._bind_connection(key())
    intake, supply = (manager.env['ydental.intake.service'], manager.env['ydental.supply.service'])
    catalog0 = root['ydental.intake.catalog'].browse(1)
    old_mapping = root['ydental.intake.mapping'].search([('ydental_catalog_id', '=', catalog0.id), ('ydental_store_id', '=', f['store_id'])], limit=1)
    area = old_mapping.ydental_area_id
    station = root['ydental.space.station'].search([('ydental_area_id', '=', area.id), ('active', '=', True)], order='id', limit=1)
    catalog = actor_result(intake, intake._operate('catalog', {'code': 'CLOSEOUT-T05-' + key(), 'name': 'CLOSEOUT-T05 independent six', 'kind': 'care', 'capability_id': catalog0.ydental_capability_id.id, 'uom_id': catalog0.ydental_product_id.uom_id.id}, key()))
    mapping = actor_result(intake, intake._operate('mapping', {'catalog_id': catalog['id'], 'area_id': area.id, 'execution_area_id': area.id}, key()))
    price = actor_result(intake, intake._operate('price', {'catalog_id': catalog['id'], 'currency_id': root.company.currency_id.id, 'unit_price': 6, 'start': fields.Datetime.to_string(fields.Datetime.now() - timedelta(minutes=1)), 'end': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=1)), 'reason': 'CLOSEOUT-T05 six-unit synthetic policy'}, key()))
    review = actor_result(intake, intake._operate('review', {'record_id': price['id'], 'version': price['version'], 'reason': 'CLOSEOUT-T05 reviewed'}, key()))
    actor_result(intake, intake._operate('publish', {'record_id': review['id'], 'version': review['version'], 'reason': 'CLOSEOUT-T05 published'}, key()))
    start = fields.Datetime.now().replace(microsecond=0) + timedelta(minutes=5)
    end = start + timedelta(minutes=5)
    slot = actor_result(supply, supply._operate('slot', {'station_id': station.id, 'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(end), 'total': 3, 'capability_ids': [catalog0.ydental_capability_id.id], 'reason': 'CLOSEOUT-T05 unique new qualification'}, key()))
    slot_record = root['ydental.supply.slot'].browse(slot['id'])
    actor_result(supply, supply._operate('publish', {'id': slot_record.id, 'version': slot_record.ydental_version, 'user_ids': [f['manager_id']], 'reason': 'CLOSEOUT-T05 legitimate synthetic capacity'}, key()))
    patient = actor_result(front.env['ydental.patient.service'], front.env['ydental.patient.service']._operate('create', {'values': {'name': 'CLOSEOUT-T05 independent synthetic patient'}}, key()))
    qualification = actor_result(front.env['ydental.intake.service'], front.env['ydental.intake.service']._operate('reserve', {'patient_id': patient['id'], 'mapping_id': mapping['id'], 'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(end), 'channel': 'reservation'}, key()))
    actor_result(front.env['ydental.intake.service'], front.env['ydental.intake.service']._operate('arrive', {'patient_id': patient['id']}, key()))
    task = root['ydental.intake.task'].browse(qualification['task_id'])
    actor_result(front.env['ydental.intake.service'], front.env['ydental.intake.service']._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key()))
    lease = actor_result(doctor, doctor._operate('enter', {'station_id': station.id}))
    called = actor_result(doctor, doctor._operate('call', {'lease_id': lease['lease_id'], 'token': lease['token']}))
    assert called['task_id'] == task.id
    execution = actor_result(doctor, doctor._operate('start', {'lease_id': lease['lease_id'], 'token': lease['token'], 'entry_id': called['entry_id']}))
    clinical = doctor.env['ydental.clinical.service']
    document = actor_result(clinical, clinical._operate('open', {'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'], 'lease_token': lease['token']}))
    content = dict(document['content'], chief_complaint='CLOSEOUT-T05 new six-unit synthetic source')
    saved = actor_result(clinical, clinical._operate('save', {'document_id': document['document_id'], 'editor_token': document['editor_token'], 'expected_version': document['version'], 'content': content, 'key': key()}))
    event = new_T05_action(root, 'one-new-event', doctor.env['ydental.treatment.service'], 'execute', {'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'document_id': document['document_id'], 'document_version': saved['version'], 'catalog_id': catalog['id'], 'quantity': 1, 'source': 'CLOSEOUT-T05-' + key(), 'reason': 'CLOSEOUT-T05 one genuine new synthetic event', 'materials': [], 'teeth': [], 'already_performed': False, 'policy': 'demo_confirmation'})
    assert event['amount'] == 6
    actor_result(clinical, clinical._operate('handover', {'document_id': document['document_id'], 'editor_token': document['editor_token'], 'expected_version': saved['version'], 'content': content, 'key': key(), 'lease_id': lease['lease_id'], 'lease_token': lease['token']}))
    service = manager.env['ydental.settlement.service']
    bill = new_T05_action(root, 'one-new-bill', service, 'bill', {'fee_ids': [event['fee_id']], 'discount': 0, 'reason': ''})
    payment = new_T05_action(root, 'one-new-receipt', service, 'pay', {'invoice_ids': [bill['invoice_id']], 'amount': 6, 'channel': 'cash', 'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'CLOSEOUT-T05 independent actual synthetic six'})
    request = new_T05_action(root, 'one-new-refund-request', service, 'refund_request', {'payment_id': payment['payment_id'], 'amount': 2, 'reason': 'CLOSEOUT-T05 one synthetic two-unit refund', 'request_key': key()})
    new_T05_action(root, 'distinct-approve', front.env['ydental.settlement.service'], 'refund_approve', {'refund_id': request['refund_id'], 'reason': 'CLOSEOUT-T05 distinct authorized approval'})
    marker = {'patient_id': patient['id'], 'event_id': event['event_id'], 'fee_id': event['fee_id'], 'invoice_id': bill['invoice_id'], 'payment_id': payment['payment_id'], 'refund_id': request['refund_id'], 'execute_key': key(), 'amount_received': 6, 'refund_amount': 2, 'actor_uid': f['manager_id'], 'approver_uid': f['frontdesk_id']}
    checkpoint(cr, root, 'D-new-source', {'T05.json': marker})

def T05_recover(cr, root):
    f = chain()
    marker = c.read(c.RUN / 'T05.json')
    manager = bind(root, f['manager_id'], f['store_id']).env['ydental.settlement.service']
    approver = bind(root, f['frontdesk_id'], f['store_id']).env['ydental.settlement.service']
    refund = root['ydental.settlement.refund'].browse(marker['refund_id'])
    failed = new_T05_action(root, 'mark-native-failed', manager, 'refund_uncertain', {'refund_id': refund.id, 'outcome': 'failed', 'reason': 'CLOSEOUT-T05 verified demonstration transfer failed before payment'})
    assert failed['state'] == 'failed' and (not refund.ydental_native_payment_id) and (not refund.ydental_credit_note_id)
    checkpoint(cr, root, 'D-failed-verified-unpaid')
    result = new_T05_action(root, 'verified-unpaid-recover', approver, 'refund_recover', {'refund_id': refund.id, 'verified_not_paid': True, 'reason': 'CLOSEOUT-T05 independent verification: no native or offline payout'})
    assert result['state'] == 'approved' and (not refund.ydental_native_payment_id) and (not refund.ydental_credit_note_id)
    checkpoint(cr, root, 'D-recovered')
    c.save(c.OUT / 'D-failed-recovered-model.json', {'layer': 'MODEL_NATIVE_COMMITTED', 'refund_id': refund.id, 'failed_then_verified_unpaid_then_approved': True, 'actually_refunded_before_HTTP': 0, 'not_a_transport_failure_label': True})

def D_admission(cr, root):
    """Before any D upstream action: current identity, live permissions and all-channel locks."""
    f = chain()
    manager = bind(root, f['manager_id'], f['store_id'])
    front = bind(root, f['frontdesk_id'], f['store_id'])
    doctor = bind(root, f['doctor_id'], f['store_id'])
    store = root['ydental.access.store'].browse(f['store_id'])
    before = snapshot(root)
    roles = []
    now = datetime.now(timezone.utc)
    for actor, cats in [(manager, ['settlement', 'finance_approval', 'patient', 'price', 'capacity']), (front, ['settlement', 'finance_approval', 'frontdesk']), (doctor, ['medical'])]:
        member = actor._membership(actor.env.uid, store.id)
        assert member and member.active and member.ydental_employee_id.active
        assert store.company_id in actor.env.user.company_ids
        for cat in cats:
            actor._check(cat, 'write', write=True)
        roles.append({'uid': actor.env.uid, 'employee_id': member.ydental_employee_id.id, 'company_id': store.company_id.id, 'store_id': store.id, 'levels': actor._levels(member)})
    assert manager.env.uid != front.env.uid
    for actor in [manager, front]:
        service = actor.env['ydental.settlement.service']
        service._config(store)
        day = service._local_date(store, now)
        service._close_guard_any(store, actor.env.uid, day)
        service._close_guard(store, actor.env.uid, day, 'cash')
    fact = {'roles': roles, 'UTC_observed': now.isoformat(), 'business_date': str(day), 'store_timezone': store.ydental_timezone, 'channel': 'cash', 'all_channels_guard_passed': True, 'old_closes': before['tables']['ydental_settlement_close'], 'new_identity_or_D_permission_expansion': False, 'old_close_unlock_or_date_faking': False}
    c.save(c.PRIVATE / 'D-admission-full.json', fact)
    c.save(c.OUT / 'D-admission.json', {k: v for k, v in fact.items() if k != 'old_closes'})
    checkpoint(cr, root, 'D-pre-upstream-admission')

def restore(cr, root):
    f = chain()
    access = bind(root, f['manager_id'], f['store_id'])
    before = snapshot(root)
    actor_result(access, access._grant(f['reader_id'], f['store_id'], {'settlement': 'none', 'export': 'write'}))
    access.env.flush_all()
    member = access._membership(f['reader_id'], f['store_id'])
    assert access._levels(member) == c.read(c.PRIVATE / 'C-reader-initial-levels.json')
    bound = bind(root, f['reader_id'], f['store_id'])
    try:
        bound.env['ydental.settlement.service']._bill_original_bytes(1)
    except AccessError:
        pass
    else:
        raise AssertionError('READ_NONE_EXPORT_WRITE_NOT_DENIED')
    after = snapshot(root)
    c.persist('C-restored-permissions', before, after, no_economics)
    checkpoint(cr, root, 'C-permissions-restored')
    c.save(c.OUT / 'C-permission-restore.json', {'current_read_none_export_write_denied_MODEL': True, 'all_original_reader_levels_restored': True})

def run(registry, action):
    with registry.cursor() as cr:
        root = api.Environment(cr, 1, {})
        if action == 'prepare-all':
            A(cr, root)
            B(cr, root)
            C(cr, root)
            prepare(cr, root)
            T05_setup(cr, root)
            T05_recover(cr, root)
        elif action == 'revoke':
            revoke(cr, root)
        elif action == 'restore':
            restore(cr, root)
        else:
            raise AssertionError('UNKNOWN_NATIVE_ACTION')
