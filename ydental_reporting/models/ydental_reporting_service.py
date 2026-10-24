from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import LazyTranslate


_lt = LazyTranslate(__name__)


METRICS = {
    'unique_patients': (_lt('Unique patients with actual arrival'), 'arrivals', 'period'),
    'arrivals': (_lt('Actual store arrivals'), 'arrivals', 'period'),
    'executions': (_lt('Confirmed actual project / dispensing events in authorized source categories'), 'execution', 'period'),
    'original_billing': (_lt('Original posted billing'), 'settlement', 'period'),
    'credits': (_lt('Posted credit notes, not cash refunds'), 'settlement', 'period'),
    'collections': (_lt('Actual offline collections, not revenue'), 'settlement', 'period'),
    'refunds': (_lt('Actual offline refunds'), 'settlement', 'period'),
    'approved_pending': (_lt('Approved refunds awaiting actual execution now'), 'settlement', 'snapshot'),
    'receivables': (_lt('Current receivable for selected original bill dates'), 'settlement', 'snapshot'),
    'consumption': (_lt('Done treatment / medicine consumption by product, lot and unit'), 'warehouse', 'period'),
    'lab_pending': (_lt('Current laboratory delivery responsibility by state'), 'laboratory', 'snapshot'),
    'followups': (_lt('Current unfinished follow-up plans by responsible person'), 'followup', 'snapshot'),
}
MAX_ROWS = 50000


class YDentalReportingService(models.AbstractModel):
    _name = 'ydental.reporting.service'
    _description = 'Authorized read-only projections of operating business sources'

    def _metric_access(self, metric, store, export=False):
        if metric not in METRICS:
            raise ValidationError(self.env._('invalid_metric: Select a documented metric.'))
        access = self.env['ydental.access.service']
        access._scope()
        if not store or not store.active or store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: Select an active store in an allowed company.'))
        category = METRICS[metric][1]
        options = {'arrivals': ('frontdesk', 'medical', 'exam'),
                   'laboratory': ('medical',),
                   'execution': ('medical', 'exam', 'pharmacy')}.get(category, (category,))
        authorized = False
        for candidate in options:
            try:
                access._check(candidate, 'read', store_id=store.id)
                authorized = True
                break
            except AccessError:
                continue
        if not authorized:
            raise AccessError(self.env._('access_denied: Every selected store requires the metric source reading permission.'))
        if export:
            access._check('export', 'write', store_id=store.id)

    def _execution_categories(self, store):
        access = self.env['ydental.access.service']
        result = []
        for category in ('medical', 'exam', 'pharmacy'):
            try:
                access._check(category, 'read', store_id=store.id)
                result.append(category)
            except AccessError:
                continue
        return result

    def _filters(self, metric, date_from, date_to, store_ids=None, company_id=None,
                 currency_id=None, state=None, export=False):
        access = self.env['ydental.access.service']
        current = access._scope().ydental_store_id
        if (not isinstance(date_from, str) or not isinstance(date_to, str)
                or len(date_from) != 10 or len(date_to) != 10):
            raise ValidationError(self.env._('invalid_dates: Supply explicit local start and end dates.'))
        try:
            start, end = fields.Date.to_date(date_from), fields.Date.to_date(date_to)
        except (ValueError, TypeError) as error:
            raise ValidationError(self.env._('invalid_dates: Supply valid local dates.')) from error
        if not start or not end or start > end or (end - start).days > 3660:
            raise ValidationError(self.env._('invalid_dates: Select an ordered range of at most ten years.'))
        store_ids = [current.id] if store_ids is None else store_ids
        if (not isinstance(store_ids, list) or not store_ids or len(store_ids) > 50
                or len(set(store_ids)) != len(store_ids)
                or any(type(value) is not int or value <= 0 for value in store_ids)):
            raise ValidationError(self.env._('invalid_scope: Select distinct explicit store identifiers.'))
        stores = self.env['ydental.access.store'].sudo().browse(store_ids).exists()
        if len(stores) != len(store_ids):
            raise AccessError(self.env._('access_denied: A selected report store is unavailable.'))
        for store in stores:
            self._metric_access(metric, store, export)
        if company_id is not None and (type(company_id) is not int
                or any(store.company_id.id != company_id for store in stores)):
            raise AccessError(self.env._('access_denied: The selected stores do not match the explicit company filter.'))
        if currency_id is not None and (type(currency_id) is not int or currency_id < 1
                or not self.env['res.currency'].sudo().browse(currency_id).exists()):
            raise ValidationError(self.env._('invalid_currency: Select an existing currency.'))
        if currency_id is not None and METRICS[metric][1] != 'settlement':
            raise ValidationError(self.env._('invalid_currency: Currency filtering applies only to money metrics.'))
        if state is not None and (not isinstance(state, str) or len(state) > 50):
            raise ValidationError(self.env._('invalid_state: Select a bounded source state.'))
        bounds = {}
        for store in stores:
            zone = ZoneInfo(store.ydental_timezone)
            bounds[store.id] = [datetime.combine(start, time.min, zone).astimezone(timezone.utc).replace(tzinfo=None),
                datetime.combine(end + timedelta(days=1), time.min, zone).astimezone(timezone.utc).replace(tzinfo=None)]
        return stores, start, end, bounds

    def _bounded(self, model, domain, order='id'):
        rows = self.env[model].sudo().search(domain, order=order, limit=MAX_ROWS + 1)
        if len(rows) > MAX_ROWS:
            raise UserError(self.env._('size_limit: More than 50000 source rows; narrow the dates or store selection. No truncated total was returned.'))
        return rows

    def _canonical_ids(self, ids):
        # Traverse only identities already present in authorized source rows.
        patients = self.env['ydental.patient'].sudo().with_context(active_test=False).browse(list(set(ids)))
        known = {row.id: row for row in patients}
        frontier = patients
        while frontier:
            targets = frontier.ydental_merged_into_id
            frontier = targets.filtered(lambda row: row.id not in known)
            known.update({row.id: row for row in frontier})
        result = {}
        for row in patients:
            current, seen = row, set()
            while current.ydental_merged_into_id:
                if current.id in seen:
                    raise UserError(self.env._('identity_inconsistent: A patient merge chain requires review.'))
                seen.add(current.id)
                current = known[current.ydental_merged_into_id.id]
            result[row.id] = current.id
        return result

    def _row(self, record, store, value=1, unit='count', event_date=False, state=False,
             patient_id=False, **facts):
        return {'source_model': record._name, 'source_id': record.id, 'store_id': store.id,
            'company_id': store.company_id.id, 'value': value, 'unit': unit,
            'event_date': str(event_date) if event_date else '', 'state': state or '',
            'patient_id': patient_id, 'facts': facts}

    def _rows(self, metric, store, start, end, utc_bounds):
        scope = fields.Domain('ydental_store_id', '=', store.id)
        def dates(name):
            return fields.Domain(name, '>=', start) & fields.Domain(name, '<=', end)
        def instants(name):
            return fields.Domain(name, '>=', utc_bounds[0]) & fields.Domain(name, '<', utc_bounds[1])
        rows = []
        if metric in ('arrivals', 'unique_patients'):
            sources = self._bounded('ydental.intake.arrival', scope & dates('ydental_date'))
            canonical = self._canonical_ids(sources.ydental_patient_id.ids)
            return [self._row(row, store, event_date=row.ydental_date,
                patient_id=canonical[row.ydental_patient_id.id], occurred_at=str(row.ydental_occurred_at),
                event_timezone=row.ydental_timezone, source_patient_id=row.ydental_patient_id.id) for row in sources]
        if metric == 'executions':
            sources = self._bounded('ydental.treatment.event', scope & dates('ydental_business_date')
                & fields.Domain('state', '=', 'confirmed')
                & fields.Domain('ydental_category', 'in', self._execution_categories(store)))
            return [self._row(row, store, row.ydental_quantity, 'catalog:%s/uom:%s/kind:%s' % (
                    row.ydental_catalog_id.id, row.ydental_uom_id.id, row.ydental_kind),
                row.ydental_business_date, row.state, row.ydental_patient_id.id,
                execution_id=row.ydental_execution_id.id, document_id=row.ydental_document_id.id,
                actual_at=str(row.ydental_actual_at), actor_id=row.ydental_actor_id.id,
                source_category=row.ydental_category, event_kind=row.ydental_kind,
                price_snapshot_id=row.ydental_price_snapshot_id.id) for row in sources]
        if metric in ('original_billing', 'credits', 'receivables'):
            links = self._bounded('ydental.settlement.source', scope)
            invoices = links.ydental_invoice_id.filtered(lambda row: row.state == 'posted'
                and row.company_id == store.company_id and row.move_type == 'out_invoice')
            targets = invoices
            credit_origins = defaultdict(set)
            if metric == 'credits':
                # All candidates must be linked to an already store-authorized
                # native bill by source, refund, or actual native reconciliation.
                # Invoice-origin text alone is never a cross-store authorizer.
                refunds = self._bounded('ydental.settlement.refund', fields.Domain('ydental_payment_id.ydental_store_id', '=', store.id))
                direct = links.ydental_invoice_id | refunds.ydental_credit_note_ids | refunds.ydental_credit_note_id
                partials = self._bounded('account.partial.reconcile',
                    fields.Domain('debit_move_id', 'in', invoices.line_ids.ids)
                    & fields.Domain('credit_move_id.move_id.move_type', '=', 'out_refund'))
                direct |= partials.credit_move_id.move_id
                for part in partials:
                    credit_origins[part.credit_move_id.move_id.id].add(part.debit_move_id.move_id.id)
                for refund in refunds:
                    for credit in refund.ydental_credit_note_ids | refund.ydental_credit_note_id:
                        credit_origins[credit.id].update(refund.ydental_payment_id.ydental_invoice_ids.filtered(
                            lambda row: row.company_id == credit.company_id and row.partner_id == credit.partner_id
                            and row.currency_id == credit.currency_id and row.name == credit.invoice_origin).ids)
                candidates = self._bounded('account.move', fields.Domain('company_id', '=', store.company_id.id)
                    & fields.Domain('move_type', '=', 'out_refund') & fields.Domain('state', '=', 'posted')
                    & fields.Domain('id', 'in', direct.ids))
                targets = candidates
            for invoice in targets:
                if not invoice.invoice_date or not start <= invoice.invoice_date <= end:
                    continue
                source_rows = links.filtered(lambda row: row.ydental_invoice_id == invoice)
                original_ids = sorted(credit_origins[invoice.id])
                rows.append(self._row(invoice, store,
                    invoice.amount_residual if metric == 'receivables' else invoice.amount_total,
                    'currency:%s' % invoice.currency_id.id, invoice.invoice_date, invoice.state,
                    currency=invoice.currency_id.name, native_number=invoice.name, source_ids=source_rows.ids,
                    original_bill_ids=original_ids, partner_id=invoice.partner_id.id,
                    balance_kind='current_at_query' if metric == 'receivables' else 'period_event',
                    price_versions=source_rows.mapped('ydental_price_version'),
                    receivable_line_ids=invoice.line_ids.filtered(lambda row: row.account_id.account_type == 'asset_receivable').ids))
            return rows
        if metric == 'collections':
            sources = self._bounded('ydental.settlement.payment', scope & dates('ydental_business_date'))
            finance = self.env['ydental.settlement.service']
            channels = finance._effective_channels(sources)
            corrections = self._bounded('ydental.settlement.correction', fields.Domain('ydental_payment_id', 'in', sources.ids))
            correction_ids = defaultdict(list)
            for correction in corrections:
                correction_ids[correction.ydental_payment_id.id].append(correction.id)
            return [self._row(row, store, row.ydental_amount, 'currency:%s' % row.ydental_currency_id.id,
                row.ydental_business_date, 'posted', row.ydental_patient_id.id, currency=row.ydental_currency_id.name,
                actual_at=str(row.ydental_actual_at), entered_at=str(row.ydental_entered_at),
                actor_id=row.ydental_cashier_id.id, original_channel=row.ydental_channel,
                effective_channel=channels[row.id],
                channel_basis='current_corrected_label_with_immutable_original',
                channel_correction_ids=correction_ids[row.id],
                native_payment_id=row.ydental_payment_id.id, invoice_ids=row.ydental_invoice_ids.ids)
                for row in sources if row.ydental_payment_id.move_id.state == 'posted']
        if metric in ('refunds', 'approved_pending'):
            domain = fields.Domain('ydental_payment_id.ydental_store_id', '=', store.id)
            if metric == 'refunds' and self._bounded('ydental.settlement.refund', domain
                    & fields.Domain('ydental_state', '=', 'done')
                    & fields.Domain('ydental_refund_business_date', '=', False)
                    & fields.Domain('ydental_actual_at', '=', False)):
                raise UserError(self.env._('source_dates_incomplete: A completed legacy refund has no verifiable event date. No complete period total can be reported.'))
            domain &= (fields.Domain('ydental_state', '=', 'done') & (
                dates('ydental_refund_business_date') | fields.Domain('ydental_refund_business_date', '=', False)
                & instants('ydental_actual_at')) if metric == 'refunds' else
                fields.Domain('ydental_state', 'in', ['approved', 'failed', 'unknown']) & (
                    instants('ydental_requested_at') | fields.Domain('ydental_requested_at', '=', False) & instants('create_date')))
            sources = self._bounded('ydental.settlement.refund', domain)
            for row in sources:
                if metric == 'refunds' and row.ydental_native_payment_id.move_id.state != 'posted':
                    continue
                event_date = row.ydental_refund_business_date if metric == 'refunds' else row.ydental_requested_at
                date_source = 'refund_business_date' if metric == 'refunds' else 'requested_at'
                if not event_date:
                    stamp = row.ydental_actual_at if metric == 'refunds' else row.create_date
                    event_date = stamp.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()
                    date_source = 'actual_at_local_legacy' if metric == 'refunds' else 'create_date_local_legacy'
                rows.append(self._row(row, store, row.ydental_amount, 'currency:%s' % row.ydental_currency_id.id,
                    event_date,
                    row.ydental_state, row.ydental_payment_id.ydental_patient_id.id,
                    currency=row.ydental_currency_id.name, actual_at=str(row.ydental_actual_at or ''),
                    actor_id=row.ydental_executor_id.id, approver_id=row.ydental_approver_id.id,
                    native_payment_id=row.ydental_native_payment_id.id,
                    credit_note_ids=(row.ydental_credit_note_ids | row.ydental_credit_note_id).ids,
                    original_payment_id=row.ydental_payment_id.id, channel=row.ydental_refund_channel or '',
                    event_date_source=date_source))
            return rows
        if metric == 'consumption':
            sources = self._bounded('ydental.inventory.event', scope & instants('ydental_actual_at')
                & fields.Domain('state', '=', 'done') & fields.Domain('ydental_kind', 'in', ['treatment', 'chairside', 'prescription'])
                & fields.Domain('ydental_move_id.state', '=', 'done'))
            return [self._row(row, store, row.ydental_input_quantity, 'product:%s/lot:%s/uom:%s' % (
                row.ydental_product_id.id, row.ydental_lot_id.id, row.ydental_uom_id.id),
                row.ydental_actual_at, row.state, native_move_id=row.ydental_move_id.id,
                product_id=row.ydental_product_id.id, lot_id=row.ydental_lot_id.id,
                uom_id=row.ydental_uom_id.id, stock_quantity=row.ydental_quantity,
                from_location_id=row.ydental_from_id.id, to_location_id=row.ydental_to_id.id,
                event_kind=row.ydental_kind) for row in sources]
        if metric == 'lab_pending':
            active = ['sent', 'processing', 'received', 'available', 'rework_returned']
            sources = self._bounded('ydental.lab.order', scope & instants('ydental_planned_at') & fields.Domain('state', 'in', active))
            children = self._bounded('ydental.lab.order', scope & fields.Domain('ydental_parent_order_id', 'in', sources.ids)
                & fields.Domain('state', '!=', 'cancelled'))
            superseded = set(children.ydental_parent_order_id.ids)
            return [self._row(row, store, event_date=row.ydental_planned_at, state=row.state,
                patient_id=row.ydental_patient_id.id, parent_order_id=row.ydental_parent_order_id.id,
                owner_id=row.ydental_responsible_id.id, receipt_at=str(row.ydental_receipt_at or ''),
                inventory_event_id=row.ydental_inventory_event_id.id) for row in sources if row.id not in superseded]
        if metric == 'followups':
            sources = self._bounded('ydental.followup', scope & instants('ydental_planned_at')
                & fields.Domain('state', 'in', ['planned', 'to_notify', 'notified']))
            return [self._row(row, store, event_date=row.ydental_planned_at, state=row.state,
                patient_id=row.ydental_patient_id.id, owner_id=row.ydental_responsible_id.id,
                lab_contact_stage=row.ydental_lab_contact_stage or '', appointment_status=row.ydental_appointment_status,
                source_event_id=row.ydental_source_event_id.id) for row in sources]
        return rows

    def _query(self, metric, date_from, date_to, store_ids=None, company_id=None,
               currency_id=None, state=None, page=1, export=False, all_rows=False):
        if type(page) is not int or page < 1:
            raise ValidationError(self.env._('invalid_page: Select a positive page number.'))
        stores, start, end, bounds = self._filters(metric, date_from, date_to, store_ids,
            company_id, currency_id, state, export)
        rows = [row for store in stores for row in self._rows(metric, store, start, end, bounds[store.id])]
        if len(rows) > MAX_ROWS:
            raise UserError(self.env._('size_limit: More than 50000 combined source rows; narrow the scope.'))
        if currency_id is not None:
            rows = [row for row in rows if row['unit'] == 'currency:%s' % currency_id]
        if state:
            rows = [row for row in rows if row['state'] == state]
        totals = defaultdict(float)
        event_counts = defaultdict(int)
        store_totals = defaultdict(lambda: defaultdict(float))
        if metric == 'unique_patients':
            totals['patients'] = len({row['patient_id'] for row in rows})
            for store in stores:
                store_totals[store.id]['patients'] = len({row['patient_id'] for row in rows if row['store_id'] == store.id})
        else:
            for row in rows:
                key = row['unit']
                if metric in ('lab_pending', 'followups'):
                    key += '/state:%s/owner:%s/stage:%s' % (row['state'], row['facts']['owner_id'], row['facts'].get('lab_contact_stage', ''))
                totals[key] += row['value']
                event_counts[key] += 1
                store_totals[row['store_id']][key] += row['value']
        if METRICS[metric][1] == 'settlement':
            for key in totals:
                currency = self.env['res.currency'].sudo().browse(int(key.split(':')[1]))
                totals[key] = currency.round(totals[key])
                for values in store_totals.values():
                    if key in values:
                        values[key] = currency.round(values[key])
        current_store = self.env['ydental.access.service']._scope().ydental_store_id.id
        scope_query = urlencode({'date_from': str(start), 'date_to': str(end),
            'store_ids': ','.join(str(value) for value in stores.ids),
            'company_id': company_id or '', 'currency_id': currency_id or '', 'state': state or ''})
        for row in rows:
            row['native_url'] = '/odoo/%s/%s' % (row['source_model'], row['source_id'])
            row['source_url'] = '/ydental/reports/source/%s/%s?%s' % (metric, row['source_id'], scope_query)
            row['requires_store_switch'] = row['store_id'] != current_store
        query_at = str(fields.Datetime.now())
        filters = {'metric': metric, 'date_from': str(start), 'date_to': str(end), 'store_ids': stores.ids,
            'company_id': company_id, 'currency_id': currency_id, 'state': state,
            'period_or_snapshot': METRICS[metric][2], 'query_at_utc': query_at,
            'historical_asof_supported': False, 'store_timezones_and_utc_bounds': {
                store.id: {'timezone': store.ydental_timezone, 'start_utc': str(bounds[store.id][0]),
                    'end_exclusive_utc': str(bounds[store.id][1])} for store in stores}}
        if metric == 'executions':
            filters['authorized_source_categories_by_store'] = {store.id: self._execution_categories(store) for store in stores}
        self.env['ydental.access.service']._audit('report.export' if export else 'report.view',
            'export', self.env.user, current_store, source='operating_report', after=dict(filters, source_row_count=len(rows)))
        return {'filters': filters, 'title': self.env._(METRICS[metric][0]), 'totals': dict(totals),
            'event_counts_by_unit': dict(event_counts),
            'store_totals': {key: dict(value) for key, value in store_totals.items()},
            'source_row_count': len(rows), 'page': page, 'page_size': 100,
            'rows': rows if export or all_rows else rows[(page - 1) * 100:page * 100]}

    def _options(self):
        access = self.env['ydental.access.service']
        current = access._scope().ydental_store_id
        choices = []
        for metric, (label, _category, timing) in METRICS.items():
            try:
                self._metric_access(metric, current)
            except AccessError:
                continue
            choices.append({'key': metric, 'label': self.env._(label), 'timing': timing})
        return current, choices
