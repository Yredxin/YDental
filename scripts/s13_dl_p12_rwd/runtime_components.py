"""Render identical loaded-QWeb fixtures to a fresh RWD output, with rollback."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/runtime_components.py'
spec = importlib.util.spec_from_file_location('p12_rwd_components_source', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.SCRIPT = engine.SCRIPT.replace("private=root/'.local/dl-p12'", "private=root/'.local/dl-p12-rwd'")

if __name__ == '__main__':
    engine.main()
