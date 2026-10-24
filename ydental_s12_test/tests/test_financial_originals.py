from datetime import datetime, timedelta, timezone
import hashlib
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.ydental_treatment_test.tests.common import bind, key, price

from .test_originals import TestDocumentOriginals


@tagged('post_install', '-at_install')
class TestFinancialOriginals(TestDocumentOriginals):
    """Native account/payment sources, kept inside rolled-back MODEL tests."""

    def finance_setup(self):
        root, company = self.root, self.stores[0].company_id
        suffix = key()[:6].upper()
        account = lambda name, kind, code, reconcile=False: root['account.account'].create({
            'name': 'S12 synthetic ' + name + ' ' + suffix, 'account_type': kind,
            'code': 'S12' + code + suffix, 'reconcile': reconcile,
            'company_ids': [Command.set(company.ids)]})
        income = account('income', 'income', 'I')
        outstanding = account('outstanding', 'asset_current', 'O', True)
        account('receivable', 'asset_receivable', 'R', True)
        account('payable', 'liability_payable', 'P', True)
        sale = root['account.journal'].create({'name': 'S12 sales ' + suffix, 'code': 'S' + suffix[:3],
            'type': 'sale', 'company_id': company.id})
        adjustment = root['account.journal'].create({'name': 'S12 adjustment ' + suffix, 'code': 'A' + suffix[:3],
            'type': 'general', 'company_id': company.id})
        bank = root['account.journal'].create({'name': 'S12 offline ' + suffix, 'code': 'B' + suffix[:3],
            'type': 'bank', 'company_id': company.id, 'default_account_id': outstanding.id})
        for direction in ('inbound', 'outbound'):
            methods = bank[direction + '_payment_method_line_ids'].filtered(lambda row: row.payment_method_id.code == 'manual')
            if methods:
                methods.write({'payment_account_id': outstanding.id})
            else:
                root['account.payment.method.line'].create({'name': 'S12 manual ' + direction,
                    'payment_method_id': root.ref('account.account_payment_method_manual_' + ('in' if direction == 'inbound' else 'out')).id,
                    'journal_id': bank.id, 'payment_account_id': outstanding.id})
        root['ydental.settlement.config']._new({'ydental_store_id': self.stores[0].id,
            'company_id': company.id, 'ydental_policy': 'demo_confirmation',
            'ydental_sales_journal_id': sale.id, 'ydental_adjustment_journal_id': adjustment.id,
            'ydental_income_account_id': income.id, **{'ydental_' + channel + '_journal_id': bank.id
                for channel in ('cash', 'wechat', 'alipay', 'card')}})
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'settlement': 'write'})
        self.admin._grant(self.users['catalog'].id, self.stores[0].id, {'finance_approval': 'write'})
        self.finance = bind(self, self.users['frontdesk']).env['ydental.settlement.service']
        self.approver = bind(self, self.users['catalog']).env['ydental.settlement.service']
        self.published_price = None

    def billed(self, amount):
        created = self.group._operate('catalog', {'code': 'S12-' + key(),
            'name': 'S12 synthetic consultation ' + str(amount), 'kind': 'care',
            'capability_id': self.capabilities[0].id, 'uom_id': self.uom.id}, key())
        catalog = self.root['ydental.intake.catalog'].browse(created['id'])
        self.group._operate('mapping', {'catalog_id': catalog.id, 'area_id': self.areas[0][0].id,
                                       'execution_area_id': self.areas[0][0].id}, key())
        result = price(self, amount=amount, catalog=catalog)
        self.published_price = self.root['ydental.intake.price'].browse(result['id'])
        self.billed_catalog = catalog
        actual = self.treatment._operate('execute', {
            'execution_id': self.execution.id, 'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token'],
            'document_id': self.document['document_id'], 'document_version': self.document['version'],
            'catalog_id': catalog.id, 'quantity': 1, 'source': key(),
            'reason': 'S12 synthetic actual consultation with no material consumption',
            'materials': [], 'teeth': [], 'already_performed': False, 'policy': 'demo_confirmation'}, key())
        self.assertEqual(actual['state'], 'confirmed')
        self.assertEqual(actual['amount'], amount)
        bill = self.finance._operate('bill', {'fee_ids': [actual['fee_id']], 'discount': 0,
                                             'reason': 'S12 synthetic native bill'}, key())
        self.assertEqual(bill['amount'], amount)
        return bill

    def pay(self, invoices, amount):
        return self.finance._operate('pay', {'invoice_ids': invoices, 'amount': amount, 'channel': 'cash',
            'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'S12 synthetic offline receipt'}, key())

    def test_740_partial_collection_approved_pending_and_actual_refund_preserve_old_receipt(self):
        self.source()
        self.finance_setup()
        bill = self.billed(740)
        payment = self.pay([bill['invoice_id']], 500)
        self.assertEqual(payment['residuals'][str(bill['invoice_id'])], 240)
        self.printing = self.finance.env['ydental.print.service']
        original, binary = self.generated({'kind': 'receipt', 'source_id': payment['payment_id'], 'version': 0})
        request = self.finance._operate('refund_request', {'payment_id': payment['payment_id'], 'amount': 100,
            'reason': 'S12 synthetic refund request', 'request_key': key()}, key())
        approved = self.approver._operate('refund_approve', {'refund_id': request['refund_id'],
            'reason': 'S12 distinct synthetic reviewer'}, key())
        self.assertEqual(approved['actually_refunded'], 0)
        payload = self.printing._original_payload('receipt', payment['payment_id'], 0)[3]
        self.assertEqual(payload['versions']['allocations'][0]['allocated'], 500)
        self.assertEqual(payload['versions']['allocations'][0]['residual'], 240)
        details = dict(payload['details'])
        self.assertIn('100', str(details['Approved refund awaiting actual execution']))
        before = self.root['ydental.document.original'].browse(original['original_id']).source_facts
        actual = self.finance._operate('refund_execute', {'refund_id': request['refund_id'],
            'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'S12 synthetic actual offline refund'}, key())
        self.assertEqual(actual['actually_refunded'], 100)
        self.assertTrue(actual['native_payment_id'])
        self.assertTrue(actual['credit_note_ids'])
        repeated, _ = self.printing._original_operate('download', {'original_id': original['original_id']})
        self.assertEqual(repeated, binary)
        self.assertEqual(self.root['ydental.document.original'].browse(original['original_id']).source_facts, before)
        refund_original, refund_binary = self.generated({'kind': 'refund', 'source_id': request['refund_id'], 'version': 0})
        self.assertTrue(refund_binary.startswith(b'%PDF-'))
        self.assertNotEqual(refund_original['original_id'], original['original_id'])

    def test_270_plus_200_allocation_and_600_price_frozen_after_620_publication(self):
        self.source()
        self.finance_setup()
        first, second = self.billed(270), self.billed(200)
        payment = self.pay([second['invoice_id'], first['invoice_id']], 300)
        self.assertEqual([(row['invoice_id'], row['amount']) for row in payment['allocations']],
                         [(first['invoice_id'], 270), (second['invoice_id'], 30)])
        self.assertEqual(sum(payment['residuals'].values()), 170)
        self.printing = self.finance.env['ydental.print.service']
        receipt, _ = self.generated({'kind': 'receipt', 'source_id': payment['payment_id'], 'version': 0})
        rows = self.root['ydental.document.original'].browse(receipt['original_id']).source_facts['versions']['allocations']
        self.assertEqual([row['allocated'] for row in rows], [270, 30])
        six = self.billed(600)
        saved, raw = self.generated({'kind': 'bill', 'source_id': six['invoice_id'], 'version': 0})
        price(self, amount=620, catalog=self.billed_catalog, replace=self.published_price,
              start=fields.Datetime.now() + timedelta(minutes=1))
        self.assertEqual(self.root['account.move'].browse(six['invoice_id']).amount_total, 600)
        self.assertEqual(self.printing._original_operate('download', {'original_id': saved['original_id']})[0], raw)

    def test_explicit_non_tax_example_upload_download_correction_and_source_permission(self):
        self.source()
        self.finance_setup()
        bill = self.billed(600)
        self.printing = self.finance.env['ydental.print.service']
        _, sample = self.generated({'kind': 'bill', 'source_id': bill['invoice_id'], 'version': 0})
        request_key = key()
        values = {'invoice_id': bill['invoice_id'], 'filename': 'S12-synthetic-non-tax-example.pdf', 'raw': sample,
                  'request_key': request_key, 'material_reference': 'S12 software fixture, no tax issuance', 'synthetic': True}
        original = self.finance._tax_original_upload(**values)
        self.assertTrue(self.finance._tax_original_upload(**values)['duplicate'])
        downloaded, row = self.finance._tax_original_bytes(original['original_id'], 'print_request')
        self.assertEqual(downloaded, sample)
        self.assertEqual(row.sha256, hashlib.sha256(sample).hexdigest())
        self.assertTrue(row.synthetic)
        with self.assertRaises(AccessError):
            row.write({'filename': 'replaced.pdf'})
        with self.assertRaises(AccessError):
            row.attachment_id.write({'raw': b'overwritten'})
        correction = self.finance._tax_original_upload(**(values | {'request_key': key(), 'previous_id': row.id}))
        self.assertEqual(self.root['ydental.settlement.tax.original'].browse(correction['original_id']).previous_id, row)
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'settlement': 'none'})
        with self.assertRaises(AccessError):
            self.finance._tax_original_bytes(row.id)

    def test_financial_report_totals_native_drill_and_generation_failure_preserve_payment(self):
        self.source()
        self.finance_setup()
        bill = self.billed(740)
        payment = self.pay([bill['invoice_id']], 500)
        self.printing = self.finance.env['ydental.print.service']
        preview = self.printing._original_operate('preview', {'kind': 'receipt', 'source_id': payment['payment_id'], 'version': 0})
        native = self.root['account.payment'].browse(payment['native_payment_id'])
        with patch.object(type(self.root['ir.actions.report']), '_render_qweb_pdf', side_effect=RuntimeError('controlled fixture')):
            with self.assertRaises(RuntimeError):
                self.printing._original_operate('generate', {'kind': 'receipt', 'source_id': payment['payment_id'],
                    'version': 0, 'expected_digest': preview['source_digest'], 'key': key()})
        self.assertEqual(native.move_id.state, 'posted')
        self.assertEqual(native.amount, 500)
        report = self.finance.env['ydental.reporting.service']
        date = str(self.root['ydental.settlement.payment'].browse(payment['payment_id']).ydental_business_date)
        unit = 'currency:%s' % self.currency.id
        collected = report._query('collections', date, date)
        billed = report._query('original_billing', date, date)
        residual = report._query('receivables', date, date)
        self.assertEqual(collected['totals'], {unit: 500})
        self.assertEqual(billed['totals'], {unit: 740})
        self.assertEqual(residual['totals'], {unit: 240})
        self.assertEqual(billed['rows'][0]['source_id'], bill['invoice_id'])
        self.assertEqual(residual['filters']['period_or_snapshot'], 'snapshot')
        self.assertFalse(residual['filters']['historical_asof_supported'])
