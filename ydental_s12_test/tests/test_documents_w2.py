import base64
import hashlib
from unittest.mock import patch

from odoo import Command
from odoo.addons.base.tests.common import BaseCommon
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.ydental_treatment_test.tests.common import bind, handover_args, key, save_args, serving
from odoo.addons.ydental_treatment_test.tests.treatment_common import opened_actual, setup


@tagged('post_install', '-at_install')
class TestDocumentsW2(BaseCommon):
    """MODEL transactions with actual PDF bytes; no real signatures or printers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        demo_supply = patch.object(type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        demo_supply.start()
        cls.addClassCleanup(demo_supply.stop)
        root = cls.env['base'].sudo().env
        root.ref('base.group_user').write({'implied_ids': [
            Command.link(root.ref('stock.group_stock_multi_warehouses').id),
            Command.link(root.ref('stock.group_stock_multi_locations').id),
        ]})
        setup(cls)

    def _source(self, confirmed=True):
        self.treatment, self.clinical, self.queue, self.lease, self.execution, self.document, self.args = opened_actual(self)
        if confirmed:
            self.document.update(self.clinical._operate('confirm', save_args(self.document, 'S12 W2 synthetic confirmed source')))
        self.printing = self.clinical.env['ydental.print.service'].with_context(lang='en_US')
        return {'kind': 'clinical', 'source_id': self.document['document_id'], 'version': self.document['version']}

    def _generate(self, selection, previous_id=None):
        preview = self.printing._original_operate('preview', selection)
        arguments = selection | {'expected_digest': preview['source_digest'], 'key': key(), 'previous_id': previous_id}
        generated = self.printing._original_operate('generate', arguments)
        raw, checksum = self.printing._original_operate('download', {'original_id': generated['original_id']})
        self.assertTrue(raw.startswith(b'%PDF-'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), checksum)
        self.assertEqual(checksum, generated['sha256'])
        return generated, raw, arguments

    def _template(self, kind='consent', manager=None, **values):
        manager = manager if manager is not None else bind(self, self.users['manager']).env['ydental.print.service']
        created = manager._original_operate('template_create', {
            'name': 'S12 W2 synthetic test content', 'kind': kind, 'version': key(),
            'body': 'SYNTHETIC SOFTWARE TEST CONTENT. No real clinical consent, signature or approval.',
            'applicability': 'Explicit synthetic software fixture only', 'synthetic': True} | values)
        for action in ('review', 'publish'):
            manager._original_operate('template_review', {'template_id': created['template_id'], 'action': action})
        return created['template_id']

    def _upload(self, original_id, raw):
        return self.printing._original_operate('consent_upload', {
            'original_id': original_id, 'filename': 'synthetic-software-evidence-not-a-signature.pdf',
            'content': base64.b64encode(raw).decode('ascii')})

    def _business_counts(self):
        return {name: self.root[name].search_count([]) for name in (
            'ydental.treatment.event', 'ydental.treatment.fee', 'stock.move', 'account.move', 'account.payment')}

    def test_consent_generation_upload_and_verification_are_separate_facts(self):
        selection = self._source() | {'kind': 'consent'}
        before = self._business_counts()
        generated, raw, _arguments = self._generate(selection)
        self.assertFalse(self.root['ydental.consent.evidence'].search_count([
            ('original_id', '=', generated['original_id'])]))
        evidence = self._upload(generated['original_id'], raw)
        stored = self.root['ydental.consent.evidence'].browse(evidence['evidence_id'])
        self.assertEqual(stored.state, 'pending')
        self.assertFalse(stored.verified_by_id)
        self.assertFalse(stored.verified_at)
        self.assertTrue(stored.synthetic)
        returned, checksum = self.printing._original_operate('consent_download', {'evidence_id': stored.id})
        self.assertEqual(returned, raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), checksum)
        accepted = self.printing._original_operate('consent_verify', {
            'evidence_id': stored.id, 'conclusion': 'verified',
            'reason': 'Synthetic verification branch only; this fixture is not a real signature'})
        self.assertEqual(accepted['state'], 'verified')
        self.assertTrue(accepted['synthetic'])
        self.assertEqual(stored.verified_by_id, self.users['doctor'])
        self.assertTrue(stored.verified_at)
        self.assertEqual(stored.template_sha256, stored.original_id.template_sha256)
        duplicate = self._upload(generated['original_id'], raw)
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(duplicate['evidence_id'], stored.id)
        self.assertEqual(duplicate['state'], 'verified')
        with self.assertRaises(UserError):
            self.printing._original_operate('consent_verify', {
                'evidence_id': stored.id, 'conclusion': 'rejected', 'reason': 'Cannot replace an original conclusion'})
        next_original, _next_raw, _arguments = self._generate(selection, previous_id=generated['original_id'])
        with self.assertRaises(UserError):
            self._upload(next_original['original_id'], raw)
        self.assertEqual(self._business_counts(), before)

    def test_consent_rejection_preserves_upload_and_live_permissions(self):
        selection = self._source() | {'kind': 'consent'}
        generated, raw, _arguments = self._generate(selection)
        evidence = self._upload(generated['original_id'], raw)
        rejected = self.printing._original_operate('consent_verify', {
            'evidence_id': evidence['evidence_id'], 'conclusion': 'rejected',
            'reason': 'Synthetic evidence fails the review criteria'})
        self.assertEqual(rejected['state'], 'rejected')
        actual, _checksum = self.printing._original_operate('consent_download', {'evidence_id': evidence['evidence_id']})
        self.assertEqual(actual, raw)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'export': 'write'})
        with self.assertRaises(AccessError):
            self.printing._original_operate('consent_download', {'evidence_id': evidence['evidence_id']})

    def test_consent_old_version_requires_explicit_published_store_policy(self):
        selection = self._source() | {'kind': 'consent'}
        template_one = self._template()
        generated, raw, _arguments = self._generate(selection | {'template_id': template_one})
        evidence = self._upload(generated['original_id'], raw)
        self.printing._original_operate('consent_verify', {
            'evidence_id': evidence['evidence_id'], 'conclusion': 'verified',
            'reason': 'Explicit synthetic software verification only'})
        template_two = self._template()
        status = self.printing._original_operate('consent_status', {'patient_id': self.execution.ydental_patient_id.id})
        self.assertEqual(next(row for row in status if row['template_id'] == template_two)['status'],
                         'awaiting_current_store_version_verification')
        template_three = self._template(accepted_previous_template_ids=[template_one])
        status = self.printing._original_operate('consent_status', {'patient_id': self.execution.ydental_patient_id.id})
        accepted = next(row for row in status if row['template_id'] == template_three)
        self.assertEqual(accepted['status'], 'verified_under_current_published_policy')
        self.assertEqual(accepted['evidence_ids'], [evidence['evidence_id']])
        other = bind(self, self.users['manager'], self.stores[1])
        other.env['ydental.patient.service']._operate('relation', {
            'patient_id': self.execution.ydental_patient_id.id}, key())
        other_printing = other.env['ydental.print.service']
        missing = other_printing._original_operate('consent_status', {'patient_id': self.execution.ydental_patient_id.id})
        self.assertEqual(missing[0]['status'], 'policy_missing_review_required')
        other_template = self._template(manager=other_printing)
        other_status = other_printing._original_operate('consent_status', {'patient_id': self.execution.ydental_patient_id.id})
        current = next(row for row in other_status if row['template_id'] == other_template)
        self.assertEqual(current['status'], 'awaiting_current_store_version_verification')
        self.assertFalse(current['evidence_ids'])
        with self.assertRaises(AccessError):
            other_printing._original_operate('consent_verify', {
                'evidence_id': evidence['evidence_id'], 'conclusion': 'verified',
                'reason': 'Other store must not inherit or reverify this original'})

    def _mixed_collection(self):
        self._source(confirmed=False)
        handed = self.clinical._operate('handover', handover_args(
            self.document, self.lease, 'D1_PENDING_KEEP_UNCONFIRMED'))
        task = self.root['ydental.intake.task'].browse(handed['continuation_task_id'])
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        queue_two, lease_two, execution_two = serving(self, self.second, self.other_station, task)
        clinical_two = queue_two.env['ydental.clinical.service']
        document_two = clinical_two._operate('open', {'execution_id': execution_two.id,
            'lease_id': lease_two['lease_id'], 'lease_token': lease_two['token']})
        document_two.update(clinical_two._operate('confirm', save_args(document_two, 'D2_CONFIRMED_TEXT')))
        return [self.document['document_id'], document_two['document_id']]

    def test_complete_collection_refuses_draft_and_links_after_normal_completion(self):
        document_ids = self._mixed_collection()
        before = self._business_counts()
        incomplete = self.printing._original_operate('select_clinical_sources', {'document_ids': document_ids, 'mode': 'complete'})
        selected = {name: incomplete[name] for name in ('kind', 'source_id', 'version')}
        with self.assertRaises(UserError) as rejected:
            self.printing._original_operate('preview', selected)
        self.assertIn(str(document_ids[0]), str(rejected.exception))
        draft = self.printing._original_operate('select_clinical_sources', {'document_ids': document_ids, 'mode': 'draft'})
        generated, raw, _arguments = self._generate({name: draft[name] for name in ('kind', 'source_id', 'version')})
        old_original = self.root['ydental.document.original'].browse(generated['original_id'])
        self.assertIn('Incomplete', old_original.source_facts['status'])
        self.assertEqual(len(old_original.source_facts['selected_sources']), 2)
        pending = self.clinical._operate('acquire', {'document_id': document_ids[0]})
        self.clinical._operate('confirm', save_args(pending, 'D1_NORMAL_COMPLETION_TEXT'))
        completed = self.printing._original_operate('select_clinical_sources', {'document_ids': document_ids, 'mode': 'complete'})
        new, _new_raw, _arguments = self._generate(
            {name: completed[name] for name in ('kind', 'source_id', 'version')}, previous_id=old_original.id)
        new_original = self.root['ydental.document.original'].browse(new['original_id'])
        self.assertEqual(new_original.previous_id, old_original)
        self.assertEqual(new_original.version, old_original.version + 1)
        self.assertNotEqual(new_original.source_id, old_original.source_id)
        self.assertEqual(new_original.source_facts['selection_scope_sha256'], old_original.source_facts['selection_scope_sha256'])
        old_again, checksum = self.printing._original_operate('download', {'original_id': old_original.id})
        self.assertEqual(old_again, raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), checksum)
        self.assertEqual(self._business_counts(), before)

    def test_excerpt_retains_exclusions_and_the_published_policy_snapshot(self):
        document_ids = self._mixed_collection()
        with self.assertRaises(UserError):
            self.printing._original_operate('select_clinical_sources', {'document_ids': document_ids, 'mode': 'excerpt'})
        disallowed = self._template(kind='clinical_summary', allow_excerpt=False)
        with self.assertRaises(UserError):
            self.printing._original_operate('select_clinical_sources', {
                'document_ids': document_ids, 'mode': 'excerpt', 'template_id': disallowed})
        policy = self._template(kind='clinical_summary', allow_excerpt=True)
        choice = self.printing._original_operate('select_clinical_sources', {
            'document_ids': document_ids, 'mode': 'excerpt', 'template_id': policy})
        selected = {name: choice[name] for name in ('kind', 'source_id', 'version')}
        preview = self.printing._original_operate('preview', selected)
        self.assertNotIn('D1_PENDING_KEEP_UNCONFIRMED', preview['html'])
        self.assertIn('D2_CONFIRMED_TEXT', preview['html'])
        self.assertIn('Not included', preview['html'])
        generated, _raw, _arguments = self._generate(selected)
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        self.assertEqual(original.template_id.id, policy)
        self.assertTrue(original.template_facts['allow_excerpt'])
        self.assertEqual(original.template_facts['state'], 'published')
        self.assertEqual(len(original.source_facts['selected_sources']), 2)
        self.assertFalse(original.source_facts['selected_sources'][0]['confirmed'])
        self.assertTrue(original.source_facts['selected_sources'][1]['confirmed'])
        with self.assertRaises(UserError):
            self.printing._original_operate('preview', selected | {'template_id': disallowed})

    def test_print_request_and_explicit_simulated_failure_do_not_claim_paper(self):
        selection = self._source()
        generated, raw, _arguments = self._generate(selection)
        before = self._business_counts()
        requested, checksum = self.printing._original_operate('print_request', {'original_id': generated['original_id']})
        self.assertEqual(requested, raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), checksum)
        audit = self.root['ydental.access.audit'].search([
            ('ydental_user_id', '=', self.users['doctor'].id), ('ydental_event', '=', 'document.print_request')], limit=1)
        self.assertTrue(audit)
        failure = self.printing._original_operate('print_failure', {'request_audit_id': audit.id,
            'reason': 'Controlled local simulation of a device error; no physical printer', 'simulated': True})
        self.assertEqual(failure['device_result'], 'simulated_device_failure')
        self.assertEqual(failure['paper_output'], 'unknown')
        self.assertTrue(failure['simulated'])
        failed_audit = self.root['ydental.access.audit'].browse(failure['audit_id'])
        self.assertEqual(failed_audit.ydental_after['request_audit_id'], audit.id)
        self.assertNotIn('paper_printed', failed_audit.ydental_after)
        with self.assertRaises(ValidationError):
            self.printing._original_operate('print_failure', {'request_audit_id': audit.id,
                'reason': 'Cannot represent an untested physical device result', 'simulated': False})
        other = bind(self, self.second).env['ydental.print.service']
        with self.assertRaises(AccessError):
            other._original_operate('print_failure', {'request_audit_id': audit.id,
                'reason': 'Another actor cannot alter the request history', 'simulated': True})
        self.assertEqual(self._business_counts(), before)

    def test_same_generation_key_recovers_after_prescription_version_changes(self):
        self._source(confirmed=False)
        lines = [{'mapping_id': self.drug_mapping.id, 'quantity': 6, 'uom_id': self.uom.id,
            'product_id': self.products['medicine'], 'specification': 'Synthetic specification',
            'usage': 'Synthetic usage', 'frequency': 'Synthetic frequency', 'course': 'Synthetic course'}]
        order = self.treatment._operate('order', self.args | {'kind': 'prescription',
            'purpose': 'Synthetic draft for result recovery', 'lines': lines}, key())
        selection = {'kind': 'prescription', 'source_id': order['order_id'], 'version': order['version']}
        generated, raw, arguments = self._generate(selection)
        before = self._business_counts()
        edited = self.treatment._operate('edit_order', self.args | {'order_id': order['order_id'],
            'version': order['version'], 'purpose': 'Legitimate new synthetic prescription draft version',
            'lines': [dict(lines[0], quantity=4)]}, key())
        self.assertGreater(edited['version'], order['version'])
        with self.assertRaises(UserError):
            self.printing._original_operate('preview', selection)
        recovered = self.printing._original_operate('generate', arguments)
        self.assertTrue(recovered['duplicate'])
        self.assertEqual(recovered['original_id'], generated['original_id'])
        self.assertEqual(recovered['sha256'], generated['sha256'])
        old_again, _checksum = self.printing._original_operate('download', {'original_id': generated['original_id']})
        self.assertEqual(old_again, raw)
        self.assertEqual(self._business_counts(), before)

    def test_formal_template_cannot_publish_without_a_real_approval_reference(self):
        manager = bind(self, self.users['manager']).env['ydental.print.service']
        created = manager._original_operate('template_create', {'name': 'Unapproved formal content placeholder',
            'kind': 'consent', 'version': key(), 'body': 'No formal content supplied. Review remains pending.',
            'applicability': 'Unpublished placeholder; no clinical or policy approval', 'synthetic': False})
        manager._original_operate('template_review', {'template_id': created['template_id'], 'action': 'review'})
        with self.assertRaises(UserError):
            manager._original_operate('template_review', {'template_id': created['template_id'], 'action': 'publish'})
        template = self.root['ydental.document.template'].browse(created['template_id'])
        self.assertEqual(template.state, 'reviewed')
        self.assertFalse(template.published_at)
        self.assertFalse(template.published_by_id)
