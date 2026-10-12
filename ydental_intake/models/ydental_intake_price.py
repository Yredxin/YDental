from odoo import fields, models
from odoo.exceptions import AccessError


class YDentalIntakePrice(models.Model):
    _name = 'ydental.intake.price'
    _description = 'Reviewed store price version'
    _inherit = 'ydental.intake.record'

    ydental_category = fields.Selection(default='price')
    state = fields.Selection([('draft', 'Draft'), ('reviewed', 'Reviewed'), ('published', 'Published')], default='draft', required=True)
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict', index=True)
    ydental_pricelist_id = fields.Many2one('product.pricelist', ondelete='restrict')
    ydental_rule_id = fields.Many2one('product.pricelist.item', ondelete='restrict')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_unit_price = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_start = fields.Datetime(required=True)
    ydental_end = fields.Datetime(required=True)
    ydental_reviewed_by_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_published_by_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_published_at = fields.Datetime()
    ydental_reason = fields.Char(required=True)

    _interval = models.Constraint('CHECK(ydental_end > ydental_start)', 'Price validity must have positive duration.')
    _positive = models.Constraint('CHECK(ydental_unit_price > 0)', 'A published base price must be positive. Free service requires an explicit discount.')


class YDentalIntakeSnapshot(models.Model):
    _name = 'ydental.intake.snapshot'
    _description = 'Immutable demonstration price snapshot, not a fee'
    _inherit = 'ydental.intake.record'

    ydental_category = fields.Selection(default='price')
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict')
    ydental_price_id = fields.Many2one('ydental.intake.price', required=True, ondelete='restrict')
    ydental_product_name = fields.Char(required=True)
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_quantity_digits = fields.Integer(required=True)
    ydental_currency_rounding = fields.Float(required=True, digits=(16, 8))
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_uom_name = fields.Char(required=True)
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_unit_price = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_quoted_at = fields.Datetime(required=True)
    ydental_policy = fields.Selection([('demo_confirmation', 'Demonstration confirmation time price, not production policy')], required=True)
    ydental_source = fields.Char(required=True, index=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    _source_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_source)', 'A price source can only be snapshotted once.')

    def _save(self, values):
        raise AccessError(self.env._('Price snapshots are immutable. Recover the original source snapshot.'))
