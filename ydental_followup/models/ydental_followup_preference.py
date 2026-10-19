from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalFollowupPreference(models.Model):
    _name = 'ydental.followup.preference'
    _description = 'Store-scoped patient follow-up contact preference'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='followup', readonly=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_opt_out = fields.Boolean(default=False, required=True)
    ydental_preferred_channel = fields.Selection([
        ('phone', 'Telephone'), ('email', 'Email'), ('message', 'Message'), ('manual', 'Manual contact only'),
    ], required=True, default='manual')
    ydental_recorded_at = fields.Datetime(required=True, readonly=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')

    _patient_store_once = models.Constraint('UNIQUE(ydental_store_id, ydental_patient_id)',
                                            'A patient has one contact preference per store.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_followup_preference_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a contact preference action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_followup_preference_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a contact preference action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Contact preference history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_followup_preference_mutation=_MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.sudo().with_context(ydental_followup_preference_mutation=_MUTATION).write(values)
