from odoo import api, fields, models
from odoo.exceptions import AccessError

from .ydental_clinical_document import _MUTATION


class YDentalClinicalVersion(models.Model):
    _name = 'ydental.clinical.version'
    _description = 'Immutable authored clinical text version'
    _inherit = 'ydental.access.source'
    _order = 'id desc'

    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_document_id = fields.Many2one('ydental.clinical.document', required=True, ondelete='restrict', index=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True)
    ydental_number = fields.Integer(required=True)
    ydental_content = fields.Json(required=True)
    ydental_author_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_recorded_at = fields.Datetime(required=True)
    ydental_kind = fields.Selection([('save', 'Draft saved'), ('confirm', 'Text confirmed'),
                                     ('correct', 'Text correction')], required=True)
    ydental_reason = fields.Char()
    ydental_previous_id = fields.Many2one('ydental.clinical.version', ondelete='restrict')
    ydental_request_key = fields.Char(required=True)
    ydental_request_digest = fields.Char(required=True)
    ydental_template = fields.Char(required=True)

    _number_unique = models.Constraint('UNIQUE(ydental_document_id, ydental_number)', 'Document version is unique.')
    _request_unique = models.Constraint('UNIQUE(ydental_document_id, ydental_request_key)', 'A save request is unique.')

    def _source_domain(self, operation):
        if operation == 'read':
            self.env['ydental.clinical.service']._access()
        return super()._source_domain(operation) if operation == 'read' else fields.Domain.FALSE

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_clinical_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a clinical document action.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Clinical versions are immutable.'))

    def unlink(self):
        raise AccessError(self.env._('Clinical versions are immutable.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_clinical_mutation=_MUTATION).create(values)
