"""Offline contract for the S07 warehouse preflight; no Odoo/database import."""

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).resolve().parents[1] / 'ydental_inventory/models/ydental_inventory_service.py'
module = ast.parse(SOURCE.read_text())
service = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == 'YDentalInventoryService')
setup = next(node for node in service.body if isinstance(node, ast.FunctionDef) and node.name == '_setup')
scope = {'UserError': type('UserError', (Exception,), {}), 'ValidationError': ValueError}
exec(compile(ast.Module(body=[setup], type_ignores=[]), str(SOURCE), 'exec'), scope)


class Record:
    def __init__(self, record_id, **fields):
        self.id = record_id
        self.fields = fields
        self.implied_ids = SimpleNamespace(ids=[])

    def write(self, values):
        self.fields.update(values)


class FakeService:
    _setup = scope['_setup']

    def __init__(self, counts, groups):
        self.created = []
        self.locks = []
        self.company = Record(10)
        self.store = Record(20, name='Test store')
        self.store.name = 'Test store'
        self.store.company_id = self.company
        self.group_user = Record(1)
        self.group_user.implied_ids.ids = list(groups)
        self.refs = {
            'base.group_user': self.group_user,
            'stock.group_stock_multi_warehouses': Record(2),
            'stock.group_stock_multi_locations': Record(3),
        }
        self.counts = [(SimpleNamespace(id=company), count) for company, count in counts.items()]
        self.env = SimpleNamespace(
            cr=SimpleNamespace(execute=lambda query, *args: self.locks.append(query)),
            ref=self.refs.__getitem__,
            _=lambda message: message,
        )

    def _text(self, text):
        return text

    def _model(self, name):
        if name == 'config':
            return SimpleNamespace(search=lambda *args, **kwargs: False,
                                   _new=lambda vals: SimpleNamespace(id=90))
        raise AssertionError(name)

    def _native(self, name):
        if name == 'stock.warehouse':
            return SimpleNamespace(_read_group=lambda *args, **kwargs: self.counts,
                                   with_company=lambda company: SimpleNamespace(create=self._create_warehouse))
        if name == 'stock.location':
            return SimpleNamespace(with_company=lambda company: SimpleNamespace(create=self._create_location))
        raise AssertionError(name)

    def _create_warehouse(self, vals):
        self.created.append(('warehouse', vals))
        warehouse = Record(30)
        warehouse.lot_stock_id = Record(31)
        warehouse.view_location_id = Record(32)
        return warehouse

    def _create_location(self, vals):
        self.created.append(('location', vals))
        return Record(40 + len(self.created))


class WarehousePreflightTest(unittest.TestCase):
    def test_missing_both_groups_rejects_before_create(self):
        fake = FakeService({10: 1}, [])
        with self.assertRaisesRegex(scope['UserError'], 'configuration_required'):
            fake._setup(fake.store, 'NEW')
        self.assertEqual(fake.created, [])
        self.assertEqual(fake.group_user.implied_ids.ids, [])

    def test_missing_location_rejects_before_create(self):
        fake = FakeService({10: 1}, [2])
        with self.assertRaisesRegex(scope['UserError'], 'Storage Locations'):
            fake._setup(fake.store, 'NEW')
        self.assertEqual(fake.created, [])

    def test_preconfigured_groups_allow_second_warehouse(self):
        fake = FakeService({10: 1}, [2, 3])
        result = fake._setup(fake.store, 'NEW')
        self.assertEqual(result['warehouse_id'], 30)
        self.assertEqual(len(fake.created), 8)
        self.assertEqual(fake.group_user.implied_ids.ids, [2, 3])
        self.assertEqual(fake.locks, ['LOCK TABLE stock_warehouse IN SHARE ROW EXCLUSIVE MODE',
                                      'SELECT id FROM res_groups WHERE id = %s FOR UPDATE'])

    def test_other_company_second_warehouse_requires_preconfiguration(self):
        fake = FakeService({11: 2}, [])
        with self.assertRaisesRegex(scope['UserError'], 'configuration_required'):
            fake._setup(fake.store, 'NEW')
        self.assertEqual(fake.created, [])

    def test_native_group_change_is_rejected(self):
        fake = FakeService({10: 1}, [2, 3])
        original = fake._create_warehouse

        def change_groups(vals):
            warehouse = original(vals)
            fake.group_user.implied_ids.ids = [2]
            return warehouse

        fake._create_warehouse = change_groups
        with self.assertRaisesRegex(scope['UserError'], 'changed global user groups'):
            fake._setup(fake.store, 'NEW')
        self.assertEqual(len(fake.created), 1)

    def test_first_warehouse_rejects_group_removal_path(self):
        fake = FakeService({}, [2, 3])
        with self.assertRaisesRegex(scope['UserError'], 'conflicts'):
            fake._setup(fake.store, 'NEW')
        self.assertEqual(fake.created, [])


if __name__ == '__main__':
    unittest.main()
