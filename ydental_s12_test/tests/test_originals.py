import copy
import hashlib
import io
from unittest.mock import patch
import zipfile

from odoo.addons.base.tests.common import DISABLED_MAIL_CREATE_CONTEXT
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools.pdf import PdfFileReader

from odoo.addons.ydental_treatment_test.tests.common import bind, key, save_args, setup
from odoo.addons.ydental_treatment_test.tests.treatment_common import opened_actual


@tagged('post_install', '-at_install')
class TestDocumentOriginals(TransactionCase):
    """Rolled-back MODEL assertions; not committed patient/economic evidence."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Native TransactionCase preserves each explicitly bound ordinary actor.
        # BaseCommon would rebind service recordsets to its default test user.
        cls.env = cls.env['base'].with_context(**DISABLED_MAIL_CREATE_CONTEXT).env
        # A class-local synthetic supply seam, as in the accepted S11 tests.
        # Persistent normal-role business evidence uses the unpatched service.
        cls.demo_supply_patch = patch.object(type(cls.env['ydental.supply.service']),
                                            '_allow_demo_supply', return_value=True)
        cls.demo_supply_patch.start()
        cls.addClassCleanup(cls.demo_supply_patch.stop)
        setup(cls)

    def source(self, confirmed=True):
        self.treatment, self.clinical, self.queue, self.lease, self.execution, self.document, _ = opened_actual(self)
        if confirmed:
            self.document.update(self.clinical._operate('confirm', save_args(self.document, 'S12 synthetic confirmed text')))
        self.printing = self.clinical.env['ydental.print.service'].with_context(lang='zh_CN')
        return {'kind': 'clinical', 'source_id': self.document['document_id'], 'version': self.document['version']}

    def generated(self, selection, request=None, previous_id=None):
        preview = self.printing._original_operate('preview', selection)
        arguments = selection | {'expected_digest': preview['source_digest'], 'key': request or key(),
                                 'previous_id': previous_id}
        result = self.printing._original_operate('generate', arguments)
        binary, checksum = self.printing._original_operate('download', {'original_id': result['original_id']})
        self.assertTrue(binary.startswith(b'%PDF-'))
        self.assertEqual(hashlib.sha256(binary).hexdigest(), checksum)
        self.assertEqual(checksum, result['sha256'])
        self.assertGreaterEqual(len(PdfFileReader(io.BytesIO(binary)).pages), 1)
        return result, binary

    def business_counts(self):
        return {name: self.root[name].search_count([]) for name in (
            'ydental.treatment.event', 'ydental.treatment.fee', 'stock.move', 'account.move', 'account.payment')}

    def test_original_pdf_is_frozen_after_master_and_document_correction(self):
        selection = self.source()
        before = self.business_counts()
        generated, original_bytes = self.generated(selection)
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        source_facts = copy.deepcopy(original.source_facts)
        template_facts = copy.deepcopy(original.template_facts)
        patient = self.execution.ydental_patient_id
        self.front.env['ydental.patient.service']._operate('edit', {
            'patient_id': patient.id, 'version': patient.ydental_version,
            'values': {'name': 'S12 synthetic renamed master'}}, key())
        self.document.update(self.clinical._operate('correct', save_args(self.document, 'S12 corrected text') | {
            'reason': 'Synthetic correction preserves historical original'}))
        after_bytes, after_sha = self.printing._original_operate('print_request', {'original_id': original.id})
        self.assertEqual(after_bytes, original_bytes)
        self.assertEqual(after_sha, generated['sha256'])
        self.assertEqual(original.source_facts, source_facts)
        self.assertEqual(original.template_facts, template_facts)
        next_original, _ = self.generated(selection | {'version': self.document['version']}, previous_id=original.id)
        new = self.root['ydental.document.original'].browse(next_original['original_id'])
        self.assertEqual(new.previous_id, original)
        self.assertEqual(new.version, original.version + 1)
        self.assertNotEqual(new.source_sha256, original.source_sha256)
        self.assertEqual(self.business_counts(), before)

    def test_source_and_export_four_combinations_keep_single_copy_distinct(self):
        selection = self.source()
        generated, expected = self.generated(selection)
        for source_read, export in ((True, True), (True, False), (False, True), (False, False)):
            with self.subTest(source_read=source_read, export=export):
                self.admin._grant(self.users['doctor'].id, self.stores[0].id, {
                    'medical': 'read' if source_read else 'none', 'export': 'write' if export else 'none'})
                if source_read:
                    actual, _ = self.printing._original_operate('download', {'original_id': generated['original_id']})
                    self.assertEqual(actual, expected)
                else:
                    with self.assertRaises(AccessError):
                        self.printing._original_operate('download', {'original_id': generated['original_id']})
                if source_read and export:
                    archive = self.printing._original_operate('export', {'original_ids': [generated['original_id']]})
                    with zipfile.ZipFile(io.BytesIO(archive)) as files:
                        self.assertEqual(files.read(files.namelist()[0]), expected)
                else:
                    with self.assertRaises(AccessError):
                        self.printing._original_operate('export', {'original_ids': [generated['original_id']]})

    def test_verified_patient_merge_preserves_old_original_and_live_source_authorization(self):
        selection = self.source()
        generated, expected_bytes = self.generated(selection)
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        frozen_facts = copy.deepcopy(original.source_facts)
        source = self.root['ydental.clinical.document'].browse(self.document['document_id'])
        source_version, source_author = source.ydental_version, source.ydental_author_id.id
        versions = self.root['ydental.clinical.version'].search([('ydental_document_id', '=', source.id)])
        old_versions = [(row.id, row.ydental_number, row.ydental_author_id.id, copy.deepcopy(row.ydental_content))
                        for row in versions]
        handover = self.clinical._operate('handover', {
            'document_id': source.id, 'editor_token': self.document['editor_token'],
            'expected_version': source_version, 'content': self.document['content'], 'key': key(),
            'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token'],
            'reason': 'S12 synthetic segment ended before group identity verification'})
        self.queue._operate('exit', {'lease_id': self.lease['lease_id'], 'token': self.lease['token']})
        continuation = self.root['ydental.intake.task'].browse(handover['continuation_task_id'])
        continuation_state = continuation.state
        patient_service = self.front.env['ydental.patient.service']
        target = patient_service._operate('create', {'values': {
            'name': 'S12 synthetic verified canonical identity'}}, key())['id']
        request = patient_service._operate('request_merge', {'source_id': self.execution.ydental_patient_id.id,
            'target_id': target, 'reason': 'Explicit synthetic duplicate identity for original-file preservation'}, key())
        before = self.business_counts()
        result = self.group.env['ydental.patient.service']._operate('confirm', {
            'request_id': request['id'], 'version': request['version'],
            'reason': 'Group verified these two new synthetic identities; preserve source history'}, key())
        self.assertEqual(result['result'], 'accepted', result)
        self.assertEqual(result['patient_id'], target)
        self.assertEqual(self.printing._original_operate('download', {'original_id': original.id})[0], expected_bytes)
        self.assertEqual(original.source_facts, frozen_facts)
        self.assertEqual(hashlib.sha256(expected_bytes).hexdigest(), original.pdf_sha256)
        self.assertEqual((source.ydental_version, source.ydental_author_id.id), (source_version, source_author))
        self.assertEqual([(row.id, row.ydental_number, row.ydental_author_id.id, row.ydental_content) for row in versions], old_versions)
        self.assertTrue(continuation.exists())
        self.assertEqual(continuation.state, continuation_state)
        self.assertEqual(self.business_counts(), before)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        with self.assertRaises(AccessError):
            self.printing._original_operate('download', {'original_id': original.id})

    def test_generation_retry_and_renderer_failure_do_not_repeat_business(self):
        selection = self.source()
        preview = self.printing._original_operate('preview', selection)
        arguments = selection | {'expected_digest': preview['source_digest'], 'key': key()}
        count = self.root['ydental.document.original'].search_count([])
        before = self.business_counts()
        with patch.object(type(self.printing.env['ir.actions.report']), '_render_qweb_pdf',
                          side_effect=UserError('render_failed: controlled synthetic engine failure')):
            with self.assertRaises(UserError):
                self.printing._original_operate('generate', arguments)
        self.assertEqual(self.root['ydental.document.original'].search_count([]), count)
        first = self.printing._original_operate('generate', arguments)
        repeated = self.printing._original_operate('generate', arguments)
        self.assertEqual(first['original_id'], repeated['original_id'])
        self.assertTrue(repeated['duplicate'])
        self.assertEqual(self.root['ydental.document.original'].search_count([]), count + 1)
        self.assertEqual(self.business_counts(), before)

    def test_stored_original_and_native_attachment_cannot_be_replaced(self):
        generated, _ = self.generated(self.source())
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        with self.assertRaises(AccessError):
            original.write({'pdf_sha256': '0' * 64})
        with self.assertRaises(AccessError):
            original.unlink()
        with self.assertRaises(AccessError):
            original.attachment_id.write({'raw': b'overwritten'})
        with self.assertRaises(AccessError):
            original.attachment_id.unlink()
        for res_model, res_id in ((original._name, original.id), ('ir.attachment', original.attachment_id.id)):
            with self.assertRaises(AccessError):
                self.printing.env['ir.binary']._find_record(res_model=res_model, res_id=res_id)

    def test_plain_text_template_cannot_inject_qweb_and_unreviewed_is_unpublished(self):
        selection = self.source()
        manager = bind(self, self.users['manager']).env['ydental.print.service']
        text = '<script>window.s12SyntheticInjection=true</script><t t-esc="7*7"/>'
        template = manager._original_operate('template_create', {
            'name': 'S12 synthetic template', 'kind': 'clinical', 'version': key(), 'body': text,
            'applicability': 'Synthetic software test only', 'synthetic': True})
        with self.assertRaises(AccessError):
            self.printing._original_operate('preview', selection | {'template_id': template['template_id']})
        for action in ('review', 'publish'):
            manager._original_operate('template_review', {'template_id': template['template_id'], 'action': action})
        preview = self.printing._original_operate('preview', selection | {'template_id': template['template_id']})
        self.assertIn('&lt;script&gt;', preview['html'])
        self.assertNotIn('<script>window.s12SyntheticInjection', preview['html'])
        self.assertIn('t-esc', preview['html'])
        with self.assertRaises(AccessError):
            self.printing._original_operate('template_create', {
                'name': 'Unprivileged template', 'kind': 'clinical', 'version': key(), 'body': text,
                'applicability': 'Synthetic only', 'synthetic': True})
