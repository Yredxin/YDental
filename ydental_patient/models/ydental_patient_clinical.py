from odoo import fields, models


class YDentalPatientClinical(models.Model):
    _name = 'ydental.patient.clinical'
    _description = 'Store patient safety background, not a treatment record'
    _inherit = 'ydental.patient.record'

    ydental_category = fields.Selection(default='medical', readonly=True, string='Business category')
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True, string='Canonical patient')
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True, string='Original patient')
    ydental_identity_snapshot = fields.Json(required=True, readonly=True, string='Identity snapshot')
    ydental_allergies = fields.Text(string='Allergies')
    ydental_prior_history = fields.Text(string='Prior history')
    ydental_medication = fields.Text(string='Medication')
    ydental_recorded_at = fields.Datetime(required=True, readonly=True, string='Recorded at')
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', readonly=True, string='Actor')
