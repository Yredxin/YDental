"""Reuse the exact S13 normal browser primitives and reviewed native dependency."""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13/browser_client.py'
spec = importlib.util.spec_from_file_location('ydental_dl_p3_normal_browser', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
def __getattr__(name):
    return getattr(engine, name)
