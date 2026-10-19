from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalNotificationJob(models.Model):
    _name = 'ydental.notification.job'
    _description = 'Versioned, persistent follow-up notification work item'
    _inherit = 'ydental.access.source'
    _order = 'ydental_due_at, id'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='followup', readonly=True)
    ydental_followup_id = fields.Many2one('ydental.followup', ondelete='restrict', index=True)
    ydental_responsible_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_source_model = fields.Selection([
        ('ydental.followup', 'Follow-up'), ('ydental.lab.order', 'Laboratory order'),
        ('ydental.lab.vendor', 'Supplier qualification'),
    ], required=True, index=True)
    ydental_source_res_id = fields.Integer(required=True, index=True)
    ydental_event_type = fields.Selection([
        ('appointment_reminder', 'Appointment reminder'), ('followup_contact', 'Follow-up contact'),
        ('lab_arrival', 'Laboratory arrival'), ('supplier_expiry', 'Supplier qualification expiry'),
    ], required=True, index=True)
    ydental_source_version = fields.Integer(required=True, index=True)
    ydental_channel_key = fields.Char(required=True, index=True)
    ydental_due_at = fields.Datetime(required=True, index=True)
    ydental_state = fields.Selection([
        ('pending', 'Pending'), ('dispatching', 'Dispatch in progress'), ('accepted', 'Accepted'),
        ('delivered', 'Confirmed delivered'), ('failed', 'Failed'), ('unknown', 'Unknown; reconcile'),
        ('cancelled', 'Cancelled'), ('not_configured', 'Channel not configured'),
    ], required=True, default='pending', index=True)
    ydental_request_id = fields.Char(index=True)
    ydental_attempt_count = fields.Integer(default=0, required=True)
    ydental_attempt_started_at = fields.Datetime(index=True)
    ydental_last_error = fields.Char()
    ydental_accepted_at = fields.Datetime()
    ydental_delivered_at = fields.Datetime()
    ydental_activity_id = fields.Many2one('mail.activity', ondelete='restrict')

    _event_once = models.Constraint(
        'UNIQUE(ydental_store_id, ydental_source_model, ydental_source_res_id, ydental_event_type, ydental_source_version, ydental_channel_key)',
        'The same source event version and channel can be queued only once.',
    )
    _request_once = models.Constraint('UNIQUE(ydental_request_id)', 'A dispatch request identifier belongs to one notification job.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_notification_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the notification service.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_notification_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the notification service.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Notification history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_notification_mutation=_MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.sudo().with_context(ydental_notification_mutation=_MUTATION).write(values)
