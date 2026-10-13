from odoo import models
from odoo.exceptions import UserError


class YDentalIntakeService(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _report(self, store, task_id, version):
        line = self.env['ydental.treatment.line'].sudo().search([
            ('ydental_task_id', '=', task_id), ('ydental_store_id', '=', store.id),
            ('ydental_order_id.ydental_kind', '=', 'exam')], limit=1)
        if line and line.state == 'issued' and (
                line.ydental_exam_validated_date != self.env['ydental.supply.service']._date(store)):
            raise UserError(self.env._('exam_revalidation_required: A doctor must confirm this unfinished order line for the current local day.'))
        return super()._report(store, task_id, version)
