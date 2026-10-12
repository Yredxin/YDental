from odoo import api, fields, models
from odoo.exceptions import AccessError

MUTATION = object()


class YDentalInventoryRecord(models.AbstractModel):
    _name = 'ydental.inventory.record'
    _description = 'Controlled inventory history'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='warehouse')
    ydental_version = fields.Integer(default=1, required=True, readonly=True, string='Version')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        store = self.env['ydental.inventory.service']._access()
        domain = fields.Domain('ydental_store_id', '=', store.id)
        if self._name == 'ydental.inventory.event':
            domain |= fields.Domain('ydental_target_store_id', '=', store.id) & fields.Domain('ydental_kind', '=', 'transfer')
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_inventory_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled inventory action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_inventory_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled inventory action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Inventory history cannot be deleted.'))

    def _new(self, values):
        return self.with_context(ydental_inventory_mutation=MUTATION).create(values)

    def _save(self, values):
        self.ensure_one()
        return self.with_context(ydental_inventory_mutation=MUTATION).write(dict(values, ydental_version=self.ydental_version + 1))
