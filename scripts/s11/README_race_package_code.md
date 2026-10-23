# S11 package-code race runner

`race_package_code.py` is an opt-in integration runner for one duplicate package
code binding race. It does not start Odoo. It opens two independent Odoo registry
cursors, proves their PostgreSQL backend PIDs differ, synchronizes both guarded
`ydental.lab.service._operate("bind_code", ...)` requests, and performs a
separate `REPEATABLE READ READ ONLY` readback after the worker commits.

The race targets must already be two committed, synthetic S11 work orders made
through the normal S11 workflow. The runner refuses to act unless both have an
`S11-` internal code, are active, belong to the selected admitted store, point
to their own actual confirmed treatment events and synthetic patients, and have
no existing package code or code-binding audit. It also requires an existing
non-superuser internal actor with actual medical-write and warehouse-write
grants, within the fresh S11 admitted company/store set. The lab service checks
medical authority before the package-code-specific warehouse check. The runner does not provision those
fixtures. Creating full source events and work orders remains a separate
runtime-preparation task.

The only business workflow mutation is a new randomly generated `S11-RACE-...`
package code. The losing action must return the guarded `code_conflict`; the
winning order must have exactly one new bind event and audit. The independent
readback verifies the losing order is unchanged, both orders retain their
supplier cost sources, purchase-cost snapshots and follow-up references, and
their linked inventory events and native stock quantities are unchanged. The
runner also commits two ordinary scoped access sessions; their IDs are retained
in the private receipt. It never deletes the resulting business or audit facts.

Before use, complete the normal target admission and update the private
`.local/s11/new-target-runtime.json` and `new-target-admission.json` for the exact clean committed
candidate. Resolve or preserve any existing `.local/s11/new-target-active.json` owner
record; the runner refuses whenever it exists. Supply IDs for two suitable new
synthetic orders and an ordinary warehouse actor. The command requires both the
full candidate and a literal execution confirmation:

```sh
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python \
  /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/race_package_code.py \
  --candidate <full-40-character-committed-HEAD> \
  --actor-id <authorized-synthetic-warehouse-user-id> \
  --store-id <admitted-synthetic-store-id> \
  --order-a <first-synthetic-order-id> \
  --order-b <second-synthetic-order-id> \
  --confirm S11-SYNTHETIC-PACKAGE-CODE-RACE-V1
```

The launcher contract checks the private input ownership, exact branch/HEAD,
core lock, target, scope lifetime and fresh independent admission before any
database connection. The runner then checks the live database name/OID/cluster,
current restricted login, installed S11 modules, actor/store grant, and all
synthetic order preconditions in a read-only transaction. A precondition failure
returns before creating scoped sessions or binding a code. Once session setup
begins, it writes atomic mode-0600 phase receipts beneath the ignored
`.local/s11/new-target-races/`; after each durable phase, a failure is marked partial and
must be independently read back before anyone considers another run. Do not
blindly retry a partial result.

All race tools use the launcher's stable `new-target-data/` filestore and
`new-target-races/` evidence namespace. Fixture receipts and source locks use
`new-target-fixtures/`. The old `races/` and `fixtures/` history stays intact;
the old scratch's event187 protection does not identify event187 in the new
database. New target source locks still prevent replay of that target's source.

This runner provides MODEL/service-level real-connection concurrency evidence,
not HTTP/RPC or browser evidence. SOURCE/PURE checks do not prove a live race;
each actual invocation needs its own worker and independent readback receipt.
