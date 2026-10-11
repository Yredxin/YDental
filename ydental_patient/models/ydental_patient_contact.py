from odoo import fields, models


class YDentalPatientContact(models.Model):
    _name = 'ydental.patient.contact'
    _description = 'Administrative contact or declared guardian relationship'
    _inherit = 'ydental.patient.record'
    _ydental_global = True

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True)
    ydental_partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    ydental_relation = fields.Selection([
        ('contact', 'Contact'), ('guardian', 'Declared guardian'), ('emergency', 'Emergency contact'),
    ], required=True)
    ydental_relationship = fields.Char(required=True)
    ydental_phone = fields.Char()
    ydental_phone_region = fields.Char()
    ydental_phone_normalized = fields.Char(index=True, readonly=True)
    ydental_phone_status = fields.Selection([
        ('empty', 'Not provided'), ('normalized', 'Normalized'), ('review', 'Manual verification required'),
    ], required=True, readonly=True)
    ydental_email = fields.Char()
    ydental_verified = fields.Boolean(readonly=True)
    ydental_verification_note = fields.Char()
    active = fields.Boolean(default=True)
