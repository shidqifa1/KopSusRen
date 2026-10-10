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
