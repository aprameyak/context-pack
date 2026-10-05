from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_MAX_ALWAYS_ON = 2048


@dataclass
class Manifest:
    path: Path
    context_protocol: str = "0.1"
    name: str = "project"
    always_on: list[str] = field(default_factory=lambda: ["POLICY.md"])
    max_always_on_bytes: int = DEFAULT_MAX_ALWAYS_ON
    roots: list[str] = field(default_factory=lambda: ["decisions", "prefs", "state"])
    private_roots: list[str] = field(default_factory=lambda: ["private"])
    write_back: list[str] = field(
        default_factory=lambda: ["decisions", "prefs", "state"]
    )
    forbid_write: list[str] = field(
        default_factory=lambda: ["POLICY.md", "manifest.toml"]
    )

    @property
    def pack_root(self) -> Path:
        return self.path.parent

    def always_on_paths(self) -> list[Path]:
        return [self.pack_root / rel for rel in self.always_on]


def default_manifest_toml(name: str) -> str:
    return f'''context_protocol = "0.1"
name = "{name}"
always_on = ["POLICY.md"]
max_always_on_bytes = {DEFAULT_MAX_ALWAYS_ON}
roots = ["decisions", "prefs", "state"]
private_roots = ["private"]
write_back = ["decisions", "prefs", "state"]
forbid_write = ["POLICY.md", "manifest.toml"]
'''


def load_manifest(pack_root: Path) -> Manifest:
    manifest_path = pack_root / "manifest.toml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    return Manifest(
        path=manifest_path,
        context_protocol=str(data.get("context_protocol", "0.1")),
        name=str(data.get("name", pack_root.parent.name or "project")),
        always_on=list(data.get("always_on", ["POLICY.md"])),
        max_always_on_bytes=int(data.get("max_always_on_bytes", DEFAULT_MAX_ALWAYS_ON)),
        roots=list(data.get("roots", ["decisions", "prefs", "state"])),
        private_roots=list(data.get("private_roots", ["private"])),
        write_back=list(data.get("write_back", ["decisions", "prefs", "state"])),
        forbid_write=list(
            data.get("forbid_write", ["POLICY.md", "manifest.toml"])
        ),
    )
