"""Bind the unchanged P12 admission rules to explicitly reviewed new RWD facts."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/bind_admission.py'
spec = importlib.util.spec_from_file_location('p12_rwd_bind_source', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

if __name__ == '__main__':
    engine.main()
