from odoo import fields, models


class YDentalInventoryOperation(models.Model):
    _name = 'ydental.inventory.operation'
    _description = 'Inventory action idempotency receipt'
    _inherit = 'ydental.inventory.record'

    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_result = fields.Json(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    _key_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_key)', 'Inventory request keys are unique within the store.')
