from odoo import models
from odoo.exceptions import UserError


class YDentalSpaceStation(models.Model):
    _inherit = 'ydental.space.station'

    def _check_space_change(self, values):
        super()._check_space_change(values)
        # S02 already authorized and locked the floor. Serialize the S03 reverse
        # references before structural changes, including ancestor topology.
        self.env['ydental.supply.service']._lock()
        if {'ydental_area_id', 'reporting_topology'} & values.keys():
            if self.env['ydental.supply.slot'].sudo().search_count([('ydental_station_id', 'in', self.ids)]):
                raise UserError(self.env._('A workstation with supply history cannot change reporting topology.'))

    def write(self, vals):
        result = super().write(vals)
        if {'active', 'ydental_enabled', 'ydental_callable', 'ydental_add_capability_ids', 'ydental_remove_capability_ids'} & vals.keys():
            service = self.env['ydental.supply.service']
            service._handle_assignment_conflicts()
            slots = self.env['ydental.supply.slot'].sudo().search([('ydental_station_id', 'in', self.ids), ('state', '=', 'published')])
            for store, records in slots.grouped('ydental_store_id').items():
                service._suspend_affected(store, records, 'Workstation supply changed')
        return result
