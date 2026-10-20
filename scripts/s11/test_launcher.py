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
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


LAUNCHER = Path(__file__).with_name('launcher.py')
SPEC = importlib.util.spec_from_file_location('ydental_s11_launcher', LAUNCHER)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class LauncherSupervisorTests(unittest.TestCase):
    def test_connected_database_must_match_admitted_cluster_identifier(self):
        runtime = {'database': {'expected_cluster_ref': launcher.EXPECTED_CLUSTER}}
        admission = {
            'database_server_addr': '127.0.0.1',
            'database_oid': launcher.EXPECTED_OID,
            'cluster_ref': launcher.EXPECTED_CLUSTER,
            'candidate_commit': 'a' * 40,
        }

        class Cursor:
            dbname = launcher.EXPECTED_DATABASE
            def __init__(self, cluster_ref):
                self.cluster_ref = cluster_ref
            def execute(self, _query):
                pass
            def fetchone(self):
                return (launcher.EXPECTED_OID, 's11_role', '127.0.0.1', 5432, self.cluster_ref)

        class Env:
            cr = None
            dbname = launcher.EXPECTED_DATABASE

        env = Env()
        with patch.object(launcher, 'validate_pair', return_value=(
            runtime, admission, {'name': launcher.EXPECTED_DATABASE, 'user': 's11_role', 'port': 5432},
            launcher.EXPECTED_BRANCH, 'a' * 40,
        )):
            env.cr = Cursor(launcher.EXPECTED_CLUSTER)
            launcher.validate_connected_database(env)
            env.cr = Cursor('wrong-cluster')
            with self.assertRaisesRegex(launcher.Refusal, 'authorized S11 scratch admission'):
                launcher.validate_connected_database(env)

    def test_live_database_probe_is_read_only_and_binds_exact_identity(self):
        class Cursor:
            def __init__(self, cluster_ref):
                self.cluster_ref = cluster_ref
            def execute(self, query):
                self.query = query
            def fetchone(self):
                return {
                    'name': launcher.EXPECTED_DATABASE,
                    'oid': launcher.EXPECTED_OID,
                    'role': 's11_role',
                    'server_addr': '127.0.0.1',
                    'server_port': 5432,
                    'cluster_ref': self.cluster_ref,
                }
            def close(self):
                pass

        class Connection:
            def __init__(self, cluster_ref):
                self.cursor_value = Cursor(cluster_ref)
                self.rolled_back = False
                self.closed = False
            def set_session(self, **kwargs):
                self.session = kwargs
            def cursor(self, **kwargs):
                return self.cursor_value
            def rollback(self):
                self.rolled_back = True
            def get_transaction_status(self):
                return 0
            def close(self):
                self.closed = True

        connection = Connection(launcher.EXPECTED_CLUSTER)
        database = {
            'name': launcher.EXPECTED_DATABASE, 'host': '127.0.0.1', 'port': 5432,
            'user': 's11_role', 'password': 'synthetic-test-only',
        }
        admission = {'database_server_addr': '127.0.0.1', 'cluster_ref': launcher.EXPECTED_CLUSTER}
        pg = ModuleType('psycopg2')
        pg.connect = Mock(return_value=connection)
        pg.extensions = SimpleNamespace(TRANSACTION_STATUS_IDLE=0)
        extras = ModuleType('psycopg2.extras')
        extras.RealDictCursor = object
        with patch.dict(sys.modules, {'psycopg2': pg, 'psycopg2.extras': extras}):
            launcher.validate_live_database(database, admission)
        pg.connect.assert_called_once()
        self.assertIn('system_identifier', connection.cursor_value.query)
        self.assertTrue(connection.session['readonly'])
        self.assertEqual(connection.session['isolation_level'], 'REPEATABLE READ')
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)

        mismatched = Connection('wrong-cluster')
        pg.connect = Mock(return_value=mismatched)
        with patch.dict(sys.modules, {'psycopg2': pg, 'psycopg2.extras': extras}):
            with self.assertRaisesRegex(launcher.Refusal, 'live PostgreSQL connection'):
                launcher.validate_live_database(database, admission)
        self.assertTrue(mismatched.closed)

    def test_start_refuses_live_database_mismatch_before_creating_run_or_owner(self):
        with tempfile.TemporaryDirectory(prefix='s11-live-db-refusal-') as temporary:
            root = Path(temporary)
            runs = root / 'runs'
            active = root / 'active.json'
            runtime = {'scope': {'id': 'synthetic', 'expires_at_utc': '2099-01-01T00:00:00Z'}}
            database = {'host': '127.0.0.1', 'port': 5432, 'user': 'synthetic', 'password': 'redacted'}
            with (patch.object(launcher, 'RUNS', runs),
                  patch.object(launcher, 'ACTIVE', active),
                  patch.object(launcher, 'validate_pair', return_value=(
                      runtime, {}, database, launcher.EXPECTED_BRANCH, 'c' * 40)),
                  patch.object(launcher, 'validate_live_database',
                               side_effect=launcher.Refusal('wrong database')),
                  patch.object(launcher.subprocess, 'Popen') as popen):
                with self.assertRaisesRegex(launcher.Refusal, 'wrong database'):
                    launcher.start_service()
            self.assertFalse(runs.exists())
            self.assertFalse(active.exists())
            popen.assert_not_called()

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

    def test_gdb_script_is_private_and_captures_sigsegv_stack_mappings_and_core(self):
        with tempfile.TemporaryDirectory(prefix='s11-gdb-script-test-') as temporary:
            run_dir = Path(temporary)
            script = launcher.write_gdb_commands(run_dir, None)
            body = script.read_text(encoding='utf-8')
            self.assertEqual(os.stat(script).st_mode & 0o777, 0o600)
            self.assertIn('handle SIGSEGV stop print nopass', body)
            self.assertIn('info threads', body)
            self.assertIn('thread apply all bt full', body)
            self.assertIn('info proc mappings', body)
            self.assertIn('generate-core-file ' + str(run_dir / 'core.dump'), body)
            self.assertNotIn('db_password', body)

    def test_gdb_owned_group_stop_verifies_pid_ticks_and_reaps_members(self):
        with tempfile.TemporaryDirectory(prefix='s11-gdb-group-test-') as temporary:
            run_dir = Path(temporary)
            process = subprocess.Popen(
                [sys.executable, '-c', 'import time; time.sleep(30)'],
                start_new_session=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                ticks = launcher.proc_start_ticks(process.pid)
                self.assertIsNotNone(ticks)
                identity = {
                    'pid': process.pid, 'start_ticks': ticks,
                    'pgid': process.pid, 'sid': os.getsid(process.pid),
                }
                (run_dir / 'inferior.json').write_text(json.dumps(identity), encoding='utf-8')
                (run_dir / 'inferior.json').chmod(0o600)
                self.assertTrue(launcher.ensure_gdb_group_stopped(run_dir, process.pid, ticks))
                process.wait(timeout=2)
                self.assertEqual(launcher.process_group_members(process.pid, identity['sid']), [])
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=2)

    def test_gdb_group_without_inferior_identity_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='s11-gdb-identity-missing-') as temporary:
            run_dir = Path(temporary)
            process = subprocess.Popen(
                [sys.executable, '-c', 'import time; time.sleep(30)'],
                start_new_session=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                ticks = launcher.proc_start_ticks(process.pid)
                self.assertFalse(launcher.ensure_gdb_group_stopped(run_dir, process.pid, ticks))
                self.assertIsNone(process.poll())
                identity_path = run_dir / 'inferior.json'
                identity_path.write_text('null\n', encoding='utf-8')
                identity_path.chmod(0o600)
                self.assertFalse(launcher.ensure_gdb_group_stopped(run_dir, process.pid, ticks))
            finally:
                process.kill()
                process.wait(timeout=2)

    def test_gdb_early_exit_reaps_inferior_in_separate_group(self):
        with tempfile.TemporaryDirectory(prefix='s11-gdb-separate-groups-') as temporary:
            run_dir = Path(temporary)
            identity_path = run_dir / 'inferior.json'
            child_code = (
                'import json, os, time; os.setpgid(0, 0); '
                'raw=open("/proc/self/stat").read(); fields=raw[raw.rfind(")")+2:].split(); '
                'info={"pid":os.getpid(),"start_ticks":int(fields[19]),"pgid":os.getpgid(0),"sid":os.getsid(0)}; '
                f'fd=os.open({str(identity_path)!r},os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); '
                'stream=os.fdopen(fd,"w"); json.dump(info,stream); stream.close(); time.sleep(30)'
            )
            debugger = subprocess.Popen(
                [sys.executable, '-c',
                 'import os,time; pid=os.fork(); '
                 f'os.execv({sys.executable!r},[{sys.executable!r},"-c",{child_code!r}]) if pid==0 else time.sleep(30)'],
                start_new_session=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            ticks = launcher.proc_start_ticks(debugger.pid)
            try:
                deadline = time.monotonic() + 3
                while not identity_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                identity = json.loads(identity_path.read_text(encoding='utf-8'))
                debugger.kill()
                debugger.wait(timeout=2)
                self.assertTrue(launcher.ensure_gdb_group_stopped(run_dir, debugger.pid, ticks))
                self.assertEqual(launcher.process_group_members(identity['pgid'], identity['sid']), [])
                self.assertEqual(launcher.process_group_members(identity['sid'], identity['sid']), [])
            finally:
                if debugger.poll() is None:
                    debugger.kill()
                    debugger.wait(timeout=2)
                if identity_path.exists():
                    identity = json.loads(identity_path.read_text(encoding='utf-8'))
                    try:
                        os.killpg(identity['pgid'], 9)
                    except ProcessLookupError:
                        pass

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
                  patch.object(launcher, 'validate_live_database'),
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
                  patch.object(launcher, 'validate_live_database'),
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
