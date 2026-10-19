"""Additional-cost rework with an independently confirmed no-patient-fee outcome."""
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.ydental_treatment_test.tests.common import bind

from .test_free_rework_lifecycle import TestFreeReworkLifecycle, _action_key, key


@tagged('post_install', '-at_install')
class TestNoPatientFeeRework(TestFreeReworkLifecycle):
    # Reuse the real synthetic S06/S08, vendor and inventory fixture helpers,
    # but do not collect the parent class's separate lifecycle tests here.
    allow_inherited_tests_method = False

    def test_additional_supplier_cost_with_frozen_no_patient_fee_branch(self):
        source_event = self._real_treatment_event()
        vendor, cooperation, original_line = self._vendor_and_purchase_cost()
        product, lot_id = self._prosthesis_product_and_lot()
        manager = self.users['manager']
        store = self.stores[0]
        order = self.group.env['ydental.lab.order'].create({
            'name': 'S11 synthetic parent for no-fee additional rework',
            'ydental_source_event_id': source_event.id,
            'ydental_vendor_id': vendor.id,
            'ydental_product_id': product.id,
            'ydental_lot_id': lot_id,
            'ydental_purchase_line_id': original_line.id,
            'ydental_quantity': 1,
            'ydental_teeth': [16],
            'ydental_material': 'Synthetic ceramic',
            'ydental_instructions': 'Synthetic laboratory work only',
            'ydental_internal_code': 'S11-NOFEE-PARENT-' + key(),
            'ydental_responsible_id': manager.id,
            'ydental_planned_at': fields.Datetime.now(),
        })
        lab = self.group.env['ydental.lab.service']
        lab._operate('send', {'order_id': order.id}, _action_key('no-fee-parent-send', order.id))
        lab._operate('processing', {'order_id': order.id}, _action_key('no-fee-parent-processing', order.id))
        lab._operate('receive', {'order_id': order.id}, _action_key('no-fee-parent-receive', order.id))
        lab._operate('putaway', {'order_id': order.id}, _action_key('no-fee-parent-putaway', order.id))
        order.write({
            'ydental_rework_kind': 'additional',
            'ydental_exception_reason': 'Synthetic additional supplier work, no patient charge',
        })
        opened = lab._operate(
            'rework', {'order_id': order.id}, _action_key('no-fee-rework', order.id))
        child = self.root['ydental.lab.order'].browse(opened['repair_order_id']).exists()
        self.assertTrue(child and child.ydental_parent_order_id == order)
        self.assertEqual(child.ydental_rework_kind, 'additional')
        with self.assertRaises(UserError):
            lab._operate('send', {'order_id': child.id}, _action_key('no-fee-premature-send', child.id))

        incoming_type = self.root['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming'), ('warehouse_id.company_id', '=', store.company_id.id),
        ], limit=1)
        service_product = self.root['product.product'].sudo().browse(original_line.product_id.id)
        purchase = self.root['purchase.order'].with_user(manager).with_company(store.company_id).create({
            'partner_id': vendor.partner_id.id,
            'company_id': store.company_id.id,
            'currency_id': store.company_id.currency_id.id,
            'picking_type_id': incoming_type.id,
            'date_order': fields.Datetime.now(),
            'order_line': [Command.create({
                'name': 'Synthetic distinct additional rework supplier cost',
                'product_id': service_product.id,
                'product_qty': 1,
                'uom_id': original_line.uom_id.id,
                'price_unit': 18.50,
                'date_planned': fields.Datetime.now(),
            })],
        })
        purchase.button_confirm()
        added_cost_line = purchase.order_line.ensure_one()
        with self.assertRaises(AccessError):
            child.with_user(self.users['frontdesk']).write({
                'ydental_no_patient_fee_declaration': True,
                'ydental_no_patient_fee_confirmation_reason': 'No commercial authority',
            })
        child.write({
            'ydental_purchase_line_id': added_cost_line.id,
            'ydental_no_patient_fee_declaration': True,
            'ydental_no_patient_fee_confirmation_reason': (
                'Synthetic supplier correction paid by clinic; no patient fee agreed'),
        })
        self.assertFalse(child.ydental_zero_supplier_cost_confirmed)
        self.assertFalse(child.ydental_additional_terms_frozen)

        # Medical authority alone cannot freeze the commercial no-fee decision.
        frontdesk_lab = bind(self, self.users['frontdesk']).env['ydental.lab.service']
        with self.assertRaises(AccessError):
            frontdesk_lab._operate(
                'confirm_no_patient_fee', {'order_id': child.id},
                _action_key('no-fee-denied', child.id))

        invoice_count = self.root['account.move'].sudo().search_count([
            ('move_type', '=', 'out_invoice'),
        ])
        payment_count = self.root['account.payment'].sudo().search_count([])
        treatment_event_count = self.root['ydental.treatment.event'].sudo().search_count([])
        no_fee_key = _action_key('no-fee-confirm', child.id)
        result = lab._operate('confirm_no_patient_fee', {'order_id': child.id}, no_fee_key)
        self.assertEqual(result['no_patient_fee_confirmed'], True)
        repeated = lab._operate('confirm_no_patient_fee', {'order_id': child.id}, no_fee_key)
        self.assertEqual(repeated['result'], 'already_accepted')
        child.invalidate_recordset()
        self.assertTrue(child.ydental_no_patient_fee_confirmed)
        self.assertEqual(child.ydental_no_patient_fee_actor_id, manager)
        self.assertTrue(child.ydental_no_patient_fee_at)
        self.assertEqual(
            child.ydental_no_patient_fee_reason,
            'Synthetic supplier correction paid by clinic; no patient fee agreed')
        self.assertFalse(child.ydental_additional_terms_frozen)
        self.assertFalse(child.ydental_charge_ids)

        with self.assertRaises(AccessError):
            child.write({'ydental_no_patient_fee_declaration': False})
        with self.assertRaises(AccessError):
            child.write({'ydental_no_patient_fee_confirmed': False})
        with self.assertRaises(UserError):
            lab._operate(
                'approve_charge_terms', {'order_id': child.id},
                _action_key('no-fee-cannot-price', child.id))

        lab._operate('send', {'order_id': child.id}, _action_key('no-fee-child-send', child.id))
        child.invalidate_recordset()
        sent = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', child.id), ('ydental_kind', '=', 'sent'),
        ], limit=1)
        self.assertEqual(child.state, 'sent')
        self.assertEqual(sent.ydental_purchase_line_id, added_cost_line)
        self.assertEqual(sent.ydental_vendor_cost, 18.50)
        self.assertEqual(sent.ydental_purchase_cost_snapshot['line_id'], added_cost_line.id)
        self.assertFalse(sent.ydental_patient_fee_id)
        self.assertEqual(sent.ydental_patient_fee_amount, 0)
        self.assertFalse(child.ydental_charge_ids)
        self.assertEqual(self.root['account.move'].sudo().search_count([
            ('move_type', '=', 'out_invoice'),
        ]), invoice_count)
        self.assertEqual(self.root['account.payment'].sudo().search_count([]), payment_count)
        self.assertEqual(
            self.root['ydental.treatment.event'].sudo().search_count([]), treatment_event_count,
            'the no-fee path must not create a treatment-event proxy',
        )
        audit_event = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', child.id), ('ydental_kind', '=', 'no_patient_fee_confirmed'),
        ], limit=1)
        self.assertEqual(audit_event.ydental_actor_id, manager)
        self.assertEqual(audit_event.ydental_reason, child.ydental_no_patient_fee_reason)
        self.assertEqual(cooperation.ydental_vendor_id, vendor)
