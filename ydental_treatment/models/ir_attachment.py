from odoo import models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _ydental_blocked_source_models(self):
        return super()._ydental_blocked_source_models() + (
            'ydental.treatment.event', 'ydental.treatment.fee', 'ydental.treatment.order',
            'ydental.treatment.line', 'ydental.treatment.segment', 'ydental.treatment.consumption',
            'ydental.treatment.price.review', 'ydental.treatment.receipt')
