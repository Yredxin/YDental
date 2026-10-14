"""Offline-only tests for the C1-R2 bounded witness."""

import unittest

from s10_c1_r2_contract import classify_sql, commit_slot, lock_order


class C1R2ContractTest(unittest.TestCase):
    def test_table_then_group_order(self):
        self.assertTrue(lock_order(['inventory_advisory_lock', 'warehouse_table_lock',
                                    'group_user_row_lock']))
        self.assertFalse(lock_order(['group_user_row_lock', 'warehouse_table_lock']))

    def test_sql_projection_omits_parameters(self):
        self.assertEqual(classify_sql('LOCK TABLE stock_warehouse IN SHARE ROW EXCLUSIVE MODE'),
                         'warehouse_table_lock')
        self.assertEqual(classify_sql('SELECT id FROM res_groups WHERE id = %s FOR UPDATE'),
                         'group_user_row_lock')
        self.assertIsNone(classify_sql('SELECT password FROM private_table'))

    def test_two_commit_budget(self):
        self.assertEqual(commit_slot([], 'baseline'), 1)
        self.assertEqual(commit_slot(['baseline'], 'warehouse'), 2)
        for prior, requested in (([], 'warehouse'), (['baseline'], 'baseline'),
                                 (['baseline', 'warehouse'], 'warehouse')):
            with self.assertRaises(ValueError):
                commit_slot(prior, requested)


if __name__ == '__main__':
    unittest.main()
