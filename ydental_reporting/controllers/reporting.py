import csv
import io
import json
from urllib.parse import urlencode

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


HEADERS = [('Cache-Control', 'no-store, private, max-age=0'), ('Pragma', 'no-cache'),
           ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer')]


class YDentalReporting(http.Controller):
    def _request_values(self, values):
        values = dict(values)
        selected = request.httprequest.args.getlist('store_ids')
        if selected:
            values['store_ids'] = ','.join(selected)
        return values

    def _service(self, revision=None):
        request.update_context(lang='zh_CN')
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).with_context(lang='zh_CN').env['ydental.reporting.service']

    def _arguments(self, values):
        arguments = {name: values[name] for name in ('metric', 'date_from', 'date_to')}
        for name in ('company_id', 'currency_id', 'page'):
            if values.get(name):
                arguments[name] = int(values[name])
        if values.get('store_ids'):
            arguments['store_ids'] = [int(value.strip()) for value in values['store_ids'].split(',')]
        if values.get('state'):
            arguments['state'] = values['state']
        return arguments

    @http.route('/ydental/reports/source/<string:metric>/<int:source_id>', type='http', auth='user', methods=['GET'])
    def source(self, metric, source_id, **kwargs):
        try:
            service = self._service()
            values = self._request_values(dict(kwargs, metric=metric))
            result = service._query(**dict(self._arguments(values), all_rows=True))
            rows = [row for row in result['rows'] if row['source_id'] == source_id]
            if not rows:
                raise AccessError(request.env._('access_denied: This source is outside the current authorized report filters.'))
            for row in rows:
                service.env['ydental.access.service']._audit('report.drill', 'export',
                    service.env[row['source_model']].browse(row['source_id']), row['store_id'],
                    source='operating_report', after={'metric': metric, 'filters': result['filters']})
            result['rows'] = rows
            return request.render('ydental_reporting.ydental_operating_report_source', {
                'display': service._presentation(result, detail=True),
                'report': result, 'title': result['title'],
                'return_url': '/ydental/reports?' + urlencode(values)}, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('operating_report.source')
            return self._failure(error, kwargs)

    def _failure(self, error, values):
        status = 403 if isinstance(error, AccessError) else 409
        if values.get('output') == 'json':
            return request.make_json_response({'error': str(error)}, status=status, headers=HEADERS)
        return request.render('ydental_reporting.ydental_operating_report_error',
            {'message': str(error), 'status': status}, status=status, headers=HEADERS)

    @http.route('/ydental/reports', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        try:
            kwargs = self._request_values(kwargs)
            service = self._service(int(kwargs['revision']) if kwargs.get('revision') else None)
            store, choices = service._options()
            if not choices:
                raise AccessError(request.env._('access_denied: No operating report source permission is available.'))
            priority = {'collections': 0, 'refunds': 1, 'receivables': 2}
            choices.sort(key=lambda choice: priority.get(choice['key'], 3))
            today = str(fields.Date.context_today(service.with_context(tz=store.ydental_timezone)))
            values = dict(metric=choices[0]['key'], date_from=today, date_to=today, store_ids=str(store.id))
            values.update({key: value for key, value in kwargs.items() if key in (
                'metric', 'date_from', 'date_to', 'store_ids', 'company_id', 'currency_id', 'state', 'page')})
            result = service._query(**self._arguments(values))
            if kwargs.get('output') == 'json':
                return request.make_json_response(result, headers=HEADERS)
            revision = service.env['ydental.access.service']._scope().ydental_revision
            links = dict(values, revision=revision)
            display = service._presentation(result)
            for row in display['rows']:
                row['source_url'] += '&page=%s' % result['page']
            return request.render('ydental_reporting.ydental_operating_report_page', {
                'report': result, 'choices': choices, 'values': values, 'revision': revision,
                'display': display, 'options': service._selection_options(values['metric'],
                    result['filters']['currency_id'], result['filters']['state']),
                'selected_stores': result['filters']['store_ids'],
                'previous_url': '/ydental/reports?' + urlencode(dict(links, page=max(1, result['page'] - 1))),
                'next_url': '/ydental/reports?' + urlencode(dict(links, page=result['page'] + 1))}, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('operating_report.view')
            return self._failure(error, kwargs)

    @http.route('/ydental/reports/export', type='http', auth='user', methods=['POST'])
    def export(self, revision, **kwargs):
        try:
            service = self._service(int(revision))
            result = service._query(**dict(self._arguments(kwargs), export=True))
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            writer.writerow(['YDental operating report; synthetic configuration subject to business review'])
            writer.writerow(['filters', json.dumps(result['filters'], ensure_ascii=False, sort_keys=True)])
            writer.writerow(['totals_by_unit', json.dumps(result['totals'], ensure_ascii=False, sort_keys=True)])
            writer.writerow(['event_counts_by_unit', json.dumps(result['event_counts_by_unit'], ensure_ascii=False, sort_keys=True)])
            columns = ['source_model', 'source_id', 'store_id', 'company_id', 'value', 'unit', 'event_date', 'state', 'patient_id', 'facts', 'source_url']
            writer.writerow(columns)
            for row in result['rows']:
                cells = []
                for name in columns:
                    value = row[name]
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict) else str(value)
                    # Plain source text must not become a spreadsheet formula.
                    cells.append("'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r')) else value)
                writer.writerow(cells)
            return request.make_response(output.getvalue().encode('utf-8-sig'), headers=HEADERS + [
                ('Content-Type', 'text/csv; charset=utf-8'), ('Content-Disposition', 'attachment; filename="ydental-operating-report.csv"')])
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('operating_report.export')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)
