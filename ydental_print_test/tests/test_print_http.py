import base64
import json

from odoo.tests import HttpCase, tagged
from odoo.addons.ydental_treatment_test.tests.test_treatment_http import TestTreatmentHTTP
from odoo.addons.ydental_treatment_test.tests.common import key
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup


@tagged('post_install', '-at_install')
class TestPrintHTTP(TestTreatmentHTTP):
    @classmethod
    def setUpClass(cls):
        HttpCase.setUpClass.__func__(cls)
        setup(cls)
        cls.admin._grant(cls.users['doctor'].id, cls.stores[0].id, {'export': 'write'})

    def p_action(self, operation, payload):
        return self.url_open('/ydental/print/action', data={'csrf_token': self.csrf, 'revision': self.revision,
            'operation': operation, 'payload': json.dumps(payload)})

    def selection(self):
        self.medical()
        return {'kind': 'clinical', 'source_id': self.doc['document_id'], 'version': self.doc['version']}

    def generated(self, source):
        preview = self.p_action('preview', source);self.assertEqual(preview.status_code, 200, preview.text)
        gen = self.p_action('generate', source | {'expected_digest': preview.json()['source_digest'], 'key': key()})
        self.assertEqual(gen.status_code, 200, gen.text)
        return gen.json()

    def test_http_three_pdf_types_binary_headers_and_request_audits(self):
        source = self.selection()
        line = {'mapping_id': self.drug_mapping.id, 'quantity': 6, 'uom_id': self.uom.id, 'product_id': self.products['medicine'],
            'specification': '合成规格', 'usage': '合成用法', 'frequency': '合成频次', 'course': '合成疗程'}
        doc = self.root['ydental.clinical.document'].browse(source['source_id'])
        args = {'execution_id': doc.ydental_current_execution_id.id, 'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token'], 'document_id': doc.id, 'document_version': self.doc['version']}
        draft = self.t_action('order', args | {'kind': 'prescription', 'purpose': '合成处方草稿', 'lines': [line]})
        self.assertEqual(draft.status_code, 200, draft.text)
        sources = [source, source | {'kind': 'consent'}, {'kind': 'prescription', 'source_id': draft.json()['order_id'], 'version': draft.json()['version']}]
        for src in sources:
            job = self.generated(src)
            for operation in ('pdf_view', 'download', 'print_request'):
                response = self.p_action(operation, {'job_id': job['job_id']})
                self.assertEqual(response.status_code, 200, response.text[:100]);self.assertTrue(response.content.startswith(b'%PDF-'))
                self.assertEqual(response.headers['Content-Type'], 'application/pdf')
                self.assertIn('no-store', response.headers['Cache-Control']);self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                self.assertNotIn('合成', response.headers['Content-Disposition'])
        self.assertEqual(self.url_open('/ydental/print').status_code, 200)

    def test_http_private_rpc_fake_binding_binary_and_report_route_denied(self):
        source = self.selection();job = self.generated(source)
        for model, method, args in (
            ('ydental.print.service', '_operate', ['preview', source]),
            ('ydental.print.service', '_generate', []),
            ('ydental.print.job', 'read', [[job['job_id']], ['ydental_pdf']]),
            ('ydental.print.job', 'search_read', [[]]),
            ('ydental.print.job', 'create', [{'ydental_kind': 'clinical'}]),
            ('ydental.print.job', 'write', [[job['job_id']], {'ydental_source_id': 1}]),
            ('ydental.print.job', 'export_data', [[job['job_id']], ['ydental_pdf']])):
            self.assertIn('error', self.rpc(model, method, args, {'ydental_print_scope': {'actor': self.users['doctor'].id}, 'ydental_binding': {'session_id': 1}}))
        for path in ('/report/pdf/ydental_print.ydental_document_pdf/', '/report/html/ydental_print.ydental_document_pdf/'):
            response = self.url_open(path + str(source['source_id']));self.assertNotEqual(response.status_code, 200)
            self.assertNotIn('Synthetic HTTP content', response.text)
        for path in ('/web/content?model=ydental.print.job&id=%s&field=ydental_pdf' % job['job_id'], '/ydental/print/action?operation=download&job_id=' + str(job['job_id'])):
            self.assertNotEqual(self.url_open(path).status_code, 200)

    def test_http_csrf_unknown_extra_fields_and_stale_revision(self):
        source = self.selection()
        response = self.url_open('/ydental/print/action', data={'operation': 'preview', 'revision': self.revision, 'payload': json.dumps(source)})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.p_action('invented', {}).status_code, 409)
        self.assertEqual(self.p_action('preview', source | {'model': 'res.users'}).status_code, 409)
        old = self.revision
        response = self.url_open('/ydental/access/action', data={'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200);self.revision = old
        self.assertEqual(self.p_action('preview', source).status_code, 409)

    def test_http_revocation_old_job_other_user_and_no_source_read(self):
        source = self.selection();job = self.generated(source)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'export': 'none'})
        self.assertEqual(self.p_action('download', {'job_id': job['job_id']}).status_code, 403)
        self.select('price');self.admin._grant(self.users['price'].id, self.stores[0].id, {'export': 'write'})
        self.assertEqual(self.p_action('preview', source).status_code, 403)
        self.assertEqual(self.p_action('download', {'job_id': job['job_id']}).status_code, 403)

    def test_http_attachment_public_and_token_bypass_no_sensitive_error(self):
        source = self.selection();job = self.generated(source)
        self.assertIn('error', self.rpc('ir.attachment', 'create', [{'name': 'forged', 'res_model': 'ydental.print.job', 'res_id': job['job_id'], 'datas': 'YQ==', 'public': True}]))
        attachment = self.root['ir.attachment'].create({'name': 'synthetic administrative test', 'res_model': 'ydental.print.job', 'res_id': job['job_id'], 'datas': base64.b64encode(b'fake-private-pdf'), 'public': True, 'access_token': key()})
        response = self.url_open('/web/content/' + str(attachment.id) + '?download=1&access_token=' + attachment.access_token)
        self.assertNotEqual(response.status_code, 200);self.assertNotIn('fake-private-pdf', response.text)
        response = self.p_action('preview', source | {'source_id': 999999999})
        self.assertEqual(response.status_code, 403);self.assertNotIn('Synthetic HTTP content', response.text)
        self.assertNotIn('999999999', response.text)

    def test_http_download_repeat_does_not_create_versions_events_fees(self):
        source = self.selection();job = self.generated(source)
        counts = {m: self.root[m].search_count([]) for m in ('ydental.clinical.version', 'ydental.treatment.event', 'ydental.treatment.fee', 'stock.move', 'ydental.intake.snapshot')}
        for _ in range(3):self.assertEqual(self.p_action('download', {'job_id': job['job_id']}).status_code, 200)
        self.assertEqual(counts, {m: self.root[m].search_count([]) for m in counts})
