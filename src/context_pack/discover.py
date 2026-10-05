from __future__ import annotations

import re
from pathlib import Path

CONTEXT_SECTION = re.compile(
    r"^##\s+Context Pack\s*$([\s\S]*?)(?=^##\s|\Z)",
    re.MULTILINE,
)
PATH_LINE = re.compile(
    r"(?:path\s*[:=]\s*|at\s+|directory\s+)[`'\"]?([^\s`'\"]+)[`'\"]?",
    re.IGNORECASE,
)
BACKTICK_PATH = re.compile(r"`([^`]+)`")


def find_git_root(start: Path) -> Path | None:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def parse_agents_pack_path(agents_text: str) -> str | None:
    match = CONTEXT_SECTION.search(agents_text)
    if not match:
        return None
    body = match.group(1)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = PATH_LINE.search(line)
        if m:
            return m.group(1).strip().rstrip("/")
        for bt in BACKTICK_PATH.findall(line):
            if "context" in bt or bt.startswith("."):
                return bt.strip().rstrip("/")
    return ".context"


def discover_pack(cwd: Path | None = None) -> Path | None:
    cwd = (cwd or Path.cwd()).resolve()
    root = find_git_root(cwd) or cwd

    agents = root / "AGENTS.md"
    if agents.is_file():
        rel = parse_agents_pack_path(agents.read_text(encoding="utf-8"))
        if rel:
            candidate = (root / rel).resolve()
            if (candidate / "manifest.toml").is_file():
                return candidate

    default = root / ".context"
    if (default / "manifest.toml").is_file():
        return default
    return None
