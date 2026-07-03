"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [cli]
tags: [l9-contract, cli]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from l9_tools.contracts.compiler import compile_contract
from l9_tools.contracts.models import ContractRequest
from l9_tools.contracts.validators import validate_contract_bundle
from l9_tools.retrieval.retrieval_policy import retrieve_context
from l9_tools.routing.agent_router import select_agent_profile
from l9_tools.routing.profile_router import select_profile
from l9_tools.routing.risk_router import route_risk
from l9_tools.utils.jsonio import read_json, write_json, write_text


def _load_task(path: Path) -> dict[str, Any]:
    value = read_json(path, default=None)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a JSON object")
    return value


def cmd_compile(args: argparse.Namespace) -> int:
    task = _load_task(args.task)
    request = ContractRequest.from_mapping(args.repo, task, agent=args.agent)
    bundle = compile_contract(
        request,
        debt_intelligence_root=args.debt_intelligence_root,
        graphiti_client_path=args.graphiti_client,
        graphiti_group_id=args.graphiti_group_id,
        structural_context_path=args.structural_context,
    )
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "contract_bundle.json", bundle.to_dict())
    write_text(out_dir / "contract.md", bundle.contract_markdown)
    print(json.dumps({"contract_id": bundle.contract_id, "out_dir": str(out_dir)}, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    bundle = read_json(args.bundle, default=None)
    if not isinstance(bundle, dict):
        print(f"{args.bundle}: must be JSON object", file=sys.stderr)
        return 1
    errors = validate_contract_bundle(bundle)
    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"status": "pass", "bundle": str(args.bundle)}, indent=2))
    return 0


def cmd_explain_risk(args: argparse.Namespace) -> int:
    task = _load_task(args.task)
    request = ContractRequest.from_mapping(args.repo, task, agent=args.agent)
    evidence = retrieve_context(request, debt_intelligence_root=args.debt_intelligence_root)
    risk, risk_reasons = route_risk(request, evidence)
    profile, profile_reasons = select_profile(request, risk)
    print(json.dumps({"repo": request.repo, "risk": risk, "ci_profile": profile, "reasons": risk_reasons + profile_reasons}, indent=2, sort_keys=True))
    return 0


def cmd_select_agent(args: argparse.Namespace) -> int:
    print(json.dumps(select_agent_profile(args.agent), indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="l9-contract")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_compile = sub.add_parser("compile")
    p_compile.add_argument("--repo", required=True)
    p_compile.add_argument("--task", type=Path, required=True)
    p_compile.add_argument("--agent", default="unknown")
    p_compile.add_argument("--debt-intelligence-root", type=Path, default=None)
    p_compile.add_argument("--graphiti-client", type=Path, default=None)
    p_compile.add_argument("--graphiti-group-id", default=None)
    p_compile.add_argument("--structural-context", type=Path, default=None)
    p_compile.add_argument("--out-dir", type=Path, default=Path("out/contracts"))
    p_compile.set_defaults(func=cmd_compile)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("bundle", type=Path)
    p_validate.set_defaults(func=cmd_validate)

    p_risk = sub.add_parser("explain-risk")
    p_risk.add_argument("--repo", required=True)
    p_risk.add_argument("--task", type=Path, required=True)
    p_risk.add_argument("--agent", default="unknown")
    p_risk.add_argument("--debt-intelligence-root", type=Path, default=None)
    p_risk.set_defaults(func=cmd_explain_risk)

    p_agent = sub.add_parser("select-agent")
    p_agent.add_argument("--agent", required=True)
    p_agent.set_defaults(func=cmd_select_agent)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (ValueError, json.JSONDecodeError, FileNotFoundError, OSError) as exc:
        print(f"l9-contract: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
