from odoo import api, fields, models
from odoo.exceptions import AccessError

from .ydental_inventory_record import MUTATION


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def _inventory_product_domain(self):
        return fields.Domain('ydental_inventory_kind', '=', False)

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        return domain if self.env.su else domain & self._inventory_product_domain()

    def check_access(self, operation):
        if not self.env.su and self.sudo().filtered('ydental_inventory_kind'):
            raise AccessError(self.env._('access_denied: Use the inventory product summary.'))
        return super().check_access(operation)

    def fetch(self, field_names):
        self.check_access('read')
        return super().fetch(field_names)

    def _inventory_product_guard(self, values):
        owned = self.sudo().filtered('ydental_inventory_kind') or values.get('ydental_inventory_kind')
        if values.get('product_tmpl_id'):
            owned = owned or self.env['product.template'].sudo().browse(values['product_tmpl_id']).ydental_inventory_kind

        if owned and self.env.context.get('ydental_inventory_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Inventory master data requires group catalog authority.'))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._inventory_product_guard(values)
        return super().create(vals_list)

    def write(self, vals):
        self._inventory_product_guard(vals)
        return super().write(vals)

    def unlink(self):
        self._inventory_product_guard({})
        return super().unlink()
