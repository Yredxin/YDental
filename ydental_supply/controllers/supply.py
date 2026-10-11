import json
import secrets
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class YDentalSupply(http.Controller):

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.supply.service']

    @http.route('/ydental/supply', type='http', auth='user', methods=['GET'])
    def dashboard(self, week_start=None, group_by='station', **kwargs):
        values = self._service()._dashboard(week_start, group_by)
        values['new_key'] = lambda: secrets.token_hex(16)
        return request.render('ydental_supply.ydental_supply_page', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/supply/today', type='http', auth='user', methods=['GET'])
    def today(self, **kwargs):
        values = self._service()._today()
        values['new_key'] = lambda: secrets.token_hex(16)
        return request.render('ydental_supply.ydental_supply_today', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/supply/action', type='http', auth='user', methods=['POST'], max_content_length=65536)
    def action(self, operation, revision, key, payload=None, output=None, **form):
        try:
            service = self._service(int(revision))
            with request.env.cr.savepoint():
                args = json.loads(payload) if payload is not None else self._form_args(service, operation, form)
                if not isinstance(args, dict):
                    raise ValidationError(request.env._('Action arguments must be an object.'))
                if operation == 'feedback':
                    service._keys(args, ('id', 'reason'))
                    result = service._feedback(args['id'], args['reason'], key)
                elif operation == 'suggest':
                    service._keys(args, ('id',))
                    result = service._workbench_suggestion(args['id'])
                elif operation in ('policy', 'assign', 'adjust', 'cancel_assignment', 'copy', 'batch', 'slot',
                                   'publish', 'resize', 'extend', 'convert', 'business', 'resolve'):
                    result = service._operate(operation, args, key)
                else:
                    raise AccessError(request.env._('access_denied: Unknown supply action.'))
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
        if output == 'json' or operation == 'suggest':
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        return request.redirect('/ydental/supply/today' if operation == 'feedback' else '/ydental/supply')

    def _form_args(self, service, operation, form):
        def ids(name):
            return [int(value) for value in request.httprequest.form.getlist(name) if value.strip()]

        def utc(name):
            store = service.env['ydental.access.service']._scope().ydental_store_id
            value = datetime.fromisoformat(form[name]).replace(tzinfo=ZoneInfo(store.ydental_timezone))
            return value.astimezone(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')

        if operation == 'policy':
            return {'name': form['name'], 'rounding': form['rounding'], 'phone_pool': form['phone_pool'],
                'cutoff_minutes': int(form['cutoff_minutes']), 'mode': form['mode'], 'approved': form.get('approved') == 'yes',
                'station_id': int(form.get('station_id') or 0), 'area_id': int(form.get('area_id') or 0),
                'reservation_weight': int(form['reservation_weight']), 'walkin_weight': int(form['walkin_weight']), 'reason': form['reason']}
        if operation in ('assign', 'adjust'):
            values = {'user_id': int(form['user_id']), 'station_id': int(form.get('station_id') or 0),
                'area_id': int(form.get('area_id') or 0), 'start': utc('start'), 'end': utc('end'), 'reason': form['reason']}
            return values if operation == 'assign' else {'id': int(form['id']), 'version': int(form['version']), 'values': values, 'reason': form['reason']}
        if operation == 'batch':
            store = service.env['ydental.access.service']._scope().ydental_store_id
            rows = []
            for day in form['dates'].split(','):
                times = [datetime.fromisoformat(day.strip() + 'T' + form[name]).replace(tzinfo=ZoneInfo(store.ydental_timezone)).astimezone(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S') for name in ('start_time', 'end_time')]
                rows.append({'user_id': int(form['user_id']), 'station_id': int(form.get('station_id') or 0), 'area_id': int(form.get('area_id') or 0), 'start': times[0], 'end': times[1], 'reason': form['reason']})
            return {'rows': rows}
        if operation == 'copy':
            return {'week_start': form['week_start']}
        if operation == 'slot':
            return {'station_id': int(form['station_id']), 'start': utc('start'), 'end': utc('end'),
                'total': int(form['total']), 'capability_ids': ids('capability_ids'), 'reason': form['reason']}
        if operation in ('publish', 'resize', 'extend', 'cancel_assignment', 'resolve'):
            args = {'id': int(form['id']), 'version': int(form['version']), 'reason': form['reason']}
            if operation == 'publish':
                args['user_ids'] = ids('user_ids')
            if operation == 'resize':
                args['total'] = int(form['total'])
            if operation == 'extend':
                args['end'] = utc('end')
            if operation == 'resolve':
                args['entity'] = form['entity']
            return args
        if operation == 'convert':
            return {'id': int(form['id'])}
        if operation in ('feedback', 'suggest'):
            return {'id': int(form['id']), **({'reason': form['reason']} if operation == 'feedback' else {})}
        if operation == 'business':
            return {'area_id': int(form['area_id']), 'state': form['state'], 'reason': form['reason'],
                **({'version': int(form['version'])} if form.get('version') else {})}
        raise AccessError(request.env._('access_denied: Unknown supply action.'))
