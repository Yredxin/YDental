from odoo import fields, models


class YDentalSupplySlot(models.Model):
    _name = 'ydental.supply.slot'
    _description = 'Shared workstation time capacity'
    _inherit = 'ydental.supply.record'
    _order = 'ydental_start, id'

    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict', index=True)
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict', index=True)
    ydental_start = fields.Datetime(required=True, index=True)
    ydental_end = fields.Datetime(required=True)
    ydental_capability_ids = fields.Many2many('ydental.access.capability', string='Published capabilities')
    ydental_policy_id = fields.Many2one('ydental.supply.policy', required=True, ondelete='restrict')
    ydental_total = fields.Integer(required=True)
    ydental_reservation_free = fields.Integer(required=True)
    ydental_walkin_free = fields.Integer(required=True)
    ydental_unavailable = fields.Integer(default=0, required=True)
    ydental_converted = fields.Boolean(default=False)
    state = fields.Selection([('draft', 'Draft'), ('published', 'Published'), ('suspended', 'Suspended')], default='draft', required=True)
    ydental_coverage = fields.Json()
    ydental_reason = fields.Char(required=True)

    _nonnegative = models.Constraint('CHECK(ydental_total >= 0 AND ydental_reservation_free >= 0 AND ydental_walkin_free >= 0 AND ydental_unavailable >= 0)', 'Capacity counters cannot be negative.')
