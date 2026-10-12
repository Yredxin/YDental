from odoo import fields, models


class YDentalInventoryBatch(models.Model):
    _name = 'ydental.inventory.batch'
    _description = 'Store lifecycle for a shared native manufacturer lot'
    _inherit = 'ydental.inventory.record'

    ydental_lot_id = fields.Many2one('stock.lot', required=True, ondelete='restrict', string='Native manufacturer lot')
    ydental_enabled = fields.Boolean(default=True, string='Store lot enabled')
    ydental_received_at = fields.Datetime(readonly=True, string='First actual store receipt')
    ydental_processing_reference = fields.Char(readonly=True, string='Stable processing source')

    _store_lot_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_lot_id)', 'Each store has one lifecycle for a manufacturer lot.')
