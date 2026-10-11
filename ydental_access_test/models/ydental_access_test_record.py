from odoo import fields, models
from odoo.exceptions import AccessError


class YDentalAccessTestRecord(models.Model):
    _name = 'ydental.access.test.record'
    _description = 'Synthetic S01 authorization source, never patient data'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_text = fields.Char()

    ydental_test_care_target = fields.Boolean(groups=fields.NO_ACCESS)

    def write(self, vals):
        if 'ydental_test_care_target' in vals and not self.env.su:
            raise AccessError('Synthetic care targets are server fixtures only.')
        return super().write(vals)
