from odoo import fields, models


class YDentalInventoryConfig(models.Model):
    _name = 'ydental.inventory.config'
    _description = 'Store inventory warehouse and explicit alert policy'
    _inherit = 'ydental.inventory.record'

    ydental_warehouse_id = fields.Many2one('stock.warehouse', required=True, ondelete='restrict', string='Warehouse')
    ydental_medicine_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Pharmacy location')
    ydental_material_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Material location')
    ydental_prosthesis_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Prosthesis awaiting collection')
    ydental_quarantine_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Return verification location')
    ydental_supplier_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Supplier location')
    ydental_customer_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Actual issue location')
    ydental_loss_id = fields.Many2one('stock.location', required=True, ondelete='restrict', string='Loss location')
    ydental_policy_configured = fields.Boolean(string='Alert policy configured')
    ydental_near_days = fields.Integer(string='Near expiry days')
    ydental_wait_days = fields.Integer(string='Collection alert days')
    ydental_low_quantity = fields.Float(string='Low stock quantity', digits='Product Unit')
    ydental_policy_reason = fields.Char(string='Policy reason')

    _store_unique = models.Constraint('UNIQUE(ydental_store_id)', 'Each store has one inventory warehouse.')
    _warehouse_unique = models.Constraint('UNIQUE(ydental_warehouse_id)', 'Inventory warehouses cannot be shared between stores.')
    _policy_positive = models.Constraint('CHECK(ydental_near_days >= 0 AND ydental_wait_days >= 0 AND ydental_low_quantity >= 0)', 'Alert thresholds cannot be negative.')
