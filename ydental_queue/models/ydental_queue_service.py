import hashlib
import inspect
import secrets
from dataclasses import dataclass
from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import consteq


@dataclass(frozen=True)
class Connection:
    actor_id: int
    session_id: int
    revision: int
    key_hash: str


@dataclass(frozen=True)
class StartPermit:
    actor_id: int
    task_id: int
    lease_id: int


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class YDentalQueueService(models.AbstractModel):
    _name = 'ydental.queue.service'
    _description = 'Workstation connection and patient execution authority'

    def _now(self):
        return fields.Datetime.now()

    def _model(self, entity):
        # Every entity is a literal selected by server code.
        return self.env['ydental.queue.' + entity].sudo()

    def _lock(self):
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [30006])
        mutex = self.env.ref('ydental_queue.ydental_queue_mutex')
        self.env.cr.execute('UPDATE ydental_queue_mutex SET ydental_revision=ydental_revision+1 WHERE id=%s', [mutex.id])
        self.env.invalidate_all()

    def _locks(self):
        self.env['ydental.intake.service']._all_locks()

    def _settings(self):
        params = self.env['ir.config_parameter'].sudo()
        try:
            heartbeat = int(params.get_str('ydental_queue.heartbeat_seconds', ''))
            timeout = int(params.get_str('ydental_queue.timeout_seconds', ''))
        except (ValueError, TypeError) as error:
            raise UserError(self.env._('configuration_required: Publish explicit heartbeat and timeout settings.')) from error
        if not 1 <= heartbeat < timeout <= 86400:
            raise UserError(self.env._('configuration_required: Timeout must exceed the positive heartbeat interval.'))
        return heartbeat, timeout

    def _bind_connection(self, key):
        session = self.env['ydental.access.service']._scope()
        if not isinstance(key, str) or not 32 <= len(key) <= 128 or not key.isalnum():
            raise AccessError(self.env._('access_denied: A holding browser connection is required.'))
        return self.with_context(ydental_queue_connection=Connection(
            self.env.uid, session.id, session.ydental_revision, digest(key)))

    def _connection(self):
        session = self.env['ydental.access.service']._scope(write=True)
        connection = self.env.context.get('ydental_queue_connection')
        if type(connection) is not Connection or (connection.actor_id, connection.session_id, connection.revision) != (
                self.env.uid, session.id, session.ydental_revision):
            raise AccessError(self.env._('access_denied: A holding browser connection is required.'))
        return session, connection

    def _category(self, station):
        category = {'care': 'medical', 'exam': 'exam', 'pharmacy': 'pharmacy'}.get(station.ydental_kind)
        if not category:
            raise AccessError(self.env._('access_denied: This workstation cannot call patients.'))
        return category

    def _station(self, station_id, admission=True):
        access = self.env['ydental.access.service']
        session = access._scope(write=True)
        station = self.env['ydental.space.station'].sudo().browse(
            self.env['ydental.intake.service']._id(station_id)).exists()
        if not station or station.ydental_store_id != session.ydental_store_id:
            raise AccessError(self.env._('access_denied: Select a workstation in the current store.'))
        category = self._category(station)
        member = access._check(category, 'write', write=True)
        caps = station.ydental_capability_ids.filtered('active')
        if not caps or not set(caps.ids) <= set(self.env.user.sudo().ydental_capability_ids.filtered('active').ids):
            raise AccessError(self.env._('access_denied: Actual staff capabilities must cover this workstation.'))
        # Disabling a busy station does not release it. Its holder may heartbeat,
        # exit or resolve its call, but cannot call another patient there.
        if admission and (not station.active or not station.ydental_enabled or not station.ydental_callable or
                          not station.ydental_area_id.active or not station.ydental_floor_id.active or
                          not station.ydental_queue_area_id.active or not station.ydental_queue_area_id.ydental_reporting):
            raise UserError(self.env._('station_unavailable: The workstation or reporting area is disabled.'))
        return station, member, category

    def _own(self):
        return self._model('lease').search([('ydental_actor_id', '=', self.env.uid), ('ydental_active', '=', True)], limit=1)

    def _held(self, lease_id, token, admission=False):
        session, connection = self._connection()
        lease = self._model('lease').browse(self.env['ydental.intake.service']._id(lease_id)).exists()
        if not lease or not lease.ydental_active or lease.ydental_actor_id.id != self.env.uid or (
            lease.ydental_session_id.id, lease.ydental_revision
        ) != (session.id, session.ydental_revision) or not consteq(lease.ydental_connection_hash, connection.key_hash) or (
            not isinstance(token, str) or len(token) > 128 or not consteq(lease.ydental_token_hash, digest(token))
        ):
            raise AccessError(self.env._('access_denied: This connection no longer holds the workstation.'))
        self._station(lease.ydental_station_id.id, admission=admission)
        return lease

    def _busy(self, lease):
        return bool(self._model('entry').search_count([('ydental_lease_id', '=', lease.id), ('state', '=', 'calling')]) or
                    self._model('execution').search_count([('ydental_lease_id', '=', lease.id)]))

    def _audit(self, event, record, after=None):
        self.env['ydental.access.service']._audit('queue.' + event, record.ydental_category,
            record, record.ydental_store_id.id, after=after, source='workstation_service')

    def _expire(self):
        now = self._now()
        expired = self._model('lease').search([('ydental_active', '=', True), ('ydental_expires_at', '<=', now)])
        for lease in expired:
            calls = self._model('entry').search([('ydental_lease_id', '=', lease.id), ('state', '=', 'calling')])
            for entry in calls:
                self._restore_call(entry)
            executions = self._model('execution').search([('ydental_lease_id', '=', lease.id), ('state', '=', 'serving')])
            executions._save({'state': 'verify'})
            executions.ydental_entry_id._save({'state': 'verify'})
            lease._save({'ydental_active': False, 'ydental_release_reason': 'timeout'})
            self._audit('connection_timeout', lease, {'calling_returned': calls.ids, 'verification_required': executions.ids})
        return expired.ids

    def _timeout(self):
        # Fixed scheduler entry, no caller-supplied object or forced-release ID.
        with self.env.cr.savepoint():
            self._locks()
            return self._expire()

    def _operate(self, operation, payload):
        handlers = {'enter': self._enter, 'switch': self._switch, 'exit': self._exit,
                    'heartbeat': self._heartbeat, 'call': self._call, 'missed': self._missed, 'start': self._start}
        if operation not in handlers or not isinstance(payload, dict):
            raise AccessError(self.env._('access_denied: Unknown workstation action.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('Unknown or missing workstation arguments.')) from error
        self._connection()
        # Session is locked before the existing patient/supply/intake sequence.
        # Never lock another session during timeout. Grants take the same fence.
        with self.env.cr.savepoint():
            self._locks()
            self._connection()
            if operation == 'enter':
                self._station(payload.get('station_id'))
            else:
                self._held(payload.get('lease_id'), payload.get('token'))
            expired = self._expire()
            if operation != 'enter' and payload['lease_id'] in expired:
                # Return a committed expiry result. Raising would roll back the
                # fault requeue and allow a stale call to remain authoritative.
                return {'result': 'connection_expired', 'verification_required': bool(self._model('execution').search_count([
                    ('ydental_lease_id', '=', payload['lease_id'])]))}
            return dict(handlers[operation](**payload), result='accepted')

    def _enter(self, station_id):
        station, member, category = self._station(station_id)
        if self._own() or self._model('lease').search_count([('ydental_station_id', '=', station.id), ('ydental_active', '=', True)]):
            raise UserError(self.env._('handover_required: The account or workstation already has a holder.'))
        if self._model('execution').search_count([('ydental_lease_id.ydental_station_id', '=', station.id)]):
            raise UserError(self.env._('handover_required: On-site verification is required before reusing this workstation.'))
        heartbeat, timeout = self._settings()
        session, connection = self._connection()
        token = secrets.token_urlsafe(32)
        lease = self._model('lease')._new({'name': station.name, 'ydental_store_id': station.ydental_store_id.id,
            'ydental_category': category, 'ydental_actor_id': self.env.uid, 'ydental_station_id': station.id,
            'ydental_session_id': session.id, 'ydental_revision': session.ydental_revision,
            'ydental_token_hash': digest(token), 'ydental_connection_hash': connection.key_hash,
            'ydental_heartbeat_at': self._now(), 'ydental_expires_at': self._now() + timedelta(seconds=timeout)})
        self._audit('enter', lease, {'station_id': station.id, 'scheduled_required': False})
        return {'lease_id': lease.id, 'token': token, 'heartbeat_seconds': heartbeat, 'station_id': station.id}

    def _switch(self, lease_id, token, station_id):
        lease = self._held(lease_id, token)
        if self._busy(lease):
            raise UserError(self.env._('handover_required: Resolve the current patient before changing workstations.'))
        station, member, category = self._station(station_id)
        if station == lease.ydental_station_id:
            return {'lease_id': lease.id, 'station_id': station.id, 'token': token, 'heartbeat_seconds': self._settings()[0]}
        if self._model('lease').search_count([('ydental_station_id', '=', station.id), ('ydental_active', '=', True)]) or self._model('execution').search_count([
                ('ydental_lease_id.ydental_station_id', '=', station.id)]):
            raise UserError(self.env._('handover_required: The target workstation is occupied or awaiting verification.'))
        # All target checks finish first. Both writes share the outer savepoint.
        lease._save({'ydental_active': False, 'ydental_release_reason': 'holder_exit'})
        lease.flush_recordset(['ydental_active'])
        self._audit('switch_exit', lease, {'target_station_id': station.id})
        return self._enter(station.id)

    def _exit(self, lease_id, token):
        lease = self._held(lease_id, token)
        if self._busy(lease):
            raise UserError(self.env._('handover_required: Resolve the current patient before exiting.'))
        lease._save({'ydental_active': False, 'ydental_release_reason': 'holder_exit'})
        self._audit('holder_exit', lease)
        return {'lease_id': lease.id}

    def _heartbeat(self, lease_id, token):
        lease = self._held(lease_id, token)
        heartbeat, timeout = self._settings()
        lease._save({'ydental_heartbeat_at': self._now(), 'ydental_expires_at': self._now() + timedelta(seconds=timeout)})
        return {'lease_id': lease.id, 'heartbeat_seconds': heartbeat}

    def _ordered(self, area_id):
        entries = self._model('entry').search([('ydental_area_id', '=', area_id), ('state', '=', 'waiting')])
        return entries.sorted(lambda e: (not (e.ydental_return and not e.ydental_opportunity_used),
                                        e.ydental_order, e.ydental_reported_at, e.id))

    def _call(self, lease_id, token):
        lease = self._held(lease_id, token, admission=True)
        if self._busy(lease):
            raise UserError(self.env._('handover_required: This workstation already has an unresolved patient.'))
        station = lease.ydental_station_id
        candidates = self._ordered(station.ydental_queue_area_id.id).filtered(
            lambda e: e.ydental_capability_id.active and e.ydental_capability_id in station.ydental_capability_ids and
            not self._model('execution').search_count([('ydental_patient_id', '=', e.ydental_patient_id.id)]))
        if not candidates:
            raise UserError(self.env._('no_eligible_waiting: No waiting task matches this workstation capability.'))
        entry = candidates[0]
        self.env['ydental.patient.service']._current_relation(entry.ydental_patient_id, entry.ydental_store_id)
        entry._save({'state': 'calling', 'ydental_lease_id': lease.id,
                     'ydental_call_used_before': entry.ydental_opportunity_used, 'ydental_opportunity_used': True})
        entry.ydental_task_id._save({'ydental_queue_opportunity_used': True})
        self._audit('call', entry, {'lease_id': lease.id, 'station_id': station.id})
        return {'entry_id': entry.id, 'task_id': entry.ydental_task_id.id, 'state': entry.state}

    def _calling(self, lease, entry_id):
        entry = self._model('entry').browse(self.env['ydental.intake.service']._id(entry_id)).exists()
        if not entry or entry.state != 'calling' or entry.ydental_lease_id != lease:
            raise UserError(self.env._('version_conflict: This call no longer belongs to the holding workstation.'))
        return entry

    def _restore_call(self, entry):
        used = entry.ydental_call_used_before
        entry._save({'state': 'waiting', 'ydental_lease_id': False, 'ydental_opportunity_used': used})
        entry.ydental_task_id._save({'ydental_queue_opportunity_used': used})
        # Original rank and all earlier genuine missed calls remain unchanged.

    def _missed(self, lease_id, token, entry_id):
        lease = self._held(lease_id, token)
        entry = self._calling(lease, entry_id)
        count = entry.ydental_area_id.ydental_missed_limit
        if count <= 0:
            raise UserError(self.env._('configuration_required: Publish an explicit positive missed-call displacement.'))
        task = entry.ydental_task_id
        task._save({'ydental_missed_count': task.ydental_missed_count + 1})
        # Normalize the current effective order, inserting after N real waiting
        # positions (or at the tail), including candidates of other capabilities.
        others = self._ordered(entry.ydental_area_id.id)
        ordered = list(others)
        ordered.insert(min(count, len(ordered)), entry)
        for rank, row in enumerate(ordered, 1):
            row._save({'ydental_order': rank})
        entry._save({'state': 'waiting', 'ydental_lease_id': False, 'ydental_opportunity_used': True})
        self._audit('missed', entry, {'missed': task.ydental_missed_count, 'displacement': count})
        return {'entry_id': entry.id, 'missed': task.ydental_missed_count, 'state': entry.state}

    def _start(self, lease_id, token, entry_id):
        lease = self._held(lease_id, token, admission=True)
        entry = self._calling(lease, entry_id)
        if self._model('execution').search_count([('ydental_patient_id', '=', entry.ydental_patient_id.id)]):
            raise UserError(self.env._('handover_required: The patient already has an unresolved actual execution.'))
        station = lease.ydental_station_id
        if entry.ydental_area_id != station.ydental_queue_area_id or entry.ydental_capability_id not in station.ydental_capability_ids:
            raise AccessError(self.env._('access_denied: The called task capability no longer matches this workstation.'))
        task = entry.ydental_task_id
        permit = StartPermit(self.env.uid, task.id, lease.id)
        intake = self.env['ydental.intake.service'].with_context(ydental_queue_start=permit)
        intake._downstream_action('start', {'task_id': task.id, 'version': task.ydental_version}, 'queue-start-' + str(entry.id))
        entry._save({'state': 'serving', 'ydental_started_at': self._now()})
        execution = self._model('execution')._new({'name': entry.name, 'ydental_store_id': entry.ydental_store_id.id,
            'ydental_category': lease.ydental_category, 'ydental_patient_id': entry.ydental_patient_id.id,
            'ydental_entry_id': entry.id, 'ydental_lease_id': lease.id, 'ydental_started_at': self._now()})
        self._audit('start', execution, {'entry_id': entry.id, 'task_id': task.id})
        return {'entry_id': entry.id, 'execution_id': execution.id, 'state': 'serving'}

    def _unresolved_execution(self, patient_id):
        return self._model('execution').search([('ydental_patient_id', '=', patient_id)], limit=1)

    def _handover_contract(self, execution_id):
        # B must implement source validation, saving and a single atomic transition.
        raise AccessError(self.env._('handover_required: On-site handover is not enabled in this batch.'))

    def _document_lock(self, source, operation):
        # S08 owns real document identity and editor locks. No clinical table here.
        raise AccessError(self.env._('access_denied: Real document locking is not connected.'))

    def _status(self):
        self.env['ydental.access.service']._require_internal()
        lease = self._own()
        if not lease:
            return {'store': '', 'area': '', 'station': '', 'state': 'idle'}
        return {'store': lease.ydental_store_id.name, 'area': lease.ydental_station_id.ydental_queue_area_id.name,
                'station': lease.ydental_station_id.name, 'state': 'connected' if lease.ydental_expires_at > self._now() else 'expired'}

    def _shift_hint(self, lease):
        if not lease:
            return ''
        assignment = self.env['ydental.supply.assignment'].sudo().search([
            ('ydental_user_id', '=', self.env.uid), ('ydental_store_id', '=', lease.ydental_store_id.id),
            ('ydental_start', '<=', self._now())], order='ydental_end desc', limit=1)
        if not assignment:
            return self.env._('No assignment required. Qualified authorized staff may sit here.')
        if assignment.ydental_end <= self._now():
            return self.env._('Shift ended. Your connection and accepted queue work continue.')
        return self.env._('Assignment is a reminder, not a workstation ownership rule.')
