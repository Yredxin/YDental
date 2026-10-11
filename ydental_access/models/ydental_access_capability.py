from odoo import fields, models


class YDentalAccessCapability(models.Model):
    _name = 'ydental.access.capability'
    _description = 'YDental common capability dictionary'

    name = fields.Char(required=True, translate=True)
    ydental_code = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint('UNIQUE(ydental_code)', 'Capability codes must be unique.')
