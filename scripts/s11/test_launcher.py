import importlib.util
import datetime as dt
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


LAUNCHER = Path(__file__).with_name('launcher.py')
SPEC = importlib.util.spec_from_file_location('ydental_s11_launcher', LAUNCHER)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class LauncherSupervisorTests(unittest.TestCase):
    def test_server_address_requires_a_valid_non_empty_ip(self):
        self.assertEqual(launcher.parse_server_address('172.18.0.2/32', 'server'), '172.18.0.2')
        self.assertEqual(launcher.parse_server_address('::1', 'server'), '::1')
        for value in (None, '', 'not-an-ip'):
            with self.subTest(value=value), self.assertRaises(launcher.Refusal):
                launcher.parse_server_address(value, 'server')

    def test_listener_check_allows_refused_connect_but_rejects_active_listener(self):
        with patch.object(launcher.socket, 'socket') as socket_factory:
            sock = socket_factory.return_value
            sock.connect_ex.return_value = errno.ECONNREFUSED
            launcher.validate_loopback_port()
            sock.close.assert_called_once()

        with patch.object(launcher.socket, 'socket') as socket_factory:
            sock = socket_factory.return_value
            sock.connect_ex.return_value = 0
            with self.assertRaisesRegex(launcher.Refusal, 'active TCP listener'):
                launcher.validate_loopback_port()

    def test_odoo_config_uses_stable_private_s11_filestore(self):
        with tempfile.TemporaryDirectory(prefix='s11-config-test-') as temporary:
            root = Path(temporary)
            private = root / 'private'
            private.mkdir(mode=0o700)
            run_dir = root / 'run'
            run_dir.mkdir(mode=0o700)
            with (patch.object(launcher, 'PRIVATE_ROOT', private),
                  patch.object(launcher, 'DATA_DIR', private / 'data'),
                  patch.object(launcher, 'CORE_ADDONS', root / 'core-addons'),
                  patch.object(launcher, 'REPO_ROOT', root)):
                config_path = launcher.render_odoo_config(
                    {'host': '127.0.0.1', 'port': 5432, 'user': 'synthetic', 'password': 'test-only'},
                    run_dir,
                )
            parser = launcher.configparser.ConfigParser(interpolation=None)
            parser.read(config_path)
            self.assertEqual(parser['options']['data_dir'], str(private / 'data'))
            self.assertTrue((private / 'data').is_dir())
            self.assertEqual(os.stat(private / 'data').st_mode & 0o777, 0o700)
            self.assertEqual(os.stat(config_path).st_mode & 0o777, 0o600)

    def test_owner_match_accepts_relative_invocation_of_exact_launcher(self):
        relative_script = os.path.relpath(launcher.SCRIPT_PATH, Path.cwd())
        with (patch.object(launcher, 'proc_start_ticks', return_value=1234),
              patch.object(launcher, 'proc_cmdline', return_value=[sys.executable, relative_script, 'start'])):
            self.assertTrue(launcher.own_process_matches(42, 1234, expected_script=True))

    def test_owner_match_rejects_different_script_with_same_basename(self):
        other_script = Path('/tmp/launcher.py')
        with (patch.object(launcher, 'proc_start_ticks', return_value=1234),
              patch.object(launcher, 'proc_cmdline', return_value=[sys.executable, str(other_script), 'start'])):
            self.assertFalse(launcher.own_process_matches(42, 1234, expected_script=True))

    def test_owned_start_path_writes_exit_receipt_and_clears_only_its_owner(self):
        with tempfile.TemporaryDirectory(prefix='s11-launcher-test-') as temporary:
            root = Path(temporary)
            runs = root / 'runs'
            active = root / 'active.json'
            fake_odoo = root / 'fake_odoo.py'
            fake_odoo.write_text("import os; os.write(1, b'synthetic child exit\\n')\n", encoding='utf-8')
            runtime = {'scope': {
                'id': 'SYNTHETIC-TEST-SCOPE',
                'expires_at_utc': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(),
            }}
            database = {'host': '127.0.0.1', 'port': 5432, 'user': 'synthetic', 'password': 'test-only'}

            def render_config(_database, run_dir):
                config = run_dir / 'odoo.conf'
                config.write_text('[options]\\n', encoding='utf-8')
                config.chmod(0o600)
                return config

            with (patch.object(launcher, 'RUNS', runs),
                  patch.object(launcher, 'ACTIVE', active),
                  patch.object(launcher, 'ODOO_ROOT', root),
                  patch.object(launcher, 'ODOO_BIN', fake_odoo),
                  patch.object(launcher, 'PYTHON', Path(sys.executable)),
                  patch.object(launcher, 'validate_pair', return_value=(
                      runtime, {}, database, launcher.EXPECTED_BRANCH, 'a' * 40)),
                  patch.object(launcher, 'validate_loopback_port'),
                  patch.object(launcher, 'render_odoo_config', side_effect=render_config)):
                self.assertEqual(launcher.start_service(), 0)

            self.assertFalse(active.exists())
            run_dirs = list(runs.iterdir())
            self.assertEqual(len(run_dirs), 1)
            receipt = json.loads((run_dirs[0] / 'exit.json').read_text(encoding='utf-8'))
            self.assertEqual(receipt['plan_id'], launcher.PLAN_ID)
            self.assertEqual(receipt['candidate_commit'], 'a' * 40)
            self.assertEqual(receipt['child_exit_code'], 0)
            self.assertEqual(receipt['reason'], 'normal_exit')
            self.assertFalse((run_dirs[0] / 'odoo.conf').exists())
            self.assertEqual((run_dirs[0] / 'server.log').read_bytes(), b'synthetic child exit\n')

    def test_owned_start_stops_sigterm_ignoring_child_after_grace(self):
        with tempfile.TemporaryDirectory(prefix='s11-launcher-stop-test-') as temporary:
            root = Path(temporary)
            runs = root / 'runs'
            active = root / 'active.json'
            fake_odoo = root / 'fake_odoo.py'
            fake_odoo.write_text(
                "import os, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "os.write(1, b'READY'); time.sleep(5)\n", encoding='utf-8')
            runtime = {'scope': {
                'id': 'SYNTHETIC-TEST-SCOPE',
                'expires_at_utc': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(),
            }}
            database = {'host': '127.0.0.1', 'port': 5432, 'user': 'synthetic', 'password': 'test-only'}

            def render_config(_database, run_dir):
                config = run_dir / 'odoo.conf'
                config.write_text('[options]\\n', encoding='utf-8')
                config.chmod(0o600)
                return config

            with (patch.object(launcher, 'RUNS', runs),
                  patch.object(launcher, 'ACTIVE', active),
                  patch.object(launcher, 'ODOO_ROOT', root),
                  patch.object(launcher, 'ODOO_BIN', fake_odoo),
                  patch.object(launcher, 'PYTHON', Path(sys.executable)),
                  patch.object(launcher, 'MAX_SERVER_SECONDS', 0.1),
                  patch.object(launcher, 'STOP_GRACE_SECONDS', 0.1),
                  patch.object(launcher, 'validate_pair', return_value=(
                      runtime, {}, database, launcher.EXPECTED_BRANCH, 'b' * 40)),
                  patch.object(launcher, 'validate_loopback_port'),
                  patch.object(launcher, 'render_odoo_config', side_effect=render_config)):
                self.assertEqual(launcher.start_service(), -9)

            self.assertFalse(active.exists())
            run_dirs = list(runs.iterdir())
            self.assertEqual(len(run_dirs), 1)
            receipt = json.loads((run_dirs[0] / 'exit.json').read_text(encoding='utf-8'))
            self.assertEqual(receipt['reason'], 'stop_grace_expired_child_killed')
            self.assertLess(receipt['child_exit_code'], 0)
            self.assertFalse(launcher.proc_start_ticks(receipt['child_pid']))
            self.assertFalse((run_dirs[0] / 'odoo.conf').exists())

    def test_silent_child_does_not_block_deadline_poll(self):
        child = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(3)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        started = time.monotonic()
        try:
            chunk = launcher.read_child_chunk(child, timeout=0.05)
            elapsed = time.monotonic() - started
            self.assertIsNone(chunk)
            self.assertLess(elapsed, 0.5)
        finally:
            child.terminate()
            child.wait(timeout=2)
            child.stdout.close()

    def test_sigterm_ignoring_silent_child_reaches_bounded_stop_deadline(self):
        child = subprocess.Popen(
            [sys.executable, '-c',
             'import os, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); '
             'os.write(1, b"READY"); time.sleep(3)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        try:
            self.assertEqual(launcher.read_child_chunk(child, timeout=1), b'READY')
            child.send_signal(15)
            stop_deadline = time.monotonic() + 0.05
            while not launcher.stop_grace_elapsed(True, stop_deadline):
                self.assertIsNone(launcher.read_child_chunk(child, timeout=0.01))
            self.assertIsNone(child.poll())
        finally:
            child.kill()
            child.wait(timeout=2)
            child.stdout.close()

    def test_child_exit_diagnostics_preserve_signal_and_nonzero_status(self):
        self.assertEqual(launcher.child_exit_diagnostics(0, 'normal_exit'), ('normal_exit', None))
        self.assertEqual(launcher.child_exit_diagnostics(2, 'normal_exit'), ('child_nonzero_exit', None))
        self.assertEqual(launcher.child_exit_diagnostics(-11, 'normal_exit'), ('child_signaled', 11))
        self.assertEqual(launcher.child_exit_diagnostics(-15, 'normal_exit', stop_requested=True),
                         ('stop_requested', 15))
        self.assertEqual(launcher.child_exit_diagnostics(0, 'normal_exit', stop_requested=True),
                         ('stop_requested', None))
        self.assertEqual(launcher.child_exit_diagnostics(-9, 'stop_grace_expired_child_killed'),
                         ('stop_grace_expired_child_killed', 9))
        self.assertEqual(launcher.child_exit_diagnostics(None, 'stop_grace_expired_child_still_running'),
                         ('stop_grace_expired_child_still_running', None))

    def test_available_child_output_is_read_without_waiting_for_eof(self):
        child = subprocess.Popen(
            [sys.executable, '-c', 'import os, time; os.write(1, b"ready"); time.sleep(3)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        try:
            self.assertEqual(launcher.read_child_chunk(child, timeout=1), b'ready')
        finally:
            child.terminate()
            child.wait(timeout=2)
            child.stdout.close()

    def test_stop_grace_deadline_is_monotonic_and_only_applies_after_stop(self):
        self.assertFalse(launcher.stop_grace_elapsed(False, 10.0, now=11.0))
        self.assertFalse(launcher.stop_grace_elapsed(True, None, now=11.0))
        self.assertFalse(launcher.stop_grace_elapsed(True, 10.0, now=9.9))
        self.assertTrue(launcher.stop_grace_elapsed(True, 10.0, now=10.0))


if __name__ == '__main__':
    unittest.main()
