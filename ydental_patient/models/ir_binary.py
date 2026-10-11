from odoo import models


class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        record = super()._find_record(xmlid, res_model, res_id, access_token, field)
        if record._name == 'ir.attachment':
            # Core accepts a valid limited-field HMAC token before calling
            # _can_return_content. Rebind to the requester and recheck protected
            # patient sources even when that core path already returned sudo.
            requester_record = record.with_env(self.env)
            requester_record._ydental_check_source()
        return record
