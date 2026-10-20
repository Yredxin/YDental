#!/usr/bin/env python3
"""Fail-closed, foreground supervisor for the S11 scratch Odoo service.

This launcher intentionally has no database-admission or credential-discovery
logic. A separately verified S11 runtime.json and admission.json are required.
It never creates a database, installs modules, or enables external delivery.
"""

from __future__ import annotations

import argparse
import configparser
import datetime as dt
import errno
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import resource
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid


PLAN_ID = "YD-S11-FOLLOWUP-LAB-V1"
EXPECTED_BRANCH = "codex/s11-followup-lab-r1"
EXPECTED_DATABASE = "ydental_s10_test_20261017105432_ce6dcbf8"
EXPECTED_OID = 2144130
EXPECTED_CLUSTER = "7694897083368259627"
EXPECTED_HTTP_HOST = "127.0.0.1"
EXPECTED_HTTP_PORT = 18411
EXPECTED_CORE_COMMIT = "f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb"
MAX_SCOPE_SECONDS = 24 * 60 * 60
MAX_SERVER_SECONDS = 20 * 60
MAX_LOG_BYTES = 32 * 1024 * 1024
MAX_RUNS = 64
MAX_TOTAL_RUN_BYTES = 512 * 1024 * 1024
MAX_CORE_BYTES = 256 * 1024 * 1024
STOP_GRACE_SECONDS = 30

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / ".local" / "s11"
RUNTIME_CONFIG = PRIVATE_ROOT / "runtime.json"
ADMISSION = PRIVATE_ROOT / "admission.json"
RUNS = PRIVATE_ROOT / "runs"
DATA_DIR = PRIVATE_ROOT / "data"
ACTIVE = PRIVATE_ROOT / "active.json"
ODOO_ROOT = REPO_ROOT.parent
ODOO_BIN = ODOO_ROOT / "odoo-bin"
PYTHON = ODOO_ROOT / ".venv" / "bin" / "python"
CORE_ADDONS = ODOO_ROOT / "odoo" / "addons"
SCRIPT_PATH = Path(__file__).resolve()
LOCAL_GDB = PRIVATE_ROOT / "tooling" / "gdb-root" / "usr" / "bin" / "gdb"
LOCAL_GDB_DATA = PRIVATE_ROOT / "tooling" / "gdb-root" / "usr" / "share" / "gdb"


class Refusal(RuntimeError):
    """A precondition was not met; no service action should be attempted."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_utc(value: object, label: str) -> dt.datetime:
    if not isinstance(value, str):
        raise Refusal(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refusal(f"{label} is not a valid ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() != dt.timedelta(0):
        raise Refusal(f"{label} must use UTC")
    return result.astimezone(dt.timezone.utc)


def parse_server_address(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Refusal(f"{label} must be a non-empty IP address")
    try:
        return ipaddress.ip_interface(value).ip.compressed
    except ValueError as exc:
        raise Refusal(f"{label} must be a valid IP address") from exc


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_private_json(path: Path) -> tuple[dict, bytes]:
    if not path.exists():
        raise Refusal(f"required S11 private file is absent: {path.relative_to(REPO_ROOT)}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise Refusal(f"cannot safely open {path.relative_to(REPO_ROOT)}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise Refusal(f"{path.relative_to(REPO_ROOT)} must be a regular file")
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise Refusal(f"{path.relative_to(REPO_ROOT)} must be owned by this user and mode 0600")
        chunks = []
        total = 0
        while True:
            data = os.read(fd, 65536)
            if not data:
                break
            total += len(data)
            if total > 1024 * 1024:
                raise Refusal(f"{path.relative_to(REPO_ROOT)} exceeds the 1 MiB limit")
            chunks.append(data)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refusal(f"{path.relative_to(REPO_ROOT)} is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise Refusal(f"{path.relative_to(REPO_ROOT)} must contain a JSON object")
    return parsed, raw


def ensure_private_root() -> None:
    parent = REPO_ROOT / ".local"
    if not parent.exists():
        raise Refusal("the ignored .local parent directory is absent or not a real directory")
    parent_info = parent.lstat()
    if not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != os.getuid():
        raise Refusal("the ignored .local parent must be a real directory owned by the current user")
    if not PRIVATE_ROOT.exists():
        raise Refusal("S11 private runtime directory is absent: .local/s11")
    info = PRIVATE_ROOT.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise Refusal(".local/s11 must be a real directory owned by the current user")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise Refusal(".local/s11 permissions must exclude group and other users")


def git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal("cannot verify the current S11 Git candidate") from exc
    return result.stdout.strip()


def verify_repository(runtime: dict, admission: dict) -> tuple[str, str]:
    branch = git_value("branch", "--show-current")
    commit = git_value("rev-parse", "HEAD")
    dirty = git_value("status", "--porcelain", "--untracked-files=all")
    if branch != EXPECTED_BRANCH or runtime.get("branch") != branch or admission.get("branch") != branch:
        raise Refusal("runtime/admission/current branch must all be codex/s11-followup-lab-r1")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise Refusal("current Git HEAD is not a full commit id")
    if runtime.get("candidate_commit") != commit or admission.get("candidate_commit") != commit:
        raise Refusal("runtime/admission candidate must equal the current Git HEAD")
    if dirty:
        raise Refusal("S11 worktree must be clean before an owned service can start")
    core_commit = git_value("-C", str(ODOO_ROOT), "rev-parse", "HEAD")
    if core_commit != EXPECTED_CORE_COMMIT:
        raise Refusal("Odoo core HEAD does not match the locked S11 core commit")
    if runtime.get("core_commit") != core_commit or admission.get("core_commit") != core_commit:
        raise Refusal("runtime/admission core commit must match the locked Odoo core")
    return branch, commit


def validate_pair() -> tuple[dict, dict, dict, str, str]:
    ensure_private_root()
    runtime, runtime_raw = read_private_json(RUNTIME_CONFIG)
    admission, _admission_raw = read_private_json(ADMISSION)
    if runtime.get("plan_id") != PLAN_ID or admission.get("plan_id") != PLAN_ID:
        raise Refusal("both private files must be bound to YD-S11-FOLLOWUP-LAB-V1")

    database = runtime.get("database")
    scope = runtime.get("scope")
    if not isinstance(database, dict) or not isinstance(scope, dict):
        raise Refusal("runtime database and scope objects are required")
    required_db = {
        "name": EXPECTED_DATABASE,
        "expected_oid": EXPECTED_OID,
        "expected_cluster_ref": EXPECTED_CLUSTER,
        "host": "127.0.0.1",
    }
    for key, expected in required_db.items():
        if database.get(key) != expected:
            raise Refusal(f"runtime database {key} does not match the S11 scratch contract")
    db_port = database.get("port")
    if not isinstance(db_port, int) or isinstance(db_port, bool) or not (1 <= db_port <= 65535):
        raise Refusal("database port must be an explicit valid integer")
    db_user = database.get("user")
    db_password = database.get("password")
    if not isinstance(db_user, str) or not db_user.strip() or not isinstance(db_password, str) or not db_password:
        raise Refusal("runtime must provide an S11 database user and password privately")
    if any(ch in db_user + db_password for ch in "\r\n\x00"):
        raise Refusal("database credentials contain unsupported control characters")

    scope_id = scope.get("id")
    if scope.get("plan_id") != PLAN_ID or not isinstance(scope_id, str) or not scope_id.strip():
        raise Refusal("runtime must name an actually issued S11-only scope")
    issued = parse_utc(scope.get("issued_at_utc"), "scope.issued_at_utc")
    expires = parse_utc(scope.get("expires_at_utc"), "scope.expires_at_utc")
    now = utc_now()
    if expires <= now or issued > now or expires - issued > dt.timedelta(seconds=MAX_SCOPE_SECONDS):
        raise Refusal("S11 scope is expired, not yet issued, or exceeds the 24-hour maximum")

    expected_application = {
        "host": EXPECTED_HTTP_HOST,
        "port": EXPECTED_HTTP_PORT,
        "workers": 0,
        "max_cron_threads": 0,
        "db_maxconn": 4,
        "dbfilter": "^" + EXPECTED_DATABASE + "$",
        "list_db": False,
    }
    application = runtime.get("application")
    if not isinstance(application, dict):
        raise Refusal("runtime application object is required")
    for key, expected in expected_application.items():
        if application.get(key) != expected:
            raise Refusal(f"runtime application {key} violates the fixed S11 loopback contract")

    exact_admission = {
        "database_name": EXPECTED_DATABASE,
        "database_oid": EXPECTED_OID,
        "cluster_ref": EXPECTED_CLUSTER,
        "database_user": db_user,
        "database_host": database["host"],
        "database_port": db_port,
        "http_host": EXPECTED_HTTP_HOST,
        "http_port": EXPECTED_HTTP_PORT,
        "dbfilter": "^" + EXPECTED_DATABASE + "$",
        "scope_id": scope_id,
        "scope_expires_at_utc": scope["expires_at_utc"],
        "scope_plan_id": PLAN_ID,
        "runtime_config_sha256": hashlib.sha256(runtime_raw).hexdigest(),
        "external_message_provider_enabled": False,
        "outbound_smtp_servers": 0,
    }
    for key, expected in exact_admission.items():
        if admission.get(key) != expected:
            raise Refusal(f"independent admission does not confirm {key}")
    parse_server_address(admission.get("database_server_addr"), "database_server_addr")
    if admission.get("target_identity_verified") is not True:
        raise Refusal("admission must affirm independent target identity verification")
    for fact in (
        "database_grants_verified",
        "database_role_not_superuser",
        "module_install_upgrade_permission_verified",
        "old_s10_protection_verified",
    ):
        if admission.get(fact) is not True:
            raise Refusal(f"admission must independently verify {fact}")
    verifier = admission.get("verified_by")
    receipt = admission.get("verification_receipt")
    preserve = admission.get("preservation_checkpoint_sha256")
    if not isinstance(verifier, str) or not verifier.strip() or not isinstance(receipt, str) or not receipt.strip():
        raise Refusal("admission must identify an independent verifier and verification receipt")
    if not isinstance(preserve, str) or not re.fullmatch(r"[0-9a-f]{64}", preserve):
        raise Refusal("admission must reference the S10 preservation checkpoint SHA-256")
    companies = admission.get("allowed_company_ids")
    stores = admission.get("allowed_store_ids")
    modules = admission.get("installed_modules")
    if not isinstance(companies, list) or not companies or not all(type(i) is int and i > 0 for i in companies):
        raise Refusal("admission must list the independently verified allowed companies")
    if not isinstance(stores, list) or not stores or not all(type(i) is int and i > 0 for i in stores):
        raise Refusal("admission must list the independently verified allowed stores")
    if not isinstance(modules, list) or not all(isinstance(name, str) for name in modules):
        raise Refusal("admission must record the actual installed module set")
    verified_at = parse_utc(admission.get("verified_at_utc"), "admission.verified_at_utc")
    if now - verified_at > dt.timedelta(minutes=30) or verified_at > now:
        raise Refusal("target admission is older than 30 minutes or dated in the future")

    branch, commit = verify_repository(runtime, admission)
    if admission.get("launcher_sha256") != file_sha256(SCRIPT_PATH):
        raise Refusal("admission must attest the exact committed S11 launcher bytes")

    if not PYTHON.is_file() or not os.access(PYTHON, os.X_OK) or not ODOO_BIN.is_file():
        raise Refusal("the locked Python/Odoo command paths are unavailable")
    if not CORE_ADDONS.is_dir() or not REPO_ROOT.is_dir():
        raise Refusal("the locked core or custom addon path is unavailable")
    return runtime, admission, database, branch, commit


def validate_connected_database(env: object) -> None:
    runtime, admission, database, branch, candidate = validate_pair()
    admitted_server_addr = parse_server_address(
        admission.get("database_server_addr"), "database_server_addr")
    env.cr.execute("""SELECT db.oid, current_user, inet_server_addr()::text, inet_server_port(),
        (pg_control_system()).system_identifier::text
        FROM pg_database db WHERE db.datname=current_database()""")
    row = env.cr.fetchone()
    connected_server_addr = parse_server_address(row[2], "connected server address") if row else None
    if (branch != EXPECTED_BRANCH or candidate != admission["candidate_commit"] or
            database["name"] != env.cr.dbname or admission["database_oid"] != EXPECTED_OID or
            admission["cluster_ref"] != EXPECTED_CLUSTER or not row or row[0] != EXPECTED_OID or
            row[1] != database["user"] or connected_server_addr != admitted_server_addr or
            row[3] != database["port"] or row[4] != EXPECTED_CLUSTER or
            runtime["database"]["expected_cluster_ref"] != admission["cluster_ref"]):
        raise Refusal("connected database does not match the authorized S11 scratch admission")


def validate_live_database(database: dict, admission: dict) -> None:
    """Reconfirm the admitted target through a fresh read-only DB connection."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    connection = None
    try:
        connection = psycopg2.connect(
            dbname=database["name"], host=database["host"], port=database["port"],
            user=database["user"], password=database["password"], connect_timeout=5,
            options="-c default_transaction_read_only=on -c statement_timeout=10000",
        )
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""SELECT current_database() AS name,
            (SELECT oid FROM pg_database WHERE datname=current_database()) AS oid,
            current_user AS role, inet_server_addr()::text AS server_addr,
            inet_server_port() AS server_port,
            (pg_control_system()).system_identifier::text AS cluster_ref""")
        identity = cursor.fetchone()
        if (not identity or identity["name"] != EXPECTED_DATABASE or
                identity["oid"] != EXPECTED_OID or identity["role"] != database["user"] or
                parse_server_address(identity["server_addr"], "live server address") !=
                parse_server_address(admission["database_server_addr"], "admitted server address") or
                identity["server_port"] != database["port"] or
                identity["cluster_ref"] != EXPECTED_CLUSTER or
                admission.get("cluster_ref") != identity["cluster_ref"]):
            raise Refusal("live PostgreSQL connection does not match the admitted S11 scratch target")
        cursor.close()
        connection.rollback()
        if connection.get_transaction_status() != psycopg2.extensions.TRANSACTION_STATUS_IDLE:
            raise Refusal("live PostgreSQL identity probe did not return to an idle transaction")
    except Refusal:
        raise
    except Exception as exc:
        raise Refusal("cannot verify the live PostgreSQL identity using the restricted S11 role") from exc
    finally:
        if connection is not None:
            connection.close()


def ensure_private_dir(path: Path) -> None:
    if path.exists():
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise Refusal(f"{path.relative_to(REPO_ROOT)} must be a private user-owned directory")
        return
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)


def proc_start_ticks(pid: int) -> int | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        close = raw.rfind(")")
        fields = raw[close + 2 :].split()
        return int(fields[19])
    except (OSError, ValueError, IndexError):
        return None


def proc_cmdline(pid: int) -> list[str] | None:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        return [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
    except OSError:
        return None


def write_json_exclusive(path: Path, value: dict) -> None:
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json_replace(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    write_json_exclusive(temporary, value)
    os.replace(temporary, path)


class SecretRedactor:
    """Redact private secrets even when a child log splits them across reads."""

    def __init__(self, secrets: list[bytes]):
        self.secrets = [item for item in secrets if item]
        self.pending = b""
        self.keep = max((len(item) for item in self.secrets), default=1) - 1

    def feed(self, chunk: bytes, final: bool = False) -> bytes:
        data = self.pending + chunk
        if final:
            safe, self.pending = data, b""
        elif len(data) <= self.keep:
            self.pending = data
            return b""
        else:
            split = len(data) - self.keep
            while True:
                earlier = split
                for secret in self.secrets:
                    search_from = 0
                    while True:
                        start = data.find(secret, search_from)
                        if start < 0:
                            break
                        if start < split < start + len(secret):
                            earlier = min(earlier, start)
                        search_from = start + 1
                if earlier == split:
                    break
                split = earlier
            safe, self.pending = data[:split], data[split:]
        for secret in self.secrets:
            safe = safe.replace(secret, b"[REDACTED]")
        return safe


def validate_loopback_port() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1.0)
        result = sock.connect_ex((EXPECTED_HTTP_HOST, EXPECTED_HTTP_PORT))
        if result == errno.ECONNREFUSED:
            return
        if result == 0:
            raise Refusal("127.0.0.1:18411 has an active TCP listener")
        raise Refusal(f"127.0.0.1:18411 listener check was inconclusive (socket error {result})")
    except OSError as exc:
        raise Refusal("127.0.0.1:18411 listener check failed; refusing to start") from exc
    finally:
        sock.close()


def read_child_chunk(child: subprocess.Popen, timeout: float = 0.5) -> bytes | None:
    """Read available child output without blocking the supervisor past timeout."""
    if child.stdout is None:
        raise Refusal("owned Odoo process has no captured output stream")
    ready, _, _ = select.select([child.stdout], [], [], timeout)
    if not ready:
        return None
    return os.read(child.stdout.fileno(), 8192)


def stop_grace_elapsed(stopping: bool, stop_deadline: float | None, now: float | None = None) -> bool:
    """Whether a requested child stop has exceeded its monotonic grace period."""
    return bool(stopping and stop_deadline is not None and (time.monotonic() if now is None else now) >= stop_deadline)


def child_exit_diagnostics(
    exit_code: int | None, reason: str, stop_requested: bool = False,
) -> tuple[str, int | None]:
    """Report spontaneous child failures without overwriting an intentional stop reason."""
    if stop_requested and reason == "normal_exit":
        reason = "stop_requested"
    if exit_code is None:
        return reason, None
    if exit_code < 0:
        if reason == "normal_exit":
            reason = "child_signaled"
        return reason, -exit_code
    if exit_code != 0 and reason == "normal_exit":
        return "child_nonzero_exit", None
    return reason, None


def ensure_run_capacity(reserve_bytes: int = MAX_LOG_BYTES) -> None:
    run_dirs = list(RUNS.iterdir())
    if len(run_dirs) >= MAX_RUNS:
        raise Refusal("S11 run history reached its 64-run retention bound; preserve it and review capacity")
    total = 0
    for item in run_dirs:
        info = item.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise Refusal("S11 run history contains a non-directory entry; preserve it for review")
        for child in item.rglob("*"):
            child_info = child.lstat()
            if stat.S_ISREG(child_info.st_mode):
                total += child_info.st_size
            elif not stat.S_ISDIR(child_info.st_mode):
                raise Refusal("S11 run history contains a special entry; preserve it for review")
    if total + reserve_bytes > MAX_TOTAL_RUN_BYTES:
        raise Refusal("S11 run history exceeded the 512 MiB retention bound; preserve it for review")


def resolve_gdb() -> tuple[Path, dict[str, str], str]:
    """Find GDB and return its path, private runtime environment, and version."""
    candidate = shutil.which("gdb")
    local = candidate is None
    binary = Path(candidate) if candidate else LOCAL_GDB
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise Refusal("GDB capture requested but no executable GDB is available")
    env = os.environ.copy()
    if local:
        libdirs = [
            PRIVATE_ROOT / "tooling" / "gdb-root" / "usr" / "lib" / "x86_64-linux-gnu",
            PRIVATE_ROOT / "tooling" / "gdb-root" / "lib" / "x86_64-linux-gnu",
        ]
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            [*(str(path) for path in libdirs), env.get("LD_LIBRARY_PATH", "")]
        ).rstrip(os.pathsep)
        env["S11_GDB_DATA_DIRECTORY"] = str(LOCAL_GDB_DATA)
    try:
        result = subprocess.run(
            [str(binary), "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=10, check=True, env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal("GDB version could not be verified") from exc
    version = result.stdout.splitlines()[0] if result.stdout else ""
    if not version.startswith("GNU gdb "):
        raise Refusal("GDB version output is not recognizable")
    probe = [str(binary), "--batch", "--quiet", "--nx"]
    if "S11_GDB_DATA_DIRECTORY" in env:
        probe.extend(["--data-directory", env["S11_GDB_DATA_DIRECTORY"]])
    probe.extend([
        "-ex", "python import gdb; assert hasattr(gdb.events, 'stop')",
        "-ex", "help generate-core-file",
    ])
    try:
        capability = subprocess.run(
            probe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=10, check=True, env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal("GDB Python events/core-generation capability could not be verified") from exc
    if "generate-core-file" not in capability.stdout:
        raise Refusal("GDB does not advertise generate-core-file support")
    return binary, env, version


def prepare_gdb_process() -> None:
    _soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    soft_limit = MAX_CORE_BYTES if hard == resource.RLIM_INFINITY else min(MAX_CORE_BYTES, hard)
    resource.setrlimit(resource.RLIMIT_FSIZE, (soft_limit, hard))
    os.umask(0o077)


def write_gdb_inferior_wrapper(run_dir: Path) -> Path:
    """Record the inferior identity, then restore its original file-size limit."""
    path = run_dir / "inferior-wrapper.py"
    source = '''import datetime, json, os, resource, sys
raw = open("/proc/self/stat", encoding="ascii").read()
fields = raw[raw.rfind(")") + 2:].split()
identity = {"pid": os.getpid(), "start_ticks": int(fields[19]), "pgid": os.getpgid(0), "sid": os.getsid(0), "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")}
fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    json.dump(identity, stream, sort_keys=True)
    stream.write("\\n")
soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
resource.setrlimit(resource.RLIMIT_FSIZE, (hard, hard))
os.execv(sys.argv[2], [sys.argv[2], *sys.argv[3:]])
'''
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(source)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def process_group_members(pgid: int, sid: int) -> list[int] | None:
    members = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text(encoding="ascii")
            fields = raw[raw.rfind(")") + 2:].split()
            if int(fields[2]) == pgid:
                if int(fields[3]) != sid:
                    return None
                if fields[0] not in ("Z", "X"):
                    members.append(int(entry.name))
        except FileNotFoundError:
            continue
        except (OSError, ValueError, IndexError):
            return None
    return members


def ensure_gdb_group_stopped(run_dir: Path, debugger_pid: int, debugger_ticks: int) -> bool:
    """Stop and verify the private GDB/inferior group before releasing ownership."""
    identity_path = run_dir / "inferior.json"
    try:
        identity_file = identity_path.lstat()
    except FileNotFoundError:
        return False
    if identity_file is not None:
        if (not stat.S_ISREG(identity_file.st_mode) or identity_file.st_uid != os.getuid()
                or stat.S_IMODE(identity_file.st_mode) != 0o600):
            return False
        try:
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if not isinstance(identity, dict):
            return False
    else:
        identity = None

    if identity is not None:
        try:
            inferior_pid = identity["pid"]
            inferior_ticks = identity["start_ticks"]
            inferior_pgid = identity["pgid"]
            inferior_sid = identity["sid"]
            if any(type(value) is not int or value <= 0 for value in (inferior_pid, inferior_ticks, inferior_pgid, inferior_sid)):
                return False
            if inferior_pgid != inferior_pid or inferior_sid != debugger_pid:
                return False
        except (KeyError, TypeError):
            return False
    groups = {debugger_pid}
    groups.add(inferior_pgid)

    def members_by_group() -> dict[int, list[int]] | None:
        result = {}
        for pgid in groups:
            members = process_group_members(pgid, debugger_pid)
            if members is None:
                return None
            result[pgid] = members
        return result

    members = members_by_group()
    if members == {pgid: [] for pgid in groups}:
        return True
    if members is None:
        return False
    for pgid, group_members in members.items():
        if group_members:
            try:
                if pgid == debugger_pid and proc_start_ticks(debugger_pid) == debugger_ticks:
                    if os.getsid(debugger_pid) != debugger_pid:
                        return False
                if identity is not None and pgid == inferior_pgid:
                    if proc_start_ticks(inferior_pid) == inferior_ticks:
                        if os.getpgid(inferior_pid) != inferior_pgid or os.getsid(inferior_pid) != debugger_pid:
                            return False
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + STOP_GRACE_SECONDS
    while time.monotonic() < deadline:
        current = members_by_group()
        if current == {group: [] for group in groups}:
            return True
        if current is None:
            return False
        time.sleep(0.1)
    current = members_by_group()
    if current is None:
        return False
    for pgid, group_members in current.items():
        if group_members:
            try:
                if (pgid == debugger_pid and proc_start_ticks(debugger_pid) == debugger_ticks
                        and os.getsid(debugger_pid) != debugger_pid):
                    return False
                if identity is not None and pgid == inferior_pgid:
                    if proc_start_ticks(inferior_pid) == inferior_ticks:
                        if os.getpgid(inferior_pid) != inferior_pgid or os.getsid(inferior_pid) != debugger_pid:
                            return False
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        current = members_by_group()
        if current == {group: [] for group in groups}:
            return True
        time.sleep(0.1)
    return members_by_group() == {pgid: [] for pgid in groups}


def write_gdb_commands(run_dir: Path, original_ld_library_path: str | None) -> Path:
    """Create a private GDB script that captures only an actual SIGSEGV."""
    core_path = str(run_dir / "core.dump")
    evidence_path = str(run_dir / "native-crash.json")
    max_core_bytes = MAX_CORE_BYTES
    run_id = run_dir.name
    original_ld_code = "None" if original_ld_library_path is None else repr(original_ld_library_path)
    script = f'''set pagination off
set confirm off
set debuginfod enabled off
set print thread-events off
handle SIGSEGV stop print nopass
python
import datetime, gdb, json, os, stat
_s11_original_ld = {original_ld_code}
if _s11_original_ld is None:
    gdb.execute("unset environment LD_LIBRARY_PATH")
else:
    gdb.execute("set environment LD_LIBRARY_PATH " + _s11_original_ld)
def _s11_capture_sigsegv(event):
    if getattr(event, "stop_signal", None) != "SIGSEGV":
        return
    inferior = gdb.selected_inferior()
    record = {{"run_id": {json.dumps(run_id)}, "signal": "SIGSEGV", "pid": inferior.pid, "threads": [{{"global_num": thread.global_num, "ptid": list(thread.ptid), "name": thread.name}} for thread in inferior.threads()], "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), "steps": {{}}}}
    gdb.write("\\nS11_NATIVE_SIGSEGV_CAPTURE_BEGIN\\n")
    for name, command in (("thread_table", "info threads"), ("backtraces", "thread apply all bt full"), ("mappings", "info proc mappings"), ("shared_libraries", "info sharedlibrary"), ("core", "generate-core-file {core_path}")):
        try:
            gdb.execute(command)
            record["steps"][name] = {{"ok": True}}
        except Exception as error:
            record["steps"][name] = {{"ok": False, "error": str(error)}}
    try:
        os.chmod({json.dumps(core_path)}, 0o600)
    except OSError as error:
        record["steps"]["core_permissions"] = {{"ok": False, "error": str(error)}}
    else:
        record["steps"]["core_permissions"] = {{"ok": (os.stat({json.dumps(core_path)}).st_mode & 0o777) == 0o600}}
        if not record["steps"]["core_permissions"]["ok"]:
            record["steps"]["core_permissions"]["error"] = "core mode is not 0600"
    try:
        core_stat = os.stat({json.dumps(core_path)})
        record["core_bytes"] = core_stat.st_size
        record["core_mode"] = oct(os.stat({json.dumps(core_path)}).st_mode & 0o777)
        record["steps"]["core_bound"] = {{"ok": stat.S_ISREG(core_stat.st_mode) and 0 < core_stat.st_size <= {max_core_bytes}}}
        if not record["steps"]["core_bound"]["ok"]:
            record["steps"]["core_bound"]["error"] = "core is absent or exceeds the 256 MiB limit"
    except OSError as error:
        record["core_bytes"] = 0
        record["steps"]["core_bound"] = {{"ok": False, "error": str(error)}}
    record["capture_complete"] = all(item.get("ok") for item in record["steps"].values())
    try:
        with open({json.dumps(evidence_path)}, "x", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True)
            stream.write("\\n")
        os.chmod({json.dumps(evidence_path)}, 0o600)
        gdb.write("S11_NATIVE_SIGSEGV_CAPTURE_END\\n" if record["capture_complete"] else "S11_NATIVE_SIGSEGV_CAPTURE_INCOMPLETE\\n")
    except Exception as error:
        gdb.write("S11_NATIVE_SIGSEGV_SIDECAR_ERROR: " + str(error) + "\\n", gdb.STDERR)
gdb.events.stop.connect(_s11_capture_sigsegv)
end
run
quit
'''
    path = run_dir / "capture.gdb"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(script)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def render_odoo_config(database: dict, run_dir: Path) -> Path:
    config_path = run_dir / "odoo.conf"
    parser = configparser.ConfigParser(interpolation=None)
    parser["options"] = {
        "addons_path": ",".join((str(CORE_ADDONS), str(REPO_ROOT))),
        # Odoo attachment rows store stable filestore hashes in PostgreSQL.
        # Keep the S11-owned filestore across launcher runs so normal web
        # assets and S11-owned attachments remain available after restart.
        "data_dir": str(DATA_DIR),
        "db_host": database["host"],
        "db_port": str(database["port"]),
        "db_user": database["user"],
        "db_password": database["password"],
        "db_name": EXPECTED_DATABASE,
        "dbfilter": "^" + EXPECTED_DATABASE + "$",
        "db_maxconn": "4",
        "list_db": "False",
        "http_interface": EXPECTED_HTTP_HOST,
        "http_port": str(EXPECTED_HTTP_PORT),
        "workers": "0",
        "max_cron_threads": "0",
        "proxy_mode": "False",
        "limit_time_cpu": "600",
        "limit_time_real": str(MAX_SERVER_SECONDS),
        "log_level": "info",
        "logfile": "",
        "smtp_server": "127.0.0.1",
        "smtp_port": "1",
        "smtp_ssl": "False",
    }
    ensure_private_dir(DATA_DIR)
    fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            parser.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            os.unlink(config_path)
        except OSError:
            pass
        raise
    return config_path


def load_active() -> dict:
    data, _ = read_private_json(ACTIVE)
    return data


def own_process_matches(pid: int, start_ticks: int, expected_script: bool = False) -> bool:
    if proc_start_ticks(pid) != start_ticks:
        return False
    argv = proc_cmdline(pid)
    if not argv:
        return False
    if expected_script:
        if len(argv) < 3 or argv[2:] not in (["start"], ["start", "--gdb"], ["--gdb", "start"]):
            return False
        try:
            return Path(argv[1]).resolve(strict=True) == SCRIPT_PATH
        except OSError:
            return False
    return False


def start_service(gdb_capture: bool = False) -> int:
    runtime, admission, database, branch, commit = validate_pair()
    if ACTIVE.exists():
        raise Refusal("an S11 active-owner record already exists; inspect with status, do not replace it")
    validate_live_database(database, admission)
    ensure_private_dir(RUNS)
    gdb_info = resolve_gdb() if gdb_capture else None
    reserve_bytes = MAX_LOG_BYTES + MAX_CORE_BYTES if gdb_capture else MAX_LOG_BYTES
    ensure_run_capacity(reserve_bytes)
    if gdb_capture and shutil.disk_usage(RUNS).free < reserve_bytes + 64 * 1024 * 1024:
        raise Refusal("insufficient free space for the bounded private GDB/core evidence allowance")
    validate_loopback_port()

    run_id = utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    run_dir = RUNS / run_id
    run_dir.mkdir(mode=0o700)
    os.chmod(run_dir, 0o700)
    log_path = run_dir / "server.log"
    config_path = render_odoo_config(database, run_dir)
    gdb_script = write_gdb_commands(run_dir, os.environ.get("LD_LIBRARY_PATH")) if gdb_capture else None
    inferior_wrapper = write_gdb_inferior_wrapper(run_dir) if gdb_capture else None
    started_at = utc_now()
    supervisor_pid = os.getpid()
    supervisor_ticks = proc_start_ticks(supervisor_pid)
    if supervisor_ticks is None:
        raise Refusal("cannot establish the supervisor process birth identity")

    marker = {
        "plan_id": PLAN_ID,
        "run_id": run_id,
        "branch": branch,
        "candidate_commit": commit,
        "core_commit": EXPECTED_CORE_COMMIT,
        "database_name": EXPECTED_DATABASE,
        "database_oid": EXPECTED_OID,
        "cluster_ref": EXPECTED_CLUSTER,
        "scope_id": runtime["scope"]["id"],
        "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "http_host": EXPECTED_HTTP_HOST,
        "http_port": EXPECTED_HTTP_PORT,
        "supervisor_pid": supervisor_pid,
        "supervisor_start_ticks": supervisor_ticks,
        "child_pid": None,
        "child_start_ticks": None,
        "debugger_mode": "gdb" if gdb_capture else "direct",
        "gdb_version": gdb_info[2] if gdb_info else None,
        "config_path": str(config_path),
        "log_path": str(log_path),
        "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
    }
    try:
        write_json_exclusive(ACTIVE, marker)
    except Exception:
        try:
            config_path.unlink()
        except OSError:
            pass
        raise

    if gdb_capture:
        gdb_binary, gdb_env, _gdb_version = gdb_info
        argv = [str(gdb_binary), "--batch", "--quiet", "--nx"]
        if "S11_GDB_DATA_DIRECTORY" in gdb_env:
            argv.extend(["--data-directory", gdb_env["S11_GDB_DATA_DIRECTORY"]])
        argv.extend(["--command", str(gdb_script), "--args", str(PYTHON), str(inferior_wrapper), str(run_dir / "inferior.json"), str(PYTHON), str(ODOO_BIN), "-c", str(config_path)])
    else:
        gdb_env = None
        argv = [str(PYTHON), str(ODOO_BIN), "-c", str(config_path)]
    child = None
    child_ticks = None
    gdb_group_stopped = not gdb_capture
    reason = "normal_exit"
    bytes_written = 0
    stopping = False
    stop_deadline = None

    def stop_child(signum: int | None = None, _frame=None) -> None:
        nonlocal stopping, stop_deadline
        stopping = True
        if stop_deadline is None:
            stop_deadline = time.monotonic() + STOP_GRACE_SECONDS
        if child is not None and child.poll() is None:
            try:
                if gdb_capture:
                    if child_ticks is None or proc_start_ticks(child.pid) != child_ticks or os.getpgid(child.pid) != child.pid:
                        return
                    os.killpg(child.pid, signal.SIGTERM)
                else:
                    child.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass

    old_term = signal.signal(signal.SIGTERM, stop_child)
    old_int = signal.signal(signal.SIGINT, stop_child)
    redactor = SecretRedactor([database["password"].encode("utf-8")])
    try:
        child = subprocess.Popen(
            argv,
            cwd=str(ODOO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
            shell=False,
            bufsize=0,
            env=gdb_env,
            preexec_fn=prepare_gdb_process if gdb_capture else None,
        )
        child_ticks = proc_start_ticks(child.pid)
        if child_ticks is None:
            stop_child()
            raise Refusal("cannot establish the Odoo child process birth identity")
        if gdb_capture and os.getpgid(child.pid) != child.pid:
            stop_child()
            raise Refusal("cannot verify the owned GDB process group")
        marker["child_pid"] = child.pid
        marker["child_start_ticks"] = child_ticks
        write_json_replace(ACTIVE, marker)
        print(f"S11 owned service started: run_id={run_id} pid={child.pid} port=18411", flush=True)
        deadline = min(
            started_at + dt.timedelta(seconds=MAX_SERVER_SECONDS),
            parse_utc(runtime["scope"]["expires_at_utc"], "scope.expires_at_utc"),
        )
        with log_path.open("xb") as log:
            os.chmod(log_path, 0o600)
            assert child.stdout is not None
            while True:
                if utc_now() >= deadline and not stopping:
                    reason = "bounded_runtime_expired"
                    stop_child()
                if stop_grace_elapsed(stopping, stop_deadline):
                    reason = "stop_grace_expired_child_killed"
                    try:
                        # This is the exact Odoo child created by this supervisor;
                        # Popen retains its process identity, so escalation cannot
                        # target an unrelated PID or a replacement process.
                        if gdb_capture:
                            if child_ticks is None or proc_start_ticks(child.pid) != child_ticks or os.getpgid(child.pid) != child.pid:
                                reason = "stop_group_identity_unverified"
                                break
                            os.killpg(child.pid, signal.SIGKILL)
                        else:
                            child.kill()
                        child.wait(timeout=5)
                    except (OSError, subprocess.TimeoutExpired):
                        reason = "stop_grace_expired_child_still_running"
                    break
                # Check the deadline even if Odoo is completely quiet. A
                # buffered blocking read can wait forever for a full pipe
                # buffer and would defeat both the run bound and stop path.
                chunk = read_child_chunk(child)
                if gdb_capture and not marker.get("inferior_pid"):
                    identity_path = run_dir / "inferior.json"
                    try:
                        inferior_identity = json.loads(identity_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        inferior_identity = None
                    if isinstance(inferior_identity, dict):
                        marker["inferior_pid"] = inferior_identity.get("pid")
                        marker["inferior_start_ticks"] = inferior_identity.get("start_ticks")
                        marker["inferior_pgid"] = inferior_identity.get("pgid")
                        marker["inferior_sid"] = inferior_identity.get("sid")
                        write_json_replace(ACTIVE, marker)
                if chunk is None:
                    if child.poll() is not None:
                        break
                    continue
                if chunk:
                    safe_chunk = redactor.feed(chunk)
                    remaining = MAX_LOG_BYTES - bytes_written
                    if remaining > 0:
                        written = safe_chunk[:remaining]
                        log.write(written)
                        log.flush()
                        bytes_written += len(written)
                    if len(safe_chunk) > remaining or bytes_written >= MAX_LOG_BYTES:
                        reason = "bounded_log_limit_reached"
                        stop_child()
                elif child.poll() is not None:
                    tail = redactor.feed(b"", final=True)
                    remaining = MAX_LOG_BYTES - bytes_written
                    if remaining > 0 and tail:
                        log.write(tail[:remaining])
                        log.flush()
                        bytes_written += min(len(tail), remaining)
                    break
                elif stopping:
                    remaining = max(0.0, (stop_deadline or time.monotonic()) - time.monotonic())
                    try:
                        child.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        reason = "stop_grace_expired_child_still_running"
                    break
        try:
            child_exit = child.wait(timeout=0 if stopping else STOP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            reason = "stop_grace_expired_child_still_running"
            child_exit = None
        reason, child_signal = child_exit_diagnostics(child_exit, reason, stopping)
        native_crash_path = run_dir / "native-crash.json"
        try:
            native_crash = json.loads(native_crash_path.read_text(encoding="utf-8")) if native_crash_path.exists() else None
        except (OSError, json.JSONDecodeError):
            native_crash = None
        inferior_path = run_dir / "inferior.json"
        try:
            inferior_info = json.loads(inferior_path.read_text(encoding="utf-8")) if inferior_path.exists() else None
        except (OSError, json.JSONDecodeError):
            inferior_info = None
        if gdb_capture:
            if isinstance(inferior_info, dict):
                marker["inferior_pid"] = inferior_info.get("pid")
                marker["inferior_start_ticks"] = inferior_info.get("start_ticks")
                marker["inferior_pgid"] = inferior_info.get("pgid")
                marker["inferior_sid"] = inferior_info.get("sid")
                write_json_replace(ACTIVE, marker)
            gdb_group_stopped = ensure_gdb_group_stopped(run_dir, child.pid, child_ticks)
            if not gdb_group_stopped:
                reason = "owned_gdb_group_still_running_or_unverified"
        core_path = run_dir / "core.dump"
        if native_crash and reason == "normal_exit":
            reason = "inferior_sigsegv_observed"
        receipt = {
            "plan_id": PLAN_ID,
            "run_id": run_id,
            "candidate_commit": commit,
            "child_pid": child.pid,
            "child_start_ticks": child_ticks,
            "child_exit_code": child_exit,
            "child_signal_number": child_signal,
            "debugger_mode": "gdb" if gdb_capture else "direct",
            "gdb_version": gdb_info[2] if gdb_info else None,
            "native_crash_evidence": native_crash is not None,
            "capture_complete": native_crash.get("capture_complete") if native_crash else None,
            "inferior_pid": native_crash.get("pid") if native_crash else inferior_info.get("pid") if inferior_info else None,
            "inferior_signal": native_crash.get("signal") if native_crash else None,
            "inferior_start_ticks": inferior_info.get("start_ticks") if isinstance(inferior_info, dict) else None,
            "inferior_pgid": inferior_info.get("pgid") if isinstance(inferior_info, dict) else None,
            "inferior_sid": inferior_info.get("sid") if isinstance(inferior_info, dict) else None,
            "owned_process_group_stopped": gdb_group_stopped,
            "core_bytes": core_path.stat().st_size if core_path.exists() else 0,
            "reason": reason,
            "log_bytes": bytes_written,
            "log_limit_bytes": MAX_LOG_BYTES,
            "finished_at_utc": utc_now().isoformat().replace("+00:00", "Z"),
        }
        write_json_exclusive(run_dir / "exit.json", receipt)
        if child_exit is None or not gdb_group_stopped:
            print(f"S11 service stop incomplete; owned child still requires inspection: run_id={run_id}", file=sys.stderr)
            return 3
        return child_exit
    finally:
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)
        # If setup or supervision raises unexpectedly, this exact child was
        # created by this supervisor and must not be left detached.
        child_stopped = child is None or child.poll() is not None
        if gdb_capture and child is not None:
            if child.poll() is None and not stopping:
                try:
                    stop_child()
                    child.wait(timeout=STOP_GRACE_SECONDS)
                except (OSError, subprocess.SubprocessError):
                    # Preserve the owner marker for later inspection; never
                    # escalate to an unverified force kill.
                    pass
            if child.poll() is not None and child_ticks is not None:
                gdb_group_stopped = ensure_gdb_group_stopped(run_dir, child.pid, child_ticks)
            child_stopped = child.poll() is not None and gdb_group_stopped
        elif child is not None and child.poll() is None:
            if not stopping:
                try:
                    child.send_signal(signal.SIGTERM)
                    child.wait(timeout=STOP_GRACE_SECONDS)
                    child_stopped = child.poll() is not None
                except (OSError, subprocess.TimeoutExpired):
                    child_stopped = child.poll() is not None
        # Do not delete a marker unless this exact supervisor owns it.
        if child_stopped:
            try:
                current = load_active()
                if current.get("supervisor_pid") == supervisor_pid and current.get("supervisor_start_ticks") == supervisor_ticks:
                    ACTIVE.unlink()
            except (OSError, Refusal):
                pass
            if child is not None and child.stdout is not None:
                child.stdout.close()
        # The private config contains the database password; remove it after
        # shutdown while retaining only redacted lifecycle metadata and logs.
        try:
            config_path.unlink()
        except (OSError, UnboundLocalError):
            pass


def status_service() -> int:
    if not PRIVATE_ROOT.exists():
        print("S11 owned service: STOPPED (no S11 private runtime directory)")
        return 0
    ensure_private_root()
    if not ACTIVE.exists():
        print("S11 owned service: STOPPED (no active-owner record)")
        return 0
    marker = load_active()
    if marker.get("plan_id") != PLAN_ID or marker.get("database_name") != EXPECTED_DATABASE or marker.get("http_port") != EXPECTED_HTTP_PORT:
        raise Refusal("active-owner record does not match this S11 launcher")
    pid = marker.get("supervisor_pid")
    ticks = marker.get("supervisor_start_ticks")
    if type(pid) is not int or type(ticks) is not int or not own_process_matches(pid, ticks, expected_script=True):
        print("S11 owned service: STALE_OWNER_RECORD (no signal sent; preserve for review)", file=sys.stderr)
        return 3
    child_pid = marker.get("child_pid")
    child_alive = type(child_pid) is int and proc_start_ticks(child_pid) == marker.get("child_start_ticks")
    state = "RUNNING" if child_alive else "STARTING_OR_EXITING"
    print(f"S11 owned service: {state} run_id={marker.get('run_id')} pid={child_pid} port=18411")
    return 0


def stop_service() -> int:
    if not PRIVATE_ROOT.exists():
        print("S11 owned service: already stopped (no S11 private runtime directory)")
        return 0
    ensure_private_root()
    if not ACTIVE.exists():
        print("S11 owned service: already stopped")
        return 0
    marker = load_active()
    if marker.get("plan_id") != PLAN_ID or marker.get("database_name") != EXPECTED_DATABASE or marker.get("http_port") != EXPECTED_HTTP_PORT:
        raise Refusal("active-owner record does not match this S11 launcher")
    pid = marker.get("supervisor_pid")
    ticks = marker.get("supervisor_start_ticks")
    if type(pid) is not int or type(ticks) is not int or not own_process_matches(pid, ticks, expected_script=True):
        raise Refusal("owner process birth/cmdline does not match; no signal sent")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        if proc_start_ticks(pid) != ticks:
            print(f"S11 owned service already exited: run_id={marker.get('run_id')}")
            return 0
        raise Refusal("verified supervisor disappeared before stop signal; no retry performed")
    deadline = time.monotonic() + STOP_GRACE_SECONDS + 5
    while time.monotonic() < deadline:
        if proc_start_ticks(pid) != ticks:
            print(f"S11 owned service stop requested and supervisor exited: run_id={marker.get('run_id')}")
            return 0
        time.sleep(0.2)
    raise Refusal("owned supervisor did not exit within the bounded stop wait; no force kill sent")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "stop", "status"))
    parser.add_argument("--gdb", action="store_true", help="run the owned S11 service under GDB and capture a private core on SIGSEGV")
    args = parser.parse_args()
    try:
        if args.command == "start":
            return start_service(gdb_capture=args.gdb)
        if args.gdb:
            raise Refusal("--gdb is valid only with the start command")
        if args.command == "stop":
            return stop_service()
        return status_service()
    except Refusal as exc:
        print(f"S11 launcher refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
