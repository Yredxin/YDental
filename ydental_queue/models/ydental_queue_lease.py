from odoo import fields, models


class YDentalQueueLease(models.Model):
    _name = 'ydental.queue.lease'
    _description = 'Actor session workstation connection'
    _inherit = 'ydental.queue.record'

    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict', index=True)
    ydental_session_id = fields.Many2one('ydental.access.session', required=True, ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_revision = fields.Integer(required=True, groups=fields.NO_ACCESS)
    ydental_token_hash = fields.Char(required=True, copy=False, groups=fields.NO_ACCESS)
    ydental_connection_hash = fields.Char(required=True, copy=False, groups=fields.NO_ACCESS)
    ydental_heartbeat_at = fields.Datetime(required=True)
    ydental_expires_at = fields.Datetime(required=True)
    ydental_active = fields.Boolean(default=True)
    ydental_release_reason = fields.Selection([('holder_exit', 'Holder exit'), ('timeout', 'Connection timeout')])

    _one_actor = models.UniqueIndex('(ydental_actor_id) WHERE ydental_active')
    _one_station = models.UniqueIndex('(ydental_station_id) WHERE ydental_active')
