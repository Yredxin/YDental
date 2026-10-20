# S11 F/T evidence index

Status at candidate `75769854a75b0944b66f66f3b1dfba56450f42b5`: **PARTIAL / IN_PROGRESS**, Issue #35 OPEN. This index distinguishes limited passing evidence from scenario completion. The detailed command/result history and earlier failures are in [summary.md](summary.md); private receipts, logs, and database snapshots remain under ignored `.local/s11/` and are not published.

## Functional scenarios

| Item | Evidence and layer | Remaining acceptance gap |
|---|---|---|
| F1 | Lifecycle MODEL coverage; followup265 linked to confirmed event414 then completed in a real browser against event416, with independent committed-state readback (summary.md, 2026-10-19 followup265 attempt12; readback SHA `f2c5587b…da661f7`). | Full applicable lifecycle and current patient650 path remain incomplete. Patient650 has a reservation only; no actual arrival, queue entry, or treatment source. |
| F2 | Two-connection invoice race for task941 produced one invoice179; independent readback found no second economic fact, then a verified same-key recovery resolved to the existing invoice. Receipt SHA `a345374f…c55af2`. | The losing call returned `SerializationFailure`; its raw response/backend PID was not retained. Do not claim both direct concurrent calls succeeded. Unknown-notification-to-rework chain remains incomplete. |
| F3 | T08 `discard` MODEL plus committed-state readback; real inventory moved to loss with cost/patient fee unchanged (receipt SHA `0e65d937…f974b8e15`; readback SHA `dc2f2403…b562ed7e`). T16 order434 multi-connection race/readback SHA `dba6892b…c5064d4`. | T08 `supplier_return` not run. No currently qualified synthetic prosthesis source/warehouse actor for the branch. |
| F4 | T15 native ORM qualification/cooperation and same-company store-scope model coverage; independent readback SHA `f9632b35…5318672a`. | Full dual-store purchase/receipt/cost/patient-fee chain is absent. A purchase-user group would expose protected company1 POs 147–149; no such access was granted. |
| F5 | T06 receipt/putaway duplicate races and T17 package-code race have independent committed-state readbacks; T17 readback SHA `b4676433…7716c0f4`. | T14 appointment-version evidence is model-only; remaining F5 assertions are not a full scenario pass. |

## Test cases

| Item | Current evidence and layer | Remaining gap / limit |
|---|---|---|
| T01 | Lifecycle MODEL coverage and followup265 browser completion/readback (summary.md followup265 attempt12). | Full scenario coverage is not independently mapped for every branch. |
| T02 | Cross-store MODEL test, candidate `caabf67`. | The exact dedicated receipt/hash is not identified in the current summary; do not infer a separate PASS beyond the recorded test result. |
| T03 | MODEL callback-state coverage and signed callback HTTP `HttpCase`, candidate `7bd9f0d`; independent post-test readback recorded in summary.md. | No real external provider callback. |
| T04 | Same signed callback HTTP candidate `7bd9f0d`: valid accepted/delivered, duplicate event, and invalid HMAC rejection. | Route test does not call a real transport/provider. |
| T05 | Preference/quiet-hour/cap MODEL coverage; followup272 browser no-contact fallback has committed-state readback (SHA `a23f9cfd…0cd0bd2`). Controlled sink handler MODEL evidence: candidate `60d1bad`, 1 test, log SHA `9b5fc11a…7b274ab`. Candidate `7576985` adds enqueue-to-postcommit-callback wiring, 1 test, log SHA `c3e56fdc…a724cc1`; independent post-test readback SHA `b21b4e00…a059e5`. | No source-transaction commit → postcommit callback lifecycle → independent claim → controlled sink chain. New callback test invokes the captured closure directly and mocks dispatcher. No patient delivery. |
| T06 | Order432 and order434 receipt/putaway multi-connection tests; order434 independent readback SHA `78af2098…7b226c8`. | Scenario-specific coverage only. |
| T07 | Task941 first invoice race and verified idempotent recovery; readback SHA `a345374f…c55af2`. | Original losing response/backend PID unavailable; result is limited to database race plus verified recovery. |
| T08 | `discard` MODEL and committed-state evidence (receipt SHA `0e65d937…f974b8e15`; readback SHA `dc2f2403…b562ed7e`). | `supplier_return` not run; valid source and same-actor warehouse/medical permissions are unavailable. |
| T09 | Completed order200 linked to one repair suborder249; independent receipt SHA `8b052154…4a99e09`. | Persistence readback only; not a new operation or concurrency test. |
| T10 | Attachment/access boundary MODEL and HTTP/RPC regression, candidate `caabf67`. | No new gap recorded for the tested boundary; this does not close other F/T items. |
| T11 | S11 TransactionCase in candidate `7f03`, included in a 60-post-test upgrade run with independent readback. | Exact dedicated receipt/hash is not identified in the current summary; retain that limit. |
| T12 | Strategy-boundary MODEL tests and followup272 browser manual fallback; T05's `60d1bad` sink-handler and `7576985` callback-wiring evidence also apply. | Automatic postcommit dispatch/claim to controlled sink remains unverified; `.invalid` contact is not validated consent and sink acceptance is not delivery. |
| T13 | Included with T01 lifecycle model/browser evidence in summary.md. | No separate T13 receipt is identified; exact standalone mapping UNKNOWN. |
| T14 | Appointment-version MODEL coverage. | No real request/concurrency evidence identified. |
| T15 | Native ORM approval and same-company store-scoping model test; independent readback SHA `f9632b35…5318672a`. | Full dual-store business chain remains incomplete. |
| T16 | Order434 receive/cancel race, two backends; independent readback SHA `dba6892b…c5064d4`. | Earlier order433 attempt had asymmetric pre/post projection; only the repaired order434 evidence is accepted. |
| T17 | Order433/434 package-code two-backend race; unique binding and `code_conflict`, independent readback SHA `b4676433…7716c0f4`. | Scenario-specific evidence only. |
| T18 | Free-rework MODEL tests and parent/child return-to-stock chain recorded in summary.md. | Task720 native execution stopped before clinical document/treatment and is fenced `verify`; do not reopen, retake over, or replay. Required actual wear/follow-up remains incomplete. |

## Overall limits

- The latest S11 test results do not share one final product candidate: many earlier F/T results belong to the exact candidates named above. The 25-test follow-up addon suite ran at `ea1928c`; the new single-test callback wiring result is at `7576985`.
- The later 25-test suite included Odoo `HttpCase` test-client coverage. It was not a real browser or external provider test. The actual HTTP/browser child SIGSEGV STOP remains in force; do not restart that path as a routine retry.
- No real SMS, external notification provider, supplier portal, production, payment provider, or patient delivery was enabled. The test sink's `accepted` result means internal acceptance only.
- No new business action in this continuation touched patient364/event417/task720 or PO147–149. Earlier S11 work involving these protected objects is retained in its historical report entries and is not replayed. No push, merge, deployment, or Issue process update was performed.
- Plan-wide independent acceptance, final influence regression, T08 `supplier_return`, complete F4, full T05/T12 automatic dispatch, and task720 downstream clinical/follow-up work remain outstanding. Keep #35 OPEN.
