from odoo import fields, models


class YDentalSupplyFeedback(models.Model):
    _name = 'ydental.supply.feedback'
    _description = 'Assignment error feedback'
    _inherit = 'ydental.supply.record'

    ydental_assignment_id = fields.Many2one('ydental.supply.assignment', required=True, ondelete='restrict')
    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_recipient_ids = fields.Many2many('res.users')
    ydental_reason = fields.Char(required=True)
    state = fields.Selection([('pending', 'Pending'), ('resolved', 'Resolved')], default='pending', required=True)
    ydental_resolution = fields.Char()
