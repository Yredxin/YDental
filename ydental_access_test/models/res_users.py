from odoo import fields, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = 'res.users'

    ydental_test_default_store_id = fields.Many2one('ydental.access.store', groups=fields.NO_ACCESS)

    def write(self, vals):
        if 'ydental_test_default_store_id' in vals and not self.env.su:
            raise AccessError('Synthetic defaults are server fixtures only.')
        return super().write(vals)
