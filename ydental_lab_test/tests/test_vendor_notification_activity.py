from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVendorNotificationActivity(TransactionCase):
    def test_supplier_expiry_activity_uses_native_vendor_thread(self):
        partner = self.env['res.partner'].sudo().create({
            'name': 'S11 synthetic activity vendor',
        })
        vendor = self.env['ydental.lab.vendor'].sudo().create({
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
