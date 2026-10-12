from odoo import models
from odoo.tools import consteq
from odoo.exceptions import AccessError


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

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
            if line and line.ydental_order_id.ydental_kind == 'exam':
                raise AccessError(self.env._('exam_integration_required: Real examination execution and results remain unavailable until S09 is authorized and installed.'))
        return super()._start(lease_id, token, entry_id)
