import hashlib
import re

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang


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

    def _tax_original_rows(self, invoice_id=None):
        store = self._access()
        domain = fields.Domain('store_id', '=', store.id) & fields.Domain('company_id', '=', store.company_id.id)
        if invoice_id is not None:
            invoice, _links, _patient, _store = self._original_invoice(invoice_id)
            domain &= fields.Domain('invoice_id', '=', invoice.id)
        rows = self.env['ydental.settlement.tax.original'].sudo().search(domain, order='recorded_at desc, id desc')
        result = []
        for row in rows:
            try:
                invoice, _links, patient, _store = self._original_invoice(row.invoice_id.id)
            except (AccessError, UserError):
                continue
            if row.patient_id.id not in self._patient_family_ids(patient):
                continue
            result.append({'id': row.id, 'invoice_id': invoice.id, 'filename': row.filename,
                'invoice_number': invoice.name, 'patient_label': '%s / %s' % (patient.name, patient.ydental_number),
                'recorded_at': str(row.recorded_at), 'sha256': row.sha256, 'synthetic': row.synthetic,
                'reference': row.material_reference, 'previous_id': row.previous_id.id,
                'previous_filename': row.previous_id.filename or ''})
            if len(result) > 5000:
                if invoice_id is not None:
                    raise UserError(self.env._('size_limit: This bill exceeds the 5000-original selector capacity.'))
                raise UserError(self.env._('size_limit: Select a bill before listing this many external originals.'))
        return result

    def _tax_original_workbench(self, term='', bills_page=1, originals_page=1, invoice_id=None):
        store = self._access()
        if (not isinstance(term, str) or len(term) > 100 or type(bills_page) is not int or bills_page < 1
                or type(originals_page) is not int or originals_page < 1):
            raise ValidationError(self.env._('invalid_search: Use a patient name, business number or bill number and a valid page.'))
        term = term.strip()

        def summary(invoice, patient):
            currency = invoice.currency_id
            return {'id': invoice.id, 'number': invoice.name, 'date': str(invoice.invoice_date),
                'patient_label': '%s / %s' % (patient.name, patient.ydental_number),
                'amount': '%s %s' % (currency.name, formatLang(self.env, invoice.amount_total, digits=currency.decimal_places))}

        selected = None
        if invoice_id is not None:
            invoice, _links, patient, _store = self._original_invoice(invoice_id)
            selected = summary(invoice, patient)
        sources = self._model('source').search([('ydental_store_id', '=', store.id)])
        invoices = sources.ydental_invoice_id.sorted(lambda row: (row.invoice_date or fields.Date.today(), row.id), reverse=True)
        choices = []
        for invoice in invoices:
            try:
                invoice, _links, patient, _store = self._original_invoice(invoice.id)
            except (AccessError, UserError):
                continue
            if term and not any(term.casefold() in (value or '').casefold()
                    for value in (patient.name, patient.ydental_number, invoice.name)):
                continue
            choices.append(summary(invoice, patient))
            if len(choices) > 5000:
                raise UserError(self.env._('size_limit: Narrow the patient or bill search before selecting an internal bill.'))

        def paginate(rows, page):
            total = len(rows)
            page_count = max(1, (total + 19) // 20)
            page = min(page, page_count)
            return rows[(page - 1) * 20:page * 20], {'page': page, 'pages': page_count, 'total': total,
                'previous': page - 1 if page > 1 else None, 'next': page + 1 if page < page_count else None}

        invoice_rows, invoice_pagination = paginate(choices, bills_page)
        originals = self._tax_original_rows(invoice_id)
        original_rows, original_pagination = paginate(originals, originals_page)
        access = self.env['ydental.access.service']
        member = access._membership(self.env.uid, store.id)
        return {'store': store, 'invoices': invoice_rows, 'invoice_pagination': invoice_pagination,
            'rows': original_rows, 'original_pagination': original_pagination,
            'selected_invoice': selected, 'previous_options': originals if selected else [],
            'can_write': access._levels(member)['settlement'] == 'write', 'search_term': term}
