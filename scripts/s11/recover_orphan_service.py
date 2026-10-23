#!/usr/bin/env python3
"""Inspect or stop the exact orphaned direct S11 child; never start a service.

Without the explicit confirmation phrase this command only reads local files
and /proc. It does not connect to HTTP/PostgreSQL. An immutable intent prevents
any retry after a signal or result becomes uncertain. Original supervisor and
child exit codes remain unknown: a pidfd proves exit, not the exit status.
"""

from __future__ import annotations

import argparse
import configparser
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import sys

import launcher


CONFIRMATION = "S11-RECOVER-EXACT-ORPHAN-V1"
Refusal = launcher.Refusal


def refuse_unless(condition: bool, message: str) -> None:
    if not condition:
        raise Refusal(message)


def private_directory(path: Path) -> None:
    info = path.lstat()
    refuse_unless(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                  and stat.S_IMODE(info.st_mode) == 0o700,
                  "recovery directory is not a private owned real directory")


def private_bytes(path: Path) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        refuse_unless(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                      and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1,
                      "recovery input is not a private owned regular file")
        raw = os.read(fd, 1024 * 1024 + 1)
        refuse_unless(len(raw) <= 1024 * 1024, "recovery input exceeds size bound")
        return raw
    finally:
        os.close(fd)


def durable_bytes(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            size = os.write(fd, view)
            refuse_unless(size > 0, "recovery evidence write did not advance")
            view = view[size:]
        os.fsync(fd)
    finally:
        os.close(fd)
    sync_directory(path.parent)


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_json(path: Path, value: dict) -> None:
    durable_bytes(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def proc_identity(pid: int) -> dict:
    root = Path("/proc") / str(pid)
    raw = (root / "stat").read_text(encoding="ascii")
    state, ticks = launcher.parse_proc_stat_identity(raw)
    tail = raw[raw.rfind(")") + 2:].split()
    uid_line = next(line for line in (root / "status").read_text().splitlines()
                    if line.startswith("Uid:"))
    return {"pid": pid, "state": state, "start_ticks": ticks,
            "ppid": int(tail[1]), "pgid": int(tail[2]), "sid": int(tail[3]),
            "uids": [int(value) for value in uid_line.split()[1:]]}


def supervisor_absent(marker: dict) -> None:
    pid = marker.get("supervisor_pid")
    refuse_unless(type(pid) is int and pid > 1
                  and type(marker.get("supervisor_start_ticks")) is int
                  and marker["supervisor_start_ticks"] > 0,
                  "recorded supervisor identity is invalid")
    # Even a reused live PID is refused rather than treated as a dead owner.
    refuse_unless(not (Path("/proc") / str(pid)).exists(),
                  "recorded supervisor PID still exists; orphan recovery refused")


def validate_config(path: Path) -> str:
    raw = private_bytes(path)
    expected = {
        "addons_path": ",".join((str(launcher.CORE_ADDONS), str(launcher.REPO_ROOT))),
        "data_dir": str(launcher.DATA_DIR), "db_host": "127.0.0.1", "db_port": "5432",
        "db_user": launcher.EXPECTED_DATABASE, "db_name": launcher.EXPECTED_DATABASE,
        "dbfilter": "^" + launcher.EXPECTED_DATABASE + "$",
        "db_maxconn": str(launcher.EXPECTED_DB_MAXCONN), "list_db": "False",
        "http_interface": launcher.EXPECTED_HTTP_HOST,
        "http_port": str(launcher.EXPECTED_HTTP_PORT), "workers": "0",
        "max_cron_threads": "0", "proxy_mode": "False", "limit_time_cpu": "600",
        "limit_time_real": str(launcher.MAX_SERVER_SECONDS), "log_level": "info",
        "logfile": "", "smtp_server": "127.0.0.1", "smtp_port": "1", "smtp_ssl": "False",
    }
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(raw.decode("utf-8"))
        valid = (parser.sections() == ["options"] and not parser.defaults()
                 and set(parser["options"]) == set(expected) | {"db_password"}
                 and bool(parser["options"]["db_password"])
                 and all(parser["options"][key] == value for key, value in expected.items()))
    except (UnicodeError, configparser.Error, KeyError):
        valid = False
    refuse_unless(valid, "orphan configuration differs from the fixed direct S11 contract")
    return hashlib.sha256(raw).hexdigest()


def listeners() -> list[dict]:
    """Read kernel socket metadata; no TCP connection or business request."""
    rows = []
    for family in ("tcp", "tcp6"):
        for line in (Path("/proc/net") / family).read_text().splitlines()[1:]:
            fields = line.split()
            address, port = fields[1].split(":")
            if fields[3] == "0A" and int(port, 16) == launcher.EXPECTED_HTTP_PORT:
                rows.append({"family": family, "address": address,
                             "uid": int(fields[7]), "inode": fields[9]})
    return rows


def child_socket_inodes(pid: int) -> set[str]:
    result = set()
    for path in (Path("/proc") / str(pid) / "fd").iterdir():
        try:
            target = os.readlink(path)
        except FileNotFoundError:
            continue
        match = re.fullmatch(r"socket:\[(\d+)\]", target)
        if match:
            result.add(match[1])
    return result


def validate_child(marker: dict, config_path: Path, pidfd: int) -> dict:
    supervisor_absent(marker)
    pid = marker["child_pid"]
    refuse_unless(not select.select([pidfd], [], [], 0)[0], "bound child already exited")
    fdinfo = Path(f"/proc/self/fdinfo/{pidfd}").read_text()
    bound_pid = next((line.split()[1] for line in fdinfo.splitlines()
                      if line.startswith("Pid:")), None)
    refuse_unless(bound_pid == str(pid), "pidfd does not bind the recorded live child")
    identity = proc_identity(pid)
    refuse_unless(identity["state"] not in ("Z", "X", "x")
                  and identity["start_ticks"] == marker["child_start_ticks"]
                  and identity["ppid"] == 1 and identity["pgid"] == pid
                  and identity["sid"] == pid and identity["uids"] == [os.getuid()] * 4,
                  "orphan child birth/parent/session/UID identity mismatch")
    root = Path("/proc") / str(pid)
    refuse_unless(os.readlink(root / "cwd") == str(launcher.ODOO_ROOT)
                  and Path(os.readlink(root / "exe")) == launcher.PYTHON.resolve()
                  and os.readlink(root / "ns/net") == os.readlink("/proc/self/ns/net"),
                  "orphan executable/cwd/network namespace mismatch")
    refuse_unless(launcher.proc_cmdline(pid) == [str(launcher.PYTHON), str(launcher.ODOO_BIN),
                                               "-c", str(config_path)],
                  "orphan child does not have the exact four direct launcher arguments")
    rows = listeners()
    refuse_unless(len(rows) == 1 and rows[0]["family"] == "tcp"
                  and rows[0]["address"] == "0100007F" and rows[0]["uid"] == os.getuid()
                  and rows[0]["inode"] in child_socket_inodes(pid),
                  "fixed loopback listener is not exclusively owned by the exact child")
    return identity


def inspect() -> tuple[dict, bytes, Path, str]:
    launcher.ensure_private_root()
    private_directory(launcher.RUNS)
    marker, raw = launcher.read_private_json(launcher.ACTIVE)
    refuse_unless(private_bytes(launcher.ACTIVE) == raw, "active marker changed during read")
    expected = {"plan_id": launcher.PLAN_ID, "branch": launcher.EXPECTED_BRANCH,
                "core_commit": launcher.EXPECTED_CORE_COMMIT,
                "database_name": launcher.EXPECTED_DATABASE, "database_oid": launcher.EXPECTED_OID,
                "cluster_ref": launcher.EXPECTED_CLUSTER, "http_host": launcher.EXPECTED_HTTP_HOST,
                "http_port": launcher.EXPECTED_HTTP_PORT, "debugger_mode": "direct",
                "s11_session_clock": None, "gdb_version": None}
    refuse_unless(all(key in marker and marker[key] == value for key, value in expected.items()),
                  "active marker does not match the fixed direct S11 target")
    run_id = marker.get("run_id")
    refuse_unless(isinstance(run_id, str)
                  and re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}", run_id) is not None,
                  "active run identifier is invalid")
    for key in ("child_pid", "child_start_ticks"):
        refuse_unless(type(marker.get(key)) is int and marker[key] > 1,
                      "recorded child identity is invalid")
    run_dir = launcher.RUNS / run_id
    private_directory(run_dir)
    refuse_unless(marker.get("config_path") == str(run_dir / "odoo.conf")
                  and marker.get("log_path") == str(run_dir / "server.log"),
                  "active marker paths do not match its private run")
    for name in ("exit.json", "orphan-recovery-intent.json", "orphan-recovery-outcome.json",
                 "orphan-active-marker-original.json"):
        refuse_unless(not os.path.lexists(run_dir / name),
                      "run already has an exit or recovery artifact; no retry allowed")
    supervisor_absent(marker)
    return marker, raw, run_dir, validate_config(run_dir / "odoo.conf")


@contextlib.contextmanager
def recovery_lock():
    launcher.ensure_private_root()
    path = launcher.PRIVATE_ROOT / "new-target-orphan-recovery.lock"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        refuse_unless(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                      and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1,
                      "recovery lock identity is unsafe")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Refusal("another orphan recovery holds the lock") from exc
        yield
    finally:
        os.close(fd)


def recover(confirm: str | None = None, timeout: float = launcher.STOP_GRACE_SECONDS) -> dict:
    refuse_unless(confirm is None or confirm == CONFIRMATION, "confirmation phrase is invalid")
    refuse_unless(0 < timeout <= launcher.STOP_GRACE_SECONDS, "recovery wait exceeds its bound")
    refuse_unless(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"),
                  "pidfd support is required; no PID-based fallback")
    guard = recovery_lock() if confirm else contextlib.nullcontext()
    with guard:
        marker, raw, run_dir, config_sha = inspect()
        pidfd = os.pidfd_open(marker["child_pid"], 0)
        try:
            identity = validate_child(marker, run_dir / "odoo.conf", pidfd)
            result = {"plan_id": launcher.PLAN_ID, "run_id": marker["run_id"],
                      "observed_at_utc": launcher.utc_now().isoformat(),
                      "active_marker_sha256": hashlib.sha256(raw).hexdigest(),
                      "config_sha256": config_sha, "child_identity": identity,
                      "original_supervisor_exit_code": None, "child_exit_code": None,
                      "exit_status_available": False, "config_retained": True,
                      "signal_attempted": False, "pidfd_exit_observed": False,
                      "result": "DRY_CHECK_OK"}
            refuse_unless(private_bytes(launcher.ACTIVE) == raw,
                          "active marker changed during validation")
            if not confirm:
                return result
            intent = dict(result, result="INTENT_SINGLE_SIGTERM", confirmation=CONFIRMATION)
            durable_json(run_dir / "orphan-recovery-intent.json", intent)
            try:
                refuse_unless(private_bytes(launcher.ACTIVE) == raw,
                              "active marker changed before signal")
                refuse_unless(validate_config(run_dir / "odoo.conf") == config_sha,
                              "configuration changed before signal")
                validate_child(marker, run_dir / "odoo.conf", pidfd)
                refuse_unless(private_bytes(launcher.ACTIVE) == raw,
                              "active marker changed at final signal boundary")
                supervisor_absent(marker)
                # Any exception after this flag leaves the immutable intent and
                # marker in place. Neither a signal nor an uncertain exit retries.
                result["signal_attempted"] = True
                signal.pidfd_send_signal(pidfd, signal.SIGTERM, None, 0)
                result["pidfd_exit_observed"] = bool(select.select([pidfd], [], [], timeout)[0])
                refuse_unless(result["pidfd_exit_observed"], "child exit was not confirmed within bound")
                refuse_unless(not listeners(), "fixed port still has a listener after child exit")
                refuse_unless(private_bytes(launcher.ACTIVE) == raw,
                              "active marker changed after exit; preserve for review")
                durable_bytes(run_dir / "orphan-active-marker-original.json", raw)
                refuse_unless(private_bytes(launcher.ACTIVE) == raw,
                              "active marker changed before retirement; preserve for review")
                launcher.ACTIVE.unlink()
                sync_directory(launcher.ACTIVE.parent)
                result["result"] = "EXACT_ORPHAN_EXIT_CONFIRMED"
                result["marker_archived_original_bytes"] = True
                result["fixed_port_has_no_listener"] = True
            except Exception as exc:
                # Never put exception messages, argv, config or credentials into
                # receipts. The exact exception type is enough to retain failure.
                result["result"] = "RECOVERY_UNCONFIRMED" if result["signal_attempted"] else "REFUSED_BEFORE_SIGNAL"
                result["failure_type"] = type(exc).__name__
            result["finished_at_utc"] = launcher.utc_now().isoformat()
            durable_json(run_dir / "orphan-recovery-outcome.json", result)
            return result
        finally:
            os.close(pidfd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", help="explicit single-signal confirmation phrase; default is read-only")
    args = parser.parse_args()
    try:
        result = recover(args.confirm)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["result"] in ("DRY_CHECK_OK", "EXACT_ORPHAN_EXIT_CONFIRMED") else 3
    except Exception as exc:
        print(f"S11 orphan recovery refused ({type(exc).__name__}); no fallback or automatic retry", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
