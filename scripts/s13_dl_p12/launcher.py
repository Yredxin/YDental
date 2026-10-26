#!/usr/bin/env python3
"""Stage-specific binding of the existing S11 supervisor and S12 PDF environment.

Keeps the sole target, original filestore, normal identity checks, process birth
and shutdown semantics. It neither starts older scopes nor changes their records.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s12/launcher.py'
spec = importlib.util.spec_from_file_location('ydental_s13_pdf_supervisor', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
base = engine.engine
base.PLAN_ID = 'YD-S13-DL-P12'
base.EXPECTED_BRANCH = 'codex/s13-dl-p12-settlement-readonly-actions-spacing-r1'
base.PRIVATE_ROOT = ROOT / '.local/dl-p12'
base.RUNTIME_CONFIG = base.PRIVATE_ROOT / 'runtime.json'
base.ADMISSION = base.PRIVATE_ROOT / 'admission.json'
base.RUNS = base.PRIVATE_ROOT / 'runs'
base.ACTIVE = base.PRIVATE_ROOT / 'active.json'
base.SCRIPT_PATH = Path(__file__).resolve()
base.DOC_ONLY_CANDIDATE_PATHS = ('CURRENT_TASK.md', 'docs/reports/s13-dl-p12/', 'scripts/s13_dl_p12/README.md')
_validate = engine.validate_pair


def validate_pair():
    value = _validate()
    if any((ROOT / path).exists() for path in ('.local/s12/active.json', '.local/s13/active.json', '.local/dl-p1/active.json', '.local/dl-p2/active.json', '.local/dl-p3/active.json', '.local/dl-p4/active.json', '.local/dl-p5/active.json', '.local/dl-p6/active.json', '.local/dl-p7/active.json', '.local/dl-p8/active.json', '.local/dl-p9/active.json', '.local/dl-p10/active.json', '.local/dl-p11/active.json')):
        raise base.Refusal('The sole target has an earlier S12/S13 owner record; resolve its normal lifecycle before S13.')
    if value[1].get('pdf_environment_adapter_sha256') != base.file_sha256(SOURCE):
        raise base.Refusal('Admission must bind the exact reused S12 PDF environment adapter.')
    return value


engine.validate_pair = validate_pair
base.validate_pair = validate_pair


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
