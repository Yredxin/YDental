import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, time, timedelta

import pytz
from psycopg2 import IntegrityError

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.orm.registry import Registry


_logger = logging.getLogger(__name__)
CONTACT_OUTCOMES = ('no_answer', 'failed', 'accepted', 'delivered', 'unknown')


def _supplier_qualification_is_current(job_version, vendor_version, vendor_state, valid_until,
                                      job_due_date, company_matches, cooperation_active):
    return bool(job_version == vendor_version and vendor_state == 'approved' and valid_until and
                job_due_date == valid_until and company_matches and cooperation_active)


def _callback_matches_current_request(job_state, job_version, schedule_version, active_request_id,
                                     active_schedule_version, request_id):
    return bool(job_version == schedule_version or (
        job_state == 'accepted' and active_request_id == request_id and
        active_schedule_version == schedule_version
    ))


def _reconciliation_action(current_state, requested_outcome):
    if current_state == 'unknown':
        return 'apply'
    if current_state == requested_outcome:
        return 'duplicate'
    return 'conflict'


def _daily_cap_attempt_counts(attempt_count, attempt_started_at, local_start, local_end):
    return bool(attempt_count > 0 and attempt_started_at and local_start <= attempt_started_at < local_end)


def _authorize_passive_lab_write(access, store):
    session = access._scope()
    if session.ydental_store_id != store:
        raise AccessError('access_denied: The laboratory order belongs to another store.')
    access._check('warehouse', 'write', store.id, write=True)
    return session


def _supplier_expiry_authorized(is_group_manager, local_store_writer, vendor_company_matches, store_company_matches,
                                cooperation_active, cooperation_vendor_matches,
                                cooperation_store_matches, assigned_responsible_matches):
    """Pure authorization predicate for the narrow group-governed expiry hook."""
    return bool((is_group_manager or local_store_writer) and vendor_company_matches and store_company_matches and
                cooperation_active and cooperation_vendor_matches and cooperation_store_matches and
                assigned_responsible_matches)


class YDentalFollowupService(models.AbstractModel):
    _name = 'ydental.followup.service'
    _description = 'Authorized follow-up, notification and reconciliation actions'

    def _now(self):
        return fields.Datetime.now()

    def _scope(self, write=False):
        access = self.env['ydental.access.service']
        member = access._check('followup', 'write' if write else 'read', write=write)
        return access._scope(write=write), member

    def _audit(self, action, record, before=None, after=None, reason=False, source='followup_action'):
        session = self.env['ydental.access.service']._scope()
        return self.env['ydental.access.service']._audit(
            'followup.' + action, 'followup', record, session.ydental_store_id.id,
            before=before, after=after, reason=reason, source=source,
        )

    def _audit_due(self, action, row, before, after):
        # Cron has no interactive login binding. Its bounded scan supplies the
        # exact source row and store, without creating or borrowing a session.
        return self.env['ydental.access.service']._audit(
            'followup.' + action, 'followup', row, row.ydental_store_id.id,
            before=before, after=after, source='followup_cron',
        )

    def _id(self, value):
        if type(value) is not int or value <= 0:
            raise ValidationError(self.env._('A positive record identifier is required.'))
        return value

    def _text(self, value, *, required=False, maximum=300):
        if value is False or value is None:
            value = ''
        if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
            raise ValidationError(self.env._('Enter valid text within the allowed length.'))
        return value.strip()

    def _date(self, value, *, required=True, timezone=None):
        if not value and not required:
            return False
        try:
            if isinstance(value, datetime):
                result = value
            elif isinstance(value, str) and 'T' in value:
                result = datetime.fromisoformat(value)
            else:
                result = fields.Datetime.to_datetime(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(self.env._('Enter a valid date and time.')) from error
        if not result:
            raise ValidationError(self.env._('Enter a valid date and time.'))
        if result.tzinfo:
            return result.astimezone(pytz.UTC).replace(tzinfo=None)
        if timezone and isinstance(value, str) and 'T' in value:
            try:
                return pytz.timezone(timezone).localize(result, is_dst=None).astimezone(pytz.UTC).replace(tzinfo=None)
            except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError, pytz.UnknownTimeZoneError) as error:
                raise ValidationError(self.env._('The local time is ambiguous or invalid for this store.')) from error
        return result

    def _followup(self, followup_id, write=False):
        session, _member = self._scope(write)
        row = self.env['ydental.followup'].browse(self._id(followup_id)).exists()
        if not row:
            raise AccessError(self.env._('access_denied: Follow-up is unavailable.'))
        # Model-level access intentionally grants ordinary staff read only;
        # authorized mutations go through this service's followup:write scope
        # and the model's private _save path.
        row.check_access('read')
        if row.ydental_store_id != session.ydental_store_id:
            raise AccessError(self.env._('access_denied: Follow-up belongs to another store.'))
        self.env['ydental.patient.service']._current_relation(row.ydental_patient_id, session.ydental_store_id)
        return row

    def _source_event(self, event_id, patient_id=None, store=None):
        event = self.env['ydental.treatment.event'].browse(self._id(event_id)).exists()
        if not event:
            raise AccessError(self.env._('access_denied: Select an actual treatment event.'))
        event.check_access('read')
        if event.ydental_kind != 'treatment':
            raise ValidationError(self.env._('Follow-up plans and completion must use a confirmed treatment event, not dispensing or correction records.'))
        execution = event.ydental_execution_id
        if not event.ydental_document_id or not execution or execution.ydental_patient_id != event.ydental_document_id.ydental_patient_id:
            raise ValidationError(self.env._('The treatment event is not linked to its actual patient document.'))
        if patient_id and execution.ydental_patient_id.id != patient_id:
            raise ValidationError(self.env._('The treatment event belongs to a different patient.'))
        if store and execution.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: The treatment event belongs to another store.'))
        return event

    def _responsible(self, user_id, store, *, medical=False):
        user_id = self._id(user_id)
        access = self.env['ydental.access.service']
        member = access._membership(user_id, store.id)
        user = self.env['res.users'].sudo().browse(user_id).exists()
        levels = access._levels(member) if member else {}
        category = 'medical' if medical else 'followup'
        if (not user or not user.active or store.company_id not in user.company_ids or not member or
                not member.ydental_employee_id.active or levels.get(category) != 'write'):
            raise AccessError(self.env._('access_denied: An active authorized store responsible person is required.'))
        return user

    def _patient(self, patient_id, store):
        patient = self.env['ydental.patient.service']._patient(self._id(patient_id), active=True)
        self.env['ydental.patient.service']._current_relation(patient, store)
        return patient

    def _contact_snapshot(self, patient):
        # Only the presence of a legal contact path is checked here. Raw contact values never enter the task or audit.
        return bool(patient.ydental_phone_normalized or patient.ydental_email)

    def _contact_model(self):
        return self.env['ydental.followup.contact'].sudo()

    def _job_model(self):
        return self.env['ydental.notification.job'].sudo()

    def _enqueue(self, *, store, source_model, source_id, source_version, event_type, due_at,
                 followup=None, responsible=None, channel_key='patient'):
        existing = self._job_model().search([
            ('ydental_store_id', '=', store.id), ('ydental_source_model', '=', source_model),
            ('ydental_source_res_id', '=', source_id), ('ydental_source_version', '=', source_version),
            ('ydental_event_type', '=', event_type), ('ydental_channel_key', '=', channel_key),
        ], limit=1)
        if existing:
            return existing
        try:
            with self.env.cr.savepoint():
                job = self._job_model()._new({
                    'name': event_type.replace('_', ' ').title(), 'ydental_store_id': store.id,
                    'ydental_category': 'followup', 'ydental_followup_id': followup.id if followup else False,
                    'ydental_responsible_id': responsible.id if responsible else False,
                    'ydental_source_model': source_model, 'ydental_source_res_id': source_id,
                    'ydental_event_type': event_type, 'ydental_source_version': source_version,
                    'ydental_channel_key': channel_key, 'ydental_due_at': due_at,
                })
        except IntegrityError:
            job = self._job_model().search([
                ('ydental_store_id', '=', store.id), ('ydental_source_model', '=', source_model),
                ('ydental_source_res_id', '=', source_id), ('ydental_source_version', '=', source_version),
                ('ydental_event_type', '=', event_type), ('ydental_channel_key', '=', channel_key),
            ], limit=1)
            if not job:
                raise
        self._postcommit_dispatch([job.id])
        return job

    def _postcommit_dispatch(self, job_ids):
        if not job_ids:
            return
        dbname = self.env.cr.dbname
        clock = self.env.context.get('ydental_s11_clock')
        self.env.cr.postcommit.add(lambda: _dispatch_after_commit(dbname, tuple(job_ids), clock))

    def _schedule(self, row):
        jobs = self._job_model().search([
            ('ydental_followup_id', '=', row.id), ('ydental_state', '=', 'pending'),
        ])
        if jobs:
            jobs._save({'ydental_state': 'cancelled', 'ydental_last_error': 'Source version superseded'})
        if row.state in ('done', 'closed'):
            return
        when = row.ydental_appointment_at or row.ydental_planned_at
        event_type = 'appointment_reminder' if row.ydental_appointment_id and row.ydental_appointment_status == 'booked' else (
            'lab_arrival' if row.ydental_followup_type == 'lab_arrival' else 'followup_contact')
        policy = self.env['ydental.followup.policy'].sudo().search([
            ('ydental_store_id', '=', row.ydental_store_id.id),
        ], limit=1)
        if policy:
            when = self._quiet_hour_due(when - timedelta(hours=policy.ydental_lead_hours), policy)
        when = max(when, fields.Datetime.to_datetime(fields.Datetime.now()))
        return self._enqueue(
            store=row.ydental_store_id, source_model='ydental.followup', source_id=row.id,
            source_version=row.ydental_schedule_version, event_type=event_type, due_at=when,
            followup=row,
        )

    def _quiet_hour_due(self, instant, policy):
        timezone = pytz.timezone(policy.ydental_store_id.ydental_timezone)
        local = pytz.UTC.localize(instant).astimezone(timezone)
        start_h, start_m = (int(part) for part in policy.ydental_quiet_start.split(':'))
        end_h, end_m = (int(part) for part in policy.ydental_quiet_end.split(':'))
        start, end = time(start_h, start_m), time(end_h, end_m)
        current = local.timetz().replace(tzinfo=None)
        quiet = (start <= current < end) if start < end else (current >= start or current < end)
        if not quiet:
            return instant
        target_date = local.date()
        if start >= end and current >= start:
            target_date += timedelta(days=1)
        target = datetime.combine(target_date, end)
        return timezone.localize(target, is_dst=None).astimezone(pytz.UTC).replace(tzinfo=None)

    def _unbooked_deadline(self, planned_at, store):
        policy = self.env['ydental.followup.policy'].sudo().search([
            ('ydental_store_id', '=', store.id),
        ], limit=1)
        window = policy.ydental_unbooked_window_hours if policy else 72
        return planned_at + timedelta(hours=window)

    def _mark_contact_success(self, row, request_id=False):
        next_schedule_version = row.ydental_schedule_version + 1
        vals = {'state': 'notified', 'ydental_schedule_version': next_schedule_version,
                'ydental_active_notification_request_id': request_id or False,
                'ydental_active_notification_schedule_version': next_schedule_version if request_id else 0}
        if not row.ydental_appointment_id:
            vals['ydental_deadline_at'] = self._unbooked_deadline(fields.Datetime.to_datetime(fields.Datetime.now()), row.ydental_store_id)
        row._save(vals)
        self._cancel_pending_jobs(row, 'Successful contact superseded automatic reminder')

    def _operate(self, operation, payload):
        if not isinstance(payload, dict):
            raise ValidationError(self.env._('Action arguments must be an object.'))
        handlers = {
            'create': self._create, 'reschedule': self._reschedule, 'contact': self._contact,
            'link_appointment': self._link_appointment, 'record_arrival': self._record_arrival,
            'mark_not_arrived': self._mark_not_arrived, 'complete': self._complete,
            'close': self._close, 'reopen': self._reopen, 'set_preference': self._set_preference,
            'reconcile_unknown': self._reconcile_unknown,
        }
        if operation not in handlers:
            raise ValidationError(self.env._('Unknown follow-up action.'))
        return handlers[operation](**payload)

    def _set_preference(self, patient_id, opt_out, preferred_channel='manual'):
        session, _member = self._scope(write=True)
        if type(opt_out) is not bool or preferred_channel not in ('phone', 'email', 'message', 'manual'):
            raise ValidationError(self.env._('Select a valid contact preference.'))
        patient = self._patient(patient_id, session.ydental_store_id)
        Preference = self.env['ydental.followup.preference'].sudo()
        row = Preference.search([
            ('ydental_store_id', '=', session.ydental_store_id.id), ('ydental_patient_id', '=', patient.id),
        ], limit=1)
        before = {'opt_out': row.ydental_opt_out, 'preferred_channel': row.ydental_preferred_channel} if row else False
        vals = {'ydental_opt_out': opt_out, 'ydental_preferred_channel': preferred_channel,
                'ydental_recorded_at': fields.Datetime.now(), 'ydental_actor_id': self.env.uid}
        if row:
            row._save(vals)
        else:
            row = Preference._new(dict(vals, name='Follow-up preference', ydental_store_id=session.ydental_store_id.id,
                                       ydental_category='followup', ydental_patient_id=patient.id))
        self._audit('preference', row, before=before,
                    after={'opt_out': opt_out, 'preferred_channel': preferred_channel})
        return {'id': row.id, 'opt_out': opt_out, 'preferred_channel': preferred_channel}

    def _queue_supplier_expiry(self, vendor, store, due_at, responsible_id):
        """Queue an internal supplier-expiry task from the fixed lab qualification source."""
        access = self.env['ydental.access.service']
        access._require_internal()
        is_group_manager = access._is_group_manager()
        if vendor._name != 'ydental.lab.vendor' or len(vendor) != 1:
            raise AccessError(self.env._('access_denied: A real supplier qualification is required.'))
        if store._name != 'ydental.access.store' or len(store) != 1:
            raise AccessError(self.env._('access_denied: A real active store is required.'))
        vendor.check_access('read')
        local_store_writer = False
        if not is_group_manager:
            session = access._scope()
            if session.ydental_store_id != store:
                raise AccessError(self.env._('access_denied: Store staff can queue expiry review only for their active store cooperation.'))
            access._check('warehouse', 'write', store.id, write=True)
            local_store_writer = True
        if (not store.active or store.company_id not in self.env.user.company_ids or
                not store.company_id or store.company_id not in vendor.company_ids or
                not vendor.valid_until or vendor.state != 'approved'):
            raise AccessError(self.env._('access_denied: Qualification does not apply to this store.'))
        cooperation = self.env['ydental.lab.cooperation'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_vendor_id', '=', vendor.id), ('active', '=', True),
        ], limit=1)
        if not cooperation:
            raise AccessError(self.env._('access_denied: An active exact supplier cooperation is required.'))
        responsible_id = self._id(responsible_id)
        member = access._membership(responsible_id, store.id)
        user = self.env['res.users'].sudo().browse(responsible_id).exists()
        if (not user or not user.active or not member or not member.ydental_employee_id.active or
                cooperation.responsible_id.id != responsible_id or
                not _supplier_expiry_authorized(
                    is_group_manager, local_store_writer, store.company_id in vendor.company_ids,
                    store.company_id in self.env.user.company_ids,
                    cooperation.active, cooperation.ydental_vendor_id == vendor,
                    cooperation.ydental_store_id == store, cooperation.responsible_id.id == responsible_id,
                )):
            raise AccessError(self.env._('access_denied: An active store qualification owner is required.'))
        due_at = self._date(due_at, timezone=store.ydental_timezone)
        source_version = vendor.qualification_version
        job = self._enqueue(
            store=store, source_model='ydental.lab.vendor', source_id=vendor.id,
            source_version=source_version, event_type='supplier_expiry',
            due_at=due_at, responsible=user, channel_key='internal',
        )
        self.env['ydental.access.service']._audit(
            'notification.supplier_expiry.queue', 'supplier', vendor, store.id,
            after={'job_id': job.id, 'due_at': fields.Datetime.to_string(due_at)}, source='followup_notification',
        )
        return job

    def _create(self, patient_id, source_event_id, followup_type, planned_at, responsible_id, deadline_at=False):
        session, _member = self._scope(write=True)
        store = session.ydental_store_id
        self.env['ydental.access.service']._check('medical', 'read')
        patient = self._patient(patient_id, store)
        event = self._source_event(source_event_id, patient.id, store)
        if event.state != 'confirmed':
            raise UserError(self.env._('A follow-up plan must be based on a confirmed actual treatment event.'))
        user = self._responsible(responsible_id, store)
        if followup_type not in ('post_visit', 'lab_arrival', 'other'):
            raise ValidationError(self.env._('Select a valid follow-up type.'))
        planned_at = self._date(planned_at, timezone=store.ydental_timezone)
        deadline_at = self._date(deadline_at, required=False, timezone=store.ydental_timezone)
        deadline_at = deadline_at or self._unbooked_deadline(planned_at, store)
        if deadline_at and deadline_at < planned_at:
            raise ValidationError(self.env._('The contact deadline cannot precede the planned contact.'))
        row = self.env['ydental.followup'].sudo()._new({
            'name': event.ydental_document_id.name, 'ydental_store_id': store.id,
            'ydental_category': 'followup', 'ydental_patient_id': patient.id,
            'ydental_source_event_id': event.id, 'ydental_followup_type': followup_type,
            'ydental_planned_at': planned_at, 'ydental_deadline_at': deadline_at,
            'ydental_responsible_id': user.id, 'ydental_created_by_id': self.env.uid,
        })
        self._audit('create', row, after={'source_event_id': event.id, 'version': row.ydental_version})
        if self._contact_snapshot(patient):
            self._schedule(row)
        else:
            row._save({'state': 'to_notify'})
            self._create_contact_activity(row, 'No verified contact path is available; arrange manual contact.')
        return {'id': row.id, 'state': row.state, 'version': row.ydental_version}

    def _reschedule(self, followup_id, planned_at, deadline_at=False, responsible_id=None):
        row = self._followup(followup_id, True)
        if row.state in ('done', 'closed'):
            raise UserError(self.env._('A completed or closed follow-up cannot be rescheduled.'))
        planned_at = self._date(planned_at, timezone=row.ydental_store_id.ydental_timezone)
        deadline_at = self._date(deadline_at, required=False, timezone=row.ydental_store_id.ydental_timezone)
        deadline_at = deadline_at or self._unbooked_deadline(planned_at, row.ydental_store_id)
        if deadline_at and deadline_at < planned_at:
            raise ValidationError(self.env._('The contact deadline cannot precede the planned contact.'))
        user = self._responsible(responsible_id or self.env.uid, row.ydental_store_id)
        before = {'planned_at': fields.Datetime.to_string(row.ydental_planned_at),
                  'appointment_id': row.ydental_appointment_id.id, 'state': row.state}
        row._save({'ydental_planned_at': planned_at, 'ydental_deadline_at': deadline_at,
                   'ydental_schedule_version': row.ydental_schedule_version + 1,
                   'ydental_responsible_id': user.id})
        self._schedule(row)
        self._audit('reschedule', row, before=before,
                    after={'planned_at': fields.Datetime.to_string(planned_at), 'version': row.ydental_version})
        return {'id': row.id, 'state': row.state, 'version': row.ydental_version}

    def _appointment_timing(self, row, appointment):
        """Read exact authorized reservation dates without capacity access."""
        appointment.check_access('read')
        if (appointment.ydental_store_id != row.ydental_store_id or
                appointment.ydental_patient_id != row.ydental_patient_id):
            raise AccessError(self.env._('access_denied: The reservation does not belong to this follow-up.'))
        # Intake validates the exact linked claim, source key, state and slot.
        # Only its display dates leave that existing narrow read bridge.
        options = self.env['ydental.intake.service']._followup_reservation_options([row.ydental_patient_id.id])
        for option in options:
            if option['id'] == appointment.id:
                return option
        raise AccessError(self.env._('access_denied: Current reservation timing is unavailable.'))

    def _link_appointment(self, followup_id, appointment_id, status='booked'):
        row = self._followup(followup_id, True)
        if row.state in ('done', 'closed'):
            raise UserError(self.env._('Completed or closed follow-ups cannot change appointment linkage.'))
        if status not in ('booked', 'cancelled'):
            raise ValidationError(self.env._('Appointment status must be booked or cancelled here.'))
        appointment = self.env['ydental.intake.entitlement'].browse(self._id(appointment_id)).exists() if appointment_id else False
        if status == 'cancelled' and (appointment or not row.ydental_appointment_id or
                                      row.ydental_appointment_id.state != 'cancelled'):
            raise ValidationError(self.env._('Clear a reservation only after intake records its actual cancellation.'))
        if appointment:
            appointment.check_access('read')
            if (appointment.ydental_patient_id != row.ydental_patient_id or
                    appointment.ydental_store_id != row.ydental_store_id or appointment.state not in ('held', 'started') or
                    appointment.ydental_channel != 'reservation'):
                raise AccessError(self.env._('access_denied: Select an active reservation for this patient and store.'))
        elif status == 'booked':
            raise ValidationError(self.env._('A real reservation entitlement is required.'))
        before = {'appointment_id': row.ydental_appointment_id.id,
                  'appointment_status': row.ydental_appointment_status, 'state': row.state}
        vals = {'ydental_appointment_id': appointment.id if appointment else False,
                'ydental_appointment_status': status,
                'ydental_schedule_version': row.ydental_schedule_version + 1}
        if appointment:
            vals['ydental_deadline_at'] = self._appointment_timing(row, appointment)['slot_start']
        row._save(vals)
        self._cancel_pending_jobs(row, 'Appointment linkage changed')
        self._schedule(row)
        self._audit('appointment_link', row, before=before,
                    after={'appointment_id': row.ydental_appointment_id.id, 'appointment_status': status,
                           'state': row.state, 'version': row.ydental_version})
        return {'id': row.id, 'state': row.state, 'appointment_status': row.ydental_appointment_status,
                'appointment_id': row.ydental_appointment_id.id}

    def _refresh_appointment_schedule(self, entitlement, previous_start=False):
        """Refresh linked follow-up reminders in the same intake reschedule transaction."""
        access = self.env['ydental.access.service']
        access._require_internal()
        session = access._scope(write=True)
        store = entitlement.ydental_store_id
        if (entitlement._name != 'ydental.intake.entitlement' or not entitlement.exists() or
                session.ydental_store_id != store):
            raise AccessError(self.env._('access_denied: Appointment reschedule source is unavailable.'))
        access._check('frontdesk', 'write', store.id, write=True)
        if entitlement.state != 'held' or entitlement.ydental_channel != 'reservation':
            return 0
        rows = self.env['ydental.followup'].sudo().search([
            ('ydental_store_id', '=', store.id),
            ('ydental_patient_id', '=', entitlement.ydental_patient_id.id),
            ('ydental_appointment_id', '=', entitlement.id),
            ('ydental_appointment_status', '=', 'booked'),
            ('state', 'not in', ('done', 'closed')),
        ], order='id')
        slot = entitlement.ydental_claim_id.ydental_slot_id
        for row in rows:
            row.invalidate_recordset(['ydental_appointment_at'])
            before = {'appointment_id': entitlement.id,
                      'appointment_at': fields.Datetime.to_string(previous_start) if previous_start else False,
                      'deadline_at': fields.Datetime.to_string(row.ydental_deadline_at),
                      'schedule_version': row.ydental_schedule_version}
            row._save({'ydental_deadline_at': slot.ydental_start,
                       'ydental_schedule_version': row.ydental_schedule_version + 1})
            self._cancel_pending_jobs(row, 'Linked appointment rescheduled')
            self._schedule(row)
            self._audit('appointment_reschedule', row, before=before,
                        after={'appointment_id': entitlement.id,
                               'appointment_at': fields.Datetime.to_string(slot.ydental_start),
                               'deadline_at': fields.Datetime.to_string(row.ydental_deadline_at),
                               'schedule_version': row.ydental_schedule_version},
                        reason='Appointment moved through the authorized intake service',
                        source='intake_appointment_reschedule')
        return len(rows)

    def _record_arrival(self, followup_id, arrival_id):
        row = self._followup(followup_id, True)
        if not row.ydental_appointment_id or row.ydental_appointment_status not in ('booked', 'not_arrived'):
            raise UserError(self.env._('Link an active reservation before recording appointment arrival.'))
        arrival = self.env['ydental.intake.arrival'].browse(self._id(arrival_id)).exists()
        if not arrival:
            raise AccessError(self.env._('access_denied: Select the actual store arrival record.'))
        arrival.check_access('read')
        slot_start = self._appointment_timing(row, row.ydental_appointment_id)['slot_start']
        slot_local_date = pytz.UTC.localize(slot_start).astimezone(pytz.timezone(row.ydental_store_id.ydental_timezone)).date()
        if (arrival.ydental_store_id != row.ydental_store_id or arrival.ydental_patient_id != row.ydental_patient_id or
                arrival.ydental_date != slot_local_date):
            raise AccessError(self.env._('access_denied: Arrival does not prove this patient appointment at this store and date.'))
        row._save({'ydental_arrival_id': arrival.id, 'ydental_appointment_status': 'arrived',
                   'ydental_schedule_version': row.ydental_schedule_version + 1})
        self._cancel_pending_jobs(row, 'Actual arrival linked')
        self._audit('arrival_link', row, after={'arrival_id': arrival.id,
                    'appointment_status': row.ydental_appointment_status, 'state': row.state})
        return {'id': row.id, 'state': row.state, 'appointment_status': row.ydental_appointment_status}

    def _mark_not_arrived(self, followup_id, reason):
        row = self._followup(followup_id, True)
        reason = self._text(reason, required=True)
        if (row.state in ('done', 'closed') or not row.ydental_appointment_id or
                row.ydental_appointment_status != 'booked'):
            raise UserError(self.env._('Only a booked appointment can be marked not arrived.'))
        timing = self._appointment_timing(row, row.ydental_appointment_id)
        timezone = pytz.timezone(row.ydental_store_id.ydental_timezone)
        now = fields.Datetime.to_datetime(self._now())
        local_now = pytz.UTC.localize(now).astimezone(timezone)
        appointment_day = pytz.UTC.localize(timing['slot_start']).astimezone(timezone).date()
        if local_now.date() <= appointment_day or now < timing['slot_end']:
            raise UserError(self.env._('The reservation local day has not ended.'))
        arrival = self.env['ydental.intake.arrival'].sudo().search([
            ('ydental_store_id', '=', row.ydental_store_id.id), ('ydental_patient_id', '=', row.ydental_patient_id.id),
            ('ydental_date', '=', appointment_day),
        ], limit=1)
        if arrival:
            raise UserError(self.env._('An actual arrival exists; do not mark this appointment as missed.'))
        row._save({'ydental_appointment_status': 'not_arrived', 'state': 'to_notify',
                   'ydental_schedule_version': row.ydental_schedule_version + 1})
        self._cancel_pending_jobs(row, 'Reservation day ended without arrival')
        self._create_contact_activity(row, 'The reservation local day ended without actual arrival. Contact the patient.')
        self._audit('not_arrived', row, after={'appointment_status': row.ydental_appointment_status,
                    'state': row.state}, reason=reason)
        return {'id': row.id, 'state': row.state, 'appointment_status': row.ydental_appointment_status}

    def _contact(self, followup_id, method, outcome, note='', request_key=''):
        row = self._followup(followup_id, True)
        if row.state in ('done', 'closed'):
            raise UserError(self.env._('A completed or closed follow-up cannot accept another contact action.'))
        if method not in ('phone', 'message', 'other') or outcome not in CONTACT_OUTCOMES:
            raise ValidationError(self.env._('Select a valid contact method and result.'))
        note = self._text(note, maximum=300)
        request_key = self._text(request_key, maximum=128)
        if request_key and len(request_key) < 16:
            raise ValidationError(self.env._('A contact idempotency key must contain at least 16 characters.'))
        if method == 'phone' and outcome in ('accepted', 'delivered'):
            outcome = 'delivered'
        contact = self._contact_model()._new({
            'name': 'Follow-up contact', 'ydental_store_id': row.ydental_store_id.id,
            'ydental_category': 'followup', 'ydental_followup_id': row.id,
            'ydental_contacted_at': fields.Datetime.now(), 'ydental_actor_id': self.env.uid,
            'ydental_method': method, 'ydental_outcome': outcome, 'ydental_note': note,
            'ydental_request_key': request_key or False,
        })
        before = row.state
        if outcome in ('accepted', 'delivered'):
            self._mark_contact_success(row)
            self._audit('contact_success', row, before={'state': before}, after={'state': row.state, 'contact_id': contact.id})
        elif outcome in ('failed', 'no_answer', 'unknown'):
            row._save({'state': 'to_notify'})
            self._create_contact_activity(row, 'Contact outcome requires another attempt or reconciliation.')
            self._audit('contact_pending', row, before={'state': before}, after={'state': row.state, 'contact_id': contact.id},
                        reason=outcome)
        return {'id': row.id, 'state': row.state, 'contact_id': contact.id}

    def _complete(self, followup_id, event_id, confirmed_unlinked=False, reason=''):
        row = self._followup(followup_id, True)
        self.env['ydental.access.service']._check('medical', 'write', write=True)
        if row.state in ('done', 'closed'):
            raise UserError(self.env._('A completed or closed follow-up cannot be completed again.'))
        if type(confirmed_unlinked) is not bool:
            raise ValidationError(self.env._('Unlinked encounter confirmation must be explicit.'))
        reason = self._text(reason, required=confirmed_unlinked)
        candidate = self.env['ydental.treatment.event'].sudo().browse(self._id(event_id)).exists()
        if not candidate:
            raise AccessError(self.env._('access_denied: Select a real completed treatment event.'))
        if candidate.ydental_kind != 'treatment':
            raise ValidationError(self.env._('Only a treatment event can complete a follow-up.'))
        execution = candidate.ydental_execution_id
        cross_store_referral = False
        if execution.ydental_store_id == row.ydental_store_id:
            event = self._source_event(event_id, row.ydental_patient_id.id, row.ydental_store_id)
        else:
            # Cross-store completion is allowed only through the exact referral
            # provenance retained by intake, after checking current authority at both ends.
            target_store = execution.ydental_store_id
            access = self.env['ydental.access.service']
            access._check('medical', 'read', target_store.id)
            self.env['ydental.patient.service']._current_relation(row.ydental_patient_id, target_store)
            source_event = self._source_event(row.ydental_source_event_id.id,
                                              row.ydental_patient_id.id, row.ydental_store_id)
            source_task = source_event.ydental_execution_id.ydental_task_id
            target_task = execution.ydental_task_id
            entitlement = target_task.ydental_entitlement_id if target_task else False
            if (candidate.ydental_store_id != target_store or execution.ydental_patient_id != row.ydental_patient_id or
                    candidate.ydental_document_id.ydental_patient_id != row.ydental_patient_id or
                    not source_task or not entitlement or entitlement.ydental_source_task_id != source_task or
                    entitlement.ydental_patient_id != row.ydental_patient_id or
                    entitlement.ydental_store_id != target_store):
                raise AccessError(self.env._('access_denied: The other-store encounter lacks an exact authorized referral from this follow-up source.'))
            event = candidate
            cross_store_referral = True
        execution = event.ydental_execution_id
        if event.state != 'confirmed' or execution.state not in ('reserved', 'handover', 'interrupted'):
            raise UserError(self.env._('Only a confirmed event from an ended actual encounter can complete follow-up.'))
        source_event = row.ydental_source_event_id
        if (event == source_event or execution == source_event.ydental_execution_id or
                event.ydental_actual_at < source_event.ydental_actual_at):
            raise UserError(self.env._('Follow-up completion requires a subsequent actual encounter, separate from its original treatment source.'))
        linked_entitlement = execution.ydental_task_id.ydental_entitlement_id
        if row.ydental_appointment_id:
            if (cross_store_referral or linked_entitlement != row.ydental_appointment_id or
                    row.ydental_appointment_status != 'arrived'):
                raise AccessError(self.env._('access_denied: Complete only from the exact linked reservation after actual arrival.'))
        elif not confirmed_unlinked:
            raise UserError(self.env._('Confirm the patient-to-encounter association explicitly when no reservation is linked.'))
        row._save({'state': 'done', 'ydental_appointment_status': 'seen',
                   'ydental_completed_event_id': event.id, 'ydental_completed_execution_id': execution.id})
        self._cancel_pending_jobs(row, 'Follow-up completed from actual encounter')
        self._audit('complete', row, after={'event_id': event.id, 'execution_id': execution.id,
                    'event_store_id': execution.ydental_store_id.id, 'cross_store_referral': cross_store_referral,
                    'appointment_status': row.ydental_appointment_status, 'state': row.state}, reason=reason)
        return {'id': row.id, 'state': row.state, 'event_id': event.id, 'execution_id': execution.id}

    def _close(self, followup_id, reason):
        row = self._followup(followup_id, True)
        reason = self._text(reason, required=True)
        if row.state in ('done', 'closed'):
            raise UserError(self.env._('A completed or already closed follow-up cannot be closed again.'))
        previous = row.state
        row._save({'state': 'closed', 'ydental_closed_reason': reason})
        self._cancel_pending_jobs(row, 'Follow-up closed')
        self._audit('close', row, before={'state': previous}, after={'state': row.state}, reason=reason)
        return {'id': row.id, 'state': row.state}

    def _reopen(self, followup_id, reason):
        row = self._followup(followup_id, True)
        reason = self._text(reason, required=True)
        if row.state != 'closed':
            raise UserError(self.env._('Only a manually closed follow-up can be reopened.'))
        before = {'state': row.state, 'appointment_status': row.ydental_appointment_status,
                  'appointment_id': row.ydental_appointment_id.id}
        row._save({'state': 'to_notify', 'ydental_closed_reason': False,
                   'ydental_schedule_version': row.ydental_schedule_version + 1})
        self._schedule(row)
        self._create_contact_activity(row, 'A manually closed follow-up was reopened. Review existing contact and appointment history.')
        self._audit('reopen', row, before=before, after={'state': row.state,
                    'appointment_status': row.ydental_appointment_status, 'appointment_id': row.ydental_appointment_id.id},
                    reason=reason)
        return {'id': row.id, 'state': row.state, 'appointment_status': row.ydental_appointment_status}

    def _cancel_pending_jobs(self, row, reason):
        jobs = self._job_model().search([
            ('ydental_followup_id', '=', row.id), ('ydental_state', '=', 'pending'),
        ])
        jobs._save({'ydental_state': 'cancelled', 'ydental_last_error': reason})

    def _create_contact_activity(self, row, note):
        activity_model = self.env['ir.model']._get_id('ydental.followup')
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return False
        prior = self.env['mail.activity'].sudo().search([
            ('res_model_id', '=', activity_model), ('res_id', '=', row.id),
            ('user_id', '=', row.ydental_responsible_id.id), ('summary', '=', 'Follow-up contact required'),
            ('active', '=', True),
        ], limit=1)
        if prior:
            # An active activity is the current work queue entry. Refresh its
            # instruction when the follow-up advances so workers do not keep
            # seeing an obsolete no-contact note after a physical exception.
            prior.write({'note': note})
            return prior
        return self.env['mail.activity'].sudo().with_context(mail_activity_quick_update=True).create({
            'activity_type_id': activity_type.id, 'res_model_id': activity_model, 'res_id': row.id,
            'user_id': row.ydental_responsible_id.id, 'summary': 'Follow-up contact required',
            'note': note, 'date_deadline': fields.Date.context_today(row),
        })

    def _create_passive_from_lab_order(self, order, planned_at, responsible_id):
        """Trusted in-process hook for the dependent laboratory addon; never an RPC action."""
        if order._name != 'ydental.lab.order' or len(order) != 1:
            raise AccessError(self.env._('access_denied: A real laboratory order is required.'))
        order.check_access('read')
        store = order.ydental_store_id
        patient = order.ydental_patient_id
        source_event = order.ydental_source_event_id
        cycle = 'order'
        if not store or not patient or not source_event:
            raise ValidationError(self.env._('The laboratory order must identify its patient and source treatment event.'))
        access = self.env['ydental.access.service']
        _authorize_passive_lab_write(access, store)
        responsible_id = self._id(responsible_id)
        if order.ydental_responsible_id.id != responsible_id:
            raise AccessError(self.env._('access_denied: Passive follow-up must use the laboratory order assigned responsible.'))
        if order.ydental_followup_id:
            return order.ydental_followup_id
        existing = self.env['ydental.followup'].sudo().search([
            ('ydental_lab_order_id', '=', order.id), ('ydental_lab_cycle_key', '=', str(cycle)),
        ], limit=1)
        if existing:
            return existing
        source_event = order.sudo().ydental_source_event_id
        if (source_event.state != 'confirmed' or source_event.ydental_kind != 'treatment' or
                source_event.ydental_execution_id.ydental_patient_id != patient or
                source_event.ydental_store_id != store):
            raise ValidationError(self.env._('The immutable laboratory source is not a confirmed treatment for this patient and store.'))
        user = self._responsible(responsible_id, store)
        planned_at = self._date(planned_at, timezone=store.ydental_timezone)
        deadline_at = self._unbooked_deadline(planned_at, store)
        row = self.env['ydental.followup'].sudo()._new({
            'name': order.name, 'ydental_store_id': store.id, 'ydental_category': 'followup',
            'ydental_patient_id': patient.id, 'ydental_source_event_id': source_event.id,
            'ydental_followup_type': 'lab_arrival', 'ydental_planned_at': planned_at,
            'ydental_deadline_at': deadline_at,
            'ydental_responsible_id': user.id, 'ydental_created_by_id': self.env.uid,
            'ydental_lab_order_id': order.id, 'ydental_lab_cycle_key': str(cycle),
        })
        self._audit('lab_arrival_create', row, after={'lab_order_id': order.id, 'cycle_key': cycle})
        if self._contact_snapshot(patient.sudo()):
            self._schedule(row)
        else:
            row._save({'state': 'to_notify'})
            self._create_contact_activity(row, 'Laboratory item arrived; no verified patient contact path is available.')
        return row

    def _supersede_lab_followup(self, order, reason):
        """Close the parent order's open passive follow-up when rework starts."""
        if order._name != 'ydental.lab.order' or len(order) != 1:
            raise AccessError(self.env._('access_denied: A real laboratory rework order is required.'))
        order.check_access('read')
        store = order.ydental_store_id
        _authorize_passive_lab_write(self.env['ydental.access.service'], store)
        parent = order.ydental_parent_order_id
        if not parent or not parent.ydental_followup_id:
            return self.env['ydental.followup']
        row = parent.ydental_followup_id.sudo()
        reason = self._text(reason, required=True, maximum=300)
        if row.ydental_store_id != store or row.ydental_lab_order_id != parent.id:
            raise AccessError(self.env._('access_denied: The parent follow-up belongs to another store.'))
        if row.state in ('done', 'closed'):
            return row
        previous = row.state
        row._save({'state': 'closed', 'ydental_closed_reason': reason,
                   'ydental_schedule_version': row.ydental_schedule_version + 1})
        self._cancel_pending_jobs(row, 'Passive follow-up superseded by laboratory rework')
        self._audit('lab_rework_supersede', row, before={'state': previous},
                    after={'state': 'closed', 'parent_order_id': parent.id}, reason=reason)
        return row

    def _close_lab_followup_after_exception(self, order, reason):
        """Stop stale patient arrival notices and leave an internal resolution task."""
        if order._name != 'ydental.lab.order' or len(order) != 1:
            raise AccessError(self.env._('access_denied: A real laboratory order is required.'))
        order.check_access('read')
        store = order.ydental_store_id
        _authorize_passive_lab_write(self.env['ydental.access.service'], store)
        row = order.ydental_followup_id
        if not row:
            return self.env['ydental.followup']
        reason = self._text(reason, required=True, maximum=300)
        row = row.sudo()
        if row.ydental_store_id != store or row.ydental_lab_order_id != order.id:
            raise AccessError(self.env._('access_denied: The laboratory follow-up belongs to another order or store.'))
        if row.state in ('done', 'closed'):
            return row
        previous = row.state
        row._save({'state': 'closed', 'ydental_closed_reason': reason,
                   'ydental_schedule_version': row.ydental_schedule_version + 1})
        self._cancel_pending_jobs(row, 'Laboratory item exception closed the arrival notice')
        self._create_contact_activity(
            row, 'Laboratory item was returned or written off. Review the patient communication and fee disposition.')
        self._audit('lab_exception_followup_close', row, before={'state': previous},
                    after={'state': 'closed', 'lab_order_id': order.id}, reason=reason)
        return row

    def _run_due(self):
        """Cron-safe, bounded scan. Jobs are still unique in SQL and are row-claimed below."""
        now = self._now()
        self._expire_appointments(now)
        self._expire_cancelled_reservations()
        self._expire_unbooked_followups(now)
        stale_before = fields.Datetime.to_datetime(fields.Datetime.now()) - timedelta(minutes=5)
        stale = self._job_model().search([
            ('ydental_state', '=', 'dispatching'), ('ydental_attempt_started_at', '<', stale_before),
        ], limit=100, order='ydental_attempt_started_at, id')
        for job in stale:
            self.env.cr.execute(
                "SELECT id FROM ydental_notification_job WHERE id=%s AND ydental_state='dispatching' FOR UPDATE SKIP LOCKED",
                [job.id],
            )
            if not self.env.cr.fetchone():
                continue
            job.invalidate_recordset(['ydental_state', 'ydental_attempt_started_at'])
            if not job.ydental_attempt_started_at or job.ydental_attempt_started_at >= stale_before:
                continue
            job._save({'ydental_state': 'unknown',
                       'ydental_last_error': 'Worker stopped after dispatch started; reconcile using the existing request identifier.'})
            self._followup_to_notify(job, 'Notification dispatch stopped with an unknown outcome; reconcile the existing request before any retry.')
        jobs = self._job_model().search([('ydental_state', '=', 'pending'), ('ydental_due_at', '<=', now)], limit=100,
                                        order='ydental_due_at, id')
        self._postcommit_dispatch(jobs.ids)
        return len(jobs)

    def _expire_unbooked_followups(self, now):
        """Move overdue contacted plans back to the contact queue once per deadline."""
        rows = self.env['ydental.followup'].sudo().search([
            ('state', '=', 'notified'), ('ydental_appointment_id', '=', False),
            ('ydental_deadline_at', '!=', False), ('ydental_deadline_at', '<=', now),
        ], limit=500, order='ydental_deadline_at, id')
        for row in rows:
            self.env.cr.execute(
                "SELECT id FROM ydental_followup WHERE id=%s AND state='notified' FOR UPDATE SKIP LOCKED",
                [row.id],
            )
            if not self.env.cr.fetchone():
                continue
            row.invalidate_recordset(['state'])
            if row.state != 'notified':
                continue
            row._save({'state': 'to_notify', 'ydental_schedule_version': row.ydental_schedule_version + 1})
            self._create_contact_activity(row, 'The contact window ended without an appointment; contact the patient again.')
            self._audit_due('overdue_contact', row, before={'state': 'notified'}, after={'state': 'to_notify'})

    def _expire_cancelled_reservations(self):
        rows = self.env['ydental.followup'].sudo().search([
            ('ydental_appointment_id', '!=', False), ('ydental_appointment_status', '=', 'booked'),
            ('ydental_appointment_id.state', '=', 'cancelled'), ('state', 'not in', ('done', 'closed')),
        ], limit=500, order='id')
        for row in rows:
            self.env.cr.execute(
                "SELECT id FROM ydental_followup WHERE id=%s AND ydental_appointment_status='booked' FOR UPDATE SKIP LOCKED",
                [row.id],
            )
            if not self.env.cr.fetchone():
                continue
            row.invalidate_recordset(['state', 'ydental_appointment_status', 'ydental_appointment_id'])
            if row.state in ('done', 'closed') or row.ydental_appointment_status != 'booked' or not row.ydental_appointment_id or row.ydental_appointment_id.state != 'cancelled':
                continue
            prior_id = row.ydental_appointment_id.id
            row._save({'ydental_appointment_id': False, 'ydental_appointment_status': 'cancelled',
                       'state': 'to_notify', 'ydental_schedule_version': row.ydental_schedule_version + 1})
            self._cancel_pending_jobs(row, 'Reservation was cancelled in intake')
            self._create_contact_activity(row, 'The linked reservation was cancelled; contact the patient to reschedule.')
            self._audit_due('appointment_cancelled', row, before={'appointment_id': prior_id, 'status': 'booked'},
                            after={'appointment_id': False, 'status': 'cancelled', 'state': 'to_notify'})

    def _expire_appointments(self, now):
        rows = self.env['ydental.followup'].sudo().search([
            ('ydental_appointment_id', '!=', False), ('ydental_appointment_status', 'in', ('booked', 'arrived')),
            ('state', 'in', ('planned', 'notified')),
            ('ydental_appointment_id.ydental_claim_id.ydental_slot_id.ydental_end', '<=', now),
        ], limit=500, order='ydental_appointment_at, id')
        for row in rows:
            timezone = pytz.timezone(row.ydental_store_id.ydental_timezone)
            slot = row.ydental_appointment_id.ydental_claim_id.ydental_slot_id
            local_date = pytz.UTC.localize(slot.ydental_start).astimezone(timezone).date()
            local_today = pytz.UTC.localize(fields.Datetime.to_datetime(now)).astimezone(timezone).date()
            if local_today <= local_date:
                continue
            self.env.cr.execute(
                "SELECT id FROM ydental_followup WHERE id=%s AND state IN ('planned','notified') FOR UPDATE SKIP LOCKED",
                [row.id],
            )
            if not self.env.cr.fetchone():
                continue
            row.invalidate_recordset(['state', 'ydental_appointment_status'])
            if row.state not in ('planned', 'notified') or row.ydental_appointment_status not in ('booked', 'arrived'):
                continue
            slot = row.ydental_appointment_id.ydental_claim_id.ydental_slot_id
            arrival = self.env['ydental.intake.arrival'].sudo().search([
                ('ydental_store_id', '=', row.ydental_store_id.id),
                ('ydental_patient_id', '=', row.ydental_patient_id.id), ('ydental_date', '=', local_date),
            ], limit=1)
            before = {'state': row.state, 'appointment_status': row.ydental_appointment_status}
            vals = {'state': 'to_notify', 'ydental_schedule_version': row.ydental_schedule_version + 1}
            if arrival:
                vals.update({'ydental_arrival_id': arrival.id, 'ydental_appointment_status': 'arrived'})
            else:
                vals['ydental_appointment_status'] = 'not_arrived'
            row._save(vals)
            self._cancel_pending_jobs(row, 'Reservation window ended')
            note = ('Actual arrival was recorded, but no treatment event completed the appointment by local day end.' if arrival else
                    'The reservation day ended without an actual arrival; contact the patient.')
            self._create_contact_activity(row, note)
            self._audit_due('appointment_overdue', row, before=before,
                            after={'state': 'to_notify', 'appointment_status': row.ydental_appointment_status})

    def _dispatch_ids(self, job_ids):
        """Claim durably before transport, then persist its result in another transaction.

        This method is called only from a post-commit callback. It owns fresh cursors and
        never commits the caller's source or cron transaction.
        """
        _dispatch_notification_jobs(self.env.cr.dbname, job_ids)

    def _send_transport(self, job):
        """No external transport is enabled in S11. A dependent test addon may override this method."""
        policy = self.env['ydental.followup.policy'].sudo().search([
            ('ydental_store_id', '=', job.ydental_store_id.id),
        ], limit=1)
        if policy and policy.ydental_channel_mode == 'controlled_test_sink':
            followup = job.ydental_followup_id
            if followup:
                activity = self._create_contact_activity(followup, 'CONTROLLED TEST SINK accepted this notification task; patient delivery is not asserted.')
                job._save({'ydental_activity_id': activity.id if activity else False})
                if job.ydental_source_version == followup.ydental_schedule_version and followup.state not in ('done', 'closed'):
                    self._contact_model()._new({
                        'name': 'Controlled test sink acceptance', 'ydental_store_id': job.ydental_store_id.id,
                        'ydental_category': 'followup', 'ydental_followup_id': followup.id,
                        'ydental_contacted_at': fields.Datetime.now(), 'ydental_actor_id': SUPERUSER_ID,
                        'ydental_method': 'message', 'ydental_outcome': 'accepted',
                        'ydental_request_key': 'controlled:' + (job.ydental_request_id or str(job.id)),
                    })
                    self._mark_contact_success(followup, job.ydental_request_id)
            elif job.ydental_source_model == 'ydental.lab.vendor' and job.ydental_responsible_id:
                activity = self._create_source_activity(
                    job.ydental_source_model, job.ydental_source_res_id, job.ydental_responsible_id,
                    'Supplier qualification expiry review',
                    'CONTROLLED TEST SINK accepted an internal review task; no supplier or patient message was sent.',
                )
                job._save({'ydental_activity_id': activity.id if activity else False})
            return 'accepted'
        return 'not_configured'

    def _followup_to_notify(self, job, note):
        row = job.ydental_followup_id
        if row and row.state not in ('done', 'closed'):
            if row.state != 'to_notify':
                row._save({'state': 'to_notify'})
            self._create_contact_activity(row, note)
        elif job.ydental_responsible_id and job.ydental_source_model == 'ydental.lab.vendor':
            self._create_source_activity(job.ydental_source_model, job.ydental_source_res_id,
                                         job.ydental_responsible_id, 'Supplier qualification expiry review', note)

    def _create_source_activity(self, model_name, res_id, user, summary, note):
        model = self.env['ir.model']._get_id(model_name)
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not model or not activity_type:
            return False
        return self.env['mail.activity'].sudo().with_context(mail_activity_quick_update=True).create({
            'activity_type_id': activity_type.id, 'res_model_id': model, 'res_id': res_id,
            'user_id': user.id, 'summary': summary, 'note': note,
            'date_deadline': fields.Date.context_today(self),
        })

    def _callback_signature(self, raw_body, signature):
        secret = self.env['ir.config_parameter'].sudo().get_str('ydental_followup.callback_secret')
        if not secret or not isinstance(signature, str) or not signature.startswith('sha256='):
            raise AccessError(self.env._('access_denied: Notification callback authentication is not configured.'))
        expected = 'sha256=' + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise AccessError(self.env._('access_denied: Invalid notification callback signature.'))

    def _receive_callback(self, raw_body, signature):
        if not isinstance(raw_body, bytes) or len(raw_body) > 8192:
            raise ValidationError(self.env._('Invalid notification callback body.'))
        self._callback_signature(raw_body, signature)
        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError) as error:
            raise ValidationError(self.env._('Invalid notification callback body.')) from error
        if not isinstance(payload, dict) or set(payload) != {'request_id', 'event_id', 'status'}:
            raise ValidationError(self.env._('Invalid notification callback fields.'))
        request_id = self._text(payload['request_id'], required=True, maximum=128)
        event_id = self._text(payload['event_id'], required=True, maximum=128)
        status = payload['status']
        if status not in ('accepted', 'delivered', 'failed'):
            raise ValidationError(self.env._('Invalid notification callback status.'))
        self.env.cr.execute('SELECT id FROM ydental_notification_job WHERE ydental_request_id=%s FOR UPDATE', [request_id])
        hit = self.env.cr.fetchone()
        if not hit:
            raise AccessError(self.env._('access_denied: Notification request identifier is unknown.'))
        job = self._job_model().browse(hit[0])
        prior = self.env['ydental.notification.callback'].sudo().search([
            ('ydental_store_id', '=', job.ydental_store_id.id), ('ydental_provider_event_id', '=', event_id),
        ], limit=1)
        if prior:
            if prior.ydental_job_id != job or prior.ydental_status != status:
                raise UserError(self.env._('Notification callback idempotency key conflicts with prior content.'))
            return {'result': 'duplicate', 'state': job.ydental_state}
        self.env['ydental.notification.callback'].sudo()._new({
            'name': event_id, 'ydental_store_id': job.ydental_store_id.id, 'ydental_category': 'followup',
            'ydental_job_id': job.id, 'ydental_provider_event_id': event_id, 'ydental_status': status,
            'ydental_received_at': fields.Datetime.now(),
        })
        followup = job.ydental_followup_id
        live = job.ydental_state in ('dispatching', 'unknown', 'accepted')
        advance = live and not (job.ydental_state == 'accepted' and status == 'accepted')
        current_schedule = bool(followup and _callback_matches_current_request(
            job.ydental_state, job.ydental_source_version, followup.ydental_schedule_version,
            followup.ydental_active_notification_request_id,
            followup.ydental_active_notification_schedule_version, request_id,
        ))
        # Keep valid receipts for superseded work, but never revive or mutate it.
        if advance and (not followup or current_schedule):
            vals = {'ydental_state': status}
            if status in ('accepted', 'delivered') and not job.ydental_accepted_at:
                vals['ydental_accepted_at'] = fields.Datetime.now()
            if status == 'delivered':
                vals['ydental_delivered_at'] = fields.Datetime.now()
            job._save(vals)
        if advance and current_schedule and followup.state not in ('done', 'closed'):
                if status in ('accepted', 'delivered'):
                    request_contact_key = 'provider-request:' + request_id
                    prior_contact = self._contact_model().search([
                        ('ydental_store_id', '=', job.ydental_store_id.id),
                        ('ydental_request_key', '=', request_contact_key),
                    ], limit=1)
                    if not prior_contact:
                        self._contact_model()._new({
                            'name': 'Provider callback', 'ydental_store_id': job.ydental_store_id.id,
                            'ydental_category': 'followup', 'ydental_followup_id': followup.id,
                            'ydental_contacted_at': fields.Datetime.now(), 'ydental_actor_id': SUPERUSER_ID,
                            'ydental_method': 'message', 'ydental_outcome': status,
                            'ydental_request_key': request_contact_key,
                        })
                    self._mark_contact_success(followup, request_id)
                elif status == 'failed':
                    self._followup_to_notify(job, 'Provider confirmed notification failure; arrange manual contact.')
        self.env['ydental.access.service']._audit(
            'notification.callback.' + status, 'followup', job, job.ydental_store_id.id,
            after={'event_id_hash': hashlib.sha256(event_id.encode()).hexdigest(), 'job_state': job.ydental_state},
            source='provider_callback',
        )
        return {'result': 'accepted', 'state': job.ydental_state}

    def _reconcile_unknown(self, job_id, outcome, evidence):
        self._scope(write=True)
        job_id = self._id(job_id)
        self.env.cr.execute('SELECT id FROM ydental_notification_job WHERE id=%s FOR UPDATE', [job_id])
        if not self.env.cr.fetchone():
            raise AccessError(self.env._('access_denied: Notification job is unavailable.'))
        job = self._job_model().browse(self._id(job_id)).exists()
        if not job or job.ydental_store_id != self.env['ydental.access.service']._scope().ydental_store_id:
            raise AccessError(self.env._('access_denied: Notification job is unavailable.'))
        if outcome not in ('accepted', 'delivered', 'failed'):
            raise UserError(self.env._('Only an unknown notification can be reconciled with an explicit result.'))
        job.invalidate_recordset(['ydental_state'])
        action = _reconciliation_action(job.ydental_state, outcome)
        if action == 'duplicate':
            return {'job_id': job.id, 'state': job.ydental_state, 'result': 'duplicate'}
        if action == 'conflict':
            raise UserError(self.env._('This notification has already been reconciled with a different outcome.'))
        evidence = self._text(evidence, required=True, maximum=120)
        evidence_digest = hashlib.sha256(evidence.encode()).hexdigest()
        vals = {'ydental_state': outcome, 'ydental_last_error': 'Manual reconciliation evidence sha256=' + evidence_digest}
        if outcome in ('accepted', 'delivered') and not job.ydental_accepted_at:
            vals['ydental_accepted_at'] = fields.Datetime.now()
        if outcome == 'delivered':
            vals['ydental_delivered_at'] = fields.Datetime.now()
        job._save(vals)
        if (outcome in ('accepted', 'delivered') and job.ydental_followup_id and
                job.ydental_followup_id.state not in ('done', 'closed') and
                job.ydental_source_version == job.ydental_followup_id.ydental_schedule_version):
            self._contact_model()._new({
                'name': 'Manual notification reconciliation', 'ydental_store_id': job.ydental_store_id.id,
                'ydental_category': 'followup', 'ydental_followup_id': job.ydental_followup_id.id,
                'ydental_contacted_at': fields.Datetime.now(), 'ydental_actor_id': self.env.uid,
                'ydental_method': 'message', 'ydental_outcome': outcome,
            })
            self._mark_contact_success(job.ydental_followup_id, job.ydental_request_id)
        elif outcome == 'failed':
            self._followup_to_notify(job, 'Notification was reconciled as failed; arrange manual contact.')
        self._audit('notification.reconcile', job, after={'state': outcome, 'evidence_sha256': evidence_digest})
        return {'job_id': job.id, 'state': outcome, 'result': 'reconciled'}


def _dispatch_after_commit(dbname, job_ids, clock=None):
    """Run dispatch after commit without holding an unnecessary outer cursor."""
    try:
        _dispatch_notification_jobs(dbname, job_ids, clock)
    except Exception:
        _logger.exception('Committed follow-up notification dispatch will be retried by cron job ids=%s', job_ids)


def _dispatch_notification_jobs(dbname, job_ids, clock=None):
    """Use only the claim and result cursors, preserving durable claim-before-send."""
    for job_id in dict.fromkeys(job_ids):
        claimed = _claim_dispatch(dbname, job_id, clock)
        if not claimed:
            continue
        request_id, terminal = claimed
        if terminal:
            continue
        _dispatch_claimed(dbname, job_id, request_id)


def _claim_dispatch(dbname, job_id, clock=None):
    """Persist the stable request key before invoking any transport code."""
    with Registry(dbname).cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {'ydental_s11_clock': clock} if clock else {})
        service = env['ydental.followup.service']
        Job = env['ydental.notification.job'].sudo()
        cr.execute('SELECT id FROM ydental_notification_job WHERE id=%s FOR UPDATE SKIP LOCKED', [job_id])
        if not cr.fetchone():
            return None
        job = Job.browse(job_id).exists()
        if not job:
            return None
        business_now = fields.Datetime.to_datetime(service._now())
        physical_now = fields.Datetime.to_datetime(fields.Datetime.now())
        if job.ydental_state == 'dispatching':
            if job.ydental_attempt_started_at and job.ydental_attempt_started_at <= physical_now - timedelta(minutes=5):
                job._save({'ydental_state': 'unknown',
                           'ydental_last_error': 'Worker stopped after durable dispatch claim; reconcile using the existing request identifier.'})
                service._followup_to_notify(job, 'Notification outcome is unknown; reconcile the existing request before retrying.')
                cr.commit()
            return None
        if job.ydental_state != 'pending':
            return None
        clock = env.context.get('ydental_s11_clock')
        if clock and clock.store_id != job.ydental_store_id.id:
            return None
        if job.ydental_due_at > business_now:
            return None
        followup = job.ydental_followup_id
        if job.ydental_source_model == 'ydental.lab.vendor':
            vendor = env['ydental.lab.vendor'].sudo().browse(job.ydental_source_res_id).exists()
            cooperation = env['ydental.lab.cooperation'].sudo().search([
                ('ydental_store_id', '=', job.ydental_store_id.id),
                ('ydental_vendor_id', '=', job.ydental_source_res_id), ('active', '=', True),
            ], limit=1)
            local_due_date = pytz.UTC.localize(job.ydental_due_at).astimezone(
                pytz.timezone(job.ydental_store_id.ydental_timezone)).date()
            current_qualification = bool(vendor and cooperation and _supplier_qualification_is_current(
                job.ydental_source_version, vendor.qualification_version, vendor.state,
                fields.Date.to_date(vendor.valid_until), local_due_date,
                job.ydental_store_id.company_id in vendor.company_ids,
                cooperation.active,
            ))
            if not current_qualification:
                job._save({'ydental_state': 'cancelled',
                           'ydental_last_error': 'Supplier qualification version or active store cooperation changed.'})
                cr.commit()
                return None
        if job.ydental_source_model == 'ydental.followup' and (
                not followup or followup.state in ('done', 'closed') or
                followup.ydental_schedule_version != job.ydental_source_version):
            job._save({'ydental_state': 'cancelled', 'ydental_last_error': 'Source schedule is no longer current.'})
            cr.commit()
            return None
        policy = env['ydental.followup.policy'].sudo().search([
            ('ydental_store_id', '=', job.ydental_store_id.id),
        ], limit=1)
        if not policy or not policy.ydental_enabled or policy.ydental_channel_mode == 'disabled':
            job._save({'ydental_state': 'not_configured', 'ydental_last_error': 'Store notification policy or channel is disabled.'})
            service._followup_to_notify(job, 'Automatic notification is disabled; arrange manual contact or internal review.')
            cr.commit()
            return None
        if job.ydental_channel_key == 'patient':
            adjusted_due = service._quiet_hour_due(business_now, policy)
            if adjusted_due > business_now:
                job._save({'ydental_due_at': adjusted_due})
                cr.commit()
                return None
        if followup:
            preference = env['ydental.followup.preference'].sudo().search([
                ('ydental_store_id', '=', followup.ydental_store_id.id),
                ('ydental_patient_id', '=', followup.ydental_patient_id.id),
            ], limit=1)
            has_channel = bool(preference and not preference.ydental_opt_out and (
                (preference.ydental_preferred_channel == 'phone' and followup.ydental_patient_id.ydental_phone_normalized) or
                (preference.ydental_preferred_channel == 'email' and followup.ydental_patient_id.ydental_email) or
                (preference.ydental_preferred_channel == 'message' and followup.ydental_patient_id.ydental_phone_normalized)
            ))
            if not has_channel:
                job._save({'ydental_state': 'not_configured',
                           'ydental_last_error': 'Patient opt-out, manual-only preference, or missing preferred contact.'})
                service._followup_to_notify(job, 'Patient preference or contact details block automatic messaging; arrange authorized manual contact.')
                cr.commit()
                return None
            # Lock the patient so two concurrent dispatchers cannot both pass the cap.
            cr.execute('SELECT id FROM ydental_patient WHERE id=%s FOR UPDATE', [followup.ydental_patient_id.id])
            timezone = pytz.timezone(job.ydental_store_id.ydental_timezone)
            local_now = pytz.UTC.localize(physical_now).astimezone(timezone)
            local_start = timezone.localize(datetime.combine(local_now.date(), time.min)).astimezone(pytz.UTC).replace(tzinfo=None)
            local_end = timezone.localize(datetime.combine(local_now.date() + timedelta(days=1), time.min)).astimezone(pytz.UTC).replace(tzinfo=None)
            # A durable claim is conservatively counted as an outbound attempt, including
            # provider failures and cancellations after claim; new jobs cannot reset the cap.
            cr.execute("""
                SELECT count(*) FROM ydental_notification_job job
                JOIN ydental_followup followup ON followup.id=job.ydental_followup_id
                WHERE job.ydental_store_id=%s AND followup.ydental_patient_id=%s
                  AND job.ydental_channel_key='patient'
                  AND job.ydental_attempt_count > 0
                  AND job.ydental_attempt_started_at >= %s AND job.ydental_attempt_started_at < %s
            """, [job.ydental_store_id.id, followup.ydental_patient_id.id,
                  local_start, local_end])
            if cr.fetchone()[0] >= policy.ydental_daily_limit:
                job._save({'ydental_state': 'not_configured', 'ydental_last_error': 'Patient daily notification limit reached.'})
                service._followup_to_notify(job, 'Patient daily automatic notification limit reached; arrange manual contact.')
                cr.commit()
                return None
        request_id = job.ydental_request_id or secrets.token_urlsafe(24)
        job._save({'ydental_state': 'dispatching', 'ydental_request_id': request_id,
                   'ydental_attempt_count': job.ydental_attempt_count + 1,
                   'ydental_attempt_started_at': fields.Datetime.now()})
        cr.commit()
        return request_id, False


def _dispatch_claimed(dbname, job_id, request_id):
    """Transport and result persistence run after the durable claim transaction."""
    with Registry(dbname).cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        service = env['ydental.followup.service']
        cr.execute('SELECT id FROM ydental_notification_job WHERE id=%s FOR UPDATE', [job_id])
        if not cr.fetchone():
            return
        job = env['ydental.notification.job'].sudo().browse(job_id).exists()
        if not job or job.ydental_state != 'dispatching' or job.ydental_request_id != request_id:
            return
        followup = job.ydental_followup_id
        if followup:
            cr.execute('SELECT id FROM ydental_followup WHERE id=%s FOR UPDATE', [followup.id])
            followup.invalidate_recordset(['state', 'ydental_schedule_version'])
            if (followup.state in ('done', 'closed') or
                    followup.ydental_schedule_version != job.ydental_source_version):
                job._save({'ydental_state': 'cancelled', 'ydental_last_error': 'Source changed before dispatch began.'})
                cr.commit()
                return
        try:
            result = service._send_transport(job)
        except TimeoutError:
            job._save({'ydental_state': 'unknown', 'ydental_last_error': 'Transport timed out; reconcile using the same request identifier.'})
            service._followup_to_notify(job, 'Notification outcome is unknown; reconcile before retrying.')
        except Exception as error:
            _logger.warning('Follow-up notification dispatch failed job=%s class=%s', job.id, type(error).__name__)
            job._save({'ydental_state': 'failed', 'ydental_last_error': type(error).__name__})
            service._followup_to_notify(job, 'Notification failed; arrange manual contact.')
        else:
            job.invalidate_recordset(['ydental_state'])
            if job.ydental_state == 'dispatching':
                if result == 'accepted':
                    job._save({'ydental_state': 'accepted', 'ydental_accepted_at': fields.Datetime.now()})
                elif result == 'unknown':
                    job._save({'ydental_state': 'unknown', 'ydental_last_error': 'Transport outcome unknown.'})
                    service._followup_to_notify(job, 'Notification outcome is unknown; reconcile before retrying.')
                else:
                    job._save({'ydental_state': 'not_configured', 'ydental_last_error': 'Notification channel is not configured.'})
                    service._followup_to_notify(job, 'No notification channel is configured; arrange manual contact.')
        cr.commit()
