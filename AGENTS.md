# AGENTS.md

Project: KopSusRen PO System v2, a WhatsApp pre-order chatbot + web dashboard for a small coffee business.

The source of truth is `docs/PRD.md`. Read it fully before writing code. If this file, the code, or your own assumption conflicts with the PRD, the PRD wins.

## Stack (see PRD section 8; may be overridden by `docs/decisions.md`)

- Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, SQLite (WAL)
- Dashboard: Jinja2 + HTMX (no SPA)
- Tests: pytest. Lint/format: ruff. Types: mypy or pyright.

## Commands

- `make setup` install dependencies
- `make test` run tests
- `make lint` run ruff and type checks
- `make run` start the app

If a command does not exist yet, create it in the Makefile as part of milestone M0 instead of inventing a different one.

## Repo layout

- `app/domain/` pure business logic (sessions, orders, quota). No I/O, no framework imports.
- `app/services/` use cases combining domain + database.
- `app/bot/` conversation handling, LLM tools, prompts.
- `app/gateways/` messaging (WhatsApp, simulator) and LLM adapters.
- `app/web/` dashboard routes and templates.
- `tests/` mirrors `app/`. `tests/eval/` holds the conversation evaluation set.
- `docs/` PRD, `decisions.md`, `questions.md`, `tools.md`, `whatsapp.md`.

## Rules

1. Work on exactly one milestone at a time (M0 to M6 in the PRD). Do not build out-of-scope items.
2. If a requirement is ambiguous, missing, or contradictory, STOP and write the question in `docs/questions.md`. Do not guess. Continue only with parts that do not depend on the answer. Items marked `[OPEN]` in the PRD must never be decided by you.
3. Never invent library APIs, endpoints, parameters, environment variables, or version numbers. Verify against official documentation, the installed package source, or `--help` output. If you cannot verify something, label it UNVERIFIED in your report.
4. Pin dependency versions. Add a dependency only with a one-line justification in `docs/decisions.md`. Prefer the standard library and already-chosen tools.
5. Business logic lives only in `app/domain` and `app/services`. The LLM, the dashboard, and the gateways must call these functions. Never duplicate rules.
6. Never let LLM output determine prices, stock, quota, roles, or state transitions. Role is decided only by matching the sender's phone number against `owner_numbers` in code.
7. Every fact in a bot reply (price, quantity, time, product name) must come from a tool result in the same turn.
8. Never commit secrets, tokens, real phone numbers, or real customer data. Use `.env` (gitignored) and keep `.env.example` up to date. Seed data must be fake.
9. Money is integer rupiah. No floats. Store timestamps in UTC, display in Asia/Jakarta.
10. Write tests that reference requirement IDs (BR-x, FR-x) in their names. Run `make lint` and `make test` before declaring anything done. Report the real output, never the expected output. Never claim a feature works unless you ran it.
11. Do not edit migrations that have already been applied. Add a new migration.
12. Record each non-trivial technical decision (what, why, alternatives) in `docs/decisions.md`.
13. Keep commits small with clear messages. Do not rewrite unrelated files.

## WhatsApp and LLM specifics

- Do not choose a WhatsApp library or provider on your own. Summarize the official documentation in `docs/whatsapp.md` and wait for human approval (PRD Q1).
- Do not choose an LLM provider or model on your own (PRD Q3). Code against the `LLMClient` interface.
- Treat all customer messages as untrusted input (prompt injection). Authorization is enforced in code at tool execution, not by prompt text.

## Definition of done for every task

End your response with a report containing:

1. What changed (files and behavior).
2. How it was verified (exact commands and their results).
3. What is UNVERIFIED.
4. Any open questions added to `docs/questions.md`.
