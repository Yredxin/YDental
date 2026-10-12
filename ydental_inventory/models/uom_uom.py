from odoo import fields, models
from odoo.exceptions import AccessError

from .ydental_inventory_record import MUTATION


class UomUom(models.Model):
    _inherit = 'uom.uom'

    def _inventory_unit_guard(self):
        if self.env.context.get('ydental_inventory_mutation') is MUTATION:
            return
        # Freeze conversion ancestry once referenced by managed products. New
        # units remain available; historical source precision stays immutable.
        descendants = self.sudo().search([('id', 'child_of', self.ids)])
        domain = fields.Domain('ydental_inventory_kind', '!=', False) & (
            fields.Domain('uom_id', 'in', descendants.ids) | fields.Domain('ydental_issue_uom_id', 'in', descendants.ids))
        if self.env['product.template'].sudo().with_context(active_test=False).search_count(domain):
            raise AccessError(self.env._('access_denied: Referenced inventory unit conversions are immutable.'))

    def write(self, vals):
        if {'relative_factor', 'relative_uom_id', 'active'} & vals.keys():
            self._inventory_unit_guard()
        return super().write(vals)

    def unlink(self):
        self._inventory_unit_guard()
        return super().unlink()
