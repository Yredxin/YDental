from odoo import fields, models


class YDentalPatientContact(models.Model):
    _name = 'ydental.patient.contact'
    _description = 'Administrative contact or declared guardian relationship'
    _inherit = 'ydental.patient.record'
    _ydental_global = True

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True, string='Canonical patient')
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True, string='Original patient')
    ydental_partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', string='Administrative contact')
    ydental_relation = fields.Selection([
        ('contact', 'Contact'), ('guardian', 'Declared guardian'), ('emergency', 'Emergency contact'),
    ], required=True, string='Relation')
    ydental_relationship = fields.Char(required=True, string='Relationship')
    ydental_phone = fields.Char(string='Phone as provided')
    ydental_phone_region = fields.Char(string='Explicit phone region')
    ydental_phone_normalized = fields.Char(index=True, readonly=True, string='Normalized phone')
    ydental_phone_status = fields.Selection([
        ('empty', 'Not provided'), ('normalized', 'Normalized'), ('review', 'Manual verification required'),
    ], required=True, readonly=True, string='Phone verification status')
    ydental_email = fields.Char(string='Email')
    ydental_verified = fields.Boolean(readonly=True, string='Verified')
    ydental_verification_note = fields.Char(string='Verification note')
    active = fields.Boolean(default=True)
