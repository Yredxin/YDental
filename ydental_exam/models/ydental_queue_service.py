from odoo import fields, models
from odoo.exceptions import AccessError, UserError


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _qualification_satisfied(self, task, station, actor):
        code = task.ydental_mapping_id.ydental_catalog_id.ydental_qualification
        if not code:
            return True
        moment = self._now()
        qualification = self.env['ydental.exam.qualification'].sudo().search([
            ('ydental_user_id', '=', actor.id), ('ydental_store_id', '=', station.ydental_store_id.id),
            ('ydental_code', '=', code), ('ydental_revoked', '=', False),
            ('ydental_valid_from', '<=', moment), ('ydental_valid_until', '>', moment)], limit=1)
        return bool(qualification and station.ydental_kind == 'exam') or super()._qualification_satisfied(task, station, actor)

    def _exam_start_authorized(self, line):
        return bool(line.state == 'issued' and line.ydental_order_id.state == 'issued' and
                    line.ydental_order_id.ydental_kind == 'exam' and line.ydental_task_id and
                    line.ydental_task_id.ydental_patient_id == line.ydental_patient_id and
                    line.ydental_task_id.ydental_store_id == line.ydental_store_id and
                    line.ydental_task_id.ydental_mapping_id == line.ydental_mapping_id)

    def _start(self, lease_id, token, entry_id):
        entry = self._model('entry').browse(self.env['ydental.intake.service']._id(entry_id)).exists()
        line = self.env['ydental.treatment.line'].sudo().search([
            ('ydental_task_id', '=', entry.ydental_task_id.id), ('state', '=', 'issued')], limit=1) if entry else False
        result = super()._start(lease_id, token, entry_id)
        if line and line.ydental_order_id.ydental_kind == 'exam':
            if result['state'] != 'serving' or not self._exam_start_authorized(line):
                raise AccessError(self.env._('source_required: The actual examination source changed.'))
            line._save({'state': 'started'})
            self.env['ydental.access.service']._audit('exam.started', 'exam', line, line.ydental_store_id.id,
                after={'execution_id': result['execution_id'], 'task_id': entry.ydental_task_id.id})
        return result

    def _finish_exam_segment(self, execution, reason):
        session, connection = self._connection()
        lease = execution.ydental_lease_id
        if execution.state != 'serving' or execution.ydental_category != 'exam' or (
                not lease.ydental_active or lease.ydental_actor_id.id != self.env.uid or
                lease.ydental_session_id != session or lease.ydental_revision != session.ydental_revision or
                lease.ydental_connection_hash != connection.key_hash or lease.ydental_expires_at <= self._now()):
            raise AccessError(self.env._('access_denied: Only the actual examination holder may finish.'))
        entry = self._execution_entry(execution)
        execution._save({'state': 'completed', 'ydental_ended_at': self._now()})
        entry._save({'state': 'completed'})
        execution.ydental_task_id._save({'state': 'done'})
        self._model('append.permit').search([('ydental_task_id', '=', execution.ydental_task_id.id),
            ('state', '=', 'started')])._save({'state': 'ended'})
        self._audit('exam_completed', execution, {'task_id': execution.ydental_task_id.id, 'reason': reason})
