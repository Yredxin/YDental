from odoo import models
from odoo.tools.misc import verify_limited_field_access_token


class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        record = super()._find_record(xmlid, res_model, res_id, access_token, field)
        if record._name == 'res.partner':
            # Limited-field tokens may have returned sudo before the normal
            # partner content hook. They never substitute for live grants.
            record.with_env(self.env).check_access('read')
        if record._name == 'ir.attachment':
            # Core accepts a valid limited-field HMAC token before calling
            # _can_return_content. Rebind to the requester and recheck protected
            # patient sources even when that core path already returned sudo.
            requester_record = record.with_env(self.env)
            requester_record._ydental_check_source()
            sources = self.env['ydental.access.service']._get_sources().values()
            if record.sudo().res_model in sources and access_token and verify_limited_field_access_token(
                record, field, access_token, scope='binary'
            ):
                # Core skipped the normal download hook on this token path.
                # Re-enter it as the requester so permitted clinical downloads
                # retain the same source.download audit as ordinary URLs.
                requester_record._can_return_content(field, access_token)
        return record
