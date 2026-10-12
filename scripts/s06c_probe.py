import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('s06c_b_probe.py')), init_globals={'env': env})
runpy.run_path(str(Path(__file__).with_name('s06c_day_probe.py')), init_globals={'env': env})
