from odoo import fields, models


class YDentalSupplyEvent(models.Model):
    _name = 'ydental.supply.event'
    _description = 'Immutable supply accounting event'
    _inherit = 'ydental.supply.record'
    _order = 'id'

    ydental_slot_id = fields.Many2one('ydental.supply.slot', ondelete='restrict', index=True, string='Capacity slot')
    ydental_claim_id = fields.Many2one('ydental.supply.claim', ondelete='restrict', string='Capacity entitlement')
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', string='Actor')
    ydental_operation = fields.Char(required=True, string='Operation')
    ydental_reason = fields.Char(required=True, string='Reason')
    ydental_before = fields.Json(, string='Before')
    ydental_after = fields.Json(, string='After')
    ydental_policy_id = fields.Many2one('ydental.supply.policy', ondelete='restrict', string='Policy version')

    def _save(self, values):
        from odoo.exceptions import AccessError
        raise AccessError(self.env._('Ledger events are immutable.'))
