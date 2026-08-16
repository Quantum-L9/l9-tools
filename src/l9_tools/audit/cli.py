"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, cli]
tags: [audit, cli]
owner: platform
status: active
/L9_META

l9-audit CLI -- deterministic, no-LLM repository audit engine.

    l9-audit run <repo> [--base-ref R] [--out F] [--analyzers a,b]
                        [--with-preflight] [--fail-on THRESHOLD]

Emits a canonical findings envelope (finding_schema.Finding records) and
returns a CI gate exit code (1 if any finding meets --fail-on, else 0).
Read-only: no network, no LLM, no repo mutation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from l9_tools.audit.engine.run import gate_exit_code, run_audit


def cmd_run(args: argparse.Namespace) -> int:
    analyzers = [a.strip() for a in (args.analyzers or "").split(",") if a.strip()]
    report = run_audit(
        args.repo,
        args.base_ref,
        analyzers=analyzers,
        with_preflight=args.with_preflight,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    code = gate_exit_code(report, args.fail_on)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(json.dumps({
            "status": "audit_complete",
            "findings": report["summary"]["total"],
            "by_severity": report["summary"]["by_severity"],
            "out": str(args.out),
            "limitations": report["limitations"],
            "gate": {"fail_on": args.fail_on, "exit_code": code},
        }, indent=2))
    else:
        sys.stdout.write(payload)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="l9-audit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Audit a repository and emit canonical findings.")
    p_run.add_argument("repo", type=Path, nargs="?", default=Path("."))
    p_run.add_argument("--base-ref", default="UNKNOWN")
    p_run.add_argument("--out", type=Path, help="Write findings envelope here (default: stdout).")
    p_run.add_argument("--analyzers", default="", help="Comma-separated opt-in adapters, e.g. ruff,eslint.")
    p_run.add_argument("--with-preflight", action="store_true",
                       help="Also run the l9-repo-preflight bridge if available.")
    p_run.add_argument("--fail-on", default="none",
                       choices=["none", "low", "medium", "high", "critical", "blocks-release"],
                       help="CI gate: exit 1 if any finding meets this threshold (default: none).")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, json.JSONDecodeError, FileNotFoundError, OSError) as exc:
        print(f"l9-audit: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
