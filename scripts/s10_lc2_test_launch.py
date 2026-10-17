"""Offline launch-boundary and exact-owned-process cleanup tests, no sockets/apps."""
import configparser
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from s10_lc2_evidence import CLUSTER, CORE, save_once
from s10_lc2_launch import OwnedApplication, ROOT, dependency_preflight, environment, launch_guard


class FakeProcess:
    pid = 123456

    def __init__(self):
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def wait(self, timeout):
        return self.returncode


class LaunchCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lc2-launch-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.stop_patch = patch('s10_lc2_launch.STOP', self.directory / 'synthetic-STOP.json')
        self.stop_patch.start()
        self.addCleanup(self.stop_patch.stop)
        self.failure_patch = patch('s10_lc2_targets._DISPATCH_FAILURE', None)
        self.failure_patch.start()
        self.addCleanup(self.failure_patch.stop)
        self.database = 'ydental_s10_test_20261017120000_1234abcd'

    def fake_application(self):
        app = object.__new__(OwnedApplication)
        app.action = 'main-service'
        app.marker = {'port': 18411, 'database': self.database, 'oid': 123}
        app.directory = self.directory
        app.run = self.directory
        app.command = ['synthetic-application-command']
        app.env = {'YDENTAL_PRODUCT_COMMIT': 'synthetic-product', 'YDENTAL_TEST_COMMIT': 'synthetic-test',
                   'YDENTAL_RUN_ID': 'synthetic-run'}
        app.event_guard = None
        app.process = None
        app.streams = []
        app.started = time.monotonic()
        app.budget = MagicMock()
        return app

    def test_actual_child_metadata_and_import_under_exact_application_environment(self):
        report = dependency_preflight(environment(self.directory, 'synthetic-product', 'synthetic-test'),
                                      self.directory)
        self.assertFalse(report['odoo_imported'])
        self.assertFalse(report['database_connection_performed'])
        self.assertEqual(report['cwd'], str(ROOT))
        phone = next(item for item in report['dependencies'] if item['module'] == 'phonenumbers')
        self.assertEqual(phone['version'], '9.0.16')
        self.assertTrue(Path(phone['import_file']).is_relative_to(ROOT / '.local/s04-deps'))
        self.assertEqual(Path(report['python_executable']).resolve(), (ROOT.parent / '.venv/bin/python').resolve())

    def test_controlled_application_path_does_not_inherit_external_pythonpath(self):
        with patch.dict('os.environ', {'PYTHONPATH': '/unapproved/synthetic-path'}):
            actual = environment(self.directory, 'synthetic-product', 'synthetic-test')
        self.assertEqual(actual['PYTHONPATH'], str(ROOT / 'scripts') + ':' + str(ROOT / '.local/s04-deps'))
        self.assertEqual(actual['PYTHONDONTWRITEBYTECODE'], '1')

    def test_start_evidence_failure_reaps_exact_owned_process(self):
        app, process = self.fake_application(), FakeProcess()
        with patch('s10_lc2_launch.socket.socket'), patch('s10_lc2_launch.subprocess.Popen', return_value=process), \
                patch('s10_lc2_launch.append_plain', side_effect=OSError('synthetic persistence failure')):
            with self.assertRaisesRegex(OSError, 'synthetic persistence failure'):
                app.start([])
        self.assertTrue(process.terminated)
        self.assertEqual(process.returncode, -15)
        self.assertEqual(app.streams, [])

    def test_primary_persistence_failure_still_reaps_and_preserves_original(self):
        app, process = self.fake_application(), FakeProcess()
        original = OSError('synthetic child-start persistence failure')
        with patch('s10_lc2_launch.socket.socket'), patch('s10_lc2_launch.subprocess.Popen', return_value=process), \
                patch('s10_lc2_launch.append_plain', side_effect=original), \
                patch('s10_lc2_launch.save_primary', side_effect=OSError('synthetic primary persistence failure')):
            with self.assertRaises(OSError) as caught:
                app.start([])
        self.assertIs(caught.exception, original)
        self.assertTrue(process.terminated)
        self.assertEqual(process.returncode, -15)

    def test_argument_override_refused_before_budget_or_process(self):
        for override in [['-d', 'old_database'], ['--db_maxconn=100'], ['shell'], ['--http-port=8069']]:
            app = self.fake_application()
            with patch('s10_lc2_launch.subprocess.Popen') as popen:
                with self.assertRaisesRegex(ValueError, 'APPLICATION_ARGUMENT_OVERRIDE_REFUSED'):
                    app.start(override)
            app.budget.consume.assert_not_called()
            popen.assert_not_called()

    def test_global_storage_failure_during_wait_reaps_owned_process(self):
        app, process = self.fake_application(), FakeProcess()
        app.process = process
        app.budget.check_storage.side_effect = RuntimeError('synthetic global storage pause')
        with self.assertRaisesRegex(RuntimeError, 'synthetic global storage pause'):
            app.wait(1200)
        self.assertTrue(process.terminated)

    def test_marker_hash_and_pool_change_refused_before_any_process(self):
        run_root = self.directory / 'runs'
        run = run_root / self.database
        run.mkdir(mode=0o700, parents=True)
        (run / 'diagnostics').mkdir(mode=0o700)
        parser = configparser.ConfigParser(interpolation=None)
        parser['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
            'db_name': self.database, 'dbfilter': '^' + self.database + '$',
            'workers': '0', 'max_cron_threads': '0', 'db_maxconn': '5',
            'http_interface': '127.0.0.1', 'http_port': '18411',
            'data_dir': str(run / 'data'), 'logfile': str(run / 'odoo-native.log'),
            'log_config': str(ROOT / 'config/logging-s10.example.json'),
            'addons_path': str(ROOT.parent / 'addons') + ',' + str(ROOT)}
        config = run / 'odoo.conf'
        with config.open('w') as stream:
            parser.write(stream)
        marker = {'database': self.database, 'oid': 123, 'cluster': CLUSTER, 'core': CORE,
                  'product_commit': 'synthetic-product', 'test_commit': 'synthetic-test',
                  'role': 'scratch', 'lc2_role': 'scratch', 'port': 18411,
                  'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest()}
        save_once(run / 'database.json', marker)
        plan = self.directory / 'plan.json'
        save_once(plan, {'targets': [{'database': self.database, 'role': 'scratch', 'port': 18411}]})
        dispatch = {'allowed_actions': ['scratch-tests', 'main-service'], 'allowed_target_names': [self.database]}
        with patch('s10_lc2_launch.PLAN', plan), patch('s10_lc2_launch.RUN_ROOT', run_root), \
                patch('s10_lc2_launch.STOP', self.directory / 'STOP'), \
                patch('s10_lc2_launch.runtime_gate', return_value=dispatch), \
                patch('s10_lc2_launch.subprocess.Popen') as popen:
            with self.assertRaisesRegex(RuntimeError, 'APPLICATION_ROLE_ACTION_DRIFT'):
                launch_guard(marker, approval='synthetic-only', product_commit='synthetic-product',
                             test_commit='synthetic-test', action='main-service')
            with self.assertRaisesRegex(RuntimeError, 'APPLICATION_MARKER_DRIFT'):
                launch_guard(marker, approval='synthetic-only', product_commit='synthetic-product',
                             test_commit='different-test', action='scratch-tests')
            with self.assertRaisesRegex(RuntimeError, 'APPLICATION_CONFIG_BOUNDARY_DRIFT'):
                launch_guard(marker, approval='synthetic-only', product_commit='synthetic-product',
                             test_commit='synthetic-test', action='scratch-tests')
        popen.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
