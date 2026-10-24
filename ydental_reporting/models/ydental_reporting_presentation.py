import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.misc import format_datetime, formatLang
from odoo.tools.translate import LazyTranslate

from .ydental_reporting_service import METRICS


_lt = LazyTranslate(__name__)
STATE_LABELS = {
    'posted': _lt('Posted'), 'confirmed': _lt('Confirmed execution'),
    'done': _lt('Completed stock movement'), 'planned': _lt('Follow-up planned'),
    'to_notify': _lt('Awaiting follow-up contact'), 'notified': _lt('Follow-up contacted'),
    'sent': _lt('Dispatched to laboratory; receipt unconfirmed'),
    'processing': _lt('Laboratory processing'), 'received': _lt('Physically received'),
    'available': _lt('Put away; awaiting fitting'),
    'rework_returned': _lt('Returned for rework'),
    'approved': _lt('Approved; not actually refunded'),
    'failed': _lt('Refund execution failed'), 'unknown': _lt('Refund outcome unknown'),
    'waiting': _lt('Awaiting laboratory inventory'), 'ready': _lt('Ready for laboratory contact'),
    'stopped': _lt('Laboratory contact stopped'),
    'cash': _lt('Cash'), 'wechat': _lt('WeChat offline'),
    'alipay': _lt('Alipay offline'), 'card': _lt('Bank card offline'),
    'treatment': _lt('Treatment consumption'), 'chairside': _lt('Chairside medicine'),
    'prescription': _lt('Take-home dispensing'), 'correction': _lt('Correction event'),
    'medical': _lt('Medical source'), 'exam': _lt('Examination source'),
    'pharmacy': _lt('Pharmacy source'),
}
METRIC_STATES = {
    'original_billing': ['posted'], 'credits': ['posted'], 'collections': ['posted'],
    'receivables': ['posted'], 'refunds': ['done'],
    'approved_pending': ['approved', 'failed', 'unknown'], 'executions': ['confirmed'],
    'consumption': ['done'],
    'lab_pending': ['sent', 'processing', 'received', 'available', 'rework_returned'],
    'followups': ['planned', 'to_notify', 'notified'],
}


class YDentalReportingPresentation(models.AbstractModel):
    _inherit = 'ydental.reporting.service'

    def _state_label(self, value, metric):
        if not value:
            return self.env._('Not applicable')
        if value == 'done' and metric == 'refunds':
            return self.env._('Actually refunded')
        if value == 'treatment' and metric == 'executions':
            return self.env._('Treatment execution')
        return self.env._(STATE_LABELS[value]) if value in STATE_LABELS else self.env._('Other recorded state')

    def _selection_options(self, metric, currency_id=None, state=None):
        """List metadata only after the same source check used by each query."""
        if metric not in METRICS:
            raise ValidationError(self.env._('invalid_metric: Select a documented metric.'))
        stores = self.env['ydental.access.store'].sudo().search([
            ('active', '=', True), ('company_id', 'in', self.env.user.sudo().company_ids.ids)], order='name, id')
        authorized = stores.browse()
        for store in stores:
            try:
                self._metric_access(metric, store)
            except AccessError:
                continue
            authorized |= store
        currencies = self.env['res.currency'].sudo().search([('active', '=', True)], order='name')
        if currency_id:
            # A bookmarked existing inactive currency remains an explicit filter.
            currencies |= self.env['res.currency'].sudo().browse(currency_id)
        if state and state not in METRIC_STATES.get(metric, []):
            raise ValidationError(self.env._('invalid_state: The selected source state does not apply to this metric. Clear it or choose an applicable state.'))
        return {
            'stores': [{'id': row.id, 'label': row.name, 'company_id': row.company_id.id,
                        'timezone': row.ydental_timezone} for row in authorized],
            'companies': [{'id': row.id, 'label': row.name} for row in authorized.company_id.sorted('name')],
            'currencies': [{'id': row.id, 'label': row.name} for row in currencies],
            'states': [{'value': value, 'label': self._state_label(value, metric)}
                       for value in METRIC_STATES.get(metric, [])],
            'money': METRICS[metric][1] == 'settlement',
        }

    def _display_number(self, value, currency=None):
        if currency:
            return '%s %s' % (currency.name,
                formatLang(self.env, value, digits=currency.decimal_places, grouping=True))
        return formatLang(self.env, value, digits=0 if float(value).is_integer() else 4, grouping=True)

    def _display_time(self, value, store):
        if not value or value == 'False':
            return self.env._('Not recorded')
        if len(str(value)) == 10:
            return str(value)
        instant = datetime.fromisoformat(str(value))
        if instant.tzinfo:
            instant = instant.astimezone(timezone.utc).replace(tzinfo=None)
        return '%s (%s)' % (format_datetime(self.env, instant,
            tz=store.ydental_timezone, dt_format='yyyy-MM-dd HH:mm:ss'), store.ydental_timezone)

    def _presentation(self, result, detail=False):
        """Enrich an already-authorized result, without changing its API values."""
        metric, filters = result['filters']['metric'], result['filters']
        stores = self.env['ydental.access.store'].sudo().browse(filters['store_ids'])
        stores_by_id = {row.id: row for row in stores}
        rows = result['rows']
        unit_keys = set(result['totals']) | {row['unit'] for row in rows}
        invoice_ids = [row['source_id'] for row in rows if row['source_model'] == 'account.move']
        invoice_links = self._bounded('ydental.settlement.source',
            fields.Domain('ydental_store_id', 'in', stores.ids)
            & fields.Domain('ydental_invoice_id', 'in', invoice_ids)) if invoice_ids else self.env['ydental.settlement.source']
        invoice_patients = {(link.ydental_invoice_id.id, link.ydental_store_id.id): link.ydental_patient_id
                            for link in invoice_links}
        records = {}
        for model in {row['source_model'] for row in rows}:
            records[model] = {record.id: record for record in self.env[model].sudo().browse([
                row['source_id'] for row in rows if row['source_model'] == model])}
        patients = self.env['ydental.patient'].sudo().browse(list({row['patient_id'] for row in rows if row['patient_id']}))
        patients_by_id = {row.id: row for row in patients}
        user_ids = {row['facts'].get(key) for row in rows
            for key in ('owner_id', 'actor_id', 'approver_id') if row['facts'].get(key)}
        user_ids.update(int(part.split(':')[1]) for key in unit_keys for part in key.split('/')
                        if part.startswith('owner:') and part != 'owner:False')
        users = self.env['res.users'].sudo().browse(list(user_ids))
        users_by_id = {row.id: row.name for row in users}
        currencies = self.env['res.currency'].sudo().browse([
            int(key.split('/')[0].split(':')[1]) for key in unit_keys if key.startswith('currency:')])
        currencies_by_id = {row.id: row for row in currencies}
        catalogs = self.env['ydental.intake.catalog'].sudo().browse([
            int(key.split('/')[0].split(':')[1]) for key in unit_keys if key.startswith('catalog:')])
        catalogs_by_id = {row.id: row.name for row in catalogs}
        products = self.env['product.product'].sudo().browse([
            int(key.split('/')[0].split(':')[1]) for key in unit_keys if key.startswith('product:')])
        products_by_id = {row.id: row.display_name for row in products}
        lots = self.env['stock.lot'].sudo().browse(list({int(part.split(':')[1]) for key in unit_keys
            for part in key.split('/') if part.startswith('lot:') and part != 'lot:False'}))
        lots_by_id = {row.id: row.name for row in lots}
        units = self.env['uom.uom'].sudo().browse(list({int(part.split(':')[1]) for key in unit_keys
            for part in key.split('/') if part.startswith('uom:')}))
        units_by_id = {row.id: row.name for row in units}

        def unit_display(key, value):
            parts = dict(part.split(':', 1) for part in key.split('/') if ':' in part)
            currency = currencies_by_id.get(int(parts['currency'])) if 'currency' in parts else None
            label = self.env._('People') if key == 'patients' else self.env._('Events')
            if 'currency' in parts:
                label = currency.name
            if 'catalog' in parts:
                label = '%s / %s / %s' % (catalogs_by_id[int(parts['catalog'])],
                    units_by_id[int(parts['uom'])], self._state_label(parts['kind'], metric))
            if 'product' in parts:
                label = '%s / %s / %s' % (products_by_id[int(parts['product'])],
                    lots_by_id.get(int(parts['lot'])) if parts.get('lot') != 'False' else self.env._('No lot recorded'),
                    units_by_id[int(parts['uom'])])
            if 'state' in parts:
                label = '%s / %s / %s' % (self._state_label(parts['state'], metric),
                    users_by_id.get(int(parts['owner']), self.env._('No responsible person recorded')),
                    self._state_label(parts.get('stage'), metric))
            return {'label': label, 'value': self._display_number(value, currency),
                    'events': result['event_counts_by_unit'].get(key)}

        displayed = []
        for row in rows:
            record = records[row['source_model']][row['source_id']]
            store = stores_by_id[row['store_id']]
            patient = patients_by_id.get(row['patient_id'])
            name = row['facts'].get('native_number') or self.env._('Source record')
            business_url = row['native_url']
            if metric in ('collections', 'refunds', 'approved_pending'):
                payment = record if metric == 'collections' else record.ydental_payment_id
                name = payment.ydental_payment_id.name if metric == 'collections' else (
                    record.ydental_native_payment_id.name or self.env._('Refund request'))
                anchor = 'payment' if metric == 'collections' else 'refund'
                business_url = '/ydental/settlement?%s#%s-%s' % (
                    urlencode({'patient_id': patient.id}), anchor, record.id)
            elif metric in ('original_billing', 'credits', 'receivables'):
                # Names and identity come only from links in this authorized store.
                patient = invoice_patients.get((record.id, store.id))
                if patient:
                    business_url = '/ydental/settlement?%s#invoice-%s' % (
                        urlencode({'patient_id': patient.id}), record.id)
            elif metric == 'lab_pending':
                name = record.ydental_internal_code
            elif metric == 'followups':
                name = record.name
                business_url = '/ydental/followups?followup_id=%s#followup-%s' % (record.id, record.id)
            elif metric == 'consumption':
                name = products_by_id[record.ydental_product_id.id]
                business_url = '/ydental/inventory?event_id=%s#event-%s' % (record.id, record.id)
            elif metric == 'executions':
                name = record.ydental_catalog_id.name
            elif metric in ('arrivals', 'unique_patients'):
                name = self.env._('Actual arrival')
            facts = []
            if metric in ('original_billing', 'credits', 'receivables'):
                facts += [(self.env._('Original amount'), self._display_number(record.amount_total, record.currency_id)),
                          (self.env._('Current receivable'), self._display_number(record.amount_residual, record.currency_id))]
            for key, label in [('actual_at', self.env._('Actually occurred at')),
                               ('entered_at', self.env._('Entered at'))]:
                if row['facts'].get(key):
                    facts.append((label, self._display_time(row['facts'][key], store)))
            for key, label in [('actor_id', self.env._('Actual operator')),
                               ('approver_id', self.env._('Approver')),
                               ('owner_id', self.env._('Responsible person'))]:
                if row['facts'].get(key):
                    facts.append((label, users_by_id[row['facts'][key]]))
            for key, label in [('effective_channel', self.env._('Current corrected channel')),
                               ('original_channel', self.env._('Original collection channel')),
                               ('channel', self.env._('Refund channel')),
                               ('lab_contact_stage', self.env._('Laboratory follow-up stage')),
                               ('source_category', self.env._('Source category'))]:
                if row['facts'].get(key):
                    facts.append((label, self._state_label(row['facts'][key], metric)))
            display = dict(row, source_label=name, store_label=store.name,
                company_label=store.company_id.name,
                patient_label='%s · %s' % (patient.name, patient.ydental_number) if patient else self.env._('Not applicable'),
                state_label=self._state_label(row['state'], metric),
                event_label=self._display_time(row['event_date'], store),
                quantity=unit_display(row['unit'], row['value']),
                business_url=business_url, facts_display=facts,
                trace=json.dumps(row['facts'], ensure_ascii=False, indent=2, sort_keys=True), allocations=[])
            if detail and metric in ('collections', 'refunds', 'approved_pending'):
                allowed_links = self._bounded('ydental.settlement.source',
                    fields.Domain('ydental_store_id', '=', store.id)
                    & fields.Domain('ydental_invoice_id', 'in', payment.ydental_invoice_ids.ids))
                invoices = allowed_links.ydental_invoice_id
                partials = self._bounded('account.partial.reconcile',
                    fields.Domain('credit_move_id', 'in', payment.ydental_payment_id.move_id.line_ids.ids)
                    & fields.Domain('debit_move_id.move_id', 'in', invoices.ids))
                currency = payment.ydental_currency_id
                display['allocations'] = [{'number': invoice.name,
                    'total': self._display_number(invoice.amount_total, currency),
                    'allocated': self._display_number(sum(partials.filtered(
                        lambda part: part.debit_move_id.move_id == invoice).mapped('amount')), currency),
                    'balance': self._display_number(invoice.amount_residual, currency),
                    'url': '/ydental/settlement?%s#invoice-%s' % (
                        urlencode({'patient_id': patient.id}), invoice.id)} for invoice in invoices.sorted(
                            lambda invoice: (invoice.invoice_date, invoice.id))]
            displayed.append(display)
        return {'rows': displayed, 'totals': [unit_display(key, value) for key, value in result['totals'].items()],
            'store_totals': [{'label': stores_by_id[store_id].name,
                'totals': [unit_display(key, value) for key, value in totals.items()]}
                for store_id, totals in result['store_totals'].items()],
            'bounds': [{'label': stores_by_id[store_id].name, **values}
                for store_id, values in filters['store_timezones_and_utc_bounds'].items()],
            'title': result['title'], 'state_label': self._state_label(filters['state'], metric)
                if filters['state'] else self.env._('All applicable source states'),
            'companies': ', '.join(stores.company_id.mapped('name')),
            'scope': ', '.join(stores.mapped('name')),
            'currency': self.env['res.currency'].sudo().browse(filters['currency_id']).name
                if filters['currency_id'] else self.env._('Separate totals per currency or unit')}
