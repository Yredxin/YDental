import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from odoo.addons.web.controllers.dataset import DataSet


class YDentalAccess(http.Controller):

    def _service(self, revision=None):
        service = request.env['ydental.access.service']
        session = service._session_for_key(request.session.sid[:42])
        return service._bind(session, revision)

    @http.route('/ydental/access', type='http', auth='user', methods=['GET'])
    def dashboard(self, **kwargs):
        service = self._service()
        values = service._dashboard()
        response = request.render('ydental_access.ydental_access_page', values)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route('/ydental/access/action', type='http', auth='user', methods=['POST'], max_content_length=65536)
    def action(self, operation, revision, payload=None, output=None, **form):
        # Only typed, explicit arguments reach private fixed-model services.
        try:
            revision = int(revision)
            service = self._service(revision)
            if payload is None:
                args = self._form_arguments(operation, form, service)
            else:
                args = json.loads(payload)
                if not isinstance(args, dict):
                    raise ValidationError(request.env._('Action arguments must be an object.'))
            with request.env.cr.savepoint():
                result = self._execute(service, operation, args)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            # The failed business savepoint is rolled back; this is a separate
            # denial fact in the outer request transaction, never a success event.
            service = self._service()
            session = service._scope()
            service._audit('action.denied', 'personnel', session, session.ydental_store_id.id,
                           result='denied', reason='access_denied_or_invalid_action', source='http_adapter')
            response = request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409)
            response.headers['Cache-Control'] = 'no-store'
            return response
        if output == 'json':
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        if operation == 'preview':
            values = {'preview': result, 'targets_json': json.dumps(args['targets']), 'revision': revision,
                      'categories': service.env['ydental.access.grant']._fields['ydental_category']._description_selection(service.env),
                      'level_labels': dict(service.env['ydental.access.grant']._fields['ydental_level']._description_selection(service.env))}
            return request.render('ydental_access.ydental_template_preview', values,
                                  headers=[('Cache-Control', 'no-store')])
        return request.redirect('/ydental/access')

    def _execute(self, service, operation, args):
        if operation == 'switch' and set(args) == {'store_id'}:
            return {'revision': service._switch(args['store_id'])}
        if operation == 'store' and set(args) == {'name', 'company_id', 'timezone'}:
            return service._create_store(args['name'], args['company_id'], args['timezone'])
        if operation == 'grant' and set(args) == {'user_id', 'store_id', 'levels'}:
            return {'membership_id': service._grant(args['user_id'], args['store_id'], args['levels'])}
        if operation == 'join' and set(args) == {'user_id', 'store_id'}:
            return {'membership_id': service._join(args['user_id'], args['store_id'])}
        if operation == 'remove' and set(args) == {'user_id', 'store_id'}:
            return service._remove(args['user_id'], args['store_id'])
        if operation == 'depart' and set(args) == {'user_id'}:
            return service._depart(args['user_id'])
        if operation == 'account' and set(args) == {'name', 'login', 'store_id'}:
            return service._create_account(args['name'], args['login'], args['store_id'])
        if operation == 'profile' and set(args) == {'user_id', 'job_title', 'capability_ids'}:
            return service._update_profile(args['user_id'], args['job_title'], args['capability_ids'])
        if operation == 'manager' and set(args) == {'user_id', 'store_id', 'appointed'}:
            return service._set_manager(args['user_id'], args['store_id'], args['appointed'])
        if operation == 'policy' and set(args) == {'manager_policy', 'password_minlength', 'inactivity_minutes', 'require_mfa'}:
            return service._configure_policy(**args)
        if operation == 'invite' and set(args) == {'user_id', 'store_id'}:
            return service._request_invitation(args['user_id'], args['store_id'])
        if operation == 'preview' and set(args) == {'template_id', 'targets'}:
            return service._template_preview(args['template_id'], args['targets'])
        if operation == 'apply' and set(args) == {'template_id', 'targets', 'receipt'}:
            return service._apply_template(args['template_id'], args['targets'], args['receipt'])
        raise AccessError(request.env._('access_denied: Unknown action or arguments.'))

    def _form_arguments(self, operation, form, service):
        if operation == 'switch':
            return {'store_id': int(form['store_id'])}
        if operation == 'store':
            return {'name': form['name'], 'company_id': int(form['company_id']), 'timezone': form['timezone']}
        store_id = service._scope().ydental_store_id.id
        if operation in ('join', 'remove', 'invite'):
            return {'user_id': int(form['user_id']), 'store_id': store_id}
        if operation == 'grant':
            return {'user_id': int(form['user_id']), 'store_id': store_id,
                    'levels': {form['category']: form['level']}}
        if operation == 'account':
            return {'name': form['name'], 'login': form['login'], 'store_id': store_id}
        if operation == 'preview':
            return {'template_id': int(form['template_id']), 'targets': [[int(form['user_id']), store_id]]}
        if operation == 'apply':
            return {'template_id': int(form['template_id']), 'targets': json.loads(form['targets']), 'receipt': form['receipt']}
        if operation == 'depart':
            return {'user_id': int(form['user_id'])}
        if operation == 'profile':
            return {'user_id': int(form['user_id']), 'job_title': form['job_title'],
                    'capability_ids': [int(i) for i in form.get('capability_ids', '').split(',') if i.strip()]}
        if operation == 'manager':
            return {'user_id': int(form['user_id']), 'store_id': store_id, 'appointed': form['appointed'] == 'true'}
        if operation == 'policy' and form.get('approved') == 'yes':
            return {'manager_policy': form['manager_policy'], 'password_minlength': int(form['password_minlength']),
                    'inactivity_minutes': int(form['inactivity_minutes']), 'require_mfa': form['require_mfa'] == 'true'}
        raise AccessError(request.env._('access_denied: Unknown action or arguments.'))

    @http.route('/ydental/access/attachment/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def attachment(self, attachment_id, purpose=None, **kwargs):
        service = self._service().with_context(ydental_purpose='care' if purpose == 'care' else False)
        attachment = service.env['ir.attachment'].browse(attachment_id)
        if attachment.sudo().res_model not in service._get_sources().values():
            raise AccessError(request.env._('access_denied: A registered source attachment is required.'))
        attachment._can_return_content('raw')
        response = service.env['ir.binary']._get_stream_from(attachment).get_response(as_attachment=True)
        response.headers['Cache-Control'] = 'no-store'
        return response


class YDentalDataSet(DataSet):

    def _bind_kwargs(self, kwargs):
        context = dict(kwargs.get('context') or {})
        service = request.env['ydental.access.service']
        session = service._existing_session_for_key(request.session.sid[:42])
        if not session:
            raise AccessError(request.env._('access_denied: Open the YDental store workspace first.'))
        # RPC context is untrusted. Only the numeric revision is consumed here;
        # a client purpose does not authorize care. Binding comes from the SID.
        bound = service._bind(session, context.get('ydental_revision'))
        context['ydental_binding'] = bound.env.context['ydental_binding']
        return dict(kwargs, context=context)

    @http.route()
    def call_kw(self, model, method, args, kwargs, path=None):
        if model in request.env['ydental.access.service']._get_sources().values() or (
            method == 'export_data' and request.env.user.has_group('ydental_base.ydental_base_group_user')
        ):
            read_methods = {
                'read', 'search', 'search_read', 'search_fetch', 'search_count', 'fields_get',
                'get_views', 'web_read', 'web_search_read', 'name_search', 'read_group',
                'formatted_read_group', 'formatted_read_grouping_sets', 'export_data',
            }
            if method not in read_methods and type((kwargs.get('context') or {}).get('ydental_revision')) is not int:
                raise AccessError(request.env._('access_denied: A page revision is required for writes.'))
            kwargs = self._bind_kwargs(kwargs)
        return super().call_kw(model, method, args, kwargs, path)

    @http.route()
    def call_button(self, model, method, args, kwargs, path=None):
        if model in request.env['ydental.access.service']._get_sources().values():
            if type((kwargs.get('context') or {}).get('ydental_revision')) is not int:
                raise AccessError(request.env._('access_denied: A page revision is required for actions.'))
            kwargs = self._bind_kwargs(kwargs)
        return super().call_button(model, method, args, kwargs, path)
