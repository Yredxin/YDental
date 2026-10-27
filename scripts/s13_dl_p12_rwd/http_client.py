"""Bind normal P12 authentication and exact owned-run checks to the RWD scope."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/http_client.py'
spec = importlib.util.spec_from_file_location('p12_rwd_normal_http', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def __getattr__(name):
    return getattr(engine, name)
