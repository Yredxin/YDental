from odoo import api, fields, models
from odoo.exceptions import AccessError


_TEMPLATE_MUTATION = object()


class YDentalDocumentTemplate(models.Model):
    _name = 'ydental.document.template'
    _description = 'Reviewed plain text document content and store policy version'
    _order = 'id desc'

    name = fields.Char(required=True)
    kind = fields.Char(required=True)
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    version = fields.Char(required=True)
    body = fields.Text(required=True)
    applicability = fields.Char(required=True)
    synthetic = fields.Boolean(required=True, default=True)
    paper = fields.Selection([('a4', 'A4'), ('80mm', '80 mm demonstration')], required=True, default='a4')
    allow_excerpt = fields.Boolean(default=False)
    approval_reference = fields.Char()
    reviewed_by_id = fields.Many2one('res.users', ondelete='restrict')
    reviewed_at = fields.Datetime()
    published_by_id = fields.Many2one('res.users', ondelete='restrict')
    published_at = fields.Datetime()
    state = fields.Selection([('draft', 'Draft / unreviewed'), ('reviewed', 'Reviewed'), ('published', 'Published')], required=True, default='draft')

    _version_once = models.Constraint('UNIQUE(kind, store_id, version)', 'A store template version is unique.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_document_template_mutation') is not _TEMPLATE_MUTATION:
            raise AccessError(self.env._('access_denied: Use the controlled template review service.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_document_template_mutation') is not _TEMPLATE_MUTATION:
            raise AccessError(self.env._('access_denied: Use the controlled template review service.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Template versions cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_document_template_mutation=_TEMPLATE_MUTATION).create(vals)

    def _save(self, vals):
        return self.with_context(ydental_document_template_mutation=_TEMPLATE_MUTATION).write(vals)
