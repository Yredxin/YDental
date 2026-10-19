"""Real-model S11 free laboratory rework and fit/follow-up separation chain."""
import base64
import secrets
from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    arrive_report, bind, handover_args, key, price, qualify, save_args, serving,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    execute_args, opened_actual, receive as receive_material, setup as treatment_setup,
)


def _action_key(label, record_id):
    return 's11-free-lifecycle-%s-%s' % (label, record_id)


@tagged('post_install', '-at_install')
class TestFreeReworkLifecycle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The shared S06/S08 fixture requires an explicit demo-supply policy;
        # limit the fixture override to this test class and retain native flow.
        cls.demo_policy_patch = patch.object(
            type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        cls.demo_policy_patch.start()
        cls.addClassCleanup(cls.demo_policy_patch.stop)

        root = cls.env['base'].sudo().env
        internal_users = root.ref('base.group_user')
        internal_users.write({'implied_ids': [
            Command.link(root.ref('stock.group_stock_multi_warehouses').id),
            Command.link(root.ref('stock.group_stock_multi_locations').id),
        ]})
        treatment_setup(cls)
        cls.users['manager'].write({
            'group_ids': [Command.link(cls.root.ref('purchase.group_purchase_manager').id)],
        })
        cls.admin._grant(cls.users['manager'].id, cls.stores[0].id, {
            'medical': 'write', 'price': 'write', 'warehouse': 'write', 'followup': 'write',
        })
        cls.admin._grant(cls.users['frontdesk'].id, cls.stores[0].id, {
            'medical': 'write', 'warehouse': 'write',
        })
        cls.group = bind(cls, cls.users['manager'])
        cls.stock = cls.group.env['ydental.inventory.service']

    def _real_treatment_event(self):
        receive_material(self)
        price(self, amount=137.25)
        treatment, clinical, _queue, lease, execution, data, args = opened_actual(self)
        result = treatment._operate('execute', execute_args(self, args, actual=True), key())
        self.assertEqual(result['state'], 'confirmed')
        event = self.root['ydental.treatment.event'].browse(result['event_id']).exists()
        self.assertTrue(event and event.state == 'confirmed' and event.ydental_kind == 'treatment')
        self.assertEqual(event.ydental_execution_id, execution)
        clinical._operate('handover', handover_args(data, lease) | {
            'reason': 'Synthetic source treatment ended before the laboratory lifecycle',
        })
        queue._operate('exit', {
            'lease_id': lease['lease_id'], 'token': lease['token'],
        })
        return event

    def _another_real_treatment_event(self, patient_id, complaint):
        """Create another confirmed event for the same patient via S06/S08 services."""
        reservation = qualify(self, patient_id=patient_id)
        arrive_report(self, reservation)
        task = self.root['ydental.intake.task'].browse(reservation['task_id']).exists()
        queue, lease, execution = serving(self, task=task)
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {
            'execution_id': execution.id,
            'lease_id': lease['lease_id'],
            'lease_token': lease['token'],
        })
        document.update(clinical._operate('save', save_args(document, text=complaint)))
        args = {
            'execution_id': execution.id,
            'lease_id': lease['lease_id'],
            'lease_token': lease['token'],
            'document_id': document['document_id'],
            'document_version': document['version'],
        }
        result = queue.env['ydental.treatment.service']._operate(
            'execute', execute_args(self, args, actual=True), key())
        self.assertEqual(result['state'], 'confirmed')
        event = self.root['ydental.treatment.event'].browse(result['event_id']).exists()
        self.assertTrue(event and event.state == 'confirmed' and event.ydental_kind == 'treatment')
        self.assertEqual(event.ydental_patient_id.id, patient_id)
        self.assertEqual(event.ydental_execution_id, execution)
        clinical._operate('handover', handover_args(document, lease) | {
            'reason': 'Synthetic follow-up encounter ended after confirmed treatment',
        })
        # Clinical handover preserves the queue holder for workstation
        # continuity. This test ends the synthetic encounter explicitly so
        # the next real encounter can acquire the same station.
        queue._operate('exit', {
            'lease_id': lease['lease_id'], 'token': lease['token'],
        })
        return event

    def _vendor_and_purchase_cost(self):
        store = self.stores[0]
        partner = self.root['res.partner'].sudo().create({
            'name': 'S11 synthetic free-rework vendor ' + key(),
        })
        vendor = self.root['ydental.lab.vendor'].with_user(self.users['manager']).create({
            'partner_id': partner.id,
            'company_ids': [Command.set([store.company_id.id])],
            'category': 'other',
            'qualification_reference': 'S11-FREE-' + key(),
            'qualification_evidence': base64.b64encode(b'Synthetic qualification evidence').decode(),
            'qualification_evidence_name': 'synthetic.txt',
            'valid_until': fields.Date.context_today(self) + timedelta(days=30),
        })
        self.group.env['ydental.lab.service']._review_vendor(
            vendor, 'approved', 'Synthetic qualification review for free-rework test')
        cooperation = self.group.env['ydental.lab.cooperation'].create({
            'ydental_vendor_id': vendor.id, 'active': True,
        })

        token = secrets.token_hex(4).upper()
        incoming_type = self.root['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming'), ('warehouse_id.company_id', '=', store.company_id.id),
        ], limit=1)
        self.assertTrue(incoming_type, 'the S08 inventory fixture must provide the store incoming type')
        service_product = self.root['product.template'].sudo().create({
            'name': 'S11 synthetic free-rework supplier service ' + token,
            'type': 'service', 'purchase_ok': True, 'sale_ok': False,
            'uom_id': self.uom.id, 'company_id': store.company_id.id,
        }).product_variant_id
        purchase = self.root['purchase.order'].with_user(self.users['manager']).with_company(
            store.company_id).create({
                'partner_id': partner.id,
                'company_id': store.company_id.id,
                'currency_id': store.company_id.currency_id.id,
                'picking_type_id': incoming_type.id,
                'date_order': fields.Datetime.now(),
                'order_line': [Command.create({
                    'name': 'Synthetic confirmed original lab processing cost',
                    'product_id': service_product.id,
                    'product_qty': 1,
                    'uom_id': self.uom.id,
                    'price_unit': 42.75,
                    'date_planned': fields.Datetime.now() + timedelta(days=1),
                })],
            })
        purchase.button_confirm()
        return vendor, cooperation, purchase.order_line.ensure_one()

    def _prosthesis_product_and_lot(self):
        product = self.stock._operate('product', {
            'code': 'S11-FREE-' + key(),
            'name': 'S11 synthetic free-rework prosthesis',
            'kind': 'prosthesis',
            'stock_uom_id': self.uom.id,
            'issue_uom_id': self.uom.id,
            'step': 1,
            'specification': 'Synthetic fixture only',
        }, key())
        lot = self.stock._operate('lot', {
            'product_id': product['id'],
            'name': 'S11-FREE-LOT-' + key(),
            'expiration': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=45)),
        }, key())
        return self.root['product.product'].browse(product['id']).exists(), lot['id']

    def _on_hand(self, lot_id):
        store = self.stock._access()
        lot = self.stock._lot(lot_id, store)
        config = self.stock._config(store)
        return self.stock._quantity(lot, self.stock._location(config, lot.product_id))

    def test_real_free_rework_cycle_keeps_original_cost_and_separates_fit_from_followup(self):
        source_event = self._real_treatment_event()
        vendor, cooperation, purchase_line = self._vendor_and_purchase_cost()
        product, lot_id = self._prosthesis_product_and_lot()
        manager = self.users['manager']
        store = self.stores[0]

        order = self.group.env['ydental.lab.order'].create({
            'name': 'S11 synthetic original laboratory cycle',
            'ydental_source_event_id': source_event.id,
            'ydental_vendor_id': vendor.id,
            'ydental_product_id': product.id,
            'ydental_lot_id': lot_id,
            'ydental_purchase_line_id': purchase_line.id,
            'ydental_quantity': 1,
            'ydental_teeth': [16],
            'ydental_material': 'Synthetic ceramic',
            'ydental_instructions': 'Synthetic laboratory instructions only',
            'ydental_internal_code': 'S11-ORIGINAL-' + key(),
            'ydental_responsible_id': manager.id,
            'ydental_planned_at': fields.Datetime.now(),
        })
        lab = self.group.env['ydental.lab.service']

        lab._operate('send', {'order_id': order.id}, _action_key('send-parent', order.id))
        lab._operate('processing', {'order_id': order.id}, _action_key('processing-parent', order.id))
        lab._operate('receive', {'order_id': order.id}, _action_key('receive-parent', order.id))
        self.assertEqual(order.state, 'received')
        self.assertFalse(order.ydental_inventory_event_id)
        lab._operate('putaway', {'order_id': order.id}, _action_key('putaway-parent', order.id))
        order.invalidate_recordset()
        self.assertEqual(order.state, 'available')
        self.assertEqual(self._on_hand(lot_id), 1)
        self.assertTrue(order.ydental_followup_id)
        parent_followup = order.ydental_followup_id
        parent_sent = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', order.id), ('ydental_kind', '=', 'sent'),
        ], limit=1)
        self.assertEqual(parent_sent.ydental_purchase_line_id, purchase_line)
        self.assertEqual(parent_sent.ydental_vendor_cost, 42.75)
        self.assertEqual(parent_sent.ydental_purchase_cost_snapshot['line_id'], purchase_line.id)
        self.assertEqual(parent_sent.ydental_purchase_cost_snapshot['subtotal'], 42.75)
        self.assertEqual(parent_sent.ydental_patient_fee_id, order.ydental_source_fee_id)
        self.assertEqual(cooperation.ydental_vendor_id, vendor)

        order.write({
            'ydental_rework_kind': 'free',
            'ydental_exception_reason': 'Synthetic no-charge laboratory correction',
        })
        warehouse_lab = bind(self, self.users['frontdesk']).env['ydental.lab.service']
        returned = warehouse_lab._operate(
            'rework', {'order_id': order.id}, _action_key('rework-parent', order.id))
        child = self.root['ydental.lab.order'].browse(returned['repair_order_id']).exists()
        order.invalidate_recordset()
        parent_followup.invalidate_recordset()
        self.assertEqual(order.state, 'rework_returned')
        self.assertEqual(parent_followup.state, 'closed')
        self.assertEqual(child.ydental_parent_order_id, order)
        self.assertEqual(child.ydental_rework_kind, 'free')
        self.assertFalse(child.ydental_purchase_line_id)
        self.assertEqual(self._on_hand(lot_id), 0)
        self.assertEqual(self.root['ydental.lab.order'].sudo().search_count([
            ('ydental_purchase_line_id', '=', purchase_line.id),
        ]), 1)

        lab._operate('send', {'order_id': child.id}, _action_key('send-child', child.id))
        lab._operate('processing', {'order_id': child.id}, _action_key('processing-child', child.id))
        lab._operate('receive', {'order_id': child.id}, _action_key('receive-child', child.id))
        child.invalidate_recordset()
        self.assertEqual(child.state, 'received')
        self.assertFalse(child.ydental_inventory_event_id)
        lab._operate('putaway', {'order_id': child.id}, _action_key('putaway-child', child.id))
        child.invalidate_recordset()
        self.assertEqual(child.state, 'available')
        self.assertEqual(self._on_hand(lot_id), 1)
        child_sent = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', child.id), ('ydental_kind', '=', 'sent'),
        ], limit=1)
        self.assertFalse(child_sent.ydental_purchase_line_id)
        self.assertFalse(child_sent.ydental_purchase_cost_snapshot)
        self.assertEqual(child_sent.ydental_vendor_cost, 0)
        self.assertFalse(child_sent.ydental_patient_fee_id)
        self.assertEqual(child.ydental_source_fee_id, order.ydental_source_fee_id)
        self.assertEqual(self.root['ydental.lab.charge'].sudo().search_count([
            ('ydental_order_id', 'in', [order.id, child.id]),
        ]), 0, 'free rework must not create a second patient charge source')

        passive_rows = self.root['ydental.followup'].sudo().search([
            ('ydental_lab_order_id', '=', child.id),
        ])
        self.assertEqual(len(passive_rows), 1, 'the child cycle has exactly one passive arrival follow-up')
        child_followup = passive_rows.ensure_one()
        self.assertEqual(child.ydental_followup_id, child_followup)
        self.assertNotEqual(child_followup, parent_followup)
        self.assertNotEqual(child_followup.state, 'done')
        self.assertFalse(child_followup.ydental_completed_event_id)

        fit_event = self._another_real_treatment_event(
            source_event.ydental_patient_id.id, 'Synthetic actual prosthesis fit visit')
        lab._operate('fit', {
            'order_id': child.id, 'fit_event_id': fit_event.id,
        }, _action_key('fit-child', child.id))
        child.invalidate_recordset()
        child_followup.invalidate_recordset()
        self.assertEqual(child.state, 'done')
        self.assertEqual(child.ydental_fit_event_id, fit_event)
        self.assertTrue(child.ydental_fit_inventory_event_id)
        self.assertEqual(self._on_hand(lot_id), 0)
        self.assertNotEqual(child_followup.state, 'done', 'fitting the item must not close follow-up by itself')
        self.assertFalse(child_followup.ydental_completed_event_id)

        completion_event = self._another_real_treatment_event(
            source_event.ydental_patient_id.id, 'Synthetic separate follow-up completion visit')
        followup_service = self.group.env['ydental.followup.service']
        followup_service._operate('complete', {
            'followup_id': child_followup.id,
            'event_id': completion_event.id,
            'confirmed_unlinked': True,
            'reason': 'Synthetic same-patient actual encounter association confirmed',
        })
        child_followup.invalidate_recordset()
        self.assertEqual(child_followup.state, 'done')
        self.assertEqual(child_followup.ydental_completed_event_id, completion_event)
        self.assertNotEqual(child_followup.ydental_completed_event_id, child.ydental_fit_event_id)
        self.assertEqual(child.ydental_fit_event_id, fit_event)

        parent_sent.invalidate_recordset()
        child_sent.invalidate_recordset()
        self.assertEqual(parent_sent.ydental_purchase_line_id, purchase_line)
        self.assertFalse(child_sent.ydental_purchase_line_id)
        self.assertEqual(self.root['ydental.lab.order'].sudo().search_count([
            ('ydental_purchase_line_id', '=', purchase_line.id),
        ]), 1)
