from odoo import fields, models


class YDentalPatientMutex(models.Model):
    _name = 'ydental.patient.mutex'
    _description = 'Patient transaction snapshot serialization fence'

    ydental_revision = fields.Integer(default=0, string='Revision')
