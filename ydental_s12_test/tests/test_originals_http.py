import hashlib
import json

from odoo.tests import HttpCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key, setup
from odoo.addons.ydental_treatment_test.tests.test_http import TestClinicalHTTP


@tagged('post_install', '-at_install')
class TestDocumentOriginalsHTTP(TestClinicalHTTP):
    """Actual HTTP inside HttpCase isolation; not durable business evidence."""

    @classmethod
    def setUpClass(cls):
        HttpCase.setUpClass.__func__(cls)
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
        generated, _ = self.generated(self.source())
        for source_read, export in ((True, True), (True, False), (False, True), (False, False)):
            with self.subTest(source_read=source_read, export=export):
                self.admin._grant(self.users['doctor'].id, self.stores[0].id, {
                    'medical': 'read' if source_read else 'none', 'export': 'write' if export else 'none'})
                single = self.document_action('download', {'original_id': generated['original_id']})
                self.assertEqual(single.status_code, 200 if source_read else 403)
                batch = self.document_action('export', {'original_ids': [generated['original_id']]})
                self.assertEqual(batch.status_code, 200 if source_read and export else 403)
                if batch.status_code == 200:
                    self.assertEqual(batch.headers['Content-Type'], 'application/zip')

    def test_http_original_binary_attachment_thumbnail_and_direct_report_denied(self):
        selection = self.source()
        generated, _ = self.generated(selection)
        original = self.root['ydental.document.original'].browse(generated['original_id'])
        for path in (
                '/web/content/' + str(original.attachment_id.id),
                '/web/image/' + str(original.attachment_id.id),
                '/web/content?model=ydental.document.original&id=%s&field=source_facts' % original.id,
                '/report/pdf/ydental_print.ydental_document_pdf/' + str(selection['source_id']),
                '/report/html/ydental_print.ydental_document_pdf/' + str(selection['source_id'])):
            response = self.url_open(path)
            self.assertNotEqual(response.status_code, 200, path)
            self.assertNotEqual(response.status_code, 500, path)
            self.assertNotIn('Synthetic HTTP content', response.text)
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
