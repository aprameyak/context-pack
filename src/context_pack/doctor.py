from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .discover import discover_pack, find_git_root
from .manifest import load_manifest
from .secrets import scan_file

FRONTMATTER = re.compile(r"^---\n([\s\S]*?)\n---\n", re.MULTILINE)
SUPERSEDES = re.compile(r"(?m)^supersedes:\s*[\"']?([^\"'\n]+)[\"']?\s*$")


@dataclass
class Finding:
    severity: str  # error | warn | info
    code: str
    message: str


def _always_on_bytes(pack: Path, rels: list[str]) -> tuple[int, list[Path]]:
    total = 0
    missing: list[Path] = []
    for rel in rels:
        path = pack / rel
        if not path.is_file():
            missing.append(path)
            continue
        total += path.stat().st_size
    return total, missing


def _iter_md_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def _check_supersedes(decisions: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not decisions.is_dir():
        return findings
    for path in _iter_md_files(decisions):
        text = path.read_text(encoding="utf-8")
        fm = FRONTMATTER.match(text)
        if not fm:
            continue
        m = SUPERSEDES.search(fm.group(1))
        if not m:
            continue
        target = m.group(1).strip()
        candidate = decisions / target
        if not candidate.is_file():
            findings.append(
                Finding(
                    "error",
                    "broken_supersedes",
                    f"{path.relative_to(decisions.parent)} supersedes missing {target}",
                )
            )
    return findings


def run_doctor(cwd: Path | None = None) -> list[Finding]:
    cwd = (cwd or Path.cwd()).resolve()
    findings: list[Finding] = []
    root = find_git_root(cwd) or cwd
    pack = discover_pack(cwd)

    agents = root / "AGENTS.md"
    if not agents.is_file():
        findings.append(
            Finding("warn", "missing_agents", "AGENTS.md not found at repo root")
        )
    elif "## Context Pack" not in agents.read_text(encoding="utf-8"):
        findings.append(
            Finding(
                "warn",
                "missing_agents_pointer",
                "AGENTS.md lacks a ## Context Pack section",
            )
        )

    if pack is None:
        findings.append(
            Finding("error", "no_pack", "No Context Pack found (.context/manifest.toml)")
        )
        return findings

    try:
        manifest = load_manifest(pack)
    except Exception as exc:  # noqa: BLE001 — surface parse errors as findings
        findings.append(Finding("error", "bad_manifest", str(exc)))
        return findings

    if manifest.context_protocol.split(".")[0] != "0":
        findings.append(
            Finding(
                "warn",
                "unknown_protocol",
                f"Unsupported context_protocol {manifest.context_protocol}; treating as best-effort",
            )
        )

    total, missing = _always_on_bytes(pack, manifest.always_on)
    for path in missing:
        findings.append(
            Finding("error", "missing_always_on", f"always_on file missing: {path.name}")
        )
    if total > manifest.max_always_on_bytes:
        findings.append(
            Finding(
                "error",
                "always_on_budget",
                f"always_on is {total} bytes; budget is {manifest.max_always_on_bytes}",
            )
        )
    elif total > int(manifest.max_always_on_bytes * 0.85):
        findings.append(
            Finding(
                "warn",
                "always_on_near_budget",
                f"always_on is {total} bytes; nearing budget {manifest.max_always_on_bytes}",
            )
        )

    # state/ and private/ are commonly gitignored and may be absent on clone.
    required_dirs = [
        name for name in manifest.roots if name not in {"state", "private"}
    ]
    for name in required_dirs:
        if not (pack / name).is_dir():
            findings.append(
                Finding("warn", "missing_root", f"expected directory missing: {name}/")
            )

    gitignore = root / ".gitignore"
    if gitignore.is_file():
        gi = gitignore.read_text(encoding="utf-8")
        if ".context/private/" not in gi and "private/" not in gi:
            findings.append(
                Finding(
                    "warn",
                    "private_not_ignored",
                    ".context/private/ is not listed in .gitignore",
                )
            )
    else:
        findings.append(Finding("warn", "no_gitignore", "No .gitignore at repo root"))

    findings.extend(_check_supersedes(pack / "decisions"))

    for path in _iter_md_files(pack):
        # skip private for team scans? still flag secrets everywhere
        hits = scan_file(path)
        for hit in hits:
            findings.append(
                Finding(
                    "error",
                    "secret_like",
                    f"{path.relative_to(pack)} matched secret pattern: {hit}",
                )
            )

    if not findings:
        findings.append(Finding("info", "ok", "Context Pack looks healthy"))
    return findings
