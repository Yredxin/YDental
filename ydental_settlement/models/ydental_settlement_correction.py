from odoo import fields, models


class YDentalSettlementCorrection(models.Model):
    _name = 'ydental.settlement.correction'
    _description = 'Audited native account reclassification for an offline label error'
    _inherit = 'ydental.settlement.record'

    ydental_payment_id = fields.Many2one('ydental.settlement.payment', required=True, ondelete='restrict')
    ydental_old_channel = fields.Selection([
        ('cash', 'Cash'), ('wechat', 'WeChat offline'),
        ('alipay', 'Alipay offline'), ('card', 'Bank card offline'),
    ], required=True)
    ydental_new_channel = fields.Selection([
        ('cash', 'Cash'), ('wechat', 'WeChat offline'),
        ('alipay', 'Alipay offline'), ('card', 'Bank card offline'),
    ], required=True)
    ydental_move_id = fields.Many2one('account.move', required=True, ondelete='restrict')
    ydental_reason = fields.Char(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_recorded_at = fields.Datetime(required=True)
