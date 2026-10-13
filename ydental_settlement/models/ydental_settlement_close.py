from odoo import fields, models


class YDentalSettlementClose(models.Model):
    _name = 'ydental.settlement.close'
    _description = 'Cashier daily close and unlock history'
    _inherit = 'ydental.settlement.record'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_cashier_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_business_date = fields.Date(required=True)
    ydental_channel = fields.Selection([
        ('cash', 'Cash'), ('wechat', 'WeChat offline'),
        ('alipay', 'Alipay offline'), ('card', 'Bank card offline'),
    ], required=True)
    ydental_state = fields.Selection([('confirmed', 'Confirmed'), ('unlocked', 'Unlocked')], required=True)
    ydental_gross = fields.Monetary(currency_field='ydental_currency_id')
    ydental_refunded = fields.Monetary(currency_field='ydental_currency_id')
    ydental_pending = fields.Monetary(currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_confirmed_at = fields.Datetime(required=True)
    ydental_unlocked_by_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_unlock_reason = fields.Char()
    ydental_unlocked_at = fields.Datetime()
    ydental_cycle = fields.Integer(required=True)

    _cycle_once = models.Constraint('UNIQUE(ydental_store_id, ydental_cashier_id, ydental_business_date, ydental_channel, ydental_cycle)',
                                    'A close cycle is unique.')
