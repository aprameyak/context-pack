from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .discover import discover_pack, find_git_root
from .doctor import Finding, run_doctor
from .inspect_cmd import build_inspect_plan
from .manifest import default_manifest_toml, load_manifest
from .policy import ADAPTER_COPILOT, ADAPTER_CURSOR, DEFAULT_POLICY

AGENTS_SECTION = """## Context Pack
This repository uses Context Pack v0.1 at `.context/`.
Read `.context/POLICY.md` before non-trivial work.
Do not load the whole `.context/` tree up front.
Prefer source and tests over notes. Retrieve only relevant `decisions/` and `prefs/` entries.
"""

GITIGNORE_LINES = [
    ".context/private/",
    ".context/state/",
]


def _ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = existing.splitlines()
    changed = False
    for entry in GITIGNORE_LINES:
        if entry not in lines:
            lines.append(entry)
            changed = True
    if changed or not path.is_file():
        text = "\n".join(lines).rstrip() + "\n"
        path.write_text(text, encoding="utf-8")


def _ensure_agents_pointer(root: Path) -> None:
    agents = root / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        if "## Context Pack" in text:
            return
        addition = "\n" + AGENTS_SECTION if text.endswith("\n") else "\n\n" + AGENTS_SECTION
        agents.write_text(text + addition, encoding="utf-8")
        return
    agents.write_text(
        "# AGENTS.md\n\nProject instructions for coding agents.\n\n" + AGENTS_SECTION,
        encoding="utf-8",
    )


def cmd_init(cwd: Path | None = None, force: bool = False) -> str:
    cwd = (cwd or Path.cwd()).resolve()
    root = find_git_root(cwd) or cwd
    pack = root / ".context"
    if (pack / "manifest.toml").is_file() and not force:
        return f"Context Pack already exists at {pack}"

    name = root.name or "project"
    pack.mkdir(parents=True, exist_ok=True)
    for sub in ("decisions", "prefs", "state", "private"):
        (pack / sub).mkdir(exist_ok=True)
        keep = pack / sub / ".gitkeep"
        if sub in {"decisions", "prefs"} and not any(pack.joinpath(sub).glob("*.md")):
            keep.write_text("", encoding="utf-8")

    (pack / "manifest.toml").write_text(default_manifest_toml(name), encoding="utf-8")
    policy = pack / "POLICY.md"
    if force or not policy.is_file():
        policy.write_text(DEFAULT_POLICY, encoding="utf-8")

    # remove gitkeep from gitignored dirs noise — private/state stay empty locally
    for sub in ("state", "private"):
        keep = pack / sub / ".gitkeep"
        if keep.exists():
            keep.unlink()

    _ensure_gitignore(root)
    _ensure_agents_pointer(root)
    return f"Initialized Context Pack at {pack}"


def cmd_status(cwd: Path | None = None) -> str:
    cwd = (cwd or Path.cwd()).resolve()
    root = find_git_root(cwd) or cwd
    pack = discover_pack(cwd)
    lines = [f"repo: {root}"]
    if pack is None:
        lines.append("pack: (none)")
        return "\n".join(lines)

    manifest = load_manifest(pack)
    always = [p for p in manifest.always_on_paths() if p.is_file()]
    always_bytes = sum(p.stat().st_size for p in always)

    def count_md(name: str) -> int:
        d = pack / name
        if not d.is_dir():
            return 0
        return sum(1 for p in d.rglob("*.md") if p.is_file())

    lines.extend(
        [
            f"pack: {pack}",
            f"protocol: {manifest.context_protocol}",
            f"name: {manifest.name}",
            f"always_on_bytes: {always_bytes}/{manifest.max_always_on_bytes}",
            f"decisions: {count_md('decisions')}",
            f"prefs: {count_md('prefs')}",
            f"state_md: {count_md('state')}",
        ]
    )

    adapters = {
        "CLAUDE.md": root / "CLAUDE.md",
        "cursor_rule": root / ".cursor" / "rules" / "context-pack.mdc",
        "copilot": root / ".github" / "copilot-instructions.md",
    }
    for label, path in adapters.items():
        lines.append(f"adapter_{label}: {'yes' if path.is_file() else 'no'}")
    return "\n".join(lines)


def cmd_doctor(cwd: Path | None = None) -> tuple[int, str]:
    findings = run_doctor(cwd)
    lines = [_format_finding(f) for f in findings]
    errors = sum(1 for f in findings if f.severity == "error")
    return (1 if errors else 0, "\n".join(lines))


def _format_finding(f: Finding) -> str:
    return f"{f.severity.upper()}\t{f.code}\t{f.message}"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60] or "decision"


def cmd_decision(title: str, cwd: Path | None = None, body: str | None = None) -> str:
    cwd = (cwd or Path.cwd()).resolve()
    pack = discover_pack(cwd)
    if pack is None:
        raise FileNotFoundError("No Context Pack found; run ctx init first")
    decisions = pack / "decisions"
    decisions.mkdir(exist_ok=True)
    today = date.today().strftime("%Y%m%d")
    slug = _slugify(title)
    path = decisions / f"{today}-{slug}.md"
    n = 2
    while path.exists():
        path = decisions / f"{today}-{slug}-{n}.md"
        n += 1
    content = body or (
        f"# {title}\n\n"
        f"## Status\nAccepted\n\n"
        f"## Context\n\n\n"
        f"## Decision\n\n\n"
        f"## Consequences\n\n"
    )
    path.write_text(content, encoding="utf-8")
    return str(path)


def cmd_inspect(query: str, cwd: Path | None = None, limit: int = 3) -> str:
    plan = build_inspect_plan(query, cwd=cwd, limit=limit)
    pack = discover_pack(cwd)
    assert pack is not None
    lines = [
        f"query: {query}",
        f"always_on ({plan.always_on_bytes} bytes):",
    ]
    for p in plan.always_on:
        lines.append(f"  - {p.relative_to(pack)}")
    lines.append(f"selected ({plan.selected_bytes} bytes):")
    if not plan.selected:
        lines.append("  - (none matched; refine query or add decisions/prefs)")
    for p in plan.selected:
        lines.append(f"  - {p.relative_to(pack)}")
    lines.extend(
        [
            f"routed_estimate_tokens: {plan.estimated_tokens}",
            f"load_all_estimate_tokens: {plan.load_all_tokens}",
            f"savings_ratio: {plan.load_all_tokens / plan.estimated_tokens:.2f}x vs load-all"
            if plan.estimated_tokens
            else "savings_ratio: n/a",
        ]
    )
    return "\n".join(lines)


def cmd_sync(cwd: Path | None = None) -> str:
    cwd = (cwd or Path.cwd()).resolve()
    root = find_git_root(cwd) or cwd
    pack = discover_pack(cwd)
    if pack is None:
        raise FileNotFoundError("No Context Pack found; run ctx init first")

    written: list[str] = []
    _ensure_agents_pointer(root)
    written.append("AGENTS.md")

    claude = root / "CLAUDE.md"
    claude_body = "@AGENTS.md\n\n## Claude Code\nUses the Context Pack pointed from AGENTS.md.\n"
    if claude.is_file():
        text = claude.read_text(encoding="utf-8")
        if "@AGENTS.md" not in text and "AGENTS.md" not in text:
            claude.write_text(claude_body + "\n" + text, encoding="utf-8")
            written.append("CLAUDE.md (prepended import)")
        else:
            written.append("CLAUDE.md (unchanged)")
    else:
        claude.write_text(claude_body, encoding="utf-8")
        written.append("CLAUDE.md")

    cursor_dir = root / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    cursor_rule = cursor_dir / "context-pack.mdc"
    cursor_rule.write_text(ADAPTER_CURSOR, encoding="utf-8")
    written.append(str(cursor_rule.relative_to(root)))

    copilot_dir = root / ".github"
    copilot_dir.mkdir(parents=True, exist_ok=True)
    copilot = copilot_dir / "copilot-instructions.md"
    if copilot.is_file() and "Context Pack" in copilot.read_text(encoding="utf-8"):
        written.append("copilot-instructions.md (unchanged)")
    else:
        if copilot.is_file():
            prev = copilot.read_text(encoding="utf-8")
            copilot.write_text(ADAPTER_COPILOT + "\n" + prev, encoding="utf-8")
            written.append("copilot-instructions.md (prepended)")
        else:
            copilot.write_text(ADAPTER_COPILOT, encoding="utf-8")
            written.append("copilot-instructions.md")

    return "Synced adapters:\n" + "\n".join(f"- {w}" for w in written)
