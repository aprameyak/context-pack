from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .discover import discover_pack
from .manifest import Manifest, load_manifest

TOKEN_CHARS = 4  # rough chars/token estimate


@dataclass
class InspectPlan:
    always_on: list[Path]
    selected: list[Path]
    always_on_bytes: int
    selected_bytes: int
    estimated_tokens: int
    load_all_bytes: int
    load_all_tokens: int


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z0-9_]{3,}", text)}


def _score(path: Path, query_tokens: set[str]) -> int:
    name_tokens = _tokenize(path.stem.replace("-", " "))
    try:
        body_tokens = _tokenize(path.read_text(encoding="utf-8")[:4000])
    except (OSError, UnicodeDecodeError):
        body_tokens = set()
    overlap = len(query_tokens & (name_tokens | body_tokens))
    # Prefer decisions slightly for architecture-ish queries
    bonus = 1 if path.parent.name == "decisions" and overlap else 0
    return overlap + bonus


def _all_candidate_files(manifest: Manifest) -> list[Path]:
    files: list[Path] = []
    for root_name in manifest.roots:
        root = manifest.pack_root / root_name
        if not root.is_dir():
            continue
        files.extend(sorted(p for p in root.rglob("*.md") if p.is_file()))
    return files


def build_inspect_plan(query: str, cwd: Path | None = None, limit: int = 3) -> InspectPlan:
    cwd = (cwd or Path.cwd()).resolve()
    pack = discover_pack(cwd)
    if pack is None:
        raise FileNotFoundError("No Context Pack found")
    manifest = load_manifest(pack)

    always_on = [p for p in manifest.always_on_paths() if p.is_file()]
    always_bytes = sum(p.stat().st_size for p in always_on)

    query_tokens = _tokenize(query)
    scored: list[tuple[int, Path]] = []
    for path in _all_candidate_files(manifest):
        score = _score(path, query_tokens) if query_tokens else 0
        if score > 0:
            scored.append((score, path))
    scored.sort(key=lambda item: (-item[0], item[1].as_posix()))
    selected = [p for _, p in scored[:limit]]

    selected_bytes = sum(p.stat().st_size for p in selected)
    load_all = always_on + _all_candidate_files(manifest)
    # unique preserve order
    seen: set[Path] = set()
    unique_all: list[Path] = []
    for p in load_all:
        if p not in seen:
            seen.add(p)
            unique_all.append(p)
    load_all_bytes = sum(p.stat().st_size for p in unique_all)

    routed = always_bytes + selected_bytes
    return InspectPlan(
        always_on=always_on,
        selected=selected,
        always_on_bytes=always_bytes,
        selected_bytes=selected_bytes,
        estimated_tokens=max(1, routed // TOKEN_CHARS),
        load_all_bytes=load_all_bytes,
        load_all_tokens=max(1, load_all_bytes // TOKEN_CHARS),
    )
