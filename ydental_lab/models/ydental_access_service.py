from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {
            'lab_vendor': 'ydental.lab.vendor',
            'lab_cooperation': 'ydental.lab.cooperation',
            'lab_order': 'ydental.lab.order',
            'lab_event': 'ydental.lab.event',
            'lab_operation': 'ydental.lab.operation',
            'lab_code_bind': 'ydental.lab.code.bind',
            'lab_code_scan': 'ydental.lab.code.scan',
            'lab_charge': 'ydental.lab.charge',
            'lab_charge_adjustment': 'ydental.lab.charge.adjustment',
            'lab_charge_credit_wizard': 'ydental.lab.charge.credit.wizard',
        }

    def _get_patient_care_sources(self):
        return super()._get_patient_care_sources() | {
            'ydental.lab.order': 'ydental_patient_id',
            'ydental.lab.event': 'ydental_order_id.ydental_patient_id',
            'ydental.lab.charge': 'ydental_patient_id',
        }
