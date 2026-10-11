from odoo import api, fields, models
from odoo.exceptions import AccessError


_PARTNER_MUTATION = object()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # This administrative back-reference exposes no clinical field or related
    # compute. It cannot be changed through ordinary imports, RPC or contacts.
    ydental_patient_owner_id = fields.Many2one('ydental.patient', ondelete='restrict', copy=False,
                                              groups='base.group_no_one', index=True, string='Patient owner')

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        if operation == 'read' and not self.env.su and not self.env[
            'ydental.patient.service'
        ]._can_read_patient_partners():
            domain &= fields.Domain('ydental_patient_owner_id', '=', False)
        return domain

    def check_access(self, operation):
        if operation == 'read' and not self.env.su and self.sudo().mapped(
            'ydental_patient_owner_id'
        ) and not self.env['ydental.patient.service']._can_read_patient_partners():
            raise AccessError(self.env._('access_denied: Patient administration permission is required.'))
        return super().check_access(operation)

    def fetch(self, field_names):
        # Recheck live grants before native fetch can reuse its access/cache.
        self.check_access('read')
        return super().fetch(field_names)

    def export_data(self, fields_to_export):
        self.check_access('read')
        if not self.env.su and self.sudo().mapped('ydental_patient_owner_id'):
            self.env['ydental.access.service']._check('export', 'write')
        return super().export_data(fields_to_export)

    def _can_return_content(self, field_name, access_token=None):
        self.check_access('read')
        return super()._can_return_content(field_name, access_token)

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
