from odoo import api, fields, models
from odoo.exceptions import AccessError


_INITIALIZE = object()


class YDentalSettlementTaxOriginal(models.Model):
    _name = 'ydental.settlement.tax.original'
    _description = 'Unmodified externally supplied tax document or explicit non-tax example'
    _order = 'id desc'

    invoice_id = fields.Many2one('account.move', required=True, ondelete='restrict', index=True)
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    recorded_at = fields.Datetime(required=True)
    filename = fields.Char(required=True)
    mimetype = fields.Char(required=True)
    synthetic = fields.Boolean(required=True, default=True)
    material_reference = fields.Char(required=True)
    request_key = fields.Char(required=True, groups=fields.NO_ACCESS)
    previous_id = fields.Many2one('ydental.settlement.tax.original', ondelete='restrict')
    sha256 = fields.Char(required=True)
    attachment_id = fields.Many2one('ir.attachment', ondelete='restrict', copy=False)

    _key_once = models.Constraint('UNIQUE(actor_id, request_key)', 'An external original key is unique per actor.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_tax_original_init') is not _INITIALIZE:
            raise AccessError(self.env._('access_denied: Use the source-authorized external original entry.'))
        return super().create(vals_list)

    def write(self, vals):
        if (self.env.context.get('ydental_tax_original_init') is not _INITIALIZE
                or set(vals) != {'attachment_id'} or any(self.mapped('attachment_id'))):
            raise AccessError(self.env._('history_immutable: Uploaded original files cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Uploaded original files cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_tax_original_init=_INITIALIZE).create(vals)

    def _attach_once(self, attachment):
        return self.with_context(ydental_tax_original_init=_INITIALIZE).write({'attachment_id': attachment.id})
