from odoo import fields, models


class YDentalSettlementMutex(models.Model):
    _name = 'ydental.settlement.mutex'
    _description = 'Settlement transaction snapshot serialization fence'

    ydental_revision = fields.Integer(default=0, string='Revision')
