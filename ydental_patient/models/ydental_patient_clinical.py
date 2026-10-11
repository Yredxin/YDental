from odoo import fields, models


class YDentalPatientClinical(models.Model):
    _name = 'ydental.patient.clinical'
    _description = 'Store patient safety background, not a treatment record'
    _inherit = 'ydental.patient.record'

    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True)
    ydental_identity_snapshot = fields.Json(required=True, readonly=True)
    ydental_allergies = fields.Text()
    ydental_prior_history = fields.Text()
    ydental_medication = fields.Text()
    ydental_recorded_at = fields.Datetime(required=True, readonly=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', readonly=True)
