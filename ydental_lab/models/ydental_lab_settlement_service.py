from datetime import timezone
import hashlib
import json

from odoo import Command, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalSettlementService(models.AbstractModel):
    _inherit = 'ydental.settlement.service'

    def _extension_operation_handlers(self):
        handlers = super()._extension_operation_handlers()
        handlers.update({'bill_lab_charge': self._bill_lab_charge,
                         'credit_lab_charge': self._credit_lab_charge})
        return handlers

    def _settled_source_domain(self, source_domain, store, family):
        fee_domain = super()._settled_source_domain(source_domain, store, family)
        charge_domain = source_domain & fields.Domain('ydental_lab_charge_id', '!=', False) & fields.Domain(
            'ydental_lab_charge_id.ydental_store_id', '=', store.id) & fields.Domain(
            'ydental_lab_charge_id.state', '=', 'billed') & fields.Domain(
            'ydental_lab_charge_id.ydental_order_id.state', 'not in', ('cancelled', 'exception'))
        if family is not None:
            charge_domain &= fields.Domain('ydental_lab_charge_id.ydental_patient_id', 'in', family)
        adjustment_domain = source_domain & fields.Domain(
            'ydental_lab_charge_adjustment_id', '!=', False) & fields.Domain(
            'ydental_lab_charge_adjustment_id.ydental_store_id', '=', store.id)
        if family is not None:
            adjustment_domain &= fields.Domain('ydental_lab_charge_adjustment_id.ydental_patient_id', 'in', family)
        return fee_domain | charge_domain | adjustment_domain

    def _bill_summary_line(self, source):
        if source.ydental_lab_charge_id:
            charge = source.ydental_lab_charge_id
            return {'name': charge.name, 'lab_charge_id': charge.id,
                    'amount': source.ydental_original_amount,
                    'price_version': source.ydental_price_version}
        if source.ydental_lab_charge_adjustment_id:
            adjustment = source.ydental_lab_charge_adjustment_id
            return {'name': adjustment.name, 'lab_charge_adjustment_id': adjustment.id,
                    'amount': source.ydental_original_amount,
                    'price_version': source.ydental_price_version}
        return super()._bill_summary_line(source)

    def _original_invoice(self, invoice_id):
        invoice, sources = self._invoice(invoice_id, self._access())
        if not any(source.ydental_lab_charge_id for source in sources):
            return super()._original_invoice(invoice_id)
        store = self._access()
        self.env['ydental.access.service']._check('export', 'write')
        patient = self._patient(sources[0].ydental_patient_id.id)
        family = set(self._patient_family_ids(patient))
        if (invoice.partner_id.ydental_patient_owner_id.id not in family or
                any(not source.ydental_lab_charge_id or source.ydental_fee_id or
                    source.ydental_store_id != store or source.ydental_patient_id.id not in family or
                    source.ydental_currency_id != invoice.currency_id or
                    source.ydental_lab_charge_id.ydental_store_id != store or
                    source.ydental_lab_charge_id.ydental_patient_id.id not in family or
                    source.ydental_lab_charge_id.state != 'billed' or
                    source.ydental_lab_charge_id.ydental_settlement_source_id != source
                    for source in sources)):
            raise AccessError(self.env._('access_denied: Every laboratory source must match this store, patient and native invoice.'))
        return invoice, sources, patient, store

    def _original_facts(self, invoice, sources):
        if not any(source.ydental_lab_charge_id for source in sources):
            return super()._original_facts(invoice, sources)
        charges = sources.ydental_lab_charge_id
        snapshots = charges.ydental_price_snapshot_id
        base = {
            'invoice': self._original_values(invoice, ['company_id', 'partner_id', 'currency_id', 'state',
                'move_type', 'invoice_date', 'amount_total', 'amount_residual', 'payment_state']),
            'sources': self._original_values(sources, ['ydental_store_id', 'ydental_patient_id',
                'ydental_fee_id', 'ydental_lab_charge_id', 'ydental_invoice_id', 'ydental_line_id',
                'ydental_original_amount', 'ydental_discount', 'ydental_currency_id', 'ydental_price_version']),
            'lab_charges': self._original_values(charges, ['ydental_order_id', 'ydental_patient_id',
                'ydental_catalog_id', 'ydental_price_id', 'ydental_price_snapshot_id', 'ydental_quantity',
                'ydental_uom_id', 'ydental_currency_id', 'ydental_unit_price', 'ydental_amount',
                'ydental_quoted_at', 'ydental_terms_confirmed_by_id', 'ydental_terms_confirmed_at',
                'ydental_confirmation_reference', 'ydental_reason', 'state', 'ydental_performed_by_id',
                'ydental_performed_at', 'ydental_performance_evidence_reference']),
            'snapshots': self._original_values(snapshots, ['ydental_price_id', 'ydental_catalog_id',
                'ydental_quantity', 'ydental_quantity_digits', 'ydental_currency_rounding', 'ydental_uom_id',
                'ydental_currency_id', 'ydental_unit_price', 'ydental_amount', 'ydental_quoted_at']),
            'lines': self._original_values(invoice.line_ids, ['account_id', 'partner_id', 'currency_id',
                'debit', 'credit', 'balance', 'amount_currency', 'amount_residual', 'amount_residual_currency']),
            'partials': self._original_values(self.env['account.partial.reconcile'].sudo().search(
                fields.Domain('debit_move_id', 'in', invoice.line_ids.ids) |
                fields.Domain('credit_move_id', 'in', invoice.line_ids.ids)),
                ['debit_move_id', 'credit_move_id', 'amount', 'debit_amount_currency', 'credit_amount_currency']),
        }
        return base

    def _bill_lab_charge(self, charge_ids, reason):
        store = self._access(write=True)
        config = self._config(store)
        if (not isinstance(charge_ids, list) or not charge_ids or
                any(type(charge_id) is not int or charge_id <= 0 for charge_id in charge_ids) or
                len(set(charge_ids)) != len(charge_ids)):
            raise ValidationError(self.env._('Select distinct performed laboratory charge sources.'))
        reason = self._text(reason, 240)
        charges = self.env['ydental.lab.charge'].sudo().browse(charge_ids).exists()
        if len(charges) != len(charge_ids):
            raise AccessError(self.env._('access_denied: A selected laboratory charge is unavailable.'))
        charges = charges.sorted('id')
        if any(charge.ydental_store_id != store or charge.state != 'performed' for charge in charges):
            raise AccessError(self.env._('access_denied: Only performed charges from the current store can be billed.'))
        if any(charge.ydental_currency_id != store.company_id.currency_id or
               charge.ydental_order_id.ydental_parent_order_id.ydental_patient_id != charge.ydental_patient_id or
               charge.ydental_price_snapshot_id.ydental_price_id != charge.ydental_price_id or
               charge.ydental_price_snapshot_id.ydental_catalog_id != charge.ydental_catalog_id or
               charge.ydental_price_snapshot_id.ydental_quantity != charge.ydental_quantity
               for charge in charges):
            raise UserError(self.env._('charge_source_invalid: Frozen price, cycle, currency or patient source no longer matches.'))
        patients = charges.mapped('ydental_patient_id')
        if len(patients) != 1:
            raise AccessError(self.env._('access_denied: Charges for different patients cannot share one invoice.'))
        patient = self._patient(patients.id)
        prior = self._model('source').search([('ydental_lab_charge_id', 'in', charge_ids)])
        if prior:
            if (len(prior) == len(charges) and set(prior.ydental_lab_charge_id.ids) == set(charge_ids)
                    and len(prior.ydental_invoice_id) == 1
                    and prior.ydental_invoice_id.state == 'posted'):
                return {'invoice_id': prior.ydental_invoice_id.id,
                        'amount': prior.ydental_invoice_id.amount_total,
                        'residual': prior.ydental_invoice_id.amount_residual}
            raise UserError(self.env._('charge_already_billed: A selected charge is already attached to another native invoice.'))
        currency = store.company_id.currency_id
        amount = currency.round(sum(charges.mapped('ydental_amount')))
        if currency.is_zero(amount) or any(currency.is_zero(charge.ydental_amount) for charge in charges):
            raise UserError(self.env._('charge_amount_invalid: Native patient charges must have a nonzero published amount.'))
        business_dates = []
        for charge in charges:
            moment = fields.Datetime.to_datetime(charge.ydental_performed_at).replace(tzinfo=timezone.utc)
            day = self._local_date(store, moment)
            self._close_guard_any(store, self.env.uid, day)
            business_dates.append(day)
        invoice_date = max(business_dates)
        commands = [Command.create({
            'name': '%s / %s' % (charge.ydental_order_id.name, charge.ydental_catalog_id.name),
            'quantity': charge.ydental_quantity, 'price_unit': charge.ydental_unit_price,
            'account_id': config.ydental_income_account_id.id, 'tax_ids': [Command.clear()],
            'product_id': charge.ydental_catalog_id.ydental_product_id.id or False,
        }) for charge in charges]
        invoice = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'out_invoice', 'company_id': store.company_id.id,
            'journal_id': config.ydental_sales_journal_id.id,
            'partner_id': patient.ydental_partner_id.id,
            'invoice_date': invoice_date, 'date': invoice_date,
            'currency_id': currency.id,
            'invoice_origin': 'YDental lab-cycle additional service charges ' + ','.join(map(str, charge_ids)),
            'invoice_line_ids': commands,
        })
        invoice.action_post()
        if invoice.state != 'posted' or currency.compare_amounts(invoice.amount_total, amount):
            raise UserError(self.env._('accounting_mismatch: Native invoice differs from frozen laboratory charge sources.'))
        lines = invoice.invoice_line_ids.sorted('id')
        if len(lines) != len(charges):
            raise UserError(self.env._('accounting_mismatch: Native invoice lines do not match the laboratory charge sources.'))
        for charge, line, business_date in zip(charges, lines, business_dates):
            if currency.compare_amounts(line.price_subtotal, charge.ydental_amount):
                raise UserError(self.env._('accounting_mismatch: Native invoice line differs from frozen charge amount.'))
            source = self._model('source')._new({
                'ydental_fee_id': False, 'ydental_lab_charge_id': charge.id,
                'ydental_store_id': store.id, 'ydental_patient_id': charge.ydental_patient_id.id,
                'ydental_invoice_id': invoice.id, 'ydental_line_id': line.id,
                'ydental_original_amount': charge.ydental_amount, 'ydental_currency_id': currency.id,
                'ydental_discount': 0, 'ydental_discount_reason': False,
                'ydental_source_business_date': business_date,
                'ydental_source_actual_at': charge.ydental_performed_at,
                'ydental_price_version': 'S05:' + str(charge.ydental_price_id.id),
            })
            charge._save({'state': 'billed', 'ydental_settlement_source_id': source.id})
        self._audit('bill_lab_charge', invoice, store,
                    after={'charge_ids': charge_ids, 'amount': amount}, reason=reason)
        return {'invoice_id': invoice.id, 'amount': invoice.amount_total,
                'residual': invoice.amount_residual, 'charge_ids': charge_ids}

    def _validate_lab_charge_credit_total(self, currency, original_amount, previous_amounts, requested_amount):
        total = currency.round(sum(previous_amounts) + requested_amount)
        if currency.compare_amounts(total, original_amount) > 0:
            raise UserError(self.env._('correction_amount_invalid: Cumulative credits cannot exceed the original billed charge.'))
        return total

    def _credit_lab_charge(self, charge_id, amount, reason, request_key):
        """Issue an immutable native credit note against an already billed charge.

        The settlement service's transaction lock, write authorization, operation
        receipt and audit envelope apply to this extension exactly as they do to
        native S10 operations. Only the unpaid receivable is reconciled; this
        operation never transfers cash.
        """
        from odoo.exceptions import UserError, ValidationError

        store = self._access(write=True)
        config = self._config(store)
        charge_id = self._positive_id(charge_id)
        if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 120:
            raise ValidationError(self.env._('invalid_action: Supply a stable correction request key.'))
        reason = self._text(reason, 240)
        if type(amount) not in (int, float):
            raise ValidationError(self.env._('invalid_amount: Enter a positive correction amount.'))
        charge = self.env['ydental.lab.charge'].sudo().browse(charge_id).exists()
        if (not charge or charge.state != 'billed' or charge.ydental_store_id != store or
                not charge.ydental_settlement_source_id):
            raise AccessError(self.env._('access_denied: Select a billed cycle charge from this store.'))
        self.env.cr.execute('SELECT id FROM ydental_lab_charge WHERE id = %s FOR UPDATE', [charge.id])
        charge.invalidate_recordset()
        source = charge.ydental_settlement_source_id
        if not source:
            raise UserError(self.env._('charge_source_invalid: Original native invoice link is missing.'))
        original = source.ydental_invoice_id
        currency = charge.ydental_currency_id
        if (not source or source.ydental_lab_charge_id != charge or source.ydental_fee_id or
                source.ydental_store_id != store or source.ydental_patient_id != charge.ydental_patient_id or
                source.ydental_currency_id != currency or
                source.ydental_line_id.move_id != original or
                currency.compare_amounts(source.ydental_original_amount, charge.ydental_amount) or
                original.state != 'posted' or original.move_type != 'out_invoice' or
                original.company_id != store.company_id or original.currency_id != currency or
                currency != store.company_id.currency_id):
            raise UserError(self.env._('charge_source_invalid: Original native invoice link is inconsistent.'))
        amount = self._money(amount, currency)
        adjustments = self.env['ydental.lab.charge.adjustment'].sudo().search(
            [('ydental_charge_id', '=', charge.id)], order='ydental_revision,id')
        replay = adjustments.filtered(lambda row: row.ydental_request_key == request_key)
        fingerprint = hashlib.sha256(json.dumps([
            charge.id, store.id, amount, reason, self.env.uid,
        ], sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        if replay:
            if len(replay) != 1 or replay.ydental_fingerprint != fingerprint:
                raise UserError(self.env._('version_conflict: Correction key is already bound to different terms.'))
            if replay.ydental_credit_move_id.state != 'posted':
                raise UserError(self.env._('credit_incomplete: Existing correction needs finance review.'))
            return {'credit_note_id': replay.ydental_credit_move_id.id,
                    'amount': -replay.ydental_amount,
                    'unpaid_reduced': 0, 'actually_refunded': 0,
                    'adjustment_id': replay.id}
        self._validate_lab_charge_credit_total(
            currency, charge.ydental_amount, adjustments.mapped('ydental_amount'), amount)
        business_date = self._local_date(store, fields.Datetime.to_datetime(fields.Datetime.now()).replace(tzinfo=timezone.utc))
        self._close_guard_any(store, self.env.uid, business_date)
        patient = self._patient(charge.ydental_patient_id.id)
        credit = self.env['account.move'].sudo().with_company(store.company_id).create({
            'move_type': 'out_refund', 'company_id': store.company_id.id,
            'journal_id': config.ydental_sales_journal_id.id,
            'partner_id': original.partner_id.id,
            'invoice_date': business_date, 'date': business_date,
            'currency_id': currency.id, 'invoice_origin': original.name,
            'invoice_line_ids': [Command.create({
                'name': '%s / correction: %s' % (charge.name, reason),
                'quantity': 1, 'price_unit': amount,
                'account_id': config.ydental_income_account_id.id,
                'tax_ids': [Command.clear()],
                'product_id': charge.ydental_catalog_id.ydental_product_id.id or False,
            })],
        })
        credit.action_post()
        if credit.state != 'posted' or currency.compare_amounts(credit.amount_total, amount):
            raise UserError(self.env._('accounting_mismatch: Native credit differs from correction amount.'))
        credit_line = credit.invoice_line_ids[:1]
        revision = (adjustments[-1].ydental_revision if adjustments else 0) + 1
        adjustment = self.env['ydental.lab.charge.adjustment']._new({
            'name': '%s / credit %s' % (charge.name, revision),
            'ydental_category': 'medical', 'ydental_charge_id': charge.id,
            'ydental_revision': revision, 'ydental_store_id': store.id,
            'ydental_patient_id': patient.id, 'ydental_currency_id': currency.id,
            'ydental_amount': amount, 'ydental_reason': reason,
            'ydental_request_key': request_key, 'ydental_fingerprint': fingerprint,
            'ydental_actor_id': self.env.uid, 'ydental_created_at': fields.Datetime.now(),
            'ydental_credit_move_id': credit.id, 'ydental_credit_line_id': credit_line.id,
        })
        adjustment_source = self._model('source')._new({
            'ydental_fee_id': False, 'ydental_lab_charge_id': False,
            'ydental_lab_charge_adjustment_id': adjustment.id,
            'ydental_store_id': store.id, 'ydental_patient_id': patient.id,
            'ydental_invoice_id': credit.id, 'ydental_line_id': credit_line.id,
            'ydental_original_amount': -amount, 'ydental_currency_id': currency.id,
            'ydental_discount': 0, 'ydental_discount_reason': False,
            'ydental_source_business_date': business_date,
            'ydental_source_actual_at': fields.Datetime.now(),
            'ydental_price_version': 'S05:%s/credit:v%s' % (charge.ydental_price_id.id, revision),
        })
        adjustment._link_source(adjustment_source)
        receivable_debit = self._receivable(original, debit=True)
        receivable_credit = self._receivable(credit, debit=False)
        allocated = min(receivable_debit.amount_residual, amount)
        if allocated > 0:
            self.env['account.partial.reconcile'].sudo().with_company(store.company_id).create({
                'debit_move_id': receivable_debit.id, 'credit_move_id': receivable_credit.id,
                'amount': allocated, 'debit_amount_currency': allocated,
                'credit_amount_currency': allocated,
            })
        self._audit('credit_lab_charge', credit, store, after={
            'charge_id': charge.id, 'adjustment_id': adjustment.id, 'revision': revision,
            'original_invoice_id': original.id, 'credit_amount': amount,
            'unpaid_reduced': allocated, 'actually_refunded': 0,
        }, reason=reason)
        return {'credit_note_id': credit.id, 'amount': -amount,
                'unpaid_reduced': allocated, 'actually_refunded': 0,
                'adjustment_id': adjustment.id}
