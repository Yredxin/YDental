from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class YDentalFollowupPolicy(models.Model):
    _name = 'ydental.followup.policy'
    _description = 'Store follow-up notification policy'

    name = fields.Char(required=True)
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict', index=True)
    ydental_timezone = fields.Char(related='ydental_store_id.ydental_timezone', readonly=True)
    ydental_enabled = fields.Boolean(default=False)
    ydental_channel_mode = fields.Selection([
        ('disabled', 'No patient channel'), ('controlled_test_sink', 'Controlled test sink only'),
    ], required=True, default='disabled')
    ydental_lead_hours = fields.Integer(required=True, default=24)
    ydental_quiet_start = fields.Char(required=True, default='21:00')
    ydental_quiet_end = fields.Char(required=True, default='08:00')
    ydental_daily_limit = fields.Integer(required=True, default=1)
    ydental_unbooked_window_hours = fields.Integer(required=True, default=72)

    _store_once = models.Constraint('UNIQUE(ydental_store_id)', 'A store can have one follow-up notification policy.')

    @api.constrains('ydental_lead_hours', 'ydental_quiet_start', 'ydental_quiet_end', 'ydental_daily_limit',
                    'ydental_unbooked_window_hours')
    def _check_policy(self):
        for policy in self:
            for value in (policy.ydental_quiet_start, policy.ydental_quiet_end):
                try:
                    hour, minute = (int(part) for part in value.split(':'))
                except (ValueError, AttributeError) as error:
                    raise ValidationError(self.env._('Quiet hours must use HH:MM.')) from error
                if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                    raise ValidationError(self.env._('Quiet hours must use a valid clock time.'))
            if (not 0 <= policy.ydental_lead_hours <= 168 or not 1 <= policy.ydental_daily_limit <= 20 or
                    not 1 <= policy.ydental_unbooked_window_hours <= 720):
                raise ValidationError(self.env._('Reminder lead time or daily limit is outside its safe range.'))

    def _check_admin(self):
        access = self.env['ydental.access.service']
        access._require_internal()
        if not access._is_group_manager():
            raise AccessError(self.env._('access_denied: Group administration is required to change notification policy.'))
        if any(record.ydental_store_id.company_id not in self.env.user.company_ids for record in self):
            raise AccessError(self.env._('access_denied: The store company is outside this account scope.'))

    @api.model_create_multi
    def create(self, vals_list):
        access = self.env['ydental.access.service']
        access._require_internal()
        if not access._is_group_manager():
            raise AccessError(self.env._('access_denied: Group administration is required to change notification policy.'))
        for vals in vals_list:
            store = self.env['ydental.access.store'].sudo().browse(vals.get('ydental_store_id')).exists()
            if not store or store.company_id not in self.env.user.company_ids:
                raise AccessError(self.env._('access_denied: The store company is outside this account scope.'))
        records = super().create(vals_list)
        for record in records:
            access._audit('followup.policy.create', 'followup', record, record.ydental_store_id.id,
                          after={'enabled': record.ydental_enabled, 'channel_mode': record.ydental_channel_mode,
                                 'daily_limit': record.ydental_daily_limit}, source='policy_model')
        return records

    def write(self, vals):
        self._check_admin()
        if 'ydental_store_id' in vals:
            raise AccessError(self.env._('Notification policy cannot move between stores.'))
        before = {record.id: (record.ydental_enabled, record.ydental_channel_mode,
                              record.ydental_daily_limit, record.ydental_lead_hours,
                              record.ydental_unbooked_window_hours) for record in self}
        result = super().write(vals)
        access = self.env['ydental.access.service']
        for record in self:
            access._audit('followup.policy.modify', 'followup', record, record.ydental_store_id.id,
                          before={'enabled': before[record.id][0], 'channel_mode': before[record.id][1],
                                  'daily_limit': before[record.id][2], 'lead_hours': before[record.id][3],
                                  'unbooked_window_hours': before[record.id][4]},
                          after={'enabled': record.ydental_enabled, 'channel_mode': record.ydental_channel_mode,
                                 'daily_limit': record.ydental_daily_limit, 'lead_hours': record.ydental_lead_hours,
                                 'unbooked_window_hours': record.ydental_unbooked_window_hours},
                          source='policy_model')
        return result

    def unlink(self):
        raise AccessError(self.env._('Notification policy history cannot be deleted.'))
