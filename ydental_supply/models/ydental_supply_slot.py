from odoo import fields, models


class YDentalSupplySlot(models.Model):
    _name = 'ydental.supply.slot'
    _description = 'Shared workstation time capacity'
    _inherit = 'ydental.supply.record'
    _order = 'ydental_start, id'

    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict', index=True, string='Workstation')
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict', index=True, string='Area')
    ydental_start = fields.Datetime(required=True, index=True, string='Start')
    ydental_end = fields.Datetime(required=True, string='End')
    ydental_capability_ids = fields.Many2many('ydental.access.capability', string='Published capabilities')
    ydental_policy_id = fields.Many2one('ydental.supply.policy', required=True, ondelete='restrict', string='Policy version')
    ydental_total = fields.Integer(required=True, string='Shared total')
    ydental_reservation_free = fields.Integer(required=True, string='Reservation free')
    ydental_walkin_free = fields.Integer(required=True, string='Walk-in free')
    ydental_unavailable = fields.Integer(default=0, required=True, string='Unavailable')
    ydental_converted = fields.Boolean(default=False, string='Converted')
    state = fields.Selection([('draft', 'Draft'), ('published', 'Published'), ('suspended', 'Suspended')], default='draft', required=True)
    ydental_coverage = fields.Json(string='Verified coverage')
    ydental_reason = fields.Char(required=True, string='Reason')

    _nonnegative = models.Constraint('CHECK(ydental_total >= 0 AND ydental_reservation_free >= 0 AND ydental_walkin_free >= 0 AND ydental_unavailable >= 0)', 'Capacity counters cannot be negative.')
