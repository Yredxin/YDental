import json
from urllib.parse import urlencode

from odoo import fields, http
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
        request.update_context(lang='zh_CN')
        service = self._service().with_context(lang='zh_CN')
        session, _member = service._scope()
        levels = service.env['ydental.access.service']._levels(_member)
        try:
            source_q = kwargs.get('source_q', '').strip()
            if len(source_q) > 100:
                raise ValueError()
            followup_page = int(kwargs.get('followup_page', '1'))
            if not 1 <= followup_page <= 1000:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            return request.make_json_response({'error': request.env._('Invalid follow-up selection.')}, status=400)
        model = service.env['ydental.followup']
        domain = fields.Domain('ydental_store_id', '=', session.ydental_store_id.id) & fields.Domain('state', '!=', 'done')
        try:
            if kwargs.get('followup_id'):
                domain &= fields.Domain('id', '=', int(kwargs['followup_id']))
        except (ValueError, TypeError):
            return request.make_json_response({'error': request.env._('Invalid follow-up selection.')}, status=400)
        rows = model.search_fetch(domain, ['name', 'ydental_patient_id', 'ydental_followup_type', 'ydental_planned_at',
            'ydental_appointment_at', 'ydental_appointment_status', 'ydental_responsible_id', 'state'],
            offset=(followup_page - 1) * 50 if not kwargs.get('followup_id') else 0,
            limit=51, order='ydental_planned_at, id')
        followup_more, rows = len(rows) > 50, rows[:50]
        medical_read = levels['medical'] in ('read', 'write')
        events = service.env['ydental.treatment.event']
        source_next = ''
        if medical_read:
            try:
                events, source_next = service._source_choices(source_q, kwargs.get('source_cursor', ''))
            except ValidationError:
                return request.make_json_response({'error': request.env._('Invalid follow-up selection.')}, status=400)
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
        event_next = ''
        # Cross-store event choices are listed only through the exact retained intake
        # referral source-task link and only when the current user has target-store
        # medical read authority plus a current patient relation there.
        focused = rows if kwargs.get('followup_id') else model
        for row in focused:
            if not medical_read:
                continue
            if not service.env['ydental.patient.service']._current_relation(
                    row.ydental_patient_id, session.ydental_store_id, required=False):
                continue
            source_task = row.ydental_source_event_id.ydental_execution_id.ydental_task_id
            if not source_task:
                continue
            if row.ydental_appointment_id and row.ydental_appointment_status != 'arrived':
                continue
            allowed_stores = []
            memberships = service.env['ydental.access.membership']
            if not row.ydental_appointment_id:
                memberships = memberships.sudo().search([
                    ('ydental_user_id', '=', service.env.uid), ('active', '=', True)])
            for member in memberships:
                target_store = member.ydental_store_id
                if target_store == session.ydental_store_id:
                    continue
                try:
                    service._check_target_store_company(target_store)
                    service.env['ydental.access.service']._check('medical', 'read', target_store.id)
                    service.env['ydental.patient.service']._current_relation(row.ydental_patient_id, target_store)
                except AccessError:
                    continue
                allowed_stores.append(target_store.id)
            event_domain = fields.Domain('ydental_kind', '=', 'treatment') & fields.Domain('state', '=', 'confirmed')
            event_domain &= fields.Domain('ydental_category', '=', 'medical') & fields.Domain('ydental_patient_id', '=', row.ydental_patient_id.id)
            event_domain &= fields.Domain('ydental_execution_id.ydental_patient_id', '=', row.ydental_patient_id.id)
            event_domain &= fields.Domain('ydental_document_id.ydental_patient_id', '=', row.ydental_patient_id.id)
            event_domain &= fields.Domain('ydental_execution_id.state', 'in', ('reserved', 'handover', 'interrupted', 'completed'))
            event_domain &= fields.Domain('id', '!=', row.ydental_source_event_id.id)
            event_domain &= fields.Domain('ydental_execution_id', '!=', row.ydental_source_event_id.ydental_execution_id.id)
            event_domain &= fields.Domain('ydental_actual_at', '>=', row.ydental_source_event_id.ydental_actual_at)
            local_scope = fields.Domain('ydental_store_id', '=', session.ydental_store_id.id) & fields.Domain(
                'ydental_execution_id.ydental_store_id', '=', session.ydental_store_id.id)
            if row.ydental_appointment_id:
                local_scope &= fields.Domain('ydental_execution_id.ydental_task_id.ydental_entitlement_id', '=', row.ydental_appointment_id.id)
            scopes = [local_scope]
            if not row.ydental_appointment_id:
                for target_store_id in allowed_stores:
                    entitlement = 'ydental_execution_id.ydental_task_id.ydental_entitlement_id.'
                    scopes.append(fields.Domain('ydental_store_id', '=', target_store_id) &
                        fields.Domain('ydental_execution_id.ydental_store_id', '=', target_store_id) &
                        fields.Domain(entitlement + 'ydental_source_task_id', '=', source_task.id) &
                        fields.Domain(entitlement + 'ydental_patient_id', '=', row.ydental_patient_id.id) &
                        fields.Domain(entitlement + 'ydental_store_id', '=', target_store_id) &
                        fields.Domain(entitlement + 'ydental_channel', 'in', ('reservation', 'walkin')) &
                        fields.Domain(entitlement + 'state', 'in', ('held', 'started')))
            event_domain &= fields.Domain.OR(scopes)
            context = {'kind': 'complete', 'followup': row.id}
            try:
                event_domain &= service._event_cursor_domain(context, kwargs.get('event_cursor', ''))
            except ValidationError:
                return request.make_json_response({'error': request.env._('Invalid follow-up selection.')}, status=400)
            found = service.env['ydental.treatment.event'].sudo().search(event_domain,
                order='ydental_actual_at desc, id desc', limit=51)
            events_by_patient[row.ydental_patient_id.id] = found[:50]
            event_next = service._event_cursor(context, found[49]) if len(found) > 50 else ''
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
            'can_write': service.env['ydental.access.service']._levels(_member)['followup'] == 'write',
            'can_complete': levels['followup'] == 'write' and levels['medical'] == 'write',
            'state_labels': dict(model._fields['state']._description_selection(service.env)),
            'contact_method_labels': dict(service.env['ydental.followup.contact']._fields['ydental_method']._description_selection(service.env)),
            'contact_outcome_labels': dict(service.env['ydental.followup.contact']._fields['ydental_outcome']._description_selection(service.env)),
            'job_state_labels': dict(service.env['ydental.notification.job']._fields['ydental_state']._description_selection(service.env)),
            'job_type_labels': dict(service.env['ydental.notification.job']._fields['ydental_event_type']._description_selection(service.env)),
            'type_labels': dict(model._fields['ydental_followup_type']._description_selection(service.env)),
            'appointment_labels': dict(model._fields['ydental_appointment_status']._description_selection(service.env)),
            'lab_contact_allowed': {row.id: row.state not in ('done', 'closed') and row.ydental_lab_contact_stage != 'stopped' and (
                row.ydental_lab_contact_stage != 'waiting' or service._lab_reservation_is_current(row)) for row in rows},
            'jobs': jobs, 'revision': session.ydental_revision, 'current_user': service.env.user,
            'source_events': events, 'medical_read': medical_read,
            'source_q': source_q, 'source_next': source_next, 'source_cursor': kwargs.get('source_cursor', ''),
            'event_next': event_next,
            'followup_page': followup_page, 'followup_more': followup_more,
            'focused_followup': focused[:1].id if focused else False,
            'followup_page_url': lambda page: '/ydental/followups?' + urlencode({'followup_page': page}),
            'source_page_url': lambda cursor: '/ydental/followups?' + urlencode({'source_q': source_q, 'source_cursor': cursor}),
            'event_page_url': lambda row, cursor: '/ydental/followups?' + urlencode({'followup_id': row.id, 'event_cursor': cursor}) + '#followup-%s' % row.id,
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
            if form.get('ui_source') == 'patient_event':
                patient_id, source_event_id = form['source_choice'].split(':')
            else:
                patient_id, source_event_id = form['patient_id'], form['source_event_id']
            return {'patient_id': int(patient_id), 'source_event_id': int(source_event_id),
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
