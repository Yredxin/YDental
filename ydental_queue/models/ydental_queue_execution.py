from odoo import fields, models


class YDentalQueueExecution(models.Model):
    _name = 'ydental.queue.execution'
    _description = 'Authoritative patient actual execution fence'
    _inherit = 'ydental.queue.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_entry_id = fields.Many2one('ydental.queue.entry', required=True, ondelete='restrict')
    ydental_lease_id = fields.Many2one('ydental.queue.lease', required=True, ondelete='restrict')
    ydental_started_at = fields.Datetime(required=True)
    state = fields.Selection([('serving', 'Serving'), ('verify', 'Away, on-site verification required')], required=True, default='serving')

    _one_patient = models.Constraint('UNIQUE(ydental_patient_id)', 'A patient has one unresolved actual execution.')
    _one_entry = models.Constraint('UNIQUE(ydental_entry_id)', 'A queue entry starts once.')
    _one_lease = models.Constraint('UNIQUE(ydental_lease_id)', 'A workstation has one unresolved execution.')
