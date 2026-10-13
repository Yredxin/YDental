from odoo import fields, models


class YDentalSettlementSource(models.Model):
    _name = 'ydental.settlement.source'
    _description = 'Immutable fee to native invoice line link'
    _inherit = 'ydental.settlement.record'

    ydental_fee_id = fields.Many2one('ydental.treatment.fee', required=True, ondelete='restrict', index=True)
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_invoice_id = fields.Many2one('account.move', required=True, ondelete='restrict')
    ydental_line_id = fields.Many2one('account.move.line', required=True, ondelete='restrict')
    ydental_original_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_discount = fields.Monetary(currency_field='ydental_currency_id')
    ydental_discount_reason = fields.Char()
    ydental_source_business_date = fields.Date(required=True)
    ydental_source_actual_at = fields.Datetime(required=True)
    ydental_price_version = fields.Char(required=True)

    _fee_once = models.Constraint('UNIQUE(ydental_fee_id)', 'A confirmed fee can be billed only once.')
    _line_once = models.Constraint('UNIQUE(ydental_line_id)', 'An invoice line has one source.')
