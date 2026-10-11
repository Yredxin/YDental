from odoo import fields, models


class YDentalSupplyDisposition(models.Model):
    _name = 'ydental.supply.disposition'
    _description = 'Future supply handling work item'
    _inherit = 'ydental.supply.record'

    ydental_assignment_id = fields.Many2one('ydental.supply.assignment', ondelete='restrict', string='Assignment')
    ydental_slot_id = fields.Many2one('ydental.supply.slot', ondelete='restrict', string='Capacity slot')
    ydental_reason = fields.Char(required=True, string='Reason')
    ydental_resolution = fields.Char(string='Resolution')
    state = fields.Selection([('pending', 'Pending replacement, migration or contact'), ('resolved', 'Resolved')], default='pending', required=True)
