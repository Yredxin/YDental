from odoo import fields, models
from odoo.exceptions import AccessError


class YDentalAccessAudit(models.Model):
    _name = 'ydental.access.audit'
    _description = 'YDental immutable business audit'
    _order = 'id desc'

    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_store_id = fields.Many2one('ydental.access.store', ondelete='restrict', index=True)
    ydental_event = fields.Char(required=True)
    ydental_category = fields.Char(required=True)
    ydental_target_model = fields.Char(required=True)
    ydental_target_id = fields.Integer(required=True)
    ydental_result = fields.Selection([('accepted', 'Accepted'), ('denied', 'Denied')], required=True)
    ydental_reason = fields.Char()
    ydental_before = fields.Json()
    ydental_after = fields.Json()
    ydental_source = fields.Char(required=True)

    def write(self, vals):
        raise AccessError(self.env._('Audit events cannot be changed.'))

    def unlink(self):
        raise AccessError(self.env._('Audit events cannot be deleted.'))
