from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalClinicalDocument(models.Model):
    _name = 'ydental.clinical.document'
    _description = 'Independent treatment text and responsibility'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict', index=True)
    ydental_current_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict', index=True)
    ydental_author_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_responsible_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_version = fields.Integer(required=True, default=0, readonly=True)
    ydental_content = fields.Json(readonly=True)
    ydental_saved_at = fields.Datetime(readonly=True)
    ydental_template = fields.Char(required=True, default='clinical-draft-v1', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('pending', 'Document awaiting completion'),
                              ('confirmed', 'Text confirmed')], required=True, default='draft', readonly=True)
    ydental_editor_id = fields.Many2one('res.users', ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_session_id = fields.Many2one('ydental.access.session', ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_session_revision = fields.Integer(groups=fields.NO_ACCESS)
    ydental_connection_hash = fields.Char(groups=fields.NO_ACCESS)
    ydental_editor_hash = fields.Char(groups=fields.NO_ACCESS)
    ydental_editor_expires = fields.Datetime(groups=fields.NO_ACCESS)
    ydental_editor_lease_id = fields.Many2one('ydental.queue.lease', ondelete='restrict', groups=fields.NO_ACCESS)

    _one_execution = models.Constraint('UNIQUE(ydental_execution_id)', 'An execution has one independent treatment document.')
    _one_current_execution = models.Constraint('UNIQUE(ydental_current_execution_id)', 'A current segment has one independent treatment document.')
    _positive_version = models.Constraint('CHECK(ydental_version >= 0)', 'Document versions cannot be negative.')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        self.env['ydental.clinical.service']._access()
        return super()._source_domain(operation)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_clinical_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a clinical document action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_clinical_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a clinical document action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Clinical document history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_clinical_mutation=_MUTATION).create(values)

    def _save(self, values):
        return self.with_context(ydental_clinical_mutation=_MUTATION).write(values)

    def init(self):
        # Backfill only this new clinical table from its immutable source;
        # no queue/execution history is rewritten by the module upgrade.
        self.env.cr.execute('UPDATE ydental_clinical_document SET ydental_current_execution_id=ydental_execution_id WHERE ydental_current_execution_id IS NULL')
