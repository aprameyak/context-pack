# context-pack

Git-friendly **Context Pack** for coding agents — an [AGENTS.md](https://agents.md/) companion, not a rival.

> Instructions that describe how to find context should stay tiny.
> Durable knowledge is retrieved on demand.

## Why

Teams juggle `AGENTS.md`, `CLAUDE.md`, Cursor rules, Copilot instructions, and “memory bank” folders that dump thousands of tokens every turn.

Context Pack v0.1 standardizes only:

1. A small **retrieval policy** (`.context/POLICY.md`)
2. Durable **decisions** / **prefs** / optional **state**
3. Thin **adapters** so one pack feeds many tools

It does **not** invent another always-on root prompt format. Discovery rides on AGENTS.md.

## Install

```bash
pip install -e .
# or without install:
PYTHONPATH=src python -m context_pack --help
```

Requires Python 3.11+.

## Quick start

```bash
ctx init
ctx decision "Use Postgres for primary storage"
ctx inspect "database schema migration"
ctx doctor
ctx sync
ctx status
```

## Commands

| Command | Purpose |
|---|---|
| `ctx init` | Create `.context/`, gitignore private/state, add AGENTS.md pointer |
| `ctx status` | Pack size, counts, adapter presence |
| `ctx doctor` | Budget, secrets, supersedes, pointer checks (exit 1 on errors) |
| `ctx decision "title"` | Scaffold `decisions/YYYYMMDD-slug.md` |
| `ctx inspect "query"` | Dry-run routed files vs load-all token estimate |
| `ctx sync` | Write CLAUDE.md import, Cursor rule, Copilot stub |

## Layout

```text
.context/
  manifest.toml
  POLICY.md
  decisions/
  prefs/
  state/      # gitignored by default
  private/    # gitignored
```

See [SPEC.md](./SPEC.md) for the v0.1 protocol.

## Adapters

`ctx sync` writes pointers, not full copies:

- `AGENTS.md` → `## Context Pack` section
- `CLAUDE.md` → `@AGENTS.md` import
- `.cursor/rules/context-pack.mdc`
- `.github/copilot-instructions.md`

## Design stance

- Minimal, Markdown-first, git-friendly
- No central server
- Compatible with AGENTS.md / Agent Skills / MCP (MCP optional later)
- Explicit context over hidden magic
- Graceful when an agent only reads AGENTS.md

## Example

See [`examples/demo`](./examples/demo).

## License

MIT
