from odoo import fields, models


class YDentalLabCodeScan(models.TransientModel):
    _name = 'ydental.lab.code.scan'
    _description = 'Resolve an external laboratory package code'

    code = fields.Char(required=True)

    def action_scan(self):
        self.ensure_one()
        return self.env['ydental.lab.service']._scan_package_code(self.code)
