from odoo import fields, models


class YDentalAccessTestRecord(models.Model):
    _name = 'ydental.access.test.record'
    _description = 'Synthetic S01 authorization source, never patient data'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_text = fields.Char()
