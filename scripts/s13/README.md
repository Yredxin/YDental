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

Baselines use the current S13 runtime and its actual scope. The explicit
`--initial-s12-baseline` option is only available before an S13 runtime exists;
it records the initial S12 handover without changing that old resource scope.

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

## Corrective private browser dependency binding

The earlier paired-image client exited with real SIGSEGV/139 after printing its
manifest. That result remains failed at the process layer. Kernel evidence and
original source/result hashes are private; its cause remains UNKNOWN. The Odoo
owned service was separately checked and normally stopped, with child exit 0.

Static investigation identified an actual independent dependency mismatch: the
approved package snapshot contains Playwright 1.64.0 and greenlet 3.0.3, while
Playwright declares `greenlet>=3.1.1,<4`. The old snapshot remains unchanged.
Only a project-private fixed greenlet 3.5.6 wheel is installed under
`.local/s13/browser-native`. The official PyPI wheel SHA256 is
`975736b002ed080d124cf81a79cb7e05cb26d6b3f5c7a7b651c0fcce70353aa1`.
The actual payload manifest is pinned by `browser_client.py`; it validates all
101 installed files before import, then checks the actual loaded version,
module path and CPython extension bytes. This keeps the same Python,
Playwright API and Chromium, and changes no shared environment, authentication,
platform configuration or old package snapshot. An already loaded incompatible
native module is refused rather than reloaded in place.

`browser_environment_facts()` performs file checks only; importing the browser
API and starting a driver/browser are separate actions. A normal execution must
record `loaded_browser_environment_facts()` and its real caller-observed exit.
Do not turn dependency compatibility or a saved JSON into a Native root-cause
finding or a claim of permanent stability. A bounded no-DB/no-login local HTML
verification requires main-agent scheduling after independent source review.

`paired_financial_after.py` holds browser proxies in `main`, closes the context
and browser in `finally`, and releases local references before returning. It
never masks a native signal or uses `os._exit`. This narrows lifecycle risks;
it does not establish that lifecycle was the cause of the earlier fault.
