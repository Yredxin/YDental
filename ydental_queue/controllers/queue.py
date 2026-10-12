import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


class YDentalQueue(http.Controller):

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.queue.service']

    @http.route('/ydental/queue', type='http', auth='user', methods=['GET'])
    def dashboard(self, **kwargs):
        queue = self._service()
        store = queue.env['ydental.intake.service']._business_read_access()
        access = queue.env['ydental.access.service']
        levels = access._levels(access._membership(queue.env.uid, store.id))
        stations = queue.env['ydental.space.station'].sudo().search([('ydental_store_id', '=', store.id)])
        own = queue._own()
        actor_execution = queue._actor_execution()
        entries = queue._model('entry').search([('ydental_store_id', '=', store.id), ('state', '!=', 'void')])
        station_rows = []
        for station in stations:
            category = {'care': 'medical', 'exam': 'exam', 'pharmacy': 'pharmacy'}.get(station.ydental_kind)
            qualified = set(station.ydental_capability_ids.filtered('active').ids) <= set(queue.env.user.sudo().ydental_capability_ids.filtered('active').ids)
            occupied = queue._model('lease').search_count([('ydental_station_id', '=', station.id), ('ydental_active', '=', True)])
            unresolved = queue._model('execution').search_count([('ydental_lease_id.ydental_station_id', '=', station.id)])
            can_enter = bool(category and levels[category] == 'write' and qualified and station.ydental_capability_ids and
                             station.active and station.ydental_enabled and station.ydental_callable and not occupied and not unresolved and not actor_execution)
            station_rows.append({'id': station.id, 'name': station.name, 'area': station.ydental_queue_area_id.name,
                'capabilities': ', '.join(station.ydental_capability_ids.mapped('name')), 'can_enter': can_enter,
                'reason': request.env._('Resolve your existing execution or on-site verification before entering another workstation.') if actor_execution else (
                    request.env._('Occupied or awaiting on-site verification') if occupied or unresolved else (
                        request.env._('Available for qualified authorized staff') if can_enter else request.env._('Disabled, insufficient permission or capability')))})
        # Frontdesk can see why each exact capability waits and the concrete
        # workstation page to resolve staffing, without hiding the waiting task.
        waiting_rows = []
        for entry in entries:
            holders = queue._model('lease').search([('ydental_store_id', '=', store.id), ('ydental_active', '=', True),
                ('ydental_expires_at', '>', queue._now())]).filtered(
                    lambda lease: lease.ydental_station_id.ydental_queue_area_id == entry.ydental_area_id)
            eligible = []
            reasons = []
            for lease in holders:
                station = lease.ydental_station_id
                reason = queue._eligibility(entry, station, lease.ydental_actor_id)
                if not reason:
                    eligible.append(station.name)
                elif reason not in reasons:
                    reasons.append(reason)
            waiting_rows.append({'entry': entry, 'reason': ', '.join(eligible) if eligible else ' '.join([
                request.env._('No connected authorized workstation covers this exact capability. Open an eligible workstation here.'), *reasons])})
        try:
            heartbeat, timeout = queue._settings()
            config_hint = request.env._('Heartbeat and timeout are explicitly configured. Production approval remains separate.')
        except UserError as error:
            heartbeat, timeout, config_hint = 0, 0, str(error)
        can_call = bool(own and not actor_execution and own.ydental_station_id.ydental_queue_area_id.ydental_missed_limit > 0)
        if own and own.ydental_station_id.ydental_queue_area_id.ydental_missed_limit <= 0:
            config_hint = request.env._('configuration_required: Publish an explicit positive missed-call displacement.')
        return request.render('ydental_queue.ydental_queue_page', {'store': store, 'status': queue._status(),
            'revision': access._scope().ydental_revision, 'stations': station_rows, 'rows': waiting_rows,
            'own': own, 'shift_hint': queue._shift_hint(own), 'config_hint': config_hint,
            'can_write': any(levels[c] == 'write' for c in ('medical', 'exam', 'pharmacy')),
            'heartbeat': heartbeat, 'can_call': can_call}, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/queue/action', type='http', auth='user', methods=['POST'], max_content_length=16384)
    def action(self, operation, revision, connection, payload):
        try:
            queue = self._service(int(revision))._bind_connection(connection)
            args = json.loads(payload)
            if not isinstance(args, dict):
                raise ValidationError(request.env._('Action arguments must be an object.'))
            result = queue._operate(operation, args)
            return request.make_json_response(result, status=409 if result['result'] == 'connection_expired' else 200,
                headers=[('Cache-Control', 'no-store')])
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('queue.action')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
