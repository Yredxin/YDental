from odoo import fields, models


class YDentalQueueMutex(models.Model):
    _name = 'ydental.queue.mutex'
    _description = 'Queue repeatable-read serialization anchor'

    ydental_revision = fields.Integer(default=0)
