from odoo import api, fields, models


class YDentalSupplyAssignment(models.Model):
    _name = 'ydental.supply.assignment'
    _description = 'Default personnel assignment'
    _inherit = 'ydental.supply.record'
    _order = 'ydental_start, id'

    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True, string='Employee account')
    ydental_employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict', string='Employee')
    ydental_station_id = fields.Many2one('ydental.space.station', ondelete='restrict', index=True, string='Workstation')
    ydental_area_id = fields.Many2one('ydental.space.area', ondelete='restrict', index=True, string='Area')
    ydental_start = fields.Datetime(required=True, index=True, string='Start')
    ydental_end = fields.Datetime(required=True, string='End')
    state = fields.Selection([('active', 'Effective'), ('cancelled', 'Cancelled')], default='active', required=True)
    ydental_reason = fields.Char(string='Reason')
    ydental_warning = fields.Char(compute='_compute_warning', string='Warning')

    @api.depends('state', 'ydental_start', 'ydental_end', 'ydental_user_id.active', 'ydental_employee_id.active',
                 'ydental_user_id.ydental_capability_ids', 'ydental_user_id.ydental_capability_ids.active',
                 'ydental_station_id.ydental_capability_ids', 'ydental_station_id.ydental_capability_ids.active',
                 'ydental_station_id.active', 'ydental_station_id.ydental_enabled')
    def _compute_warning(self):
        service = self.env['ydental.supply.service']
        for record in self:
            record.ydental_warning = service._assignment_warning(record.sudo())
