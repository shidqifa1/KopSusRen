# PRD: KopSusRen PO System v2 (Rebuild)

Draft v0.1 | 2026-10-09 | Product owner: KopSusRen owner | Audience: the owner and AI coding agents

## 0. How to use this document

- This PRD is the single source of truth. If code, chat history, or an agent's assumption conflicts with it, this document wins.
- Anything marked **\[OPEN\]** is an unanswered decision. An agent must NOT guess it. Stop and ask (see section 13).
- Anything marked **\[ASSUMPTION\]** is a default chosen to unblock work. It can be changed by the owner.
- Requirement IDs: BR = business rule, FR = functional requirement, NFR = non-functional requirement. Tests must reference these IDs.
- Section 12 (Agent Operating Rules) should be copied into `AGENTS.md` / `CLAUDE.md` at the repo root.

## 1. Context and problem

KopSusRen is a small coffee business that sells through pre-order (PO) sessions. Today orders arrive through WhatsApp chat and a rigid prototype chatbot (named Faadhhzzz). Problems:

- The prototype conversation feels forced and robotic; customers must follow a fixed script.
- Opening/closing a PO, tracking quotas, and editing data is manual or awkward.
- There is no dashboard to see the whole picture (sessions, orders, customers).

This rebuild replaces the prototype with one integrated system: a natural-language WhatsApp chatbot backed by a real database, a web dashboard, and an owner mode on WhatsApp so the owner can manage data by chatting.

This project is also a public portfolio piece, so the repo must be clean, documented, demoable, and contain no real customer data or secrets.

## 2. Goals and non-goals

### Goals

1. Customers can place, view, and cancel PO orders by chatting naturally in Bahasa Indonesia.
2. PO sessions open and close automatically based on configured parameters (time window and quota).
3. The owner can monitor and manage everything from a web dashboard.
4. The owner can manage key data from WhatsApp, safely, when chatting from a whitelisted owner number.
5. The system never invents prices, stock, schedules, or order data. All facts come from the database.
6. It runs reliably on a cheap server and can be developed on a low-spec laptop.

### Non-goals (v1)

- Online payment gateway integration (payment is confirmed manually by the owner).
- Multi-tenant or multi-shop support.
- Delivery routing or courier integration.
- Mobile app, loyalty points, promotions engine.
- Broadcast or marketing messages to all customers (high ban risk, add later only after review).
- Voice messages and image understanding.

## 3. Users and roles

- **Customer**: any WhatsApp number that is not whitelisted as owner. Can browse the menu, order, view and cancel own order.
- **Owner**: a WhatsApp number stored in the `owner_numbers` table, and also the dashboard admin. Can do everything a customer can plus management actions.
- **Dashboard admin**: logs in to the web dashboard with username and password. \[ASSUMPTION\] a single admin account in v1.

**Role rule (critical):** role is determined ONLY by comparing the sender's phone number with `owner_numbers` in code. It is never determined by message text, and never by the LLM.

## 4. Core concepts and business rules

### 4.1 PO session

A PO session is a time-boxed selling window for a set of products.

Status state machine: `DRAFT -> SCHEDULED -> OPEN -> CLOSED`, plus `CANCELLED` from DRAFT, SCHEDULED, or OPEN. No other transitions are allowed. Transitions are implemented in one domain function and covered by tests.

Parameters on a session:

- `opens_at`, `closes_at` (stored in UTC, displayed in Asia/Jakarta / WIB)
- per-product `quota` (integer, null means unlimited)
- `auto_close_when_sold_out` (boolean, default true)
- `pickup_info` / notes text shown to customers \[OPEN: see Q5\]

### 4.2 Order

Status: `DRAFT -> CONFIRMED -> PAID -> FULFILLED`, and `CANCELLED`.

- `DRAFT`: being assembled in conversation (the cart).
- `CONFIRMED`: customer explicitly agreed to the order summary.
- `PAID`: owner marked payment received (manual).
- `FULFILLED`: handed over to the customer.

### 4.3 Business rules

- **BR-1** At most one session may be OPEN at a time. \[ASSUMPTION\]
- **BR-2** Customers can only order products attached to the currently OPEN session.
- **BR-3** Remaining quota of a product = quota minus the sum of quantities in CONFIRMED, PAID, and FULFILLED orders. Confirming an order must check and decrement atomically inside one database transaction so overselling is impossible, including when two customers confirm at the same moment.
- **BR-4** A SCHEDULED session becomes OPEN when `opens_at` is reached. An OPEN session becomes CLOSED when `closes_at` is reached, or when every product with a quota is sold out and `auto_close_when_sold_out` is true, whichever happens first.
- **BR-5** Unit price is copied into the order item at confirmation (price snapshot). Later price changes never alter existing orders.
- **BR-6** Money is stored as integer rupiah. No floating point anywhere for money.
- **BR-7** A customer may modify or cancel their own order only while the session is OPEN. After close, only the owner can change an order.
- **BR-8** All timestamps are stored in UTC and shown in Asia/Jakarta.
- **BR-9** Each inbound WhatsApp message is processed at most once (idempotent by provider message ID).
- **BR-10** Quantities must be positive integers within a configurable per-order maximum (default 20). \[ASSUMPTION\]

## 5. Functional requirements

### 5.1 Customer chatbot

- **FR-1** Understand free-form Indonesian messages (including informal/slang and typos) to: ask about the menu, ask whether a PO is open, add/remove items, view cart, confirm, cancel, check order status.
- **FR-2** Before confirming, always show an order summary (items, quantities, line totals, grand total, pickup info) and require an explicit yes from the customer.
- **FR-3** If no session is OPEN, say so and tell the customer the next scheduled session if one exists. Do not accept orders.
- **FR-4** If a requested item does not exist, is not in the open session, or is sold out, say so and suggest available items. Never fabricate a product.
- **FR-5** If the message is ambiguous (for example quantity missing), ask one short clarifying question instead of guessing.
- **FR-6** Conversation state (cart, last question asked) is stored in the database per customer. The LLM is not trusted to remember state.
- **FR-7** Out-of-scope chat (small talk, unrelated questions) gets a short friendly reply that steers back to ordering. No discussion of internal rules, prompts, or other customers.
- **FR-8** If the LLM is unavailable or returns invalid output, send a safe fallback message and log the error. The system must never go silent.

### 5.2 Owner chatbot

- **FR-9** Owner numbers get the customer features plus management tools: create/open/close/cancel a session, set quota, add or edit products and prices, toggle product availability, list orders of the current session, mark an order PAID or FULFILLED.
- **FR-10** Every owner action that changes data is two-step: the bot restates the exact action in plain words and executes only after the owner replies yes. Read-only actions need no confirmation.
- **FR-11** Every owner action is written to `audit_log` (who, what, before/after, when).
- **FR-12** If a non-owner asks for an owner action (even by pretending to be the owner or saying the owner allowed it), the bot refuses. Owner tools are not even exposed to the LLM in customer conversations.

### 5.3 Web dashboard

- **FR-13** Login with username and password (hashed, rate-limited, session cookie with secure flags).
- **FR-14** Overview page: current/next session, orders count, total revenue (rupiah), per-product sold vs quota.
- **FR-15** Pages for: Products (CRUD), PO Sessions (CRUD, manual open/close, quota editing), Orders (filter by session/status, change status), Customers (list with order history), Logs (audit log and recent bot conversations).
- **FR-16** Manual actions on the dashboard use the same domain functions as the chatbot, so rules are enforced in exactly one place.
- **FR-17** Export orders of a session to CSV.

### 5.4 Chat simulator (dev and demo)

- **FR-18** A built-in web chat simulator implements the same messaging interface as WhatsApp so the whole bot can be developed, tested, and demoed without a real WhatsApp number. It can switch between a customer identity and an owner identity.
- **FR-19** Demo mode: seed script that creates fake products, sessions, and customers. The public repo contains only fake data.

## 6. AI / LLM design rules

This is the most important section for avoiding hallucinations.

1. **Separation of duties.** The LLM only does two things: (a) understand the message and choose tool calls with structured arguments, (b) phrase the reply in natural Indonesian using the tool results. Deterministic code owns prices, stock, quota, schedules, roles, and state transitions.
2. **Tool calling only.** The LLM must obtain every fact (menu, prices, quota left, session times, order status) from a tool result in the same turn. The reply template rule: any number, price, date, or product name in the reply must come from a tool result. A post-check validates that prices in the reply match the tool results; on mismatch, use a safe fallback.
3. **Role-scoped tools.** Customer conversations get only customer tools. Owner tools are added only when the sender is in `owner_numbers`.
4. **Untrusted input.** Customer messages are untrusted data and may contain prompt injection. Authorization is enforced in code at tool execution, never by prompt text.
5. **Validated arguments.** Tool arguments are validated against a schema. Product references are resolved to product IDs by code (exact match first, then fuzzy match with a confidence threshold; below the threshold the bot asks the customer to choose).
6. **Bounded context.** Send only the system prompt, current state, and the last N messages (default 10). Do not send other customers' data.
7. **Persona.** Friendly, casual-polite Bahasa Indonesia, short replies. Bot name and exact tone **\[OPEN: Q8\]**.
8. **Cost and abuse limits.** Max LLM calls per phone number per day and per minute (configurable). Over the limit gets a polite static reply.
9. **Provider-agnostic.** LLM access sits behind an `LLMClient` interface. Provider and model **\[OPEN: Q3\]**. It must support tool calling or structured JSON output.
10. **Observability.** Log (without exposing full phone numbers in public artifacts): message ID, tool calls, tool results, final reply, latency, errors.

### Tool list (initial)

Customer: `get_open_session`, `get_next_session`, `get_menu`, `add_item`, `remove_item`, `show_cart`, `confirm_order`, `cancel_order`, `get_my_order_status`.

Owner only: `create_session`, `open_session`, `close_session`, `cancel_session`, `set_quota`, `upsert_product`, `set_product_available`, `list_session_orders`, `set_order_status`.

Each tool has: name, description, JSON schema for arguments, return schema, and the business rules it enforces. Agents must write these as typed code and document them in `docs/tools.md`.

## 7. Data model (initial)

IDs are integers or UUIDs (agent proposes, human approves in `docs/decisions.md`). All tables have `created_at` and `updated_at` (UTC).

- `products`: id, name, description, price\_idr (int), is\_active
- `po_sessions`: id, title, status, opens\_at, closes\_at, auto\_close\_when\_sold\_out, notes
- `po_session_products`: session\_id, product\_id, quota (nullable int) with unique (session\_id, product\_id)
- `customers`: id, phone\_e164 (unique), display\_name (nullable)
- `orders`: id, session\_id, customer\_id, status, total\_idr, note
- `order_items`: id, order\_id, product\_id, quantity, unit\_price\_idr (snapshot)
- `conversation_state`: customer\_id (unique), state\_json, updated\_at
- `messages`: id, provider\_message\_id (unique), direction (in/out), customer\_id, text, created\_at
- `owner_numbers`: id, phone\_e164 (unique), label
- `audit_log`: id, actor (owner number or dashboard admin), action, payload\_json, created\_at
- `admin_users`: id, username (unique), password\_hash

Indexes and constraints must enforce: one OPEN session at a time (application check plus a database-level guard where possible), non-negative quantities, quota consistency.

## 8. Architecture and tech stack

The stack below is an **\[ASSUMPTION\]** chosen for low resource usage and simplicity. The human may override it before M0.

- Language/runtime: Python 3.12, FastAPI.
- Database: SQLite in WAL mode behind SQLAlchemy 2.x plus Alembic migrations, so a move to PostgreSQL later is possible. Quota logic must be correct under concurrent requests (transactions, tested).
- Dashboard: server-rendered Jinja2 templates with HTMX. No SPA framework in v1.
- Scheduler: an in-process periodic tick (every 60 seconds) that evaluates BR-4. It must be idempotent and must catch up after downtime (a restart must not miss an open/close).
- Messaging: `MessagingGateway` interface with `parse_inbound(request) -> InboundMessage`, `send_text(to, text)`. Implementations: `SimulatorGateway` (M3) and a WhatsApp gateway **\[OPEN: Q1\]**.
- LLM: `LLMClient` interface (section 6).
- Tooling: pytest, ruff, mypy or pyright, pre-commit, `Makefile` with `make setup`, `make test`, `make lint`, `make run`.
- Config: environment variables via `.env` (never committed) plus `.env.example` listing every variable.

Suggested layout:

- `app/domain/` pure business logic (sessions, orders, quota). No I/O, no framework imports.
- `app/services/` use cases that combine domain and database.
- `app/bot/` conversation handling, tools, prompts.
- `app/gateways/` messaging and LLM adapters.
- `app/web/` dashboard routes and templates.
- `tests/` mirrors the structure. `docs/` holds decisions, tools, and questions.

WhatsApp integration note: options include the official WhatsApp Business Platform (Cloud API) and unofficial libraries. Unofficial libraries carry a real risk of the number being banned; the official API has its own rules such as a customer-service window and approved templates for business-initiated messages. The agent must verify current rules in the official documentation, summarize them in `docs/whatsapp.md`, and get human approval before choosing. Do not rely on memory for these details.

## 9. Non-functional requirements

- **NFR-1** The app must run within about 512 MB RAM on a small VPS and must be developable on a low-spec Ubuntu laptop (no heavy services required for dev).
- **NFR-2** Bot reply latency target: under 8 seconds for 95% of messages, excluding provider outages. \[ASSUMPTION\]
- **NFR-3** Secrets only in environment variables. No secrets, tokens, real phone numbers, or real customer data in git history. A secret-scanning pre-commit hook is required.
- **NFR-4** Daily automated database backup with a documented restore procedure, tested at least once.
- **NFR-5** Structured logging with correlation per message. Errors never expose stack traces to customers.
- **NFR-6** Phone numbers are personal data: minimize collection, mask in logs shown on the dashboard where reasonable, and document retention in the README.
- **NFR-7** Dashboard security: password hashing, CSRF protection, secure cookies, login rate limiting.
- **NFR-8** Webhook endpoints verify the provider's signature or secret token.

## 10. Milestones and acceptance criteria

Each milestone is done only when every acceptance item is verified by running it. Each milestone also produces a demo artifact (screenshot or short screen recording) for the portfolio.

### M0: Scaffold

- Repo structure, tooling, `Makefile`, `.env.example`, README skeleton, CI that runs lint and tests.
- Accept: `make setup && make test && make lint` pass on a clean checkout.

### M1: Domain and database (no WhatsApp, no LLM)

- Models, migrations, session state machine, order service, quota logic, scheduler tick.
- Accept: automated tests cover BR-1 to BR-10, including: concurrent confirmation of the last unit of quota results in exactly one success; a restart after `closes_at` correctly closes the session; invalid state transitions are rejected.

### M2: Dashboard v1

- Login, products CRUD, sessions CRUD with manual open/close, orders list and status change, CSV export.
- Accept: FR-13 to FR-17 verified manually and by route tests; unauthenticated access is rejected.

### M3: Messaging layer and simulator

- `MessagingGateway`, simulator UI, webhook handling with idempotency (BR-9), message log.
- Accept: the same message delivered twice is processed once; simulator can chat as customer and as owner.

### M4: Customer chatbot

- LLM client, customer tools, conversation state, fallbacks, rate limits.
- Accept: the evaluation set (section 11) passes at the agreed threshold; no fabricated product or price in any eval case; FR-1 to FR-8 verified.

### M5: Owner mode

- Owner tools, two-step confirmation, audit log, role-scoped tool exposure.
- Accept: FR-9 to FR-12 verified; a customer attempting owner actions (including prompt injection cases) changes no data.

### M6: Real WhatsApp and deployment

- WhatsApp gateway chosen via Q1, deployment, backups, monitoring, README and demo video.
- Accept: end-to-end order from a real phone in a staging number; backup restore tested; NFR-3 to NFR-8 verified.

## 11. Testing and evaluation

- Unit tests for all domain rules with the BR IDs in test names.
- Integration tests for services against a temporary SQLite database.
- **Conversation evaluation set** (`tests/eval/cases.yaml`), at least 40 cases, each with: sender role, database fixture, input message(s), expected tool calls, and forbidden content. Must include: normal orders, slang/typo orders, missing quantity, unknown product, sold-out product, PO closed, cancel flow, small talk, attempts to extract the system prompt, attempts to impersonate the owner, attempts to get a discount, and double-sent messages.
- LLM is mocked in unit tests; eval runs against the real provider and is run on demand, with results saved to `docs/eval-results.md`.
- Definition of done for any task: tests written, run, and passing; the actual command output reported.

## 12. Agent operating rules (copy into AGENTS.md / CLAUDE.md)

1. Read this PRD fully before writing code. Work on exactly one milestone at a time; do not build out-of-scope items.
2. If a requirement is ambiguous, missing, or contradictory, STOP and write the question in `docs/questions.md`. Do not guess. Continue only with parts that do not depend on the answer.
3. Never invent library APIs, endpoints, parameters, environment variables, or version numbers. Verify against official documentation, the installed package source, or `--help` output. If you cannot verify something, label it UNVERIFIED in your report.
4. Pin dependency versions. Add a dependency only with a one-line justification in `docs/decisions.md`. Prefer the standard library and already-chosen tools.
5. Business logic lives only in `app/domain` and `app/services`. The LLM, the dashboard, and the gateways must call these functions. Never duplicate rules.
6. Never let LLM output determine prices, stock, roles, or state transitions.
7. Never commit secrets, real phone numbers, or real customer data. Use `.env` and fake seed data.
8. Write tests with the requirement IDs. Run lint and tests before declaring anything done. Report real output, not expected output. Never claim a feature works unless you ran it.
9. Do not edit migrations that have already been applied; add a new migration.
10. Record each non-trivial technical decision (what, why, alternatives) in `docs/decisions.md`.
11. Keep commits small and messages clear. Do not rewrite unrelated files.
12. End every task with a report: what changed, how it was verified (commands and results), what is UNVERIFIED, and any open questions.

## 13. Open questions (human must answer)

Blocking before M0: Q2 (hosting), Q11 (repo visibility). Blocking before M3/M6: Q1. Blocking before M4: Q3, Q7, Q8.

- **Q1** How does the current prototype connect to WhatsApp (which library or service)? Keep it, or switch to the official API?
- **Q2** Where will this be hosted (VPS provider, budget per month)? Is a custom domain available?
- **Q3** Which LLM provider and model, and what monthly budget cap?
- **Q4** Payment flow: bank transfer, QRIS, cash on pickup? Does the bot need to show payment instructions and accept proof of payment?
- **Q5** Fulfillment: pickup only or delivery too? What customer data is required (name, address, notes)? What pickup info appears on each session?
- **Q6** Real product list, prices, and typical volume (orders per PO, POs per month) for sizing and seed data.
- **Q7** What exactly are the 'certain parameters' for auto open/close? This PRD assumes time window plus quota. Are there others (for example raw material stock, day of week rules)?
- **Q8** Bot name, persona, and tone (casual slang vs polite). Keep the name Faadhhzzz?
- **Q9** Can there be more than one owner number and more than one dashboard admin?
- **Q10** Is any code from the prototype reusable, or is this a full rewrite?
- **Q11** Will the repository be public (portfolio) from day one?

## 14. Assumptions log

- Single shop, single owner role set, single dashboard admin.
- One OPEN session at a time.
- Python/FastAPI/SQLite/HTMX stack.
- Max 20 units per item per order.
- Payment confirmed manually by the owner.
- Language: Bahasa Indonesia only.
- Timezone: Asia/Jakarta.

## 15. Glossary

- **PO (pre-order) session**: a window during which customers can order a limited set of products.
- **Quota**: maximum units of a product that can be sold in one session.
- **Owner mode**: management abilities granted to whitelisted WhatsApp numbers.
- **Tool calling**: the LLM requests a function call with structured arguments; code executes it and returns results.
- **Idempotent**: processing the same input twice has the same effect as once.
