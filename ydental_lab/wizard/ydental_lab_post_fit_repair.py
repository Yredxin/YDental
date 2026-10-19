from odoo import fields, models
from odoo.exceptions import ValidationError


class YDentalLabPostFitRepair(models.TransientModel):
    _name = 'ydental.lab.post.fit.repair'
    _description = 'Open a linked post-fit laboratory repair cycle'

    order_id = fields.Many2one('ydental.lab.order', required=True, readonly=True, ondelete='cascade')
    reason = fields.Char(required=True, size=240)

    def action_apply(self):
        self.ensure_one()
        if not self.order_id:
            raise ValidationError(self.env._('Select the completed laboratory order.'))
        result = self.env['ydental.lab.service']._operate(
            'post_fit_repair', {'order_id': self.order_id.id, 'reason': self.reason},
            'post-fit-repair-wizard-%s-v1' % self.id,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Linked post-fit repair cycle'),
            'res_model': 'ydental.lab.order',
            'view_mode': 'form',
            'res_id': result['repair_order_id'],
            'target': 'current',
        }
