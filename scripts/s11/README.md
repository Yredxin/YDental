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

- `runtime.json`, based on `runtime.example.json`, contains the verified DB
  login and newly issued S11 scope metadata. The login may be sourced from an
  authorized shared YDental project credential provider; this does not reuse an
  S10 runtime scope or approval. It must be owned by the current user and mode
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
An authorized shared project credential may be read into the ignored private
S11 runtime file; never reuse an S10 scope, approval, STOP state, or expired
runtime window. Do not store secrets in Git, logs, shell history, screenshots,
or chat. The GitHub repository is public, so never upload credential values or
recoverable secret configuration.

The admission receipt is a binding check, not a cryptographic attestation. The
named independent verifier must retain the evidence and confirm the target
identity and grants before producing the private file. A stale or changed target
requires a new admission receipt. The launcher does not connect to PostgreSQL
before admission. After validating the current pair, each start performs a fresh
read-only identity probe using the same restricted S11 DB role before creating
run artifacts or launching Odoo.
The example's PostgreSQL port is illustrative only and must be replaced with the
independently verified S11 target value; no port or login is inferred from
historical stage configuration.

## Fixed launch contract

Before installing or testing the S11 addons, install the pinned S11 Python
dependency into the project virtualenv:

```sh
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python -m pip install -r /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/requirements.txt
```

The launcher checks the S11 plan ID, branch, clean current HEAD, locked core
commit, private input ownership/modes, scope lifetime (maximum 24 hours), fresh
admission (maximum 30 minutes), exact DB name/OID/cluster, and exact hashes. It
then checks that port `18411` has no active TCP listener and starts the sibling
Odoo wrapper with an ephemeral mode-`0600` configuration. A refused loopback
connect is considered free; TIME_WAIT sockets from a recently closed owned test
do not block a restart. An active listener or an inconclusive probe fails closed.
The config fixes loopback binding,
`workers=0`, `max_cron_threads=0`, `db_maxconn=4`, exact `db_name` and `dbfilter`,
`list_db=False`, and SMTP to the non-listening loopback port 1. The admission must
confirm no configured SMTP servers and no external message provider. Only the
current S11 DB role is supplied to Odoo; no broad cron or public DB manager is
enabled.

The service is supervised in the foreground for at most 20 minutes and never
past scope expiry. One service log is capped at 32 MiB. The ephemeral Odoo config
containing the DB password is deleted on exit; run metadata excludes secrets.
The Odoo filestore uses the stable private `.local/s11/data/` directory across
owned restarts. This is required because the scratch DB stores attachment hashes
for web bundles in PostgreSQL; a fresh per-run data directory would return empty
web assets and leave the authenticated browser client blank. The path is S11
owned and mode `0700`; it is separate from the prior S10 launcher data directory.
Run history is append-only and capped at 128 run directories / 512 MiB; reaching either bound
refuses a new run and requires review rather than automatic deletion.
The stop command signals only the recorded supervisor PID with matching Linux
process birth time and launcher command. In direct mode the supervisor controls
its exact `Popen`-owned Odoo child. In GDB mode, the debugger and inferior share
a fresh private session and may occupy separate process groups; the verified
supervisor signals and verifies both groups. It never signals an unverified
process or unknown service. A stale owner record is preserved for review.

For an authorized diagnostic run after the exact committed candidate has a fresh
independent admission, use `start --gdb`. This starts the same fixed Odoo target
under GDB in the owned run directory. On an actual `SIGSEGV`, GDB records all
thread backtraces, process mappings, loaded libraries, and a core snapshot. The
run directory is mode `0700`; files are mode `0600`. Core generation is capped
at 256 MiB by the GDB process file-size limit, and startup reserves the log/core
allowance both in run-history capacity and on disk. GDB version, inferior PID,
capture outcome, and core size are recorded in the exit receipt; `native-crash.json`
identifies the inferior, signal, each collection step, and whether all required
artifacts completed. GDB's size limit applies to core capture; the private
inferior wrapper restores the original file-size allowance before executing
Odoo. GDB capture remains optional and is never enabled implicitly. Do not
upload or commit core files or raw runtime logs.

GDB starts in a private session; its inferior may use a separate process group
inside that session. The private inferior wrapper records its PID, process
birth ticks, group ID, and session ID before exec. Before signaling either
owned group or releasing the active-owner record, the supervisor verifies the
session/group identities and confirms both groups have no live members; a
missing or ambiguous identity keeps the owner record for review. The exit receipt records
the debugger separately from the inferior. If GDB cannot be resolved or its
Python event/core support cannot be verified, the run is refused before
creating the service. This diagnostic option requires the same fresh admission
and does not authorize additional business requests or writes.

## Normal use after admission

Run from a terminal after a committed candidate and completed independent
admission. Starting blocks in the foreground while the single owned Odoo service
runs; use another terminal for status or stop:

```sh
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py start
# For a separately admitted native-diagnostic run:
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py start --gdb
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py status
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/launcher.py stop
```

Record each command's exit code. `start` emits Odoo output only to the capped
private log and prints a non-secret run ID/PID/port. `status` checks process
ownership; it does not make an HTTP request or claim readiness. `stop` signals
only the verified launcher supervisor and waits up to 75 seconds. It treats a
matching owned PID in Linux zombie state (`Z`) as exited after reading process
state and birth ticks from the same `/proc/<pid>/stat` snapshot. A refusal or
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

## Session-scoped S11 synthetic business clock

To test date-triggered S11 behavior without waiting for wall-clock dates, use
the dedicated debug entry only after committing the candidate and obtaining a
fresh independently reviewed admission. It verifies the fixed scratch database,
OID/cluster, private admission and stopped-service conditions, then starts the
owned Odoo process under GDB and initializes `ydental_s11_clock_test`:

```sh
/home/redxin/code/odoo/odoo-sd/code/.venv/bin/python /home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s11/debug_clock.py
```

From an authenticated, authorized S11 test account on the local browser, open
`http://127.0.0.1:18411/ydental/s11/debug-clock`. Enter an ISO-8601 UTC time
and a reason. The clock is bound to that browser session, actor and active
store; it can only move forward, must be within 30 days of physical UTC, and
expires after eight physical hours. Use “Clear this session clock” to return
that session to physical business time. The run has an explicit `S11_SESSION_CLOCK`
manifest and GDB capture; it is not an OS or PostgreSQL clock change.

Only application business-time seams in the listed S11 service addons consume
this value. Clinical/lab action dates in the scratch are synthetic and must be
read as such. Access audit metadata retains both simulated business UTC and
physical audit UTC. ORM creation/write timestamps, GDB elapsed/stale time,
notification attempt/daily-cap timestamps, settlement/fund cutoffs, host time,
PostgreSQL time and any external provider time remain physical. The follow-up
adapter only uses the synthetic time for due/quiet-hour eligibility and keeps
the existing controlled sink boundary; it does not authorize real delivery.

This debug entrance does not bypass patient/task/source rules, queue FIFO,
permissions, purchase/stock controls, protected records or the normal business
workflow. It does not make synthetic events evidence of physical attendance or
physical supplier delivery. If cluster inspection is denied, a target check
fails, a crash occurs, or data changes unexpectedly, stop the affected run and
preserve its evidence; do not fall back to changing machine time.
