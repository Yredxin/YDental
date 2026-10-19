# S11 owned Odoo launcher

`launcher.py` is a stage-specific foreground supervisor for the S11 scratch
application. It does not create a database, install or upgrade modules, initialize
users, perform business actions, or enable an external notification provider.
It can start only the fixed scratch database at `127.0.0.1:18411` and only when
the S11 private configuration and independent target-admission receipt are
present and match the current clean product candidate.

## Required private inputs

The launcher refuses to start unless both files exist beneath the ignored path
`.local/s11/`:

- `runtime.json`, based on `runtime.example.json`, contains the real S11-only DB
  login and issued scope metadata. It must be owned by the current user and mode
  `0600`; `.local/s11` must be a user-owned private directory with no group or
  other access.
- `admission.json`, based on `admission.example.json`, records a fresh independent
  verification of the exact DB name/OID/cluster, DB role, dbfilter, companies,
  stores, installed modules, non-superuser grants and upgrade permission, scope,
  S10 preservation checkpoint, and disabled
  external message/SMTP configuration. It must also be mode `0600` and attest the
  hashes of the exact runtime file and committed launcher.

These examples contain placeholders and intentionally cannot pass validation.
They do not create or assert credentials, scope, database access, or verification.
Do not copy S10 private material into these files. Do not store secrets in Git,
logs, shell history, screenshots, or chat. No `.local/s11` runtime or admission
files were present when this launcher was added; no credentials or scope have
been acquired or inferred.

The admission receipt is a binding check, not a database probe or cryptographic
attestation. The named independent verifier must retain the evidence and confirm
the target identity and grants before producing the private file. A stale or
changed target requires a new admission receipt. The launcher does not connect to
PostgreSQL before admission; starting Odoo is the first application connection.
The example's PostgreSQL port is illustrative only and must be replaced with the
independently verified S11 target value; no port or login is inferred from
historical stage configuration.

## Fixed launch contract

The launcher checks the S11 plan ID, branch, clean current HEAD, locked core
commit, private input ownership/modes, scope lifetime (maximum 24 hours), fresh
admission (maximum 30 minutes), exact DB name/OID/cluster, and exact hashes. It
then verifies that port `18411` is free and starts the sibling Odoo wrapper with
an ephemeral mode-`0600` configuration. The config fixes loopback binding,
`workers=0`, `max_cron_threads=0`, `db_maxconn=4`, exact `db_name` and `dbfilter`,
`list_db=False`, and SMTP to the non-listening loopback port 1. The admission must
confirm no configured SMTP servers and no external message provider. Only the
current S11 DB role is supplied to Odoo; no broad cron or public DB manager is
enabled.

The service is supervised in the foreground for at most 20 minutes and never
past scope expiry. One service log is capped at 32 MiB. The ephemeral Odoo config
containing the DB password is deleted on exit; run metadata excludes secrets.
Run history is append-only and capped at 64 runs / 512 MiB; reaching either bound
refuses a new run and requires review rather than automatic deletion.
The stop command signals only the recorded supervisor PID with matching Linux
process birth time and launcher command. The supervisor first gives its exact
`Popen`-owned Odoo child a bounded SIGTERM grace; if that child ignores SIGTERM,
the supervisor may force-stop only that same child through its retained `Popen`
handle. It never signals an unverified child or unknown service. A stale owner
record is preserved for review.

## Normal use after admission

Run from a terminal after a committed candidate and completed independent
admission. Starting blocks in the foreground while the single owned Odoo service
runs; use another terminal for status or stop:

```sh
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py start
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py status
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py stop
```

Record each command's exit code. `start` emits Odoo output only to the capped
private log and prints a non-secret run ID/PID/port. `status` checks process
ownership; it does not make an HTTP request or claim readiness. `stop` signals
only the verified launcher supervisor and waits up to 35 seconds. A refusal or
stale marker requires inspection; do not remove the marker or signal a PID by
hand until ownership is independently resolved. After stopping, confirm
`status` reports STOPPED and separately verify the owned child/port and target
state before any next action. Never inspect, stop, or adopt the unrelated
`127.0.0.1:8069` / PID `42433` service.

Installing/upgrading modules, running cron, creating synthetic identities,
opening browser sessions, or executing business tests require their own bounded
S11 commands and checkpoints; this launcher performs none of them. Main DB,
S10 private scopes/launchers, PostgreSQL cluster administration, core changes,
external delivery, and production remain out of scope.
