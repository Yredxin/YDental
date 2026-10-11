from odoo import fields, models


class YDentalSupplyAssignment(models.Model):
    _name = 'ydental.supply.assignment'
    _description = 'Default personnel assignment'
    _inherit = 'ydental.supply.record'
    _order = 'ydental_start, id'

    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict')
    ydental_station_id = fields.Many2one('ydental.space.station', ondelete='restrict', index=True)
    ydental_area_id = fields.Many2one('ydental.space.area', ondelete='restrict', index=True)
    ydental_start = fields.Datetime(required=True, index=True)
    ydental_end = fields.Datetime(required=True)
    state = fields.Selection([('active', 'Effective'), ('cancelled', 'Cancelled')], default='active', required=True)
    ydental_reason = fields.Char()
    ydental_warning = fields.Char(compute='_compute_warning')

    def _compute_warning(self):
        service = self.env['ydental.supply.service']
        for record in self:
            record.ydental_warning = service._assignment_warning(record.sudo())
