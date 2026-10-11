from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {
            'supply_' + entity: 'ydental.supply.' + entity for entity in
            ('policy', 'assignment', 'slot', 'claim', 'event', 'operation', 'feedback', 'disposition', 'business')}

    def _get_default_store_id(self):
        candidates = self.env['ydental.supply.service']._default_candidates()
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            return False
        previous = self.env['ydental.access.session'].sudo().search([
            ('ydental_user_id', '=', self.env.uid), ('ydental_store_id', '!=', False)], order='write_date desc, id desc')
        for session in previous:
            member = self._membership(self.env.uid, session.ydental_store_id.id)
            if session.ydental_store_id.active and member and member.ydental_employee_id.active:
                return session.ydental_store_id.id
        return super()._get_default_store_id()

    def _after_membership_removed(self, membership):
        result = super()._after_membership_removed(membership)
        self.env['ydental.supply.service']._membership_removed(membership)
        return result
