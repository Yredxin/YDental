# DL-P4 scoped runtime adapters

Reuse the existing S12/S11 sole-target read-only admission, supervisor, protected projection and normal-login clients. Stage records use `.local/dl-p4`; the only allowed module load is `ydental_reporting`. Core, database, filestore, privilege checks, process birth, no-clock and shutdown contracts stay fixed. Previous P1–P3 owner markers also prevent conflicting execution.

`runtime_config.py create` creates a new P4 scope without admission or DB writes. A fresh probe, full protection checkpoint and named independent review are required by `bind_admission.py` before launch. An exact clean fixed candidate is required for module loads; report-only later commits do not change the product candidate. Never renew or erase older scope/STOP records, replay old business, or print private provider values.

`test_runtime.py` is a pure boundary check, not business evidence. Detailed actual execution, field contracts, test layers and independent results belong in `docs/reports/s13-dl-p4/`.
