from odoo import fields, models


class YDentalIntakeEntitlement(models.Model):
    _name = 'ydental.intake.entitlement'
    _description = 'Capacity-backed reservation or walk-in qualification'
    _inherit = 'ydental.intake.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_mapping_id = fields.Many2one('ydental.intake.mapping', required=True, ondelete='restrict')
    ydental_claim_id = fields.Many2one('ydental.supply.claim', required=True, ondelete='restrict')
    ydental_channel = fields.Selection([('reservation', 'Reservation'), ('phone', 'Telephone'), ('walkin', 'Walk-in')], required=True)
    state = fields.Selection([('held', 'Valid unused qualification'), ('started', 'Started, cannot return capacity'), ('cancelled', 'Qualification cancelled')], required=True, default='held')
    ydental_source_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    ydental_reason = fields.Char()

    _claim_unique = models.Constraint('UNIQUE(ydental_claim_id)', 'A claim belongs to one current qualification.')


class YDentalIntakeTask(models.Model):
    _name = 'ydental.intake.task'
    _description = 'Explicit service task, separate from qualification and queue'
    _inherit = 'ydental.intake.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_mapping_id = fields.Many2one('ydental.intake.mapping', required=True, ondelete='restrict')
    ydental_entitlement_id = fields.Many2one('ydental.intake.entitlement', ondelete='restrict')
    ydental_parent_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    ydental_source_kind = fields.Selection([('independent', 'Independent service'), ('continuation', 'Same encounter continuation'), ('derived', 'Derived external service')], default='independent', required=True)
    state = fields.Selection([('pending', 'Pending reporting'), ('accepted', 'Intake position accepted'), ('started', 'Started by downstream server'), ('done', 'Finished by downstream server'), ('cancelled', 'Qualification cancelled')], required=True, default='pending')
    ydental_missed_count = fields.Integer(default=0)
    ydental_reason = fields.Char()


class YDentalIntakeArrival(models.Model):
    _name = 'ydental.intake.arrival'
    _description = 'Actual store arrival, separate from service reporting'
    _inherit = 'ydental.intake.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_date = fields.Date(required=True)
    ydental_timezone = fields.Char(required=True)
    ydental_occurred_at = fields.Datetime(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    _arrival_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_patient_id, ydental_date)', 'One arrival fact per patient, store and local date.')


class YDentalIntakePosition(models.Model):
    _name = 'ydental.intake.position'
    _description = 'S05 accepted position contract, no queue number or calling state'
    _inherit = 'ydental.intake.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict', index=True)
    ydental_active = fields.Boolean(default=True)
    ydental_accepted_at = fields.Datetime(required=True)
    ydental_reason = fields.Char()

    _one_position = models.UniqueIndex('(ydental_patient_id) WHERE ydental_active')


class YDentalIntakeReferral(models.Model):
    _name = 'ydental.intake.referral'
    _description = 'Untimed target service request with explicit expiry'
    _inherit = 'ydental.intake.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_origin_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_identity_snapshot = fields.Json(required=True)
    ydental_mapping_id = fields.Many2one('ydental.intake.mapping', required=True, ondelete='restrict')
    ydental_source_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_valid_until = fields.Datetime(required=True)
    ydental_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    state = fields.Selection([('pending', 'Pending target walk-in qualification'), ('accepted', 'Target qualification acquired')], default='pending', required=True)
    ydental_reason = fields.Char(required=True)
