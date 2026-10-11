# Questions

No new questions for M0. PRD Q2 and Q11 are resolved for this milestone by
D-001 and D-002. Other PRD questions remain deferred to their owning milestones.
# Open questions

## M1 planning — 2026-10-10

M1-01 through M1-08 were resolved by human approval on 2026-10-11;
the approved answers below amend the PRD. PRD Q5 remains open:
fulfillment is only nullable free text. PRD Q7 remains open: use only the
existing time-window and per-product-quota assumptions; add no new parameters.

- **M1-01 — RESOLVED — Scaffold prerequisite:** The current working tree has no source
  files, Makefile, dependency manifest, or Alembic setup. Should the M0 scaffold
  be restored/completed separately before M1? M1 must not recreate M0 tooling.
- **M1-02 — RESOLVED — BR-4 scheduling conflicts:** What happens when a SCHEDULED session
  reaches opens_at while another session is OPEN? Are overlapping windows
  rejected, or does a due session wait? If its entire window elapsed during
  downtime, should the tick traverse SCHEDULED -> OPEN -> CLOSED in one
  transaction? DRAFT -> OPEN is forbidden by the stated state machine, despite
  the later manual-open requirements; should manual opening require scheduling
  first and may it occur before opens_at?
- **M1-03 — RESOLVED — BR-4 sold-out semantics:** Does an unlimited-quota product keep a
  session open when all finite quotas are sold out? What happens for an empty
  product set or an all-unlimited session? Does is_active affect this decision?
- **M1-04 — RESOLVED — BR-7 order changes and state machine:** List permitted order
  cancellation/status transitions, including owner reversals and cancellation
  of PAID/FULFILLED orders. Can a customer edit a CONFIRMED or PAID order while
  OPEN? If so, how do edits affect status, price snapshots, explicit
  reconfirmation, and quota? What happens to orders when a session is CANCELLED?
- **M1-05 — RESOLVED — Quota and product edits:** May quota be reduced below already sold
  quantity? May an attached product be removed or deactivated with existing
  drafts/confirmed orders? Does is_active prohibit ordering an attached product?
  What happens to outstanding drafts after a price change between summary and
  confirmation? FR-2 requires agreement to the summary; BR-5 snapshots at
  confirmation.
- **M1-06 — RESOLVED — BR-9 milestone boundary:** M1 requires BR-1 through BR-10 coverage,
  while M3 introduces message handling and idempotency. May M1 implement a
  provider-neutral inbound-ID claim and transactional business-effect wrapper
  with fake IDs, leaving parsing, delivery, and message processing to M3? What
  durable outcome should a duplicate invocation return?
- **M1-07 — RESOLVED — Data scope:** Should M1 create all section-7 tables, including
  conversation_state, messages, audit_log, and admin_users, as schema only?
  If so, confirm the proposed minimal schema does not yet require unanswered
  retention, conversation-state, and admin-authentication decisions.
- **M1-08 — RESOLVED — BR-10 limit:** BR-10 says per-order maximum, while section 14 says
  20 units per item per order. Confirm the section-14 interpretation and how
  the configurable limit is supplied (without adding a PO-session parameter).

IDs are integers, explicitly approved on 2026-10-11.
Q4 payment instructions, Q5 fulfillment, Q6 real product data,
Q7 extra session parameters, and Q9 owner/admin counts remain unresolved;
M1 must not select answers to them.

### Approved resolutions — 2026-10-11

- M1-01: Verify branch `m1-domain` and passing `make setup`, `make test`,
  and `make lint` on the existing M0 scaffold before writing M1 code.
- M1-02: Reject overlapping SCHEDULED windows at scheduling time. Manual
  opening requires SCHEDULED and no other OPEN session. After downtime, open
  a due session if its closing time has not passed; otherwise CANCEL it as
  never opened and write an audit_log entry.
- M1-03: Auto-close for sold-out only if every attached product has a finite
  quota and all are exhausted; an unlimited product disables this condition.
  Scheduling requires at least one active product. Inactive products cannot
  be added; deactivating one in OPEN stops new orders for it only.
- M1-04: Customers may cancel their own DRAFT/CONFIRMED orders only while
  OPEN. Owners may cancel any order except FULFILLED, releasing quota.
  CONFIRMED order editing is deferred; cancel and reorder. Cancelling a
  session cancels all non-FULFILLED orders and flags PAID ones for the owner.
- M1-05: Quota cannot fall below confirmed sold quantity. Products with
  active orders cannot be removed from a session. `confirm_order` receives
  the total shown to the customer; a price mismatch rejects confirmation
  and returns a fresh summary.
- M1-06: Implement provider-neutral `record_inbound_message` returning a
  `duplicate` flag; M3 connects it to the webhook.
- M1-07: Integer IDs. M1 tables only: products, po_sessions,
  po_session_products, customers, orders, order_items, owner_numbers,
  messages, audit_log. Defer conversation_state to M4 and admin_users to M2.
- M1-08: Positive integer quantity per item per order; configurable via
  `MAX_QTY_PER_ITEM`, default 20. Update BR-10 only in the PRD.

### Implementation blockers — 2026-10-11

- **M1-09 — RESOLVED — Decision numbering:** The approved instruction requests
  D-004 onward for eight M1 entries, but D-004 through D-006 already document
  M0 decisions. Preserve M0 IDs and begin M1 at D-007, or renumber the existing
  M0 entries to reserve D-004 through D-011 for M1?
- **M1-10 — RESOLVED — Approved slice boundaries:** The approved instruction
  splits slice 3 into 3a (drafts, summary, confirmation, atomic quota) and 3b
  (cancellation, owner status actions, session-cancel effects). The remaining
  slice boundaries are absent from the repository and available conversation.
  What are the approved boundaries for the remaining slices?

Resolution 2026-10-11: Preserve existing decision IDs and approved wording.
Start at D-008 as requested (D-007 reserved; checkout currently ends D-006).
Approved slices: 1 persistence; 2 lifecycle; 3a orders/atomic quota;
3b cancellation/owner actions; 4 idempotency/acceptance. Test and lint each,
commit locally on success, append progress, continue; stop after two failures.
No push and no decisions on PRD [OPEN] items.
