"""Read the actual loaded combined QWeb through the unchanged native RO runner."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/runtime_views.py'
source = SOURCE.read_text().replace('.local/dl-p12', '.local/dl-p13')
source = source.replace('YDENTAL_P12_VIEW_LABEL', 'YDENTAL_P13_VIEW_LABEL')
source = source.replace('P12_ACTUAL_NATIVE_COMBINED_ARCH_COMPLETE', 'P13_ACTUAL_NATIVE_COMBINED_ARCH_COMPLETE')
spec = importlib.util.spec_from_file_location('p13_native_views', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)

if __name__ == '__main__':
    raise SystemExit(engine.main())
