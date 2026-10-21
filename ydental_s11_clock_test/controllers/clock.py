import os
from datetime import datetime, timedelta, timezone

from odoo import http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request

from ..models.clock import EXPECTED_DB, guard, run_id, session_hash


class S11ClockController(http.Controller):

    def _authorize(self):
        guard(request.env)
        if request.env.cr.dbname != EXPECTED_DB or not request.env.user.has_group('ydental_s11_clock_test.group_operator'):
            raise AccessError('S11 debug clock operator permission is required.')
        remote = request.httprequest.remote_addr
        if remote not in ('127.0.0.1', '::1'):
            raise AccessError('S11 debug clock is available only over loopback.')
        service = request.env['ydental.access.service']
        session = service._session_for_key(request.session.sid[:42])
        service._scope()
        return service, session, session_hash(request.session.sid[:42])

    @http.route('/ydental/s11/debug-clock', type='http', auth='user', methods=['GET'])
    def page(self, **kwargs):
        service, access_session, key = self._authorize()
        physical_now = datetime.now(timezone.utc).replace(tzinfo=None)
        row = request.env['ydental.s11.clock.session'].sudo().search([
            ('session_hash', '=', key), ('actor_id', '=', request.env.uid),
            ('store_id', '=', access_session.ydental_store_id.id), ('run_id', '=', run_id()),
            ('expires_at', '>', physical_now),
        ], limit=1)
        response = request.render('ydental_s11_clock_test.clock_page', {
            'simulated_now': row.simulated_now if row else False,
            'run_id': run_id(), 'csrf_token': request.csrf_token(),
        })
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route('/ydental/s11/debug-clock/action', type='http', auth='user', methods=['POST'], csrf=True, max_content_length=4096)
    def action(self, operation, simulated_at=None, reason=None, **kwargs):
        service, access_session, key = self._authorize()
        if operation not in ('set', 'advance', 'clear') or not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 240:
            raise ValidationError('Choose a valid clock action and give a short test reason.')
        ClockSession = request.env['ydental.s11.clock.session'].sudo()
        Event = request.env['ydental.s11.clock.event'].sudo()
        request.env.cr.execute('SELECT id FROM ydental_s11_clock_session WHERE session_hash=%s FOR UPDATE', [key])
        request.env.cr.fetchone()
        row = ClockSession.search([('session_hash', '=', key)], limit=1)
        now_real = datetime.now(timezone.utc).replace(tzinfo=None)
        stored_now = row.simulated_now if row else False
        active_row = bool(row and row.actor_id.id == request.env.uid
                          and row.store_id.id == access_session.ydental_store_id.id
                          and row.run_id == run_id() and row.expires_at > now_real)
        old = row.simulated_now if active_row else False
        if operation == 'clear':
            if row:
                row.unlink()
            Event.create({'run_id': run_id(), 'actor_id': request.env.uid, 'store_id': access_session.ydental_store_id.id,
                          'operation': 'clear', 'old_now': stored_now, 'physical_at': now_real, 'reason': reason.strip()})
            response = request.make_json_response({'status': 'cleared', 'physical_now_utc': now_real.isoformat() + 'Z'})
        else:
            try:
                requested = datetime.fromisoformat((simulated_at or '').replace('Z', '+00:00'))
            except ValueError as error:
                raise ValidationError('Use an ISO-8601 timestamp with an explicit UTC offset.') from error
            if requested.tzinfo is None or requested.utcoffset() != timedelta(0):
                raise ValidationError('Synthetic business time must be UTC.')
            requested = requested.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)
            if abs(requested - now_real) > timedelta(days=30):
                raise ValidationError('Synthetic time must stay within 30 days of physical UTC.')
            if requested < now_real:
                raise ValidationError('Synthetic business time cannot be set before physical UTC.')
            if old and requested < old:
                raise ValidationError('Synthetic time can only move forward; clear the session to start a new run.')
            if operation == 'advance' and not old:
                raise ValidationError('Start a clock before advancing it.')
            expiry = now_real + timedelta(hours=8)
            values = {'simulated_now': requested, 'expires_at': expiry, 'run_id': run_id(),
                      'actor_id': request.env.uid, 'store_id': access_session.ydental_store_id.id}
            if row:
                row.write(values)
            else:
                ClockSession.create(dict(values, session_hash=key))
            Event.create({'run_id': run_id(), 'actor_id': request.env.uid, 'store_id': access_session.ydental_store_id.id,
                          'operation': 'start' if not old else 'advance', 'old_now': old,
                          'new_now': requested, 'physical_at': now_real, 'reason': reason.strip()})
            response = request.make_json_response({'status': 'active', 'simulated_now_utc': requested.isoformat() + 'Z',
                                                   'physical_now_utc': now_real.isoformat() + 'Z', 'run_id': run_id()})
        response.headers['Cache-Control'] = 'no-store'
        return response
