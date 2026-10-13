from odoo import fields, models


class YDentalSettlementPayment(models.Model):
    _name = 'ydental.settlement.payment'
    _description = 'Offline confirmation linked to native payment'
    _inherit = 'ydental.settlement.record'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_payment_id = fields.Many2one('account.payment', required=True, ondelete='restrict')
    ydental_cashier_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_channel = fields.Selection([
        ('cash', 'Cash'), ('wechat', 'WeChat offline'),
        ('alipay', 'Alipay offline'), ('card', 'Bank card offline'),
    ], required=True)
    ydental_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_actual_at = fields.Datetime(required=True)
    ydental_entered_at = fields.Datetime(required=True)
    ydental_business_date = fields.Date(required=True)
    ydental_proof = fields.Char(required=True)
    ydental_key = fields.Char(required=True)
    ydental_invoice_ids = fields.Many2many('account.move', relation='ydental_settlement_payment_invoice_rel',
                                           column1='settlement_payment_id', column2='invoice_id')

    _payment_once = models.Constraint('UNIQUE(ydental_payment_id)', 'A native payment has one offline confirmation.')
    _key_once = models.Constraint('UNIQUE(ydental_store_id, ydental_cashier_id, ydental_key)', 'Payment request key must be unique.')
