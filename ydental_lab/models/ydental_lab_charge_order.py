from odoo import fields, models


class YDentalLabOrder(models.Model):
    _inherit = 'ydental.lab.order'

    ydental_charge_ids = fields.One2many(
        'ydental.lab.charge', 'ydental_order_id', string='Additional service charges', readonly=True)
