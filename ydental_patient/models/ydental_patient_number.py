from odoo import fields, models


class YDentalPatientNumber(models.Model):
    _name = 'ydental.patient.number'
    _description = 'Stable original and canonical patient number mapping'
    _inherit = 'ydental.patient.record'
    _ydental_global = True

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True)
    _number_unique = models.Constraint('UNIQUE(name)', 'A patient number mapping must be unique.')
