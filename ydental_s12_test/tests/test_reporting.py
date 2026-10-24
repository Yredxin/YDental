from datetime import timedelta
from unittest.mock import patch

from odoo.addons.base.tests.common import DISABLED_MAIL_CREATE_CONTEXT
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import bind, key, setup


@tagged('post_install', '-at_install')
class TestOperatingReports(TransactionCase):
    """Read model totals from genuine synthetic source service events."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env['base'].with_context(**DISABLED_MAIL_CREATE_CONTEXT).env
        synthetic_supply = patch.object(type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        synthetic_supply.start()
        cls.addClassCleanup(synthetic_supply.stop)
        setup(cls)

    def reporting(self, role='doctor'):
        return bind(self, self.users[role]).env['ydental.reporting.service']

    def arrived(self, label='one'):
        patient = self.front.env['ydental.patient.service']._operate('create', {
            'values': {'name': 'S12 report synthetic ' + label + ' ' + key()}}, key())['id']
        arrival = self.front._operate('arrive', {'patient_id': patient}, key())
        return patient, arrival

    def query(self, metric, **values):
        dates = self.group.env['ydental.supply.service']._date(self.stores[0])
        return self.reporting()._query(metric, str(dates), str(dates), **values)

    def test_unique_patient_is_deduplicated_across_authorized_stores_and_arrival_retries(self):
        patient, arrival = self.arrived()
        repeated = self.front._operate('arrive', {'patient_id': patient}, key())
        self.assertEqual(repeated['id'], arrival['id'])
        other = bind(self, self.users['frontdesk'], self.stores[1])
        other._operate('arrive', {'patient_id': patient}, key())
        unique = self.query('unique_patients', store_ids=self.stores.ids)
        arrivals = self.query('arrivals', store_ids=self.stores.ids)
        self.assertEqual(unique['totals'], {'patients': 1})
        self.assertEqual(arrivals['totals'], {'count': 2})
        self.assertEqual(unique['store_totals'][self.stores[0].id], {'patients': 1})
        self.assertEqual(unique['store_totals'][self.stores[1].id], {'patients': 1})
        self.assertEqual(len({row['source_id'] for row in arrivals['rows']}), 2)
        self.assertTrue(all(row['source_model'] == 'ydental.intake.arrival' for row in arrivals['rows']))

    def test_source_and_export_four_combinations_never_grant_source_access_via_export(self):
        self.arrived()
        actor = self.users['none']
        dates = self.group.env['ydental.supply.service']._date(self.stores[0])
        report = bind(self, actor).env['ydental.reporting.service']
        for source_read, export in ((True, True), (True, False), (False, True), (False, False)):
            with self.subTest(source_read=source_read, export=export):
                self.admin._grant(actor.id, self.stores[0].id, {
                    'frontdesk': 'read' if source_read else 'none', 'export': 'write' if export else 'none'})
                if source_read:
                    self.assertEqual(report._query('arrivals', str(dates), str(dates))['totals'], {'count': 1})
                else:
                    with self.assertRaises(AccessError):
                        report._query('arrivals', str(dates), str(dates))
                if source_read and export:
                    self.assertEqual(report._query('arrivals', str(dates), str(dates), export=True)['source_row_count'], 1)
                else:
                    with self.assertRaises(AccessError):
                        report._query('arrivals', str(dates), str(dates), export=True)
        self.admin._grant(actor.id, self.stores[0].id, {'frontdesk': 'read', 'export': 'write'})
        with self.assertRaises(AccessError):
            report._query('arrivals', str(dates), str(dates), store_ids=self.stores.ids)

    def test_pagination_aggregation_drill_and_export_keep_the_same_real_source_collection(self):
        for index in range(102):
            self.arrived(str(index))
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'export': 'write'})
        first = self.query('arrivals')
        second = self.query('arrivals', page=2)
        exported = self.query('arrivals', export=True)
        self.assertEqual(first['source_row_count'], 102)
        self.assertEqual(first['totals'], second['totals'])
        self.assertEqual(first['totals'], exported['totals'])
        self.assertEqual((len(first['rows']), len(second['rows']), len(exported['rows'])), (100, 2, 102))
        self.assertEqual([row['source_id'] for row in first['rows'] + second['rows']],
                         [row['source_id'] for row in exported['rows']])
        self.assertTrue(all('/ydental/reports/source/arrivals/' in row['source_url'] for row in exported['rows']))
        self.assertEqual(first['filters']['period_or_snapshot'], 'period')
        self.assertFalse(first['filters']['historical_asof_supported'])

    def test_store_local_dst_bounds_are_explicit_and_invalid_filters_fail_closed(self):
        self.stores[1].write({'ydental_timezone': 'America/Los_Angeles'})
        report = self.reporting()
        stores, _start, _end, bounds = report._filters('arrivals', '2026-03-08', '2026-03-08', self.stores[1].ids)
        self.assertEqual(stores, self.stores[1])
        self.assertEqual(bounds[stores.id][1] - bounds[stores.id][0], timedelta(hours=23))
        with self.assertRaises(ValidationError):
            report._query('arrivals', '2026-02-30', '2026-03-01')
        with self.assertRaises(ValidationError):
            report._query('arrivals', '2026-03-08', '2026-03-08', store_ids=[True])
        with self.assertRaises(ValidationError):
            report._query('arrivals', '2026-03-08', '2026-03-08', currency_id=self.currency.id)
        with self.assertRaises(AccessError):
            report._query('arrivals', '2026-03-08', '2026-03-08', company_id=self.stores[0].company_id.id + 999999)
