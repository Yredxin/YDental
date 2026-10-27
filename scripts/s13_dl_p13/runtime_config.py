"""Fresh P13 resource metadata using the existing create/rebind implementation."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/runtime_config.py'
source = SOURCE.read_text()
source = source.replace("'dl-p12-'", "'dl-p13-'")
source = source.replace("ROOT/'.local/dl-p11/active.json'", "ROOT/'.local/dl-p11/active.json',ROOT/'.local/dl-p12/active.json',ROOT/'.local/dl-p12-rwd/active.json'")
source = source.replace(
    'Authorized DL-P12 settlement patient lookup and read-only fee actions, static SVG and spacing verification; normal patient candidate search, explicit selection, fee trace and pagination GET only; no economic, inventory, document or external business',
    'Authorized DL-P13 first bill panel presentation and read-only interaction verification; normal authentication, store selection and GET only; no live operation=bill or other economic, inventory, PDF, external or persistent fixture actions')
spec = importlib.util.spec_from_file_location('p13_resource_metadata', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)
engine.RUNTIME = engine.PRIVATE / 'runtime.json'
engine.ANCHOR = '4e3e3aa1027286de473044d23f54d5faa81c9384'
_create = engine.create


def create(candidate, hours, operator):
    if engine.RUNTIME.exists():
        raise RuntimeError('Create is exclusive; rebind an unexpired scope explicitly.')
    return _create(candidate, hours, operator)


engine.create = create

if __name__ == '__main__':
    engine.main()
