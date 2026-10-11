from odoo import fields, models


class YDentalSupplyClaim(models.Model):
    _name = 'ydental.supply.claim'
    _description = 'Capacity entitlement ledger source'
    _inherit = 'ydental.supply.record'

    ydental_slot_id = fields.Many2one('ydental.supply.slot', required=True, ondelete='restrict', index=True)
    ydental_capability_id = fields.Many2one('ydental.access.capability', required=True, ondelete='restrict')
    ydental_pool = fields.Selection([('reservation', 'Reservation'), ('walkin', 'Walk-in')], required=True)
    ydental_source = fields.Char(required=True, index=True)
    ydental_source_key = fields.Char(required=True, index=True)
    state = fields.Selection([('held', 'Held'), ('consumed', 'Consumed'), ('cancelled', 'Cancelled')], default='held', required=True)

    _source_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_source, ydental_source_key)', 'One capacity entitlement per source is required.')
