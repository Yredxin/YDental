import csv
import io
from urllib.parse import urlencode
from unittest.mock import patch

from odoo.tests import HttpCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key, setup
from odoo.addons.ydental_treatment_test.tests.test_http import TestClinicalHTTP


@tagged('post_install', '-at_install')
class TestOperatingReportsHTTP(TestClinicalHTTP):
    @classmethod
    def setUpClass(cls):
        HttpCase.setUpClass.__func__(cls)
        supply = patch.object(type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        supply.start()
        cls.addClassCleanup(supply.stop)
        setup(cls)

    def report_source(self):
        patient = self.front.env['ydental.patient.service']._operate('create', {
            'values': {'name': 'S12 synthetic reporting HTTP source'}}, key())['id']
        arrival = self.front._operate('arrive', {'patient_id': patient}, key())
        self.select('doctor')
        date = str(self.group.env['ydental.supply.service']._date(self.stores[0]))
        return arrival['id'], {'metric': 'arrivals', 'date_from': date, 'date_to': date,
                               'store_ids': str(self.stores[0].id)}

    def export(self, values):
        return self.url_open('/ydental/reports/export', data={
            'csrf_token': self.csrf, 'revision': self.revision, **values})

    def test_http_view_drill_and_csv_share_filters_and_source_facts(self):
        arrival_id, arguments = self.report_source()
        report = self.url_open('/ydental/reports?' + urlencode(arguments | {'output': 'json'}))
        self.assertEqual(report.status_code, 200, report.text[:300])
        result = report.json()
        self.assertEqual(result['totals'], {'count': 1})
        self.assertEqual(result['rows'][0]['source_id'], arrival_id)
        source = self.url_open(result['rows'][0]['source_url'])
        self.assertEqual(source.status_code, 200, source.text[:300])
        self.assertIn('ydental.intake.arrival', source.text)
        self.assertEqual(self.export(arguments).status_code, 403)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'export': 'write'})
        exported = self.export(arguments)
        self.assertEqual(exported.status_code, 200, exported.text[:300])
        self.assertIn('text/csv', exported.headers['Content-Type'])
        rows = list(csv.reader(io.StringIO(exported.content.decode('utf-8-sig'))))
        self.assertEqual(rows[1][0], 'filters')
        self.assertIn('store_timezones_and_utc_bounds', rows[1][1])
        self.assertEqual(rows[-1][0], 'ydental.intake.arrival')
        self.assertEqual(int(rows[-1][1]), arrival_id)
        self.assertIn('no-store', exported.headers['Cache-Control'])

    def test_http_export_permission_never_authorizes_unreadable_source_or_other_store(self):
        _arrival, arguments = self.report_source()
        self.select('none')
        self.admin._grant(self.users['none'].id, self.stores[0].id, {'export': 'write'})
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(arguments)).status_code, 403)
        self.assertEqual(self.export(arguments).status_code, 403)
        self.admin._grant(self.users['none'].id, self.stores[0].id, {'frontdesk': 'read'})
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(arguments)).status_code, 200)
        self.assertEqual(self.export(arguments).status_code, 200)
        other_scope = arguments | {'store_ids': ','.join(map(str, self.stores.ids))}
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(other_scope)).status_code, 403)
        self.assertEqual(self.export(other_scope).status_code, 403)
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(arguments | {'metric': 'collections'})).status_code, 403)

    def test_http_invalid_filters_csrf_private_rpc_and_filtered_drill_fail_at_product(self):
        arrival_id, arguments = self.report_source()
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(arguments | {'metric': 'arbitrary_model'})).status_code, 409)
        self.assertEqual(self.url_open('/ydental/reports?' + urlencode(arguments | {'date_from': '2026-02-30'})).status_code, 409)
        denied = self.url_open('/ydental/reports/export', data={'revision': self.revision, **arguments})
        self.assertEqual(denied.status_code, 400)
        self.assertIn('error', self.rpc('ydental.reporting.service', '_query', ['arrivals', arguments['date_from'], arguments['date_to']]))
        source = '/ydental/reports/source/arrivals/%s?' % arrival_id
        invalid_scope = arguments | {'date_from': '2001-01-01', 'date_to': '2001-01-01'}
        self.assertEqual(self.url_open(source + urlencode(invalid_scope)).status_code, 403)
