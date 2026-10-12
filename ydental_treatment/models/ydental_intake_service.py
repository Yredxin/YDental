from odoo import models
from odoo.exceptions import AccessError, UserError

from .ydental_treatment_service import ReferralSource, fingerprint


class YDentalIntakeService(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _authorize_referral(self, operation, payload, permit):
        if type(permit) is not ReferralSource:
            return super()._authorize_referral(operation, payload, permit)
        service = self.env['ydental.treatment.service']
        execution, doc = service._medical(permit.execution_id, permit.lease_id, permit.lease_token,
            permit.document_id, permit.document_version)
        if (permit.actor_id, permit.store_id, permit.fingerprint) != (
                self.env.uid, execution.ydental_store_id.id, fingerprint([operation, payload])) or (
                execution.ydental_task_id.id != payload.get('source_task_id') or operation not in ('refer_timed', 'refer_untimed')):
            raise AccessError(self.env._('source_required: Referral parameters must match the real current clinical source.'))
        return 'medical'

    def _valid_task(self, task, store):
        service = self.env['ydental.treatment.service']
        segments = service._model('segment').search([('ydental_task_id', '=', task.id)], limit=1)
        lines = service._model('line').search([('ydental_task_id', '=', task.id)], limit=1)
        if segments and (segments.state == 'done' or segments.ydental_order_id.state != 'issued' or not any(
                service._remaining(line) > 0 for line in service._model('line').search([
                    ('ydental_order_id', '=', segments.ydental_order_id.id), ('state', '=', 'issued')]))):
            raise UserError(self.env._('overdispense: The pharmacy segment has ended or has no approved remaining quantity.'))
        if lines and (lines.state != 'issued' or lines.ydental_order_id.state != 'issued'):
            raise UserError(self.env._('order_frozen: This examination order line is no longer available.'))
        return super()._valid_task(task, store)
