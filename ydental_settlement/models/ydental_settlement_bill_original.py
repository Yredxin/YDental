from odoo import api, fields, models
from odoo.exceptions import AccessError

_ORIGINAL_INIT = object()


class YDentalSettlementBillOriginal(models.Model):
    _name = 'ydental.settlement.bill.original'
    _description = 'Immutable internal bill file original'
    _order = 'id desc'

    invoice_id = fields.Many2one('account.move', required=True, ondelete='restrict', index=True)
    patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    generated_at = fields.Datetime(required=True)
    request_key = fields.Char(required=True)
    version = fields.Integer(required=True)
    previous_id = fields.Many2one('ydental.settlement.bill.original', ondelete='restrict')
    source_facts = fields.Json(required=True)
    source_sha256 = fields.Char(required=True)
    template_xmlid = fields.Char(required=True)
    template_sha256 = fields.Char(required=True)
    pdf_sha256 = fields.Char(required=True)
    attachment_id = fields.Many2one('ir.attachment', ondelete='restrict', copy=False)

    _version_once = models.Constraint('UNIQUE(invoice_id, version)', 'An internal bill version is unique.')
    _key_once = models.Constraint('UNIQUE(actor_id, request_key)', 'An original request key is unique for its actor.')
    _positive_version = models.Constraint('CHECK(version > 0)', 'An original requires a positive version.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_bill_original_init') is not _ORIGINAL_INIT:
            raise AccessError(self.env._('access_denied: Use the controlled bill original service.'))
        return super().create(vals_list)

    def write(self, vals):
        if (self.env.context.get('ydental_bill_original_init') is not _ORIGINAL_INIT
                or set(vals) != {'attachment_id'} or any(self.mapped('attachment_id'))):
            raise AccessError(self.env._('history_immutable: Bill originals cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Bill originals cannot be deleted.'))

    @api.model
    def _create_original(self, vals):
        # No ordinary model ACL. Only the already source-authorized service calls this initializer.
        return self.sudo().with_context(ydental_bill_original_init=_ORIGINAL_INIT).create(vals)

    def _attach_once(self, attachment):
        return self.with_context(ydental_bill_original_init=_ORIGINAL_INIT).write({'attachment_id': attachment.id})
