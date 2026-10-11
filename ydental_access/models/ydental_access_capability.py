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
            self.env['ydental.access.audit'].sudo().create([
                self.env['ydental.access.service']._audit_values(
                    'capability.create', 'personnel', record, after=record._audit_snapshot(), source='model_create',
                ) for record in records
            ])
        return records

    def write(self, vals):
        if not self.env.su:
            self._check_dictionary_manager()
            before = {record.id: record._audit_snapshot() for record in self}
        result = super().write(vals)
        if not self.env.su:
            snapshots = {record.id: record._audit_snapshot() for record in self}
            self.env['ydental.access.audit'].sudo().create([
                self.env['ydental.access.service']._audit_values(
                    'capability.modify', 'personnel', record, before=before[record.id],
                    after=snapshots[record.id], source='model_write',
                ) for record in self if before[record.id] != snapshots[record.id]
            ])
        return result
