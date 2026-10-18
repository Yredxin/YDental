from odoo import models

from odoo.addons.ydental_intake.models.ydental_intake_record import MUTATION


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _force_default_sale_tax(self, companies):
        # Native company initialization must preserve versioned service sources.
        # A validated catalog action retains its existing native initialization.
        products = self if self.env.context.get('ydental_intake_mutation') is MUTATION else self.filtered(
            lambda product: not product.ydental_intake_owned)
        return super(ProductTemplate, products)._force_default_sale_tax(companies)

    def _force_default_purchase_tax(self, companies):
        products = self if self.env.context.get('ydental_intake_mutation') is MUTATION else self.filtered(
            lambda product: not product.ydental_intake_owned)
        return super(ProductTemplate, products)._force_default_purchase_tax(companies)
