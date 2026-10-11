from odoo import models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        result = super().write(vals)
        if 'active' in vals:
            self.env['ydental.supply.service']._handle_assignment_conflicts()
        return result
