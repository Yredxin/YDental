from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class YDentalSyntheticFinance(http.Controller):
    def _access(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision)

    @http.route('/ydental/settlement/synthetic-setup', type='http', auth='user', methods=['GET'])
    def synthetic_setup(self):
        access = self._access()
        store = access._scope().ydental_store_id
        service = access.env['ydental.settlement.service']
        if not service._synthetic_setup_allowed(store):
            raise AccessError(request.env._('access_denied: Synthetic finance setup is unavailable.'))
        return request.render('ydental_settlement.ydental_synthetic_setup_page', {
            'store': store, 'revision': access._scope().ydental_revision,
        }, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/settlement/synthetic-setup', type='http', auth='user', methods=['POST'])
    def synthetic_setup_create(self, revision, confirmed=None, **post):
        try:
            access = self._access(int(revision))
            with request.env.cr.savepoint():
                result = access.env['ydental.settlement.service']._create_synthetic_finance(confirmed == 'yes')
        except (AccessError, UserError, ValidationError, ValueError, TypeError) as error:
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
        return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/settlement/synthetic-receivable', type='http', auth='user', methods=['POST'])
    def synthetic_receivable(self, revision, confirmed=None, **post):
        try:
            access = self._access(int(revision))
            with request.env.cr.savepoint():
                result = access.env['ydental.patient.service']._bind_e2e_synthetic_receivable(confirmed == 'yes')
        except (AccessError, UserError, ValidationError, ValueError, TypeError) as error:
            denied = isinstance(error, AccessError)
            access = request.env['ydental.access.service']
            if denied:
                access._denial('patient.synthetic_receivable')
            access._audit('patient.synthetic_receivable_attempt', 'patient', request.env.user,
                result='denied', source='isolated_synthetic_setup',
                after={'failure_kind': 'permission_or_scope' if denied else 'request_or_state'})
            return request.make_json_response({'error': 'access_denied' if denied else 'request_failed'},
                status=403 if denied else 409, headers=[('Cache-Control', 'no-store')])
        return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
