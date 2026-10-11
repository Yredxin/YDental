from odoo import fields, models


class YDentalSupplyBusiness(models.Model):
    _name = 'ydental.supply.business'
    _description = 'Store area local business day'
    _inherit = 'ydental.supply.record'

    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict', index=True)
    ydental_date = fields.Date(required=True, index=True)
    ydental_timezone = fields.Char(required=True)
    state = fields.Selection([('open', 'Open'), ('draining', 'Ordinary reporting stopped'), ('closed', 'Ordinary calling stopped')], required=True)
    ydental_reason = fields.Char(required=True)

    _day_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_area_id, ydental_date)', 'One business record per store, area and local date is required.')
