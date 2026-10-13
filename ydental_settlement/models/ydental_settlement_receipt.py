from odoo import fields, models


class YDentalSettlementReceipt(models.Model):
    _name = 'ydental.settlement.receipt'
    _description = 'Idempotent settlement command receipt'
    _inherit = 'ydental.settlement.record'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_operation = fields.Char(required=True)
    ydental_result = fields.Json(required=True)

    _key_once = models.Constraint('UNIQUE(ydental_store_id, ydental_actor_id, ydental_key)', 'Settlement key must be unique.')
