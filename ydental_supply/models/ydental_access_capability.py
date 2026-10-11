from odoo import models


class YDentalAccessCapability(models.Model):
    _inherit = 'ydental.access.capability'

    def write(self, vals):
        result = super().write(vals)
        if 'active' in vals:
            service = self.env['ydental.supply.service']
            service._lock()
            slots = self.env['ydental.supply.slot'].sudo().search([('state', '=', 'published')])
            for store, records in slots.grouped('ydental_store_id').items():
                service._suspend_affected(store, records, 'Capability dictionary changed')
        return result
