"""Offline CREATE boundary tests; fake connection only, no database imports."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from s10_lc2_evidence import CLUSTER
from s10_lc2_runtime import create_targets


class FakeBudget:
    def __init__(self):
        self.counts = {}

    def consume(self, kind):
        self.counts[kind] = self.counts.get(kind, 0) + 1


class FakeMaintenance:
    def __init__(self, fail_create=None, idle=True):
        self.autocommit = False
        self.closed = False
        self.statements = []
        self.create_count = 0
        self.fail_create, self.idle = fail_create, idle
        self.last_query = ''

    def get_transaction_status(self):
        return 0 if self.idle else 2

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params=None):
        if not self.autocommit:
            raise AssertionError('query before explicit autocommit')
        self.statements.append(query)
        self.last_query = query
        if query.startswith('CREATE DATABASE'):
            self.create_count += 1
            if self.fail_create == self.create_count:
                raise RuntimeError('synthetic CREATE failure')

    def fetchone(self):
        if 'system_identifier' in self.last_query:
            return (CLUSTER, 'odoo')
        if self.create_count == 0:
            return (2144127,)
        return (900000 + self.create_count,)

    def fetchall(self):
        return []

    def close(self):
        self.closed = True


class CreateBoundaryCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lc2-create-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.targets = [{'database': 'ydental_s10_test_20261017120000_1234abcd', 'role': 'main'},
                        {'database': 'ydental_s10_test_20261017120000_1234abce', 'role': 'scratch'}]
        self.credentials = {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}

    def test_two_creates_share_exactly_one_idle_autocommit_connection(self):
        connection, calls, budget = FakeMaintenance(), [], FakeBudget()

        def connect(**kwargs):
            calls.append(kwargs)
            return connection

        created = create_targets(connect, self.credentials, targets=self.targets,
                                 directory=self.directory / 'window', budget=budget,
                                 main_admission={'copy_admission': True})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['dbname'], 'postgres')
        self.assertEqual(connection.create_count, 2)
        self.assertTrue(connection.closed)
        self.assertEqual([item['role'] for item in created], ['main', 'scratch'])
        self.assertEqual(budget.counts, {'maintenance': 1, 'create': 2})
        commands = [sql for sql in connection.statements if sql.startswith('CREATE DATABASE')]
        self.assertIn('TEMPLATE "ydental_s10_test_20261017080710_2494c102"', commands[0])
        self.assertIn('TEMPLATE template0', commands[1])

    def test_create_failure_preserves_first_success_and_never_retries(self):
        connection, budget = FakeMaintenance(fail_create=2), FakeBudget()
        with self.assertRaisesRegex(RuntimeError, 'synthetic CREATE failure'):
            create_targets(lambda **kw: connection, self.credentials, targets=self.targets,
                           directory=self.directory / 'window', budget=budget,
                           main_admission={'copy_admission': True})
        self.assertTrue(connection.closed)
        self.assertEqual(connection.create_count, 2)
        self.assertTrue((self.directory / 'window/main-created.json').exists())
        self.assertFalse((self.directory / 'window/scratch-created.json').exists())
        self.assertFalse(any(sql.startswith(('DROP ', 'ALTER ')) for sql in connection.statements))

    def test_nonidle_or_unadmitted_state_refuses_before_create(self):
        connection = FakeMaintenance(idle=False)
        with self.assertRaisesRegex(RuntimeError, 'IDLE_AUTOCOMMIT'):
            create_targets(lambda **kw: connection, self.credentials, targets=self.targets,
                           directory=self.directory / 'nonidle', budget=FakeBudget(),
                           main_admission={'copy_admission': True})
        self.assertEqual(connection.statements, [])
        self.assertTrue(connection.closed)
        calls = []
        with self.assertRaisesRegex(RuntimeError, 'MAIN_COPY_NOT_ADMITTED'):
            create_targets(lambda **kw: calls.append(kw), self.credentials, targets=self.targets,
                           directory=self.directory / 'no-admission', budget=FakeBudget(), main_admission={})
        self.assertEqual(calls, [])

    def test_unpersisted_create_intent_refuses_before_mutation(self):
        connection = FakeMaintenance()
        with patch('s10_lc2_runtime.safe_plain', return_value=False), self.assertRaisesRegex(RuntimeError, 'CREATE_INTENT_NOT_PERSISTED'):
            create_targets(lambda **kw: connection, self.credentials, targets=self.targets,
                           directory=self.directory / 'window', budget=FakeBudget(),
                           main_admission={'copy_admission': True})
        self.assertEqual(connection.create_count, 0)
        self.assertTrue(connection.closed)

    def test_copy_source_oid_drift_stops_before_any_create(self):
        connection = FakeMaintenance()
        original_fetchone = connection.fetchone

        def changed_source():
            if connection.last_query == 'SELECT oid FROM pg_database WHERE datname=%s':
                return (99,)
            return original_fetchone()

        connection.fetchone = changed_source
        with self.assertRaisesRegex(RuntimeError, 'COPY_SOURCE_OID_DRIFT'):
            create_targets(lambda **kw: connection, self.credentials, targets=self.targets,
                           directory=self.directory / 'window', budget=FakeBudget(),
                           main_admission={'copy_admission': True})
        self.assertEqual(connection.create_count, 0)
        self.assertTrue(connection.closed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
