from odoo import fields, models


class YDentalPatient(models.Model):
    _name = 'ydental.patient'
    _description = 'Group patient identity, administrative information only'
    _inherit = 'ydental.patient.record'
    _ydental_global = True

    name = fields.Char(index='trigram')
    active = fields.Boolean(default=True)
    ydental_number = fields.Char(required=True, readonly=True, index=True)
    ydental_partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    ydental_birth_date = fields.Date()
    ydental_birth_note = fields.Char()
    ydental_sex = fields.Selection([
        ('unknown', 'Unknown'), ('female', 'Female'), ('male', 'Male'), ('other', 'Other'),
    ], required=True, default='unknown')
    ydental_phone = fields.Char()
    ydental_phone_region = fields.Char()
    ydental_phone_normalized = fields.Char(index=True, readonly=True)
    ydental_phone_status = fields.Selection([
        ('empty', 'Not provided'), ('normalized', 'Normalized'), ('review', 'Manual verification required'),
    ], required=True, readonly=True)
    ydental_email = fields.Char(index=True)
    ydental_merged_into_id = fields.Many2one('ydental.patient', ondelete='restrict', readonly=True, index=True)
    ydental_recorded_at = fields.Datetime(required=True, readonly=True)
    ydental_business_date = fields.Date(required=True, readonly=True)

    _number_unique = models.Constraint('UNIQUE(ydental_number)', 'Patient numbers must be group unique.')
    _partner_unique = models.Constraint('UNIQUE(ydental_partner_id)', 'A contact has only one patient identity.')
    _no_self_merge = models.Constraint('CHECK(ydental_merged_into_id != id)', 'A patient cannot merge into itself.')
