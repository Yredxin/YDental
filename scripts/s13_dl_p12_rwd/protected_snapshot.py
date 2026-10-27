"""RWD output binding of the unchanged complete native projection and guards."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/protected_snapshot.py'
spec = importlib.util.spec_from_file_location('p12_rwd_complete_projection', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.PRIVATE = ROOT / '.local/dl-p12-rwd'


def __getattr__(name):
    return getattr(engine, name)


if __name__ == '__main__':
    raise SystemExit(engine.main())
