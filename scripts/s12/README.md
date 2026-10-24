# S12 local execution tools

Only `ydental_s11_synth_20261023_01`, OID `2171423`, cluster
`7694897083368259627` is supported. These tools do not create, copy or rename a
database. The locked Odoo core is `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`.

`admission_probe.py` reads only the `database` object of the explicitly named
authorized provider, opens one `READ ONLY / REPEATABLE READ` transaction on that
target, records observed identity, role and object privileges, module state,
companies/stores and disabled outbound settings, then rolls back and closes.
It does not claim independent acceptance or issue scope/admission. Receipts are
new mode-0600 files under ignored `.local/s12/`; original receipts are never
overwritten. No credential value or authentication hash is selected into evidence.

```sh
../.venv/bin/python scripts/s12/admission_probe.py --provider .local/s11/new-target-runtime.json --output .local/s12/admission/target-readonly-confirmed.json --operator /root/tester
```

`launcher.py` binds the existing `scripts/s11/launcher.py` supervisor to S12. It
uses new S12 private `runtime.json`, `admission.json`, `active.json` and `runs/`
records. Runtime/admission use the same existing schema with S12 plan/branch,
the actual current candidate and newly issued S12 scope. In addition:

- runtime `data_dir` must equal the absolute existing
  `.local/s11/new-target-data` directory for this same database;
- admission `launcher_sha256` binds the S12 wrapper and
  `base_launcher_sha256` binds the reused S11 supervisor source;
- both S11 and S12 active-owner records must be absent before a new start;
- S11 session-clock startup is unavailable and clock environment variables are
  rejected. It does not initialize or upgrade any module.

The reused supervisor still prints some historical `S11` diagnostic labels. Its
structured records use the actual S12 plan, candidate, scope and S12 paths. The
same target keeps its already committed attachment filestore, without copying
or altering old runtime/scope files. The supervisor retains its fixed loopback
port `18411`, disabled cron/SMTP, process ownership and normal stop behavior.

```sh
../.venv/bin/python scripts/s12/launcher.py status
../.venv/bin/python scripts/s12/launcher.py start
../.venv/bin/python scripts/s12/launcher.py stop
```

`start` requires a committed clean candidate and a fresh independently reviewed
admission. It blocks in the foreground. An explicit `start --gdb` retains the
existing native-crash evidence option, with no session clock. A stale owner,
unknown process outcome or new native crash must be investigated before another
run. Neither private scope metadata nor a successful probe replaces platform
permissions or authorizes a business replay.

`protected_snapshot.py` retains the S11 accepted protection projection and
committed synthetic anchors, expanding user/company coverage and including new
S12 tables. Authentication/session/bearer material is excluded, text and binary
business content is hashed privately, and file bytes are hashed from the same
existing filestore. It performs no upgrade. The main operator must first stop
writers and save an actual private freeze receipt with the full candidate,
target, OID, affected module list and `writers_quiescent: true`. Collection
requires that exact candidate, locked core, S12 runtime and only named S12
modules; incomplete pre snapshots never authorize an upgrade. `compare` is
offline and records actual field changes for independent classification.

```sh
../.venv/bin/python scripts/s12/protected_snapshot.py collect --phase pre --label final --candidate COMMIT --modules ydental_print,ydental_settlement --freeze-receipt .local/s12/verification/final-freeze.json
../.venv/bin/python scripts/s12/protected_snapshot.py collect --phase post --label final --candidate COMMIT --modules ydental_print,ydental_settlement --freeze-receipt .local/s12/verification/final-freeze.json
../.venv/bin/python scripts/s12/protected_snapshot.py compare --pre .local/s12/verification/upgrade-final-pre.json --post .local/s12/verification/upgrade-final-post.json --output .local/s12/verification/upgrade-final-diff.json
```
