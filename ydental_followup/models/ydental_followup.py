from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalFollowup(models.Model):
    _name = 'ydental.followup'
    _description = 'Patient follow-up plan and contact state'
    _inherit = ['ydental.access.source', 'mail.thread', 'mail.activity.mixin']
    _order = 'ydental_planned_at, id'

    name = fields.Char(required=True, index=True)
    ydental_category = fields.Selection(default='followup', readonly=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_source_event_id = fields.Many2one('ydental.treatment.event', required=True, ondelete='restrict', index=True)
    ydental_source_document_id = fields.Many2one(
        related='ydental_source_event_id.ydental_document_id', store=True, index=True, related_sudo=False,
    )
    ydental_followup_type = fields.Selection([
        ('post_visit', 'Post-visit follow-up'), ('lab_arrival', 'Laboratory arrival'), ('other', 'Other'),
    ], required=True, default='post_visit', index=True)
    ydental_planned_at = fields.Datetime(required=True, index=True)
    ydental_deadline_at = fields.Datetime(index=True)
    ydental_responsible_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_appointment_id = fields.Many2one('ydental.intake.entitlement', ondelete='restrict', index=True)
    ydental_appointment_at = fields.Datetime(related='ydental_appointment_id.ydental_claim_id.ydental_slot_id.ydental_start', store=True, index=True)
    ydental_appointment_status = fields.Selection([
        ('none', 'Not booked'), ('booked', 'Booked'), ('not_arrived', 'Did not arrive'),
        ('arrived', 'Arrived, not yet treated'), ('seen', 'Treated'), ('cancelled', 'Cancelled'),
    ], required=True, default='none', index=True)
    ydental_arrival_id = fields.Many2one('ydental.intake.arrival', ondelete='restrict', readonly=True)
    ydental_completed_event_id = fields.Many2one('ydental.treatment.event', ondelete='restrict', readonly=True)
    ydental_completed_execution_id = fields.Many2one('ydental.queue.execution', ondelete='restrict', readonly=True)
    ydental_lab_order_id = fields.Integer(index=True)
    ydental_lab_cycle_key = fields.Char(index=True)
    state = fields.Selection([
        ('planned', 'Planned'), ('to_notify', 'Contact required'), ('notified', 'Contacted'),
        ('done', 'Completed at actual visit'), ('closed', 'Closed with reason'),
    ], required=True, default='planned', index=True, tracking=True)
    ydental_version = fields.Integer(required=True, default=1, readonly=True)
    ydental_schedule_version = fields.Integer(required=True, default=1, readonly=True, index=True)
    ydental_active_notification_request_id = fields.Char(readonly=True, copy=False)
    ydental_active_notification_schedule_version = fields.Integer(default=0, required=True, readonly=True, copy=False)
    ydental_closed_reason = fields.Char(readonly=True)
    ydental_created_by_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')

    _lab_cycle_unique = models.Constraint(
        'UNIQUE(ydental_lab_order_id, ydental_lab_cycle_key)',
        'A laboratory order cycle can create only one passive follow-up.',
    )

    def _source_domain(self, operation):
        if operation not in ('read', 'write'):
            return fields.Domain.FALSE
        self.env['ydental.access.service']._check('followup', 'write' if operation == 'write' else 'read',
                                                  write=operation == 'write')
        return super()._source_domain(operation)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_followup_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a follow-up business action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_followup_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a follow-up business action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Follow-up history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_followup_mutation=_MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.sudo().with_context(ydental_followup_mutation=_MUTATION).write(
                dict(values, ydental_version=record.ydental_version + 1))

    def _cron_run_due(self):
        return self.env['ydental.followup.service']._run_due()
