import inspect

from odoo import models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _handlers(self):
        return super()._handlers() | {'reserve': self._reserve, 'restore': self._restore, 'handover': self._handover}

    def _operate(self, operation, payload):
        handlers = {'query_return': self._query_return, 'append': self._append, 'revoke': self._revoke}
        if operation not in handlers:
            return super()._operate(operation, payload)
        if not isinstance(payload, dict):
            raise ValidationError(self.env._('Unknown or missing workstation arguments.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('Unknown or missing workstation arguments.')) from error
        self.env['ydental.access.service']._scope(write=operation != 'query_return')
        with self.env.cr.savepoint():
            self._locks()
            # Query is deliberately read-only: no expiry, task, entry or audit writes.
            if operation != 'query_return':
                self._append_access()
                self._expire()
            return handlers[operation](**payload)

    def _service_snapshot(self, task):
        mapping = task.ydental_mapping_id
        catalog = mapping.ydental_catalog_id
        return {'catalog_id': catalog.id, 'capability_id': catalog.ydental_capability_id.id,
                'qualification': catalog.ydental_qualification or '', 'area_id': mapping.ydental_area_id.id,
                'execution_area_id': mapping.ydental_execution_area_id.id}

    def _hold(self, patient_id=None, lease_id=None, actor_id=None):
        domain = [('state', 'in', ('active', 'verify'))]
        if patient_id is not None:
            domain.append(('ydental_patient_id', '=', patient_id))
        if lease_id is not None:
            domain.append(('ydental_lease_id', '=', lease_id))
        if actor_id is not None:
            domain.append(('ydental_actor_id', '=', actor_id))
        return self._model('hold').search(domain, limit=1)

    def _busy(self, lease):
        return super()._busy(lease) or bool(self._hold(lease_id=lease.id))

    def _assert_actor_idle(self):
        super()._assert_actor_idle()
        if self._hold(actor_id=self.env.uid):
            raise UserError(self.env._('handover_required: Resolve the reserved patient or on-site verification first.'))

    def _enter(self, station_id):
        if self._model('hold').search_count([('ydental_station_id', '=', station_id), ('state', 'in', ('active', 'verify'))]):
            raise UserError(self.env._('handover_required: This workstation has a reserved patient.'))
        return super()._enter(station_id)

    def _switch(self, lease_id, token, station_id):
        if self._model('hold').search_count([('ydental_station_id', '=', station_id), ('state', 'in', ('active', 'verify'))]):
            raise UserError(self.env._('handover_required: This workstation has a reserved patient.'))
        return super()._switch(lease_id, token, station_id)

    def _expire(self):
        result = super()._expire()
        holds = self._model('hold').search([('state', '=', 'active'), ('ydental_lease_id.ydental_active', '=', False)])
        holds._save({'state': 'verify'})
        for hold in holds:
            self.env['ydental.access.service'].with_user(self.env.ref('base.user_root'))._audit(
                'queue.hold_timeout', hold.ydental_category, hold, hold.ydental_store_id.id,
                after={'holder_user_id': hold.ydental_actor_id.id, 'hold_id': hold.id,
                       'station_id': hold.ydental_station_id.id, 'verification_required': True},
                source='workstation_timeout_automation')
        return result

    def _status(self):
        hold = self._hold(actor_id=self.env.uid)
        if hold:
            valid = hold.state == 'active' and hold.ydental_lease_id.ydental_active and hold.ydental_lease_id.ydental_expires_at > self._now()
            return {'store': hold.ydental_store_id.name, 'area': hold.ydental_area_id.name,
                    'station': hold.ydental_station_id.name, 'state': 'holding' if valid else 'verify',
                    'state_label': self.env._('Waiting for patient return') if valid else self.env._('On-site verification required')}
        return super()._status()

    def _source_execution(self, execution_id, lease):
        execution = self._model('execution').browse(self.env['ydental.intake.service']._id(execution_id)).exists()
        if not execution or execution.ydental_lease_id != lease or execution.ydental_store_id != lease.ydental_store_id:
            raise AccessError(self.env._('access_denied: Select the execution held by this connection.'))
        return execution

    def _external_target_authorized(self, execution, target_task):
        # S08/S09 must verify the actual frozen order/prescription source.
        return False

    def _save_before_handover(self, execution):
        raise AccessError(self.env._('save_required: A trusted server document save integration is required.'))

    def _release_execution_documents(self, execution):
        # S08 extends this inside the same transaction, after its save succeeds.
        return None

    def _end_segment(self, execution, terminal):
        execution._save({'state': terminal, 'ydental_ended_at': self._now()})
        execution.flush_recordset(['state'])
        task = execution.ydental_task_id
        task._save({'state': 'suspended' if terminal == 'reserved' else 'handed_over'})
        self._model('entry').search([('ydental_task_id', '=', task.id)])._save({'state': terminal})
        self._model('append.permit').search([('ydental_task_id', '=', task.id), ('state', '=', 'started')])._save({'state': 'ended'})

    def _reserve(self, lease_id, token, execution_id, target_task_id):
        lease = self._held(lease_id, token)
        execution = self._source_execution(execution_id, lease)
        target = self.env['ydental.intake.service']._get('task', target_task_id, lease.ydental_store_id)
        prior = self._model('hold').search([('ydental_execution_id', '=', execution.id)], limit=1)
        if prior:
            if prior.ydental_target_task_id != target or prior.state != 'active':
                raise UserError(self.env._('version_conflict: This reservation is already resolved or has another target.'))
            return {'hold_id': prior.id, 'state': prior.state}
        if execution.state != 'serving' or lease.ydental_category != 'medical' or target == execution.ydental_task_id or (
                target.ydental_patient_id != execution.ydental_patient_id or target.state not in ('pending', 'accepted') or
                target.ydental_mapping_id.ydental_catalog_id.ydental_kind not in ('exam', 'medicine') or
                self._external_target_authorized(execution, target) is not True):
            raise AccessError(self.env._('source_required: Reserve only a trusted external examination or pharmacy task.'))
        self.env['ydental.patient.service']._current_relation(execution.ydental_patient_id, lease.ydental_store_id)
        self.env['ydental.intake.service']._target(target.ydental_mapping_id.id, lease.ydental_store_id)
        self._end_segment(execution, 'reserved')
        hold = self._model('hold')._new({'name': execution.name, 'ydental_store_id': lease.ydental_store_id.id,
            'ydental_category': 'medical', 'ydental_patient_id': execution.ydental_patient_id.id,
            'ydental_task_id': execution.ydental_task_id.id, 'ydental_target_task_id': target.id,
            'ydental_execution_id': execution.id, 'ydental_lease_id': lease.id,
            'ydental_actor_id': self.env.uid, 'ydental_station_id': lease.ydental_station_id.id,
            'ydental_area_id': lease.ydental_station_id.ydental_queue_area_id.id, 'ydental_created_at': self._now()})
        self._audit('reserve', hold, {'execution_id': execution.id, 'target_task_id': target.id})
        return {'hold_id': hold.id, 'state': hold.state}

    def _query_return(self, patient_id):
        store = self.env['ydental.intake.service']._business_read_access()
        patient = self.env['ydental.patient.service']._business_patient(patient_id)
        self.env['ydental.patient.service']._current_relation(patient, store)
        hold = self._hold(patient_id=patient.id)
        if not hold or hold.ydental_store_id != store:
            return {'result': 'hint_only', 'state': 'no_hold', 'message': self.env._('Use the explicit target task for ordinary reporting.')}
        valid = hold.state == 'active' and hold.ydental_lease_id.ydental_active and hold.ydental_lease_id.ydental_expires_at > self._now()
        return {'result': 'hint_only', 'hold_id': hold.id, 'station': hold.ydental_station_id.name,
                'area': hold.ydental_area_id.name, 'state': 'holding' if valid else 'verify',
                'message': self.env._('Return to the original workstation.') if valid else self.env._('On-site verification required')}

    def _restore(self, lease_id, token, hold_id, confirmed):
        lease = self._held(lease_id, token, admission=True)
        hold = self._model('hold').browse(self.env['ydental.intake.service']._id(hold_id)).exists()
        if not hold or hold.ydental_lease_id != lease or hold.ydental_actor_id.id != self.env.uid or confirmed is not True:
            raise AccessError(self.env._('access_denied: The original holder must confirm actual patient return.'))
        if hold.state == 'restored':
            resumed = self._model('execution').search([('ydental_resumed_from_id', '=', hold.ydental_execution_id.id)], limit=1)
            return {'hold_id': hold.id, 'execution_id': resumed.id, 'state': resumed.state}
        if hold.state != 'active' or self._unresolved_execution(hold.ydental_patient_id.id):
            raise UserError(self.env._('handover_required: Another actual execution or on-site verification prevents return.'))
        entry = self._model('entry').search([('ydental_task_id', '=', hold.ydental_task_id.id)], limit=1)
        reason = self._eligibility(entry, lease.ydental_station_id)
        if reason:
            raise AccessError(reason)
        intake = self.env['ydental.intake.service']
        self.env['ydental.patient.service']._current_relation(hold.ydental_patient_id, hold.ydental_store_id)
        positions = intake._model('position').search([('ydental_patient_id', '=', hold.ydental_patient_id.id), ('ydental_active', '=', True)])
        for position in positions:
            intake._withdraw(position.ydental_task_id, 'Original holder confirmed actual return')
        execution = self._model('execution')._new({'name': hold.name, 'ydental_store_id': hold.ydental_store_id.id,
            'ydental_category': 'medical', 'ydental_patient_id': hold.ydental_patient_id.id,
            'ydental_task_id': hold.ydental_task_id.id, 'ydental_resumed_from_id': hold.ydental_execution_id.id,
            'ydental_service_snapshot': hold.ydental_execution_id.ydental_service_snapshot,
            'ydental_lease_id': lease.id, 'ydental_started_at': self._now()})
        hold._save({'state': 'restored', 'ydental_ended_at': self._now()})
        hold.ydental_task_id._save({'state': 'started'})
        entry._save({'state': 'serving'})
        self._audit('restore', execution, {'hold_id': hold.id, 'withdrawn_task_ids': positions.ydental_task_id.ids})
        return {'hold_id': hold.id, 'execution_id': execution.id, 'state': 'serving'}

    def _continuation(self, execution, mapping_id=None, reason=''):
        intake = self.env['ydental.intake.service']
        source = execution.ydental_task_id
        snapshot = execution.ydental_service_snapshot or self._service_snapshot(source)
        mapping = intake._target(mapping_id or source.ydental_mapping_id.id, source.ydental_store_id)
        if mapping.ydental_catalog_id.id != snapshot['catalog_id'] or mapping.ydental_catalog_id.ydental_kind != 'care':
            raise UserError(self.env._('qualification_required: An independent service needs a new S05 qualification.'))
        if mapping != source.ydental_mapping_id:
            reason = intake._text(reason)
        current = self._service_snapshot(source)
        if current != snapshot:
            raise UserError(self.env._('version_conflict: The original service requirements changed; review the source.'))
        task = intake._model('task').search([('ydental_source_execution_id', '=', execution.id)], limit=1)
        if not task:
            task = intake._new('task', source.ydental_store_id, dict(intake._identity(source.ydental_patient_id),
                name=mapping.name, ydental_mapping_id=mapping.id, ydental_parent_task_id=source.id,
                ydental_source_kind='continuation', ydental_source_execution_id=execution.id,
                ydental_continuation_snapshot=dict(snapshot, area_id=mapping.ydental_area_id.id,
                    execution_area_id=mapping.ydental_execution_area_id.id), ydental_reason=reason))
        return task

    def _handover(self, lease_id, token, execution_id, mapping_id=None, reason=''):
        lease = self._held(lease_id, token)
        execution = self._source_execution(execution_id, lease)
        if lease.ydental_category != 'medical':
            raise AccessError(self.env._('access_denied: Outpatient handover requires the treating workstation.'))
        if execution.state == 'handover':
            task = self.env['ydental.intake.service']._model('task').search([('ydental_source_execution_id', '=', execution.id)], limit=1)
            if mapping_id is not None and mapping_id != task.ydental_mapping_id.id:
                raise UserError(self.env._('version_conflict: This handover already has a continuation direction.'))
            return {'execution_id': execution.id, 'continuation_task_id': task.id, 'state': 'handover'}
        hold = self._hold(lease_id=lease.id)
        if execution.state != 'serving' and not (execution.state == 'reserved' and hold.ydental_execution_id == execution):
            raise UserError(self.env._('handover_required: Resolve the current segment in its legitimate holding context.'))
        self.env['ydental.patient.service']._current_relation(execution.ydental_patient_id, lease.ydental_store_id)
        if self._save_before_handover(execution) is not True:
            raise UserError(self.env._('save_required: Latest draft save failed; execution remains held.'))
        task = self._continuation(execution, mapping_id, reason)
        self._release_execution_documents(execution)
        self._end_segment(execution, 'handover')
        if hold:
            hold._save({'state': 'handover', 'ydental_ended_at': self._now()})
        self._audit('handover', execution, {'continuation_task_id': task.id, 'lease_retained': True})
        return {'execution_id': execution.id, 'continuation_task_id': task.id, 'state': 'handover'}

    def _append_access(self):
        access = self.env['ydental.access.service']
        store = access._check('frontdesk', 'write', write=True).ydental_store_id
        if not self.env.user.has_group('ydental_queue.ydental_group_append'):
            raise AccessError(self.env._('access_denied: Explicit append authorization and store frontdesk write are both required.'))
        return store

    def _active_permit(self, task):
        return self._model('append.permit').search([('ydental_task_id', '=', task.id), ('state', '=', 'active')], limit=1)

    def _permit_valid(self, task):
        permit = self._active_permit(task)
        return bool(permit and permit.ydental_store_id == task.ydental_store_id and permit.ydental_patient_id == task.ydental_patient_id and
                    permit.ydental_mapping_id == task.ydental_mapping_id and permit.ydental_capability_id == task.ydental_mapping_id.ydental_catalog_id.ydental_capability_id and
                    permit.ydental_business_date == self.env['ydental.supply.service']._date(task.ydental_store_id))

    def _append(self, task_id, reason):
        store = self._append_access()
        intake = self.env['ydental.intake.service']
        task = intake._get('task', task_id, store)
        reason = intake._text(reason)
        if self._hold(patient_id=task.ydental_patient_id.id) or self._unresolved_execution(task.ydental_patient_id.id):
            raise UserError(self.env._('handover_required: Resolve the existing reservation or execution first.'))
        if self._permit_valid(task):
            return {'result': 'already_accepted', 'permit_id': self._active_permit(task).id}
        mapping = intake._target(task.ydental_mapping_id.id, store)
        business = self.env['ydental.supply.service']._business_record(store, mapping.ydental_area_id.id)
        if not business or business.state == 'open':
            raise UserError(self.env._('append_unavailable: Explicit append is only for stopped ordinary reception.'))
        # Validate the S05 task/claim/date first. A temporary frozen server permit
        # only bypasses _open; it never manufactures an entitlement or capacity.
        permit = self._model('append.permit')._new({'name': task.name, 'ydental_store_id': store.id,
            'ydental_category': 'frontdesk', 'ydental_patient_id': task.ydental_patient_id.id,
            'ydental_task_id': task.id, 'ydental_mapping_id': mapping.id,
            'ydental_capability_id': mapping.ydental_catalog_id.ydental_capability_id.id,
            'ydental_business_date': self.env['ydental.supply.service']._date(store), 'ydental_timezone': store.ydental_timezone,
            'ydental_actor_id': self.env.uid, 'ydental_created_at': self._now(), 'ydental_reason': reason})
        intake._valid_task(task, store)
        self._audit('append', permit, {'task_id': task.id, 'capacity_added': False})
        return {'result': 'accepted', 'permit_id': permit.id, 'task_id': task.id}

    def _revoke(self, permit_id, reason):
        store = self._append_access()
        permit = self._model('append.permit').browse(self.env['ydental.intake.service']._id(permit_id)).exists()
        if not permit or permit.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Select a permit in the current store.'))
        reason = self.env['ydental.intake.service']._text(reason)
        if permit.state == 'revoked':
            return {'result': 'already_accepted', 'permit_id': permit.id, 'state': permit.state}
        if permit.state != 'active' or permit.ydental_task_id.state in ('started', 'suspended', 'handed_over', 'done'):
            raise UserError(self.env._('already_started: A started segment cannot lose its permit by ordinary revoke.'))
        self.env['ydental.intake.service']._withdraw(permit.ydental_task_id, reason)
        permit._save({'state': 'revoked', 'ydental_revoked_at': self._now(), 'ydental_revoked_by_id': self.env.uid, 'ydental_revoke_reason': reason})
        self._audit('append_revoke', permit, {'task_id': permit.ydental_task_id.id, 'qualification_cancelled': False})
        return {'result': 'accepted', 'permit_id': permit.id, 'state': permit.state}

    def _eligibility(self, entry, station, actor=None):
        reason = super()._eligibility(entry, station, actor)
        if reason:
            return reason
        task = entry.ydental_task_id
        if task.ydental_continuation_snapshot and task.ydental_continuation_snapshot != self._service_snapshot(task):
            return self.env._('version_conflict: Continuation service requirements changed; review the source.')
        # Restore is allowed directly to an effective hold even when stopped.
        hold = self._hold(patient_id=entry.ydental_patient_id.id)
        if hold and hold.ydental_task_id == task and hold.ydental_station_id == station and hold.state == 'active':
            return ''
        business = self.env['ydental.supply.service']._business_record(task.ydental_store_id, entry.ydental_area_id.id)
        if business and business.state == 'closed' and not self._permit_valid(task):
            return self.env._('append_required: This stopped area requires an active task-bound append permit.')
        # A revoked permit keeps the task blocked even if ordinary calling opens.
        permits = self._model('append.permit').search([('ydental_task_id', '=', task.id)], order='id desc', limit=1)
        if permits and permits.state != 'active':
            return self.env._('append_required: The task append permit is no longer active.')
        return ''

    def _start(self, lease_id, token, entry_id):
        result = super()._start(lease_id, token, entry_id)
        entry = self._model('entry').browse(entry_id)
        self._active_permit(entry.ydental_task_id)._save({'state': 'started'})
        return result
