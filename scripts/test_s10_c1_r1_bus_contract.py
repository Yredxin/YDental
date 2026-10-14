"""Offline Bus projection tests; no Odoo or database connection."""

import unittest

from s10_c1_r1_bus_contract import bus_stage, project_intent


class BusContractTest(unittest.TestCase):
    def test_preparation_row_is_recorded_without_failing_product(self):
        self.assertEqual(bus_stage('after_catalog_create', 1, ()), 'PREPARATION_BUS_RECORDED')

    def test_prior_user_intent_does_not_become_warehouse_intent(self):
        user = project_intent(('synthetic_db', 'res.users', 91), 'mail.record/insert', {91: 'settings_actor'})
        self.assertEqual(user, {'type': 'mail.record/insert', 'target_model': 'res.users',
                                'scope': 'settings_actor'})
        self.assertEqual(bus_stage('warehouse_setup', 0, ()), 'NO_WAREHOUSE_BUS')

    def test_stock_group_sync_is_explicit_exception(self):
        self.assertEqual(bus_stage('warehouse_setup', 1, ('stock_group_sync',)),
                         'UNEXPECTED_STOCK_GROUP_SYNC')

    def test_unknown_warehouse_bus_is_recorded_without_a_false_whitelist(self):
        self.assertEqual(bus_stage('warehouse_setup', 1, ()), 'WAREHOUSE_BUS_RECORDED')

    def test_payload_and_identifiers_are_not_projected(self):
        projected = project_intent(('private_db', 'res.users', 91), 'mail.record/insert', {91: 'actor'})
        self.assertNotIn('private_db', str(projected))
        self.assertNotIn('91', str(projected))
        self.assertEqual(projected['scope'], 'actor')

    def test_unsafe_type_does_not_pass_through(self):
        projected = project_intent(('db', 'res.users', 1), 'token@example.invalid', {})
        self.assertEqual(projected['type'], 'NOT_CAPTURED_UNSAFE')


if __name__ == '__main__':
    unittest.main()
