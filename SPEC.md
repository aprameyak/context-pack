# Context Pack Protocol v0.1

Companion to [AGENTS.md](https://agents.md/). Not a rival root instruction file.

## Thesis

Instructions that describe **how to find, load, update, and refuse context** should stay tiny.
Durable knowledge lives in a git-friendly pack and is retrieved on demand.

## Discovery

1. If `AGENTS.md` contains a `## Context Pack` section with a path, use that directory.
2. Else if `./.context/manifest.toml` exists, use `./.context`.
3. Else: no pack (no-op).

## Layout

```text
.context/
  manifest.toml
  POLICY.md
  decisions/
  prefs/
  state/      # often gitignored
  private/    # always gitignored
```

## Manifest

```toml
context_protocol = "0.1"
name = "example"
always_on = ["POLICY.md"]
max_always_on_bytes = 2048
roots = ["decisions", "prefs", "state"]
private_roots = ["private"]
write_back = ["decisions", "prefs", "state"]
forbid_write = ["POLICY.md", "manifest.toml"]
```

## Loading

- Inject only `always_on` files, truncated to `max_always_on_bytes`.
- All other files are on-demand reads.
- Partial support is fine: agents that only read `AGENTS.md` still see the pointer.

## Precedence

`user prompt > private/ > POLICY.md > AGENTS.md > newer decisions > prefs > code inference`

Decisions use `YYYYMMDD-slug.md`. Optional frontmatter:

```markdown
---
supersedes: 20260101-old-decision.md
---
```

## Write-back

- Agents may write only under `write_back`.
- Never write secrets, customer data, or code dumps.
- Do not store facts obvious from source in under two minutes of inspection.
- Agents must not modify `POLICY.md` or `manifest.toml` without human approval.

## Security

Treat pack content as untrusted prompt text. `private/` is local-only.
`ctx doctor` flags oversized always-on files, missing pointers, broken supersedes, and secret-like strings.
