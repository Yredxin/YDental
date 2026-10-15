# S10-UI1-R2: HTML navigation reproduced; upgrade command blocked Web recovery

**Result: BLOCKED_TEST_HARNESS.** Firefox reproduced the original UI1 defect on unchanged product code. A minimal controller/QWeb candidate was written, but the one authorized upgrade attempt failed at Odoo CLI parsing (`--test-disable` is not a recognized option, exit 2). The candidate was not loaded into the new database; post-change Web and PDF acceptance are **NOT_RUN**. This is neither a product acceptance result nor a complete S10 PASS.

## Identity, checkpoint, and offline executor gate

The latest authority was [#34 comment 6182293301](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182293301). Full API GET of #23/#29/#31/#34 bodies and all effective comments yielded 3/7/8/116 comments; #35 remained OPEN with 0. No later delivery or parallel UI1 executor was found. The branch and origin remote both started at `d59f15d364c3d00641fdb7a155fcbb35236838a5` with a clean worktree. Fixed core, historical S10 commits, current S10 service blob and S07 service SHA matched the authority. The [R2 checkpoint](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182394266) was posted before CREATE/Odoo/Firefox/product edits and read back byte for byte through the API.

R2 test copies fixed the local `target` variable shadowing the `target()` function. The actual old R1 `create()` failed in the same temporary fake PG/network/filesystem setup with `TypeError: 'PosixPath' object is not callable`; the actual R2 `create()` and CLI dispatch completed nonempty copy, fake CREATE, config/marker, fixed adapter AST check, tail validation and return. Copy hash failure, SQL CREATE failure, post-CREATE identity mismatch and repeat invocation failed closed. The R2 evidence writer round-tripped nested `date`/`datetime`/`Decimal` without precision loss and did not publish a partial failure. Strict stage result gates checked exit, signal11, timeout, OID/config, baseline response and finance proof. Actual response classification distinguished JSON/HTML/303 and rejected a bare Location header. Compile, 34 inherited marker/adapter checks and 19 full-flow checks exited 0, all **SIMULATED_PASS**, not real Web/finance results.

## Real isolated run and baseline

One new database `ydental_s10_test_20261015014500_c72e6f91` / OID2100240 was cloned from pure 92-module template OID2100080. Its 124 filestore files, private config, complete marker, actual OID/cluster and unchanged fixed adapter passed the independent `verify-target` command before Odoo. `prepare` was Odoo process 1 (exit0, no signal11), after the adapter guard prepared two synthetic confirmed fees and committed fixture once. `serve-before` was process 2, started the original code on loopback and stopped normally (exit0, no signal11).

One real Firefox process logged in as the authorized synthetic manager and submitted the ordinary HTML bill form **before the product patch**. POST `Content-Type: application/x-www-form-urlencoded` returned HTTP200 `application/json; charset=utf-8`; the final browser path was `/ydental/settlement/action` with no workbench or feedback. This is **REPRODUCED_JSON_NAVIGATION**, not a requests-only inference. The baseline bill committed once: one `bill` idempotency receipt, one native `out_invoice` in `posted` state for synthetic 100.00, zero payments/refunds/closes. S01 audit count rose from 156 after fixture to 162 after baseline (includes session and business actions); mail.mail remained 0. Internal Bus was 30 in both snapshots. The screenshot is preserved privately; only its SHA is committed.

The candidate adds an explicit HTML form marker, leaves unmarked JSON clients on their existing response path, and uses server-session one-time feedback plus local 303 Post/Redirect/Get. The feedback query contains only a random token and is checked against the session, not a success claim or financial detail. No model, ACL, accounting, S05/S07 or core changes were made. Python compile, XML parse/all 13 POST forms include the common token template, and `git diff --check` passed. **Candidate behavior has not been tested in Odoo.**

## Stop event and remaining acceptance

The third and only upgrade invocation exited 2 before registry/module update because current Odoo CLI rejects `--test-disable`. It produced no signal11. The controller correctly wrote a failed result and stopped. No corrected command, second upgrade, after-HTTP or extra browser was attempted. The waiting Firefox process was interrupted to close its contexts; that is not a browser acceptance failure or a post-change run. The new DB and all files/logs remain intact. The existing `ydental_settlement` module is still installed at the old version in the DB.

| Item | Actual result |
| --- | --- |
| CREATE | 1/1, exit0, OID2100240 |
| Sequential Odoo processes | 3/4: prepare exit0, before HTTP exit0, upgrade CLI exit2 |
| Firefox processes | 1/1, original baseline reproduced; intentionally stopped after upgrade failure |
| Named business COMMITs | 2/12: fixture, baseline_bill |
| Successful module upgrades | 0/1; one failed invocation consumed the attempt |
| Post-change HTML, JSON API, replay, payment/refund/close/unlock | NOT_RUN |
| Rights, CSRF, revision, cross-store negative Web tests | NOT_RUN |
| >50 HTTP pagination | NOT_RUN |
| Bill/receipt/refund PDF download and visual review, unauthorized direct link | NOT_RUN |

The failure is a test executor CLI option, not an observed Odoo product invariant failure. No second DB or retries were used. All old DBs, including OID2056451, template2100080, C1 OIDs2100125/2100126/2100176, FC1/FC2 2100197/2100212 and old UI1 failures2100227/2100239, were found in a read-only inventory and retained with filestores, markers and logs. No Project/Issue/workflow mutation, sudo, infrastructure security work, FC1/FC2 rerun, merge, deployment or S11 work occurred. S10 full technical and production status remains BLOCKED; old Native SIGSEGV cause remains UNKNOWN.

[Sanitized machine evidence](evidence/s10-ui1-r2-blocked/verification.json) records process results, hashes and exact statuses without credentials, patient data, raw logs or screenshots.
