from odoo import fields, models


class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')
