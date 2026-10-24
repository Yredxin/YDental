from odoo import api, fields, models
from odoo.exceptions import AccessError


_SELECTION_INIT = object()


class YDentalDocumentSelection(models.Model):
    _name = 'ydental.document.selection'
    _description = 'Explicit immutable clinical source collection for one PDF scope'
    _order = 'id desc'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_version = fields.Integer(required=True, default=1)
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    selected_at = fields.Datetime(required=True)
    documents = fields.Json(required=True)
    mode = fields.Selection([('draft', 'Incomplete source collection'), ('complete', 'All selected sources confirmed'),
        ('excerpt', 'Policy-approved confirmed excerpt')], required=True)
    template_id = fields.Many2one('ydental.document.template', ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_document_selection_init') is not _SELECTION_INIT:
            raise AccessError(self.env._('access_denied: Select clinical sources through the document service.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('history_immutable: Create a new explicit source selection.'))

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Clinical source selections cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_document_selection_init=_SELECTION_INIT).create(vals)
