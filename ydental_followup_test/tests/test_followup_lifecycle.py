from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key, bind, handover_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    execute_args, opened_actual, receive, setup as treatment_setup,
)
from odoo.addons.ydental_treatment_test.tests.common import make_slot


@tagged('post_install', '-at_install')
class TestFollowupLifecycle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        treatment_setup(cls)
        for store in cls.stores:
            cls.admin._grant(cls.users['manager'].id, store.id, {'followup': 'write'})

    def test_real_treatment_followup_contact_overdue_appointment_and_close(self):
        # Build the source through the same intake, queue, clinical and treatment
        # actions used by the synthetic treatment suite. No event or appointment
        # state is directly manufactured in this test.
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
