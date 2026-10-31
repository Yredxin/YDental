import json
import logging
import secrets
from urllib.parse import urlencode

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.ydental_access.controllers.access import YDentalDataSet

_logger = logging.getLogger(__name__)


class YDentalPatientDataSet(YDentalDataSet):

    @http.route()
    def call_kw(self, model, method, args, kwargs, path=None):
        if model == 'res.partner':
            # Dataset replaces the request context with the RPC context. Bind
            # patient Contacts reads to this login's SID, never a client flag.
            # A login without a workspace retains ordinary Contacts access.
            context = dict(kwargs.get('context') or {})
            context.pop('ydental_binding', None)
            access = request.env['ydental.access.service']
            session = access._existing_session_for_key(request.session.sid[:42]) if request.env.user.has_group(
                'ydental_base.ydental_base_group_user'
            ) else False
            if session:
                context['ydental_binding'] = access._bind(session).env.context['ydental_binding']
            kwargs = dict(kwargs, context=context)
        return super().call_kw(model, method, args, kwargs, path)


class YDentalPatient(http.Controller):

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.patient.service']

    def _values(self, service):
        access = service.env['ydental.access.service']
        session = access._scope()
        store = service._access()
        member = access._membership(service.env.uid, store.id)
        levels = access._levels(member)
        confirm_label = service.env._('Confirm verified merge')
        refresh_label = service.env._('Refresh identity versions')
        reject_label = service.env._('Reject with reason')
        return {'store': store, 'revision': session.ydental_revision, 'key': lambda: secrets.token_hex(16),
                'sex_labels': service.env['ydental.patient']._fields['ydental_sex']._description_selection(service.env),
                'contact_labels': service.env['ydental.patient.contact']._fields['ydental_relation']._description_selection(service.env),
                'merge_decisions': [('confirm', confirm_label), ('refresh_merge', refresh_label), ('reject', reject_label)],
                'can_admin': any(levels[c] == 'write' for c in ('patient', 'frontdesk')),
                'can_frontdesk': levels['frontdesk'] == 'write',
                'can_care': any(levels[c] in ('read', 'write') for c in ('medical', 'exam')),
                'can_medical_write': levels['medical'] == 'write', 'can_export': levels['export'] == 'write',
                'is_group': access._is_group_manager(), 'status_labels': {
                    'pending_configuration': service.env._('Policy text or approval needs completion'),
                    'pending_verification': service.env._('Verify this store document requirements'),
                }}

    def _render(self, template, values):
        return request.render(template, values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/patients', type='http', auth='user', methods=['GET'])
    def patients(self, q='', **kwargs):
        service = self._service()
        values = self._values(service)
        merges = service.env['ydental.patient.merge'].search_fetch([], [
            'name', 'state', 'ydental_version', 'ydental_conflicts', 'ydental_reason'], limit=50, order='id desc')
        values.update(patients=service._search(q), q=q, merges=merges)
        return self._render('ydental_patient.ydental_patient_list', values)

    @http.route('/ydental/patients/<int:patient_id>', type='http', auth='user', methods=['GET'])
    def patient(self, patient_id, merge_q='', merge_page='1', **kwargs):
        service = self._service()
        values = self._values(service)
        patient = service._patient(patient_id)
        patient = service.env['ydental.patient'].browse(patient.id)
        patient.read(['name', 'ydental_number'])
        candidates = service.env['ydental.patient']
        term = ''
        page = 1
        has_more = False
        if values['can_admin'] and patient.active:
            term = service._text(merge_q, 100)
            if not isinstance(merge_page, str) or not merge_page.isdecimal() or not 1 <= len(merge_page) <= 4 or not 1 <= int(merge_page) <= 1000:
                return request.make_response('无效的候选页码。', status=400, headers=[('Cache-Control', 'no-store')])
            page = int(merge_page)
            if term:
                service._access(write=True)
                domain = fields.Domain('id', '!=', patient.id) & fields.Domain('active', '=', True) & fields.Domain('ydental_merged_into_id', '=', False)
                matches = fields.Domain.OR([fields.Domain('name', 'ilike', term), fields.Domain('ydental_number', '=', term)])
                mapping = service.env['ydental.patient.number'].search([('name', '=', term)], limit=1)
                if mapping:
                    matches |= fields.Domain('id', '=', mapping.ydental_patient_id.id)
                domain &= matches
                found = service.env['ydental.patient'].search(domain, order='id', offset=(page - 1) * 20, limit=21)
                candidates, has_more = found[:20], len(found) > 20
        def merge_page_url(number):
            return '/ydental/patients/%s?%s#request-merge' % (patient.id, urlencode({'merge_q': term, 'merge_page': number}))
        values.update(patient=patient, duplicates=service._duplicates(patient.id), prompts=service._prompts(patient.id),
            relations=service.env['ydental.patient.relation'].search([
                ('ydental_patient_id', '=', patient.id), ('ydental_superseded_by_id', '=', False)]),
            contacts=service.env['ydental.patient.contact'].with_context(active_test=False).search([('ydental_patient_id', '=', patient.id)]),
            numbers=service.env['ydental.patient.number'].search([('ydental_patient_id', '=', patient.id)]),
            merge_candidates=candidates, merge_q=term, merge_page=page, merge_has_more=has_more,
            merge_page_url=merge_page_url)
        return self._render('ydental_patient.ydental_patient_detail', values)

    @http.route('/ydental/patients/<int:patient_id>/clinical', type='http', auth='user', methods=['GET'])
    def clinical(self, patient_id, purpose=None, **kwargs):
        service = self._service()
        access = service.env['ydental.access.service']._patient_care(patient_id, purpose)
        service = access.env['ydental.patient.service']
        values = self._values(service)
        patient = service._patient(patient_id)
        records = service.env['ydental.patient.clinical'].search_fetch([
            ('ydental_patient_id', '=', patient.id)], ['name', 'ydental_store_id', 'ydental_allergies',
            'ydental_prior_history', 'ydental_medication', 'ydental_identity_snapshot', 'ydental_version'])
        values.update(patient=patient, clinical=records, purpose=purpose)
        return self._render('ydental_patient.ydental_patient_clinical_page', values)

    @http.route('/ydental/patients/<int:patient_id>/attachment/<int:attachment_id>',
                type='http', auth='user', methods=['GET'])
    def attachment(self, patient_id, attachment_id, purpose=None, **kwargs):
        service = self._service()
        access = service.env['ydental.access.service']._patient_care(patient_id, purpose)
        attachment = access.env['ir.attachment'].browse(attachment_id)
        attachment_meta = attachment.sudo()
        if attachment_meta.res_model not in access._get_patient_care_sources():
            raise AccessError(request.env._('access_denied: A typed patient clinical source is required.'))
        source = access.env[attachment_meta.res_model].browse(attachment_meta.res_id)
        source.check_access('read')
        field_name = access._get_patient_care_sources()[attachment_meta.res_model]
        if source[field_name].id != service._patient(patient_id).id:
            raise AccessError(request.env._('access_denied: The attachment belongs to another patient scope.'))
        attachment._can_return_content('raw')
        response = access.env['ir.binary']._get_stream_from(attachment).get_response(as_attachment=True)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route('/ydental/patients/action', type='http', auth='user', methods=['POST'], max_content_length=32768)
    def action(self, operation, revision, key, payload=None, output=None, **form):
        service = None
        try:
            service = self._service(int(revision))
            args = json.loads(payload) if payload is not None else self._form_arguments(operation, form)
            if not isinstance(args, dict):
                raise ValidationError(request.env._('Action arguments must be an object.'))
            with request.env.cr.savepoint():
                if operation == 'export':
                    if set(args) != {'patient_id'}:
                        raise AccessError(request.env._('access_denied: Select one patient to export.'))
                    service._access()
                    patient = service._patient(args['patient_id'])
                    result = service.env['ydental.patient'].browse(patient.id).export_data([
                        'ydental_number', 'name', 'ydental_birth_date', 'ydental_sex', 'ydental_phone', 'ydental_email'])
                else:
                    result = service._operate(operation, args, key)
        except (AccessError, UserError, TypeError, ValueError, KeyError) as error:
            access = request.env['ydental.access.service']
            try:
                access._denial('patient.action')
            except Exception as log_error:
                _logger.error('Patient denial log failed: %s', type(log_error).__name__)
            try:
                # Bind the existing server session, not the stale client revision.
                # Keep a failure to record the denial separate from the first error.
                with request.env.cr.savepoint():
                    session = access._existing_session_for_key(request.session.sid[:42])
                    if session:
                        access = access._bind(session)
                        access._audit('patient.action.denied', 'patient', session, session.ydental_store_id.id,
                                      result='denied', reason='access_denied_or_invalid_action', source='http_adapter')
            except Exception as audit_error:
                _logger.error('Patient denial audit failed: %s', type(audit_error).__name__)
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                                              headers=[('Cache-Control', 'no-store')])
        if output == 'json' or operation == 'export':
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        if operation == 'create':
            return request.redirect('/ydental/patients/%s' % result['id'])
        if form.get('patient_id'):
            return request.redirect('/ydental/patients/%s' % int(form['patient_id']))
        return request.redirect('/ydental/patients')

    def _form_arguments(self, operation, form):
        if operation in ('create', 'edit'):
            values = {key: form.get(key, '') for key in ('name', 'birth_date', 'birth_note', 'sex', 'phone', 'phone_region', 'email')}
            result = {'values': values}
            if operation == 'edit':
                result.update(patient_id=int(form['patient_id']), version=int(form['version']))
            return result
        if operation in ('relation', 'export'):
            return {'patient_id': int(form['patient_id'])}
        if operation == 'arrival':
            return {'patient_id': int(form['patient_id']), 'reason': form.get('reason', '')}
        if operation == 'archive':
            return {'patient_id': int(form['patient_id']), 'version': int(form['version']), 'reason': form['reason']}
        if operation == 'contact':
            result = {'patient_id': int(form['patient_id']), 'name': form['name'], 'relation': form['relation'],
                'relationship': form['relationship'], 'phone': form.get('phone', ''),
                'phone_region': form.get('phone_region', ''), 'email': form.get('email', ''),
                'verified': form.get('verified') == 'yes', 'verification_note': form.get('verification_note', '')}
            if form.get('contact_id'):
                result.update(contact_id=int(form['contact_id']), version=int(form['version']),
                              active=form.get('active') == 'yes')
            return result
        if operation == 'clinical':
            result = {'patient_id': int(form['patient_id']), 'values': {
                key: form.get(key, '') for key in ('allergies', 'prior_history', 'medication')}}
            if form.get('record_id'):
                result.update(record_id=int(form['record_id']), version=int(form['version']))
            return result
        if operation == 'policy':
            return {'name': form['name'], 'code': form['code'], 'body_reference': form.get('body_reference', ''),
                    'approved': form.get('approved') == 'yes', 'required': True}
        if operation == 'request_merge':
            return {'source_id': int(form['patient_id']), 'target_id': int(form['target_id']), 'reason': form['reason']}
        if operation in ('confirm', 'reject', 'refresh_merge'):
            return {'request_id': int(form['request_id']), 'version': int(form['version']), 'reason': form['reason']}
        raise AccessError(request.env._('access_denied: Unknown patient form action.'))
