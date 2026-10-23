from datetime import datetime, time, timedelta
from unittest.mock import patch

import pytz

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    arrive_report,
    bind,
    handover_args,
    key,
    make_slot,
    price,
    qualify,
    save_args,
    serving,
)
from odoo.addons.ydental_treatment_test.tests.common import patient as create_patient
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

    def test_followup_operator_links_arrival_and_missed_visit_without_capacity_access(self):
        price(self, amount=137.25)
        receive(self)
        treatment, clinical, queue, lease, execution, document, args = opened_actual(self)
        actual = treatment._operate('execute', execute_args(self, args), key())
        clinical._operate('handover', handover_args(document, lease) | {
            'reason': 'Synthetic source encounter ended before ordinary follow-up',
        })
        queue._operate('exit', {'lease_id': lease['lease_id'], 'token': lease['token']})
        patient = execution.ydental_patient_id
        operator = self.users['doctor']
        self.admin._grant(operator.id, self.stores[0].id, {'followup': 'write'})
        service = bind(self, operator).env['ydental.followup.service']
        membership = service.env['ydental.access.service']._membership(operator.id, self.stores[0].id)
        self.assertEqual(service.env['ydental.access.service']._levels(membership)['capacity'], 'none')
        manager = bind(self, self.users['manager'])
        timezone = pytz.timezone(self.stores[0].ydental_timezone)
        for offset, arrived in ((2, True), (3, False)):
            start = fields.Datetime.now().replace(microsecond=0) + timedelta(days=offset)
            end = start + timedelta(minutes=5)
            slot = make_slot(self, manager, self.stations[0][0], start, end)
            reservation = manager._operate('reserve', {
                'patient_id': patient.id, 'mapping_id': self.mappings[0][0].id,
                'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(end),
                'channel': 'reservation',
            }, key())
            claim = self.root['ydental.intake.entitlement'].browse(reservation['id']).ydental_claim_id
            self.assertFalse(service.env['ydental.supply.claim'].has_access('read'))
            with self.assertRaises(AccessError):
                service.env['ydental.supply.claim'].browse(claim.id).check_access('read')
            created = service._operate('create', {
                'patient_id': patient.id, 'source_event_id': actual['event_id'],
                'followup_type': 'post_visit', 'planned_at': fields.Datetime.to_string(start),
                'responsible_id': operator.id,
            })
            row = self.root['ydental.followup'].browse(created['id'])
            linked = service._operate('link_appointment', {
                'followup_id': row.id, 'appointment_id': reservation['id'],
            })
            self.assertEqual(linked['state'], created['state'])
            self.assertEqual(row.ydental_deadline_at, slot.ydental_start)
            if arrived:
                with patch.object(fields.Datetime, 'now', return_value=start + timedelta(minutes=1)):
                    manager._operate('arrive', {'patient_id': patient.id}, key())
                local_date = pytz.UTC.localize(start).astimezone(timezone).date()
                arrival = self.root['ydental.intake.arrival'].search([
                    ('ydental_patient_id', '=', patient.id), ('ydental_store_id', '=', self.stores[0].id),
                    ('ydental_date', '=', local_date),
                ]).ensure_one()
                result = service._operate('record_arrival', {'followup_id': row.id, 'arrival_id': arrival.id})
                self.assertEqual((result['state'], result['appointment_status']), (created['state'], 'arrived'))
                self.assertFalse(row.ydental_completed_event_id)
            else:
                local_date = pytz.UTC.localize(start).astimezone(timezone).date()
                day_end = timezone.localize(datetime.combine(local_date + timedelta(days=1), time.min)).astimezone(pytz.UTC).replace(tzinfo=None)
                with patch.object(type(service), '_now', return_value=day_end):
                    result = service._operate('mark_not_arrived', {
                        'followup_id': row.id, 'reason': 'Synthetic verified absence after the reservation local day',
                    })
                self.assertEqual((result['state'], result['appointment_status']), ('to_notify', 'not_arrived'))
            self.assertEqual(service.env['ydental.access.service']._levels(membership)['capacity'], 'none')

    def test_real_treatment_followup_contact_overdue_appointment_and_close(self):
        patient_service = bind(self, self.users['manager']).env['ydental.patient.service']
        source_a, source_b, held_patient_id = (create_patient(self) for _ in range(3))
        for source_id, target_id in ((source_a, source_b), (source_b, held_patient_id)):
            request = patient_service._operate('request_merge', {
                'source_id': source_id, 'target_id': target_id,
                'reason': 'Synthetic S11 canonical relation regression',
            }, key())
            patient_service._operate('confirm', {
                'request_id': request['id'], 'version': request['version'],
                'reason': 'Verified synthetic identity chain',
            }, key())
        canonical_relations = patient_service._current_relations([source_a, source_b], self.stores[0])
        self.assertEqual(set(canonical_relations), {source_a, source_b})
        self.assertEqual(canonical_relations[source_a].ydental_patient_id.id, held_patient_id)
        self.assertEqual(canonical_relations[source_b].ydental_patient_id.id, held_patient_id)

        held_reservation = qualify(self, patient_id=held_patient_id)
        intake = bind(self, self.users['manager'])
        rescheduled_start = self.end + timedelta(minutes=5)
        rescheduled_end = rescheduled_start + timedelta(minutes=5)
        rescheduled_slot = make_slot(
            self, intake, self.stations[0][0], rescheduled_start, rescheduled_end)
        intake._operate('reschedule', {
            'record_id': held_reservation['id'], 'version': held_reservation['version'],
            'mapping_id': self.mappings[0][0].id,
            'start': fields.Datetime.to_string(rescheduled_start),
            'end': fields.Datetime.to_string(rescheduled_end),
            'reason': 'Synthetic follow-up reservation reschedule provenance regression',
        }, key())
        held_options = intake._followup_reservation_options([held_patient_id])
        held_option = next((option for option in held_options
                            if option['id'] == held_reservation['id']), None)
        self.assertTrue(held_option, 'a native held reservation must resolve through its linked intake task')
        self.assertEqual(held_option['slot_start'], rescheduled_slot.ydental_start)

        # Build the source through the same intake, queue, clinical and treatment
        # actions used by the synthetic treatment suite. No event or appointment
        # state is directly manufactured in this test.
        price(self, amount=137.25)
        receive(self)
        treatment, clinical, _queue, lease, execution, document, args = opened_actual(self)
        started_task = execution.ydental_task_id
        started_entitlement = started_task.ydental_entitlement_id
        self.assertEqual(started_entitlement.state, 'started')
        self.assertEqual(started_entitlement.ydental_claim_id.state, 'consumed')
        started_options = intake._followup_reservation_options([started_task.ydental_patient_id.id])
        started_option = next((option for option in started_options
                               if option['id'] == started_entitlement.id), None)
        self.assertTrue(started_option, 'a started reservation must retain its workbench option')
        self.assertEqual(started_option['slot_start'], started_entitlement.ydental_claim_id.ydental_slot_id.ydental_start)
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
        _queue._operate('exit', {'lease_id': lease['lease_id'], 'token': lease['token']})
        entitlement = execution.ydental_task_id.ydental_entitlement_id
        self.assertTrue(entitlement)
        self.assertEqual(entitlement.ydental_channel, 'reservation')

        service = bind(self, self.users['manager']).env['ydental.followup.service']
        patient = execution.ydental_patient_id
        current_relations = patient_service._current_relations(
            [held_patient_id, patient.id], self.stores[0])
        self.assertEqual(set(current_relations), {held_patient_id, patient.id})
        self.assertEqual(current_relations[patient.id].ydental_patient_id, patient)
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
        cron_model = self.root['ydental.followup'].with_context({})
        with patch.object(type(service), '_now', return_value=overdue_at):
            cron_model._cron_run_due()
            cron_model._cron_run_due()
        followup.invalidate_recordset(['state', 'ydental_schedule_version'])
        self.assertEqual(followup.state, 'to_notify')
        self.assertEqual(job.ydental_state, 'cancelled')
        overdue_audits = self.root['ydental.access.audit'].search([
            ('ydental_event', '=', 'followup.overdue_contact'),
            ('ydental_target_model', '=', 'ydental.followup'), ('ydental_target_id', '=', followup.id),
        ])
        self.assertEqual(len(overdue_audits), 1)
        self.assertEqual(overdue_audits.ydental_store_id, self.stores[0])
        self.assertEqual(overdue_audits.ydental_source, 'followup_cron')

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

        # Reusing the original visit cannot complete a new follow-up, including
        # an explicitly confirmed association without an appointment.
        linked_followup = service._operate('create', payload | {
            'planned_at': fields.Datetime.to_string(fields.Datetime.now()),
        })
        linked_row = self.root['ydental.followup'].browse(linked_followup['id'])
        with self.assertRaises(UserError):
            service._operate('complete', {
                'followup_id': linked_row.id, 'event_id': event.id,
                'confirmed_unlinked': True, 'reason': 'Original visit is not a return encounter',
            })
        self.assertNotEqual(linked_row.state, 'done')
        reservation = qualify(self, patient_id=patient.id)
        service._operate('link_appointment', {
            'followup_id': linked_row.id, 'appointment_id': reservation['id'], 'status': 'booked',
        })
        arrive_report(self, reservation)
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
        task = self.root['ydental.intake.task'].browse(reservation['task_id'])
        queue, next_lease, next_execution = serving(self, task=task)
        next_clinical = queue.env['ydental.clinical.service']
        next_document = next_clinical._operate('open', {
            'execution_id': next_execution.id, 'lease_id': next_lease['lease_id'],
            'lease_token': next_lease['token'],
        })
        next_document.update(next_clinical._operate('save', save_args(next_document)))
        next_args = {
            'execution_id': next_execution.id, 'lease_id': next_lease['lease_id'],
            'lease_token': next_lease['token'], 'document_id': next_document['document_id'],
            'document_version': next_document['version'],
        }
        next_result = queue.env['ydental.treatment.service']._operate('execute', execute_args(self, next_args), key())
        next_event = self.root['ydental.treatment.event'].browse(next_result['event_id'])
        next_clinical._operate('handover', handover_args(next_document, next_lease) | {
            'reason': 'Synthetic return encounter ended after its actual treatment',
        })
        service._operate('complete', {
            'followup_id': linked_row.id,
            'event_id': next_event.id,
        })
        linked_row.invalidate_recordset(['ydental_appointment_status', 'state', 'ydental_completed_event_id'])
        self.assertEqual(linked_row.state, 'done')
        self.assertEqual(linked_row.ydental_appointment_status, 'seen')
        self.assertEqual(linked_row.ydental_completed_event_id, next_event)
        self.assertNotEqual(linked_row.ydental_completed_execution_id, execution)

    def test_controlled_sink_records_internal_acceptance_without_delivery(self):
        price(self)
        receive(self)
        treatment, _clinical, _queue, _lease, execution, _document, args = opened_actual(self)
        treatment_result = treatment._operate('execute', execute_args(self, args), key())
        event = self.root['ydental.treatment.event'].browse(treatment_result['event_id'])
        patient = execution.ydental_patient_id

        patient_service = bind(self, self.users['manager']).env['ydental.patient.service']
        patient_service._operate('edit', {
            'patient_id': patient.id,
            'version': patient.ydental_version,
            'values': {'email': 's11-controlled-sink@synthetic.invalid'},
        }, key())
        followup_service = bind(self, self.users['manager']).env['ydental.followup.service']
        followup_service._operate('set_preference', {
            'patient_id': patient.id, 'opt_out': False, 'preferred_channel': 'email',
        })
        self.root['ydental.followup.policy'].with_user(self.users['manager']).create({
            'name': 'S11 synthetic controlled sink policy',
            'ydental_store_id': self.stores[0].id,
            'ydental_enabled': True,
            'ydental_channel_mode': 'controlled_test_sink',
            'ydental_daily_limit': 2,
        })
        followup_result = followup_service._operate('create', {
            'patient_id': patient.id,
            'source_event_id': event.id,
            'followup_type': 'post_visit',
            'planned_at': fields.Datetime.to_string(fields.Datetime.now()),
            'responsible_id': self.users['manager'].id,
        })
        followup = self.root['ydental.followup'].browse(followup_result['id'])
        job = self.root['ydental.notification.job'].sudo().search([
            ('ydental_followup_id', '=', followup.id), ('ydental_state', '=', 'pending'),
        ], limit=1)
        self.assertTrue(job)
        request_id = 's11-controlled-' + key()
        # This direct handler test supplies the claimed state and durable
        # request ID; it does not invoke the post-commit dispatcher or claim transaction.
        job._save({'ydental_state': 'dispatching', 'ydental_request_id': request_id})

        mail_count_before = self.root['mail.mail'].sudo().search_count([])
        result = followup_service._send_transport(job)

        followup.invalidate_recordset([
            'state', 'ydental_schedule_version', 'ydental_active_notification_request_id',
        ])
        job.invalidate_recordset(['ydental_activity_id'])
        contact = self.root['ydental.followup.contact'].sudo().search([
            ('ydental_followup_id', '=', followup.id), ('ydental_request_key', '=', 'controlled:' + request_id),
        ])
        self.assertEqual(result, 'accepted')
        self.assertEqual(followup.state, 'notified')
        self.assertEqual(followup.ydental_active_notification_request_id, request_id)
        self.assertEqual(len(contact), 1)
        self.assertEqual(contact.ydental_outcome, 'accepted')
        self.assertEqual(contact.ydental_actor_id.id, self.root.uid)
        self.assertTrue(job.ydental_activity_id)
        self.assertIn('patient delivery is not asserted', job.ydental_activity_id.note)
        self.assertEqual(self.root['mail.mail'].sudo().search_count([]), mail_count_before)

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
        arrived_row.invalidate_recordset(['state', 'ydental_appointment_status'])
        self.assertEqual(arrived_row.state, 'planned', 'slot end is not local day end')
        timezone = pytz.timezone(self.stores[0].ydental_timezone)
        local_day = pytz.UTC.localize(later_start).astimezone(timezone).date()
        day_end = timezone.localize(datetime.combine(local_day + timedelta(days=1), time.min)).astimezone(
            pytz.UTC).replace(tzinfo=None)
        with patch.object(type(service), '_now', return_value=day_end), self.assertRaises(UserError):
            service._operate('mark_not_arrived', {
                'followup_id': arrived_id, 'reason': 'Actual arrival must prevent a missed-visit mark',
            })
        self.assertEqual(arrived_row.ydental_appointment_status, 'booked')
        service._expire_appointments(day_end - timedelta(seconds=1))
        self.assertEqual(arrived_row.state, 'planned')
        service._expire_appointments(day_end)
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
        self.assertEqual(no_arrival_row.state, 'planned')
        missed_day = pytz.UTC.localize(no_arrival_start).astimezone(timezone).date()
        missed_day_end = timezone.localize(datetime.combine(missed_day + timedelta(days=1), time.min)).astimezone(
            pytz.UTC).replace(tzinfo=None)
        manual_row = self.root['ydental.followup'].browse(service._operate('create', base)['id'])
        service._operate('link_appointment', {
            'followup_id': manual_row.id, 'appointment_id': reservation['id'], 'status': 'booked',
        })
        manual_args = {'followup_id': manual_row.id, 'reason': 'Verified no arrival by local day end'}
        before_version = manual_row.ydental_version
        for too_early in (no_arrival_end + timedelta(seconds=1), missed_day_end - timedelta(seconds=1)):
            with patch.object(type(service), '_now', return_value=too_early), self.assertRaises(UserError):
                service._operate('mark_not_arrived', manual_args)
        manual_row.invalidate_recordset()
        self.assertEqual((manual_row.state, manual_row.ydental_appointment_status), ('planned', 'booked'))
        self.assertEqual(manual_row.ydental_version, before_version)
        reader = bind(self, self.users['reader']).env['ydental.followup.service']
        with self.assertRaises(AccessError):
            reader._operate('mark_not_arrived', manual_args)
        with patch.object(type(service), '_now', return_value=missed_day_end):
            marked = service._operate('mark_not_arrived', manual_args)
            with self.assertRaises(UserError):
                service._operate('mark_not_arrived', manual_args)
        self.assertEqual((marked['state'], marked['appointment_status']), ('to_notify', 'not_arrived'))
        self.assertFalse(manual_row.ydental_arrival_id)
        with patch.object(type(service), '_now', return_value=missed_day_end):
            self.root['ydental.followup'].with_context({})._cron_run_due()
            self.root['ydental.followup'].with_context({})._cron_run_due()
        no_arrival_row.invalidate_recordset(['state', 'ydental_appointment_status', 'ydental_arrival_id'])
        self.assertEqual(no_arrival_row.state, 'to_notify')
        self.assertEqual(no_arrival_row.ydental_appointment_status, 'not_arrived')
        self.assertFalse(no_arrival_row.ydental_arrival_id)
        activities = self.root['mail.activity'].sudo().search([
            ('res_model', '=', 'ydental.followup'), ('res_id', '=', no_arrival_id),
        ])
        self.assertTrue(activities, 'a missed appointment must remain visible for manual follow-up')
        audits = self.root['ydental.access.audit'].search([
            ('ydental_event', '=', 'followup.appointment_overdue'),
            ('ydental_target_model', '=', 'ydental.followup'), ('ydental_target_id', '=', no_arrival_id),
        ])
        self.assertEqual(len(audits), 1)

        # Cancel through intake, then run the actual cron without a login scope.
        cancel_start = no_arrival_start + timedelta(days=1)
        cancel_end = cancel_start + timedelta(minutes=5)
        make_slot(self, manager, station, cancel_start, cancel_end)
        cancellable = qualify(self, patient_id=patient.id, service=manager, start=cancel_start, end=cancel_end)
        cancel_row = self.root['ydental.followup'].browse(service._operate('create', base)['id'])
        service._operate('link_appointment', {
            'followup_id': cancel_row.id, 'appointment_id': cancellable['id'], 'status': 'booked',
        })
        manager._operate('cancel', {
            'record_id': cancellable['id'], 'version': cancellable['version'],
            'reason': 'Synthetic reservation cancellation before its service date',
        }, key())
        cron = self.root['ydental.followup'].with_context({})
        cron._cron_run_due()
        cron._cron_run_due()
        cancel_row.invalidate_recordset()
        self.assertEqual((cancel_row.state, cancel_row.ydental_appointment_status), ('to_notify', 'cancelled'))
        self.assertFalse(cancel_row.ydental_appointment_id)
        cancelled_audits = self.root['ydental.access.audit'].search([
            ('ydental_event', '=', 'followup.appointment_cancelled'),
            ('ydental_target_model', '=', 'ydental.followup'), ('ydental_target_id', '=', cancel_row.id),
        ])
        self.assertEqual(len(cancelled_audits), 1)
        self.assertEqual(cancelled_audits.ydental_store_id, self.stores[0])

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
            ('ydental_event', '=', 'followup.appointment_reschedule'),
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
