from odoo import fields, models


class YDentalSettlementRefund(models.Model):
    _name = 'ydental.settlement.refund'
    _description = 'Separated offline refund approval and actual execution'
    _inherit = 'ydental.settlement.record'

    ydental_payment_id = fields.Many2one('ydental.settlement.payment', required=True, ondelete='restrict')
    ydental_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_requester_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_approver_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_executor_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_reason = fields.Char(required=True)
    ydental_decision_reason = fields.Char()
    ydental_state = fields.Selection([
        ('requested', 'Requested'), ('approved', 'Approved awaiting offline refund'),
        ('failed', 'Execution failed'), ('unknown', 'External state unknown'),
        ('done', 'Actually refunded'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'),
    ], required=True, default='requested')
    ydental_native_payment_id = fields.Many2one('account.payment', ondelete='restrict')
    ydental_credit_note_id = fields.Many2one('account.move', ondelete='restrict')
    ydental_credit_note_ids = fields.Many2many('account.move', relation='ydental_settlement_refund_credit_rel',
                                                column1='refund_id', column2='move_id')
    ydental_actual_at = fields.Datetime()
    ydental_key = fields.Char(required=True)

    _key_once = models.Constraint('UNIQUE(ydental_payment_id, ydental_key)', 'Refund request key must be unique.')
