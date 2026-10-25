#!/usr/bin/env python3
"""S13 binding for the existing read-only sole-target admission probe.

Only the stage record destination and plan/branch change. The existing provider,
identity, native privilege and outbound checks remain in the reused source.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s12/admission_probe.py'
spec = importlib.util.spec_from_file_location('ydental_s13_readonly_probe', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.PRIVATE = ROOT / '.local/dl-p5'
engine.PLAN = 'YD-S13-DL-P5'
engine.BRANCH = 'codex/s13-dl-p5-settlement-lookup-r1'
_write = engine.write_receipt


def write_receipt(path, value):
    if isinstance(value, dict):
        value = dict(value, dl_p5_probe_binding_sha256=engine.hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     reused_probe_sha256=engine.hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    return _write(path, value)


engine.write_receipt = write_receipt


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
