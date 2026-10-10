# Decisions

## D-001 Hosting (PRD Q2)
Local only for now. M0 to M5 run locally; no deployment work until M6.
Hosting provider to be decided before M6.

## D-002 Repository visibility (PRD Q11)
Public from day one (portfolio).
Consequences:
- Secret scanning pre-commit hook is part of M0, not later.
- .gitignore must cover .env, *.db, *.sqlite*, logs, and backups from the first commit.
- Only fake seed data in the repo. No real phone numbers, names, or menus with real customer data.

## D-003 Python version
Use the newest Python 3.x available on the dev machine that is >= 3.11.
The agent must verify every dependency supports it, pin it in pyproject.toml
(requires-python) and .python-version, and record the chosen version here.
This overrides "Python 3.12" in the PRD stack if a different version is chosen.

Chosen for M0: Python 3.12.3, the newest executable available on PATH (only
`python3` and `python3.12`; both resolve to 3.12.3). `.python-version` pins
3.12.3; `requires-python = ">=3.12.3,<3.13"` limits the lock to the verified minor
version. Installed package metadata accepts this runtime wherever declared;
distlib has no Requires-Python declaration and is exercised by hook setup.

## D-004 M0 dependencies and version lock

Use standard-library venv and pip freeze instead of adding a lock-generation
tool. Resolve once in an empty Python 3.12.3 environment, pin direct versions
in pyproject.toml, and freeze all installed runtime/dev dependencies into
requirements.lock. Install with `--no-deps`, then validate with `pip check`.
Alternatives: pip-tools or uv; neither is necessary for this small scaffold.
The lock pins versions, not artifact hashes; other platforms are unverified.

Direct dependencies (verified by installation from PyPI):
- FastAPI 0.143.0: mandated HTTP framework; M0 exposes only `/health`.
- Uvicorn 0.54.0: lightweight ASGI server for `make run`.
- HTTPX 0.28.1: ASGI transport for HTTP smoke tests, without a live server or
  Starlette's deprecated HTTPX TestClient integration.
- pytest 9.1.1: mandated test runner.
- Ruff 0.17.0: mandated lint and formatting checks.
- mypy 2.4.0: selected permitted type checker; strict checking without a Node runtime.
- pre-commit 4.6.2: mandated Git hook runner for secret scanning.

All transitive dependencies are pinned in requirements.lock because these
packages require them; no SQLAlchemy, Alembic, template engine, LLM, or messaging
dependency is added before its owning milestone.

References: [pip freeze](https://pip.pypa.io/en/stable/cli/pip_freeze/) and
[FastAPI metadata configuration](https://fastapi.tiangolo.com/tutorial/metadata/).
Installed source and CLI help are used to verify APIs and commands.

## D-005 Public-repository secret scanning and CI

Use Yelp detect-secrets v1.5.0 for both the installed pre-commit hook and CI's
`pre-commit run detect-secrets --all-files`. This adds one lightweight Python
scanner rather than a separate CI-only scanner or downloaded binary.
Do not create a baseline that could hide findings. Test rejection with a fake
staged token, unstage it with `git reset -- <file>`, then remove the fixture;
never commit it. All scaffold files must be staged for a local all-files scan.

Verified with `git ls-remote` against each upstream repository:
- detect-secrets v1.5.0: `68e8b45440415753fff70a312ece8da92ba85b4a`.
- actions/checkout v4.2.2: `11bd71901bbe5b1630ceea73d27597364c9af683`.
- actions/setup-python v5.6.0: `a26af69be951a213d495a4c3e4e4022e16d87065`.

Use these immutable revisions rather than floating release tags. CI uses
Ubuntu 24.04, Python from .python-version, read-only repository permissions,
and the same Makefile checks as local development.
Scanner documentation: https://github.com/Yelp/detect-secrets/tree/v1.5.0.
The hook's runtime transitive dependencies are also pinned through
additional_dependencies, using versions verified in its installed environment:
requests 2.34.2 and PyYAML 6.0.3 (scanner requirements), plus certifi 2026.7.22,
charset-normalizer 3.5.2, idna 3.20, and urllib3 2.8.0 (requests requirements).
The verified hook SHA triggered the scanner's hex-entropy detector during the
first scan. Allowlist only that revision line with the scanner's documented
inline pragma; keep all other files and findings subject to scanning.

## D-006 M0 boundaries and verification artifact

Disable FastAPI docs, ReDoc, and OpenAPI routes so `/health` is the only route.
Introduce no environment variables or `.env` loader; .env.example documents
that fact. Keep domain/service/gateway/bot packages empty until their milestones.
Tests reference M0 for scaffold checks and NFR-3 for public-data safeguards;
BR/FR IDs apply when those behaviors are implemented in later milestones.

Record actual terminal output in docs/m0-verification.txt, redacting home paths
and usernames. This terminal transcript is the M0 demo artifact approved in the
plan; no UI screenshot exists because M0 has no dashboard.
