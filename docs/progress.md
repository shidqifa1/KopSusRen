# M1 progress

## Preconditions and approved amendments — 2026-10-11

- `git status --short --branch`: branch `m1-domain`; pre-existing modification
  to docs/questions.md contains M1-01 through M1-08. Preserved that content.
- Read the complete docs/PRD.md and project instructions before code changes.
- `make setup`: exit 0; pinned dependencies already installed;
  `pip check`: No broken requirements found; pre-commit hook installed.
- `make test && make lint`: exit 0; 2 passed in 0.39s; Ruff checks passed;
  14 files already formatted; mypy: no issues found in 14 source files.
- Updated only BR-10 in docs/PRD.md and recorded approved resolutions in
  docs/questions.md. Q5 and Q7 remain open.
- No M1 code or slice commits yet. Decision numbering and missing approved
  slice boundaries are pending human clarification (M1-09 and M1-10).
- The execution sandbox could not initialize its UID map; required shell
  checks ran with explicit escalation approval.

## Slice 1 — Persistence — 2026-10-11

- Resolved M1-09/M1-10; preserved approved wording in D-008–D-015.
  Actual checkout ends at D-006; D-007 left unused per supplied numbering.
- Added nine-table schema, frozen Alembic migration, UTC adapter, connection
  pragmas and database constraint tests. Pinned SQLAlchemy/Alembic and transitives.
- Baseline `make setup && make test && make lint`: escalation needed for Git
  hook installation; exit 0, 2 tests passed, Ruff/mypy passed.
- Attempt 1 `make test && make lint`: 37 tests passed; lint failed on two
  overlong lines. Fixed them and Alembic configuration deprecation warning.
- Attempt 2 `make test && make lint`: exit 0; 37 passed in 2.45s; Ruff passed;
  24 files formatted; mypy no issues in 24 files.
- Local commit created; no push. No new open questions.

## Slice 2 — Session lifecycle — 2026-10-11

- One pure PRD transition function; transactional lifecycle and injected-time
  idempotent tick, schedule validation, sold-out semantics, restart catch-up.
- Attempt 1 `make test && make lint`: 19 failed, 50 passed. The unchanged-row
  assertion incorrectly compared independently generated created/updated times.
  Corrected the test to compare every persisted column against its prior value.
- Attempt 2 `make test && make lint`: exit 0; 69 passed in 3.63s; Ruff passed;
  29 files formatted; mypy no issues in 29 files.
- Local commit created; no push. No new open questions.

## Slice 3a — Orders and atomic quota — 2026-10-11

- Persistent drafts, typed summaries, confirmation snapshots, fresh summary on
  price mismatch, quantity validation via MAX_QTY_PER_ITEM, ownership checks.
- Verified BEGIN IMMEDIATE emitted before reads and blocks a second sqlite3
  connection from reserving a write lock before any write occurred.
- Barrier-released confirmations use separate thread connections; exactly one
  succeeds for quota 1, sold quantity 1, loser retains unchanged draft/items.
  Multi-item rollback, repeated confirmation and sold statuses also verified.
- Attempt 1 `make test && make lint`: exit 0; 85 passed in 4.54s; Ruff passed;
  32 files formatted; mypy no issues in 32 files.
- Local commit created; no push. No new open questions.

## Slice 3b — Cancellation and owner actions — 2026-10-11

- Added pure order transitions, customer/owner cancellation, forward owner status
  changes, session cancellation effects, paid-order attention audit payloads.
- Owner authorization queries owner_numbers at execution; all owner mutations,
  including customer-order features, audited. Added product/session creation,
  price/availability edits and quota edits rejecting reductions below sold units.
- `make test && make lint`: exit 0; 125 passed in 9.79s, Ruff/mypy passed.
  Review found owner customer-feature mutations also require auditing; added
  coverage and reran: exit 0; 126 passed in 8.27s; Ruff passed; 34 files formatted;
  mypy no issues in 34 files. No failed slice attempt.
- Local commit created; no push. No new open questions. Payment/refund behavior
  and fulfillment details remain deferred to unanswered PRD questions.
