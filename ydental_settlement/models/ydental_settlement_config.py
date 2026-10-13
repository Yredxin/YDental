from odoo import fields, models


class YDentalSettlementConfig(models.Model):
    _name = 'ydental.settlement.config'
    _description = 'Explicit store accounting policy'
    _inherit = 'ydental.settlement.record'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    ydental_policy = fields.Selection([
        ('demo_confirmation', 'Synthetic offline demonstration only'),
    ], required=True)
    ydental_sales_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    ydental_income_account_id = fields.Many2one('account.account', required=True, ondelete='restrict')
    ydental_adjustment_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    ydental_cash_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    ydental_wechat_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    ydental_alipay_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    ydental_card_journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')

    _store_unique = models.Constraint('UNIQUE(ydental_store_id)', 'One accounting policy per store.')
