"""P13 identity/output binding of the unchanged complete native projection.

The single hard-coded branch and plan label are rebound explicitly. All native
identity, privilege, anchor, schema, file, scope and transaction checks remain.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/protected_snapshot.py'
source = SOURCE.read_text()
old = "branch!='codex/s13-dl-p12-settlement-readonly-actions-spacing-r1'"
assert source.count(old) == 1
source = source.replace(old, "branch!='codex/s13-dl-p13-settlement-bill-panel-r1'")
source = source.replace("'docs/reports/s13-dl-p12/'", "'docs/reports/s13-dl-p13/'")
source = source.replace("'plan_id':'YD-S13-DL-P12'", "'plan_id':'YD-S13-DL-P13'")
spec = importlib.util.spec_from_file_location('p13_complete_projection', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)
engine.PRIVATE = ROOT / '.local/dl-p13'


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
