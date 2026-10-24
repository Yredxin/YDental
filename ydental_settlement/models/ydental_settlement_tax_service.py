import hashlib
import re

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalSettlementTaxService(models.AbstractModel):
    _inherit = 'ydental.settlement.service'

    def _tax_original_upload(self, invoice_id, filename, raw, request_key, material_reference,
                             synthetic=True, previous_id=None):
        store = self._access(write=True)
        invoice, _links, patient, _store = self._original_invoice(invoice_id)
        if (not isinstance(raw, bytes) or not raw or len(raw) > 10000000
                or not isinstance(request_key, str) or not 16 <= len(request_key) <= 128
                or type(synthetic) is not bool):
            raise ValidationError(self.env._('invalid_source: Supply an original file and a stable upload key.'))
        filename = self._text(filename, 150)
        material_reference = self._text(material_reference, 240)
        if '/' in filename or '\\' in filename or re.search(r'[\x00-\x1f\x7f]', filename):
            raise ValidationError(self.env._('invalid_source: Use a plain original filename.'))
        if raw.startswith(b'%PDF-'):
            mimetype = 'application/pdf'
        elif raw.startswith(b'\x89PNG\r\n\x1a\n'):
            mimetype = 'image/png'
        elif raw.startswith(b'\xff\xd8\xff'):
            mimetype = 'image/jpeg'
        else:
            raise ValidationError(self.env._('invalid_source: Only original PDF, PNG or JPEG material is accepted.'))
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [32022, invoice.id])
        Originals = self.env['ydental.settlement.tax.original'].sudo()
        sha256 = hashlib.sha256(raw).hexdigest()
        prior = Originals.search([('actor_id', '=', self.env.uid), ('request_key', '=', request_key)], limit=1)
        if prior:
            if (prior.invoice_id.id, prior.sha256, prior.synthetic, prior.material_reference, prior.previous_id.id) != (
                    invoice.id, sha256, synthetic, material_reference, previous_id or False):
                raise UserError(self.env._('version_conflict: This upload key already identifies different material.'))
            self._tax_original_bytes(prior.id)
            return {'original_id': prior.id, 'sha256': prior.sha256, 'duplicate': True}
        if previous_id:
            previous = Originals.browse(self._positive_id(previous_id)).exists()
            if not previous or previous.invoice_id != invoice:
                raise AccessError(self.env._('access_denied: A correction must reference this bill original.'))
        row = Originals._new({'invoice_id': invoice.id, 'store_id': store.id,
            'company_id': store.company_id.id, 'patient_id': patient.id, 'actor_id': self.env.uid,
            'recorded_at': fields.Datetime.now(), 'filename': filename, 'mimetype': mimetype,
            'synthetic': synthetic, 'material_reference': material_reference, 'request_key': request_key,
            'previous_id': previous_id, 'sha256': sha256})
        attachment = self.env['ir.attachment'].sudo().create({'name': filename, 'raw': raw,
            'type': 'binary', 'mimetype': mimetype, 'res_model': row._name, 'res_id': row.id,
            'company_id': store.company_id.id, 'public': False, 'access_token': False})
        row._attach_once(attachment)
        self._audit('external_original_upload', invoice, store, after={'original_id': row.id,
            'sha256': sha256, 'synthetic_non_tax_example': synthetic, 'tax_issuance': 'not_performed'})
        return {'original_id': row.id, 'sha256': sha256, 'duplicate': False}

    def _tax_original_bytes(self, original_id, operation='download'):
        if operation not in ('view', 'download', 'print_request'):
            raise ValidationError(self.env._('invalid_action: Select an original file operation.'))
        store = self._access()
        row = self.env['ydental.settlement.tax.original'].sudo().browse(self._positive_id(original_id)).exists()
        if not row:
            raise AccessError(self.env._('access_denied: This external original is unavailable.'))
        invoice, _links, patient, _store = self._original_invoice(row.invoice_id.id)
        if (row.store_id != store or row.company_id != store.company_id
                or row.patient_id.id not in self._patient_family_ids(patient)):
            raise AccessError(self.env._('access_denied: This external original is outside the source scope.'))
        attachment = row.attachment_id
        if (not attachment or attachment.res_model != row._name or attachment.res_id != row.id
                or attachment.company_id != store.company_id or attachment.public or attachment.access_token):
            raise UserError(self.env._('original_missing: The uploaded original is unavailable.'))
        raw = attachment.raw.content
        if not raw or hashlib.sha256(raw).hexdigest() != row.sha256:
            raise UserError(self.env._('original_corrupt: The uploaded original checksum does not match.'))
        self._audit('external_original_' + operation, invoice, store, after={'original_id': row.id,
            'sha256': row.sha256, 'synthetic_non_tax_example': row.synthetic, 'paper_output': 'unknown'})
        return raw, row

    def _tax_original_rows(self):
        store = self._access()
        rows = self.env['ydental.settlement.tax.original'].sudo().search([
            ('store_id', '=', store.id), ('company_id', '=', store.company_id.id)], limit=100)
        return [{'id': row.id, 'invoice_id': row.invoice_id.id, 'filename': row.filename,
            'sha256': row.sha256, 'synthetic': row.synthetic, 'reference': row.material_reference,
            'previous_id': row.previous_id.id} for row in rows]
