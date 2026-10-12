from odoo import fields, models


class YDentalTreatmentReceipt(models.Model):
    _name = 'ydental.treatment.receipt'
    _description = 'YDentalTreatmentReceipt'
    _inherit = 'ydental.treatment.record'

    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_result = fields.Json(required=True)
    _key_once = models.Constraint('UNIQUE(ydental_actor_id, ydental_key)', 'An action key has one stable result.')
