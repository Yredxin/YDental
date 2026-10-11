from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalSupplyRecord(models.AbstractModel):
    _name = 'ydental.supply.record'
    _description = 'Controlled supply record'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='capacity', readonly=True)
    ydental_version = fields.Integer(default=1, readonly=True, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_supply_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled supply action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_supply_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled supply action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Supply history cannot be deleted.'))

    def _save(self, values):
        # Only private validated services receive this unforgeable context token.
        for record in self:
            record.with_context(ydental_supply_mutation=_MUTATION).write(
                dict(values, ydental_version=record.ydental_version + 1))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_supply_mutation=_MUTATION).create(values)
