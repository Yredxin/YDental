import hashlib
import inspect
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from psycopg2.errors import UniqueViolation

from odoo import Command, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.pdf import PdfFileReader, PdfReadError
from odoo.addons.base.models.ir_qweb import QWebError
from odoo.addons.ydental_inventory.models.ydental_inventory_record import MUTATION as INVENTORY_MUTATION


CHANNELS = {'cash', 'wechat', 'alipay', 'card'}


@dataclass(frozen=True)
class SettlementPdfScope:
    actor_id: int
    session_id: int
    revision: int
    kind: str
    source_id: int
    digest: str


class YDentalSettlementService(models.AbstractModel):
    _name = 'ydental.settlement.service'
    _description = 'Bound offline settlement and native account reconciliation'

    def _model(self, name):
        # Only internal constants reach this helper; no model name comes from RPC.
        return self.env['ydental.settlement.' + name].sudo()

    def _access(self, write=False, finance=False):
        access = self.env['ydental.access.service']
        category = 'finance_approval' if finance else 'settlement'
        store = access._check(category, 'write' if write else 'read', write=write).ydental_store_id
        if store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: The store company is outside the account scope.'))
        return store

    def _config(self, store):
        config = self._model('config').search([('ydental_store_id', '=', store.id)], limit=1)
        if not config or config.ydental_policy != 'demo_confirmation' or config.company_id != store.company_id:
            raise UserError(self.env._('accounting_policy_missing: Configure an explicit synthetic store policy.'))
        company = store.company_id
        if (config.ydental_sales_journal_id.company_id != company or config.ydental_sales_journal_id.type != 'sale'
                or config.ydental_adjustment_journal_id.company_id != company
                or config.ydental_adjustment_journal_id.type != 'general'
                or company not in config.ydental_income_account_id.company_ids
                or config.ydental_income_account_id.account_type != 'income'):
            raise UserError(self.env._('accounting_policy_invalid: Sales journal and income account must match the store company.'))
        for channel in CHANNELS:
            journal = config['ydental_' + channel + '_journal_id']
            if journal.company_id != company or journal.type not in ('bank', 'cash'):
                raise UserError(self.env._('accounting_policy_invalid: Payment journal must match the store company.'))
            if not journal.inbound_payment_method_line_ids.filtered(
                    lambda line: line.payment_method_id.code == 'manual' and line.payment_account_id):
                raise UserError(self.env._('accounting_policy_invalid: A real manual outstanding account is required.'))
        return config

    def _journal(self, config, channel):
        if channel not in CHANNELS:
            raise ValidationError(self.env._('Select a supported offline payment category.'))
        return config['ydental_' + channel + '_journal_id']

    def _audit(self, action, target, store, after=None, reason=False):
        self.env['ydental.access.service']._audit('settlement.' + action, 'settlement', target,
            store.id, after=after, reason=reason, source='confirmed_offline_transaction')

    def _positive_id(self, value):
        if type(value) is not int or value <= 0:
            raise ValidationError(self.env._('Select a valid record identifier.'))
        return value

    def _money(self, value, currency, allow_zero=False):
        if type(value) not in (int, float) or not (-1e12 < value < 1e12):
            raise ValidationError(self.env._('Enter a finite money amount.'))
        amount = currency.round(value)
        if abs(amount - value) > 1e-7 or amount < 0 or not allow_zero and currency.is_zero(amount):
            raise ValidationError(self.env._('Enter a valid nonnegative currency amount.'))
        return amount

    def _text(self, value, maximum=300, required=True):
        if not isinstance(value, str) or len(value) > maximum or required and not value.strip():
            raise ValidationError(self.env._('Enter a valid reason or proof.'))
        return value.strip()

    def _instant(self, value):
        if not isinstance(value, str) or len(value) > 40:
            raise ValidationError(self.env._('Provide an actual UTC timestamp.'))
        try:
            instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError as error:
            raise ValidationError(self.env._('Provide an actual UTC timestamp.')) from error
        if instant.tzinfo is None or instant.utcoffset().total_seconds() != 0:
            raise ValidationError(self.env._('Provide an actual UTC timestamp.'))
        instant = instant.astimezone(timezone.utc)
        if instant > datetime.now(timezone.utc):
            raise ValidationError(self.env._('Actual offline funds cannot have a future timestamp.'))
        return instant

    def _local_date(self, store, instant):
        return instant.astimezone(ZoneInfo(store.ydental_timezone)).date()

    def _lock(self):
        # A single S10 transaction fence fixes lock order across fee, payment,
        # refund and close paths. Native accounting locks are taken afterwards.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [32010])

    def _operate(self, operation, payload, key):
        handlers = {
            'bill': self._bill, 'pay': self._pay, 'refund_request': self._refund_request,
            'refund_approve': self._refund_approve, 'refund_reject': self._refund_reject,
            'refund_execute': self._refund_execute, 'refund_uncertain': self._refund_uncertain,
            'refund_recover': self._refund_recover, 'refund_cancel': self._refund_cancel,
            'close': self._close,
            'unlock': self._unlock, 'reclassify': self._reclassify,
            'waive': self._waive, 'trade': self._trade,
        }
        if operation not in handlers or not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 120:
            raise ValidationError(self.env._('invalid_action: Supply a documented operation and key.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_action: Unexpected or missing parameters.')) from error
        store = self._access(write=True, finance=operation in ('refund_approve', 'refund_reject', 'unlock'))
        digest = hashlib.sha256(json.dumps([operation, store.id, payload], sort_keys=True,
                                           ensure_ascii=True).encode()).hexdigest()
        with self.env.cr.savepoint():
            self._lock()
            self._access(write=True, finance=operation in ('refund_approve', 'refund_reject', 'unlock'))
            receipt = self._model('receipt').search([
                ('ydental_store_id', '=', store.id), ('ydental_actor_id', '=', self.env.uid),
                ('ydental_key', '=', key)], limit=1)
            if receipt:
                if receipt.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: This request key belongs to another action.'))
                return dict(receipt.ydental_result, result='already_accepted')
            result = handlers[operation](**payload)
            self._model('receipt')._new({
                'ydental_store_id': store.id, 'ydental_actor_id': self.env.uid,
                'ydental_key': key, 'ydental_fingerprint': digest,
                'ydental_operation': operation, 'ydental_result': result,
            })
            return dict(result, result='accepted')

    def _fee(self, fee_id, store):
        fee = self.env['ydental.treatment.fee'].sudo().browse(self._positive_id(fee_id)).exists()
        if not fee or fee.ydental_store_id != store or fee.ydental_event_id.state != 'confirmed':
            raise AccessError(self.env._('access_denied: Select a confirmed fee in this store.'))
        if not fee.ydental_patient_id or not fee.ydental_price_snapshot_id and not fee.ydental_price_review_id:
            raise UserError(self.env._('fee_unverified: A confirmed price or historical review is required.'))
        if fee.ydental_currency_id != store.company_id.currency_id:
            raise UserError(self.env._('currency_unverified: Only the explicitly configured company currency is available.'))
        return fee

    def _patient(self, patient_id):
        return self.env['ydental.patient.service']._patient(self._positive_id(patient_id))

    def _same_patient(self, fee, patient):
        return self._patient(fee.ydental_patient_id.id) == patient

    def _bill(self, fee_ids, discount, reason):
        store = self._access(write=True)
        config = self._config(store)
        if not isinstance(fee_ids, list) or not fee_ids or any(type(x) is not int for x in fee_ids) or len(set(fee_ids)) != len(fee_ids):
            raise ValidationError(self.env._('Select distinct confirmed fee sources.'))
        fees = [self._fee(fee_id, store) for fee_id in fee_ids]
        patient = self._patient(fees[0].ydental_patient_id.id)
        if any(not self._same_patient(fee, patient) for fee in fees):
            raise AccessError(self.env._('access_denied: Mixed patient fees cannot be billed.'))
        prior = self._model('source').search([('ydental_fee_id', 'in', fee_ids)])
        if prior:
            if len(prior) == len(fees) and not discount and len(prior.ydental_invoice_id) == 1:
                return {'invoice_id': prior.ydental_invoice_id.id, 'amount': prior.ydental_invoice_id.amount_total}
            raise UserError(self.env._('fee_already_billed: Source fees cannot be billed twice.'))
        if any(fee.ydental_amount < 0 for fee in fees):
            if len(fees) != 1 or fees[0].ydental_amount >= 0 or discount:
                raise UserError(self.env._('correction_separate: Bill each confirmed reversal against its original source.'))
            self._close_guard_any(store, self.env.uid, fees[0].ydental_event_id.ydental_business_date)
            return self._bill_correction(fees[0], store, config)
        currency = store.company_id.currency_id
        original = currency.round(sum(fee.ydental_amount for fee in fees))
        discount = self._money(discount, currency, allow_zero=True)
        if discount > original or discount and not self._text(reason):
            raise ValidationError(self.env._('Discount requires a reason and cannot exceed the selected fees.'))
        date = max(fee.ydental_event_id.ydental_business_date for fee in fees)
        for fee in fees:
            self._close_guard_any(store, self.env.uid, fee.ydental_event_id.ydental_business_date)
        commands = [Command.create({
            'name': fee.name,
            'quantity': fee.ydental_quantity,
            'price_unit': fee.ydental_unit_price,
            'account_id': config.ydental_income_account_id.id,
            'tax_ids': [Command.clear()],
            'product_id': fee.ydental_product_id.id or False,
        }) for fee in fees]
        if discount:
            commands.append(Command.create({
                'name': self.env._('Explicit demonstration discount: %s', self._text(reason)),
                'quantity': 1, 'price_unit': -discount,
                'account_id': config.ydental_income_account_id.id,
                'tax_ids': [Command.clear()],
            }))
        invoice = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'out_invoice', 'company_id': store.company_id.id,
            'journal_id': config.ydental_sales_journal_id.id,
            'partner_id': patient.ydental_partner_id.id,
            'invoice_date': date, 'date': date,
            'currency_id': currency.id,
            'invoice_origin': 'YDental confirmed fee sources ' + ','.join(map(str, fee_ids)),
            'invoice_line_ids': commands,
        })
        invoice.action_post()
        if invoice.state != 'posted' or currency.compare_amounts(invoice.amount_total, original - discount):
            raise UserError(self.env._('accounting_mismatch: Native invoice differs from frozen fees.'))
        lines = invoice.invoice_line_ids.sorted('id')[:len(fees)]
        if len(lines) != len(fees):
            raise UserError(self.env._('accounting_mismatch: Native source lines are incomplete.'))
        for fee, line in zip(fees, lines):
            if currency.compare_amounts(line.price_subtotal, fee.ydental_amount):
                raise UserError(self.env._('accounting_mismatch: Native source line differs from its frozen fee.'))
            snapshot = fee.ydental_price_snapshot_id
            version = 'S05:' + str(snapshot.ydental_price_id.id) if snapshot else 'review:' + str(fee.ydental_price_review_id.id)
            try:
                with self.env.cr.savepoint():
                    self._model('source')._new({
                        'ydental_fee_id': fee.id, 'ydental_store_id': store.id,
                        'ydental_patient_id': fee.ydental_patient_id.id,
                        'ydental_invoice_id': invoice.id, 'ydental_line_id': line.id,
                        'ydental_original_amount': fee.ydental_amount, 'ydental_currency_id': currency.id,
                        'ydental_discount': discount if fee == fees[0] else 0,
                        'ydental_discount_reason': reason if discount and fee == fees[0] else False,
                        'ydental_source_business_date': fee.ydental_event_id.ydental_business_date,
                        'ydental_source_actual_at': fee.ydental_event_id.ydental_actual_at,
                        'ydental_price_version': version,
                    })
            except UniqueViolation as error:
                if error.diag.constraint_name != 'ydental_settlement_source_fee_once':
                    raise
                # A competing REPEATABLE READ transaction cannot see the winner's
                # new source. Abort this invoice instead of leaking a SQL error.
                raise UserError(self.env._('concurrent_bill: This fee was billed by another request. Refresh and review its invoice.')) from error
        self._audit('bill', invoice, store, after={'fee_ids': fee_ids, 'amount': invoice.amount_total,
                                                   'discount': discount}, reason=reason)
        return {'invoice_id': invoice.id, 'amount': invoice.amount_total, 'residual': invoice.amount_residual}

    def _bill_correction(self, fee, store, config):
        parent = fee.ydental_parent_id
        link = self._model('source').search([('ydental_fee_id', '=', parent.id)], limit=1) if parent else False
        if not link or link.ydental_store_id != store or link.ydental_invoice_id.move_type != 'out_invoice':
            raise UserError(self.env._('correction_source_missing: Bill the original confirmed fee first.'))
        original = link.ydental_invoice_id
        currency = store.company_id.currency_id
        amount = currency.round(-fee.ydental_amount)
        if amount <= 0 or currency.compare_amounts(amount, link.ydental_original_amount) > 0:
            raise UserError(self.env._('correction_amount_invalid: Reversal exceeds original source.'))
        date = fee.ydental_event_id.ydental_business_date
        credit = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'out_refund', 'company_id': store.company_id.id,
            'journal_id': config.ydental_sales_journal_id.id,
            'partner_id': original.partner_id.id,
            'invoice_date': date, 'date': date, 'currency_id': currency.id,
            'invoice_origin': original.name,
            'invoice_line_ids': [Command.create({
                'name': fee.name, 'quantity': abs(fee.ydental_quantity) or 1,
                'price_unit': fee.ydental_unit_price if fee.ydental_quantity else amount,
                'account_id': config.ydental_income_account_id.id,
                'tax_ids': [Command.clear()],
                'product_id': fee.ydental_product_id.id or False,
            })],
        })
        credit.action_post()
        if credit.state != 'posted' or currency.compare_amounts(credit.amount_total, amount):
            raise UserError(self.env._('accounting_mismatch: Native correction credit differs from fee.'))
        line = credit.invoice_line_ids[:1]
        snapshot = fee.ydental_price_snapshot_id
        self._model('source')._new({
            'ydental_fee_id': fee.id, 'ydental_store_id': store.id,
            'ydental_patient_id': fee.ydental_patient_id.id,
            'ydental_invoice_id': credit.id, 'ydental_line_id': line.id,
            'ydental_original_amount': fee.ydental_amount,
            'ydental_currency_id': currency.id,
            'ydental_source_business_date': date,
            'ydental_source_actual_at': fee.ydental_event_id.ydental_actual_at,
            'ydental_price_version': 'S05:' + str(snapshot.ydental_price_id.id)
                if snapshot else 'review:' + str(fee.ydental_price_review_id.id),
        })
        allocated = min(original.amount_residual, amount)
        if allocated > 0:
            self.env['account.partial.reconcile'].sudo().with_company(store.company_id).create({
                'debit_move_id': self._receivable(original, debit=True).id,
                'credit_move_id': self._receivable(credit, debit=False).id,
                'amount': allocated, 'debit_amount_currency': allocated,
                'credit_amount_currency': allocated,
            })
        self._audit('bill_correction', credit, store, after={'fee_id': fee.id,
            'original_invoice_id': original.id, 'credit_amount': amount,
            'unpaid_reduced': allocated})
        return {'credit_note_id': credit.id, 'amount': -amount,
                'unpaid_reduced': allocated, 'actually_refunded': 0}

    def _invoice(self, invoice_id, store):
        invoice = self.env['account.move'].sudo().browse(self._positive_id(invoice_id)).exists()
        sources = self._model('source').search([('ydental_invoice_id', '=', invoice.id)]) if invoice else False
        if not invoice or invoice.state != 'posted' or invoice.move_type != 'out_invoice' or not sources or (
                any(source.ydental_store_id != store for source in sources)
                or invoice.company_id != store.company_id):
            raise AccessError(self.env._('access_denied: Select a posted invoice from this store.'))
        return invoice, sources

    def _close_guard(self, store, cashier_id, business_date, channel):
        closed = self._model('close').search([
            ('ydental_store_id', '=', store.id), ('ydental_cashier_id', '=', cashier_id),
            ('ydental_business_date', '=', business_date), ('ydental_channel', '=', channel),
        ], order='ydental_cycle desc', limit=1)
        if closed and closed.ydental_state == 'confirmed':
            raise UserError(self.env._('day_closed: A finance approver must unlock this cashier day.'))

    def _close_guard_any(self, store, cashier_id, business_date):
        for channel in CHANNELS:
            self._close_guard(store, cashier_id, business_date, channel)

    def _receivable(self, move, debit):
        lines = move.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable'
                                        and line.balance > 0 if debit else
                                        line.account_id.account_type == 'asset_receivable' and line.balance < 0)
        if len(lines) != 1:
            raise UserError(self.env._('accounting_mismatch: Expected one native receivable line.'))
        return lines

    def _pay(self, invoice_ids, amount, channel, actual_utc, proof):
        store = self._access(write=True)
        config = self._config(store)
        if not isinstance(invoice_ids, list) or not invoice_ids or any(type(x) is not int for x in invoice_ids) or len(set(invoice_ids)) != len(invoice_ids):
            raise ValidationError(self.env._('Explicitly select distinct same-store invoices.'))
        invoices = [self._invoice(invoice_id, store)[0] for invoice_id in invoice_ids]
        sources = self._model('source').search([('ydental_invoice_id', 'in', invoice_ids)])
        patient = self._patient(sources[0].ydental_patient_id.id)
        if any(self._patient(source.ydental_patient_id.id) != patient for source in sources):
            raise AccessError(self.env._('access_denied: Mixed patient invoices cannot share a payment.'))
        currency = store.company_id.currency_id
        amount = self._money(amount, currency)
        if currency.compare_amounts(amount, sum(invoice.amount_residual for invoice in invoices)) > 0:
            raise UserError(self.env._('payment_exceeds_residual: Do not create an unallocated patient payment.'))
        actual = self._instant(actual_utc)
        business_date = self._local_date(store, actual)
        self._close_guard(store, self.env.uid, business_date, channel)
        journal = self._journal(config, channel)
        method = journal.inbound_payment_method_line_ids.filtered(lambda line: line.payment_method_id.code == 'manual')[:1]
        if not method:
            raise UserError(self.env._('accounting_policy_invalid: Native manual payment method is absent.'))
        payment = self.env['account.payment'].sudo().with_company(store.company_id).create({
            'payment_type': 'inbound', 'partner_type': 'customer',
            'company_id': store.company_id.id, 'partner_id': patient.ydental_partner_id.id,
            'journal_id': journal.id, 'payment_method_line_id': method.id,
            'amount': amount, 'currency_id': currency.id, 'date': business_date,
            'memo': self.env._('YDental confirmed offline %s', channel),
            'payment_reference': self._text(proof, 200),
        })
        payment.action_post()
        if payment.move_id.state != 'posted':
            raise UserError(self.env._('accounting_mismatch: Native offline payment did not post.'))
        credit = self._receivable(payment.move_id, debit=False)
        remaining = amount
        allocations = []
        for invoice in sorted(invoices, key=lambda move: (move.invoice_date or move.date, move.id)):
            if currency.is_zero(remaining):
                break
            allocated = min(remaining, invoice.amount_residual)
            if currency.is_zero(allocated):
                continue
            debit = self._receivable(invoice, debit=True)
            partial = self.env['account.partial.reconcile'].sudo().with_company(store.company_id).create({
                'debit_move_id': debit.id, 'credit_move_id': credit.id, 'amount': allocated,
                'debit_amount_currency': allocated, 'credit_amount_currency': allocated,
            })
            allocations.append({'invoice_id': invoice.id, 'partial_id': partial.id, 'amount': allocated})
            remaining = currency.round(remaining - allocated)
        if not currency.is_zero(remaining):
            raise UserError(self.env._('accounting_mismatch: Offline payment was not fully allocated.'))
        record = self._model('payment')._new({
            'ydental_store_id': store.id, 'ydental_patient_id': patient.id,
            'ydental_payment_id': payment.id, 'ydental_cashier_id': self.env.uid,
            'ydental_channel': channel, 'ydental_amount': amount, 'ydental_currency_id': currency.id,
            'ydental_actual_at': actual.replace(tzinfo=None),
            'ydental_entered_at': fields.Datetime.now(),
            'ydental_business_date': business_date, 'ydental_proof': proof,
            'ydental_key': str(payment.id),
            'ydental_invoice_ids': [Command.set(invoice_ids)],
        })
        self._audit('pay', record, store, after={'payment_id': payment.id, 'allocations': allocations,
                                                'amount': amount})
        return {'payment_id': record.id, 'native_payment_id': payment.id, 'amount': amount,
                'allocations': allocations, 'residuals': {str(invoice.id): invoice.amount_residual for invoice in invoices}}

    def _payment_record(self, payment_id, store):
        record = self._model('payment').browse(self._positive_id(payment_id)).exists()
        if not record or record.ydental_store_id != store or record.ydental_payment_id.move_id.state != 'posted':
            raise AccessError(self.env._('access_denied: Select a posted offline payment in this store.'))
        return record

    def _refund(self, refund_id, store):
        refund = self._model('refund').browse(self._positive_id(refund_id)).exists()
        if not refund or refund.ydental_payment_id.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Select a refund request in this store.'))
        return refund

    def _refund_capacity(self, payment):
        reserved = self._model('refund').search([
            ('ydental_payment_id', '=', payment.id),
            ('ydental_state', 'in', ('requested', 'approved', 'failed', 'unknown', 'done')),
        ])
        return payment.ydental_currency_id.round(payment.ydental_amount - sum(reserved.mapped('ydental_amount')))

    def _refund_request(self, payment_id, amount, reason, request_key):
        store = self._access(write=True)
        payment = self._payment_record(payment_id, store)
        amount = self._money(amount, payment.ydental_currency_id)
        if payment.ydental_currency_id.compare_amounts(amount, self._refund_capacity(payment)) > 0:
            raise UserError(self.env._('refund_exceeds_received: Actual and protected refunds exceed this offline receipt.'))
        self._close_guard(store, payment.ydental_cashier_id.id, payment.ydental_business_date,
                          self._effective_channel(payment))
        refund = self._model('refund')._new({
            'ydental_payment_id': payment.id, 'ydental_amount': amount,
            'ydental_currency_id': payment.ydental_currency_id.id,
            'ydental_requester_id': self.env.uid, 'ydental_reason': self._text(reason),
            'ydental_key': self._text(request_key, 120),
        })
        self._audit('refund.request', refund, store, after={'amount': amount}, reason=reason)
        return {'refund_id': refund.id, 'state': refund.ydental_state, 'actually_refunded': 0,
                'reserved': amount}

    def _refund_approve(self, refund_id, reason):
        store = self._access(write=True, finance=True)
        refund = self._refund(refund_id, store)
        if refund.ydental_state != 'requested' or refund.ydental_requester_id.id == self.env.uid:
            raise AccessError(self.env._('access_denied: A different finance approver must approve a pending request.'))
        if self._refund_capacity(refund.ydental_payment_id) < -0.000001:
            raise UserError(self.env._('refund_exceeds_received: Protected requests exceed actual receipt.'))
        refund._save({'ydental_state': 'approved', 'ydental_approver_id': self.env.uid,
                      'ydental_decision_reason': self._text(reason)})
        self._audit('refund.approve', refund, store, after={'state': 'approved', 'amount': refund.ydental_amount}, reason=reason)
        return {'refund_id': refund.id, 'state': 'approved', 'actually_refunded': 0,
                'reserved': refund.ydental_amount}

    def _refund_reject(self, refund_id, reason):
        store = self._access(write=True, finance=True)
        refund = self._refund(refund_id, store)
        if refund.ydental_state != 'requested' or refund.ydental_requester_id.id == self.env.uid:
            raise AccessError(self.env._('access_denied: A different finance approver must reject a pending request.'))
        refund._save({'ydental_state': 'rejected', 'ydental_approver_id': self.env.uid,
                      'ydental_decision_reason': self._text(reason)})
        self._audit('refund.reject', refund, store, after={'state': 'rejected'}, reason=reason)
        return {'refund_id': refund.id, 'state': 'rejected', 'credit_note_id': False,
                'actually_refunded': 0}

    def _refund_uncertain(self, refund_id, outcome, reason):
        store = self._access(write=True)
        refund = self._refund(refund_id, store)
        if refund.ydental_state != 'approved' or outcome not in ('failed', 'unknown'):
            raise UserError(self.env._('refund_state_invalid: Only an approved pending refund can be marked uncertain.'))
        refund._save({'ydental_state': outcome, 'ydental_decision_reason': self._text(reason)})
        self._audit('refund.' + outcome, refund, store, after={'state': outcome}, reason=reason)
        return {'refund_id': refund.id, 'state': outcome, 'actually_refunded': 0,
                'reserved': refund.ydental_amount}

    def _refund_recover(self, refund_id, verified_not_paid, reason):
        store = self._access(write=True, finance=True)
        refund = self._refund(refund_id, store)
        if refund.ydental_state not in ('failed', 'unknown') or verified_not_paid is not True:
            raise UserError(self.env._('refund_recovery_required: Verify the external offline transfer before re-arming.'))
        refund._save({'ydental_state': 'approved', 'ydental_decision_reason': self._text(reason)})
        self._audit('refund.recover', refund, store, after={'verified_not_paid': True}, reason=reason)
        return {'refund_id': refund.id, 'state': 'approved', 'actually_refunded': 0}

    def _refund_cancel(self, refund_id, verified_not_paid, evidence, reason):
        """Release protected capacity only after an explicit no-payment review."""
        store = self._access(write=True)
        refund = self._refund(refund_id, store)
        if refund.ydental_state not in ('requested', 'approved', 'failed', 'unknown'):
            raise UserError(self.env._('refund_state_invalid: Only an unexecuted refund may be cancelled.'))
        if refund.ydental_state != 'requested' or refund.ydental_requester_id.id != self.env.uid:
            self._access(write=True, finance=True)
            if refund.ydental_requester_id.id == self.env.uid:
                raise AccessError(self.env._('access_denied: A distinct finance reviewer must release this refund.'))
        if verified_not_paid is not True or refund.ydental_native_payment_id or refund.ydental_credit_note_ids:
            raise UserError(self.env._('refund_recovery_required: Verify no offline refund or native reversal occurred.'))
        payment = refund.ydental_payment_id
        self._close_guard(store, payment.ydental_cashier_id.id,
                          payment.ydental_business_date, self._effective_channel(payment))
        evidence = self._text(evidence, 200)
        reason = self._text(reason)
        refund._save({'ydental_state': 'cancelled', 'ydental_cancelled_by_id': self.env.uid,
                      'ydental_cancelled_at': fields.Datetime.now(),
                      'ydental_cancel_reason': reason, 'ydental_cancel_evidence': evidence,
                      'ydental_release_verified': True})
        available = self._refund_capacity(payment)
        self._audit('refund.cancel', refund, store,
            after={'state': 'cancelled', 'verified_not_paid': True,
                   'released': refund.ydental_amount, 'available': available}, reason=reason)
        return {'refund_id': refund.id, 'state': 'cancelled', 'actually_refunded': 0,
                'released': refund.ydental_amount, 'available': available}

    def _refund_execute(self, refund_id, actual_utc, proof):
        store = self._access(write=True)
        config = self._config(store)
        refund = self._refund(refund_id, store)
        if refund.ydental_state != 'approved' or not refund.ydental_approver_id or refund.ydental_requester_id == refund.ydental_approver_id:
            raise AccessError(self.env._('access_denied: Confirm a distinct approval before actual refund.'))
        payment = refund.ydental_payment_id
        actual = self._instant(actual_utc)
        business_date = self._local_date(store, actual)
        self._close_guard(store, self.env.uid, business_date, payment.ydental_channel)
        currency = payment.ydental_currency_id
        journal = self._journal(config, payment.ydental_channel)
        method = journal.outbound_payment_method_line_ids.filtered(lambda line: line.payment_method_id.code == 'manual')[:1]
        if not method:
            raise UserError(self.env._('accounting_policy_invalid: Native outbound manual method is absent.'))
        original = payment.ydental_payment_id
        partials = self.env['account.partial.reconcile'].sudo().search([
            ('credit_move_id', 'in', original.move_id.line_ids.ids),
            ('debit_move_id.move_id', 'in', payment.ydental_invoice_ids.ids),
        ], order='id')
        if currency.compare_amounts(sum(partials.mapped('amount')), refund.ydental_amount) < 0:
            raise UserError(self.env._('refund_exceeds_allocated: Native receipt allocations are insufficient.'))
        remaining = refund.ydental_amount
        credits = self.env['account.move'].sudo()
        for partial in partials.sorted(key=lambda part: (part.debit_move_id.move_id.invoice_date,
                                                         part.debit_move_id.move_id.id, part.id)):
            if currency.is_zero(remaining):
                break
            amount = min(remaining, partial.amount)
            invoice = partial.debit_move_id.move_id
            credit_note = self.env['account.move'].sudo().with_company(store.company_id).create({
                'move_type': 'out_refund', 'company_id': store.company_id.id,
                'journal_id': config.ydental_sales_journal_id.id,
                'partner_id': invoice.partner_id.id,
                'invoice_date': business_date, 'date': business_date,
                'currency_id': currency.id,
                'invoice_origin': invoice.name,
                'invoice_line_ids': [Command.create({
                    'name': self.env._('Actual offline refund of invoice %s', invoice.name),
                    'quantity': 1, 'price_unit': amount,
                    'account_id': config.ydental_income_account_id.id,
                    'tax_ids': [Command.clear()],
                })],
            })
            credit_note.action_post()
            if credit_note.state != 'posted' or currency.compare_amounts(credit_note.amount_total, amount):
                raise UserError(self.env._('accounting_mismatch: Native credit note did not post correctly.'))
            credits |= credit_note
            remaining = currency.round(remaining - amount)
        if not currency.is_zero(remaining):
            raise UserError(self.env._('accounting_mismatch: Refund credit notes are incomplete.'))
        outbound = self.env['account.payment'].sudo().with_company(store.company_id).create({
            'payment_type': 'outbound', 'partner_type': 'customer',
            'company_id': store.company_id.id, 'partner_id': original.partner_id.id,
            'journal_id': journal.id, 'payment_method_line_id': method.id,
            'amount': refund.ydental_amount, 'currency_id': currency.id, 'date': business_date,
            'memo': self.env._('YDental actually refunded offline'),
            'payment_reference': self._text(proof, 200),
        })
        outbound.action_post()
        if outbound.move_id.state != 'posted':
            raise UserError(self.env._('accounting_mismatch: Native refund payment did not post.'))
        debit = self._receivable(outbound.move_id, debit=True)
        for credit_note in credits:
            credit = self._receivable(credit_note, debit=False)
            amount = credit_note.amount_total
            self.env['account.partial.reconcile'].sudo().with_company(store.company_id).create({
                'debit_move_id': debit.id, 'credit_move_id': credit.id,
                'amount': amount, 'debit_amount_currency': amount, 'credit_amount_currency': amount,
            })
        refund._save({'ydental_state': 'done', 'ydental_executor_id': self.env.uid,
                      'ydental_native_payment_id': outbound.id,
                      'ydental_credit_note_id': credits[:1].id,
                      'ydental_credit_note_ids': [Command.set(credits.ids)],
                      'ydental_actual_at': actual.replace(tzinfo=None)})
        self._audit('refund.execute', refund, store, after={'native_payment_id': outbound.id,
            'credit_note_ids': credits.ids, 'amount': refund.ydental_amount})
        return {'refund_id': refund.id, 'state': 'done', 'actually_refunded': refund.ydental_amount,
                'native_payment_id': outbound.id, 'credit_note_ids': credits.ids}

    def _waive(self, invoice_id, amount, reason):
        store = self._access(write=True)
        config = self._config(store)
        invoice, _sources = self._invoice(invoice_id, store)
        self._close_guard_any(store, self.env.uid, fields.Date.context_today(self.with_context(tz=store.ydental_timezone)))
        currency = store.company_id.currency_id
        amount = self._money(amount, currency)
        if currency.compare_amounts(amount, invoice.amount_residual) > 0:
            raise UserError(self.env._('waiver_exceeds_residual: Only unpaid receivable can be waived.'))
        credit = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'out_refund', 'company_id': store.company_id.id,
            'journal_id': config.ydental_sales_journal_id.id,
            'partner_id': invoice.partner_id.id,
            'invoice_date': fields.Date.context_today(self), 'currency_id': currency.id,
            'invoice_origin': invoice.name,
            'invoice_line_ids': [Command.create({
                'name': self.env._('Unpaid receivable waiver: %s', self._text(reason)),
                'quantity': 1, 'price_unit': amount,
                'account_id': config.ydental_income_account_id.id,
                'tax_ids': [Command.clear()],
            })],
        })
        credit.action_post()
        self.env['account.partial.reconcile'].sudo().with_company(store.company_id).create({
            'debit_move_id': self._receivable(invoice, debit=True).id,
            'credit_move_id': self._receivable(credit, debit=False).id,
            'amount': amount, 'debit_amount_currency': amount, 'credit_amount_currency': amount,
        })
        self._audit('waive', credit, store, after={'invoice_id': invoice.id, 'amount': amount}, reason=reason)
        return {'credit_note_id': credit.id, 'invoice_residual': invoice.amount_residual,
                'actually_refunded': 0}

    def _effective_channel(self, payment):
        correction = self._model('correction').search([('ydental_payment_id', '=', payment.id)],
                                                     order='id desc', limit=1)
        return correction.ydental_new_channel if correction else payment.ydental_channel

    def _close(self, business_date, channel):
        store = self._access(write=True)
        self._config(store)
        if channel not in CHANNELS or not isinstance(business_date, str):
            raise ValidationError(self.env._('Select a business date and offline payment category.'))
        date = fields.Date.to_date(business_date)
        if not date or date > fields.Date.context_today(self):
            raise ValidationError(self.env._('Select a valid past or current business date.'))
        existing = self._model('close').search([
            ('ydental_store_id', '=', store.id), ('ydental_cashier_id', '=', self.env.uid),
            ('ydental_business_date', '=', date), ('ydental_channel', '=', channel),
        ], order='ydental_cycle desc', limit=1)
        if existing and existing.ydental_state == 'confirmed':
            raise UserError(self.env._('day_closed: Unlock before closing this cashier day again.'))
        payments = self._model('payment').search([
            ('ydental_store_id', '=', store.id), ('ydental_cashier_id', '=', self.env.uid),
            ('ydental_business_date', '=', date),
        ]).filtered(lambda payment: self._effective_channel(payment) == channel)
        refunds = self._model('refund').search([
            ('ydental_payment_id', 'in', payments.ids),
        ])
        currency = store.company_id.currency_id
        gross = currency.round(sum(payments.mapped('ydental_amount')))
        refunded = currency.round(sum(refunds.filtered(lambda refund: refund.ydental_state == 'done').mapped('ydental_amount')))
        pending = currency.round(sum(refunds.filtered(lambda refund: refund.ydental_state in
            ('requested', 'approved', 'failed', 'unknown')).mapped('ydental_amount')))
        for native in payments.ydental_payment_id.move_id | refunds.ydental_native_payment_id.move_id:
            if native.state != 'posted' or not currency.is_zero(sum(native.line_ids.mapped('balance'))):
                raise UserError(self.env._('accounting_mismatch: Native payment journal is not balanced.'))
        record = self._model('close')._new({
            'ydental_store_id': store.id, 'ydental_cashier_id': self.env.uid,
            'ydental_business_date': date, 'ydental_channel': channel,
            'ydental_state': 'confirmed', 'ydental_gross': gross,
            'ydental_refunded': refunded, 'ydental_pending': pending,
            'ydental_currency_id': currency.id, 'ydental_confirmed_at': fields.Datetime.now(),
            'ydental_cycle': existing.ydental_cycle + 1 if existing else 1,
        })
        self._audit('close', record, store, after={'gross': gross, 'refunded': refunded,
                                                   'pending': pending, 'cycle': record.ydental_cycle})
        return {'close_id': record.id, 'gross': gross, 'refunded': refunded,
                'pending': pending, 'net': currency.round(gross - refunded)}

    def _unlock(self, close_id, reason):
        store = self._access(write=True, finance=True)
        record = self._model('close').browse(self._positive_id(close_id)).exists()
        if not record or record.ydental_store_id != store or record.ydental_state != 'confirmed':
            raise AccessError(self.env._('access_denied: Select a confirmed close in this store.'))
        latest = self._model('close').search([
            ('ydental_store_id', '=', store.id), ('ydental_cashier_id', '=', record.ydental_cashier_id.id),
            ('ydental_business_date', '=', record.ydental_business_date),
            ('ydental_channel', '=', record.ydental_channel),
        ], order='ydental_cycle desc', limit=1)
        if latest != record:
            raise UserError(self.env._('version_conflict: Unlock the latest close cycle.'))
        record._save({'ydental_state': 'unlocked', 'ydental_unlocked_by_id': self.env.uid,
                      'ydental_unlock_reason': self._text(reason),
                      'ydental_unlocked_at': fields.Datetime.now()})
        self._audit('unlock', record, store, after={'cycle': record.ydental_cycle}, reason=reason)
        return {'close_id': record.id, 'state': 'unlocked'}

    def _reclassify(self, payment_id, new_channel, reason):
        store = self._access(write=True)
        config = self._config(store)
        payment = self._payment_record(payment_id, store)
        old_channel = self._effective_channel(payment)
        if new_channel not in CHANNELS or old_channel == new_channel:
            raise ValidationError(self.env._('Select a different supported offline category.'))
        self._close_guard(store, payment.ydental_cashier_id.id, payment.ydental_business_date, old_channel)
        self._close_guard(store, payment.ydental_cashier_id.id, payment.ydental_business_date, new_channel)
        native = payment.ydental_payment_id
        old_lines = native.move_id.line_ids.filtered(lambda line: line.account_id.account_type != 'asset_receivable'
            and line.debit > 0)
        new_journal = self._journal(config, new_channel)
        new_method = new_journal.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_method_id.code == 'manual')[:1]
        if len(old_lines) != 1 or not new_method or not new_method.payment_account_id:
            raise UserError(self.env._('accounting_policy_invalid: Explicit native clearing accounts are required.'))
        old_account = old_lines.account_id
        new_account = new_method.payment_account_id
        if old_account == new_account or store.company_id not in new_account.company_ids:
            raise UserError(self.env._('accounting_policy_invalid: Reclassification needs distinct same-company accounts.'))
        amount = payment.ydental_amount
        move = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'entry', 'company_id': store.company_id.id,
            'journal_id': config.ydental_adjustment_journal_id.id,
            'date': payment.ydental_business_date,
            'ref': self.env._('YDental offline channel correction; payment %s', native.name),
            'line_ids': [
                Command.create({'name': self._text(reason), 'account_id': new_account.id,
                                'debit': amount, 'credit': 0}),
                Command.create({'name': self._text(reason), 'account_id': old_account.id,
                                'debit': 0, 'credit': amount}),
            ],
        })
        move.action_post()
        if move.state != 'posted' or not store.company_id.currency_id.is_zero(sum(move.line_ids.mapped('balance'))):
            raise UserError(self.env._('accounting_mismatch: Native channel correction did not balance.'))
        correction = self._model('correction')._new({
            'ydental_payment_id': payment.id, 'ydental_old_channel': old_channel,
            'ydental_new_channel': new_channel, 'ydental_move_id': move.id,
            'ydental_reason': reason, 'ydental_actor_id': self.env.uid,
            'ydental_recorded_at': fields.Datetime.now(),
        })
        self._audit('reclassify', correction, store, after={'move_id': move.id,
            'old_channel': old_channel, 'new_channel': new_channel}, reason=reason)
        return {'correction_id': correction.id, 'move_id': move.id,
                'old_channel': old_channel, 'new_channel': new_channel,
                'actual_cash_refunded': 0}

    def _trade(self, target_store_id, source_lot_id, target_lot_id, quantity,
               uom_id, unit_price, source_key, reason):
        """Confirm a dual-authorized native sale and purchase with actual stock."""
        source = self._access(write=True)
        access = self.env['ydental.access.service']
        target = self.env['ydental.access.store'].sudo().browse(self._positive_id(target_store_id)).exists()
        if not target or not target.active or target == source or target.company_id == source.company_id:
            raise AccessError(self.env._('access_denied: Select another active legal entity.'))
        for store in (source, target):
            if store.company_id not in self.env.user.sudo().company_ids:
                raise AccessError(self.env._('access_denied: Both legal entities must be in the user company scope.'))
            access._check('warehouse', 'write', store_id=store.id, write=True)
            access._check('finance_approval', 'write', store_id=store.id, write=True)
        source_config = self._config(source)
        target_config = self._config(target)
        currency = source.company_id.currency_id
        if target.company_id.currency_id != currency:
            raise UserError(self.env._('trade_currency_unapproved: Both synthetic companies must share a currency.'))
        if (target_config.ydental_purchase_journal_id.company_id != target.company_id or
                target_config.ydental_purchase_journal_id.type != 'purchase' or
                target.company_id not in target_config.ydental_expense_account_id.company_ids or
                target_config.ydental_expense_account_id.account_type not in ('expense', 'expense_direct_cost')):
            raise UserError(self.env._('trade_policy_missing: Configure the target purchase journal and expense account.'))
        source_key = self._text(source_key, 120)
        reason = self._text(reason)
        price = self._money(unit_price, currency)
        inventory = self.env['ydental.inventory.service']
        source_lot = inventory._lot(source_lot_id, source)
        target_lot = inventory._lot(target_lot_id, target)
        product = source_lot.product_id
        if (target_lot.product_id != product or target_lot.name != source_lot.name or
                not product.is_storable or not product.sale_ok or not product.purchase_ok):
            raise UserError(self.env._('trade_source_invalid: The two approved company lots must represent one stock product.'))
        inventory._usable(source_lot, source)
        inventory._usable(target_lot, target)
        qty, unit, _snapshot = inventory._unit(product, quantity, uom_id)
        prior = self._model('trade').search([
            ('ydental_source_store_id', '=', source.id), ('ydental_source_key', '=', source_key)], limit=1)
        if prior:
            if (prior.ydental_target_store_id != target or prior.ydental_source_lot_id != source_lot or
                    prior.ydental_target_lot_id != target_lot or abs(prior.ydental_quantity - qty) > 1e-8 or
                    currency.compare_amounts(prior.ydental_unit_price, price) or prior.ydental_reason != reason):
                raise UserError(self.env._('version_conflict: The intercompany source key is immutable.'))
            return {'trade_id': prior.id, 'sale_order_id': prior.ydental_sale_order_id.id,
                    'purchase_order_id': prior.ydental_purchase_order_id.id,
                    'sale_invoice_id': prior.ydental_sale_invoice_id.id,
                    'purchase_bill_id': prior.ydental_purchase_bill_id.id,
                    'out_move_id': prior.ydental_out_move_id.id,
                    'in_move_id': prior.ydental_in_move_id.id}
        source_stock = inventory._config(source)
        target_stock = inventory._config(target)
        source_location = inventory._location(source_stock, product)
        target_location = inventory._location(target_stock, product)
        if product.uom_id.compare(inventory._quantity(source_lot, source_location), qty) < 0:
            raise UserError(self.env._('insufficient_balance: Source lot has no actual available quantity.'))
        income = product.with_company(source.company_id).property_account_income_id or product.categ_id.with_company(
            source.company_id).property_account_income_categ_id
        expense = product.with_company(target.company_id).property_account_expense_id or product.categ_id.with_company(
            target.company_id).property_account_expense_categ_id
        if income != source_config.ydental_income_account_id or expense != target_config.ydental_expense_account_id:
            raise UserError(self.env._('trade_policy_missing: Product accounts must match the two explicit company policies.'))
        context = {'ydental_inventory_mutation': INVENTORY_MUTATION,
                   'tracking_disable': True, 'mail_create_nosubscribe': True}
        sale = self.env['sale.order'].sudo().with_company(source.company_id).with_context(**context).create({
            'company_id': source.company_id.id, 'partner_id': target.company_id.partner_id.id,
            'warehouse_id': source_stock.ydental_warehouse_id.id,
            'order_line': [Command.create({'product_id': product.id, 'product_uom_qty': qty,
                'product_uom_id': product.uom_id.id, 'price_unit': price, 'tax_ids': [Command.clear()]})],
        })
        sale.action_confirm()
        purchase = self.env['purchase.order'].sudo().with_company(target.company_id).with_context(**context).create({
            'company_id': target.company_id.id, 'partner_id': source.company_id.partner_id.id,
            'picking_type_id': target_stock.ydental_warehouse_id.in_type_id.id,
            'origin': sale.name, 'partner_ref': sale.name,
            'order_line': [Command.create({'product_id': product.id, 'product_qty': qty,
                'uom_id': product.uom_id.id, 'price_unit': price,
                'date_planned': fields.Datetime.now(), 'tax_ids': [Command.clear()]})],
        })
        purchase.button_confirm()
        if sale.state != 'sale' or purchase.state != 'purchase':
            raise UserError(self.env._('trade_approval_required: Both native orders must be confirmed.'))
        out_pickings = sale.picking_ids.filtered(lambda picking: picking.picking_type_id.code == 'outgoing')
        in_pickings = purchase.picking_ids.filtered(lambda picking: picking.picking_type_id.code == 'incoming')
        if len(out_pickings) != 1 or len(in_pickings) != 1:
            raise UserError(self.env._('trade_stock_mismatch: Expected one native delivery and one receipt.'))
        out_move = self._trade_finish_move(out_pickings, product, source_lot, qty,
                                           source_location, source, outgoing=True)
        in_move = self._trade_finish_move(in_pickings, product, target_lot, qty,
                                          target_location, target, outgoing=False)
        sale_invoice = sale.with_context(default_journal_id=source_config.ydental_sales_journal_id.id)._create_invoices()
        purchase.with_context(default_journal_id=target_config.ydental_purchase_journal_id.id).action_create_invoice()
        purchase_bill = purchase.invoice_ids.filtered(lambda bill: bill.move_type == 'in_invoice')
        if len(sale_invoice) != 1 or len(purchase_bill) != 1:
            raise UserError(self.env._('trade_account_mismatch: Expected one native invoice and one vendor bill.'))
        purchase_bill.write({'invoice_date': fields.Date.context_today(self)})
        sale_invoice.action_post()
        purchase_bill.action_post()
        expected = currency.round(qty * price)
        if (sale_invoice.state != 'posted' or purchase_bill.state != 'posted' or
                sale_invoice.company_id != source.company_id or purchase_bill.company_id != target.company_id or
                sale_invoice.journal_id != source_config.ydental_sales_journal_id or
                purchase_bill.journal_id != target_config.ydental_purchase_journal_id or
                currency.compare_amounts(sale_invoice.amount_total, expected) or
                currency.compare_amounts(purchase_bill.amount_total, expected) or
                not sale_invoice.invoice_line_ids.filtered(lambda line: sale.order_line & line.sale_line_ids) or
                not purchase_bill.invoice_line_ids.filtered(lambda line: line.purchase_line_id in purchase.order_line)):
            raise UserError(self.env._('trade_account_mismatch: Native company invoices must match linked orders.'))
        trade = self._model('trade')._new({
            'ydental_source_store_id': source.id, 'ydental_target_store_id': target.id,
            'ydental_source_key': source_key, 'ydental_actor_id': self.env.uid,
            'ydental_product_id': product.id, 'ydental_source_lot_id': source_lot.id,
            'ydental_target_lot_id': target_lot.id, 'ydental_quantity': qty,
            'ydental_unit_id': product.uom_id.id, 'ydental_unit_price': price,
            'ydental_currency_id': currency.id, 'ydental_reason': reason,
            'ydental_sale_order_id': sale.id, 'ydental_purchase_order_id': purchase.id,
            'ydental_out_move_id': out_move.id, 'ydental_in_move_id': in_move.id,
            'ydental_sale_invoice_id': sale_invoice.id, 'ydental_purchase_bill_id': purchase_bill.id,
        })
        self._audit('trade', trade, source, after={'target_store_id': target.id,
            'sale_order_id': sale.id, 'purchase_order_id': purchase.id,
            'sale_invoice_id': sale_invoice.id, 'purchase_bill_id': purchase_bill.id,
            'out_move_id': out_move.id, 'in_move_id': in_move.id}, reason=reason)
        access._audit('settlement.trade_receive', 'finance_approval', trade, target.id,
            after={'source_store_id': source.id, 'purchase_bill_id': purchase_bill.id,
                   'in_move_id': in_move.id}, reason=reason, source='confirmed_intercompany_trade')
        return {'trade_id': trade.id, 'sale_order_id': sale.id,
                'purchase_order_id': purchase.id, 'sale_invoice_id': sale_invoice.id,
                'purchase_bill_id': purchase_bill.id, 'out_move_id': out_move.id,
                'in_move_id': in_move.id, 'amount': expected}

    def _trade_finish_move(self, picking, product, lot, quantity, location, store, outgoing):
        move = picking.move_ids.filtered(lambda row: row.product_id == product)
        if len(move) != 1 or move.company_id != store.company_id or move.state == 'done':
            raise UserError(self.env._('trade_stock_mismatch: Native order movement is ambiguous.'))
        move = move.with_context(ydental_inventory_mutation=INVENTORY_MUTATION)
        move._do_unreserve()
        move.write({'ydental_store_id': store.id,
                    'location_id' if outgoing else 'location_dest_id': location.id})
        source = location if outgoing else move.location_id
        target = move.location_dest_id if outgoing else location
        self.env['stock.move.line'].sudo().with_company(store.company_id).with_context(
            ydental_inventory_mutation=INVENTORY_MUTATION).create({
                'move_id': move.id, 'picking_id': picking.id, 'product_id': product.id,
                'uom_id': product.uom_id.id, 'quantity': quantity, 'lot_id': lot.id,
                'location_id': source.id, 'location_dest_id': target.id,
                'company_id': store.company_id.id, 'ydental_store_id': store.id,
                'picked': True,
            })
        move.write({'picked': True})
        picking.with_context(ydental_inventory_mutation=INVENTORY_MUTATION)._action_done()
        if picking.state != 'done' or move.state != 'done':
            raise UserError(self.env._('trade_stock_mismatch: Native company movement was not completed.'))
        return move

    def _patient_family_ids(self, patient):
        family = {patient.id}
        patients = self.env['ydental.patient'].sudo().with_context(active_test=False)
        while True:
            aliases = set(patients.search([('ydental_merged_into_id', 'in', list(family))]).ids)
            if aliases <= family:
                return list(family)
            family.update(aliases)

    def _workbench_page(self, model, domain, page, order):
        count = model.search_count(domain)
        return model.search(domain, order=order, offset=(page - 1) * 50, limit=50), count

    def _workbench(self, patient_id=None, pages=None):
        store = self._access()
        patient = self._patient(patient_id) if patient_id else False
        if patient:
            self.env['ydental.patient.service']._current_relation(patient, store)
        pages = pages or {}
        if not isinstance(pages, dict) or any(key not in ('today', 'history', 'pending', 'invoices')
                                               or type(value) is not int or not 1 <= value <= 10000
                                               for key, value in pages.items()):
            raise ValidationError(self.env._('Select a valid workbench page.'))
        page_numbers = {key: pages.get(key, 1) for key in ('today', 'history', 'pending', 'invoices')}
        family = self._patient_family_ids(patient) if patient else None
        fee_domain = fields.Domain('ydental_store_id', '=', store.id) & fields.Domain(
            'ydental_event_id.state', '=', 'confirmed') & fields.Domain(
            'ydental_settlement_source_ids', 'not any', fields.Domain.TRUE)
        event_domain = fields.Domain('ydental_store_id', '=', store.id) & fields.Domain('state', '=', 'pending')
        source_domain = fields.Domain('ydental_store_id', '=', store.id)
        if family is not None:
            patient_domain = fields.Domain('ydental_patient_id', 'in', family)
            fee_domain &= patient_domain
            event_domain &= patient_domain
            source_domain &= patient_domain
        today = fields.Date.context_today(self.with_context(tz=store.ydental_timezone))
        fees = self.env['ydental.treatment.fee'].sudo()
        today_fees, today_count = self._workbench_page(fees,
            fee_domain & fields.Domain('ydental_event_id.ydental_business_date', '=', today),
            page_numbers['today'], 'id desc')
        history, history_count = self._workbench_page(fees,
            fee_domain & fields.Domain('ydental_event_id.ydental_business_date', '!=', today),
            page_numbers['history'], 'id desc')
        pending, pending_count = self._workbench_page(self.env['ydental.treatment.event'].sudo(),
            event_domain, page_numbers['pending'], 'id desc')
        invoice_domain = fields.Domain('company_id', '=', store.company_id.id) & fields.Domain(
            'state', '=', 'posted') & fields.Domain('move_type', '=', 'out_invoice') & fields.Domain(
            'amount_residual', '>', 0) & fields.Domain(
            'ydental_settlement_source_ids', 'any', source_domain)
        invoices, invoice_count = self._workbench_page(self.env['account.move'].sudo(),
            invoice_domain, page_numbers['invoices'], 'invoice_date asc, id asc')
        for fee in today_fees | history:
            self._audit('source_view', fee, store)
        for event in pending:
            self._audit('pending_event_view', event, store,
                        after={'state': event.state, 'reason': event.ydental_pending_reason})
        for invoice in invoices:
            self._audit('invoice_view', invoice, store)
        return {'store': store, 'patient': patient,
                'today': today_fees, 'history': history,
                'pending': pending, 'invoices': invoices,
                'pages': page_numbers, 'page_counts': {'today': today_count,
                    'history': history_count, 'pending': pending_count, 'invoices': invoice_count},
                'payments': self._model('payment').search([('ydental_store_id', '=', store.id)], order='id desc', limit=50),
                'refunds': self._model('refund').search([('ydental_payment_id.ydental_store_id', '=', store.id)],
                                                       order='id desc', limit=50),
                'closes': self._model('close').search([('ydental_store_id', '=', store.id)], order='id desc', limit=30)}

    def _other_store_summary(self, patient_id):
        store = self._access()
        patient = self._patient(patient_id)
        self.env['ydental.patient.service']._current_relation(patient, store)
        rows = {}
        seen_invoice_ids = set()
        family = self._patient_family_ids(patient)
        for link in self._model('source').search([
                ('ydental_store_id', '!=', store.id), ('ydental_patient_id', 'in', family),
                ('ydental_invoice_id.state', '=', 'posted'), ('ydental_invoice_id.amount_residual', '>', 0)]):
            if link.ydental_invoice_id.id in seen_invoice_ids:
                continue
            other = link.ydental_store_id
            if other.company_id not in self.env.user.sudo().company_ids:
                continue
            if link.ydental_invoice_id.amount_residual <= 0:
                continue
            row = rows.setdefault(other.id, {'store': other.name, 'store_id': other.id,
                                             'company': other.company_id.name,
                                             'currency': other.company_id.currency_id.name,
                                             'residual': 0})
            row['residual'] += link.ydental_invoice_id.amount_residual
            seen_invoice_ids.add(link.ydental_invoice_id.id)
        for row in rows.values():
            row['residual'] = self.env['ydental.access.store'].sudo().browse(
                row['store_id']).company_id.currency_id.round(row['residual'])
        self._audit('other_store_summary', patient, store, after={'store_count': len(rows)})
        return list(rows.values())

    def _report_payload(self, kind, source_id):
        store = self._access()
        self.env['ydental.access.service']._check('export', 'write')
        source_id = self._positive_id(source_id)
        currency = store.company_id.currency_id
        payload = {'kind': kind, 'source_id': source_id, 'company': store.company_id.name,
                   'store': store.name, 'currency': currency.name,
                   'operator': self.env.user.name,
                   'demo': '演示线下业务凭据；非税务发票、非银行或支付平台到账证明'}
        if kind == 'bill':
            invoice, sources = self._invoice(source_id, store)
            patient = self._patient(sources[0].ydental_patient_id.id)
            received_partials = self.env['account.partial.reconcile'].sudo().search([
                ('debit_move_id.move_id', '=', invoice.id),
                ('credit_move_id.move_id.origin_payment_id', '!=', False),
            ])
            payload.update({'patient': patient.ydental_number, 'number': invoice.name,
                'business_date': str(invoice.invoice_date), 'total': invoice.amount_total,
                'residual': invoice.amount_residual,
                'received': currency.round(sum(received_partials.mapped('amount'))),
                'lines': [{'name': link.ydental_fee_id.name,
                           'fee_id': link.ydental_fee_id.id, 'amount': link.ydental_original_amount,
                           'price_version': link.ydental_price_version} for link in sources],
                'discount': currency.round(sum(sources.mapped('ydental_discount')))})
            target = invoice
        elif kind == 'receipt':
            payment = self._payment_record(source_id, store)
            patient = self._patient(payment.ydental_patient_id.id)
            partials = self.env['account.partial.reconcile'].sudo().search([
                ('credit_move_id', 'in', payment.ydental_payment_id.move_id.line_ids.ids),
                ('debit_move_id.move_id', 'in', payment.ydental_invoice_ids.ids),
            ], order='id')
            refunds = self._model('refund').search([('ydental_payment_id', '=', payment.id)])
            done = sum(refunds.filtered(lambda row: row.ydental_state == 'done').mapped('ydental_amount'))
            pending = sum(refunds.filtered(lambda row: row.ydental_state in
                ('requested', 'approved', 'failed', 'unknown')).mapped('ydental_amount'))
            payload.update({'patient': patient.ydental_number,
                'number': payment.ydental_payment_id.name,
                'business_date': str(payment.ydental_business_date),
                'actual_utc': str(payment.ydental_actual_at),
                'recorded_utc': str(payment.ydental_entered_at),
                'channel': self._effective_channel(payment),
                'received': payment.ydental_amount, 'refunded': currency.round(done),
                'pending': currency.round(pending),
                'net': currency.round(payment.ydental_amount - done),
                'residual': currency.round(sum(payment.ydental_invoice_ids.mapped('amount_residual'))),
                'allocations': [{'invoice': part.debit_move_id.move_id.name, 'amount': part.amount}
                                for part in partials]})
            target = payment
        elif kind == 'refund':
            refund = self._refund(source_id, store)
            payment = refund.ydental_payment_id
            patient = self._patient(payment.ydental_patient_id.id)
            payload.update({'patient': patient.ydental_number,
                'number': str(refund.id), 'business_date': str(payment.ydental_business_date),
                'state': refund.ydental_state, 'requested': refund.ydental_amount,
                'pending': refund.ydental_amount if refund.ydental_state in
                    ('requested', 'approved', 'failed', 'unknown') else 0,
                'refunded': refund.ydental_amount if refund.ydental_state == 'done' else 0,
                'actual_utc': str(refund.ydental_actual_at or ''),
                'native_payment': refund.ydental_native_payment_id.name or '',
                'reason': refund.ydental_reason})
            target = refund
        else:
            raise AccessError(self.env._('access_denied: Unknown settlement report kind.'))
        return target, payload

    def _validate_pdf_scope(self):
        scope = self.env.context.get('ydental_settlement_pdf_scope')
        session = self.env['ydental.access.service']._scope()
        if type(scope) is not SettlementPdfScope or (
                scope.actor_id, scope.session_id, scope.revision) != (
                    self.env.uid, session.id, session.ydental_revision):
            raise AccessError(self.env._('access_denied: A bound settlement export request is required.'))
        _target, payload = self._report_payload(scope.kind, scope.source_id)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        if digest != scope.digest:
            raise UserError(self.env._('version_conflict: Settlement report source changed while rendering.'))
        return payload

    def _pdf(self, kind, source_id):
        target, payload = self._report_payload(kind, source_id)
        session = self.env['ydental.access.service']._scope()
        scope = SettlementPdfScope(self.env.uid, session.id, session.ydental_revision,
            kind, source_id, hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                       ensure_ascii=True).encode()).hexdigest())
        report = self.env['ir.actions.report'].with_context(
            ydental_settlement_pdf_scope=scope, lang='zh_CN', force_report_rendering=True,
            report_pdf_no_attachment=True)
        try:
            pdf, result = report._render_qweb_pdf('ydental_settlement.ydental_settlement_pdf', [source_id])
            if result != 'pdf' or not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF-') or len(pdf) > 10000000 or (
                    len(PdfFileReader(io.BytesIO(pdf)).pages) > 20):
                raise UserError(self.env._('render_failed: Settlement PDF is invalid or too long.'))
        except (QWebError, PdfReadError, OSError, ValueError) as error:
            raise UserError(self.env._('render_failed: Settlement PDF could not be generated.')) from error
        digest = hashlib.sha256(pdf).hexdigest()
        self._audit('report_download', target, self._access(), after={'kind': kind, 'pdf_sha256': digest})
        return pdf, digest
