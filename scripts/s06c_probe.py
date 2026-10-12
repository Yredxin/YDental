import runpy
from pathlib import Path
# C advances synthetic request clocks across several days. Build the A/B UI
# fixtures afterwards so those clocks cannot expire their live holder fixtures.
runpy.run_path(str(Path(__file__).with_name('s06c_day_probe.py')), init_globals={'env': env})
runpy.run_path(str(Path(__file__).with_name('s06c_b_probe.py')), init_globals={'env': env})
