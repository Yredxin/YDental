from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.ydental_treatment_test.tests.common import key, bind

from .test_free_rework_lifecycle import TestFreeReworkLifecycle


@tagged('post_install', '-at_install')
class TestPostFitRepair(TestFreeReworkLifecycle):
    """A completed fit opens a separate draft repair cycle without rewriting history."""

    allow_inherited_tests_method = False

    def test_completed_fit_opens_linked_unclassified_repair_from_reason_wizard(self):
        source_event = self._real_treatment_event()
        vendor, _cooperation, purchase_line = self._vendor_and_purchase_cost()
        product, lot_id = self._prosthesis_product_and_lot()
        order = self.group.env['ydental.lab.order'].create({
            'name': 'S11 synthetic fitted post-fit repair source',
            'ydental_source_event_id': source_event.id,
            'ydental_vendor_id': vendor.id,
            'ydental_product_id': product.id,
            'ydental_lot_id': lot_id,
            'ydental_purchase_line_id': purchase_line.id,
            'ydental_quantity': 1,
            'ydental_teeth': [16],
            'ydental_material': 'Synthetic ceramic',
            'ydental_instructions': 'Synthetic original laboratory cycle',
            'ydental_internal_code': 'S11-POSTFIT-' + key()[:12],
            'ydental_responsible_id': self.users['manager'].id,
        })
        lab = self.group.env['ydental.lab.service']
        for operation in ('send', 'processing', 'receive', 'putaway'):
            lab._operate(operation, {'order_id': order.id}, 's11-postfit-%s-%s' % (operation, order.id))
        order.invalidate_recordset()
        self.assertEqual(order.state, 'available')

        fit_event = self._another_real_treatment_event(
            order.ydental_patient_id.id, 'Synthetic actual service for post-fit repair fixture')
        fit_result = lab._operate('fit', {
            'order_id': order.id, 'fit_event_id': fit_event.id,
        }, 's11-postfit-fit-%s' % order.id)
        order.invalidate_recordset()
        self.assertEqual((fit_result['state'], order.state), ('done', 'done'))
        parent_followup = order.ydental_followup_id
        original_fit_stock_event = order.ydental_fit_inventory_event_id
        original_fee = order.ydental_source_fee_id
        original_purchase_line = order.ydental_purchase_line_id

        ordinary_reader = bind(self, self.users['reader']).env['ydental.lab.service']
        with self.assertRaises(AccessError):
            ordinary_reader._operate('post_fit_repair', {
                'order_id': order.id, 'reason': 'Unauthorized repair attempt',
            }, 's11-postfit-denied-%s' % order.id)
        with self.assertRaises(ValidationError):
            lab._operate('post_fit_repair', {'order_id': order.id, 'reason': ''},
                         's11-postfit-empty-%s' % order.id)

        wizard_action = order.action_open_post_fit_repair_wizard()
        self.assertEqual(wizard_action['res_model'], 'ydental.lab.post.fit.repair')
        self.assertEqual(wizard_action['target'], 'new')
        order_view = self.env.ref('ydental_lab.ydental_lab_order_view_form').arch_db
        wizard_view = self.env.ref('ydental_lab.ydental_lab_post_fit_repair_view_form').arch_db
        self.assertIn('action_open_post_fit_repair_wizard', order_view)
        self.assertIn('name="reason"', wizard_view)
        self.assertTrue(self.env['ydental.lab.post.fit.repair']._fields['reason'].required)
        wizard = self.group.env['ydental.lab.post.fit.repair'].create({
            'order_id': order.id,
            'reason': 'Synthetic patient-reported concern after the original fit',
        })
        action = wizard.action_apply()
        repair = self.root['ydental.lab.order'].browse(action['res_id']).exists()
        replay = wizard.action_apply()
        self.assertEqual(replay['res_id'], repair.id)
        self.assertEqual(repair.state, 'draft')
        self.assertEqual(repair.ydental_parent_order_id, order)
        self.assertTrue(repair.ydental_post_fit_repair)
        self.assertEqual(repair.ydental_rework_no, 1)
        self.assertFalse(repair.ydental_rework_kind)
        self.assertFalse(repair.ydental_purchase_line_id)
        self.assertFalse(repair.ydental_source_fee_id)
        self.assertFalse(repair.ydental_charge_ids)
        self.assertEqual(order.state, 'done')
        self.assertEqual(order.ydental_fit_event_id, fit_event)
        self.assertEqual(order.ydental_fit_inventory_event_id, original_fit_stock_event)
        self.assertEqual(order.ydental_source_fee_id, original_fee)
        self.assertEqual(order.ydental_purchase_line_id, original_purchase_line)
        self.assertEqual(parent_followup.state, 'closed')

        repair_event = self.root['ydental.lab.event'].sudo().search([
            ('ydental_order_id', '=', repair.id), ('ydental_kind', '=', 'post_fit_repair'),
        ], limit=1)
        self.assertTrue(repair_event)
        self.assertEqual(repair_event.ydental_reason, wizard.reason)
        self.assertFalse(repair_event.ydental_purchase_line_id)
        self.assertFalse(repair_event.ydental_patient_fee_id)

        with self.assertRaises(UserError):
            lab._operate('post_fit_repair', {
                'order_id': order.id, 'reason': 'A second simultaneous draft is not allowed',
            }, 's11-postfit-second-%s' % order.id)
        self.assertEqual(self.root['ydental.lab.order'].search_count([
            ('ydental_parent_order_id', '=', order.id), ('ydental_post_fit_repair', '=', True),
        ]), 1)

        # The repair category is a deliberate user choice after opening the
        # draft; it is never copied from the completed cycle.
        manager_repair = self.group.env['ydental.lab.order'].browse(repair.id)
        manager_repair.write({'ydental_rework_kind': 'free'})
        self.assertEqual(manager_repair.ydental_rework_kind, 'free')
