from odoo import fields, models


class StockLot(models.Model):
    _name = 'stock.lot'
    _inherit = ['stock.lot', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')
