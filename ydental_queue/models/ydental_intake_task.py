from odoo import fields, models


class YDentalIntakeTask(models.Model):
    _inherit = 'ydental.intake.task'

    ydental_queue_opportunity_used = fields.Boolean(readonly=True)
