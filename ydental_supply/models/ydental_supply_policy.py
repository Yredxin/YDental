from odoo import fields, models


class YDentalSupplyPolicy(models.Model):
    _name = 'ydental.supply.policy'
    _description = 'Versioned capacity publication policy'
    _inherit = 'ydental.supply.record'
    _order = 'id desc'

    ydental_area_id = fields.Many2one('ydental.space.area', ondelete='restrict', string='Area')
    ydental_station_id = fields.Many2one('ydental.space.station', ondelete='restrict', string='Workstation')
    ydental_mode = fields.Selection([('demo', 'Demonstration'), ('published', 'Approved publication')], required=True, string='Publication mode')
    ydental_reservation_weight = fields.Integer(default=1, required=True, string='Reservation weight')
    ydental_walkin_weight = fields.Integer(default=2, required=True, string='Walk-in weight')
    ydental_rounding = fields.Selection([('floor', 'Round reservation down'), ('nearest', 'Round reservation to nearest')], required=True, string='Rounding')
    ydental_phone_pool = fields.Selection([('reservation', 'Reservation'), ('walkin', 'Walk-in')], required=True, string='Telephone pool')
    ydental_cutoff_minutes = fields.Integer(default=0, required=True, string='Cutoff minutes')
    ydental_reason = fields.Char(required=True, string='Reason')

    def _split(self, quantity):
        self.ensure_one()
        numerator = quantity * self.ydental_reservation_weight
        divisor = self.ydental_reservation_weight + self.ydental_walkin_weight
        reservation = numerator // divisor if self.ydental_rounding == 'floor' else (2 * numerator + divisor) // (2 * divisor)
        return reservation, quantity - reservation
