from odoo import fields, models


class StockLocation(models.Model):
    _name = 'stock.location'
    _inherit = ['stock.location', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')
