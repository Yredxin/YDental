from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {'s04_activity': 'ydental.patient.test.activity',
                                       's04_source': 'ydental.patient.test.source'}

    def _get_patient_care_sources(self):
        return super()._get_patient_care_sources() | {'ydental.patient.test.source': 'ydental_patient_id'}
