"""Fresh P13 owner binding; keep the existing supervisor and native guards."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s12/launcher.py'
spec = importlib.util.spec_from_file_location('p13_native_supervisor', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
base = engine.engine
base.PLAN_ID = 'YD-S13-DL-P13'
base.EXPECTED_BRANCH = 'codex/s13-dl-p13-settlement-bill-panel-r1'
base.PRIVATE_ROOT = ROOT / '.local/dl-p13'
base.RUNTIME_CONFIG = base.PRIVATE_ROOT / 'runtime.json'
base.ADMISSION = base.PRIVATE_ROOT / 'admission.json'
base.RUNS = base.PRIVATE_ROOT / 'runs'
base.ACTIVE = base.PRIVATE_ROOT / 'active.json'
base.SCRIPT_PATH = Path(__file__).resolve()
base.DOC_ONLY_CANDIDATE_PATHS = (
    'CURRENT_TASK.md', 'docs/reports/s13-dl-p13/', 'scripts/s13_dl_p13/README.md',
)
_validate = engine.validate_pair


def validate_pair():
    previous = ['s12', 's13'] + ['dl-p' + str(i) for i in range(1, 13)] + ['dl-p12-rwd']
    if any((ROOT / '.local' / name / 'active.json').exists() for name in previous):
        raise base.Refusal('Resolve the exact earlier owner through its normal lifecycle.')
    value = _validate()
    if value[1].get('pdf_environment_adapter_sha256') != base.file_sha256(SOURCE):
        raise base.Refusal('Admission must bind the reused S12 environment adapter.')
    return value


engine.validate_pair = validate_pair
base.validate_pair = validate_pair


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
