from odoo import fields, models


class YDentalTreatmentSegment(models.Model):
    _name = 'ydental.treatment.segment'
    _description = 'YDentalTreatmentSegment'
    _inherit = 'ydental.treatment.record'

    ydental_order_id = fields.Many2one('ydental.treatment.order', required=True, ondelete='restrict', index=True)
    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict', index=True)
    ydental_execution_id = fields.Many2one('ydental.queue.execution', ondelete='restrict')
    ydental_sequence = fields.Integer(required=True)
    ydental_finished_at = fields.Datetime()
    state = fields.Selection([('pending', 'Awaiting explicit reporting'), ('active', 'Actual dispensing segment'), ('done', 'Segment finished')], required=True, default='pending')
    _task_once = models.Constraint('UNIQUE(ydental_task_id)', 'A pharmacy task belongs to one prescription segment.')
    _sequence_once = models.Constraint('UNIQUE(ydental_order_id, ydental_sequence)', 'Prescription segments have stable consecutive identities.')
    _one_live = models.UniqueIndex("(ydental_order_id) WHERE state IN ('pending', 'active')")
