from odoo import fields, models


class YDentalInventoryMutex(models.Model):
    _name = 'ydental.inventory.mutex'
    _description = 'Inventory transaction serialization fence'

    ydental_revision = fields.Integer(default=0)
