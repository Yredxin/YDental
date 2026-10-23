from odoo import api, fields, models
from odoo.exceptions import AccessError

from .constants import CATEGORIES, RANK


_QUERY_GUARD = object()


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
        if not categories:
            return fields.Domain.FALSE
        domain = fields.Domain.AND([
            fields.Domain('ydental_store_id', '=', session.ydental_store_id.id),
            fields.Domain('ydental_category', 'in', categories),
        ])
        if operation == 'read':
            clinical = [c for c in ('medical', 'exam') if c in categories]
            domain |= (fields.Domain('ydental_category', 'in', clinical) &
                       service._get_care_domain(self._name))
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
        domain = super()._access_domain(operation)
        if domain.is_false():
            return domain
        try:
            source_domain = self._source_domain(operation)
        except AccessError:
            # Core has_access() is a boolean probe, including native menu
            # filtering. A missing business grant must hide this model only.
            # Explicit record check_access() keeps its original rejection.
            return fields.Domain.FALSE
        return domain & source_domain

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

    def search_fetch(self, domain, field_names=None, offset=0, limit=None, order=None):
        records = super().search_fetch(domain, field_names, offset=offset, limit=limit, order=order)
        if not self.env.su:
            records._source_audit('source.view')
        return records

    def _source_query(self, operation, callback):
        self.check_access('read')
        if self.env.su or self.env.context.get('ydental_query_guard') is _QUERY_GUARD:
            return callback(self)
        result = callback(self.with_context(ydental_query_guard=_QUERY_GUARD))
        service = self.env['ydental.access.service']
        values = service._audit_values(
            'source.query', 'query', self.browse(), service._scope().ydental_store_id.id,
            source='source_query', after={'operation': operation},
        )
        values['ydental_target_id'] = 0
        self.env['ydental.access.audit'].sudo().create(values)
        return result

    @api.model
    def search_count(self, domain, limit=None):
        return self._source_query('count', lambda records: super(
            YDentalAccessSource, records).search_count(domain, limit=limit))

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        return self._source_query('name_search', lambda records: super(
            YDentalAccessSource, records).name_search(name, domain, operator, limit))

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        return self._source_query('aggregate', lambda records: super(
            YDentalAccessSource, records)._read_group(domain, groupby, aggregates, having, offset, limit, order))

    @api.model
    def _read_grouping_sets(self, domain, grouping_sets, aggregates=(), order=None):
        return self._source_query('aggregate', lambda records: super(
            YDentalAccessSource, records)._read_grouping_sets(domain, grouping_sets, aggregates, order))

    @api.model
    def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        return self._source_query('aggregate', lambda records: super(
            YDentalAccessSource, records).formatted_read_group(domain, groupby, aggregates, having, offset, limit, order))

    @api.model
    def formatted_read_grouping_sets(self, domain, grouping_sets, aggregates=(), *, order=None):
        return self._source_query('aggregate', lambda records: super(
            YDentalAccessSource, records).formatted_read_grouping_sets(domain, grouping_sets, aggregates, order=order))

    def export_data(self, fields_to_export):
        service = self.env['ydental.access.service']
        service._check('export', 'write')
        self.check_access('read')
        result = super().export_data(fields_to_export)
        self._source_audit('source.export')
        return result

    def _source_audit(self, event, before=None, after=None):
        if self.env.context.get('ydental_query_guard') is _QUERY_GUARD:
            return
        service = self.env['ydental.access.service']
        session = service._scope()
        if self:
            self.env['ydental.access.audit'].sudo().create([
                service._audit_values(event, source.sudo().ydental_category, source,
                                      session.ydental_store_id.id, source='source_model', before=before, after=after)
                for source in self
            ])
