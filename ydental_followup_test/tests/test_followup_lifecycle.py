from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    bind,
    handover_args,
    key,
    make_slot,
    price,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    execute_args,
    opened_actual,
    receive,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    setup as treatment_setup,
)


@tagged('post_install', '-at_install')
class TestFollowupLifecycle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_policy_patch = patch.object(
            type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        cls.demo_policy_patch.start()
        cls.addClassCleanup(cls.demo_policy_patch.stop)
        # This populated scratch already has native warehouses. Set the stock
        # group prerequisites only inside this rollback-only Odoo test class,
        # matching the existing S08 integration fixture.
        internal_users = cls.env.ref('base.group_user')
        internal_users.write({'implied_ids': [
            Command.link(cls.env.ref('stock.group_stock_multi_warehouses').id),
            Command.link(cls.env.ref('stock.group_stock_multi_locations').id),
        ]})
        treatment_setup(cls)
        for store in cls.stores:
            cls.admin._grant(cls.users['manager'].id, store.id, {'followup': 'write'})

    def test_real_treatment_followup_contact_overdue_appointment_and_close(self):
        # Build the source through the same intake, queue, clinical and treatment
        # actions used by the synthetic treatment suite. No event or appointment
        # state is directly manufactured in this test.
        price(self, amount=137.25)
        receive(self)
        treatment, clinical, _queue, lease, execution, document, args = opened_actual(self)
        treatment_result = treatment._operate(
            'execute', execute_args(self, args), key())
        event = self.root['ydental.treatment.event'].browse(treatment_result['event_id'])
        self.assertEqual((event.ydental_kind, event.state), ('treatment', 'confirmed'))
        self.assertEqual(event.ydental_execution_id, execution)

        # Ending the clinical segment records the real encounter boundary while
        # retaining its exact reservation entitlement for follow-up completion.
        clinical._operate('handover', handover_args(document, lease) | {
            'reason': 'Synthetic encounter ended after confirmed treatment',
        })
        execution.invalidate_recordset(['state', 'ydental_ended_at'])
        self.assertEqual(execution.state, 'handover')
        entitlement = execution.ydental_task_id.ydental_entitlement_id
        self.assertTrue(entitlement)
        self.assertEqual(entitlement.ydental_channel, 'reservation')

        service = bind(self, self.users['manager']).env['ydental.followup.service']
        patient_service = bind(self, self.users['manager']).env['ydental.patient.service']
        patient = execution.ydental_patient_id
        patient_service._operate('edit', {
            'patient_id': patient.id,
            'version': patient.ydental_version,
            'values': {'phone': '+14155550137', 'phone_region': 'US'},
        }, key())
        patient.invalidate_recordset(['ydental_phone', 'ydental_phone_normalized', 'ydental_version'])
        self.assertTrue(patient.ydental_phone_normalized, 'the synthetic follow-up fixture needs a valid contact path')
        planned_at = fields.Datetime.to_datetime(fields.Datetime.now()) - timedelta(minutes=1)
        payload = {
            'patient_id': execution.ydental_patient_id.id,
            'source_event_id': event.id,
            'followup_type': 'post_visit',
            'planned_at': fields.Datetime.to_string(planned_at),
            'responsible_id': self.users['manager'].id,
        }

        # Ordinary authorization remains separate from notification delivery:
        # the reader cannot create a plan, even though the source is valid.
        reader_service = bind(self, self.users['reader']).env['ydental.followup.service']
        with self.assertRaises(AccessError):
            reader_service._operate('create', payload)

        created = service._operate('create', payload)
        followup = self.root['ydental.followup'].browse(created['id'])
        self.assertEqual(created['state'], 'planned')
        self.assertEqual(followup.ydental_source_event_id, event)
        self.assertTrue(followup.ydental_deadline_at)

        # The due reminder is a persistent, version-bound job. It remains an
        # internal pending task until a configured dispatcher claims it.
        job = self.root['ydental.notification.job'].sudo().search([
            ('ydental_followup_id', '=', followup.id),
            ('ydental_source_version', '=', followup.ydental_schedule_version),
            ('ydental_event_type', '=', 'followup_contact'),
        ], limit=1)
        self.assertTrue(job)
        self.assertEqual(job.ydental_state, 'pending')
        self.assertLessEqual(job.ydental_due_at, fields.Datetime.now())

        no_answer = service._operate('contact', {
            'followup_id': followup.id, 'method': 'phone', 'outcome': 'no_answer',
            'note': 'Synthetic call not answered',
        })
        self.assertEqual(no_answer['state'], 'to_notify')
        self.assertEqual(followup.state, 'to_notify')
        self.assertEqual(job.ydental_state, 'pending')
        self.assertEqual(
            self.root['ydental.followup.contact'].sudo().browse(no_answer['contact_id']).ydental_outcome,
            'no_answer',
        )

        contacted = service._operate('contact', {
            'followup_id': followup.id, 'method': 'phone', 'outcome': 'delivered',
            'note': 'Synthetic successful manual call',
        })
        self.assertEqual(contacted['state'], 'notified')
        self.assertEqual(followup.state, 'notified')
        self.assertEqual(self.root['ydental.followup.contact'].sudo().search_count([
            ('ydental_followup_id', '=', followup.id),
        ]), 2)
        self.assertGreater(followup.ydental_deadline_at, fields.Datetime.now())

        # Exercise the real repeated-cron transition with an explicit test
        # boundary; this does not change the host clock or pretend time elapsed.
        overdue_at = followup.ydental_deadline_at + timedelta(seconds=1)
        service._expire_unbooked_followups(overdue_at)
        followup.invalidate_recordset(['state', 'ydental_schedule_version'])
        self.assertEqual(followup.state, 'to_notify')
        self.assertEqual(job.ydental_state, 'cancelled')

        linked = service._operate('link_appointment', {
            'followup_id': followup.id, 'appointment_id': entitlement.id, 'status': 'booked',
        })
        self.assertEqual(linked['appointment_id'], entitlement.id)
        self.assertEqual(linked['appointment_status'], 'booked')
        self.assertEqual(followup.state, 'to_notify')

        rescheduled_at = fields.Datetime.to_datetime(fields.Datetime.now()) + timedelta(hours=2)
        rescheduled = service._operate('reschedule', {
            'followup_id': followup.id,
            'planned_at': fields.Datetime.to_string(rescheduled_at),
            'responsible_id': self.users['manager'].id,
        })
        self.assertEqual(rescheduled['state'], 'to_notify')
        self.assertEqual(followup.ydental_appointment_id, entitlement)
        self.assertEqual(followup.ydental_appointment_status, 'booked')
        self.assertEqual(followup.ydental_planned_at, rescheduled_at)

        closed = service._operate('close', {
            'followup_id': followup.id, 'reason': 'Synthetic patient declined further follow-up',
        })
        self.assertEqual(closed['state'], 'closed')
        self.assertEqual(followup.ydental_closed_reason, 'Synthetic patient declined further follow-up')
        self.assertEqual(followup.ydental_appointment_status, 'booked')

        # Verify the positive appointment path separately: only a real arrival
        # tied to this exact held reservation permits the actual linked treatment
        # event to complete follow-up.
        linked_followup = service._operate('create', payload | {
            'planned_at': fields.Datetime.to_string(fields.Datetime.now()),
        })
        linked_row = self.root['ydental.followup'].browse(linked_followup['id'])
        service._operate('link_appointment', {
            'followup_id': linked_row.id, 'appointment_id': entitlement.id, 'status': 'booked',
        })
        actual_arrival = self.root['ydental.intake.arrival'].sudo().search([
            ('ydental_patient_id', '=', patient.id),
            ('ydental_store_id', '=', execution.ydental_store_id.id),
        ], order='id desc', limit=1)
        self.assertTrue(actual_arrival, 'the treatment fixture must provide a real intake arrival')
        service._operate('record_arrival', {
            'followup_id': linked_row.id, 'arrival_id': actual_arrival.id,
        })
        linked_row.invalidate_recordset(['ydental_appointment_status', 'state'])
        self.assertEqual(linked_row.ydental_appointment_status, 'arrived')
        self.assertNotEqual(linked_row.state, 'done', 'arrival alone is not a completed encounter')
        service._operate('complete', {
            'followup_id': linked_row.id,
            'event_id': event.id,
        })
        linked_row.invalidate_recordset(['ydental_appointment_status', 'state', 'ydental_completed_event_id'])
        self.assertEqual(linked_row.state, 'done')
        self.assertEqual(linked_row.ydental_appointment_status, 'seen')
        self.assertEqual(linked_row.ydental_completed_event_id, event)

    def test_expired_appointment_distinguishes_arrived_without_treatment_from_no_arrival(self):
        price(self, amount=137.25)
        receive(self)
        treatment, clinical, _queue, lease, execution, document, args = opened_actual(self)
        treatment_result = treatment._operate('execute', execute_args(self, args), key())
        event = self.root['ydental.treatment.event'].browse(treatment_result['event_id'])
        clinical._operate('handover', handover_args(document, lease) | {
            'reason': 'Synthetic encounter ended before the separately booked follow-up',
        })
        patient = execution.ydental_patient_id
        patient_service = bind(self, self.users['manager']).env['ydental.patient.service']
        patient_service._operate('edit', {
            'patient_id': patient.id,
            'version': patient.ydental_version,
            'values': {'phone': '+14155550138', 'phone_region': 'US'},
        }, key())

        service = bind(self, self.users['manager']).env['ydental.followup.service']
        base = {
            'patient_id': patient.id,
            'source_event_id': event.id,
            'followup_type': 'post_visit',
            'planned_at': fields.Datetime.to_string(fields.Datetime.now()),
            'responsible_id': self.users['manager'].id,
        }
        manager = bind(self, self.users['manager'])
        mapping = self.mappings[0][0]
        station = self.stations[0][0]
        later_start = fields.Datetime.now().replace(microsecond=0) + timedelta(days=2)
        later_end = later_start + timedelta(minutes=5)
        make_slot(self, manager, station, later_start, later_end)
        arrived_reservation = manager._operate('reserve', {
            'patient_id': patient.id,
            'mapping_id': mapping.id,
            'start': fields.Datetime.to_string(later_start),
            'end': fields.Datetime.to_string(later_end),
            'channel': 'reservation',
        }, key())
        arrived_id = service._operate('create', base)['id']
        arrived_row = self.root['ydental.followup'].browse(arrived_id)
        service._operate('link_appointment', {
            'followup_id': arrived_id, 'appointment_id': arrived_reservation['id'], 'status': 'booked',
        })

        # Advance only this test action to the explicit synthetic reservation
        # date. This creates a real intake arrival row for a held reservation;
        # no queue start or treatment event is created for that appointment.
        with patch.object(fields.Datetime, 'now', return_value=later_start + timedelta(minutes=1)):
            manager._operate('arrive', {'patient_id': patient.id}, key())
        service._expire_appointments(later_end + timedelta(seconds=1))
        arrived_row.invalidate_recordset(['state', 'ydental_appointment_status', 'ydental_arrival_id'])
        self.assertEqual(arrived_row.state, 'to_notify')
        self.assertEqual(arrived_row.ydental_appointment_status, 'arrived')
        self.assertTrue(arrived_row.ydental_arrival_id)
        self.assertFalse(arrived_row.ydental_completed_event_id)

        # A later reservation for the same synthetic patient has no arrival on
        # its local business date. Expiring its actual slot must retain the
        # different no-arrival status and create a contact task.
        no_arrival_start = later_start + timedelta(days=1)
        no_arrival_end = no_arrival_start + timedelta(minutes=5)
        make_slot(self, manager, station, no_arrival_start, no_arrival_end)
        reservation = manager._operate('reserve', {
            'patient_id': patient.id,
            'mapping_id': mapping.id,
            'start': fields.Datetime.to_string(no_arrival_start),
            'end': fields.Datetime.to_string(no_arrival_end),
            'channel': 'reservation',
        }, key())
        no_arrival_id = service._operate('create', base)['id']
        no_arrival_row = self.root['ydental.followup'].browse(no_arrival_id)
        service._operate('link_appointment', {
            'followup_id': no_arrival_id, 'appointment_id': reservation['id'], 'status': 'booked',
        })
        service._expire_appointments(no_arrival_end + timedelta(seconds=1))
        no_arrival_row.invalidate_recordset(['state', 'ydental_appointment_status', 'ydental_arrival_id'])
        self.assertEqual(no_arrival_row.state, 'to_notify')
        self.assertEqual(no_arrival_row.ydental_appointment_status, 'not_arrived')
        self.assertFalse(no_arrival_row.ydental_arrival_id)
        activities = self.root['mail.activity'].sudo().search([
            ('res_model', '=', 'ydental.followup'), ('res_id', '=', no_arrival_id),
        ])
        self.assertTrue(activities, 'a missed appointment must remain visible for manual follow-up')

    def test_intake_appointment_reschedule_replaces_pending_followup_reminder(self):
        price(self, amount=137.25)
        receive(self)
        treatment, clinical, _queue, lease, execution, document, args = opened_actual(self)
        result = treatment._operate('execute', execute_args(self, args), key())
        event = self.root['ydental.treatment.event'].browse(result['event_id'])
        clinical._operate('handover', handover_args(document, lease) | {
            'reason': 'Synthetic completed encounter before a rescheduled follow-up appointment',
        })
        patient = execution.ydental_patient_id
        bind(self, self.users['manager']).env['ydental.patient.service']._operate('edit', {
            'patient_id': patient.id,
            'version': patient.ydental_version,
            'values': {'phone': '+14155550139', 'phone_region': 'US'},
        }, key())

        manager = bind(self, self.users['manager'])
        frontdesk = bind(self, self.users['frontdesk'])
        service = manager.env['ydental.followup.service']
        mapping = self.mappings[0][0]
        station = self.stations[0][0]
        now = fields.Datetime.now().replace(microsecond=0)
        old_start = now + timedelta(days=2)
        old_end = old_start + timedelta(minutes=5)
        new_start = now + timedelta(days=3)
        new_end = new_start + timedelta(minutes=5)
        make_slot(self, manager, station, old_start, old_end)
        make_slot(self, manager, station, new_start, new_end)
        reservation = manager._operate('reserve', {
            'patient_id': patient.id, 'mapping_id': mapping.id,
            'start': fields.Datetime.to_string(old_start), 'end': fields.Datetime.to_string(old_end),
            'channel': 'reservation',
        }, key())
        followup_id = service._operate('create', {
            'patient_id': patient.id, 'source_event_id': event.id,
            'followup_type': 'post_visit', 'planned_at': fields.Datetime.to_string(now),
            'responsible_id': self.users['manager'].id,
        })['id']
        linked = service._operate('link_appointment', {
            'followup_id': followup_id, 'appointment_id': reservation['id'], 'status': 'booked',
        })
        self.assertEqual(linked['appointment_id'], reservation['id'])
        row = self.root['ydental.followup'].browse(followup_id)
        old_version = row.ydental_schedule_version
        old_job = self.root['ydental.notification.job'].sudo().search([
            ('ydental_followup_id', '=', followup_id),
            ('ydental_source_version', '=', old_version),
            ('ydental_event_type', '=', 'appointment_reminder'),
        ], limit=1)
        self.assertTrue(old_job)
        self.assertEqual(old_job.ydental_state, 'pending')

        payload = {
            'record_id': reservation['id'], 'version': reservation['version'],
            'mapping_id': mapping.id, 'start': fields.Datetime.to_string(new_start),
            'end': fields.Datetime.to_string(new_end),
            'reason': 'Synthetic appointment moved to the next local business date',
        }
        operation_key = key()
        frontdesk._operate('reschedule', payload, operation_key)
        reservation_record = self.root['ydental.intake.entitlement'].browse(reservation['id'])
        reservation_record.invalidate_recordset(['state', 'ydental_claim_id'])
        self.assertEqual(reservation_record.state, 'held')
        row.invalidate_recordset(['ydental_appointment_at', 'ydental_deadline_at', 'ydental_schedule_version'])
        self.assertEqual(row.ydental_appointment_id.id, reservation['id'])
        self.assertEqual(row.ydental_appointment_status, 'booked')
        self.assertEqual(row.ydental_appointment_at, new_start)
        self.assertEqual(row.ydental_deadline_at, new_start)
        self.assertEqual(row.ydental_schedule_version, old_version + 1)
        old_job.invalidate_recordset(['ydental_state'])
        self.assertEqual(old_job.ydental_state, 'cancelled')
        current_jobs = self.root['ydental.notification.job'].sudo().search([
            ('ydental_followup_id', '=', followup_id),
            ('ydental_source_version', '=', row.ydental_schedule_version),
            ('ydental_event_type', '=', 'appointment_reminder'),
        ])
        self.assertEqual(len(current_jobs), 1)
        self.assertEqual(current_jobs.ydental_state, 'pending')
        self.assertLessEqual(current_jobs.ydental_due_at, new_start)
        audit = self.root['ydental.access.audit'].sudo().search([
            ('ydental_event', '=', 'appointment_reschedule'),
            ('ydental_category', '=', 'followup'),
            ('ydental_target_model', '=', 'ydental.followup'),
            ('ydental_target_id', '=', followup_id),
            ('ydental_source', '=', 'intake_appointment_reschedule'),
            ('ydental_result', '=', 'accepted'),
        ], order='id desc', limit=1)
        self.assertTrue(audit, 'rescheduling a linked appointment must leave a follow-up audit row')
        self.assertEqual(audit.ydental_user_id, self.users['frontdesk'])
        self.assertEqual(audit.ydental_before['schedule_version'], old_version)
        self.assertEqual(audit.ydental_after['schedule_version'], old_version + 1)
        self.assertEqual(audit.ydental_after['appointment_at'], fields.Datetime.to_string(new_start))

        repeated = frontdesk._operate('reschedule', payload, operation_key)
        self.assertEqual(repeated['result'], 'already_accepted')
        self.assertEqual(row.ydental_schedule_version, old_version + 1)
        self.assertEqual(self.root['ydental.notification.job'].sudo().search_count([
            ('ydental_followup_id', '=', followup_id),
            ('ydental_source_version', '=', row.ydental_schedule_version),
            ('ydental_event_type', '=', 'appointment_reminder'),
            ('ydental_state', '=', 'pending'),
        ]), 1)
