from odoo import fields, models
from odoo.exceptions import ValidationError


class YDentalLabCodeBind(models.TransientModel):
    _name = 'ydental.lab.code.bind'
    _description = 'Bind one external laboratory package code'

    order_id = fields.Many2one('ydental.lab.order', required=True, readonly=True, ondelete='cascade')
    code = fields.Char(required=True)

    def action_apply(self):
        self.ensure_one()
        if not self.order_id:
            raise ValidationError(self.env._('Select an authorized laboratory order.'))
        self.env['ydental.lab.service']._operate('bind_code', {
            'order_id': self.order_id.id, 'code': self.code,
        }, self.env['ydental.lab.service']._new_key())
        return {'type': 'ir.actions.act_window_close'}
