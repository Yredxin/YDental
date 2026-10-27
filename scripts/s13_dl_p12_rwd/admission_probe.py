"""RWD destination and plan binding; reuse the unchanged native identity probe."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/admission_probe.py'
spec = importlib.util.spec_from_file_location('p12_rwd_probe_source', SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
engine = source.engine
engine.PRIVATE = ROOT / '.local/dl-p12-rwd'
engine.PLAN = 'YD-S13-DL-P12-RWD'
_previous_write = engine.write_receipt


def write_receipt(path, value):
    if isinstance(value, dict):
        value = dict(value, rwd_probe_binding_sha256=engine.hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest())
    return _previous_write(path, value)


engine.write_receipt = write_receipt


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
