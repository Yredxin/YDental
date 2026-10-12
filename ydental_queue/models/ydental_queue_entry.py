from odoo import fields, models
from odoo.exceptions import AccessError


class YDentalQueueEntry(models.Model):
    _name = 'ydental.queue.entry'
    _description = 'Durable task queue opportunity and actual call'
    _inherit = 'ydental.queue.record'
    _order = 'ydental_order, ydental_reported_at, id'

    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict', index=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')
    ydental_capability_id = fields.Many2one('ydental.access.capability', required=True, ondelete='restrict')
    ydental_lease_id = fields.Many2one('ydental.queue.lease', ondelete='restrict')
    ydental_business_date = fields.Date(required=True)
    ydental_timezone = fields.Char(required=True)
    ydental_reported_at = fields.Datetime(required=True)
    ydental_started_at = fields.Datetime()
    ydental_number = fields.Char(required=True)
    ydental_order = fields.Integer(required=True)
    ydental_missed_count = fields.Integer(default=0, readonly=True)
    ydental_return = fields.Boolean()
    ydental_opportunity_used = fields.Boolean()
    ydental_call_used_before = fields.Boolean()
    ydental_call_rank = fields.Integer(string='Effective regional rank before call')
    ydental_call_order_before = fields.Integer(string='Pre-call order anchor')
    state = fields.Selection([('waiting', 'Waiting'), ('calling', 'Calling'), ('serving', 'Serving'),
                              ('verify', 'Away, on-site verification required'), ('reserved', 'Waiting for reserved return'),
                              ('handover', 'Segment handed over'), ('day_closed', 'Business day queue ended'), ('void', 'Number voided')], required=True, default='waiting')

    _one_task_day = models.Constraint('UNIQUE(ydental_task_id, ydental_business_date)', 'A task retains one queue segment per business day.')
    _one_patient = models.UniqueIndex("(ydental_patient_id) WHERE state IN ('waiting', 'calling')")
    _one_call = models.UniqueIndex("(ydental_lease_id) WHERE state = 'calling'")
    _number_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_area_id, ydental_business_date, ydental_number)', 'Queue display numbers must be unique in their business scope.')

    def init(self):
        from odoo.tools.sql import constraint_definition, drop_constraint
        name = 'ydental_queue_entry_one_task'
        if constraint_definition(self.env.cr, self._table, name):
            drop_constraint(self.env.cr, self._table, name)
            self.env.cr.execute('UPDATE ydental_queue_entry q SET ydental_missed_count=t.ydental_missed_count FROM ydental_intake_task t WHERE t.id=q.ydental_task_id')

    def write(self, vals):
        for field in ('ydental_task_id', 'ydental_business_date', 'ydental_number', 'ydental_timezone'):
            if field in vals:
                raise AccessError(self.env._('history_immutable: Queue identity, day and number cannot be rewritten.'))
        return super().write(vals)
