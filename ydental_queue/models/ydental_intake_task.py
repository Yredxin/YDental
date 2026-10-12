from odoo import fields, models


class YDentalIntakeTask(models.Model):
    _inherit = 'ydental.intake.task'

    ydental_queue_opportunity_used = fields.Boolean(readonly=True)

    ydental_source_execution_id = fields.Many2one('ydental.queue.execution', readonly=True, ondelete='restrict')
    ydental_continuation_snapshot = fields.Json(readonly=True)
    state = fields.Selection(selection_add=[('suspended', 'Waiting for reserved return'), ('handed_over', 'Segment handed over')],
                             ondelete={'suspended': 'set default', 'handed_over': 'set default'})

    _one_continuation = models.Constraint('UNIQUE(ydental_source_execution_id)', 'One continuation per handed over segment.')
