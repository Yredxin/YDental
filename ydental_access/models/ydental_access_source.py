from odoo import api, fields, models
from odoo.exceptions import AccessError

from .constants import CATEGORIES, RANK


class YDentalAccessSource(models.AbstractModel):
    _name = 'ydental.access.source'
    _description = 'YDental source authorization contract'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict', index=True)
    ydental_category = fields.Selection(CATEGORIES, required=True)

    def _source_domain(self, operation):
        service = self.env['ydental.access.service']
        session = service._scope(write=operation != 'read')
        member = service._membership(self.env.uid, session.ydental_store_id.id)
        if not member or not member.ydental_employee_id.active:
            return fields.Domain.FALSE
        levels = service._levels(member)
        minimum = 1 if operation == 'read' else 2
        categories = [code for code, value in levels.items() if RANK[value] >= minimum]
        domain = fields.Domain.AND([
            fields.Domain('ydental_store_id', '=', session.ydental_store_id.id),
            fields.Domain('ydental_category', 'in', categories),
        ])
        if operation == 'read' and self.env.context.get('ydental_purpose') == 'care':
            clinical = [c for c in ('medical', 'exam') if c in categories]
            domain |= fields.Domain('ydental_category', 'in', clinical)
        if operation != 'read' and service._get_execution_store_id() not in (
            False, session.ydental_store_id.id,
        ):
            return fields.Domain.FALSE
        if operation == 'unlink':
            return fields.Domain.FALSE
        return domain

    def _access_domain(self, operation):
        if self.env.su:
            return super()._access_domain(operation)
        return super()._access_domain(operation) & self._source_domain(operation)

    def check_access(self, operation):
        if not self.env.su:
            # Do not let the ORM read cache bypass a changed binding.
            domain = self._source_domain(operation)
            if domain.is_false() or self and self.sudo().filtered_domain(domain).ids != self.ids:
                self.env['ydental.access.service']._denial('source.' + operation)
                raise AccessError(self.env._('access_denied: This source is outside the authorized store scope.'))
        return super().check_access(operation)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            service = self.env['ydental.access.service']
            session = service._scope(write=True)
            for vals in vals_list:
                if vals.get('ydental_store_id') != session.ydental_store_id.id:
                    raise AccessError(self.env._('access_denied: Source store must match the login scope.'))
                service._check(vals.get('ydental_category'), 'write', write=True)
        records = super().create(vals_list)
        if not self.env.su:
            records._source_audit('source.create')
        return records

    def write(self, vals):
        if not self.env.su:
            self.check_access('write')
            if {'ydental_store_id', 'ydental_category'} & vals.keys():
                raise AccessError(self.env._('access_denied: Source ownership cannot be changed.'))
        result = super().write(vals)
        if not self.env.su:
            self._source_audit('source.modify', after={'fields': sorted(vals)})
        return result

    def read(self, fields=None, load='_classic_read'):
        result = super().read(fields, load)
        if not self.env.su:
            self._source_audit('source.view')
        return result

    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        records = super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
        if not self.env.su:
            records._source_audit('source.view')
        return records

    def export_data(self, fields_to_export):
        service = self.env['ydental.access.service']
        service._check('export', 'write')
        self.check_access('read')
        result = super().export_data(fields_to_export)
        self._source_audit('source.export')
        return result

    def _source_audit(self, event, before=None, after=None):
        service = self.env['ydental.access.service']
        session = service._scope()
        if self:
            self.env['ydental.access.audit'].sudo().create([
                service._audit_values(event, source.sudo().ydental_category, source,
                                      session.ydental_store_id.id, source='source_model', before=before, after=after)
                for source in self
            ])
