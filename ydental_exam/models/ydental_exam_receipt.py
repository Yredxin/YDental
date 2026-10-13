from odoo import fields, models


class YDentalExamReceipt(models.Model):
    _name = 'ydental.exam.receipt'
    _description = 'Idempotent examination action receipt'
    _inherit = 'ydental.treatment.record'

    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_result = fields.Json(required=True)
    _key = models.Constraint('UNIQUE(ydental_actor_id, ydental_key)', 'An actor action key is unique.')
