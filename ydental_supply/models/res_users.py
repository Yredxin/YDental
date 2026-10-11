from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        result = super().write(vals)
        if {'active', 'ydental_capability_ids'} & vals.keys():
            service = self.env['ydental.supply.service']
            service._lock()
            slots = self.env['ydental.supply.slot'].sudo().search([('state', '=', 'published')])
            for store, records in slots.grouped('ydental_store_id').items():
                service._suspend_affected(store, records, 'Staff availability or capabilities changed')
        return result
