"""T16 normal provenance and cancellation boundaries; no synthetic job rows.

Worker tests use Odoo's registry_test_mode and native TestCursor savepoints.
They are MODEL tests, not independent connections or committed competition.
The controlled transport's acceptance is simulated, never patient delivery.
"""

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.ydental_followup.models import ydental_followup_service as notification
from odoo.addons.ydental_treatment_test.tests.common import bind, key, make_slot, qualify

from .test_free_rework_lifecycle import TestFreeReworkLifecycle


@tagged('post_install', '-at_install')
class TestLabCancellation(TestFreeReworkLifecycle):
    allow_inherited_tests_method = False

    def _new_order(self, creator=None, with_cost=True):
        source = self._real_treatment_event()
        vendor, _cooperation, line = self._vendor_and_purchase_cost()
        product, lot_id = self._prosthesis_product_and_lot()
        patient = source.ydental_patient_id
        self.group.env['ydental.patient.service']._operate('edit', {
            'patient_id': patient.id, 'version': patient.ydental_version,
            'values': {'email': 's11-cancel-' + key() + '@example.invalid'},
        }, key())
        self.group.env['ydental.followup.service']._operate('set_preference', {
            'patient_id': patient.id, 'opt_out': False, 'preferred_channel': 'email',
        })
        values = {
            'name': 'S11 normal pre-putaway cancellation ' + key(),
            'ydental_source_event_id': source.id, 'ydental_vendor_id': vendor.id,
            'ydental_product_id': product.id, 'ydental_lot_id': lot_id,
            'ydental_quantity': 1, 'ydental_teeth': [16], 'ydental_material': 'Synthetic ceramic',
            'ydental_instructions': 'Synthetic cancellation integration',
            'ydental_internal_code': 'S11-CANCEL-' + key(),
            'ydental_responsible_id': self.users['manager'].id,
            'ydental_planned_at': fields.Datetime.now() + timedelta(days=2),
        }
        if with_cost:
            values['ydental_purchase_line_id'] = line.id
        actor = bind(self, creator) if creator else self.group
        return actor.env['ydental.lab.order'].create(values)

    def _reservation(self, order, days=2):
        start = fields.Datetime.now().replace(microsecond=0) + timedelta(days=days)
        end = start + timedelta(minutes=5)
        make_slot(self, self.group, self.stations[0][0], start, end)
        return qualify(self, patient_id=order.ydental_patient_id.id, service=self.group, start=start, end=end)

    def _link(self, order, reservation):
        self.group.env['ydental.followup.service']._operate('link_appointment', {
            'followup_id': order.ydental_followup_id.id, 'appointment_id': reservation['id'],
        })
        return self._jobs(order).filtered(lambda row: row.ydental_state == 'pending').ensure_one()

    def _jobs(self, order):
        return self.root['ydental.notification.job'].sudo().search([
            ('ydental_followup_id', '=', order.ydental_followup_id.id),
        ], order='id')

    def _send_receive(self, order):
        lab = bind(self, self.users['frontdesk']).env['ydental.lab.service']
        for operation in ('send', 'receive'):
            lab._operate(operation, {'order_id': order.id}, key())
        order.invalidate_recordset()
        return lab

    def _policy(self, lead=0):
        return self.group.env['ydental.followup.policy'].create({
            'name': 'Synthetic cancellation notification policy', 'ydental_store_id': self.stores[0].id,
            'ydental_enabled': True, 'ydental_channel_mode': 'controlled_test_sink',
            'ydental_lead_hours': lead, 'ydental_daily_limit': 5,
            'ydental_quiet_start': '00:00', 'ydental_quiet_end': '00:01',
        })

    def _drive_notification(self, job):
        self.env.flush_all()
        # Native test harness preserves rollback-only fixture isolation. This
        # deliberately makes no independent-connection or commit claim.
        with self.registry_test_mode():
            notification._dispatch_notification_jobs(self.env.cr.dbname, [job.id])
        self.env.invalidate_all()

    def test_opening_without_followup_or_warehouse_grant_creates_one_waiting_plan(self):
        clinician = self.users['doctor']
        order = self._new_order(creator=clinician, with_cost=False)
        service = bind(self, clinician).env['ydental.followup.service']
        levels = service.env['ydental.access.service']._levels(
            service.env['ydental.access.service']._membership(clinician.id, self.stores[0].id))
        self.assertEqual((levels['followup'], levels['warehouse']), ('none', 'none'))
        row = order.sudo().ydental_followup_id
        self.assertEqual((row.ydental_lab_order_id, row.ydental_lab_contact_stage, row.state),
                         (order.id, 'waiting', 'planned'))
        self.assertEqual(row.ydental_source_event_id, order.sudo().ydental_source_event_id)
        self.assertEqual(self.root['ydental.followup'].sudo().search_count([
            ('ydental_lab_order_id', '=', order.id), ('ydental_lab_cycle_key', '=', 'order'),
        ]), 1)
        self.assertFalse(self._jobs(order))
        self.assertFalse(self.root['mail.activity'].search([
            ('res_model', '=', 'ydental.followup'), ('res_id', '=', row.id),
        ]))
        with self.assertRaises(AccessError):
            service._operate('contact', {'followup_id': row.id, 'method': 'phone', 'outcome': 'delivered'})
        with self.assertRaises(AccessError):
            bind(self, clinician).env['ydental.lab.service']._operate('cancel', {
                'order_id': order.id, 'reason': 'A clinician alone cannot perform warehouse cancellation',
            }, key())

    def test_waiting_plan_reschedules_without_arrival_job_and_blocks_early_completion(self):
        order = self._new_order()
        service = self.group.env['ydental.followup.service']
        row = order.ydental_followup_id
        service._operate('reschedule', {
            'followup_id': row.id, 'planned_at': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=4)),
        })
        self.assertFalse(self._jobs(order))
        with self.assertRaises(UserError):
            service._operate('contact', {'followup_id': row.id, 'method': 'phone', 'outcome': 'delivered'})
        with self.assertRaises(UserError):
            service._operate('complete', {'followup_id': row.id, 'event_id': order.ydental_source_event_id.id,
                                          'confirmed_unlinked': True, 'reason': 'No physical stock yet'})
        service._operate('close', {'followup_id': row.id, 'reason': 'Review waiting plan'})
        service._operate('reopen', {'followup_id': row.id, 'reason': 'Continue waiting'})
        self.assertEqual(row.state, 'planned')
        self.assertFalse(self._jobs(order))

    def test_waiting_reservation_contact_never_activates_laboratory_arrival(self):
        order = self._new_order()
        self._policy()
        reservation = self._reservation(order)
        job = self._link(order, reservation)
        row = order.ydental_followup_id
        service = self.group.env['ydental.followup.service']
        service._operate('contact', {'followup_id': row.id, 'method': 'phone', 'outcome': 'delivered'})
        self.assertEqual((row.state, row.ydental_lab_contact_stage), ('notified', 'waiting'))
        self.assertEqual(job.ydental_state, 'cancelled')
        self.assertEqual(row.ydental_deadline_at, row.ydental_appointment_at)
        self.assertFalse(order.ydental_receipt_at)
        with self.assertRaises(UserError):
            service._operate('complete', {'followup_id': row.id, 'event_id': order.ydental_source_event_id.id,
                                          'confirmed_unlinked': True, 'reason': 'An appointment is not put-away'})

    def test_real_reservation_pending_is_cancelled_after_receipt_without_reversing_history(self):
        order = self._new_order()
        self._policy()
        row = order.ydental_followup_id
        reservation = self._reservation(order)
        job = self._link(order, reservation)
        self.assertEqual((job.ydental_event_type, job.ydental_state, job.ydental_attempt_count),
                         ('appointment_reminder', 'pending', 0))
        self.assertEqual(job.ydental_source_res_id, row.id)
        self.assertEqual(job.ydental_source_version, row.ydental_schedule_version)
        warehouse = self._send_receive(order)
        receipt = (order.ydental_receipt_at, order.ydental_receipt_actor_id.id)
        sent = self.root['ydental.lab.event'].search([
            ('ydental_order_id', '=', order.id), ('ydental_kind', '=', 'sent'),
        ]).ensure_one()
        snapshot = sent.ydental_purchase_cost_snapshot
        patient_fee = order.ydental_source_fee_id
        fee_amount = patient_fee.ydental_amount
        before_stock = self._on_hand(order.ydental_lot_id.id)
        before_version = row.ydental_schedule_version
        before_mail = self.root['mail.mail'].search_count([])
        before_sms = self.root['sms.sms'].search_count([])
        warehouse._operate('cancel', {'order_id': order.id, 'reason': 'Received package not put away; verify disposition'}, key())
        self.assertEqual(order.state, 'cancelled')
        self.assertEqual((order.ydental_receipt_at, order.ydental_receipt_actor_id.id), receipt)
        self.assertFalse(order.ydental_inventory_event_id)
        self.assertFalse(order.ydental_fit_event_id)
        self.assertEqual(self._on_hand(order.ydental_lot_id.id), before_stock)
        self.assertEqual(sent.ydental_purchase_cost_snapshot, snapshot)
        self.assertEqual((order.ydental_source_fee_id, patient_fee.ydental_amount), (patient_fee, fee_amount))
        self.assertEqual((row.state, row.ydental_lab_contact_stage, job.ydental_state),
                         ('closed', 'stopped', 'cancelled'))
        self.assertGreater(row.ydental_schedule_version, before_version)
        self.assertEqual(job.ydental_attempt_count, 0)
        physical = self.root['mail.activity'].search([
            ('res_model', '=', 'ydental.lab.order'), ('res_id', '=', order.id),
            ('summary', '=', 'Laboratory cancellation: physical and financial review'), ('active', '=', True),
        ]).ensure_one()
        communication = self.root['mail.activity'].search([
            ('res_model', '=', 'ydental.followup'), ('res_id', '=', row.id),
            ('summary', '=', 'Follow-up contact required'), ('active', '=', True),
        ]).ensure_one()
        self.assertEqual((physical.user_id, communication.user_id),
                         (self.users['frontdesk'], row.ydental_responsible_id))
        self.assertNotIn('42.75', physical.note)
        self.assertNotIn('137.25', physical.note)
        physical.with_user(self.users['frontdesk']).action_feedback(feedback='Synthetic package location verified; financial review remains separate')
        self.assertFalse(physical.active)
        self.assertEqual(self.root['mail.mail'].search_count([]), before_mail)
        self.assertEqual(self.root['sms.sms'].search_count([]), before_sms)
        service = self.group.env['ydental.followup.service']
        for operation, payload in (
            ('reopen', {'reason': 'Cannot revive cancelled arrival notices'}),
            ('contact', {'method': 'phone', 'outcome': 'delivered'}),
            ('record_arrival', {'arrival_id': 99999991}),
        ):
            with self.subTest(operation=operation), self.assertRaises(UserError):
                service._operate(operation, {'followup_id': row.id, **payload})
        with self.assertRaises(UserError):
            warehouse._operate('putaway', {'order_id': order.id}, key())

    def _assert_notification_history_survives(self, timeout):
        order = self._new_order()
        policy = self._policy(lead=168)
        row = order.ydental_followup_id
        reservation = self._reservation(order)
        job = self._link(order, reservation)
        if timeout:
            with patch.object(type(self.group.env['ydental.followup.service']), '_send_transport',
                              side_effect=TimeoutError('simulated provider uncertainty')):
                self._drive_notification(job)
            self.assertEqual((job.ydental_state, job.ydental_attempt_count), ('unknown', 1))
        else:
            self._drive_notification(job)
            self.assertEqual((job.ydental_state, job.ydental_attempt_count), ('accepted', 1))
            self.assertEqual(row.state, 'notified')
        previous = (job.ydental_state, job.ydental_request_id, job.ydental_attempt_count)
        policy.write({'ydental_lead_hours': 0})
        start = fields.Datetime.now().replace(microsecond=0) + timedelta(days=3)
        end = start + timedelta(minutes=5)
        make_slot(self, self.group, self.stations[0][0], start, end)
        entitlement = self.root['ydental.intake.entitlement'].browse(reservation['id'])
        self.group._operate('reschedule', {
            'record_id': entitlement.id, 'version': entitlement.ydental_version,
            'mapping_id': self.mappings[0][0].id, 'start': fields.Datetime.to_string(start),
            'end': fields.Datetime.to_string(end), 'reason': 'Actual reservation moved before lab cancellation',
        }, key())
        pending = self._jobs(order).filtered(lambda candidate: candidate.ydental_state == 'pending').ensure_one()
        self.assertNotEqual(pending, job)
        warehouse = self._send_receive(order)
        warehouse._operate('cancel', {'order_id': order.id, 'reason': 'Preserve earlier notification outcome'}, key())
        self.assertEqual((job.ydental_state, job.ydental_request_id, job.ydental_attempt_count), previous)
        self.assertEqual(pending.ydental_state, 'cancelled')
        self.assertEqual(row.state, 'closed')

    def test_sent_reminder_survives_cancellation(self):
        self._assert_notification_history_survives(timeout=False)

    def test_unknown_request_survives_cancellation_without_another_attempt(self):
        self._assert_notification_history_survives(timeout=True)

    def test_missing_review_activity_rolls_back_order_plan_jobs_and_receipt(self):
        order = self._new_order()
        self._policy()
        job = self._link(order, self._reservation(order))
        warehouse = self._send_receive(order)
        row = order.ydental_followup_id
        prior = (order.state, row.state, row.ydental_schedule_version, job.ydental_state)
        service_type = type(warehouse.env['ydental.followup.service'])
        with patch.object(service_type, '_create_source_activity', return_value=False), self.assertRaises(UserError):
            warehouse._operate('cancel', {'order_id': order.id, 'reason': 'Task creation must be atomic'}, key())
        self.env.invalidate_all()
        self.assertEqual((order.state, row.state, row.ydental_schedule_version, job.ydental_state), prior)
        self.assertTrue(order.ydental_receipt_at)
        self.assertFalse(order.ydental_inventory_event_id)

    def test_putaway_activates_original_plan_once_and_available_cannot_cancel(self):
        order = self._new_order()
        self._policy()
        row = order.ydental_followup_id
        appointment_job = self._link(order, self._reservation(order))
        warehouse = self._send_receive(order)
        warehouse._operate('putaway', {'order_id': order.id}, key())
        self.assertEqual((order.state, order.ydental_followup_id, row.ydental_lab_contact_stage),
                         ('available', row, 'ready'))
        self.assertEqual(appointment_job.ydental_state, 'cancelled')
        arrival = self._jobs(order).filtered(lambda job: job.ydental_state == 'pending').ensure_one()
        self.assertEqual(arrival.ydental_event_type, 'lab_arrival')
        before = (row.ydental_schedule_version, self._jobs(order).ids)
        warehouse.env['ydental.followup.service']._create_passive_from_lab_order(
            order, order.ydental_planned_at, order.ydental_responsible_id.id)
        self.assertEqual((row.ydental_schedule_version, self._jobs(order).ids), before)
        with self.assertRaises(UserError):
            warehouse._operate('cancel', {'order_id': order.id, 'reason': 'Stock requires physical exception disposition'}, key())
        self.assertEqual(self._on_hand(order.ydental_lot_id.id), 1)

    def test_manually_closed_plan_is_not_reopened_by_putaway(self):
        order = self._new_order()
        self._policy()
        row = order.ydental_followup_id
        appointment_job = self._link(order, self._reservation(order))
        self.group.env['ydental.followup.service']._operate('close', {
            'followup_id': row.id, 'reason': 'Synthetic explicit manual closure before stock',
        })
        warehouse = self._send_receive(order)
        warehouse._operate('putaway', {'order_id': order.id}, key())
        self.assertEqual((order.state, row.state, row.ydental_lab_contact_stage),
                         ('available', 'closed', 'ready'))
        self.assertEqual(appointment_job.ydental_state, 'cancelled')
        self.assertFalse(self._jobs(order).filtered(lambda candidate: candidate.ydental_state == 'pending'))
        self.assertEqual(row.ydental_closed_reason, 'Synthetic explicit manual closure before stock')

    def test_actual_reservation_cancellation_blocks_a_still_waiting_source(self):
        order = self._new_order()
        self._policy()
        reservation = self._reservation(order)
        job = self._link(order, reservation)
        entitlement = self.root['ydental.intake.entitlement'].browse(reservation['id'])
        self.group._operate('cancel', {
            'record_id': entitlement.id, 'version': entitlement.ydental_version,
            'reason': 'Synthetic actual booking cancellation before laboratory stock',
        }, key())
        service = self.group.env['ydental.followup.service']
        self.assertFalse(service._lab_job_allowed(job))
        service._schedule(order.ydental_followup_id)
        self.assertEqual(job.ydental_state, 'cancelled')
        self.assertFalse(self._jobs(order).filtered(lambda candidate: candidate.ydental_state == 'pending'))
        with self.assertRaises(UserError):
            service._operate('contact', {'followup_id': order.ydental_followup_id.id,
                                         'method': 'phone', 'outcome': 'delivered'})

    def test_draft_responsible_and_date_follow_plan_without_granting_contact_write(self):
        order = self._new_order(creator=self.users['doctor'], with_cost=False)
        self.admin._grant(self.users['reader'].id, self.stores[0].id, {'followup': 'write', 'medical': 'read'})
        planned = fields.Datetime.now() + timedelta(days=5)
        order.write({'ydental_responsible_id': self.users['reader'].id, 'ydental_planned_at': planned})
        row = order.sudo().ydental_followup_id
        self.assertEqual((row.ydental_responsible_id, row.ydental_planned_at), (self.users['reader'], planned))
        self.assertFalse(self._jobs(order))
        with self.assertRaises(AccessError):
            order.write({'ydental_followup_id': row.id})
        with self.assertRaises(AccessError):
            row.with_user(self.users['reader']).write({'ydental_lab_contact_stage': 'ready'})

    def test_order_external_message_paths_and_forged_context_cannot_queue_delivery(self):
        order = self._new_order()
        external = self.root['res.partner'].create({
            'name': 'Synthetic external laboratory recipient', 'email': 'outside@example.invalid',
        })
        before_mail = self.root['mail.mail'].search_count([])
        before_sms = self.root['sms.sms'].search_count([])
        for name, args, kwargs in (
            ('message_post', (), {'body': 'No external order content', 'partner_ids': external.ids}),
            ('message_notify', (), {'partner_ids': external.ids, 'body': 'No external notification'}),
            ('message_post_with_source', ('mail.mail_notification_layout',), {}),
            ('message_mail_with_source', ('mail.mail_notification_layout',), {}),
        ):
            with self.subTest(name=name), self.assertRaises(AccessError):
                getattr(order, name)(*args, **kwargs)
        with self.assertRaises(AccessError):
            order.with_context(ydental_lab_order_activity_done=True).message_post(body='A client boolean is not a server token')
        composer = order.env['mail.compose.message'].with_context(
            default_model='ydental.lab.order', default_res_ids=order.ids,
            default_composition_mode='mass_mail',
        ).create({'composition_mode': 'mass_mail'})
        for action in (composer.action_send_mail, composer.action_schedule_message):
            with self.assertRaises(AccessError):
                action()
        template = self.root['mail.template'].create({
            'name': 'Synthetic blocked order email', 'model_id': self.root['ir.model']._get_id('ydental.lab.order'),
            'subject': 'No external order mail', 'body_html': '<p>Not sent</p>',
            'email_to': 'outside@example.invalid',
        })
        with self.assertRaises(AccessError):
            template.with_user(self.users['manager']).send_mail(order.id, force_send=True)
        sms = order.env['sms.composer'].create({
            'res_model': 'ydental.lab.order', 'res_ids': repr(order.ids),
            'composition_mode': 'mass', 'body': 'No external order SMS',
        })
        for action in (sms.action_send_sms_mass_now, sms.action_send_sms, sms.action_schedule_message):
            with self.assertRaises(AccessError):
                action()
        self.assertEqual(self.root['mail.mail'].search_count([]), before_mail)
        self.assertEqual(self.root['sms.sms'].search_count([]), before_sms)

    def test_order_internal_notifications_are_forced_to_inbox_and_filter_external_users(self):
        order = self._new_order()
        model_type = type(order)
        user = self.users['frontdesk']
        recipients = [
            {'id': user.partner_id.id, 'uid': user.id, 'notif': 'email'},
            {'id': self.root.ref('base.public_partner').id, 'uid': self.root.ref('base.public_user').id, 'notif': 'email'},
            {'id': 99999991, 'uid': False, 'notif': 'sms'},
        ]
        with (patch.object(model_type, '_notify_get_recipients', return_value=recipients),
              patch.object(model_type, '_notify_thread_by_inbox') as inbox,
              patch.object(model_type, '_notify_thread_by_email', side_effect=AssertionError('email path forbidden'))):
            result = order.with_context(ydental_lab_order_activity_done=True)._notify_thread(False)
        self.assertEqual(result, [dict(recipients[0], notif='inbox')])
        inbox.assert_called_once_with(False, result)

    def test_manual_default_null_stage_retains_normal_followup_behavior(self):
        order = self._new_order()
        service = self.group.env['ydental.followup.service']
        created = service._operate('create', {
            'patient_id': order.ydental_patient_id.id, 'source_event_id': order.ydental_source_event_id.id,
            'followup_type': 'post_visit', 'responsible_id': self.users['manager'].id,
            'planned_at': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=1)),
        })
        manual = self.root['ydental.followup'].browse(created['id'])
        self.assertFalse(manual.ydental_lab_contact_stage)
        self.assertFalse(manual.ydental_lab_order_id)
        manual.flush_recordset(['ydental_lab_contact_stage'])
        self.env.cr.execute('SELECT ydental_lab_contact_stage FROM ydental_followup WHERE id=%s', [manual.id])
        self.assertIsNone(self.env.cr.fetchone()[0])
        service._operate('contact', {'followup_id': manual.id, 'method': 'phone', 'outcome': 'delivered'})
        self.assertEqual(manual.state, 'notified')
        self.assertFalse(manual.ydental_lab_contact_stage)
        self.assertFalse(manual._fields['ydental_lab_contact_stage'].copy)
        self.assertTrue(manual._fields['ydental_lab_contact_stage'].readonly)
