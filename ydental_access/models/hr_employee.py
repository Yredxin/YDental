from odoo import fields, models
from odoo.exceptions import AccessError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ydental_job_title = fields.Char(
        related='user_id.ydental_job_title', related_sudo=False, groups='hr.group_hr_user',
    )
    ydental_capability_ids = fields.Many2many(
        related='user_id.ydental_capability_ids', related_sudo=False, groups='hr.group_hr_user',
    )

    def write(self, vals):
        if {'ydental_job_title', 'ydental_capability_ids'} & vals.keys():
            raise AccessError(self.env._('Common staff fields must be changed on the trusted account source.'))
        return super().write(vals)
