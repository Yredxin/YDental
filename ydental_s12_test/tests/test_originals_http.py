import hashlib
import io
import json
from unittest.mock import patch
import zipfile

from odoo.tests import HttpCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key, price, save_args, setup
from odoo.addons.ydental_treatment_test.tests.test_http import TestClinicalHTTP
from odoo.addons.ydental_treatment_test.tests.treatment_common import opened_actual
from odoo.addons.ydental_exam_test.tests.test_exam import TestExamination

from .test_financial_originals import TestFinancialOriginals


@tagged('post_install', '-at_install')
class TestDocumentOriginalsHTTP(TestClinicalHTTP):
    """Actual HTTP inside HttpCase isolation; not durable business evidence."""

    @classmethod
    def setUpClass(cls):
        HttpCase.setUpClass.__func__(cls)
        cls.demo_supply_patch = patch.object(type(cls.env['ydental.supply.service']),
                                            '_allow_demo_supply', return_value=True)
        cls.demo_supply_patch.start()
        cls.addClassCleanup(cls.demo_supply_patch.stop)
        setup(cls)

    def document_action(self, operation, payload, revision=None):
        return self.url_open('/ydental/documents/action', data={
            'csrf_token': self.csrf, 'revision': self.revision if revision is None else revision,
            'operation': operation, 'payload': json.dumps(payload)})

    def source(self):
        self.begin_reception()
        saved = self.action('save', self.args())
        self.assertEqual(saved.status_code, 200, saved.text[:300])
        self.doc.update(saved.json())
        confirmed = self.action('confirm', self.args())
        self.assertEqual(confirmed.status_code, 200, confirmed.text[:300])
        self.doc.update(confirmed.json())
        return {'kind': 'clinical', 'source_id': self.doc['document_id'], 'version': self.doc['version']}

    def generated(self, selection):
        preview = self.document_action('preview', selection)
        self.assertEqual(preview.status_code, 200, preview.text[:300])
        arguments = selection | {'expected_digest': preview.json()['source_digest'], 'key': key()}
        generated = self.document_action('generate', arguments)
        self.assertEqual(generated.status_code, 200, generated.text[:300])
        return generated.json(), arguments

    def test_http_saved_original_and_print_request_have_distinct_audits(self):
        generated, arguments = self.generated(self.source())
        downloaded = self.document_action('download', {'original_id': generated['original_id']})
        self.assertEqual(downloaded.status_code, 200)
        self.assertTrue(downloaded.content.startswith(b'%PDF-'))
        self.assertEqual(hashlib.sha256(downloaded.content).hexdigest(), generated['sha256'])
        self.assertEqual(downloaded.headers['X-YDental-PDF-SHA256'], generated['sha256'])
        self.assertEqual(downloaded.headers['Content-Type'], 'application/pdf')
        self.assertIn('no-store', downloaded.headers['Cache-Control'])
        self.assertEqual(downloaded.headers['X-Content-Type-Options'], 'nosniff')
        count = self.root['ydental.document.original'].search_count([])
        repeated = self.document_action('generate', arguments)
        self.assertEqual(repeated.status_code, 200, repeated.text[:300])
        self.assertEqual(repeated.json()['original_id'], generated['original_id'])
        self.assertEqual(self.root['ydental.document.original'].search_count([]), count)
        for operation in ('pdf_view', 'print_request'):
            response = self.document_action(operation, {'original_id': generated['original_id']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, downloaded.content)
        events = self.root['ydental.access.audit'].search([('ydental_event', 'like', 'document.%')])
        self.assertTrue({'document.view', 'document.generate', 'document.download',
                         'document.pdf_view', 'document.print_request'} <= set(events.mapped('ydental_event')))
        self.assertTrue(all(row.ydental_after.get('paper_output') == 'unknown' for row in events))
        self.assertNotIn('document.paper_printed', events.mapped('ydental_event'))

    def test_http_source_and_export_permissions_are_checked_on_each_old_page_request(self):
        clinical_original, _ = self.generated(self.source())
        handover = self.action('handover', self.args() | {
            'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token']})
        self.assertEqual(handover.status_code, 200, handover.text[:300])
        self.assertEqual(self.action('exit', {
            'lease_id': self.lease['lease_id'], 'token': self.lease['token']}, queue=True).status_code, 200)
        # These extra sources follow the ordinary MODEL business services in
        # this rolled-back HttpCase; category delivery below is real HTTP.
        self.treatment, clinical, queue, self.lease, self.execution, self.document, arguments = opened_actual(self)
        self.document.update(clinical._operate('confirm', save_args(self.document)))
        arguments['document_version'] = self.document['version']
        TestFinancialOriginals.finance_setup(self)
        bill = TestFinancialOriginals.billed(self, 25)
        TestExamination._bind_templates(self)
        price(self, 80, catalog=self.catalogs[2])
        issued = TestExamination._order(self, self.treatment, arguments, indexes=(2,))
        clinical._operate('handover', save_args(self.document) | {
            'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token']})
        queue._operate('exit', {'lease_id': self.lease['lease_id'], 'token': self.lease['token']})
        examiner, action = TestExamination._external_start(self, issued)
        _actual, confirmed = TestExamination._complete_external(self, examiner, action)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {
            'medical': 'read', 'exam': 'read', 'settlement': 'read', 'export': 'write'})
        exam_original, _ = self.generated({'kind': 'exam', 'source_id': confirmed['result_id'], 'version': confirmed['version']})
        bill_original, _ = self.generated({'kind': 'bill', 'source_id': bill['invoice_id'], 'version': 0})
        originals = {'medical': clinical_original, 'exam': exam_original, 'settlement': bill_original}
        for category, generated in originals.items():
            for source_read, export in ((True, True), (True, False), (False, True), (False, False)):
                with self.subTest(category=category, source_read=source_read, export=export):
                    # In particular exam has a legitimate medical-read
                    # fallback, so disable every alternate source category.
                    permissions = dict.fromkeys(originals, 'none')
                    permissions[category] = 'read' if source_read else 'none'
                    permissions['export'] = 'write' if export else 'none'
                    self.admin._grant(self.users['doctor'].id, self.stores[0].id, permissions)
                    single = self.document_action('download', {'original_id': generated['original_id']})
                    self.assertEqual(single.status_code, 200 if source_read else 403)
                    if source_read:
                        self.assertTrue(single.content.startswith(b'%PDF-'))
                        self.assertEqual(hashlib.sha256(single.content).hexdigest(), generated['sha256'])
                    batch = self.document_action('export', {'original_ids': [generated['original_id']]})
                    self.assertEqual(batch.status_code, 200 if source_read and export else 403)
                    if batch.status_code == 200:
                        self.assertEqual(batch.headers['Content-Type'], 'application/zip')
                        with zipfile.ZipFile(io.BytesIO(batch.content)) as archive:
                            self.assertEqual(len(archive.namelist()), 1)
                            self.assertEqual(archive.read(archive.namelist()[0]), single.content)

    def test_http_original_binary_attachment_thumbnail_and_direct_report_denied(self):
        selection = self.source()
        generated, _ = self.generated(selection)
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        for path in (
                '/web/content/' + str(original.attachment_id.id),
                '/web/image/' + str(original.attachment_id.id) + '?download=1',
                '/web/content?model=ydental.document.original&id=%s&field=source_facts' % original.id,
                '/report/pdf/ydental_print.ydental_document_pdf/' + str(selection['source_id']),
                '/report/html/ydental_print.ydental_document_pdf/' + str(selection['source_id'])):
            response = self.url_open(path)
            self.assertNotEqual(response.status_code, 200, path)
            self.assertNotEqual(response.status_code, 500, path)
            self.assertNotIn('Synthetic HTTP content', response.text)
        image = self.url_open('/web/image/' + str(original.attachment_id.id))
        self.assertEqual(image.status_code, 200)
        # Native content_image returns its public placeholder after the source
        # guard raises UserError. A 200 placeholder is not a source thumbnail.
        native_placeholder = self.root.ref('web.image_placeholder')
        self.assertEqual(native_placeholder.type, 'url')
        self.assertEqual(native_placeholder.url, '/web/static/img/placeholder.png')
        placeholder = self.root['ir.binary']._placeholder(native_placeholder.url.lstrip('/'))
        self.assertEqual(image.content, placeholder)
        self.assertTrue(image.headers['Content-Type'].startswith('image/'))
        self.assertFalse(image.content.startswith(b'%PDF-'))
        self.assertNotEqual(hashlib.sha256(image.content).hexdigest(), original.pdf_sha256)
        for model, method, arguments in (
                ('ydental.print.service', '_original_operate', ['download', {'original_id': original.id}]),
                ('ydental.document.original', 'read', [[original.id], ['source_facts']]),
                ('ydental.document.original', 'export_data', [[original.id], ['source_facts']]),
                ('ir.attachment', 'read', [[original.attachment_id.id], ['datas']])):
            result = self.rpc(model, method, arguments, {'ydental_document_original_init': True,
                                                       'ydental_binding': {'session_id': 1}})
            self.assertIn('error', result)

    def test_http_csrf_unknown_schema_stale_store_and_revocation_fail_at_product(self):
        selection = self.source()
        generated, _ = self.generated(selection)
        no_csrf = self.url_open('/ydental/documents/action', data={
            'operation': 'download', 'revision': self.revision,
            'payload': json.dumps({'original_id': generated['original_id']})})
        self.assertEqual(no_csrf.status_code, 400)
        self.assertEqual(self.document_action('unknown', {}).status_code, 409)
        self.assertEqual(self.document_action('preview', selection | {'model': 'res.users'}).status_code, 409)
        switched = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switched.status_code, 200, switched.text[:300])
        self.assertEqual(self.document_action('download', {'original_id': generated['original_id']}).status_code, 409)
