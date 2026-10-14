"""SIMULATED checks of the actual S07 _setup body; no Odoo or database import."""

import ast
from pathlib import Path
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ydental_inventory/models/ydental_inventory_service.py'


class AccessError(Exception):
    pass


class UserError(Exception):
    pass


class ValidationError(Exception):
    pass


def actual_setup():
    tree = ast.parse(SOURCE.read_text())
    model = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                 and n.name == 'YDentalInventoryService')
    method = next(n for n in model.body if isinstance(n, ast.FunctionDef) and n.name == '_setup')
    code = compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(SOURCE), 'exec')
    namespace = {'AccessError': AccessError, 'UserError': UserError, 'ValidationError': ValidationError}
    exec(code, namespace)
    return namespace['_setup']


class Harness:
    def __init__(self, *, admin, counts, multi_warehouse=False, multi_location=False,
                 warehouse_failure=False, existing=False):
        self.company = Mock(id=11)
        self.store = Mock(id=21, name='Synthetic Store', company_id=self.company)
        self.multi_warehouse = object()
        self.multi_location = object()
        self.user = Mock()
        self.user.implied_ids = set()
        if multi_warehouse:
            self.user.implied_ids.add(self.multi_warehouse)
        if multi_location:
            self.user.implied_ids.add(self.multi_location)
        self.user.sudo.return_value = self.user
        self.user._apply_group.side_effect = self.user.implied_ids.add
        self.env = Mock()
        self.env._.side_effect = lambda text: text
        self.env.is_system.return_value = admin
        self.env.ref.side_effect = {
            'base.group_user': self.user,
            'stock.group_stock_multi_warehouses': self.multi_warehouse,
            'stock.group_stock_multi_locations': self.multi_location,
        }.get
        self.config = Mock()
        self.config.search.return_value = Mock(id=88) if existing else False
        self.config._new.return_value = Mock(id=89)
        self.warehouse = Mock()
        self.warehouse._read_group.return_value = [(Mock(id=company_id), count)
                                                   for company_id, count in counts]
        native_record = Mock(id=55)
        def native_create(_values):
            if self.multi_location in self.user.implied_ids:
                self.user.implied_ids.add(self.multi_warehouse)
            return native_record
        self.warehouse.with_company.return_value.create.side_effect = native_create
        if warehouse_failure:
            self.warehouse.with_company.return_value.create.side_effect = UserError('native failure')
        self.location = Mock()
        self.location.with_company.return_value.create.return_value = Mock(id=66)
        self.models = {'config': self.config}
        self.natives = {'stock.warehouse': self.warehouse, 'stock.location': self.location}

    def _model(self, model):
        return self.models[model]

    def _native(self, model):
        return self.natives[model]

    def _text(self, value):
        return value

    def run(self):
        return actual_setup()(self, self.store, 'SYN')


class ActualBodyTests(unittest.TestCase):
    def test_second_warehouse_requires_system_authority(self):
        fixture = Harness(admin=False, counts=[(11, 1)])
        with self.assertRaises(AccessError):
            fixture.run()
        fixture.warehouse.with_company.return_value.create.assert_not_called()
        fixture.user._apply_group.assert_not_called()

    def test_admin_enables_only_stock_location_group(self):
        fixture = Harness(admin=True, counts=[(11, 1)])
        result = fixture.run()
        self.assertEqual(result['warehouse_id'], 55)
        fixture.user._apply_group.assert_called_once_with(fixture.multi_location)
        fixture.warehouse.with_company.return_value.create.assert_called_once()

    def test_existing_multiwarehouse_allows_ordinary_setup(self):
        fixture = Harness(admin=False, counts=[(11, 1)], multi_warehouse=True,
                          multi_location=True)
        fixture.run()
        fixture.user._apply_group.assert_not_called()

    def test_inconsistent_native_group_state_rejected(self):
        fixture = Harness(admin=True, counts=[(11, 1)], multi_warehouse=True)
        with self.assertRaises(UserError):
            fixture.run()
        fixture.warehouse.with_company.return_value.create.assert_not_called()

    def test_other_company_global_transition_requires_admin(self):
        fixture = Harness(admin=False, counts=[(11, 0), (12, 2)])
        with self.assertRaises(AccessError):
            fixture.run()

    def test_first_warehouse_needs_no_global_change(self):
        fixture = Harness(admin=False, counts=[(11, 0)])
        fixture.run()
        fixture.user._apply_group.assert_not_called()

    def test_existing_setup_remains_idempotent(self):
        fixture = Harness(admin=False, counts=[(11, 1)], existing=True)
        self.assertEqual(fixture.run(), {'id': 88})
        fixture.warehouse._read_group.assert_not_called()

    def test_native_failure_propagates_without_config(self):
        fixture = Harness(admin=True, counts=[(11, 1)], warehouse_failure=True)
        with self.assertRaisesRegex(UserError, 'native failure'):
            fixture.run()
        fixture.config._new.assert_not_called()

    def test_forbidden_product_and_settings_calls_absent(self):
        source = ast.get_source_segment(SOURCE.read_text(), next(
            n for c in ast.parse(SOURCE.read_text()).body if isinstance(c, ast.ClassDef)
            and c.name == 'YDentalInventoryService' for n in c.body
            if isinstance(n, ast.FunctionDef) and n.name == '_setup'))
        self.assertNotIn('res.config.settings', source)
        self.assertNotIn('product.pricelist', source)
        self.assertNotIn('ydental_intake_mutation', source)


if __name__ == '__main__':
    unittest.main()
