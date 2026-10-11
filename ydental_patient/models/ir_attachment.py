from odoo import api, fields, models
from odoo.exceptions import AccessError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _ydental_blocked_source_models(self):
        # Untyped files on administrative records cannot carry clinical data
        # past the separate medical source ACL. S12 adds typed signed originals.
        return ('ydental.patient', 'ydental.patient.number', 'ydental.patient.relation',
                'ydental.patient.contact', 'ydental.patient.policy', 'ydental.patient.merge',
                'ydental.patient.operation')

    def _ydental_check_source(self):
        for attachment in self.sudo():
            blocked = attachment.res_model in self._ydental_blocked_source_models()
            if attachment.res_model == 'res.partner' and attachment.res_id:
                blocked = bool(self.env['res.partner'].sudo().browse(attachment.res_id).exists().ydental_patient_owner_id)
            if blocked:
                raise AccessError(self.env._('access_denied: Untyped patient contact attachments are unavailable.'))
            if attachment.res_model in self.env['ydental.access.service']._get_patient_care_sources():
                self.env[attachment.res_model].browse(attachment.res_id).check_access('read')

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        if self.env.su:
            return domain
        protected = self.env['res.partner'].sudo()._search([('ydental_patient_owner_id', '!=', False)])
        return domain & ~fields.Domain('res_model', 'in', self._ydental_blocked_source_models()) & ~(
            fields.Domain('res_model', '=', 'res.partner') & fields.Domain('res_id', 'in', protected))

    def check_access(self, operation):
        if not self.env.su:
            self._ydental_check_source()
        return super().check_access(operation)

    def read(self, fields=None, load='_classic_read'):
        # Native binary caches can already contain sudo-loaded data. Recheck
        # the live source before read, even when no database fetch is needed.
        self.check_access('read')
        return super().read(fields, load)

    def fetch(self, field_names):
        self.check_access('read')
        return super().fetch(field_names)

    def _can_return_content(self, field_name, access_token=None):
        # Enforce source access even for public flags and bearer URLs.
        self._ydental_check_source()
        return super()._can_return_content(field_name, access_token)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            for vals in vals_list:
                model, record_id = vals.get('res_model'), vals.get('res_id')
                if model in self._ydental_blocked_source_models() or (model == 'res.partner' and record_id and
                        self.env['res.partner'].sudo().browse(record_id).exists().ydental_patient_owner_id):
                    raise AccessError(self.env._('access_denied: Use a typed clinical attachment source.'))
        return super().create(vals_list)
