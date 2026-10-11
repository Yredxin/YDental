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

    def write(self, vals):
        if 'company_id' in vals and self.env['ydental.access.membership'].sudo().with_context(active_test=False).search_count([
            ('ydental_store_id', 'in', self.ids),
        ]):
            raise AccessError(self.env._('Store company cannot be changed after staff assignment.'))
        return super().write(vals)
