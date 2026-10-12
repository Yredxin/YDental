from odoo import fields, models


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
    ydental_return = fields.Boolean()
    ydental_opportunity_used = fields.Boolean()
    ydental_call_used_before = fields.Boolean()
    state = fields.Selection([('waiting', 'Waiting'), ('calling', 'Calling'), ('serving', 'Serving'),
                              ('verify', 'Away, on-site verification required'), ('void', 'Number voided')], required=True, default='waiting')

    _one_task = models.Constraint('UNIQUE(ydental_task_id)', 'A task retains one queue history.')
    _one_patient = models.UniqueIndex("(ydental_patient_id) WHERE state IN ('waiting', 'calling')")
    _one_call = models.UniqueIndex("(ydental_lease_id) WHERE state = 'calling'")
    _number_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_area_id, ydental_business_date, ydental_number)', 'Queue display numbers must be unique in their business scope.')
