import base64
import io
import json
import subprocess
import unicodedata
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools.pdf import PdfFileReader

from odoo.addons.ydental_treatment_test.tests.common import key, price, bind, handover_args, save_args, lease_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual, prescription, receive, pharmacy_start, distinct_medicine
from odoo.addons.ydental_clinical.models.ydental_clinical_service import TEETH
from odoo.addons.ydental_print.models.ydental_print_service import REPORT, normalized


@tagged('post_install', '-at_install')
class TestControlledPrint(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        cls.admin._grant(cls.users['doctor'].id, cls.stores[0].id, {'export': 'write'})
        cls.admin._grant(cls.pharmacist.id, cls.stores[0].id, {'export': 'write'})

    def source(self):
        self.s, self.c, self.q, self.l, self.e, self.d, self.a = opened_actual(self)
        self.p = self.c.env['ydental.print.service'].with_context(lang='zh_CN')
        return {'kind': 'clinical', 'source_id': self.d['document_id'], 'version': self.d['version']}

    def generate(self, selection):
        preview = self.p._operate('preview', selection)
        job = self.p._operate('generate', selection | {'expected_digest': preview['source_digest'], 'key': key()})
        pdf, signature = self.p._operate('download', {'job_id': job['job_id']})
        self.assertTrue(pdf.startswith(b'%PDF-'));self.assertGreater(len(pdf), 5000)
        reader = PdfFileReader(io.BytesIO(pdf));self.assertGreaterEqual(len(reader.pages), 1)
        self.assertIn('演示', unicodedata.normalize('NFKC', ''.join(page.extract_text() for page in reader.pages)))
        return job, pdf

    def test_three_actual_pdf_binaries_no_attachment_and_audit_distinct(self):
        selection = self.source()
        for kind in ('clinical', 'consent'):
            job, pdf = self.generate(selection | {'kind': kind})
            self.p._operate('pdf_view', {'job_id': job['job_id']})
            self.p._operate('print_request', {'job_id': job['job_id']})
        order = prescription(self, self.s, self.a)
        self.generate({'kind': 'prescription', 'source_id': order['order_id'], 'version': order['version']})
        self.assertFalse(self.root['ir.attachment'].search_count([('res_model', '=', 'ydental.print.job')]))
        events = self.root['ydental.access.audit'].search([('ydental_event', 'like', 'print.%')]).mapped('ydental_event')
        for event in ('print.view', 'print.generate', 'print.pdf_view', 'print.download', 'print.print_requested'):
            self.assertIn(event, events)
        self.assertFalse(any('paper_printed' in e for e in events))

    def test_long_chinese_52_teeth_zero_unknown_missing_and_injection(self):
        selection = self.source()
        args = save_args(self.d);args['content']['history'] = '合成长病史段落，中文换页核对。' * 650
        args['content']['findings'] = '<script>notExecutable()</script><img src="file:///etc/passwd">'
        args['content']['teeth'] = [{'tooth': t, 'state': 'unknown' if t == 51 else 'missing' if t == 48 else 'present', 'surfaces': []} for t in TEETH] + [{'tooth': 0, 'state': 'not_applicable', 'surfaces': []}]
        self.d.update(self.c._operate('save', args));selection['version'] = self.d['version']
        preview = self.p._operate('preview', selection)
        self.assertIn('&lt;script&gt;', preview['html']);self.assertNotIn('<img src=', preview['html'])
        job, pdf = self.generate(selection)
        self.assertGreater(len(PdfFileReader(io.BytesIO(pdf)).pages), 2)
        payload = self.p._source(**selection)[3]
        self.assertEqual(len(payload['teeth']), 53)
        self.assertEqual(payload['teeth'][0]['tooth'], 0)

    def test_pending_and_confirmed_independent_author_and_old_correction_version(self):
        selection = self.source()
        for i in range(2):self.d.update(self.c._operate('save', save_args(self.d, 'D1合成保存' + str(i))))
        self.d.update(self.c._operate('handover', handover_args(self.d, self.l)))
        selected = selection | {'version': self.d['version']}
        payload = self.p._source(**selected)[3]
        self.assertIn('待完善', payload['status'])
        historical = selected.copy()
        self.d.update(self.c._operate('acquire', {'document_id': self.d['document_id']}))
        self.d.update(self.c._operate('confirm', save_args(self.d, 'D1明确核对确认')))
        confirmed = self.d['version']
        self.d.update(self.c._operate('correct', save_args(self.d, '附原因新版本') | {'reason': '合成文字更正'}))
        old = self.p._source(**(selected | {'version': confirmed}))[3]
        new = self.p._source(**(selected | {'version': self.d['version']}))[3]
        self.assertNotEqual(old['sections'][0], new['sections'][0])
        self.assertEqual(self.root['ydental.clinical.version'].search([('ydental_document_id', '=', self.d['document_id']), ('ydental_number', '=', historical['version'])]).ydental_kind, 'save')
        self.generate(selected | {'version': confirmed})

    def test_consent_does_not_copy_medical_content_or_signature(self):
        selection = self.source() | {'kind': 'consent'}
        payload = self.p._source(**selection)[3]
        self.assertIn('未签署', payload['status']);self.assertEqual(len(payload['sections']), 8)
        self.assertNotIn('Synthetic clinical draft', normalized(payload))
        self.assertTrue(all('待' in section['paragraphs'][0] for section in payload['sections']))
        self.generate(selection)

    def test_source_read_and_export_both_required_revocation_next_request(self):
        selection = self.source()
        job, _ = self.generate(selection)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'export': 'none'})
        with self.assertRaises(AccessError):self.p._operate('download', {'job_id': job['job_id']})
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'export': 'write', 'medical': 'none'})
        with self.assertRaises(AccessError):self.p._operate('preview', selection)
        self.admin._grant(self.users['price'].id, self.stores[0].id, {'export': 'write'})
        price_reader = bind(self, self.users['price']).env['ydental.print.service']
        with self.assertRaises(AccessError):price_reader._operate('preview', selection)

    def test_pharmacy_minimal_rx_and_no_clinical_or_draft(self):
        selection = self.source();order = prescription(self, self.s, self.a)
        pharm = bind(self, self.pharmacist).env['ydental.print.service'].with_context(lang='zh_CN')
        with self.assertRaises(AccessError):pharm._operate('preview', selection)
        with self.assertRaises(AccessError):pharm._operate('preview', selection | {'kind': 'consent'})
        value = pharm._source('prescription', order['order_id'], order['version'])[3]
        self.assertFalse(value['sections']);self.assertEqual(value['lines'][0]['approved'], 6)
        self.assertNotIn('chief_complaint', normalized(value))

    def test_prescription_real_four_plus_two_and_stale_generated_copy(self):
        receive(self, kind='medicine');price(self, amount=10, catalog=self.drug_catalog)
        selection = self.source();order = prescription(self, self.s, self.a)
        rx = {'kind': 'prescription', 'source_id': order['order_id'], 'version': order['version']}
        before, _ = self.generate(rx)
        self.c._operate('handover', handover_args(self.d, self.l));self.q._operate('exit', lease_args(self.l))
        pharm, args = pharmacy_start(self, order)
        dose = args | {'line_id': order['line_ids'][0], 'lot_id': self.lots['medicine'], 'quantity': 4,
            'source': key(), 'reason': '合成真实四份', 'policy': 'demo_confirmation'}
        pharm._operate('dispense', dose, key())
        middle = self.p._source(**rx)[3]['lines'][0]
        self.assertEqual((middle['approved'], middle['dispensed'], middle['remaining']), (6, 4, 2))
        with self.assertRaises(UserError):self.p._operate('download', {'job_id': before['job_id']})
        self.generate(rx)
        finished = pharm._operate('finish', args | {'reason': '合成结束第一段'}, key())
        pharm, args2 = pharmacy_start(self, order, finished['next_task_id'])
        pharm._operate('dispense', dose | args2 | {'quantity': 2, 'source': key()}, key())
        pharm._operate('finish', args2 | {'reason': '合成结束第二段'}, key())
        payload = self.p._source(**rx)[3]
        self.assertEqual((payload['lines'][0]['dispensed'], payload['lines'][0]['remaining']), (6, 0))
        self.assertEqual(len(payload['events']), 2);self.generate(rx)

    def test_generation_key_idempotent_and_model_immutable(self):
        selection = self.source();preview = self.p._operate('preview', selection)
        args = selection | {'expected_digest': preview['source_digest'], 'key': key()}
        first = self.p._operate('generate', args);second = self.p._operate('generate', args)
        self.assertEqual(first['job_id'], second['job_id'])
        for op in ('create', 'write', 'unlink', 'read', 'export_data'):
            job = self.p.env['ydental.print.job'].browse(first['job_id'])
            with self.assertRaises(AccessError):
                if op == 'create':job.create({'ydental_kind': 'clinical'})
                elif op == 'write':job.write({'ydental_source_id': 999})
                elif op == 'unlink':job.unlink()
                elif op == 'read':job.read(['ydental_pdf'])
                else:job.export_data(['ydental_pdf'])

    def test_report_direct_bypass_even_with_fake_context_and_data(self):
        selection = self.source()
        report = self.p.env['ir.actions.report']
        for renderer in (report._render_qweb_html, report._render_qweb_pdf):
            with self.assertRaises(AccessError):renderer(REPORT, [selection['source_id']], data={'p': {'kind': 'clinical'}})
        with self.assertRaises(AccessError):report.with_context(ydental_print_scope={'actor': self.p.env.uid})._render_qweb_html(REPORT, [selection['source_id']])

    def test_source_digest_change_unknown_version_type_and_payload_fail_closed(self):
        selection = self.source();preview = self.p._operate('preview', selection)
        self.d.update(self.c._operate('save', save_args(self.d, '新服务器内容')))
        with self.assertRaises(UserError):self.p._operate('generate', selection | {'expected_digest': preview['source_digest'], 'key': key()})
        for bad in (selection | {'kind': 'arbitrary_model'}, selection | {'version': 9999}, selection | {'source_id': True}, selection | {'model': 'res.users'}):
            with self.assertRaises((AccessError, UserError, ValidationError)):self.p._operate('preview', bad)

    def test_source_relation_and_cross_store_purpose(self):
        selection = self.source()
        self.admin._grant(self.users['doctor'].id, self.stores[1].id, {'medical': 'read', 'export': 'write'})
        other = bind(self, self.users['doctor'], self.stores[1]).env['ydental.print.service']
        with self.assertRaises(AccessError):other._operate('preview', selection)
        # Establish the genuine current-store patient relationship through S04.
        patient = self.e.ydental_patient_id
        bind(self, self.users['frontdesk'], self.stores[1]).env['ydental.patient.service']._operate('relation', {'patient_id': patient.id}, key())
        value = other._operate('preview', selection | {'purpose': 'history_review'})
        self.assertTrue(value['source_digest'])
        with self.assertRaises(AccessError):other._operate('preview', selection | {'purpose': ''})

    def test_expiry_other_actor_session_and_source_attachment_rejected(self):
        selection = self.source();job, _ = self.generate(selection)
        other = bind(self, self.users['doctor']).env['ydental.print.service']
        with self.assertRaises(AccessError):other._operate('download', {'job_id': job['job_id']})
        from datetime import timedelta
        with patch.object(fields.Datetime, 'now', return_value=fields.Datetime.now() + timedelta(minutes=16)):
            with self.assertRaises(AccessError):self.p._operate('download', {'job_id': job['job_id']})
        with self.assertRaises(AccessError):self.p.env['ir.attachment'].create({'name': 'forged', 'res_model': 'ydental.print.job', 'res_id': job['job_id'], 'datas': base64.b64encode(b'fake')})

    def test_engine_failure_timeout_font_missing_leave_no_job_or_business_mutation(self):
        selection = self.source();preview = self.p._operate('preview', selection)
        args = selection | {'expected_digest': preview['source_digest'], 'key': key()}
        before = self.root['ydental.print.job'].search_count([])
        from odoo.addons.ydental_print.models import ir_actions_report
        with patch.object(ir_actions_report.shutil, 'which', return_value=None):
            with self.assertRaises(UserError):self.p._operate('generate', args)
        original = ir_actions_report.subprocess.run
        def timeout(command, **kwargs):
            if 'wkhtmltopdf' in command[0]:raise subprocess.TimeoutExpired(command[0], 30)
            return original(command, **kwargs)
        with patch.object(ir_actions_report.subprocess, 'run', side_effect=timeout):
            with self.assertRaises(UserError):self.p._operate('generate', args)
        with patch.object(ir_actions_report.IrActionsReport, '_run_wkhtmltopdf', side_effect=UserError('render_failed')):
            with self.assertRaises(UserError):self.p._operate('generate', args)
        with patch.object(type(self.p.env['ir.actions.report']), '_render_qweb_pdf', return_value=(b'%PDF-1.4 synthetic corrupt file', 'pdf')):
            with self.assertRaises(UserError):self.p._operate('generate', args)
        self.assertEqual(self.root['ydental.print.job'].search_count([]), before)
        self.assertEqual(self.root['ydental.clinical.document'].browse(self.d['document_id']).ydental_version, self.d['version'])
        self.assertFalse(self.root['ydental.treatment.event'].search_count([('ydental_execution_id', '=', self.e.id)]))

    def test_company_removed_and_audit_never_copies_clinical_body(self):
        selection = self.source()
        args = save_args(self.d, 'S08C-SYNTHETIC-PRIVATE-BODY-MUST-NOT-BE-IN-AUDIT')
        self.d.update(self.c._operate('save', args));selection['version'] = self.d['version']
        job, _ = self.generate(selection)
        audits = self.root['ydental.access.audit'].search([('ydental_event', 'like', 'print.%')])
        self.assertNotIn('S08C-SYNTHETIC-PRIVATE-BODY-MUST-NOT-BE-IN-AUDIT', json.dumps(audits.mapped('ydental_after')))
        company = self.root['res.company'].create({'name': 'S08C isolated synthetic company'})
        self.users['doctor'].write({'company_id': company.id, 'company_ids': [fields.Command.set(company.ids)]})
        with self.assertRaises(AccessError):self.p._operate('download', {'job_id': job['job_id']})

    def test_sixteen_long_chinese_prescription_rows_retain_every_field(self):
        selection = self.source()
        rows = []
        for number in range(16):
            values = {'mapping_id': self.drug_mapping.id, 'quantity': 6, 'uom_id': self.uom.id, 'product_id': self.products['medicine']}
            for name in ('specification', 'usage', 'frequency', 'course'):
                marker = 'S08C-%s-%02d-END' % (name, number)
                values[name] = ('合成长字段，仅供排版测试，不代表医学意见。' * 20)[:240 - len(marker)] + marker
            rows.append(values)
        draft = self.s._operate('order', self.a | {'kind': 'prescription', 'purpose': '合成长表草稿', 'lines': rows}, key())
        _, pdf = self.generate({'kind': 'prescription', 'source_id': draft['order_id'], 'version': draft['version']})
        text = unicodedata.normalize('NFKC', ''.join(page.extract_text() for page in PdfFileReader(io.BytesIO(pdf)).pages))
        for number in range(16):
            for name in ('specification', 'usage', 'frequency', 'course'):
                self.assertIn('S08C-%s-%02d-END' % (name, number), text.replace('\n', ''))
