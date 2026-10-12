from odoo import fields, models


class YDentalTreatmentPriceReview(models.Model):
    _name = 'ydental.treatment.price.review'
    _description = 'YDentalTreatmentPriceReview'
    _inherit = 'ydental.treatment.record'

    ydental_event_id = fields.Many2one('ydental.treatment.event', required=True, ondelete='restrict')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_unit_price = fields.Float(required=True, digits=(16, 6))
    ydental_evidence = fields.Char(required=True)
    ydental_reviewed_at = fields.Datetime(required=True)
    _event_once = models.Constraint('UNIQUE(ydental_event_id)', 'A missing historical price is reviewed once.')
    _positive = models.Constraint('CHECK(ydental_unit_price > 0)', 'Historical review requires a positive evidenced price.')
