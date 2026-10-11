from odoo import fields, models
from odoo.exceptions import AccessError

from .constants import GROUP_MANAGER


class ResUsers(models.Model):
    _inherit = 'res.users'

    ydental_job_title = fields.Char(groups='ydental_access.ydental_group_manager,hr.group_hr_user')
    ydental_capability_ids = fields.Many2many(
        'ydental.access.capability', groups='ydental_access.ydental_group_manager,hr.group_hr_user',
    )

    def write(self, vals):
        if {'ydental_job_title', 'ydental_capability_ids'} & vals.keys() and not (
            self.env.su or self.env.user.has_group(GROUP_MANAGER)
        ):
            raise AccessError(self.env._('Group administration is required for common staff fields.'))
        return super().write(vals)

    def _after_session_login(self):
        super()._after_session_login()
        if self.env.user.has_group('ydental_base.ydental_base_group_user'):
            self.env['ydental.access.service']._audit(
                'login', 'personnel', self.env.user, source='native_authenticated_login',
            )
