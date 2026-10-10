# KopSusRen PO System v2

A WhatsApp pre-order chatbot and web dashboard for a small coffee business.
M0 provides only a scaffold and `GET /health`, returning `{"status":"ok"}`.
Ordering, persistence, dashboard, messaging, and LLM integrations are not built yet.

## Local development

Use Python 3.12.3 (`.python-version`) and GNU Make. Dependencies require Python
3.12; `make setup` uses `python3.12` by default. Network access to PyPI and GitHub
is needed for initial setup. Run from a Git checkout:

```sh
make setup
make test
make lint
make run
```

The app listens on `http://127.0.0.1:8000`; check `/health`. Stop with Ctrl-C.
FastAPI's OpenAPI, Swagger, and ReDoc routes are disabled.
M0 uses no environment variables and does not load `.env`.

## Structure and scope

- `app/domain/`: pure business rules, without I/O or framework imports.
- `app/services/`: database-backed use cases.
- `app/bot/`: conversations, tools, and prompts.
- `app/gateways/`: messaging and LLM adapters.
- `app/web/`: dashboard routes and templates.
- `tests/`: mirrors application packages; `tests/eval/` is reserved for M4.
- `docs/PRD.md`: source of truth; `docs/decisions.md`: technical decisions.

Only M0 is implemented. M1–M6 follow the PRD in order. Development remains local
through M5; provider selection and deployment are deferred.

## Dependencies and lock generation

`pyproject.toml` pins direct runtime and development dependencies.
`requirements.lock` pins the entire resolved dependency set, including transitive
packages. It was generated in an empty Python 3.12.3 virtual environment after
installing the M0 dependencies, using `python -m pip freeze`.
`make setup` installs that lock with `--no-deps`, then runs `pip check`.

To regenerate intentionally, create an empty temporary virtual environment,
install the exact direct pins from `pyproject.toml`, and run its
`python -m pip freeze > requirements.lock`. Review every changed dependency,
verify Python compatibility, record decisions, and rerun clean setup/tests/lint.
No separate lock-generation tool is used. This is a version lock, not a
hash-verified or cross-platform resolution lock.

## Public repository safeguards

Use fake data only. Never commit secrets, real phone numbers, or customer data.
`.env`, virtual environments, SQLite databases and sidecars, logs, and backups
are ignored. `.env.example` must list every variable introduced later.
`make setup` installs a pinned detect-secrets pre-commit hook. CI also runs:

```sh
.venv/bin/pre-commit run detect-secrets --all-files
```

Scan staged files locally with `.venv/bin/pre-commit run detect-secrets`.
Scanning is an additional safeguard and does not replace reviewing staged files.
M0 stores no customer data. A retention policy must be documented before customer
data handling is implemented; no retention duration has been chosen.

## Verification

CI runs setup, tests, lint/types, and secret scanning. Action and hook revisions
are pinned to verified commit SHAs. Actual local M0 results are recorded in
`docs/m0-verification.txt` without local usernames or home paths.
