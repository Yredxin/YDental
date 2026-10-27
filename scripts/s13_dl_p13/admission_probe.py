"""P13 plan/branch/output binding of the unchanged sole-target native probe."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s12/admission_probe.py'
spec = importlib.util.spec_from_file_location('p13_native_probe', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.PRIVATE = ROOT / '.local/dl-p13'
engine.PLAN = 'YD-S13-DL-P13'
engine.BRANCH = 'codex/s13-dl-p13-settlement-bill-panel-r1'
_original_write = engine.write_receipt


def write_receipt(path, value):
    if isinstance(value, dict):
        value = dict(value, p13_probe_binding_sha256=engine.hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
            reused_probe_sha256=engine.hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    return _original_write(path, value)


engine.write_receipt = write_receipt


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
