# S10 GitHub-only targeted finance patch — BLOCKED pending Ubuntu runtime validation

**State: WIP / NOT_RUN. This is not a CODEX delivery, S10 technical PASS, user acceptance, or authorization to deploy.**

## Provenance and scope

- User instruction: implement the latest [S10 review and authorization](https://github.com/Yredxin/YDental/issues/34#issuecomment-6158230350).
- Fixed predecessor: `d99f27fffcd6f9b79f1b1ac271dd026493b826b6`.
- GPT GitHub-only implementation product: `fadd5cc83f297a7f9806ee7f4f175f1735520651`.
- Added unexecuted test scripts commit: `e745976bc3493b67228c4647d9cdb0aabc8a74be`.
- This final documentation commit contains **no product or test changes**.
- This ChatGPT session can write the GitHub branch but **has no connection to the user's Ubuntu Codex CLI, Odoo20 runtime, PostgreSQL cluster, Firefox or private `.local` evidence**. No installation, upgrade, migration, execution, real browser interaction, real Postgres concurrency, sample PDF rendering, or translation coverage is claimed for the modified version.

## Code edits (untested)

1. `ydental_settlement/models/ydental_settlement_refund.py` adds nullable immutable audit fields for request time, terminal time, **actual refund business date** and **actual refund channel**. Existing records are not mass-updated, deleted or fabricated.
2. `ydental_settlement/models/ydental_settlement_service.py` separates daily **inbound cash from outbound refund** using the refund execution user, real UTC refund time converted by source-store IANA timezone and frozen native payout channel. It no longer attributes today's actual outbound to the original payment's date and cashier. Frozen previous close records remain unchanged. Pending amounts are a separately described as-of exposure snapshot associated with the original cashier, not a same-day cash flow. For legacy rejected rows with no new terminal field, the service uses Odoo's protected write_date; migration/history assumptions **require a real replay and independent review**.
3. Refund execution uses the payment's last audited, reclassified `_effective_channel` rather than an incorrect historical `payment.ydental_channel`. It refuses actual refund timestamps before the application or recorded channel change. The native payment's journal and the frozen channel are cross-checked during daily close. Its actual business date, channel and operator are logged in the server-side audit.
4. Refund request/cancel uses the **current operation business date** for close locks rather than the original receipt date, avoiding false blocks for valid later-day refunds. Real actual refunds continue to use their actual-day close lock. These changes need lock/order and historical reconciliation tests.
5. `_workbench` and the GET controller use independent patient-scoped, store-scoped **50-row pagination** for payments/refunds and store-scoped pagination for closes, instead of silently truncating the lists. The QWeb page provides previous/next links. Refund PDFs now indicate frozen actual day/channel for the done state.

## Added guarded test-source canaries — NOT_RUN

- `scripts/s10_completion/refund_day_channel.py`: requires a new, guarded S10 synthetic DB with the real F5 fixture already committed. It records an actual inbound payment on an earlier local day, confirms/unlocks/corrects the original cash classification, requests and approves a refund on a later day, captures a pending snapshot, unlocks it, posts an actual refund using the corrected native WeChat journal, and asserts old close immutable, current refund-day close correctly allocated. **Not executed here.**
- `scripts/s10_completion/paged_finance_history.py`: requires real F1/F5 fixtures, creates 55 pending synthetic refund requests, 55 past closing cycles and 55 native partial payments via authorized service calls, reads page 2, and attempts legitimate older-record cancel/unlock. It must be scheduled **before** relevant payment-day closes / Firefox scenarios, otherwise legitimate `day_closed` rules will reject the fixture. **Not executed here.**

**Strict validation prerequisite:** Ubuntu Codex must first run Python `py_compile`/AST, XML parse, check actual Odoo20 field API and security model, inspect the nullable schema upgrade on existing synthetic data, re-test all existing S10 fixture scripts and current D1/D2 regression. New methods may have integration bugs; **the existence of a commit or source script is not evidence of Odoo correctness**. Review refund day-end/as-of pending semantics and past correction/accounting policies with the appropriate business reviewer before calling this feature complete.

## Outstanding acceptance and stop conditions

- S10-F1—F6, T01—T16 on this **new code/tree**: **NOT_RUN** in this GitHub-only implementation; earlier Codex PASS/PARTIAL evidence is tied to the prior SHA and must not be reused as current-version proof.
- Full same-SHA new isolated DB install → upgrade → committed clinical/stock/account/refund activity → upgrade; 2 distinct real PostgreSQL backends with barrier, native move/payment/journal/partial reconcile reconciliation, Firefox all-role flows, all three Chinese PDFs as rendered files, PO extraction, S08/S09 applicable tests and Project full-read evidence: **NOT_RUN**.
- Production tax/payment/journal policy approval, true external cash and native SIGSEGV root cause: **BLOCKED/UNKNOWN**.
- No old database, volume, branch history, Odoo core, `odoo-12`, S01—S09 product, Project fields, S11 issue or actual finance/patient data was modified by this GitHub-only edit.

**Next executor:** the original Ubuntu S10 Codex CLI session must fetch the new branch HEAD, independently inspect this WIP code and run/correct the missing tests on a **new guarded synthetic database**. If changes are needed, append a new well-structured product→test→final series without rewriting earlier commits. Post an accurate `[CODEX] S10 ... BLOCKED/交付验收申请` with fixed SHA and real logs to #34 and stop. GPT must independently review those real results before any project status change or stage PASS.
