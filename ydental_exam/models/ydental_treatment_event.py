from odoo import fields, models
from odoo.exceptions import UserError


class YDentalTreatmentEvent(models.Model):
    _inherit = 'ydental.treatment.event'

    ydental_kind = fields.Selection(selection_add=[('exam', 'Actual examination')],
        ondelete={'exam': lambda rows: rows._preserve_exam_history()})

    def _preserve_exam_history(self):
        if self:
            raise UserError(self.env._('history_immutable: Preserve actual examination fee history before removing its module.'))
