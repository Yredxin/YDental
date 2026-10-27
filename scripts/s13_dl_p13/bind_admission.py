"""Bind unchanged native admission checks to independently reviewed P13 facts."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/bind_admission.py'
source = SOURCE.read_text().replace('DLP12_', 'DLP13_')
source = source.replace(
    'DL-P12 settlement lookup and read-only fee presentation only; normal GET search, explicit patient selection, fee trace and pagination reads allowed; no economic/stock/document/print/sign/template/scan actions, new originals, next plan or production',
    'DL-P13 first bill panel presentation and read-only interaction only; normal authentication/store selection and GET allowed; no live operation=bill, other economic/stock/PDF/print/sign/scan actions, persistent fixtures, next plan or production')
spec = importlib.util.spec_from_file_location('p13_bind_admission', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)

if __name__ == '__main__':
    engine.main()
