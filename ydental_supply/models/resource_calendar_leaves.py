from odoo import api, models


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    def _supply_timeoff_changed(self):
        service = self.env['ydental.supply.service']
        service._lock()
        service._handle_assignment_conflicts()
        slots = self.env['ydental.supply.slot'].sudo().search([('state', '=', 'published')])
        for store, records in slots.grouped('ydental_store_id').items():
            service._suspend_affected(store, records, 'Time off changed; verify replacement coverage')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._supply_timeoff_changed()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._supply_timeoff_changed()
        return result
