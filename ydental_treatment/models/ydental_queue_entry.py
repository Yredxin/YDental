from odoo import fields, models
from odoo.exceptions import UserError


class YDentalQueueEntry(models.Model):
    _inherit = 'ydental.queue.entry'

    state = fields.Selection(selection_add=[('completed', 'Actual segment completed')],
        ondelete={'completed': lambda rows: rows._prevent_terminal_removal()})

    def _prevent_terminal_removal(self):
        if self:
            raise UserError(self.env._('history_immutable: Preserve completed pharmacy queue history before module removal.'))
