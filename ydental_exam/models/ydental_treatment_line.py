from odoo import fields, models
from odoo.exceptions import UserError


class YDentalTreatmentLine(models.Model):
    _inherit = 'ydental.treatment.line'

    state = fields.Selection(selection_add=[('aborted', 'Actual examination aborted'),
        ('partial', 'Partially completed examination')], ondelete={
        'aborted': lambda rows: rows._preserve_exam_history(),
        'partial': lambda rows: rows._preserve_exam_history()})

    def _preserve_exam_history(self):
        if self:
            raise UserError(self.env._('history_immutable: Preserve actual examination history before removing its module.'))
