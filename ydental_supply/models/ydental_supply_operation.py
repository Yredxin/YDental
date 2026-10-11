from odoo import fields, models


class YDentalSupplyOperation(models.Model):
    _name = 'ydental.supply.operation'
    _description = 'Idempotent supply action receipt'
    _inherit = 'ydental.supply.record'

    ydental_key = fields.Char(required=True, index=True, string='Idempotency key')
    ydental_fingerprint = fields.Char(required=True, string='Request fingerprint')
    ydental_result = fields.Json(required=True, string='Result')

    _key_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_key)', 'Supply action keys must be unique within a store.')
