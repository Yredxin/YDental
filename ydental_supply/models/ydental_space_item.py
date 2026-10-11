from odoo import api, models


class YDentalSpaceItem(models.Model):
    _inherit = 'ydental.space.item'

    def _supply_items_changed(self, previous_stations=None):
        stations = self.sudo().ydental_station_id | (previous_stations or self.env['ydental.space.station'].sudo())
        service = self.env['ydental.supply.service']
        service._lock()
        service._handle_assignment_conflicts()
        slots = self.env['ydental.supply.slot'].sudo().search([('ydental_station_id', 'in', stations.ids), ('state', '=', 'published')])
        for store, records in slots.grouped('ydental_store_id').items():
            service._suspend_affected(store, records, 'Workstation resource placement changed')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._supply_items_changed()
        return records

    def write(self, vals):
        previous = self.sudo().ydental_station_id
        result = super().write(vals)
        if {'active', 'ydental_resource_id', 'ydental_station_id'} & vals.keys():
            self._supply_items_changed(previous)
        return result
