# S13 limited UX execution tools

These tools support `YD-S13-UX-DOCUMENTS-V1` only, on
`codex/s13-ux-documents-r1`, retaining the existing database
`ydental_s11_synth_20261023_01` / OID2171423 / cluster7694897083368259627
and `.local/s11/new-target-data` filestore. No database is created, copied or renamed.

The small admission/launcher adapters reuse S12 target checks, font and private
PDF wheel validation and the S11 owned foreground supervisor. S13 has its own
runtime/scope/admission/active/runs; existing S11/S12 scopes are not renewed.
An older active-owner record prevents S13 start or upgrade. Resolve its actual
normal lifecycle first; no tool clears STOP or stale owner records.

`capture_before.py` is a one-time normal-browser baseline of the explicitly named
S12 process. It records that process, its loaded-code candidate, current dirty
paths and the possible static-file difference. It does not assert a frozen S13
candidate. Its helper is the existing approved local S12 browser source. It
performs normal login/store selection and GETs, without generating or handling
business. The before screenshot manifest is private.

`protected_snapshot.py collect --phase baseline` reads a complete source/file
projection but is **not** an upgrade authorization. `pre`/`post` still require an
exact clean candidate and actual writer freeze. All credential, bearer/session
and authentication hash columns are removed before SELECT; clinical text and
business binary are represented by private hashes. The local snapshot is never
published. `compare` runs offline and requires independent classification.

Typical sequence (replace COMMIT/LABEL with actual fixed values):

```sh
../.venv/bin/python -m unittest discover -s scripts/s13 -p test_runtime.py -v
../.venv/bin/python scripts/s13/runtime_config.py create --candidate COMMIT --operator /root --hours 8
../.venv/bin/python scripts/s13/admission_probe.py --provider .local/s13/runtime.json --output .local/s13/admission/LABEL-probe.json --operator /root/tester
```

A named non-implementer independently reviews the actual probe, source/file
checkpoint, runtime and launcher bytes and writes a private receipt with:
`status=S13_RUNTIME_ADMISSION_REVIEWED`, `reviewer`, `candidate_commit`,
`probe_sha256`, `checkpoint_sha256`, `runtime_sha256`, `launcher_sha256`, and
`reviewed_no_product_or_test_tool_implementation=true`. Binding this receipt is
metadata preparation, not business acceptance:

```sh
../.venv/bin/python scripts/s13/bind_admission.py --probe .local/s13/admission/LABEL-probe.json --checkpoint .local/s13/verification/upgrade-initial-baseline.json --review .local/s13/acceptance/LABEL-runtime-review.json
../.venv/bin/python scripts/s13/launcher.py status
```

`launcher.py start` remains foreground-owned and is invoked by the main agent
only after the actual fixed-candidate checks. It does not upgrade any module.
`stop` retains exact process birth/ownership checks and normal exit receipts.
Legacy human-readable S11/S12 messages may remain in the reused engine; structured
plan/branch/scope/paths identify S13. Neither metadata nor test role names prove
platform permission or OS isolation.

The main agent creates an actual private writer-freeze receipt containing
`candidate_commit`, `database`, `database_oid`, `modules`, `writers_quiescent=true`.
Then:

```sh
../.venv/bin/python scripts/s13/protected_snapshot.py collect --phase pre --label LABEL --candidate COMMIT --modules AFFECTED_MODULES --freeze-receipt .local/s13/verification/LABEL-freeze.json
../.venv/bin/python scripts/s13/run_checks.py --phase upgrade --candidate COMMIT --modules AFFECTED_MODULES --freeze .local/s13/verification/LABEL-freeze.json --pre .local/s13/verification/upgrade-LABEL-pre.json --label LABEL
../.venv/bin/python scripts/s13/protected_snapshot.py collect --phase post --label LABEL --candidate COMMIT --modules AFFECTED_MODULES --freeze-receipt .local/s13/verification/LABEL-freeze.json
```

No upgrade runs after an incomplete pre. A timeout keeps exact child identity and
unknown outcome; it is not automatically retried or killed. Native failure stops
the affected operation. The installed `ydental_s12_test` addon remains an optional
existing rollback/HTTP regression target; its old name does not imply full S12
business replay or user acceptance. New normal-browser/HTTP results and PDF/QR
facts are separate from SOURCE/PURE, MODEL and independently committed state.

Credentials stay only in explicitly authorized normal local providers. No
password, cookie, CSRF, session/profile, raw request body or connection secret is
recorded in public output. Original PDFs, screenshots, raw results and hashes
remain under ignored mode-0700 `.local/s13/` with mode-0600 files.
