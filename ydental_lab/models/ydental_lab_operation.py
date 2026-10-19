from odoo import fields, models

from .ydental_lab_record import MUTATION


class YDentalLabOperation(models.Model):
    _name = 'ydental.lab.operation'
    _description = 'Laboratory action idempotency receipt'
    _inherit = 'ydental.lab.record'

    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_result = fields.Json(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    _store_key_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_key)', 'Laboratory action key is unique per store.')
