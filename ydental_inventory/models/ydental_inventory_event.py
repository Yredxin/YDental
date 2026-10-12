from odoo import fields, models


class YDentalInventoryEvent(models.Model):
    _name = 'ydental.inventory.event'
    _description = 'Unique inventory source and recovery event'
    _inherit = 'ydental.inventory.record'

    ydental_source_key = fields.Char(required=True, index=True, string='Source key')
    ydental_kind = fields.Selection([('receipt', 'Receipt'), ('replenishment', 'Replenishment'), ('treatment', 'Treatment consumption'),
        ('chairside', 'Chairside medicine'), ('prescription', 'Take home prescription'), ('inventory', 'Inventory correction'),
        ('transfer', 'Same company transfer'), ('return', 'Physical return'), ('verification', 'Return verification')], required=True, string='Source kind')
    ydental_source_namespace = fields.Char(required=True, string='Source namespace')
    ydental_fingerprint = fields.Char(required=True)
    ydental_product_id = fields.Many2one('product.product', required=True, ondelete='restrict', string='Product')
    ydental_lot_id = fields.Many2one('stock.lot', required=True, ondelete='restrict', string='Lot')
    ydental_quantity = fields.Float(required=True, digits='Product Unit', string='Stock quantity')
    ydental_input_quantity = fields.Float(required=True, digits=0, string='Confirmed input quantity')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict', string='Confirmed input unit')
    ydental_unit_snapshot = fields.Json(required=True, string='Unit precision snapshot')
    ydental_from_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='From location')
    ydental_to_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='To location')
    ydental_target_store_id = fields.Many2one('ydental.access.store', ondelete='restrict', string='Transfer target')
    ydental_move_id = fields.Many2one('stock.move', ondelete='restrict', string='Native movement')
    ydental_parent_id = fields.Many2one('ydental.inventory.event', ondelete='restrict', string='Original issue or return')
    ydental_responsible_id = fields.Many2one('res.users', required=True, ondelete='restrict', string='Responsible user')
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', string='Actual source actor')
    ydental_summary = fields.Char(string='Necessary execution summary')
    ydental_reason = fields.Char(required=True, string='Evidence and reason')
    ydental_price_snapshot = fields.Json(string='Original price snapshot')
    ydental_fee_reference = fields.Char(string='Original fee association')
    ydental_actual_at = fields.Datetime(required=True, string='Actual source time')
    ydental_synthetic = fields.Boolean(string='Synthetic validation source')
    state = fields.Selection([('pending', 'Pending reconciliation'), ('done', 'Stock confirmed')], required=True, default='done')

    _source_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_source_namespace, ydental_source_key)', 'An inventory source is applied once.')
