from odoo import api, models
from odoo.exceptions import AccessError

MODEL = 'ydental.settlement.bill.original'
ORIGINAL_MODELS = (MODEL, 'ydental.settlement.tax.original')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _ydental_blocked_source_models(self):
        # Bill files have one controlled source/export endpoint; native bearer/RPC access is denied.
        return super()._ydental_blocked_source_models() + ORIGINAL_MODELS

    def write(self, vals):
        if any(row.res_model in ORIGINAL_MODELS for row in self.sudo()) or vals.get('res_model') in ORIGINAL_MODELS:
            raise AccessError(self.env._('history_immutable: Original bill attachments cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        if any(row.res_model in ORIGINAL_MODELS for row in self.sudo()):
            raise AccessError(self.env._('history_immutable: Original bill attachments cannot be deleted.'))
        return super().unlink()


class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field='raw'):
        # Native limited-field tokens are checked before _can_return_content. Deny this source first.
        candidate = self.env.ref(xmlid, False) if xmlid else self.env[res_model].browse(res_id) if res_id and res_model in self.env else False
        if candidate and (candidate._name in ORIGINAL_MODELS or candidate._name == 'ir.attachment'
                and any(row.res_model in ORIGINAL_MODELS for row in candidate.sudo())):
            raise AccessError(self.env._('access_denied: Use the authorized internal bill original endpoint.'))
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
