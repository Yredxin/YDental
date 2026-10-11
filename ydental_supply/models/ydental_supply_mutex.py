from odoo import fields, models


class YDentalSupplyMutex(models.Model):
    _name = 'ydental.supply.mutex'
    _description = 'Supply transaction serialization point'

    name = fields.Char(required=True)
    ydental_revision = fields.Integer(default=0)
