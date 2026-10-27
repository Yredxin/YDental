"""P13 stage binding of the unchanged frozen native upgrade runner."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/run_checks.py'
spec = importlib.util.spec_from_file_location('p13_frozen_native_check', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

if __name__ == '__main__':
    raise SystemExit(engine.main())
