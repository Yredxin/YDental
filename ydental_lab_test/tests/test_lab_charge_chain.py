"""End-to-end synthetic test for a real S05 quote and native S10 invoice.

The shared treatment test helpers create actual synthetic clinical execution
fixtures; this test does not replace the charge or settlement service.
"""
import base64
import secrets
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import bind, key, price
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    execute_args, opened_actual, receive, setup as treatment_setup,
)


def _s11_key(label, record_id):
    """Keep synthetic action keys stable and above the service minimum."""
    return 's11-lab-chain-%s-%s' % (label, record_id)


@tagged('post_install', '-at_install')
class TestLabChargeNativeChain(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The S10 adapter intentionally refuses to open its own demo runner in
        # the S11-preserved scratch. Keep the override inside this S11 test
        # class and exercise all real supply/queue/treatment logic unchanged.
        cls.demo_policy_patch = patch.object(
            type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        cls.demo_policy_patch.start()
        cls.addClassCleanup(cls.demo_policy_patch.stop)
        # This fixture creates a second native stock warehouse. Configure the
        # ordinary internal-user groups through the Settings-owned group model,
        # matching the production prerequisite enforced by inventory setup.
        root = cls.env['base'].sudo().env
        internal_users = root.ref('base.group_user')
        internal_users.write({'implied_ids': [
            Command.link(root.ref('stock.group_stock_multi_warehouses').id),
            Command.link(root.ref('stock.group_stock_multi_locations').id),
        ]})
        treatment_setup(cls)
        # The test actor uses the existing synthetic manager role, with the
        # native purchase group required for a zero-cost supplier attestation.
        cls.users['manager'].write({'group_ids': [Command.link(cls.root.ref('purchase.group_purchase_manager').id)]})
        cls.admin._grant(cls.users['manager'].id, cls.stores[0].id,
                         {'settlement': 'write', 'medical': 'write', 'price': 'write',
                          'warehouse': 'write', 'followup': 'write'})

    def _real_treatment_source(self):
        receive(self)
        price(self, amount=137.25)
        treatment, _clinical, _queue, _lease, execution, _data, args = opened_actual(self)
        result = treatment._operate('execute', execute_args(self, args, actual=True), key())
        self.assertEqual(result['state'], 'confirmed')
        event = self.root['ydental.treatment.event'].browse(result['event_id']).exists()
        self.assertTrue(event and event.state == 'confirmed' and event.ydental_kind == 'treatment')
        self.assertEqual(event.ydental_execution_id, execution)
        return event

    def _settlement_config(self):
        company = self.stores[0].company_id
        root = self.root
        token = secrets.token_hex(4).upper()
        income = root['account.account'].sudo().create({
            'name': 'S11 synthetic lab charge income ' + token,
            'code': 'S11' + token, 'account_type': 'income',
            'company_ids': [Command.set([company.id])],
        })
        cash_account = root['account.account'].sudo().create({
            'name': 'S11 synthetic outstanding ' + token,
            'code': 'S12' + token, 'account_type': 'asset_current',
            'reconcile': True, 'company_ids': [Command.set([company.id])],
        })
        sale = root['account.journal'].sudo().create({
            'name': 'S11 synthetic sales ' + token, 'code': 'S' + token[:3],
            'type': 'sale', 'company_id': company.id,
        })
        adjustment = root['account.journal'].sudo().create({
            'name': 'S11 synthetic adjustment ' + token, 'code': 'A' + token[:3],
            'type': 'general', 'company_id': company.id,
        })
        bank = root['account.journal'].sudo().create({
            'name': 'S11 synthetic bank ' + token, 'code': 'B' + token[:3],
            'type': 'bank', 'company_id': company.id, 'default_account_id': cash_account.id,
        })
        manual_in = root.ref('account.account_payment_method_manual_in')
        manual_lines = bank.inbound_payment_method_line_ids.filtered(
            lambda row: row.payment_method_id == manual_in)
        if manual_lines:
            manual_lines[:1].sudo().write({'payment_account_id': cash_account.id})
        else:
            root['account.payment.method.line'].sudo().create({
                'name': 'Manual inbound synthetic ' + token, 'payment_method_id': manual_in.id,
                'journal_id': bank.id, 'payment_account_id': cash_account.id,
            })
        config = root['ydental.settlement.config']._new({
            'ydental_store_id': self.stores[0].id, 'company_id': company.id,
            'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sale.id,
            'ydental_adjustment_journal_id': adjustment.id, 'ydental_income_account_id': income.id,
            'ydental_cash_journal_id': bank.id, 'ydental_wechat_journal_id': bank.id,
            'ydental_alipay_journal_id': bank.id, 'ydental_card_journal_id': bank.id,
        })
        return config

    def _charge_cycle(self, event, catalog, with_purchase_cost=False):
        manager = self.users['manager']
        store = self.stores[0]
        partner = self.root['res.partner'].sudo().create({'name': 'S11 synthetic lab vendor ' + key()})
        vendor = self.root['ydental.lab.vendor'].with_user(manager).create({
            'partner_id': partner.id, 'company_ids': [Command.set([store.company_id.id])],
            'category': 'other', 'qualification_reference': 'S11-SYNTH-' + key(),
            'qualification_evidence': base64.b64encode(b'Synthetic qualification only').decode(),
            'qualification_evidence_name': 'synthetic.txt',
            'valid_until': fields.Date.context_today(self) + timedelta(days=30),
        })
        lab_service = self.root['ydental.lab.service'].with_user(manager)
        lab_service._review_vendor(vendor, 'approved', 'Synthetic test qualification review')
        cooperation = self.group.env['ydental.lab.cooperation'].create({
            'ydental_vendor_id': vendor.id, 'active': True,
        })
        inventory = self.group.env['ydental.inventory.service']
        prosthesis = inventory._operate('product', {
            'code': 'S11-LAB-' + key(), 'name': 'S11 synthetic prosthesis', 'kind': 'prosthesis',
            'stock_uom_id': self.uom.id, 'issue_uom_id': self.uom.id, 'step': 1,
            'specification': 'Synthetic fixture only',
        }, key())
        purchase_line = self.root['purchase.order.line']
        if with_purchase_cost:
            token = key()
            incoming_type = self.root['stock.picking.type'].sudo().search([
                ('code', '=', 'incoming'), ('warehouse_id.company_id', '=', store.company_id.id),
            ], limit=1)
            self.assertTrue(incoming_type)
            service_product = self.root['product.template'].sudo().create({
                'name': 'S11 synthetic vendor service ' + token, 'type': 'service',
                'purchase_ok': True, 'sale_ok': False, 'uom_id': self.uom.id,
                'company_id': store.company_id.id,
            }).product_variant_id
            purchase = self.root['purchase.order'].with_user(manager).with_company(store.company_id).create({
                'partner_id': partner.id, 'company_id': store.company_id.id,
                'currency_id': store.company_id.currency_id.id,
                'picking_type_id': incoming_type.id,
                'date_order': fields.Datetime.now(),
                'order_line': [Command.create({
                    'name': 'Synthetic confirmed external lab service cost',
                    'product_id': service_product.id, 'product_qty': 1,
                    'uom_id': self.uom.id, 'price_unit': 42.75,
                    'date_planned': fields.Datetime.now() + timedelta(days=1),
                })],
            })
            purchase.button_confirm()
            purchase_line = purchase.order_line.ensure_one()
        parent = self.group.env['ydental.lab.order'].create({
            'name': 'S11 synthetic original order', 'ydental_source_event_id': event.id,
            'ydental_vendor_id': vendor.id, 'ydental_product_id': prosthesis['id'],
            'ydental_quantity': 1, 'ydental_teeth': [16], 'ydental_material': 'Synthetic material',
            'ydental_instructions': 'Synthetic fixture, not clinical instructions',
            'ydental_internal_code': 'S11-' + key(), 'ydental_responsible_id': manager.id,
            'ydental_planned_at': fields.Datetime.now(),
        })
        child = self.group.env['ydental.lab.order']._new({
            'name': 'S11 synthetic additional rework', 'ydental_store_id': store.id,
            'ydental_category': 'medical', 'ydental_patient_id': parent.ydental_patient_id.id,
            'ydental_source_event_id': event.id, 'ydental_source_document_id': parent.ydental_source_document_id.id,
            'ydental_source_fee_id': parent.ydental_source_fee_id.id,
            'ydental_vendor_id': vendor.id, 'ydental_product_id': prosthesis['id'],
            'ydental_quantity': 1, 'ydental_teeth': [16], 'ydental_material': 'Synthetic material',
            'ydental_instructions': 'Synthetic fixture, not clinical instructions',
            'ydental_internal_code': 'S11-R-' + key(), 'ydental_responsible_id': manager.id,
            'ydental_planned_at': fields.Datetime.now(), 'ydental_parent_order_id': parent.id,
            'ydental_rework_no': 1, 'ydental_rework_kind': 'additional',
            'ydental_purchase_line_id': purchase_line.id if with_purchase_cost else False,
            'ydental_additional_service_id': catalog.id,
            'ydental_additional_service_quantity': 1,
            'ydental_additional_consent_reference': 'SYNTHETIC-CONSENT-' + key(),
            'ydental_additional_terms_reason': 'Synthetic explicitly agreed additional service',
        })
        self.assertTrue(cooperation.active)
        return child, vendor, purchase_line

    def test_published_price_performed_service_native_invoice_zero_supplier_cost_and_retry(self):
        event = self._real_treatment_source()
        self._settlement_config()
        catalog = self.catalogs[1]
        price(self, amount=80.25, catalog=catalog)
        child, _vendor, _purchase_line = self._charge_cycle(event, catalog)
        lab = self.group.env['ydental.lab.service']
        lab._operate('confirm_zero_supplier_cost', {
            'order_id': child.id, 'reason': 'No added supplier charge; patient terms remain separate',
        }, _s11_key('zero-cost', child.id))
        self.assertTrue(child.ydental_zero_supplier_cost_confirmed)
        self.assertFalse(child.ydental_purchase_line_id)
        lab._operate('approve_charge_terms', {'order_id': child.id}, _s11_key('terms', child.id))
        charge = child.ydental_charge_ids.ensure_one()
        amount_before_reprice = charge.ydental_amount
        snapshot = charge.ydental_price_snapshot_id
        original_price = charge.ydental_price_id
        price(self, amount=251.75, start=fields.Datetime.now() + timedelta(seconds=30),
              catalog=catalog, replace=original_price)
        self.assertEqual(charge.ydental_amount, amount_before_reprice)
        self.assertEqual(snapshot.ydental_amount, amount_before_reprice)
        lab._operate('send', {'order_id': child.id}, _s11_key('send', child.id))
        child.write({
            'ydental_additional_performed_at': fields.Datetime.now() - timedelta(seconds=1),
            'ydental_additional_performance_evidence_reference': 'SYNTHETIC-ACTUAL-PERFORMANCE-' + key(),
        })
        lab._operate('confirm_charge_performed', {'order_id': child.id}, _s11_key('performed', child.id))
        charge.invalidate_recordset()
        self.assertEqual(charge.state, 'performed')
        self.assertEqual(charge.ydental_category, 'medical')
        self.assertEqual(self.group.env['ydental.lab.charge'].search_count([('id', '=', charge.id)]), 1)
        medical_only = bind(self, self.users['doctor']).env['ydental.lab.charge']
        self.assertEqual(medical_only.search_count([('id', '=', charge.id)]), 0)
        price_only = bind(self, self.users['price']).env['ydental.lab.charge']
        self.assertEqual(price_only.search_count([('id', '=', charge.id)]), 0)
        settlement = self.group.env['ydental.settlement.service']
        move_count = self.root['account.move'].sudo().search_count([])
        source_count = self.root['ydental.settlement.source'].sudo().search_count([
            ('ydental_lab_charge_id', '=', charge.id)])
        move_model = self.root['account.move']
        original_post = type(move_model).action_post

        def post_then_fail(records):
            original_post(records)
            raise UserError('Synthetic post-then-fail rollback check')

        with patch.object(type(move_model), 'action_post', autospec=True, side_effect=post_then_fail):
            with self.assertRaises(UserError):
                settlement._operate('bill_lab_charge', {
                    'charge_ids': [charge.id], 'reason': 'Synthetic rollback check',
                }, 's11-bill-rollback-' + str(charge.id))
        self.assertEqual(self.root['account.move'].sudo().search_count([]), move_count)
        self.assertEqual(self.root['ydental.settlement.source'].sudo().search_count([
            ('ydental_lab_charge_id', '=', charge.id)]), source_count)
        result = settlement._operate('bill_lab_charge', {
            'charge_ids': [charge.id], 'reason': 'Synthetic patient charge, no added vendor cost',
        }, 's11-bill-' + str(charge.id))
        replay = settlement._operate('bill_lab_charge', {
            'charge_ids': [charge.id], 'reason': 'Synthetic patient charge, no added vendor cost',
        }, 's11-bill-' + str(charge.id))
        source_replay = settlement._operate('bill_lab_charge', {
            'charge_ids': [charge.id], 'reason': 'Synthetic retry after native billing',
        }, 's11-bill-retry-' + str(charge.id))
        invoice = self.root['account.move'].browse(result['invoice_id']).exists()
        source = self.root['ydental.settlement.source'].search([
            ('ydental_lab_charge_id', '=', charge.id)]).exists()
        self.assertEqual(self.root['account.move'].sudo().search_count([]), move_count + 1)
        self.assertEqual(len(source), 1)
        self.assertTrue(invoice and invoice.state == 'posted' and invoice.move_type == 'out_invoice')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids, source.ydental_line_id)
        self.assertEqual(invoice.invoice_line_ids.quantity, charge.ydental_quantity)
        self.assertEqual(invoice.invoice_line_ids.price_unit, charge.ydental_unit_price)
        self.assertEqual(source.ydental_invoice_id, invoice)
        self.assertEqual(charge.ydental_settlement_source_id, source)
        self.assertEqual(replay['invoice_id'], invoice.id)
        self.assertEqual(source_replay['invoice_id'], invoice.id)
        self.assertEqual(source.ydental_original_amount, amount_before_reprice)
        # An actual performed service stays in financial history even when its
        # unreceived laboratory order is later cancelled.
        self.group.env['ydental.lab.service']._operate('cancel', {
            'order_id': child.id, 'reason': 'Synthetic cancellation after separate service performance',
        }, 's11-cancel-after-charge-' + str(child.id))
        projected = settlement._settled_source_domain(fields.Domain.TRUE, self.stores[0], None)
        self.assertIn(source.id, self.group.env['ydental.settlement.source'].search(projected).ids)

    def test_missing_effective_price_rolls_back_without_charge_or_snapshot(self):
        event = self._real_treatment_source()
        catalog = self.catalogs[1]
        child, _vendor, _purchase_line = self._charge_cycle(event, catalog)
        charge_count = self.root['ydental.lab.charge'].sudo().search_count([])
        snapshot_count = self.root['ydental.intake.snapshot'].sudo().search_count([
            ('ydental_source', '=', 's11-lab-charge-%s-%s' % (child.id, catalog.id))])
        with self.assertRaises(UserError):
            self.group.env['ydental.lab.charge.service']._prepare_terms(
                child, catalog.id, 1, 'SYNTHETIC-CONSENT-UNPRICED', 'Synthetic missing-price check')
        self.assertEqual(self.root['ydental.lab.charge'].sudo().search_count([]), charge_count)
        self.assertEqual(self.root['ydental.intake.snapshot'].sudo().search_count([
            ('ydental_source', '=', 's11-lab-charge-%s-%s' % (child.id, catalog.id))]), snapshot_count)

    def test_confirmed_native_purchase_line_is_snapshotted_once_and_mutation_is_rejected(self):
        event = self._real_treatment_source()
        catalog = self.catalogs[1]
        price(self, amount=80.25, catalog=catalog)
        child, _vendor, purchase_line = self._charge_cycle(event, catalog, with_purchase_cost=True)
        self.assertTrue(purchase_line and purchase_line.order_id.state == 'purchase')
        self.assertEqual(purchase_line.order_id.partner_id, child.ydental_vendor_id.partner_id)
        self.assertEqual(purchase_line.order_id.company_id, child.ydental_store_id.company_id)
        self.assertEqual(purchase_line.product_id.type, 'service')
        self.assertEqual(purchase_line.uom_id, purchase_line.product_id.uom_id)

        lab = self.group.env['ydental.lab.service']
        lab._operate('approve_charge_terms', {'order_id': child.id}, _s11_key('po-terms', child.id))
        lab._operate('send', {'order_id': child.id}, _s11_key('po-send', child.id))
        sent = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', child.id), ('ydental_kind', '=', 'sent')], limit=1)
        snapshot = sent.ydental_purchase_cost_snapshot
        self.assertEqual(sent.ydental_purchase_line_id, purchase_line)
        self.assertEqual(sent.ydental_purchase_state_at_dispatch, 'purchase')
        self.assertEqual(snapshot['line_id'], purchase_line.id)
        self.assertEqual(snapshot['purchase_id'], purchase_line.order_id.id)
        self.assertEqual(snapshot['vendor_id'], child.ydental_vendor_id.partner_id.id)
        self.assertEqual(snapshot['company_id'], child.ydental_store_id.company_id.id)
        self.assertEqual(snapshot['currency_id'], child.ydental_store_id.company_id.currency_id.id)
        self.assertEqual(snapshot['product_id'], purchase_line.product_id.id)
        self.assertEqual(snapshot['uom_id'], purchase_line.uom_id.id)
        self.assertEqual(snapshot['quantity'], purchase_line.product_qty)
        self.assertEqual(snapshot['unit_price'], purchase_line.price_unit)
        self.assertEqual(snapshot['subtotal'], purchase_line.price_subtotal)
        self.assertEqual(self.root['ydental.lab.order'].sudo().search_count([
            ('ydental_purchase_line_id', '=', purchase_line.id)]), 1)

        purchase = purchase_line.order_id.with_user(self.users['manager'])
        purchase.button_unlock()
        purchase_line.with_user(self.users['manager']).write({'price_unit': 43.75})
        with self.assertRaises(UserError):
            lab._operate('processing', {'order_id': child.id}, _s11_key('po-cost-changed', child.id))
        child.invalidate_recordset()
        sent.invalidate_recordset()
        self.assertEqual(child.state, 'sent')
        self.assertEqual(sent.ydental_purchase_cost_snapshot, snapshot)

    def test_native_credit_revisions_are_linked_capped_replayable_and_never_cash_refunds(self):
        event = self._real_treatment_source()
        self._settlement_config()
        catalog = self.catalogs[1]
        price(self, amount=80.25, catalog=catalog)
        child, _vendor, _purchase_line = self._charge_cycle(event, catalog)
        lab = self.group.env['ydental.lab.service']
        lab._operate('confirm_zero_supplier_cost', {
            'order_id': child.id, 'reason': 'No added vendor cost; patient charge is separate',
        }, _s11_key('credit-zero', child.id))
        lab._operate('approve_charge_terms', {'order_id': child.id}, _s11_key('credit-terms', child.id))
        charge = child.ydental_charge_ids.ensure_one()
        lab._operate('send', {'order_id': child.id}, _s11_key('credit-send', child.id))
        child.write({
            'ydental_additional_performed_at': fields.Datetime.now() - timedelta(seconds=1),
            'ydental_additional_performance_evidence_reference': 'SYNTHETIC-CREDIT-CHAIN-' + key(),
        })
        lab._operate('confirm_charge_performed', {'order_id': child.id}, _s11_key('credit-performed', child.id))
        settlement = self.group.env['ydental.settlement.service']
        billed = settlement._operate('bill_lab_charge', {
            'charge_ids': [charge.id], 'reason': 'Synthetic billed patient charge',
        }, 's11-credit-bill-' + str(charge.id))
        original = self.root['account.move'].browse(billed['invoice_id']).exists()
        original_amount = charge.ydental_amount
        original_receivable = self.group.env['ydental.settlement.service']._receivable(original, debit=True)
        payment_model = self.root['account.payment'].sudo()
        payments_before = payment_model.search_count([])

        first_payload = {
            'charge_id': charge.id, 'amount': 10.0,
            'reason': 'Synthetic correction revision one', 'request_key': 's11-credit-adjustment-one-' + str(charge.id),
        }
        first = settlement._operate('credit_lab_charge', first_payload, 's11-credit-op-one-' + str(charge.id))
        replay = settlement._operate('credit_lab_charge', first_payload, 's11-credit-op-replay-' + str(charge.id))
        self.assertEqual(replay['credit_note_id'], first['credit_note_id'])
        self.assertEqual(replay['adjustment_id'], first['adjustment_id'])
        self.assertEqual(first['actually_refunded'], 0)
        credit = self.root['account.move'].browse(first['credit_note_id']).exists()
        adjustment = self.root['ydental.lab.charge.adjustment'].browse(first['adjustment_id']).exists()
        source = adjustment.ydental_settlement_source_id
        self.assertEqual(credit.move_type, 'out_refund')
        self.assertEqual(credit.state, 'posted')
        self.assertEqual(adjustment.ydental_revision, 1)
        self.assertEqual(adjustment.ydental_credit_move_id, credit)
        self.assertEqual(adjustment.ydental_credit_line_id.move_id, credit)
        self.assertEqual(source.ydental_lab_charge_adjustment_id, adjustment)
        self.assertFalse(source.ydental_lab_charge_id)
        self.assertFalse(source.ydental_fee_id)
        self.assertEqual(source.ydental_invoice_id, credit)
        self.assertEqual(source.ydental_line_id, adjustment.ydental_credit_line_id)
        self.assertEqual(source.ydental_original_amount, -10.0)
        credit_receivable = settlement._receivable(credit, debit=False)
        reconcile = self.root['account.partial.reconcile'].sudo().search([
            ('debit_move_id', '=', original_receivable.id),
            ('credit_move_id', '=', credit_receivable.id)], limit=1)
        self.assertTrue(reconcile)
        self.assertEqual(reconcile.amount, 10.0)
        self.assertEqual(original.amount_residual, original_amount - 10.0)
        self.assertEqual(credit.amount_residual, 0.0)
        self.assertEqual(payment_model.search_count([]), payments_before)

        second_payload = {
            'charge_id': charge.id, 'amount': 15.0,
            'reason': 'Synthetic correction revision two', 'request_key': 's11-credit-adjustment-two-' + str(charge.id),
        }
        second = settlement._operate('credit_lab_charge', second_payload, 's11-credit-op-two-' + str(charge.id))
        second_adjustment = self.root['ydental.lab.charge.adjustment'].browse(second['adjustment_id']).exists()
        self.assertEqual(second_adjustment.ydental_revision, 2)
        self.assertEqual(second['actually_refunded'], 0)
        self.assertEqual(self.root['ydental.lab.charge.adjustment'].sudo().search_count([
            ('ydental_charge_id', '=', charge.id)]), 2)

        moves_before_cap = self.root['account.move'].sudo().search_count([])
        with self.assertRaises(UserError):
            settlement._operate('credit_lab_charge', {
                'charge_id': charge.id, 'amount': original_amount - 24.99,
                'reason': 'Synthetic cumulative cap rejection',
                'request_key': 's11-credit-adjustment-over-cap-' + str(charge.id),
            }, 's11-credit-op-cap-' + str(charge.id))
        self.assertEqual(self.root['account.move'].sudo().search_count([]), moves_before_cap)
        self.assertEqual(self.root['ydental.lab.charge.adjustment'].sudo().search_count([
            ('ydental_charge_id', '=', charge.id)]), 2)
        self.assertEqual(payment_model.search_count([]), payments_before)
