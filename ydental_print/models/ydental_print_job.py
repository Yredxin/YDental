from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalPrintJob(models.Model):
    _name = 'ydental.print.job'
    _description = 'Short-lived demonstration PDF, never a signed original'

    # No ordinary ACL. Binary is database-only, never an ir.attachment.
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_session_id = fields.Many2one('ydental.access.session', required=True, ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_revision = fields.Integer(required=True, groups=fields.NO_ACCESS)
    ydental_kind = fields.Selection([('clinical', 'Clinical text'), ('prescription', 'Prescription'), ('consent', 'Unsigned consent sample')], required=True)
    ydental_source_id = fields.Integer(required=True)
    ydental_version = fields.Integer(required=True)
    ydental_purpose = fields.Char()
    ydental_source_digest = fields.Char(required=True)
    ydental_pdf_digest = fields.Char(required=True)
    ydental_template = fields.Char(required=True)
    ydental_versions = fields.Json(required=True)
    ydental_expires_at = fields.Datetime(required=True)
    ydental_key = fields.Char(required=True, groups=fields.NO_ACCESS)
    ydental_pdf = fields.Binary(required=True, attachment=False, groups=fields.NO_ACCESS)

    _request_once = models.Constraint('UNIQUE(ydental_session_id, ydental_revision, ydental_key)', 'A generation request is unique within its login revision.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_print_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the controlled PDF service.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('history_immutable: Demonstration PDF metadata is immutable.'))

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Retain PDF generation evidence.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_print_mutation=_MUTATION).create(values)
