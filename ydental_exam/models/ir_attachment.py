from odoo import models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _ydental_blocked_source_models(self):
        return super()._ydental_blocked_source_models() + (
            'ydental.exam.result', 'ydental.exam.version', 'ydental.exam.qualification', 'ydental.exam.receipt')
