#!/usr/bin/env python3
"""Launch the fixed S11 scratch server with its session clock debug entrance enabled."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 's11'))
import launcher as L


def private_write(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def main() -> int:
    try:
        if Path(sys.executable).resolve() != L.PYTHON.resolve():
            raise L.Refusal('use the locked S11 virtualenv Python')
        L.ensure_private_root()
        runtime, admission, database, branch, commit = L.validate_pair()
        L.validate_live_database(database, admission)
        if L.ACTIVE.exists() or L.status_service() != 0:
            raise L.Refusal('the S11 service must be stopped before opening the debug-clock entrance')
        L.validate_loopback_port()
        run_root = L.PRIVATE_ROOT / 'clock-runs'
        L.ensure_private_dir(run_root)
        if len(list(run_root.iterdir())) >= L.MAX_RUNS:
            raise L.Refusal('S11 debug-clock history reached its bound; preserve and review it')
        started = L.utc_now()
        run_id = started.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
        run_dir = run_root / run_id
        run_dir.mkdir(mode=0o700)
        os.chmod(run_dir, 0o700)
        manifest = {
            'mode': 'S11_SESSION_CLOCK', 'run_id': run_id,
            'physical_started_at_utc': started.isoformat().replace('+00:00', 'Z'),
            'branch': branch, 'candidate_commit': commit,
            'database_name': database['name'], 'database_oid': database['expected_oid'],
            'database_cluster': database['expected_cluster_ref'],
            'runtime_sha256': L.file_sha256(L.RUNTIME_CONFIG),
            'admission_sha256': L.file_sha256(L.ADMISSION),
            'scope_id': runtime['scope']['id'],
            'scope_expires_at_utc': runtime['scope']['expires_at_utc'],
            'system_clock_changed': False, 'postgres_clock_changed': False,
        }
        raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
        private_write(run_dir / 'clock.json', raw)
        env = os.environ.copy()
        env.update({
            'YDENTAL_S11_CLOCK_RUN_ID': run_id,
            'YDENTAL_S11_CLOCK_RUN_DIR': str(run_dir),
            'YDENTAL_S11_CLOCK_MANIFEST_SHA256': hashlib.sha256(raw).hexdigest(),
        })
        print(json.dumps({'mode': manifest['mode'], 'run_id': run_id,
                          'candidate_commit': commit, 'database': database['name'],
                          'clock_entry': '/ydental/s11/debug-clock',
                          'manifest': str((run_dir / 'clock.json').relative_to(ROOT))}, sort_keys=True), flush=True)
        os.execve(sys.executable, [sys.executable, str(ROOT / 'scripts' / 's11' / 'launcher.py'),
                                   'start', '--gdb', '--s11-clock'], env)
    except L.Refusal as exc:
        print(f'S11 debug clock refused: {exc}', file=sys.stderr)
        return 2
    except OSError as exc:
        print(f'S11 debug clock failed before launcher exec: {type(exc).__name__}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
