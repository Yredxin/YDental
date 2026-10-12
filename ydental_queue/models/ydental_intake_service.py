from dataclasses import dataclass

from odoo import models
from odoo.exceptions import AccessError, UserError

from .ydental_queue_service import StartPermit


@dataclass(frozen=True)
class Admission:
    actor_id: int
    task_id: int


class YDentalIntakeService(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _business_read_access(self):
        try:
            return super()._business_read_access()
        except AccessError:
            return self.env['ydental.access.service']._check('pharmacy', 'read').ydental_store_id

    def _valid_task(self, task, store):
        reason = self.env['ydental.queue.service']._hold_target_reason(task)
        if reason:
            raise UserError(reason)
        start = self.env.context.get('ydental_queue_start')
        queue = self.env['ydental.queue.service']
        if type(start) is StartPermit and (start.actor_id, start.task_id) == (self.env.uid, task.id):
            self._authorize_downstream('start', {'task_id': task.id})
            entry = queue._model('entry').search([('ydental_task_id', '=', task.id), ('state', '=', 'calling'),
                ('ydental_lease_id', '=', start.lease_id)], limit=1)
            if not entry or queue._queue_day_expired(entry):
                raise UserError(self.env._('day_closed: This business-day queue segment is terminal.'))
            patient = self.env['ydental.patient.service']._business_patient(task.ydental_patient_id.id)
            if task.ydental_patient_id != patient:
                raise UserError(self.env._('version_conflict: Refresh the canonical task identity.'))
            self.env['ydental.patient.service']._current_relation(patient, store)
            self._target(task.ydental_mapping_id.id, store)
            if task.ydental_entitlement_id and (task.ydental_entitlement_id.state != 'held' or
                    task.ydental_entitlement_id.ydental_claim_id.state != 'held' or
                    task.ydental_entitlement_id.ydental_claim_id.ydental_slot_id.state != 'published'):
                raise UserError(self.env._('qualification_required: Review the original held qualification.'))
            return patient
        service = self.with_context(ydental_queue_admission=Admission(self.env.uid, task.id))
        patient = super(YDentalIntakeService, service)._valid_task(task, store)
        if task.ydental_continuation_snapshot and task.ydental_continuation_snapshot != self.env['ydental.queue.service']._service_snapshot(task):
            raise UserError(self.env._('version_conflict: Continuation service requirements changed; review the source.'))
        return patient

    def _open(self, mapping):
        admission = self.env.context.get('ydental_queue_admission')
        if type(admission) is Admission and admission.actor_id == self.env.uid:
            task = self._model('task').browse(admission.task_id)
            if task.ydental_mapping_id == mapping and self.env['ydental.queue.service']._permit_valid(task):
                return None
        return super()._open(mapping)

    def _all_locks(self):
        super()._all_locks()
        self.env['ydental.queue.service']._lock()

    def _report(self, store, task_id, version):
        task = self._get('task', task_id, store)
        queue = self.env['ydental.queue.service']
        date = self.env['ydental.supply.service']._date(store)
        old = queue._model('entry').search([('ydental_task_id', '=', task.id),
            ('ydental_business_date', '<', date), ('state', 'in', ('waiting', 'calling'))])
        if old:
            self._version(task, version)
            patient = self._valid_task(task, store)
            if not self._model('arrival').search_count([('ydental_store_id', '=', store.id),
                    ('ydental_patient_id', 'in', self.env['ydental.patient.service']._identity_ids(patient)), ('ydental_date', '=', date)]):
                raise UserError(self.env._('Record actual arrival before service reporting.'))
            # Explicit new-day report ends the old daily position, never changes
            # its date/number or copies its missed/return/permit opportunity.
            old._save({'state': 'day_closed', 'ydental_lease_id': False})
            self._model('position').search([('ydental_task_id', '=', task.id), ('ydental_active', '=', True)])._save({
                'ydental_active': False, 'ydental_reason': 'Explicit new business day report'})
            for entry in old:
                queue._audit('day_closed', entry, {'reason': 'Explicit new business day report'})
        return super()._report(store, task_id, version)

    def _queue_assert_idle(self, task):
        super()._queue_assert_idle(task)
        reason = self.env['ydental.queue.service']._hold_target_reason(task)
        if reason:
            raise UserError(reason)
        if self.env['ydental.queue.service']._unresolved_execution(task.ydental_patient_id.id):
            raise UserError(self.env._('handover_required: This patient has an unresolved actual execution.'))

    def _queue_accept(self, task, previous):
        queue = self.env['ydental.queue.service']
        queue._lock()
        queue._expire()
        queue._settings()
        self._queue_assert_idle(task)
        mapping = task.ydental_mapping_id
        if previous:
            # Target validation already succeeded. Withdraw under this savepoint
            # before inserting the new unique patient position; failure rolls back.
            self._queue_void(previous, 'Successful explicit task switch')
        date = self.env['ydental.supply.service']._date(task.ydental_store_id)
        entry = queue._model('entry').search([('ydental_task_id', '=', task.id), ('ydental_business_date', '=', date)], limit=1)
        if entry and entry.state == 'day_closed':
            raise UserError(self.env._('day_closed: This business-day queue segment is terminal.'))
        if entry:
            # A durable task retains its rank, date, return classification and
            # genuine missed count through re-report/area-switch-away-and-back.
            entry._save({'state': 'waiting', 'ydental_lease_id': False})
        else:
            task._save({'ydental_missed_count': 0, 'ydental_queue_opportunity_used': False})
            returned = bool(queue._model('entry').search_count([
                ('ydental_patient_id', '=', task.ydental_patient_id.id),
                ('ydental_store_id', '=', task.ydental_store_id.id), ('ydental_business_date', '=', date),
                ('ydental_started_at', '!=', False)]))
            number = self.env['ir.sequence'].sudo().next_by_code('ydental.queue.number')
            entry = queue._model('entry')._new({'name': task.name, 'ydental_store_id': task.ydental_store_id.id,
                'ydental_category': {'exam': 'exam', 'medicine': 'pharmacy'}.get(mapping.ydental_catalog_id.ydental_kind, 'medical'),
                'ydental_task_id': task.id, 'ydental_patient_id': task.ydental_patient_id.id,
                'ydental_area_id': mapping.ydental_area_id.id,
                'ydental_capability_id': mapping.ydental_catalog_id.ydental_capability_id.id,
                'ydental_business_date': date, 'ydental_timezone': task.ydental_store_id.ydental_timezone,
                'ydental_reported_at': queue._now(), 'ydental_number': (mapping.ydental_area_id.ydental_prefix or '') + number,
                'ydental_order': int(number) * 1000, 'ydental_return': returned,
                'ydental_opportunity_used': False})
        queue._audit('report', entry, {'task_id': task.id, 'return_opportunity': entry.ydental_return})
        return {'queue_id': entry.id, 'queue_status': 'waiting', 'queue_contract': 's06_real_queue'}

    def _queue_void(self, position, reason):
        queue = self.env['ydental.queue.service']
        queue._lock()
        rows = queue._model('entry').search([('ydental_task_id', '=', position.ydental_task_id.id)])
        if rows.filtered(lambda e: e.state in ('serving', 'verify')) or queue._unresolved_execution(position.ydental_patient_id.id):
            raise UserError(self.env._('handover_required: An actual execution cannot be voided by reception.'))
        for row in rows.filtered(lambda e: e.state in ('waiting', 'calling')):
            row._save({'state': 'void', 'ydental_lease_id': False})
            row.flush_recordset(['state'])
            queue._audit('void', row, {'reason': reason})

    def _void(self, store, task_id, version, reason, cancel_qualification=False):
        task = self._get('task', task_id, store)
        if not self.env['ydental.queue.service']._model('entry').search_count([
                ('ydental_task_id', '=', task.id), ('state', 'in', ['waiting', 'calling'])]):
            raise UserError(self.env._('version_conflict: Only an existing waiting or calling number can be voided.'))
        return super()._void(store, task_id, version, reason, cancel_qualification)

    def _authorize_downstream(self, operation, payload):
        permit = self.env.context.get('ydental_queue_start')
        if operation != 'start' or type(permit) is not StartPermit or (permit.actor_id, permit.task_id) != (
                self.env.uid, payload.get('task_id')):
            return super()._authorize_downstream(operation, payload)
        queue = self.env['ydental.queue.service']
        lease = queue._model('lease').browse(permit.lease_id)
        station, member, category = queue._station(lease.ydental_station_id.id)
        if not lease.ydental_active or lease.ydental_actor_id.id != self.env.uid or lease.ydental_expires_at <= queue._now() or not queue._model('entry').search_count([
                ('ydental_task_id', '=', permit.task_id), ('ydental_lease_id', '=', lease.id), ('state', '=', 'calling')]):
            raise AccessError(self.env._('access_denied: Start requires the current called task and holding connection.'))
        return station.ydental_store_id
