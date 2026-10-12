from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .ydental_intake_record import MUTATION


class YDentalIntakeNative(models.AbstractModel):
    _name = 'ydental.intake.native'
    _description = 'Protect native objects owned by versioned service catalog'
    _ydental_marker_path = 'ydental_intake_owned'
    _ydental_price_path = None

    def _ydental_read_domain(self):
        ordinary = fields.Domain(self._ydental_marker_path, '=', False)
        try:
            service = self.env['ydental.intake.service']
            store = service._read_access()
            if self._ydental_price_path:
                service.env['ydental.access.service']._check('price', 'read')
                return ordinary | fields.Domain(self._ydental_price_path, '=', store.id)
            return fields.Domain.TRUE
        except (AccessError, UserError):
            return ordinary

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        if not self.env.su and operation == 'read':
            domain &= self._ydental_read_domain()
        return domain

    def check_access(self, operation):
        if not self.env.su and operation == 'read' and self.sudo().filtered_domain(self._ydental_read_domain()).ids != self.ids:
            raise AccessError(self.env._('access_denied: This native service source is outside the current scope.'))
        return super().check_access(operation)

    def fetch(self, field_names):
        self.check_access('read')
        return super().fetch(field_names)

    def _ydental_owned_values(self, values):
        return values.get('ydental_intake_owned') or 'ydental_intake_owned' in values or 'ydental_intake_store_id' in values

    def _ydental_guard(self, vals=None):
        if self.env.context.get('ydental_intake_mutation') is MUTATION:
            return
        if self.sudo().filtered_domain(fields.Domain(self._ydental_marker_path, '=', True)) or vals and self._ydental_owned_values(vals):
            raise AccessError(self.env._('access_denied: Native service data must use the controlled catalog or price action.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._ydental_guard(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._ydental_guard(vals)
        return super().write(vals)

    def unlink(self):
        self._ydental_guard()
        return super().unlink()


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'ydental.intake.native']

    ydental_intake_owned = fields.Boolean(readonly=True, copy=True)


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'ydental.intake.native']
    _ydental_marker_path = 'product_tmpl_id.ydental_intake_owned'

    def _ydental_owned_values(self, values):
        template_id = values.get('product_tmpl_id')
        return super()._ydental_owned_values(values) or template_id and self.env['product.template'].sudo().browse(template_id).ydental_intake_owned


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'ydental.intake.native']
    _ydental_price_path = 'ydental_intake_store_id'

    ydental_intake_owned = fields.Boolean(readonly=True, copy=True)
    ydental_intake_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict')


class ProductPricelistItem(models.Model):
    _name = 'product.pricelist.item'
    _inherit = ['product.pricelist.item', 'ydental.intake.native']
    _ydental_marker_path = 'pricelist_id.ydental_intake_owned'
    _ydental_price_path = 'pricelist_id.ydental_intake_store_id'

    def _ydental_owned_values(self, values):
        pricelist_id = values.get('pricelist_id')
        return super()._ydental_owned_values(values) or pricelist_id and self.env['product.pricelist'].sudo().browse(pricelist_id).ydental_intake_owned
