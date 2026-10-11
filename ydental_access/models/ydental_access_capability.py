from odoo import api, fields, models
from odoo.exceptions import AccessError

from .constants import GROUP_MANAGER


class YDentalAccessCapability(models.Model):
    _name = 'ydental.access.capability'
    _description = 'YDental common capability dictionary'

    name = fields.Char(required=True, translate=True)
    ydental_code = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint('UNIQUE(ydental_code)', 'Capability codes must be unique.')

    def _check_dictionary_manager(self):
        self.env['ydental.access.service']._require_internal()
        if not self.env.user.has_group(GROUP_MANAGER):
            raise AccessError(self.env._('access_denied: Group administration is required.'))

    def _audit_snapshot(self):
        self.ensure_one()
        return {'name': self.name, 'code': self.ydental_code, 'active': self.active}

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            self._check_dictionary_manager()
        records = super().create(vals_list)
        if not self.env.su:
            for record in records:
                self.env['ydental.access.service']._audit('capability.create', 'personnel', record,
                                                       after=record._audit_snapshot(), source='model_create')
        return records

    def write(self, vals):
        if not self.env.su:
            self._check_dictionary_manager()
            before = {record.id: record._audit_snapshot() for record in self}
        result = super().write(vals)
        if not self.env.su:
            for record in self:
                after = record._audit_snapshot()
                if before[record.id] != after:
                    self.env['ydental.access.service']._audit('capability.modify', 'personnel', record,
                                                           before=before[record.id], after=after, source='model_write')
        return result
