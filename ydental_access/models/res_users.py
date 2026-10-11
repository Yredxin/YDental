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
        common = bool({'ydental_job_title', 'ydental_capability_ids'} & vals.keys()) and not self.env.su
        service = self.env['ydental.access.service']
        if common:
            service._check_user_company_scope(self)
            self._ydental_check_profile_company_values(vals)
            before = {user.id: user._ydental_profile_values() for user in self}
        result = super().write(vals)
        if common:
            snapshots = {user.id: user._ydental_profile_values() for user in self}
            self.env['ydental.access.audit'].sudo().create([
                service._audit_values('profile.change', 'personnel', user, before=before[user.id],
                                      after=snapshots[user.id], source='model_write')
                for user in self if before[user.id] != snapshots[user.id]
            ])
        return result

    def _ydental_check_profile_company_values(self, vals):
        """Check proposed companies before a combined native/profile write.

        Company create/update/delete commands are separate native master-data
        actions, not part of changing common staff fields.
        """
        proposed = {vals['company_id']} if 'company_id' in vals else set()
        for command in vals.get('company_ids', []):
            if not isinstance(command, (list, tuple)) or not command or command[0] not in (3, 4, 5, 6):
                raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))
            if command[0] == fields.Command.LINK:
                proposed.add(command[1])
            elif command[0] == fields.Command.SET:
                proposed.update(command[2])
        if not proposed <= set(self.env.user.company_ids.ids):
            raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))

    def _ydental_profile_values(self):
        self.ensure_one()
        return {'job_title': self.ydental_job_title, 'capability_ids': sorted(self.ydental_capability_ids.ids)}

    def _after_session_login(self):
        super()._after_session_login()
        if self.env.user.has_group('ydental_base.ydental_base_group_user'):
            self.env['ydental.access.service']._audit(
                'login', 'personnel', self.env.user, source='native_authenticated_login',
            )
