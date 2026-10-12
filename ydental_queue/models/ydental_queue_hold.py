from odoo import fields, models


class YDentalQueueHold(models.Model):
    _name = 'ydental.queue.hold'
    _description = 'Original workstation return reservation, never actual execution'
    _inherit = 'ydental.queue.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_target_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict')
    ydental_lease_id = fields.Many2one('ydental.queue.lease', required=True, ondelete='restrict')
    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict')
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_created_at = fields.Datetime(required=True)
    ydental_ended_at = fields.Datetime()
    state = fields.Selection([('active', 'Waiting for patient return'), ('verify', 'On-site verification required'),
                              ('restored', 'Patient returned'), ('handover', 'Handed over')], default='active', required=True)

    _one_source = models.Constraint('UNIQUE(ydental_execution_id)', 'A segment reserves its workstation once.')
    _one_patient = models.UniqueIndex("(ydental_patient_id) WHERE state IN ('active', 'verify')")
    _one_lease = models.UniqueIndex("(ydental_lease_id) WHERE state IN ('active', 'verify')")


class YDentalQueueAppendPermit(models.Model):
    _name = 'ydental.queue.append.permit'
    _description = 'Explicit task-bound stopped-area admission permit'
    _inherit = 'ydental.queue.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict', index=True)
    ydental_mapping_id = fields.Many2one('ydental.intake.mapping', required=True, ondelete='restrict')
    ydental_capability_id = fields.Many2one('ydental.access.capability', required=True, ondelete='restrict')
    ydental_business_date = fields.Date(required=True)
    ydental_timezone = fields.Char(required=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_created_at = fields.Datetime(required=True)
    ydental_reason = fields.Char(required=True)
    ydental_revoked_by_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_revoked_at = fields.Datetime()
    ydental_revoke_reason = fields.Char()
    state = fields.Selection([('active', 'Authorized for this segment'), ('started', 'Actual execution started'),
                              ('ended', 'Segment ended'), ('revoked', 'Permit revoked')], required=True, default='active')

    _one_task = models.UniqueIndex("(ydental_task_id) WHERE state IN ('active', 'started')")
