import zoneinfo

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class YDentalAccessStore(models.Model):
    _name = 'ydental.access.store'
    _description = 'YDental operating store'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', index=True)
    ydental_timezone = fields.Char(required=True)
    active = fields.Boolean(default=True)

    @api.constrains('ydental_timezone')
    def _check_timezone(self):
        for store in self:
            try:
                zoneinfo.ZoneInfo(store.ydental_timezone)
            except (zoneinfo.ZoneInfoNotFoundError, ValueError, TypeError) as error:
                raise ValidationError(self.env._('A valid IANA store timezone is required.')) from error

    def _check_group_company(self, company_ids):
        service = self.env['ydental.access.service']
        service._require_internal()
        if not service._is_group_manager() or not set(company_ids) <= set(self.env.user.company_ids.ids):
            raise AccessError(self.env._('access_denied: Group administration within allowed companies is required.'))

    def _audit_snapshot(self):
        self.ensure_one()
        return {'name': self.name, 'company_id': self.company_id.id,
                'timezone': self.ydental_timezone, 'active': self.active}

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            self._check_group_company([vals.get('company_id', self.env.company.id) for vals in vals_list])
        stores = super().create(vals_list)
        if not self.env.su:
            for store in stores:
                self.env['ydental.access.service']._audit('store.create', 'personnel', store, store.id,
                                                       after=store._audit_snapshot(), source='model_create')
        return stores

    def write(self, vals):
        if 'company_id' in vals and self.env['ydental.access.membership'].sudo().with_context(active_test=False).search_count([
            ('ydental_store_id', 'in', self.ids),
        ]):
            raise AccessError(self.env._('Store company cannot be changed after staff assignment.'))
        if not self.env.su:
            self._check_group_company(self.company_id.ids + ([vals['company_id']] if 'company_id' in vals else []))
            before = {store.id: store._audit_snapshot() for store in self}
        result = super().write(vals)
        if not self.env.su:
            for store in self:
                after = store._audit_snapshot()
                if before[store.id] != after:
                    self.env['ydental.access.service']._audit('store.modify', 'personnel', store, store.id,
                                                           before=before[store.id], after=after, source='model_write')
        return result
