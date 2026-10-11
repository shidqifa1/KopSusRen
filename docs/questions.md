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

## UI specification review — 2026-10-11

These findings are OPEN; no requirement, token, or visual behavior was changed.
This is a documentation review, not M2/M3 implementation or acceptance.

| PRD requirement | UI-UX coverage | Conflict or gap |
|---|---|---|
| FR-13 | Section 7 login form, generic errors, rate-limit copy | Password hashing, cookie security and authenticated/unauthenticated behavior are not specified; see UI-01. |
| FR-14 | Section 7 overview metrics, current session, per-product quota | Next scheduled session display is missing; see UI-02. |
| FR-15 | Section 7 products, sessions, orders, customers, logs | CRUD and session-action coverage is incomplete; see UI-03. Customer history and both log sections are present. |
| FR-16 | Server-rendered Jinja2 + HTMX in sections 1 and 6 | Shared domain/service calls for all manual actions are not stated; see UI-04. |
| FR-17 | CSV actions in session detail and order list | Session selection and availability outside CLOSED are unclear; see UI-05. |
| FR-18 | Section 7 simulator, fake identities, feature gate | Dev-only wording conflicts with demo scope; shared messaging interface is omitted; see UI-06. |
| FR-19 | Fake simulator identities and screenshot data | Fake product/session/customer seed script and demo setup are missing; see UI-07. |
| NFR-1 | Low-end-device principle and section 10 asset budgets | Server RAM and resource verification are missing; see UI-08. Asset limits alone do not verify RAM usage. |
| NFR-7 | Login rate-limit copy and server-side validation | CSRF, password hashing, cookie flags and security acceptance checks are absent; see UI-01. |

- **UI-01 — OPEN — FR-13 / NFR-7 security coverage:** Should the UI contract
  explicitly reference the PRD security requirements and add acceptance coverage
  for unauthenticated access, password hashing, CSRF on all mutations (including
  HTMX), secure session cookies, login rate limiting and their user-visible
  failures? No authentication implementation or security parameters chosen here.
- **UI-02 — OPEN — FR-14 next-session gap:** Where should the next SCHEDULED
  session appear, including the no-OPEN-session state? The current empty state
  only offers creation. The aggregate "x dari y" quota also lacks a display rule
  for unlimited per-product quotas; what should that metric/progress state show?
- **UI-03 — OPEN — FR-15 CRUD/action gaps:** Specify product deletion, session
  creation/editing/deletion, DRAFT scheduling/cancellation and product attachment
  and quota editing controls. Section 7 only details SCHEDULED/OPEN/CLOSED actions.
  How should service rejections and destructive confirmations be presented?
  This question does not authorize new state transitions or resolve PRD Q5/Q7.
- **UI-04 — OPEN — FR-16 shared-rule gap:** Should the UI specification explicitly
  require every dashboard mutation to call the existing domain/services used by
  the chatbot, with no rules duplicated in routes/templates/HTMX responses?
  FR-16 remains mandatory under the PRD; no alternative architecture is adopted.
- **UI-05 — OPEN — FR-17 export scope:** Does section 7's CLOSED-session export
  describe button placement only, or intentionally restrict CSV export to CLOSED?
  FR-17 states export of a session without that restriction. How does the Orders
  export select its session, especially when no session filter is selected?
- **UI-06 — OPEN — FR-18 simulator scope/interface:** Reconcile "dev only" with
  the PRD's dev-and-demo simulator. Is a demo allowed to enable the same feature
  gate, and how is the shared MessagingGateway path made explicit? Identity
  selection must still resolve authorization from owner_numbers, not UI labels.
  No new deployment behavior, provider or role rule is selected here.
- **UI-07 — OPEN — FR-19 fake-data seed gap:** Where should the required fake
  product/session/customer seed script and demo setup be documented, and should
  the simulator spec link to it? Real product data (Q6) remains unanswered.
- **UI-08 — OPEN — NFR-1 / performance measurement gap:** What reproducible
  workload verifies the roughly 512 MB server RAM target and low-spec development
  target? Are section 10 KB limits decimal or binary, and does HTML include inline
  assets and the largest populated page? CSS/JS/HTML budgets do not replace RAM
  acceptance. No sizes for nonexistent application assets are claimed.
- **UI-09 — OPEN — Document precedence conflict:** UI-UX says it wins on visual
  and UX matters, while AGENTS.md and PRD section 0 say the PRD always wins. How
  should overlapping functional UX requirements be handled? The two requested
  binding-reference sentences were added without changing either precedence rule.
- **UI-10 — OPEN — Internal component/rule conflicts:** Resolve exactly one
  primary action (sections 1/6 and the supplied binding rules) versus at most one
  and explicitly zero allowed (section 7); 20px card padding versus the token-only
  spacing rule; raw RGBA modal shadow/backdrop colors versus all colors as CSS
  variables; and section 10's logo-only image rule versus section 6's optional
  inline SVG icons. UI-3 restricts backdrop-filter declarations to @supports and
  two selectors, but section 5's reduced-transparency reset also includes .card
  and is outside @supports. Which literal rules/examples should M2 tests enforce?
- **UI-11 — OPEN — Contrast/rendered-background coverage:** All 13 explicit
  section 2 pairs pass. The contract does not cover actual composited --glass
  over gradient backgrounds, metric helper text, bot bubbles, error text on form
  surfaces, loading opacity, or the focus ring on other adjacent backgrounds.
  Should additional rendered-state pairs be specified? This document-only script
  is explicitly authorized for this task; section 12 UI-1 still requires parsing
  the future tokens.css. No tokens or contract pairs were changed.

### Contrast computation

`.venv/bin/python scripts/check_contrast.py`: exit 0, **13/13 pass**, 0 fail.
Thresholds are checked before rounding: text 4.5:1; focus 3:1.
Tokens in docs/UI-UX.md remain byte-for-byte unchanged; no failing-pair proposal
is needed. Actual rendered-page contrast and UI-1 through UI-8 remain UNVERIFIED.

| Pair | Ratio | Minimum | Result |
|---|---:|---:|---|
| `--text` on `--bg` | 13.5229:1 | 4.5:1 | PASS |
| `--text` on `--surface` | 14.9673:1 | 4.5:1 | PASS |
| `--text-2` on `--bg` | 5.0806:1 | 4.5:1 | PASS |
| `--text-2` on `--surface` | 5.6232:1 | 4.5:1 | PASS |
| `--on-primary` on `--primary` | 4.8834:1 | 4.5:1 | PASS |
| `--on-primary` on `--primary-hover` | 6.1072:1 | 4.5:1 | PASS |
| `--on-primary` on `--danger-strong` | 5.6982:1 | 4.5:1 | PASS |
| `--tint-sage-text` on `--tint-sage` | 5.6430:1 | 4.5:1 | PASS |
| `--tint-latte-text` on `--tint-latte` | 7.0303:1 | 4.5:1 | PASS |
| `--tint-gold-text` on `--tint-gold` | 6.2952:1 | 4.5:1 | PASS |
| `--tint-danger-text` on `--tint-danger` | 5.5574:1 | 4.5:1 | PASS |
| `--tint-neutral-text` on `--tint-neutral` | 6.2260:1 | 4.5:1 | PASS |
| `--focus` on `--bg` | 4.4121:1 | 3:1 | PASS |

### Documentation-task verification

- `make test && make lint`: exit 0; 2 passed in 0.49s; Ruff passed,
  14 files formatted; mypy no issues in 14 source files.
- `.venv/bin/ruff check scripts/check_contrast.py`: exit 0, all checks passed.
- `.venv/bin/ruff format --check scripts/check_contrast.py`: exit 0,
  1 file already formatted.
- `.venv/bin/mypy scripts/check_contrast.py`: initial run found an Any-return
  annotation issue with exponentiation; replaced it with standard-library
  math.pow and reran: exit 0, no issues in 1 source file.
- `.venv/bin/python scripts/check_contrast.py --self-test`: exit 0,
  7 tests passed in 0.003s (formula reference values, linearization boundary,
  unrounded threshold, symmetry and parser error/coverage checks).
- `.venv/bin/python scripts/check_contrast.py`: exit 0; table above.
- `git diff --check`: exit 0, no whitespace errors. PRD diff contains only the
  two requested binding-reference sentences and their paragraph spacing.
- UI deviations: no visual changes. The task-authorized checker input is
  docs/UI-UX.md instead of the future tokens.css required by M2 UI-1.
- UNVERIFIED: rendered UI/security behavior, UI-1 through UI-8 integration,
  browser screenshots, total CSS/JS/HTML sizes and server RAM. Only the downloaded
  upstream HTMX distribution size (51,238 bytes) is measured at this stage.

## M2 planning — 2026-10-11

No code written. Prerequisite verified: migrations/versions/0001_m1_initial_schema.py,
app/db and app/services are present; make test: 136 passed in 8.66s;
make lint: Ruff passed, 37 files formatted, mypy passed for 37 source files.
Owner decisions recorded in D-026 through D-035; do not ask them again.
UI-01 security mechanisms, UI-04 shared service rule, UI-08 KB units/workload,
and part of UI-02/UI-03 are now specified by the owner. Their remaining details
below are still OPEN. UI-6 explicitly allows at most one primary button under
the current instruction; zero on Orders is allowed. UI-8 is deferred to M3.

- **M2-01 — OPEN — Dashboard service boundary and admin authorization:** Existing
  mutation services require an exact phone match in owner_numbers; there is no
  authenticated-admin execution path. Existing services also lack overview/list,
  customer-history/log/export reads, product deletion, and session edit/delete.
  May M2 extend app/services with authenticated-admin authorization and missing
  read/CRUD use cases while reusing M1 domain rules and transactions? How should
  admin identity be represented in audit actors? Routes must never fake an owner
  phone number or access ORM/query logic directly. Literal use of only existing
  M1 service methods cannot cover FR-14/FR-15/FR-17 or even admin authentication.
- **M2-02 — OPEN — CRUD controls, transitions and copy (remaining UI-03):** Specify
  product deletion semantics (hard delete versus availability toggle), session
  editing/deletion permissions and controls, DRAFT scheduling/cancellation
  actions, and product attachment/removal controls. Specify create/edit submit
  labels, validation/success/confirmation text, navigation/skip/logout copy and
  URL mapping not present in UI-UX. No new state transition is proposed.
- **M2-03 — OPEN — Security policy parameters:** Specify signing-key environment
  variable name, cookie SameSite value and lifetime, localhost definition,
  rate-limit attempts/window and trusted per-IP source, username/password
  validation policy and behavior when create-admin finds an existing account.
  Specify unauthenticated full-page/HTMX response behavior and CSRF failure copy.
  Mechanisms in D-026 through D-028 are settled, not being reconsidered.
- **M2-04 — OPEN — Literal CSS conflicts (remaining UI-10):** The card example uses
  20px padding outside the spacing scale. Modal shadow/backdrop RGBA colors are
  outside tokens.css despite the all-colors-as-variables rule. UI-3 restricts
  backdrop-filter declarations to @supports and .glass-bar/.modal, but the
  reduced-transparency example sets it outside @supports and on .card. Specify
  the authoritative compliant declarations/tokens without changing the visual
  direction. Logo/brand treatment remains explicitly OPEN; optional icons versus
  logo-only wording is still unresolved if icons are wanted.
- **M2-05 — OPEN — Remaining overview display details:** For mixed finite and
  unlimited products, does the aggregate sold numerator include unlimited sales,
  and what does the aggregate progressbar show (also for zero/all-unlimited quota)?
  Define most-recent-CLOSED ordering/tie-break, five-latest-order ordering/status
  scope, and how the required no-OPEN empty state combines with CLOSED metrics
  and next-SCHEDULED information. The scope and status sets in D-030 are settled.
- **M2-06 — OPEN — CSV scope and representations (remaining UI-05):** Is export
  available for all session statuses, and what happens without an Orders session
  filter? Does export follow the status filter? Specify waktu's source timestamp,
  nomor_order representation (no separate order-number field exists), status
  representation (internal value or Indonesian label), and injection prefix.
  Encoding, delimiter, columns, row granularity and masking are already settled.
- **M2-07 — OPEN — List/log details and privacy:** Specify default filters and
  stable ordering, previous/next labels, customer-list and audit/conversation
  columns, what constitutes a conversation before M3, and whether both Log
  sections paginate independently. How should E.164 phones be displayed with
  the first-four/last-three mask example using a domestic prefix? Structured
  payloads/message text can themselves contain full phones: specify redaction
  scope for NFR-6. Full phones remain permitted only on explicitly opened
  customer detail pages. Retention policy remains unspecified.

UI-09 precedence and UI-11 optional rendered-contrast additions remain recorded;
no new interpretation or contrast pairs were selected. NFR-1 RAM workload is
still unspecified; binary asset budgets with 50 fake orders do not establish
512 MB RAM acceptance. PRD Q1/Q3/Q4/Q5/Q6/Q7/Q8 decisions outside the supplied
M2 fields remain deferred; no provider, payment or structured fulfillment work
is proposed. UI-06/UI-07 are outside M2.
