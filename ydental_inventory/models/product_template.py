from odoo import api, fields, models
from odoo.exceptions import AccessError

from .ydental_inventory_record import MUTATION


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ydental_inventory_kind = fields.Selection([('medicine', 'Medicine'), ('material', 'Material'), ('prosthesis', 'Prosthesis')], readonly=True, string='Inventory product kind')
    ydental_specification = fields.Char(readonly=True, string='Specification')
    ydental_issue_uom_id = fields.Many2one('uom.uom', readonly=True, ondelete='restrict', string='Issue unit')
    ydental_stock_step = fields.Float(default=0.01, readonly=True, digits=0, string='Minimum stock quantity step')
    ydental_suggested_quantity = fields.Float(readonly=True, digits='Product Unit', string='Suggested quantity only')

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
