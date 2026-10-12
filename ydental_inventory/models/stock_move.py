from odoo import fields, models


class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')
