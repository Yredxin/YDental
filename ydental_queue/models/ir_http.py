from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user.has_group('ydental_base.ydental_base_group_user'):
            result['ydental_workstation'] = self.env['ydental.queue.service']._status()
        return result
