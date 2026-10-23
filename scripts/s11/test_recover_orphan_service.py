"""Recovery checks use temporary synthetic children, never the S11 service."""

import configparser
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import recover_orphan_service as recovery


launcher = recovery.launcher
SERVER = '''import configparser, os, signal, socket, sys, time
p = configparser.ConfigParser(interpolation=None)
p.read(sys.argv[2])
if os.environ.get("S11_SYNTH_IGNORE_TERM") == "1":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
s = socket.socket()
s.bind(("127.0.0.1", int(p["options"]["http_port"])))
s.listen(1)
while True:
    time.sleep(0.1)
'''
SPAWN = '''import os, sys
pid = os.fork()
if pid:
    print(pid, flush=True)
    os._exit(0)
os.setsid()
fd = os.open(os.devnull, os.O_RDWR)
for n in (0, 1, 2):
    os.dup2(fd, n)
if fd > 2:
    os.close(fd)
os.execv(sys.argv[1], sys.argv[1:])
'''


@unittest.skipUnless(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"),
                     "Linux pidfd support required")
class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="s11-synthetic-orphan-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        repo, core = self.root / "repo", self.root / "core"
        private = repo / ".local" / "s11"
        runs = private / "new-target-runs"
        self.run = runs / "20261023T100000Z-123456789abc"
        for directory in (repo, core, repo / ".local", private, runs, self.run):
            directory.mkdir(mode=0o700)
        self.server = core / "synthetic_server.py"
        self.server.write_text(SERVER)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            self.port = reservation.getsockname()[1]
        self.assertNotEqual(self.port, 18411)
        self.paths = patch.multiple(
            launcher, REPO_ROOT=repo, ODOO_ROOT=core, PRIVATE_ROOT=private,
            RUNS=runs, ACTIVE=private / "new-target-active.json",
            DATA_DIR=private / "new-target-data", ODOO_BIN=self.server,
            PYTHON=Path(sys.executable), CORE_ADDONS=core / "addons",
            EXPECTED_HTTP_PORT=self.port,
        )
        self.paths.start()
        self.addCleanup(self.paths.stop)
        self.config = launcher.render_odoo_config({
            "host": "127.0.0.1", "port": 5432, "user": launcher.EXPECTED_DATABASE,
            "password": "synthetic-only-value",}, self.run)
        self.log = self.run / "server.log"
        self.log.write_bytes(b"")
        self.log.chmod(0o600)
        self.pid = None
        self.pidfd = None
        self.addCleanup(self.stop_synthetic_child)

    def spawn(self, ignore_term=False):
        env = os.environ.copy()
        env["S11_SYNTH_IGNORE_TERM"] = "1" if ignore_term else "0"
        spawned = subprocess.run(
            [sys.executable, "-c", SPAWN, str(launcher.PYTHON), str(self.server),
             "-c", str(self.config)], cwd=launcher.ODOO_ROOT, env=env,
            check=True, capture_output=True, text=True, timeout=5)
        self.pid = int(spawned.stdout.strip())
        self.pidfd = os.pidfd_open(self.pid, 0)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if recovery.listeners() and recovery.proc_identity(self.pid)["ppid"] == 1:
                break
            if select.select([self.pidfd], [], [], 0)[0]:
                self.fail("synthetic child exited before fixture readiness")
            time.sleep(0.01)
        else:
            self.fail("synthetic child fixture did not become ready")
        self.marker = {
            "plan_id": launcher.PLAN_ID, "branch": launcher.EXPECTED_BRANCH,
            "core_commit": launcher.EXPECTED_CORE_COMMIT,
            "database_name": launcher.EXPECTED_DATABASE, "database_oid": launcher.EXPECTED_OID,
            "cluster_ref": launcher.EXPECTED_CLUSTER, "http_host": launcher.EXPECTED_HTTP_HOST,
            "http_port": self.port, "debugger_mode": "direct", "gdb_version": None,
            "s11_session_clock": None, "run_id": self.run.name,
            "supervisor_pid": 2147483647, "supervisor_start_ticks": 123,
            "child_pid": self.pid, "child_start_ticks": launcher.proc_start_ticks(self.pid),
            "config_path": str(self.config), "log_path": str(self.log),
        }
        self.save_marker()

    def stop_synthetic_child(self):
        # Only the fixture's bound pidfd can be signalled here. SIGKILL belongs
        # solely to cleanup of the deliberately SIGTERM-ignoring test fixture.
        if self.pidfd is not None:
            try:
                if not select.select([self.pidfd], [], [], 0)[0]:
                    signal.pidfd_send_signal(self.pidfd, signal.SIGKILL, None, 0)
                    select.select([self.pidfd], [], [], 5)
            finally:
                os.close(self.pidfd)

    def save_marker(self):
        launcher.ACTIVE.write_text(json.dumps(self.marker))
        launcher.ACTIVE.chmod(0o600)

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_real_synthetic_orphan_dry_check_has_no_filesystem_or_signal_effect(self):
        self.spawn()
        before = self.snapshot()
        result = recovery.recover()
        self.assertEqual(result["result"], "DRY_CHECK_OK")
        self.assertFalse(result["signal_attempted"])
        self.assertEqual(before, self.snapshot())
        self.assertFalse(select.select([self.pidfd], [], [], 0)[0])

    def test_real_synthetic_orphan_single_signal_exit_and_exact_archive(self):
        self.spawn()
        original = launcher.ACTIVE.read_bytes()
        real_send = signal.pidfd_send_signal
        with patch.object(signal, "pidfd_send_signal", wraps=real_send) as send:
            result = recovery.recover(recovery.CONFIRMATION)
        send.assert_called_once()
        self.assertEqual(send.call_args.args[1], signal.SIGTERM)
        self.assertEqual(result["result"], "EXACT_ORPHAN_EXIT_CONFIRMED")
        self.assertTrue(result["pidfd_exit_observed"])
        self.assertFalse(launcher.ACTIVE.exists())
        self.assertEqual((self.run / "orphan-active-marker-original.json").read_bytes(), original)
        self.assertIsNone(result["original_supervisor_exit_code"])
        self.assertIsNone(result["child_exit_code"])
        self.assertTrue(self.config.exists())
        self.assertFalse((self.run / "exit.json").exists())
        self.assertNotIn("synthetic-only-value", json.dumps(result))
        self.assertFalse(recovery.listeners())

    def test_real_timeout_preserves_marker_and_blocks_a_second_signal(self):
        self.spawn(ignore_term=True)
        original = launcher.ACTIVE.read_bytes()
        result = recovery.recover(recovery.CONFIRMATION, timeout=0.05)
        self.assertEqual(result["result"], "RECOVERY_UNCONFIRMED")
        self.assertFalse(result["pidfd_exit_observed"])
        self.assertEqual(launcher.ACTIVE.read_bytes(), original)
        self.assertTrue(self.config.exists())
        with patch.object(signal, "pidfd_send_signal") as send:
            with self.assertRaises(recovery.Refusal):
                recovery.recover(recovery.CONFIRMATION)
            send.assert_not_called()

    def test_invalid_confirmation_is_read_only(self):
        self.spawn()
        before = self.snapshot()
        with self.assertRaises(recovery.Refusal):
            recovery.recover("yes")
        self.assertEqual(self.snapshot(), before)

    def test_live_recorded_supervisor_pid_refused_even_with_wrong_birth(self):
        self.spawn()
        self.marker["supervisor_pid"] = os.getpid()
        self.save_marker()
        with self.assertRaisesRegex(recovery.Refusal, "supervisor PID still exists"):
            recovery.recover()

    def test_wrong_target_gdb_clock_and_paths_refused(self):
        self.spawn()
        for key, value in (("database_oid", 1), ("database_name", "other"),
                           ("cluster_ref", "other"), ("debugger_mode", "gdb"),
                           ("s11_session_clock", {}), ("config_path", "/tmp/other"),
                           ("log_path", "/tmp/other"), ("run_id", "../other")):
            original = self.marker[key]
            with self.subTest(key=key):
                self.marker[key] = value
                self.save_marker()
                with self.assertRaises(recovery.Refusal):
                    recovery.recover()
            self.marker[key] = original
        self.save_marker()

    def test_reused_child_birth_refused(self):
        self.spawn()
        self.marker["child_start_ticks"] += 1
        self.save_marker()
        with self.assertRaisesRegex(recovery.Refusal, "identity mismatch"):
            recovery.recover()

    def test_non_orphan_parent_group_session_uid_and_zombie_refused(self):
        self.spawn()
        real_identity = recovery.proc_identity(self.pid)
        for key, value in (("ppid", os.getpid()), ("pgid", 1), ("sid", 1),
                           ("uids", [os.getuid() + 1] * 4), ("state", "Z")):
            with self.subTest(key=key):
                altered = dict(real_identity, **{key: value})
                with patch.object(recovery, "proc_identity", return_value=altered):
                    with self.assertRaises(recovery.Refusal):
                        recovery.recover()

    def test_extra_argument_refused(self):
        self.spawn()
        argv = launcher.proc_cmdline(self.pid)
        with patch.object(launcher, "proc_cmdline", return_value=argv + ["--init=other"]):
            with self.assertRaisesRegex(recovery.Refusal, "four direct"):
                recovery.recover()

    def test_listener_not_owned_by_child_refused(self):
        self.spawn()
        with patch.object(recovery, "child_socket_inodes", return_value=set()):
            with self.assertRaisesRegex(recovery.Refusal, "listener"):
                recovery.recover()

    def test_wildcard_ipv6_or_additional_listener_refused(self):
        self.spawn()
        row = recovery.listeners()[0]
        for rows in ([dict(row, address="00000000")], [dict(row, family="tcp6")], [row, row]):
            with self.subTest(rows=rows):
                with patch.object(recovery, "listeners", return_value=rows):
                    with self.assertRaisesRegex(recovery.Refusal, "listener"):
                        recovery.recover()

    def test_modified_config_cron_log_db_and_extra_option_refused(self):
        self.spawn()
        original = self.config.read_text()
        for key, value in (("db_name", "other"), ("db_user", "other"),
                           ("db_host", "other"), ("max_cron_threads", "1"),
                           ("logfile", "/tmp/other"), ("smtp_port", "25"),
                           ("server_wide_modules", "other")):
            with self.subTest(key=key):
                parser = configparser.ConfigParser(interpolation=None)
                parser.read_string(original)
                parser["options"][key] = value
                with self.config.open("w") as stream:
                    parser.write(stream)
                with self.assertRaisesRegex(recovery.Refusal, "configuration differs"):
                    recovery.recover()
        self.config.write_text(original)

    def test_unsafe_permissions_and_symlink_refused(self):
        self.spawn()
        self.config.chmod(0o644)
        with self.assertRaises(recovery.Refusal):
            recovery.recover()
        self.config.chmod(0o600)
        moved = self.config.with_suffix(".saved")
        self.config.rename(moved)
        self.config.symlink_to(moved)
        with self.assertRaises(OSError):
            recovery.recover()

    def test_missing_pidfd_support_has_no_fallback(self):
        self.spawn()
        with patch.object(os, "pidfd_open"):
            del os.pidfd_open
            with self.assertRaisesRegex(recovery.Refusal, "pidfd support"):
                recovery.recover()

    def test_existing_intent_or_exit_prevents_signal(self):
        self.spawn()
        for name in ("exit.json", "orphan-recovery-intent.json", "orphan-recovery-outcome.json",
                     "orphan-active-marker-original.json"):
            with self.subTest(name=name):
                path = self.run / name
                path.write_text("{}")
                path.chmod(0o600)
                with self.assertRaisesRegex(recovery.Refusal, "no retry"):
                    recovery.recover()
                path.unlink()

    def test_marker_change_on_final_validation_refuses_before_signal(self):
        self.spawn()
        real_validate = recovery.validate_child
        calls = 0
        def mutate_after_validation(*args):
            nonlocal calls
            answer = real_validate(*args)
            calls += 1
            if calls == 2:
                self.marker["candidate_commit"] = "changed"
                self.save_marker()
            return answer
        with patch.object(recovery, "validate_child", side_effect=mutate_after_validation):
            with patch.object(signal, "pidfd_send_signal") as send:
                result = recovery.recover(recovery.CONFIRMATION)
                send.assert_not_called()
        self.assertEqual(result["result"], "REFUSED_BEFORE_SIGNAL")
        self.assertTrue((self.run / "orphan-recovery-intent.json").exists())
        self.assertTrue(launcher.ACTIVE.exists())

    def test_live_owner_appearing_at_signal_boundary_refused(self):
        self.spawn()
        real_absent = recovery.supervisor_absent
        calls = 0
        def owner_appears(marker):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise recovery.Refusal("owner appeared")
            return real_absent(marker)
        with patch.object(recovery, "supervisor_absent", side_effect=owner_appears):
            with patch.object(signal, "pidfd_send_signal") as send:
                result = recovery.recover(recovery.CONFIRMATION)
                send.assert_not_called()
        self.assertEqual(result["result"], "REFUSED_BEFORE_SIGNAL")

    def test_signal_exception_is_unknown_and_not_retryable(self):
        self.spawn()
        with patch.object(signal, "pidfd_send_signal", side_effect=OSError("private detail")):
            result = recovery.recover(recovery.CONFIRMATION)
        self.assertEqual(result["result"], "RECOVERY_UNCONFIRMED")
        self.assertTrue(result["signal_attempted"])
        self.assertNotIn("private detail", json.dumps(result))
        self.assertTrue(launcher.ACTIVE.exists())

    def test_marker_change_after_exit_preserves_changed_marker(self):
        self.spawn()
        real_listeners = recovery.listeners
        def mutate_on_free_port():
            rows = real_listeners()
            if not rows:
                self.marker["candidate_commit"] = "changed"
                self.save_marker()
            return rows
        with patch.object(recovery, "listeners", side_effect=mutate_on_free_port):
            result = recovery.recover(recovery.CONFIRMATION)
        self.assertEqual(result["result"], "RECOVERY_UNCONFIRMED")
        self.assertTrue(result["pidfd_exit_observed"])
        self.assertTrue(launcher.ACTIVE.exists())
        self.assertFalse((self.run / "orphan-active-marker-original.json").exists())

    def test_concurrent_recovery_lock_refused_without_signal(self):
        self.spawn()
        with recovery.recovery_lock():
            with self.assertRaisesRegex(recovery.Refusal, "holds the lock"):
                recovery.recover(recovery.CONFIRMATION)


if __name__ == "__main__":
    unittest.main()
