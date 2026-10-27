"""New RWD scope binding of the unchanged P12 supervisor and native guards."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/launcher.py'
spec = importlib.util.spec_from_file_location('p12_rwd_supervisor_source', SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
engine = source.engine
base = source.base
base.PLAN_ID = 'YD-S13-DL-P12-RWD'
base.PRIVATE_ROOT = ROOT / '.local/dl-p12-rwd'
base.RUNTIME_CONFIG = base.PRIVATE_ROOT / 'runtime.json'
base.ADMISSION = base.PRIVATE_ROOT / 'admission.json'
base.RUNS = base.PRIVATE_ROOT / 'runs'
base.ACTIVE = base.PRIVATE_ROOT / 'active.json'
base.SCRIPT_PATH = Path(__file__).resolve()
_validate = source.validate_pair


def validate_pair():
    if (ROOT / '.local/dl-p12/active.json').exists():
        raise base.Refusal('Resolve the prior P12 owner through its normal lifecycle.')
    return _validate()


engine.validate_pair = validate_pair
base.validate_pair = validate_pair


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
