from odoo import models
from odoo.exceptions import AccessError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _ydental_blocked_source_models(self):
        return super()._ydental_blocked_source_models() + ('ydental.print.job', 'ydental.document.original', 'ydental.consent.evidence')

    def write(self, vals):
        protected = ('ydental.document.original', 'ydental.consent.evidence')
        if any(row.res_model in protected for row in self.sudo()) or vals.get('res_model') in protected:
            raise AccessError(self.env._('history_immutable: Document original attachments cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        if any(row.res_model in ('ydental.document.original', 'ydental.consent.evidence') for row in self.sudo()):
            raise AccessError(self.env._('history_immutable: Document original attachments cannot be deleted.'))
        return super().unlink()


class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field='raw'):
        protected = ('ydental.document.original', 'ydental.consent.evidence')
        candidate = self.env.ref(xmlid, False) if xmlid else self.env[res_model].browse(res_id) if res_id and res_model in self.env else False
        if candidate and (candidate._name in protected or candidate._name == 'ir.attachment'
                and any(row.res_model in protected for row in candidate.sudo())):
            raise AccessError(self.env._('access_denied: Use the authorized document original endpoint.'))
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
