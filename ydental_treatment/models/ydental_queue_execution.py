from odoo import fields, models
from odoo.exceptions import UserError


class YDentalQueueExecution(models.Model):
    _inherit = 'ydental.queue.execution'

    state = fields.Selection(selection_add=[('completed', 'Actual pharmacy segment completed')],
        ondelete={'completed': lambda rows: rows._prevent_terminal_removal()})
    _terminal_time = models.Constraint(
        "CHECK ((state IN ('serving', 'verify') AND ydental_ended_at IS NULL) OR (state IN ('reserved', 'handover', 'interrupted', 'completed') AND ydental_ended_at IS NOT NULL))",
        'A terminal segment retains its end time.')

    def _prevent_terminal_removal(self):
        if self:
            raise UserError(self.env._('history_immutable: Preserve completed pharmacy segments before removing their module.'))
