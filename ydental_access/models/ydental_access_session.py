from odoo import fields, models


class YDentalAccessSession(models.Model):
    _name = 'ydental.access.session'
    _description = 'YDental independent login store scope'

    ydental_key_hash = fields.Char(required=True, copy=False, groups=fields.NO_ACCESS)
    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_store_id = fields.Many2one('ydental.access.store', ondelete='restrict')
    ydental_revision = fields.Integer(default=0, required=True)

    _key_unique = models.Constraint('UNIQUE(ydental_key_hash)', 'Login scope must be unique.')
