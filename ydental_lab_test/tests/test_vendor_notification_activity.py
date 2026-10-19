from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError
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
        reassignee = new_test_user(
            root,
            name='S11 synthetic vendor activity reassignee',
            login='s11_vendor_activity_reassignee',
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_id=root.company.id,
            company_ids=[Command.set([root.company.id])],
        )
        ordinary_user = new_test_user(
            root,
            name='S11 synthetic vendor outbound reader',
            login='s11_vendor_outbound_reader',
            groups='ydental_base.ydental_base_group_user',
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

        mail_count = root['mail.mail'].sudo().search_count([])
        activity = self.env['ydental.followup.service']._create_source_activity(
            'ydental.lab.vendor', vendor.id, manager,
            'Supplier qualification expiry review',
            'Synthetic internal review activity; no external notification is sent.',
        )

        self.assertTrue(activity)
        self.assertEqual(activity.res_model_id.model, 'ydental.lab.vendor')
        self.assertEqual(activity.res_id, vendor.id)
        self.assertEqual(activity.user_id, manager)
        self.assertIn(activity, vendor.activity_ids)
        self.assertEqual(root['mail.mail'].sudo().search_count([]), mail_count)

        vendor_as_manager = vendor.with_user(manager)
        for method, kwargs in (
            ('message_post', {'body': 'No vendor email'}),
            ('message_notify', {'partner_ids': partner.ids, 'body': 'No external recipient'}),
            ('message_post_with_source', ('mail.mail_notification_layout',)),
            ('message_mail_with_source', ('mail.mail_notification_layout',)),
        ):
            with self.subTest(method=method), self.assertRaises(AccessError):
                if isinstance(kwargs, tuple):
                    getattr(vendor_as_manager, method)(*kwargs)
                else:
                    getattr(vendor_as_manager, method)(**kwargs)

        composer = root['mail.compose.message'].with_user(ordinary_user).with_context(
            default_model='ydental.lab.vendor',
            default_res_ids=[vendor.id],
            default_composition_mode='mass_mail',
        ).create({'composition_mode': 'mass_mail'})
        self.assertEqual(composer.model, 'ydental.lab.vendor')
        with self.assertRaises(AccessError):
            composer.action_send_mail()
        with self.assertRaises(AccessError):
            composer.action_schedule_message()

        template = root['mail.template'].sudo().create({
            'name': 'S11 synthetic blocked vendor email',
            'model_id': root['ir.model']._get_id('ydental.lab.vendor'),
            'subject': 'S11 synthetic notice',
            'body_html': '<p>S11 synthetic content</p>',
            'email_to': 'outside@example.invalid',
        })
        with self.assertRaises(AccessError):
            template.with_user(ordinary_user).send_mail(vendor.id, force_send=True)
        self.assertEqual(root['mail.mail'].sudo().search_count([]), mail_count)

        sms_count = root['sms.sms'].sudo().search_count([])
        sms_composer = root['sms.composer'].with_user(ordinary_user).create({
            'res_model': 'ydental.lab.vendor',
            'res_ids': repr([vendor.id]),
            'composition_mode': 'mass',
            'body': 'S11 synthetic message must not leave Odoo',
        })
        with self.assertRaises(AccessError):
            sms_composer.action_send_sms_mass_now()
        with self.assertRaises(AccessError):
            sms_composer.action_send_sms()
        with self.assertRaises(AccessError):
            sms_composer.action_schedule_message()
        self.assertEqual(root['sms.sms'].sudo().search_count([]), sms_count)

        activity.with_user(manager).write({'user_id': reassignee.id})
        activity.invalidate_recordset(['user_id', 'active', 'date_done'])
        self.assertEqual(activity.user_id, reassignee)
        activity.with_user(reassignee).action_feedback(feedback='Synthetic review completed internally')
        activity.invalidate_recordset(['active', 'date_done', 'feedback'])
        self.assertFalse(activity.active)
        self.assertTrue(activity.date_done)
        self.assertEqual(activity.feedback, 'Synthetic review completed internally')
        self.assertEqual(root['mail.mail'].sudo().search_count([]), mail_count)
