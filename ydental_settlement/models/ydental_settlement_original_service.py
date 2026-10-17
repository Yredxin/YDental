import hashlib
import json

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalSettlementOriginalService(models.AbstractModel):
    _inherit = 'ydental.settlement.service'

    def _original_invoice(self, invoice_id):
        store = self._access()
        self.env['ydental.access.service']._check('export', 'write')
        invoice, sources = self._invoice(invoice_id, store)
        patient = self._patient(sources[0].ydental_patient_id.id)
        family = set(self._patient_family_ids(patient))
        if invoice.partner_id.ydental_patient_owner_id.id not in family:
            raise AccessError(self.env._('access_denied: The invoice patient source is inconsistent.'))
        for source in sources:
            fee = self._fee(source.ydental_fee_id.id, store)
            event = fee.ydental_event_id
            if (source.ydental_patient_id.id not in family or fee.ydental_patient_id.id not in family
                    or event.ydental_patient_id.id not in family or event.ydental_store_id != store
                    or source.ydental_currency_id != invoice.currency_id
                    or fee.ydental_currency_id != invoice.currency_id):
                raise AccessError(self.env._('access_denied: Every original source must match this store and patient.'))
        return invoice, sources, patient, store

    def _original_values(self, records, names):
        result = []
        for record in records.sorted('id'):
            row = {'id': record.id}
            for name in names:
                field = record._fields[name]
                value = record[name]
                if field.type == 'many2one':
                    value = value.id
                elif field.type in ('many2many', 'one2many'):
                    value = sorted(value.ids)
                elif field.type in ('date', 'datetime'):
                    value = str(value) if value else False
                row[name] = value
            result.append(row)
        return result

    def _original_facts(self, invoice, sources):
        fees = sources.ydental_fee_id
        snapshots = fees.ydental_price_snapshot_id
        return {'invoice': self._original_values(invoice, ['company_id', 'partner_id', 'currency_id', 'state',
                    'move_type', 'invoice_date', 'amount_total', 'amount_residual', 'payment_state']),
                'sources': self._original_values(sources, ['ydental_store_id', 'ydental_patient_id', 'ydental_fee_id',
                    'ydental_invoice_id', 'ydental_line_id', 'ydental_original_amount', 'ydental_discount',
                    'ydental_currency_id', 'ydental_price_version']),
                'fees': self._original_values(fees, ['ydental_event_id', 'ydental_store_id', 'ydental_patient_id',
                    'ydental_price_snapshot_id', 'ydental_price_review_id', 'ydental_quantity', 'ydental_unit_price',
                    'ydental_amount', 'ydental_currency_id']),
                'snapshots': self._original_values(snapshots, ['ydental_price_id', 'ydental_catalog_id', 'ydental_quantity',
                    'ydental_quantity_digits', 'ydental_currency_rounding', 'ydental_uom_id', 'ydental_currency_id',
                    'ydental_unit_price', 'ydental_amount', 'ydental_quoted_at']),
                'lines': self._original_values(invoice.line_ids, ['account_id', 'partner_id', 'currency_id',
                    'debit', 'credit', 'balance', 'amount_currency', 'amount_residual', 'amount_residual_currency']),
                'partials': self._original_values(self.env['account.partial.reconcile'].sudo().search(fields.Domain('debit_move_id', 'in', invoice.line_ids.ids) | fields.Domain('credit_move_id', 'in', invoice.line_ids.ids)),
                    ['debit_move_id', 'credit_move_id', 'amount', 'debit_amount_currency', 'credit_amount_currency'])}

    def _original_digest(self, value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

    def _original_template(self):
        # Fixed module report only, never a caller-selected template/model.
        return self._original_digest(self.env.ref('ydental_settlement.ydental_settlement_pdf').sudo().with_context(lang='zh_CN').arch_db)

    def _store_bill_original(self, invoice_id, request_key, previous_id=None):
        if not isinstance(request_key, str) or not 16 <= len(request_key) <= 128:
            raise ValidationError(self.env._('invalid_key: Supply a stable original request key.'))
        invoice, sources, patient, store = self._original_invoice(invoice_id)
        # Serialize only this invoice original version; no accounting update is used as a lock.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [32021, invoice.id])
        originals = self._model('bill.original')
        prior = originals.search([('actor_id', '=', self.env.uid), ('request_key', '=', request_key)], limit=1)
        if prior:
            if prior.invoice_id != invoice or prior.previous_id.id != (previous_id or False):
                raise UserError(self.env._('version_conflict: This original key belongs to another source or version.'))
            return {'original_id': prior.id, 'version': prior.version, 'sha256': prior.pdf_sha256, 'duplicate': True}
        latest = originals.search([('invoice_id', '=', invoice.id)], order='version desc', limit=1)
        if (latest and previous_id != latest.id) or (not latest and previous_id):
            raise UserError(self.env._('version_conflict: Select the latest original as the previous version.'))
        before = self._original_facts(invoice, sources)
        template = self._original_template()
        raw, digest = self._pdf('bill', invoice.id)
        self.env.flush_all()
        invoice_after, sources_after, _patient, _store = self._original_invoice(invoice.id)
        if (self._original_digest(before) != self._original_digest(self._original_facts(invoice_after, sources_after))
                or template != self._original_template()):
            raise UserError(self.env._('version_conflict: The bill source changed during original generation.'))
        original = originals._create_original({'invoice_id': invoice.id, 'patient_id': sources[0].ydental_patient_id.id,
            'store_id': store.id, 'company_id': store.company_id.id, 'currency_id': invoice.currency_id.id,
            'actor_id': self.env.uid, 'generated_at': fields.Datetime.now(), 'request_key': request_key,
            'version': latest.version + 1 if latest else 1, 'previous_id': latest.id,
            'source_facts': before, 'source_sha256': self._original_digest(before),
            'template_xmlid': 'ydental_settlement.ydental_settlement_pdf', 'template_sha256': template, 'pdf_sha256': digest})
        # Narrow privileged creation: fixed linked source, server-rendered bytes, private and no bearer token.
        attachment = self.env['ir.attachment'].sudo().create({'name': 'internal-bill-original-%s-v%s.pdf' % (invoice.id, original.version),
            'type': 'binary', 'raw': raw, 'mimetype': 'application/pdf', 'res_model': original._name,
            'res_id': original.id, 'company_id': store.company_id.id, 'public': False, 'access_token': False})
        original._attach_once(attachment)
        self._audit('bill_original_store', invoice, store, after={'original_id': original.id, 'version': original.version, 'pdf_sha256': digest})
        return {'original_id': original.id, 'version': original.version, 'sha256': digest, 'duplicate': False}

    def _bill_original_bytes(self, original_id):
        self._access()
        self.env['ydental.access.service']._check('export', 'write')
        original = self._model('bill.original').browse(self._positive_id(original_id)).exists()
        if not original:
            raise UserError(self.env._('original_missing: This internal bill original does not exist.'))
        invoice, _sources, patient, store = self._original_invoice(original.invoice_id.id)
        if (original.store_id != store or original.company_id != store.company_id
                or original.patient_id.id not in self._patient_family_ids(patient)):
            raise AccessError(self.env._('access_denied: This original is outside the current source scope.'))
        attachment = original.attachment_id
        if (not attachment or attachment.res_model != original._name or attachment.res_id != original.id
                or attachment.company_id != store.company_id or attachment.public or attachment.access_token):
            raise UserError(self.env._('original_missing: The stored original file is unavailable.'))
        raw = attachment.raw.content
        if not raw or hashlib.sha256(raw).hexdigest() != original.pdf_sha256:
            raise UserError(self.env._('original_corrupt: The stored bytes do not match the original checksum.'))
        self._audit('bill_original_download', invoice, store, after={'original_id': original.id, 'version': original.version, 'pdf_sha256': original.pdf_sha256})
        return raw, original.pdf_sha256

    def _workbench(self, patient_id=None, pages=None):
        values = super()._workbench(patient_id, pages)
        rows = {}
        if self.env['ydental.access.service']._levels(self.env['ydental.access.service']._membership(self.env.uid, values['store'].id))['export'] == 'write':
            invoices = values['settled'] | values['invoices']
            for original in self._model('bill.original').search([('invoice_id', 'in', invoices.ids),
                    ('store_id', '=', values['store'].id), ('company_id', '=', values['store'].company_id.id)], order='version desc'):
                rows.setdefault(original.invoice_id.id, []).append({'id': original.id, 'version': original.version})
        values['bill_originals'] = rows
        return values
