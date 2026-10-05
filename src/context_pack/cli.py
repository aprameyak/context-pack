from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from . import commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ctx",
        description="Context Pack CLI — AGENTS.md companion for retrieval policy",
    )
    parser.add_argument("--version", action="version", version=f"ctx {__version__}")
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="Operate as if invoked from this directory",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create .context pack and AGENTS.md pointer")
    p_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite POLICY.md and manifest.toml",
    )

    sub.add_parser("status", help="Show pack status and adapter presence")
    sub.add_parser("doctor", help="Validate pack health; exit 1 on errors")

    p_dec = sub.add_parser("decision", help="Scaffold a dated decision file")
    p_dec.add_argument("title", help="Decision title")

    p_ins = sub.add_parser(
        "inspect",
        help="Dry-run which files would load for a query",
    )
    p_ins.add_argument("query", help="Task/query keywords")
    p_ins.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Max on-demand files to select (default: 3)",
    )

    sub.add_parser(
        "sync",
        help="Write thin adapters for Claude, Cursor, and Copilot",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cwd = args.cwd.resolve() if args.cwd else None

    try:
        if args.command == "init":
            print(commands.cmd_init(cwd=cwd, force=args.force))
            return 0
        if args.command == "status":
            print(commands.cmd_status(cwd=cwd))
            return 0
        if args.command == "doctor":
            code, out = commands.cmd_doctor(cwd=cwd)
            print(out)
            return code
        if args.command == "decision":
            print(commands.cmd_decision(args.title, cwd=cwd))
            return 0
        if args.command == "inspect":
            print(commands.cmd_inspect(args.query, cwd=cwd, limit=args.limit))
            return 0
        if args.command == "sync":
            print(commands.cmd_sync(cwd=cwd))
            return 0
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
