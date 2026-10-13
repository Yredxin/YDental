from odoo import fields, models


class YDentalSettlementTrade(models.Model):
    _name = 'ydental.settlement.trade'
    _description = 'Linked native intercompany sale, purchase, stock and account evidence'
    _inherit = 'ydental.settlement.record'

    ydental_source_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_target_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_source_key = fields.Char(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    ydental_source_lot_id = fields.Many2one('stock.lot', required=True, ondelete='restrict')
    ydental_target_lot_id = fields.Many2one('stock.lot', required=True, ondelete='restrict')
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_unit_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_unit_price = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_reason = fields.Char(required=True)
    ydental_sale_order_id = fields.Many2one('sale.order', required=True, ondelete='restrict')
    ydental_purchase_order_id = fields.Many2one('purchase.order', required=True, ondelete='restrict')
    ydental_out_move_id = fields.Many2one('stock.move', required=True, ondelete='restrict')
    ydental_in_move_id = fields.Many2one('stock.move', required=True, ondelete='restrict')
    ydental_sale_invoice_id = fields.Many2one('account.move', required=True, ondelete='restrict')
    ydental_purchase_bill_id = fields.Many2one('account.move', required=True, ondelete='restrict')

    _source_once = models.Constraint(
        'UNIQUE(ydental_source_store_id, ydental_source_key)',
        'An intercompany source key can be confirmed only once.')
