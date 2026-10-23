import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class YDentalFollowup(http.Controller):

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.followup.service']

    def _render(self, template, values):
        return request.render(template, values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/followups', type='http', auth='user', methods=['GET'])
    def followups(self, **kwargs):
        service = self._service()
        session, _member = service._scope()
        model = service.env['ydental.followup']
        rows = model.search_fetch([
            ('ydental_store_id', '=', session.ydental_store_id.id), ('state', '!=', 'done'),
        ], ['name', 'ydental_patient_id', 'ydental_followup_type', 'ydental_planned_at',
            'ydental_appointment_at', 'ydental_appointment_status', 'ydental_responsible_id', 'state'],
            limit=100, order='ydental_planned_at, id')
        events = service.env['ydental.treatment.event'].search_fetch([
            ('ydental_store_id', '=', session.ydental_store_id.id), ('ydental_kind', '=', 'treatment'),
            ('state', '=', 'confirmed'),
            ('ydental_execution_id.state', 'in', ('reserved', 'handover', 'interrupted')),
        ], ['ydental_execution_id', 'ydental_business_date', 'ydental_catalog_id', 'state'],
            limit=500, order='ydental_business_date desc, id desc')
        event_patients = events.mapped('ydental_execution_id.ydental_patient_id')
        appointments = service.env['ydental.intake.service']._followup_reservation_options(
            rows.mapped('ydental_patient_id').ids)
        arrivals = service.env['ydental.intake.arrival'].search_fetch([
            ('ydental_store_id', '=', session.ydental_store_id.id),
        ], ['ydental_patient_id', 'ydental_date', 'ydental_occurred_at'], limit=500,
            order='ydental_occurred_at desc')
        contacts = service.env['ydental.followup.contact'].search_fetch([
            ('ydental_store_id', '=', session.ydental_store_id.id),
            ('ydental_followup_id', 'in', rows.ids),
        ], ['ydental_followup_id', 'ydental_contacted_at', 'ydental_actor_id',
            'ydental_method', 'ydental_outcome', 'ydental_note'], limit=1000,
            order='ydental_contacted_at desc, id desc') if rows else service.env['ydental.followup.contact']
        events_by_patient = {}
        appointments_by_patient = {}
        arrivals_by_patient = {}
        contacts_by_followup = {}
        for event in events:
            patient_id = event.ydental_execution_id.ydental_patient_id.id
            events_by_patient.setdefault(patient_id, []).append(event)
        # Cross-store event choices are listed only through the exact retained intake
        # referral source-task link and only when the current user has target-store
        # medical read authority plus a current patient relation there.
        for row in rows:
            source_task = row.ydental_source_event_id.ydental_execution_id.ydental_task_id
            if not source_task:
                continue
            referrals = service.env['ydental.intake.entitlement'].sudo().search([
                ('ydental_source_task_id', '=', source_task.id), ('ydental_patient_id', '=', row.ydental_patient_id.id),
                # Untimed referrals are accepted as walk-ins by native intake.
                ('ydental_channel', 'in', ('reservation', 'walkin')), ('state', 'in', ('held', 'started')),
            ], limit=100)
            for referral in referrals:
                target_store = referral.ydental_store_id
                if target_store == session.ydental_store_id:
                    continue
                try:
                    service.env['ydental.access.service']._check('medical', 'read', target_store.id)
                    service.env['ydental.patient.service']._current_relation(row.ydental_patient_id, target_store)
                except AccessError:
                    continue
                referred_events = service.env['ydental.treatment.event'].sudo().search([
                    ('ydental_store_id', '=', target_store.id), ('ydental_kind', '=', 'treatment'),
                    ('ydental_patient_id', '=', row.ydental_patient_id.id),
                    ('state', '=', 'confirmed'), ('ydental_execution_id.state', 'in', ('reserved', 'handover', 'interrupted')),
                    ('ydental_execution_id.ydental_task_id.ydental_entitlement_id', '=', referral.id),
                ], limit=100, order='ydental_business_date desc, id desc')
                events_by_patient.setdefault(row.ydental_patient_id.id, []).extend(referred_events)
        for appointment in appointments:
            appointments_by_patient.setdefault(appointment['patient_id'], []).append(appointment)
        for arrival in arrivals:
            arrivals_by_patient.setdefault(arrival.ydental_patient_id.id, []).append(arrival)
        for contact in contacts:
            contacts_by_followup.setdefault(contact.ydental_followup_id.id, []).append(contact)
        jobs = service.env['ydental.notification.job'].search_fetch([
            ('ydental_store_id', '=', session.ydental_store_id.id),
            ('ydental_state', 'in', ('failed', 'unknown', 'not_configured')),
        ], ['name', 'ydental_followup_id', 'ydental_event_type', 'ydental_due_at', 'ydental_state',
            'ydental_last_error', 'ydental_request_id'], limit=100, order='id desc')
        return self._render('ydental_followup.followup_list', {
            'rows': rows, 'store': session.ydental_store_id,
            'jobs': jobs, 'revision': session.ydental_revision, 'current_user': service.env.user,
            'patients': event_patients, 'source_events': events,
            'events_by_patient': events_by_patient, 'appointments_by_patient': appointments_by_patient,
            'arrivals_by_patient': arrivals_by_patient, 'contacts_by_followup': contacts_by_followup,
        })

    @http.route('/ydental/followups/action', type='http', auth='user', methods=['POST'], max_content_length=32768)
    def action(self, operation, revision, payload=None, **form):
        service = None
        try:
            service = self._service(int(revision))
            args = json.loads(payload) if payload is not None else self._form_arguments(operation, form)
            if not isinstance(args, dict):
                raise ValidationError(request.env._('Action arguments must be an object.'))
            result = service._operate(operation, args)
        except (AccessError, UserError, ValidationError, TypeError, ValueError, KeyError) as error:
            status = 403 if isinstance(error, AccessError) else 409
            return request.make_json_response({'error': str(error)}, status=status,
                                              headers=[('Cache-Control', 'no-store')])
        if result.get('id'):
            return request.redirect('/ydental/followups#followup-%s' % result['id'])
        return request.redirect('/ydental/followups')

    def _form_arguments(self, operation, form):
        if operation == 'create':
            return {'patient_id': int(form['patient_id']), 'source_event_id': int(form['source_event_id']),
                    'followup_type': form['followup_type'], 'planned_at': form['planned_at'],
                    'deadline_at': form.get('deadline_at') or False,
                    'responsible_id': int(form.get('responsible_id') or request.env.uid)}
        if operation == 'contact':
            return {'followup_id': int(form['followup_id']), 'method': form['method'],
                    'outcome': form['outcome'], 'note': form.get('note', ''),
                    'request_key': form.get('request_key', '')}
        if operation == 'set_preference':
            return {'patient_id': int(form['patient_id']), 'opt_out': form.get('opt_out') == 'yes',
                    'preferred_channel': form['preferred_channel']}
        if operation == 'reschedule':
            return {'followup_id': int(form['followup_id']), 'planned_at': form['planned_at'],
                    'deadline_at': form.get('deadline_at') or False,
                    'responsible_id': int(form.get('responsible_id') or request.env.uid)}
        if operation == 'link_appointment':
            appointment_id = form.get('appointment_id')
            status = form.get('status', 'booked')
            return {'followup_id': int(form['followup_id']),
                    'appointment_id': int(appointment_id) if appointment_id else False,
                    'status': status}
        if operation == 'record_arrival':
            return {'followup_id': int(form['followup_id']), 'arrival_id': int(form['arrival_id'])}
        if operation == 'complete':
            return {'followup_id': int(form['followup_id']), 'event_id': int(form['event_id']),
                    'confirmed_unlinked': form.get('confirmed_unlinked') == 'yes',
                    'reason': form.get('reason', '')}
        if operation in ('close', 'reopen', 'mark_not_arrived'):
            args = {'followup_id': int(form['followup_id']), 'reason': form['reason']}
            return args
        if operation == 'reconcile_unknown':
            return {'job_id': int(form['job_id']), 'outcome': form['outcome'], 'evidence': form['evidence']}
        raise ValidationError(request.env._('Unknown follow-up form action.'))

    @http.route('/ydental/followups/provider-callback', type='http', auth='public', csrf=False,
                methods=['POST'], save_session=False, max_content_length=8192)
    def provider_callback(self, **kwargs):
        raw_body = request.httprequest.get_data(cache=False)
        signature = request.httprequest.headers.get('X-YDental-Signature', '')
        try:
            result = request.env['ydental.followup.service'].sudo()._receive_callback(raw_body, signature)
        except (AccessError, UserError, ValidationError, TypeError, ValueError, KeyError) as error:
            status = 403 if isinstance(error, AccessError) else 409
            return request.make_json_response({'error': str(error)}, status=status,
                                              headers=[('Cache-Control', 'no-store')])
        return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
