from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalNotificationCallback(models.Model):
    _name = 'ydental.notification.callback'
    _description = 'Deduplicated provider callback receipt'
    _inherit = 'ydental.access.source'
    _order = 'id desc'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='followup', readonly=True)
    ydental_job_id = fields.Many2one('ydental.notification.job', required=True, ondelete='restrict', index=True)
    ydental_provider_event_id = fields.Char(required=True, index=True)
    ydental_status = fields.Selection([('accepted', 'Accepted'), ('delivered', 'Delivered'), ('failed', 'Failed')], required=True)
    ydental_received_at = fields.Datetime(required=True, readonly=True)

    _provider_event_once = models.Constraint('UNIQUE(ydental_store_id, ydental_provider_event_id)',
                                             'A provider callback can be recorded only once.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_notification_callback_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Provider callback receipts are controlled.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Provider callback receipts cannot be changed.'))

    def unlink(self):
        raise AccessError(self.env._('Provider callback receipts cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_notification_callback_mutation=_MUTATION).create(values)
