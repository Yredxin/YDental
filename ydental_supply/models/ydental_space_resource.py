from odoo import models


class YDentalSpaceResource(models.Model):
    _inherit = 'ydental.space.resource'

    def write(self, vals):
        result = super().write(vals)
        if 'ydental_capability_ids' in vals:
            service = self.env['ydental.supply.service']
            service._lock()
            slots = self.env['ydental.supply.slot'].sudo().search([('state', '=', 'published')])
            for store, records in slots.grouped('ydental_store_id').items():
                service._suspend_affected(store, records, 'Resource capabilities changed')
        return result
