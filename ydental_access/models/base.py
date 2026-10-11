from odoo import models


class Base(models.AbstractModel):
    _inherit = 'base'

    def export_data(self, fields_to_export):
        protected = not self.env.su and self.env.user.has_group('ydental_base.ydental_base_group_user')
        if protected:
            service = self.env['ydental.access.service']
            service._check('export', 'write')
            self.check_access('read')
        result = super().export_data(fields_to_export)
        if protected and self._name not in service._get_sources().values():
            session = service._scope()
            if self:
                self.env['ydental.access.audit'].sudo().create([
                    service._audit_values('source.export', 'export', record, session.ydental_store_id.id,
                                          source='native_export') for record in self
                ])
        return result
