from odoo import fields, models


class StockLot(models.Model):
    _name = 'stock.lot'
    _inherit = ['stock.lot', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')
    ydental_enabled = fields.Boolean(default=True, string='Enabled lot')
    ydental_received_at = fields.Datetime(readonly=True, string='First actual receipt time')
    ydental_processing_reference = fields.Char(readonly=True, string='Stable processing source')
