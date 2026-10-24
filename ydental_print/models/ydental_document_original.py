from odoo import api, fields, models
from odoo.exceptions import AccessError


_ORIGINAL_INIT = object()


class YDentalDocumentOriginal(models.Model):
    _name = 'ydental.document.original'
    _description = 'Immutable source and template document original'
    _order = 'id desc'

    kind = fields.Char(required=True, index=True)
    source_model = fields.Char(required=True)
    source_id = fields.Integer(required=True, index=True)
    source_version = fields.Integer(required=True)
    purpose = fields.Char()
    patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    category = fields.Char(required=True)
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    generated_at = fields.Datetime(required=True)
    request_key = fields.Char(required=True, groups=fields.NO_ACCESS)
    version = fields.Integer(required=True)
    previous_id = fields.Many2one('ydental.document.original', ondelete='restrict')
    source_facts = fields.Json(required=True, groups=fields.NO_ACCESS)
    render_facts = fields.Json(required=True, groups=fields.NO_ACCESS)
    source_sha256 = fields.Char(required=True)
    template_id = fields.Many2one('ydental.document.template', ondelete='restrict')
    template_facts = fields.Json(required=True)
    template_sha256 = fields.Char(required=True)
    pdf_sha256 = fields.Char(required=True)
    attachment_id = fields.Many2one('ir.attachment', ondelete='restrict', copy=False)

    _version_once = models.Constraint('UNIQUE(kind, source_id, store_id, version)', 'A document original version is unique.')
    _key_once = models.Constraint('UNIQUE(actor_id, request_key)', 'An original request key is unique for its actor.')
    _positive_version = models.Constraint('CHECK(version > 0)', 'An original requires a positive version.')
    _successor_once = models.Constraint('UNIQUE(previous_id)', 'An original can have only one successor version.')
    _summary_version_once = models.UniqueIndex(
        "(store_id, (source_facts->>'selection_scope_sha256'), version) WHERE kind = 'clinical_summary'",
        'A clinical source collection scope has one original per version.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_document_original_init') is not _ORIGINAL_INIT:
            raise AccessError(self.env._('access_denied: Use the controlled document original service.'))
        return super().create(vals_list)

    def write(self, vals):
        if (self.env.context.get('ydental_document_original_init') is not _ORIGINAL_INIT
                or set(vals) != {'attachment_id'} or any(self.mapped('attachment_id'))):
            raise AccessError(self.env._('history_immutable: Document originals cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Document originals cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_document_original_init=_ORIGINAL_INIT).create(vals)

    def _attach_once(self, attachment):
        return self.with_context(ydental_document_original_init=_ORIGINAL_INIT).write({'attachment_id': attachment.id})
