from odoo import api, fields, models
from odoo.exceptions import AccessError


_EVIDENCE_MUTATION = object()


class YDentalConsentEvidence(models.Model):
    _name = 'ydental.consent.evidence'
    _description = 'Uploaded consent evidence with an explicit human verification result'
    _order = 'id desc'

    original_id = fields.Many2one('ydental.document.original', required=True, ondelete='restrict')
    patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    template_id = fields.Many2one('ydental.document.template', ondelete='restrict')
    template_sha256 = fields.Char(required=True)
    uploaded_by_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    uploaded_at = fields.Datetime(required=True)
    filename = fields.Char(required=True)
    sha256 = fields.Char(required=True)
    synthetic = fields.Boolean(required=True)
    attachment_id = fields.Many2one('ir.attachment', ondelete='restrict')
    state = fields.Selection([('pending', 'Uploaded / awaiting verification'), ('verified', 'Verification accepted'),
        ('rejected', 'Verification rejected')], required=True, default='pending')
    verified_by_id = fields.Many2one('res.users', ondelete='restrict')
    verified_at = fields.Datetime()
    verification_reason = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_consent_evidence_mutation') is not _EVIDENCE_MUTATION:
            raise AccessError(self.env._('access_denied: Use the controlled consent evidence upload.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_consent_evidence_mutation') is not _EVIDENCE_MUTATION:
            raise AccessError(self.env._('history_immutable: Consent evidence is immutable.'))
        if set(vals) == {'attachment_id'} and not any(self.mapped('attachment_id')):
            return super().write(vals)
        if (set(vals) == {'state', 'verified_by_id', 'verified_at', 'verification_reason'}
                and all(row.state == 'pending' for row in self)):
            return super().write(vals)
        raise AccessError(self.env._('history_immutable: Keep the uploaded file and original verification conclusion.'))

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Consent evidence cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_consent_evidence_mutation=_EVIDENCE_MUTATION).create(vals)

    def _save(self, vals):
        return self.with_context(ydental_consent_evidence_mutation=_EVIDENCE_MUTATION).write(vals)
