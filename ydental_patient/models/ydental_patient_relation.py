from odoo import fields, models


class YDentalPatientRelation(models.Model):
    _name = 'ydental.patient.relation'
    _description = 'Patient store relationship, independent of arrival'
    _inherit = 'ydental.patient.record'
    _ydental_global = True

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', readonly=True)
    ydental_superseded_by_id = fields.Many2one('ydental.patient.relation', ondelete='restrict', readonly=True)
    ydental_first_arrival = fields.Datetime(readonly=True)
    ydental_first_business_date = fields.Date(readonly=True)
    ydental_arrival_recorded_at = fields.Datetime(readonly=True)
    ydental_arrival_actor_id = fields.Many2one('res.users', ondelete='restrict', readonly=True)
    ydental_arrival_reason = fields.Char(readonly=True)
    ydental_created_at = fields.Datetime(required=True, readonly=True)

    _current_unique = models.UniqueIndex(
        '(ydental_patient_id, ydental_store_id) WHERE ydental_superseded_by_id IS NULL')
