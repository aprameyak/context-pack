# context-pack

context-pack is a small convention and a `ctx` CLI for keeping project knowledge for coding agents in a `.context/` folder in your repo. Agents always load only a short retrieval policy and read decisions and preferences on demand. It works alongside [AGENTS.md](https://agents.md/) instead of replacing it.

## Why

Projects often end up with `AGENTS.md`, `CLAUDE.md`, Cursor rules, Copilot instructions, and "memory bank" folders that put thousands of tokens into every turn. Context Pack v0.1 standardizes only three things:

1. A small retrieval policy that is always loaded (`.context/POLICY.md`, capped at 2 KB by default).
2. Durable decisions and preferences (plus optional state) that are read only when relevant.
3. Thin adapters so the same pack is found from Claude Code, Cursor, and Copilot.

Discovery goes through a `## Context Pack` section in `AGENTS.md`, so an agent that reads only `AGENTS.md` still finds the pack.

## Example

From [`examples/demo`](examples/demo), which has one decision and one preference file:

```console
$ ctx inspect "add a postgres table"
query: add a postgres table
always_on (176 bytes):
  - POLICY.md
selected (123 bytes):
  - decisions/20260301-use-postgres.md
routed_estimate_tokens: 74
load_all_estimate_tokens: 94
savings_ratio: 1.27x vs load-all
```

`inspect` is a dry run: it shows which files an agent following the policy would read for a task, and a rough token estimate (4 characters per token) compared with loading the whole pack.

## Install

Requires Python 3.11+. The CLI has no third-party runtime dependencies.

```bash
git clone https://github.com/aprameyak/context-pack.git
cd context-pack
pip install -e .
```

Or run it without installing: `PYTHONPATH=src python -m context_pack --help`.

## Usage

```bash
ctx init                                   # create .context/, update .gitignore, add the AGENTS.md pointer
ctx decision "Use Postgres for primary storage"   # create .context/decisions/YYYYMMDD-use-postgres-for-primary-storage.md
ctx inspect "database schema migration"    # dry run: which files would load for this query
ctx doctor                                 # check the pack; exits 1 on errors
ctx sync                                   # write the Claude, Cursor, and Copilot adapters
ctx status                                 # pack size, file counts, adapter presence
```

Global options: `--cwd PATH` runs as if from another directory, and `--version`. `ctx init --force` overwrites `POLICY.md` and `manifest.toml`; `ctx inspect --limit N` changes how many on-demand files are selected (default 3).

`ctx init` creates this layout:

```text
.context/
  manifest.toml
  POLICY.md
  decisions/
  prefs/
  state/      # gitignored by default
  private/    # gitignored
```

`ctx sync` writes pointers, not copies:

- `AGENTS.md`: a `## Context Pack` section
- `CLAUDE.md`: an `@AGENTS.md` import
- `.cursor/rules/context-pack.mdc`
- `.github/copilot-instructions.md`

`ctx doctor` prints one finding per line (`ERROR`, `WARN`, or `INFO`). It checks for always-on files that are missing or over the byte budget, a missing `AGENTS.md` or `## Context Pack` pointer, a missing `.gitignore` or an unignored `private/`, `supersedes` references to decision files that do not exist, and secret-like strings such as AWS keys, private key headers, GitHub tokens, and Slack tokens.

The full protocol (discovery order, manifest fields, precedence, write-back rules) is in [SPEC.md](SPEC.md).

## How it works

- `src/context_pack/cli.py`: argparse entry point for the `ctx` command.
- `src/context_pack/commands.py`: implementation of each subcommand.
- `src/context_pack/discover.py`: finds the pack from the `AGENTS.md` pointer, falling back to `./.context/manifest.toml`.
- `src/context_pack/manifest.py`: reads `manifest.toml` and holds the default manifest.
- `src/context_pack/inspect_cmd.py`: scores files in the manifest roots by keyword overlap between the query and each file's name and first 4,000 characters.
- `src/context_pack/doctor.py` and `secrets.py`: health checks and secret patterns.

This repository uses its own pack in `.context/`, and `examples/` holds a sample manifest, decision, and a complete demo repo.

## Contributing

Issues and pull requests are welcome. Keep the runtime stdlib-only. Before opening a PR, run what CI runs:

```bash
pip install -e ".[dev]"
pytest -q
ctx doctor
```

## License

MIT, see [LICENSE](LICENSE).
