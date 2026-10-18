from odoo import api, fields, models
from odoo.exceptions import AccessError

from .ydental_inventory_record import MUTATION


class YDentalInventoryNative(models.AbstractModel):
    _name = 'ydental.inventory.native'
    _description = 'Controlled native inventory access'

    def _inventory_guard(self, values=None):
        if self.env.context.get('ydental_inventory_mutation') is MUTATION:
            return
        # Stock roles use the workbench, including users who also hold native
        # stock groups. JSON cannot forge the server object mutation token.
        if not self.env.su and self.env.user.has_group('ydental_base.ydental_base_group_user'):
            raise AccessError(self.env._('access_denied: Use the store inventory workbench.'))
        values = values or {}
        for field, model in (('location_id', 'stock.location'), ('location_dest_id', 'stock.location'),
                ('lot_id', 'stock.lot'), ('move_id', 'stock.move')):
            if field in self._fields:
                linked = self.sudo()[field]
                if linked and linked.filtered('ydental_store_id'):
                    raise AccessError(self.env._('access_denied: Managed inventory requires a controlled source.'))
                if values.get(field) and self.env[model].sudo().browse(values[field]).ydental_store_id:
                    raise AccessError(self.env._('access_denied: Managed inventory requires a controlled source.'))
        if values.get('product_id') and self.env['product.product'].sudo().browse(values['product_id']).ydental_inventory_kind:
            raise AccessError(self.env._('access_denied: Managed inventory requires a controlled source.'))
        if self.sudo().filtered('ydental_store_id') or values and values.get('ydental_store_id'):
            raise AccessError(self.env._('access_denied: Managed inventory requires a controlled source.'))

    def _inventory_read_domain(self, operation='read'):
        # Native Settings administration reads shared stock configuration when
        # creating a company. It still cannot read store-owned inventory or
        # gain native mutation permission through this metadata read exception.
        if (self.env.user.has_group('ydental_base.ydental_base_group_user')
                and (operation != 'read' or not self.env.is_system())):
            return fields.Domain.FALSE
        return fields.Domain('ydental_store_id', '=', False)

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        return domain if self.env.su else domain & self._inventory_read_domain(operation)

    def check_access(self, operation):
        if not self.env.su:
            domain = self._inventory_read_domain(operation)
            if domain.is_false() or self.sudo().filtered_domain(domain).ids != self.ids:
                raise AccessError(self.env._('access_denied: Native inventory is available only through the scoped workbench.'))
        return super().check_access(operation)

    def fetch(self, field_names):
        self.check_access('read')
        return super().fetch(field_names)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._inventory_guard(values)
        return super().create(vals_list)

    def write(self, vals):
        self._inventory_guard(vals)
        return super().write(vals)

    def unlink(self):
        self._inventory_guard()
        return super().unlink()
