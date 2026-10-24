from odoo import models
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.ydental_print.models.ydental_print_service import digest, normalized


FINANCIAL_KINDS = ('bill', 'receipt', 'refund')


class YDentalPrintService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_authorize(self, kind, source_id, version, purpose=None):
        if kind not in FINANCIAL_KINDS:
            return super()._original_authorize(kind, source_id, version, purpose)
        if purpose or type(version) is not int or version != 0:
            raise ValidationError(self.env._('invalid_source: Financial files use their native source facts.'))
        finance = self.env['ydental.settlement.service']
        store = finance._access()
        if kind == 'bill':
            source, _links, _patient, _store = finance._original_invoice(source_id)
        elif kind == 'receipt':
            source = finance._payment_record(source_id, store)
            for invoice in source.ydental_invoice_ids:
                finance._original_invoice(invoice.id)
        else:
            source = finance._refund(source_id, store)
            finance._payment_record(source.ydental_payment_id.id, store)
        return self, source, False, 'settlement'

    def _original_patient(self, source, kind):
        if kind == 'bill':
            return self.env['ydental.settlement.service']._original_invoice(source.id)[2]
        if kind == 'refund':
            return source.ydental_payment_id.ydental_patient_id
        return super()._original_patient(source, kind)

    def _original_source(self, kind, source_id, version, purpose=None):
        if kind not in FINANCIAL_KINDS:
            return super()._original_source(kind, source_id, version, purpose)
        service, source, _selected, category = self._original_authorize(kind, source_id, version, purpose)
        finance = self.env['ydental.settlement.service']
        _target, facts = finance._report_payload(kind, source_id, require_export=False)
        patient = finance._patient(self._original_patient(source, kind).id)
        store = finance._access()
        currency = store.company_id.currency_id
        title = {'bill': self.env._('Internal bill - not a tax invoice'),
                 'receipt': self.env._('Offline collection receipt - not revenue or a tax invoice'),
                 'refund': self.env._('Offline refund voucher - approval is not execution')}[kind]
        details = []
        sections = []
        versions = {'source_model': source._name, 'source_id': source.id,
                    'source_write_date': str(source.write_date), 'native_facts': facts}
        if kind == 'bill':
            _invoice, links = finance._invoice(source_id, store)
            for link in links:
                summary = finance._bill_summary_line(link)
                sections.append({'label': self.env._('Confirmed source %s', link.id),
                    'paragraphs': [str(summary['name']),
                        self.env._('Frozen amount: %(amount)s %(currency)s; price source: %(version)s',
                            amount=link.ydental_original_amount, currency=currency.name,
                            version=link.ydental_price_version)]})
            versions['accounting'] = finance._original_facts(source, links)
        else:
            payment = source if kind == 'receipt' else source.ydental_payment_id
            refunds = finance._model('refund').search([('ydental_payment_id', '=', payment.id)], order='id')
            approved = refunds.filtered(lambda row: row.ydental_state in ('approved', 'failed', 'unknown'))
            requested = refunds.filtered(lambda row: row.ydental_state == 'requested')
            facts['approved_in_transit'] = currency.round(sum(approved.mapped('ydental_amount')))
            facts['requested_not_approved'] = currency.round(sum(requested.mapped('ydental_amount')))
            versions['refunds'] = finance._original_values(refunds, ['ydental_state', 'ydental_amount',
                'ydental_approver_id', 'ydental_executor_id', 'ydental_actual_at',
                'ydental_refund_business_date', 'ydental_native_payment_id', 'ydental_credit_note_ids'])
            allocations = self.env['account.partial.reconcile'].sudo().search([
                ('credit_move_id', 'in', payment.ydental_payment_id.move_id.line_ids.ids),
                ('debit_move_id.move_id', 'in', payment.ydental_invoice_ids.ids)], order='id')
            allocation_rows = []
            for invoice in payment.ydental_invoice_ids.sorted(lambda row: (row.invoice_date, row.id)):
                _native, links, _patient, _store = finance._original_invoice(invoice.id)
                amount = currency.round(sum(allocations.filtered(
                    lambda row: row.debit_move_id.move_id == invoice).mapped('amount')))
                allocation_rows.append({'invoice_id': invoice.id, 'number': invoice.name,
                    'invoice_date': str(invoice.invoice_date), 'allocated': amount,
                    'total': invoice.amount_total, 'residual': invoice.amount_residual,
                    'currency_id': invoice.currency_id.id, 'source_ids': links.ids})
                sections.append({'label': self.env._('Selected bill %s', invoice.name),
                    'paragraphs': [self.env._('Allocation: %(amount)s %(currency)s; current balance at generation: %(balance)s',
                        amount=amount, currency=currency.name, balance=invoice.amount_residual)]})
            versions['allocations'] = allocation_rows
            versions['partial_reconciles'] = finance._original_values(allocations,
                ['debit_move_id', 'credit_move_id', 'amount', 'debit_amount_currency', 'credit_amount_currency'])
            details += [self._pair(self.env._('Approved refund awaiting actual execution'), facts['approved_in_transit']),
                self._pair(self.env._('Requested refund, not approved'), facts['requested_not_approved']),
                self._pair(self.env._('Original collection operator'), payment.ydental_cashier_id.name),
                self._pair(self.env._('Native payment ID'), payment.ydental_payment_id.id)]
        for name in ('number', 'business_date', 'actual_utc', 'recorded_utc', 'total', 'received',
                     'residual', 'refunded', 'net', 'state', 'requested', 'refund_business_date',
                     'refund_channel', 'native_payment', 'reason'):
            if name in facts:
                details.append(self._pair(name, facts[name]))
        payload = {'kind': kind, 'title': title, 'template': 'S12-FINANCIAL-1',
            'source_id': source.id, 'version': version,
            'identity': [self._pair(self.env._('Patient'), patient.name),
                self._pair(self.env._('Patient number'), patient.ydental_number),
                self._pair(self.env._('Source patient ID'), self._original_patient(source, kind).id),
                self._pair(self.env._('Canonical patient ID'), patient.id),
                self._pair(self.env._('Store'), store.name),
                self._pair(self.env._('Company'), store.company_id.name),
                self._pair(self.env._('Currency'), currency.name)],
            'details': details, 'sections': sections, 'teeth': [], 'lines': [], 'events': [],
            'status': self.env._('Synthetic offline business document; not a tax invoice'),
            'selected_state': self.env._('Amounts and allocations are frozen at generation. Current balances are shown separately in the business page.'),
            'versions': versions}
        return service, source, category, payload, digest(normalized(payload))

    def _original_choices(self):
        choices = []
        try:
            choices = super()._original_choices()
        except AccessError:
            pass
        finance = self.env['ydental.settlement.service']
        try:
            store = finance._access()
        except AccessError:
            return choices
        links = finance._model('source').search([('ydental_store_id', '=', store.id)], order='id desc', limit=200)
        sources = [('bill', self.env['account.move'].sudo().browse(links.ydental_invoice_id.ids)),
            ('receipt', finance._model('payment').search([('ydental_store_id', '=', store.id)], order='id desc', limit=100)),
            ('refund', finance._model('refund').search([('ydental_payment_id.ydental_store_id', '=', store.id)], order='id desc', limit=100))]
        for kind, records in sources:
            for source in records:
                try:
                    self._original_authorize(kind, source.id, 0)
                except AccessError:
                    continue
                choices.append({'kind': kind, 'id': source.id, 'version': 0,
                    'state': 'native', 'kind_label': kind, 'state_label': self.env._('Native confirmed source')})
        return choices
