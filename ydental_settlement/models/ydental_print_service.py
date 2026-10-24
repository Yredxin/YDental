from odoo import models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.misc import formatLang

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
        def money(value):
            return '%s %s' % (currency.name, formatLang(self.env, value, digits=currency.decimal_places))

        title = {'bill': self.env._('Internal bill - not a tax invoice'),
                 'receipt': self.env._('Offline collection receipt - not revenue or a tax invoice'),
                 'refund': self.env._('Offline refund voucher - approval is not execution')}[kind]
        details = []
        sections = []
        financial = {'number': facts['number'], 'currency': currency.name, 'rows': [],
            'totals': [], 'times': [], 'state': '', 'reason': ''}
        if 'business_date' in facts:
            financial['times'].append(self._pair(self.env._('Original bill or collection business date'), facts['business_date']))
        versions = {'source_model': source._name, 'source_id': source.id,
                    'source_write_date': str(source.write_date), 'native_facts': facts}
        if kind == 'bill':
            _invoice, links = finance._invoice(source_id, store)
            for link in links:
                summary = finance._bill_summary_line(link)
                financial['rows'].append({'number': str(summary['name']),
                    'price_version': link.ydental_price_version,
                    'amount': money(link.ydental_original_amount)})
                sections.append({'label': self.env._('Confirmed source %s', link.id),
                    'paragraphs': [str(summary['name']),
                        self.env._('Frozen amount: %(amount)s %(currency)s; price source: %(version)s',
                            amount=link.ydental_original_amount, currency=currency.name,
                            version=link.ydental_price_version)]})
            versions['accounting'] = finance._original_facts(source, links)
            financial['totals'] = [self._pair(self.env._('Bill total'), money(facts['total'])),
                self._pair(self.env._('Explicit discount'), money(facts['discount'])),
                self._pair(self.env._('Actual collection allocated'), money(facts['received'])),
                self._pair(self.env._('Receivable at generation'), money(facts['residual']))]
            financial['state'] = self.env._('Posted internal bill; not a tax invoice')
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
                financial['rows'].append({'number': invoice.name,
                    'bill_total': money(invoice.amount_total), 'allocated': money(amount),
                    'residual': money(invoice.amount_residual)})
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
            financial['totals'] = [
                self._pair(self.env._('Actual collection'), money(payment.ydental_amount)),
                self._pair(self.env._('Actually refunded'), money(facts['refunded'])),
                self._pair(self.env._('Approved refund awaiting actual execution'), money(facts['approved_in_transit'])),
                self._pair(self.env._('Requested refund, not approved'), money(facts['requested_not_approved']))]
            if kind == 'receipt':
                financial['state'] = self.env._('Recorded offline collection; not revenue')
                financial['totals'] += [self._pair(self.env._('Net actual collection'), money(facts['net'])),
                    self._pair(self.env._('Selected bills receivable at generation'), money(facts['residual']))]
                financial['times'] += [self._pair(self.env._('Collection actually occurred at (UTC)'), facts['actual_utc']),
                    self._pair(self.env._('Collection entered at (UTC)'), facts['recorded_utc'])]
                financial['channel'] = dict(payment._fields['ydental_channel']._description_selection(self.env)).get(facts['channel'], facts['channel'])
            else:
                state_labels = {'requested': self.env._('Refund requested; not approved'),
                    'approved': self.env._('Approved; awaiting actual refund'),
                    'failed': self.env._('Refund execution failed; pending verification'),
                    'unknown': self.env._('Refund execution result unknown; pending verification'),
                    'done': self.env._('Actually refunded'), 'rejected': self.env._('Refund rejected'),
                    'cancelled': self.env._('Refund cancelled')}
                financial['state'] = state_labels[facts['state']]
                financial['reason'] = facts['reason']
                financial['totals'] += [self._pair(self.env._('Requested refund amount'), money(facts['requested']))]
                financial['times'] += [self._pair(self.env._('Refund request entered at (UTC)'), str(source.create_date)),
                    self._pair(self.env._('Refund actually occurred at (UTC)'), facts['actual_utc'] or self.env._('Not recorded')),
                    self._pair(self.env._('Actual refund business date'), facts['refund_business_date'] or self.env._('Not recorded'))]
                financial['channel'] = dict(source._fields['ydental_refund_channel']._description_selection(self.env)).get(
                    facts['refund_channel'], self.env._('Not recorded'))
        field_labels = {
            'number': self.env._('Native document number'), 'business_date': self.env._('Original bill or collection business date'),
            'actual_utc': self.env._('Actual occurrence (UTC)'), 'recorded_utc': self.env._('Entry time (UTC)'),
            'total': self.env._('Bill total'), 'received': self.env._('Actual collection'),
            'residual': self.env._('Receivable at generation'), 'refunded': self.env._('Actually refunded'),
            'net': self.env._('Net actual collection'), 'state': self.env._('Refund state'),
            'requested': self.env._('Requested refund amount'), 'refund_business_date': self.env._('Actual refund business date'),
            'refund_channel': self.env._('Actual refund channel'), 'native_payment': self.env._('Native refund payment number'),
            'reason': self.env._('Refund reason')}
        amount_fields = {'total', 'received', 'residual', 'refunded', 'net', 'requested'}
        for name in ('number', 'business_date', 'actual_utc', 'recorded_utc', 'total', 'received',
                     'residual', 'refunded', 'net', 'state', 'requested', 'refund_business_date',
                     'refund_channel', 'native_payment', 'reason'):
            if name in facts:
                value = money(facts[name]) if name in amount_fields else facts[name]
                if name == 'state':
                    value = financial['state']
                elif name == 'refund_channel':
                    value = financial.get('channel') or self.env._('Not recorded')
                details.append(self._pair(field_labels[name], value))
        payload = {'kind': kind, 'title': title, 'template': 'YD-S13-FINANCIAL-2',
            'source_id': source.id, 'version': version,
            'identity': [self._pair(self.env._('Patient'), patient.name),
                self._pair(self.env._('Patient number'), patient.ydental_number),
                self._pair(self.env._('Source patient ID'), self._original_patient(source, kind).id),
                self._pair(self.env._('Canonical patient ID'), patient.id),
                self._pair(self.env._('Store'), store.name),
                self._pair(self.env._('Company'), store.company_id.name),
                self._pair(self.env._('Currency'), currency.name)],
            'financial': financial, 'details': details, 'sections': sections, 'teeth': [], 'lines': [], 'events': [],
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
        links = finance._model('source').search(self._original_search_domain([
            ('ydental_store_id', '=', store.id)]), order='id desc', limit=200)
        sources = [('bill', self.env['account.move'].sudo().browse(links.ydental_invoice_id.ids)),
            ('receipt', finance._model('payment').search(self._original_search_domain([
                ('ydental_store_id', '=', store.id)]), order='id desc', limit=100)),
            ('refund', finance._model('refund').search(self._original_search_domain([
                ('ydental_payment_id.ydental_store_id', '=', store.id)], patient_field='ydental_payment_id.ydental_patient_id'), order='id desc', limit=100))]
        for kind, records in sources:
            for source in records:
                try:
                    self._original_authorize(kind, source.id, 0)
                except AccessError:
                    continue
                choices.append({'kind': kind, 'id': source.id, 'version': 0,
                    'state': 'native', 'kind_label': kind, 'state_label': self.env._('Native confirmed source')})
        return choices
