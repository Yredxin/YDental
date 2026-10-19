from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestVendorNotificationActivity(TransactionCase):
    def test_supplier_expiry_activity_uses_native_vendor_thread(self):
        root = self.env['base'].sudo().env
        manager = new_test_user(
            root,
            name='S11 synthetic vendor activity manager',
            login='s11_vendor_activity_manager',
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_id=root.company.id,
            company_ids=[Command.set([root.company.id])],
        )
        partner = root['res.partner'].create({
            'name': 'S11 synthetic activity vendor',
        })
        vendor = root['ydental.lab.vendor'].with_user(manager).create({
            'partner_id': partner.id,
            'company_ids': [Command.set([self.env.company.id])],
            'category': 'other',
            'qualification_reference': 'S11-SYNTH-ACTIVITY',
            'valid_until': fields.Date.context_today(self) + timedelta(days=1),
        })

        activity = self.env['ydental.followup.service']._create_source_activity(
            'ydental.lab.vendor', vendor.id, self.env.user,
            'Supplier qualification expiry review',
            'Synthetic internal review activity; no external notification is sent.',
        )

        self.assertTrue(activity)
        self.assertEqual(activity.res_model_id.model, 'ydental.lab.vendor')
        self.assertEqual(activity.res_id, vendor.id)
        self.assertEqual(activity.user_id, self.env.user)
        self.assertIn(activity, vendor.activity_ids)
