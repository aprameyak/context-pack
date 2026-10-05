from __future__ import annotations

import re
from pathlib import Path

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "generic_api_key_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
    (
        "pem_private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "github_token",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    ),
    (
        "slack_token",
        re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ),
]


def scan_text(text: str) -> list[str]:
    hits: list[str] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(name)
    return hits


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return scan_text(text)
