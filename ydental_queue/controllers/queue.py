import json
import secrets

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
        actor_hold = queue._hold(actor_id=queue.env.uid)
        entries = queue._model('entry').search([('ydental_store_id', '=', store.id), ('state', '!=', 'void')])
        station_rows = []
        for station in stations:
            category = {'care': 'medical', 'exam': 'exam', 'pharmacy': 'pharmacy'}.get(station.ydental_kind)
            qualified = set(station.ydental_capability_ids.filtered('active').ids) <= set(queue.env.user.sudo().ydental_capability_ids.filtered('active').ids)
            occupied = queue._model('lease').search_count([('ydental_station_id', '=', station.id), ('ydental_active', '=', True)])
            expired = queue._model('lease').search_count([('ydental_station_id', '=', station.id),
                ('ydental_store_id', '=', store.id), ('ydental_active', '=', True), ('ydental_expires_at', '<=', queue._now())])
            unresolved = queue._model('execution').search_count([('ydental_lease_id.ydental_station_id', '=', station.id), ('state', 'in', ('serving', 'verify'))])
            unresolved += queue._model('hold').search_count([('ydental_station_id', '=', station.id), ('state', 'in', ('active', 'verify'))])
            can_enter = bool(category and levels[category] == 'write' and qualified and station.ydental_capability_ids and
                             station.active and station.ydental_enabled and station.ydental_callable and not occupied and not unresolved and not actor_execution and not actor_hold)
            station_rows.append({'id': station.id, 'name': station.name, 'area': station.ydental_queue_area_id.name,
                'capabilities': ', '.join(station.ydental_capability_ids.mapped('name')), 'can_enter': can_enter,
                'can_expire': bool(expired and category and levels[category] == 'write'),
                'reason': request.env._('Resolve your existing execution or on-site verification before entering another workstation.') if actor_execution or actor_hold else (
                    request.env._('Occupied or awaiting on-site verification') if occupied or unresolved else (
                        request.env._('Available for qualified authorized staff') if can_enter else request.env._('Disabled, insufficient permission or capability')))})
        # Frontdesk can see why each exact capability waits and the concrete
        # workstation page to resolve staffing, without hiding the waiting task.
        waiting_rows = []
        for entry in entries:
            if entry.state not in ('waiting', 'calling'):
                # Execution/history rows keep their own state; call eligibility
                # must not label an ongoing serving segment as day_closed.
                waiting_rows.append({'entry': entry, 'reason': ''})
                continue
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
        verifications = []
        for execution in queue._model('execution').search([('ydental_store_id', '=', store.id), ('state', 'in', ('verify', 'reserved'))]):
            hold = queue._hold(patient_id=execution.ydental_patient_id.id)
            if execution.state != 'verify' and not (hold and hold.state == 'verify' and hold.ydental_execution_id == execution):
                continue
            station = execution.ydental_lease_id.ydental_station_id
            entry = queue._execution_entry(execution)
            if not queue._service_eligibility(entry, station):
                verifications.append({'execution': execution, 'station': station,
                    'operation': 'takeover_verify' if execution.state == 'verify' else 'handover_verify_hold'})
        try:
            heartbeat, timeout = queue._settings()
            config_hint = request.env._('Heartbeat and timeout are explicitly configured. Production approval remains separate.')
        except UserError as error:
            heartbeat, timeout, config_hint = 0, 0, str(error)
        can_call = bool(own and not queue._busy(own) and not actor_execution and own.ydental_station_id.ydental_queue_area_id.ydental_missed_limit > 0)
        if own and own.ydental_station_id.ydental_queue_area_id.ydental_missed_limit <= 0:
            config_hint = request.env._('configuration_required: Publish an explicit positive missed-call displacement.')
        areas = queue.env['ydental.space.area'].sudo().search([('ydental_store_id', '=', store.id), ('ydental_reporting', '=', True)])
        business_rows = [{'area': a, 'business': queue.env['ydental.supply.service']._business_record(store, a.id)} for a in areas]
        scope = access._scope()
        current_execution = bool(actor_execution and own and actor_execution.state == 'serving'
            and actor_execution.ydental_store_id == store and own.ydental_store_id == store
            and actor_execution.ydental_lease_id == own and own.ydental_expires_at > queue._now()
            and own.ydental_session_id == scope and own.ydental_revision == scope.ydental_revision)
        pending_tasks = queue.env['ydental.intake.task'].sudo().search([
            ('ydental_store_id', '=', store.id), ('state', 'in', ('pending', 'accepted'))])
        task_patients = {}
        if levels['frontdesk'] in ('read', 'write'):
            access._check('frontdesk', 'read')
            relations = queue.env['ydental.patient.service']._current_relations(
                pending_tasks.ydental_patient_id.ids, store, required=False)
            for task in pending_tasks:
                relation = relations.get(task.ydental_patient_id.id)
                patient = relation.ydental_patient_id if relation else False
                if patient and patient.active:
                    task_patients[task.id] = {'id': patient.id, 'name': patient.name,
                                              'number': patient.ydental_number}
        return request.render('ydental_queue.ydental_queue_page' , {'store': store, 'status': queue._status(),
            'revision': access._scope().ydental_revision, 'screen_lang': queue.env.user.lang or 'en_US', 'stations': station_rows, 'rows': waiting_rows,
            'own': own, 'shift_hint': queue._shift_hint(own), 'config_hint': config_hint,
            'can_write': any(levels[c] == 'write' for c in ('medical', 'exam', 'pharmacy')),
            'can_read_medical': levels['medical'] in ('read', 'write'),
            'clinical_installed': 'ydental.clinical.service' in queue.env,
            'heartbeat': heartbeat, 'can_call': can_call, 'verifications': verifications,
            'execution': actor_execution if actor_execution and actor_execution.state == 'serving' else False,
            'can_open_medical_execution': bool(current_execution and actor_execution.ydental_category == 'medical'
                and levels['medical'] == 'write' and 'ydental.clinical.service' in queue.env),
            'can_open_pharmacy_execution': bool(current_execution and actor_execution.ydental_category == 'pharmacy'
                and levels['pharmacy'] == 'write'),
            'actor_hold': actor_hold, 'can_frontdesk': levels['frontdesk'] == 'write',
            'can_append': levels['frontdesk'] == 'write' and queue.env.user.has_group('ydental_queue.ydental_group_append'),
            'return_targets': queue.env['ydental.intake.task'].sudo().search([
                ('ydental_store_id', '=', store.id), ('state', 'in', ('pending', 'accepted'))]).filtered(
                    lambda task: bool(actor_execution and task.ydental_patient_id == actor_execution.ydental_patient_id and
                                      task.ydental_mapping_id.ydental_catalog_id.ydental_kind in ('exam', 'medicine'))),
            'pending_tasks': pending_tasks, 'task_patients': task_patients,
            'can_identify_task_patients': levels['frontdesk'] in ('read', 'write'),
            'business_rows': business_rows, 'can_capacity': levels['capacity'] == 'write',
            'screen_credentials': queue._model('screen.token').search([('ydental_store_id', '=', store.id)]) if levels['capacity'] == 'write' else [],
            'permits': queue._model('append.permit').search([('ydental_store_id', '=', store.id), ('state', 'in', ('active', 'started'))])}, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/queue/action', type='http', auth='user', methods=['POST'], max_content_length=16384)
    def action(self, operation, revision, connection, payload):
        try:
            queue = self._service(int(revision))._bind_connection(connection)
            args = json.loads(payload)
            if not isinstance(args, dict):
                raise ValidationError(request.env._('Action arguments must be an object.'))
            if operation == 'business':
                result = queue.env['ydental.supply.service']._operate('business', args, secrets.token_hex(16))
            else:
                result = queue._operate(operation, args)
            return request.make_json_response(result, status=409 if result['result'] == 'connection_expired' else 200,
                headers=[('Cache-Control', 'no-store')])
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('queue.action')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
