# AGENTS.md

## Setup
- Python 3.11+
- `python -m venv .venv && .venv/bin/pip install -e ".[dev]"`
- Tests: `.venv/bin/pytest -q`

## Code style
- Stdlib-only runtime (no third-party deps in the CLI package)
- Keep always-on policy examples under 2KB
- Prefer small, tested changes

## Context Pack
This repository uses Context Pack v0.1 at `.context/`.
Read `.context/POLICY.md` before non-trivial work.
Do not load the whole `.context/` tree up front.
Prefer source and tests over notes. Retrieve only relevant `decisions/` and `prefs/` entries.
