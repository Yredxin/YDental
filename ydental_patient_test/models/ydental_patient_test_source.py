from odoo import fields, models


class YDentalPatientTestSource(models.Model):
    _name = 'ydental.patient.test.source'
    _description = 'Synthetic history or finance source, no real downstream business'
    _inherit = 'ydental.patient.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_text = fields.Text()
    ydental_signed_fact = fields.Boolean(default=False)
