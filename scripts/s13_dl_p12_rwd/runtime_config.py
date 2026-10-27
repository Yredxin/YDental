"""Create fresh RWD metadata without changing any previous scope or guard."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/runtime_config.py'
spec = importlib.util.spec_from_file_location('p12_rwd_runtime_source', SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.RUNTIME = engine.PRIVATE / 'runtime.json'
_create = engine.create


def create(candidate, hours, operator):
    if engine.RUNTIME.exists():
        raise RuntimeError('Create is exclusive; rebind an unexpired scope explicitly.')
    return _create(candidate, hours, operator)


engine.create = create


if __name__ == '__main__':
    engine.main()
