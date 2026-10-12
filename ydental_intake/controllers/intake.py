import json
import secrets

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.ydental_patient.controllers.patient import YDentalPatientDataSet


class YDentalIntake(http.Controller):

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.intake.service']

    @http.route('/ydental/intake', type='http', auth='user', methods=['GET'])
    def dashboard(self, **kwargs):
        service = self._service()
        store = service._read_access()
        env = service.env
        access = env['ydental.access.service']
        levels = access._levels(access._membership(env.uid, store.id))
        values = {'store': store, 'revision': access._scope().ydental_revision,
            'key': lambda: secrets.token_hex(16), 'can_frontdesk': levels['frontdesk'] == 'write',
            'catalogs': env['ydental.intake.catalog'].search([]), 'mappings': env['ydental.intake.mapping'].search([]),
            'tasks': env['ydental.intake.task'].search([], order='id desc', limit=100),
            'entitlements': env['ydental.intake.entitlement'].search([], order='id desc', limit=100),
            'arrivals': env['ydental.intake.arrival'].search([], order='id desc', limit=30),
            'patients': env['ydental.patient'].search([('active', '=', True)], limit=100),
            'referrals': env['ydental.intake.referral'].search([('state', '=', 'pending')], limit=100),
            'positions': env['ydental.intake.position'].search([('ydental_active', '=', True)])}
        return request.render('ydental_intake.ydental_intake_page', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/intake/prices', type='http', auth='user', methods=['GET'])
    def prices(self, **kwargs):
        service = self._service()
        access = service.env['ydental.access.service']
        store = access._check('price', 'read').ydental_store_id
        levels = access._levels(access._membership(service.env.uid, store.id))
        env = service.env
        values = {'store': store, 'revision': access._scope().ydental_revision, 'key': lambda: secrets.token_hex(16),
            'can_price': levels['price'] == 'write', 'can_catalog': levels['price'] == 'write' and access._is_group_manager(),
            'catalogs': env['ydental.intake.catalog'].with_context(active_test=False).search([]),
            'mappings': env['ydental.intake.mapping'].with_context(active_test=False).search([]),
            'prices': env['ydental.intake.price'].search([], order='id desc'),
            'snapshots': env['ydental.intake.snapshot'].search([], order='id desc', limit=30),
            'capabilities': env['ydental.access.capability'].sudo().search([('active', '=', True)]),
            'uoms': env['uom.uom'].sudo().search([], limit=100), 'currencies': env['res.currency'].sudo().search([('active', '=', True)]),
            'areas': env['ydental.space.area'].sudo().search([('ydental_store_id', '=', store.id), ('active', '=', True)])}
        return request.render('ydental_intake.ydental_intake_price_page', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/intake/action', type='http', auth='user', methods=['POST'], max_content_length=32768)
    def action(self, operation, revision, key, payload=None, output=None, **form):
        service = None
        try:
            service = self._service(int(revision))
            args = json.loads(payload) if payload is not None else self._form_arguments(operation, form)
            if not isinstance(args, dict):
                raise ValidationError(request.env._('Action arguments must be an object.'))
            result = service._operate(operation, args, key)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            if service:
                access = service.env['ydental.access.service']
                session = access._scope()
                access._audit('intake.action.denied', 'frontdesk', session, session.ydental_store_id.id,
                    result='denied', reason='access_denied_or_invalid_action', source='http_adapter')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
        if output == 'json':
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        return request.redirect('/ydental/intake/prices' if operation in ('catalog', 'catalog_edit', 'mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot') else '/ydental/intake')

    def _form_arguments(self, operation, form):
        # Typed, explicit form schemas. Payload JSON receives the same service
        # signature validation and never selects a model, domain or field list.
        schemas = {
            'catalog': ('code name kind capability_id uom_id qualification', 'capability_id uom_id'),
            'catalog_edit': ('record_id version name active', 'record_id version'),
            'mapping': ('catalog_id area_id execution_area_id', 'catalog_id area_id execution_area_id'),
            'mapping_edit': ('record_id version active', 'record_id version'),
            'price': ('catalog_id currency_id unit_price start end reason', 'catalog_id currency_id'),
            'review': ('record_id version reason', 'record_id version'),
            'publish': ('record_id version reason', 'record_id version'),
            'snapshot': ('catalog_id currency_id quantity source policy', 'catalog_id currency_id'),
            'reserve': ('patient_id mapping_id start end channel', 'patient_id mapping_id'),
            'register': ('patient_id mapping_id start end', 'patient_id mapping_id'),
            'walkin_report': ('patient_id mapping_id start end', 'patient_id mapping_id'),
            'arrive': ('patient_id', 'patient_id'),
            'report': ('task_id version', 'task_id version'),
            'void': ('task_id version reason cancel_qualification', 'task_id version'),
            'cancel': ('record_id version reason', 'record_id version'),
            'reschedule': ('record_id version mapping_id start end reason', 'record_id version mapping_id'),
            'refer_timed': ('source_task_id version mapping_id start end reason', 'source_task_id version mapping_id'),
            'refer_untimed': ('source_task_id version mapping_id valid_until reason', 'source_task_id version mapping_id'),
            'accept_referral': ('record_id version start end', 'record_id version'),
        }
        if operation not in schemas:
            raise AccessError(request.env._('access_denied: Unknown intake form action.'))
        names, integers = schemas[operation]
        result = {name: form[name] for name in names.split() if name in form and form[name] != ''}
        if operation == 'publish' and form.get('replace_choice'):
            replacement_id, replacement_version = form['replace_choice'].split(':')
            result.update(replace_id=int(replacement_id), replace_version=int(replacement_version))
        for name in integers.split():
            if name in result:
                result[name] = int(result[name])
        for name in ('active', 'cancel_qualification'):
            if name in result:
                result[name] = result[name] == 'yes'
        for name in ('unit_price', 'quantity'):
            if name in result:
                result[name] = float(result[name])
        for name in ('start', 'end', 'valid_until'):
            if name in result:
                result[name] = result[name].replace('T', ' ')
        return result


class YDentalIntakeDataSet(YDentalPatientDataSet):

    @http.route()
    def call_kw(self, model, method, args, kwargs, path=None):
        if model in ('product.template', 'product.product', 'product.pricelist', 'product.pricelist.item'):
            context = dict(kwargs.get('context') or {})
            context.pop('ydental_binding', None)
            access = request.env['ydental.access.service']
            session = access._existing_session_for_key(request.session.sid[:42]) if request.env.user.has_group(
                'ydental_base.ydental_base_group_user'
            ) else False
            if session:
                context['ydental_binding'] = access._bind(session, context.get('ydental_revision')).env.context['ydental_binding']
            kwargs = dict(kwargs, context=context)
        return super().call_kw(model, method, args, kwargs, path)
