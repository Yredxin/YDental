from odoo import api, fields, models
from odoo.exceptions import AccessError


_PARTNER_MUTATION = object()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # This administrative back-reference exposes no clinical field or related
    # compute. It cannot be changed through ordinary imports, RPC or contacts.
    ydental_patient_owner_id = fields.Many2one('ydental.patient', ondelete='restrict', copy=False,
                                              groups='base.group_no_one', index=True, string='Patient owner')

    @api.model_create_multi
    def create(self, vals_list):
        controlled = self.env.context.get('ydental_patient_partner_mutation') is _PARTNER_MUTATION
        if not controlled and (self.env.context.get('default_ydental_patient_owner_id') or any(
            'ydental_patient_owner_id' in vals for vals in vals_list
        )):
            raise AccessError(self.env._('access_denied: Patient contacts require a controlled identity action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_patient_partner_mutation') is not _PARTNER_MUTATION and (
            'ydental_patient_owner_id' in vals or self.sudo().mapped('ydental_patient_owner_id')
        ):
            raise AccessError(self.env._('access_denied: Maintain patient contacts through the patient workspace.'))
        return super().write(vals)

    def unlink(self):
        if self.sudo().mapped('ydental_patient_owner_id'):
            raise AccessError(self.env._('Patient contacts and original identities cannot be deleted or merged by Contacts.'))
        return super().unlink()

    def message_post(self, **kwargs):
        if self.sudo().mapped('ydental_patient_owner_id'):
            raise AccessError(self.env._('access_denied: Patient clinical information cannot be posted to contact chatter.'))
        return super().message_post(**kwargs)

    @api.model
    def _ydental_patient_new(self, values):
        context = {key: value for key, value in self.env.context.items() if not key.startswith('default_')}
        return self.with_context(context, ydental_patient_partner_mutation=_PARTNER_MUTATION,
                                 tracking_disable=True, mail_create_nosubscribe=True).create(values)

    def _ydental_patient_save(self, values):
        return self.with_context(ydental_patient_partner_mutation=_PARTNER_MUTATION,
                                 tracking_disable=True).write(values)
