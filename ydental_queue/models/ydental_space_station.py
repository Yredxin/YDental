from odoo import models


class YDentalSpaceStation(models.Model):
    _inherit = 'ydental.space.station'

    def _get_runtime_states(self):
        self.check_access('read')
        queue = self.env['ydental.queue.service']
        result = []
        for station in self:
            lease = queue._model('lease').search([('ydental_station_id', '=', station.id), ('ydental_active', '=', True)], limit=1)
            unresolved = queue._model('execution').search([('ydental_lease_id.ydental_station_id', '=', station.id), ('state', 'in', ('serving', 'verify'))], limit=1)
            hold = queue._model('hold').search([('ydental_station_id', '=', station.id), ('state', 'in', ('active', 'verify'))], limit=1)
            state = unresolved.state if unresolved else (('holding' if hold.state == 'active' and lease else 'verify') if hold else ('occupied' if lease else 'idle'))
            result.append({'id': station.id, 'state': state, 'label': state})
        return result
