from odoo import api, models
from odoo.exceptions import AccessError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    _ydental_lab_source_models = ('ydental.lab.vendor', 'ydental.lab.order')

    def _ydental_check_source(self):
        super()._ydental_check_source()
        if self.env.su:
            return
        for attachment in self.sudo():
            if attachment.res_model in self._ydental_lab_source_models and attachment.res_id:
                source = self.env[attachment.res_model].browse(attachment.res_id).exists()
                if not source:
                    raise AccessError(self.env._('access_denied: Laboratory attachment source is unavailable.'))
                source.check_access('read')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.su:
            for attachment in records:
                if attachment.res_model in self._ydental_lab_source_models and attachment.res_id:
                    self.env[attachment.res_model].browse(attachment.res_id).check_access('write')
        return records

    def write(self, vals):
        if not self.env.su and {'res_model', 'res_id'} & vals.keys():
            for attachment in self:
                model = vals.get('res_model', attachment.res_model)
                record_id = vals.get('res_id', attachment.res_id)
                if model in self._ydental_lab_source_models and record_id:
                    self.env[model].browse(record_id).check_access('write')
        return super().write(vals)
