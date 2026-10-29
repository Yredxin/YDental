from odoo import models
from odoo.tools import consteq
from odoo.exceptions import AccessError


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _handlers(self):
        return super()._handlers() | {'medical_complete': self._medical_complete}

    def _medical_complete(self, lease_id, token, execution_id):
        lease = self._held(lease_id, token)
        execution = self._source_execution(execution_id, lease)
        if lease.ydental_category != 'medical' or execution.ydental_category != 'medical':
            raise AccessError(self.env._('access_denied: Only the treating workstation may complete a medical reception.'))
        if execution.state != 'serving':
            raise AccessError(self.env._('access_denied: Only the current serving medical reception can be completed.'))
        self.env['ydental.patient.service']._current_relation(execution.ydental_patient_id, lease.ydental_store_id)
        self = self.with_context(ydental_medical_completion=True)
        self._save_before_handover(execution)
        self._release_execution_documents(execution)
        execution._save({'state': 'completed', 'ydental_ended_at': self._now()})
        execution.flush_recordset(['state'])
        execution.ydental_task_id._save({'state': 'done'})
        self._execution_entry(execution)._save({'state': 'completed'})
        self._model('append.permit').search([
            ('ydental_task_id', '=', execution.ydental_task_id.id), ('state', '=', 'started'),
        ])._save({'state': 'ended'})
        self._audit('medical_completed', execution, {'task_id': execution.ydental_task_id.id, 'lease_retained': True})
        return {'execution_id': execution.id, 'state': 'completed'}

    def _finish_pharmacy_segment(self, execution):
        session, connection = self._connection()
        lease = execution.ydental_lease_id
        if execution.state != 'serving' or execution.ydental_category != 'pharmacy' or (
                lease.ydental_actor_id.id != self.env.uid or not lease.ydental_active or
                lease.ydental_expires_at <= self._now() or lease.ydental_session_id != session or
                lease.ydental_revision != session.ydental_revision or not consteq(lease.ydental_connection_hash, connection.key_hash)):
            raise AccessError(self.env._('access_denied: Only the real pharmacy segment holder can finish its execution.'))
        service = self.env['ydental.treatment.service']
        service._access('pharmacy')
        segment = service._model('segment').search([('ydental_execution_id', '=', execution.id), ('state', '=', 'active')], limit=1)
        if not segment:
            raise AccessError(self.env._('source_required: Finish only a real prescription dispensing segment.'))
        # This is the controlled S06 extension boundary; it closes the existing
        # authoritative records and their append permit in the same transaction.
        execution._save({'state': 'completed', 'ydental_ended_at': self._now()})
        execution.flush_recordset(['state'])
        execution.ydental_task_id._save({'state': 'done'})
        self._execution_entry(execution)._save({'state': 'completed'})
        self._model('append.permit').search([('ydental_task_id', '=', execution.ydental_task_id.id),
            ('state', '=', 'started')])._save({'state': 'ended'})
        self._audit('pharmacy_completed', execution, {'task_id': execution.ydental_task_id.id})

    def _external_target_authorized(self, execution, target_task):
        service = self.env['ydental.treatment.service']
        order = service._model('order').search([('ydental_execution_id', '=', execution.id), ('state', '=', 'issued')])
        exam = service._model('line').search_count([('ydental_order_id', 'in', order.filtered(lambda o: o.ydental_kind == 'exam').ids),
            ('ydental_task_id', '=', target_task.id), ('state', '=', 'issued')])
        pharmacy = service._model('segment').search_count([('ydental_order_id', 'in', order.filtered(lambda o: o.ydental_kind == 'prescription').ids),
            ('ydental_task_id', '=', target_task.id), ('state', '=', 'pending')])
        return bool(exam or pharmacy) or super()._external_target_authorized(execution, target_task)

    def _start(self, lease_id, token, entry_id):
        entry = self._model('entry').browse(self.env['ydental.intake.service']._id(entry_id)).exists()
        if entry:
            line = self.env['ydental.treatment.service']._model('line').search([
                ('ydental_task_id', '=', entry.ydental_task_id.id), ('state', '=', 'issued')], limit=1)
            if line and line.ydental_order_id.ydental_kind == 'exam' and not self._exam_start_authorized(line):
                raise AccessError(self.env._('exam_integration_required: Real examination execution and results remain unavailable until S09 is authorized and installed.'))
        return super()._start(lease_id, token, entry_id)

    def _exam_start_authorized(self, line):
        # An installed upper module must validate the frozen examination source.
        return False
