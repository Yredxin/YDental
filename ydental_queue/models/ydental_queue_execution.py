from odoo import fields, models


class YDentalQueueExecution(models.Model):
    _name = 'ydental.queue.execution'
    _description = 'Authoritative patient actual execution fence'
    _inherit = 'ydental.queue.record'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_entry_id = fields.Many2one('ydental.queue.entry', ondelete='restrict')
    ydental_resumed_from_id = fields.Many2one('ydental.queue.execution', ondelete='restrict')
    ydental_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict', index=True)
    ydental_service_snapshot = fields.Json()
    ydental_lease_id = fields.Many2one('ydental.queue.lease', required=True, ondelete='restrict')
    ydental_started_at = fields.Datetime(required=True)
    ydental_ended_at = fields.Datetime()
    ydental_handed_over_at = fields.Datetime()
    state = fields.Selection([('serving', 'Serving'), ('verify', 'Away, on-site verification required'),
                              ('reserved', 'Segment ended for external service'), ('handover', 'Segment handed over')], required=True, default='serving')

    _unresolved_patient = models.UniqueIndex("(ydental_patient_id) WHERE state IN ('serving', 'verify')")
    _one_entry = models.Constraint('UNIQUE(ydental_entry_id)', 'A queue entry starts once.')
    _unresolved_lease = models.UniqueIndex("(ydental_lease_id) WHERE state IN ('serving', 'verify')")
    _one_resume = models.Constraint('UNIQUE(ydental_resumed_from_id)', 'A held segment resumes once.')
    _source_identity = models.Constraint(
        'CHECK ((ydental_entry_id IS NOT NULL) <> (ydental_resumed_from_id IS NOT NULL))',
        'An execution starts from one entry or resumes one historical segment.')
    _terminal_time = models.Constraint(
        "CHECK ((state IN ('serving', 'verify') AND ydental_ended_at IS NULL) OR (state IN ('reserved', 'handover') AND ydental_ended_at IS NOT NULL))",
        'A terminal segment retains its end time.')

    def init(self):
        # A used lifetime SQL constraints. B replaces only these two constraints;
        # their names are fixed server identifiers. All historical rows survive.
        from odoo.tools.sql import constraint_definition, drop_constraint
        for name in ('ydental_queue_execution_one_patient', 'ydental_queue_execution_one_lease'):
            if constraint_definition(self.env.cr, self._table, name):
                drop_constraint(self.env.cr, self._table, name)
        self.env.cr.execute('''UPDATE ydental_queue_execution e SET ydental_task_id=q.ydental_task_id
            FROM ydental_queue_entry q WHERE e.ydental_entry_id=q.id AND e.ydental_task_id IS NULL''')
        self.env.cr.execute('''UPDATE ydental_queue_execution e SET ydental_service_snapshot=jsonb_build_object(
            'catalog_id', c.id, 'capability_id', q.ydental_capability_id,
            'qualification', COALESCE(c.ydental_qualification, ''), 'area_id', m.ydental_area_id,
            'execution_area_id', m.ydental_execution_area_id)
            FROM ydental_queue_entry q JOIN ydental_intake_task t ON q.ydental_task_id=t.id
            JOIN ydental_intake_mapping m ON t.ydental_mapping_id=m.id
            JOIN ydental_intake_catalog c ON m.ydental_catalog_id=c.id
            WHERE e.ydental_entry_id=q.id AND e.ydental_service_snapshot IS NULL''')
