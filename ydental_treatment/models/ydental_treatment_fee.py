from odoo import fields, models


class YDentalTreatmentFee(models.Model):
    _name = 'ydental.treatment.fee'
    _description = 'YDentalTreatmentFee'
    _inherit = 'ydental.treatment.record'

    ydental_event_id = fields.Many2one('ydental.treatment.event', required=True, ondelete='restrict', index=True)
    ydental_parent_id = fields.Many2one('ydental.treatment.fee', ondelete='restrict')
    ydental_price_snapshot_id = fields.Many2one('ydental.intake.snapshot', ondelete='restrict')
    ydental_price_review_id = fields.Many2one('ydental.treatment.price.review', ondelete='restrict')
    ydental_medicine_link_id = fields.Many2one('ydental.treatment.medicine.link', ondelete='restrict')
    ydental_product_id = fields.Many2one('product.product', ondelete='restrict')
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_unit_price = fields.Float(required=True, digits=(16, 6))
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_policy = fields.Selection([('demo_confirmation', 'Demonstration; production pricing policy awaits approval')], required=True)
    _one_event = models.Constraint('UNIQUE(ydental_event_id)', 'An execution creates one immutable fee source.')
    _price_positive = models.Constraint('CHECK(ydental_unit_price > 0)', 'A fee source requires a verified nonzero price.')
