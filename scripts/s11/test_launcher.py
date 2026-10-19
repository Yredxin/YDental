import importlib.util
import datetime as dt
import json
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
