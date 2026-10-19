from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalFollowupContact(models.Model):
    _name = 'ydental.followup.contact'
    _description = 'Immutable follow-up contact attempt'
    _inherit = 'ydental.access.source'
    _order = 'ydental_contacted_at desc, id desc'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='followup', readonly=True)
    ydental_followup_id = fields.Many2one('ydental.followup', required=True, ondelete='restrict', index=True)
    ydental_contacted_at = fields.Datetime(required=True, readonly=True, index=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')
    ydental_method = fields.Selection([('phone', 'Telephone'), ('message', 'Message'), ('other', 'Other')], required=True)
    ydental_outcome = fields.Selection([
        ('no_answer', 'No answer'), ('failed', 'Failed'), ('accepted', 'Accepted by channel'),
        ('delivered', 'Confirmed delivered'), ('unknown', 'Unknown; reconcile before retry'),
    ], required=True)
    ydental_note = fields.Char()
    ydental_request_key = fields.Char(index=True)

    _request_once = models.Constraint('UNIQUE(ydental_store_id, ydental_request_key)',
                                      'A contact request key can be recorded only once per store.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_followup_contact_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Contact history is append-only.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Follow-up contact history cannot be changed.'))

    def unlink(self):
        raise AccessError(self.env._('Follow-up contact history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_followup_contact_mutation=_MUTATION).create(values)
