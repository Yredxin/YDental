from odoo import models
from odoo.exceptions import AccessError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _can_return_content(self, field_name, access_token=None):
        source_models = self.env['ydental.access.service']._get_sources().values()
        if self.sudo().res_model in source_models:
            # Public flags and bearer attachment links cannot bypass source
            # authorization, including immediately after permission revocation.
            service = self.env['ydental.access.service']
            session = service._scope()
            source = self.env[self.sudo().res_model].browse(self.sudo().res_id)
            source.check_access('read')
            service._audit('source.download', source.sudo().ydental_category, source,
                           session.ydental_store_id.id, source='native_attachment')
            return True
        return super()._can_return_content(field_name, access_token)

    def write(self, vals):
        if not self.env.su:
            sources = self.env['ydental.access.service']._get_sources().values()
            if any(a.sudo().res_model in sources for a in self) and {'public', 'access_token', 'res_model', 'res_id'} & vals.keys():
                raise AccessError(self.env._('access_denied: Protected attachments cannot be published or moved.'))
        return super().write(vals)
