# Questions

No new questions for M0. PRD Q2 and Q11 are resolved for this milestone by
D-001 and D-002. Other PRD questions remain deferred to their owning milestones.

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
