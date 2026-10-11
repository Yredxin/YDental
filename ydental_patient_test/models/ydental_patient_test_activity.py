from odoo import fields, models


class YDentalPatientTestActivity(models.Model):
    _name = 'ydental.patient.test.activity'
    _description = 'Synthetic active reference, not an appointment or queue'
    _inherit = 'ydental.patient.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_kind = fields.Selection([
        ('reservation', 'Synthetic reservation reference'), ('queue', 'Synthetic exclusive number reference'),
        ('execution', 'Synthetic executing reference'),
    ], required=True)
    ydental_active = fields.Boolean(default=True)
    ydental_fail_migration = fields.Boolean(default=False)
