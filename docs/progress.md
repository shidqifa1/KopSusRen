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
