"""P13 binding of normal login, exact owned-run and GET-only business guards."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/http_client.py'
source = SOURCE.read_text().replace('docs/reports/s13-dl-p12/', 'docs/reports/s13-dl-p13/')
spec = importlib.util.spec_from_file_location('p13_normal_http', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)


def __getattr__(name):
    return getattr(engine, name)
