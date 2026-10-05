from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from context_pack.cli import main
from context_pack.commands import cmd_decision, cmd_init, cmd_inspect, cmd_status, cmd_sync
from context_pack.discover import parse_agents_pack_path
from context_pack.doctor import run_doctor
from context_pack.secrets import scan_text


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_parse_agents_pack_path() -> None:
    text = "# AGENTS\n\n## Context Pack\nUses pack at `.context/`.\n\n## Other\nx\n"
    assert parse_agents_pack_path(text) == ".context"


def test_init_status_doctor_happy(repo: Path) -> None:
    msg = cmd_init(cwd=repo)
    assert "Initialized" in msg
    assert (repo / ".context" / "manifest.toml").is_file()
    assert (repo / ".context" / "POLICY.md").is_file()
    assert "## Context Pack" in (repo / "AGENTS.md").read_text(encoding="utf-8")
    gi = (repo / ".gitignore").read_text(encoding="utf-8")
    assert ".context/private/" in gi

    status = cmd_status(cwd=repo)
    assert "protocol: 0.1" in status
    assert "always_on_bytes:" in status

    findings = run_doctor(cwd=repo)
    assert all(f.severity != "error" for f in findings)


def test_decision_and_inspect(repo: Path) -> None:
    cmd_init(cwd=repo)
    path = Path(cmd_decision("Use Postgres for primary store", cwd=repo))
    assert path.is_file()
    assert "postgres" in path.name

    prefs = repo / ".context" / "prefs" / "go-style.md"
    prefs.write_text("# Go style\nUse gofmt.\n", encoding="utf-8")

    out = cmd_inspect("postgres database architecture", cwd=repo)
    assert "decisions/" in out
    assert "routed_estimate_tokens:" in out
    assert "load_all_estimate_tokens:" in out


def test_doctor_catches_secrets_and_budget(repo: Path) -> None:
    cmd_init(cwd=repo)
    bad = repo / ".context" / "prefs" / "leak.md"
    bad.write_text("api_key = \"sk-1234567890abcdef\"\n", encoding="utf-8")
    findings = run_doctor(cwd=repo)
    assert any(f.code == "secret_like" for f in findings)

    policy = repo / ".context" / "POLICY.md"
    policy.write_text("x" * 3000, encoding="utf-8")
    findings = run_doctor(cwd=repo)
    assert any(f.code == "always_on_budget" for f in findings)


def test_doctor_broken_supersedes(repo: Path) -> None:
    cmd_init(cwd=repo)
    d = repo / ".context" / "decisions" / "20261004-new.md"
    d.write_text(
        "---\nsupersedes: 20260101-missing.md\n---\n\n# New\n",
        encoding="utf-8",
    )
    findings = run_doctor(cwd=repo)
    assert any(f.code == "broken_supersedes" for f in findings)


def test_sync_adapters(repo: Path) -> None:
    cmd_init(cwd=repo)
    out = cmd_sync(cwd=repo)
    assert "CLAUDE.md" in out
    assert (repo / "CLAUDE.md").is_file()
    assert "@AGENTS.md" in (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert (repo / ".cursor" / "rules" / "context-pack.mdc").is_file()
    assert (repo / ".github" / "copilot-instructions.md").is_file()


def test_secret_patterns() -> None:
    assert scan_text("AKIAIOSFODNN7EXAMPLE")
    assert scan_text("github token ghp_abcdefghijklmnopqrstuv")
    assert not scan_text("no secrets here, just postgres and redis")


def test_cli_main_doctor(repo: Path) -> None:
    cmd_init(cwd=repo)
    assert main(["--cwd", str(repo), "doctor"]) == 0
    assert main(["--cwd", str(repo), "status"]) == 0


def test_cli_module_entrypoint(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cmd_init(cwd=repo)
    src = str(Path(__file__).resolve().parents[1] / "src")
    monkeypatch.setenv("PYTHONPATH", src)
    proc = subprocess.run(
        [sys.executable, "-m", "context_pack", "--cwd", str(repo), "status"],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo,
    )
    assert proc.returncode == 0, proc.stderr
    assert "protocol: 0.1" in proc.stdout
