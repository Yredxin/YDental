from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {'clinical_document': 'ydental.clinical.document',
                                        'clinical_version': 'ydental.clinical.version'}

    def _get_patient_care_sources(self):
        return super()._get_patient_care_sources() | {'ydental.clinical.document': 'ydental_patient_id',
                                                     'ydental.clinical.version': 'ydental_patient_id'}
