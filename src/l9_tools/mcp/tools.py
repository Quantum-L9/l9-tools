"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [mcp]
tags: [tools, json-rpc]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_tools.audit.engine.run import gate_exit_code, run_audit
from l9_tools.contracts.compiler import compile_contract
from l9_tools.contracts.models import ContractRequest
from l9_tools.contracts.validators import validate_contract_bundle
from l9_tools.retrieval.retrieval_policy import retrieve_context
from l9_tools.routing.agent_router import select_agent_profile
from l9_tools.routing.profile_router import select_profile
from l9_tools.routing.risk_router import route_risk

_FAIL_ON = ["none", "low", "medium", "high", "critical", "blocks-release"]


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {"name": "l9_contract_compile", "description": "Compile an evidence-backed L9 coding contract.", "inputSchema": {"type": "object", "required": ["repo", "task"], "properties": {"repo": {"type": "string"}, "task": {"type": "object"}, "agent": {"type": "string"}, "debt_intelligence_root": {"type": "string"}, "graphiti_client": {"type": "string"}, "graphiti_group_id": {"type": "string"}, "structural_context": {"type": "string"}}}},
    {"name": "l9_contract_validate", "description": "Validate a compiled L9 coding contract bundle.", "inputSchema": {"type": "object", "required": ["bundle"], "properties": {"bundle": {"type": "object"}}}},
    {"name": "l9_contract_explain_risk", "description": "Explain risk and CI profile selection for a task.", "inputSchema": {"type": "object", "required": ["repo", "task"], "properties": {"repo": {"type": "string"}, "task": {"type": "object"}}}},
    {"name": "l9_contract_fetch_context", "description": "Fetch normalized context from configured retrieval adapters.", "inputSchema": {"type": "object", "required": ["repo", "task"], "properties": {"repo": {"type": "string"}, "task": {"type": "object"}}}},
    {"name": "l9_contract_select_profile", "description": "Select CI profile from task and routing policy.", "inputSchema": {"type": "object", "required": ["repo", "task"], "properties": {"repo": {"type": "string"}, "task": {"type": "object"}}}},
    {"name": "l9_contract_select_agent", "description": "Return agent-specific contract modifiers.", "inputSchema": {"type": "object", "required": ["agent"], "properties": {"agent": {"type": "string"}}}},
    {"name": "l9_contract_render", "description": "Compile and return only the Markdown contract.", "inputSchema": {"type": "object", "required": ["repo", "task"], "properties": {"repo": {"type": "string"}, "task": {"type": "object"}}}},
    {"name": "l9_audit_run", "description": "Run the deterministic (no-LLM, read-only) repository audit engine and return the canonical findings envelope.", "inputSchema": {"type": "object", "required": ["repo"], "properties": {"repo": {"type": "string"}, "base_ref": {"type": "string"}, "analyzers": {"type": "array", "items": {"type": "string"}}, "with_preflight": {"type": "boolean"}}}},
    {"name": "l9_audit_gate", "description": "Run the audit engine and return a CI gate decision (exit_code + summary) for the given fail_on threshold.", "inputSchema": {"type": "object", "required": ["repo"], "properties": {"repo": {"type": "string"}, "base_ref": {"type": "string"}, "analyzers": {"type": "array", "items": {"type": "string"}}, "with_preflight": {"type": "boolean"}, "fail_on": {"type": "string", "enum": _FAIL_ON}}}},
]


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "l9_contract_compile":
        return _compile_from_args(arguments).to_dict()

    if name == "l9_contract_render":
        return _compile_from_args(arguments).contract_markdown

    if name == "l9_contract_validate":
        bundle = arguments.get("bundle")
        if not isinstance(bundle, dict):
            return {"status": "fail", "errors": ["bundle must be an object"]}
        errors = validate_contract_bundle(bundle)
        return {"status": "pass" if not errors else "fail", "errors": errors}

    if name == "l9_contract_fetch_context":
        request = _request_from_args(arguments)
        evidence = retrieve_context(
            request,
            debt_intelligence_root=_optional_path(arguments.get("debt_intelligence_root")),
            graphiti_client_path=_optional_path(arguments.get("graphiti_client")),
            graphiti_group_id=arguments.get("graphiti_group_id"),
            structural_context_path=_optional_path(arguments.get("structural_context")),
        )
        return {"evidence": [item.to_dict() for item in evidence]}

    if name == "l9_contract_explain_risk":
        request = _request_from_args(arguments)
        evidence = retrieve_context(request, debt_intelligence_root=_optional_path(arguments.get("debt_intelligence_root")))
        risk, risk_reasons = route_risk(request, evidence)
        profile, profile_reasons = select_profile(request, risk)
        return {"risk": risk, "ci_profile": profile, "reasons": risk_reasons + profile_reasons}

    if name == "l9_contract_select_profile":
        request = _request_from_args(arguments)
        risk, risk_reasons = route_risk(request, [])
        profile, profile_reasons = select_profile(request, risk)
        return {"risk": risk, "ci_profile": profile, "reasons": risk_reasons + profile_reasons}

    if name == "l9_contract_select_agent":
        return select_agent_profile(str(arguments.get("agent") or "unknown"))

    if name == "l9_audit_run":
        return _audit_from_args(arguments)

    if name == "l9_audit_gate":
        report = _audit_from_args(arguments)
        fail_on = str(arguments.get("fail_on") or "none")
        if fail_on not in _FAIL_ON:
            raise ValueError(f"fail_on must be one of {_FAIL_ON}")
        code = gate_exit_code(report, fail_on)
        return {
            "fail_on": fail_on,
            "exit_code": code,
            "passed": code == 0,
            "summary": report["summary"],
            "msna_id": report["msna_id"],
            "limitations": report["limitations"],
        }

    raise ValueError(f"unknown tool: {name}")


def _audit_from_args(arguments: dict[str, Any]) -> dict[str, Any]:
    repo = str(arguments.get("repo") or "")
    if not repo:
        raise ValueError("repo is required")
    analyzers = arguments.get("analyzers") or []
    if not isinstance(analyzers, list):
        raise ValueError("analyzers must be an array of strings")
    return run_audit(
        Path(repo),
        str(arguments.get("base_ref") or "UNKNOWN"),
        analyzers=[str(a) for a in analyzers],
        with_preflight=bool(arguments.get("with_preflight")),
    )


def _compile_from_args(arguments: dict[str, Any]):
    request = _request_from_args(arguments)
    return compile_contract(
        request,
        debt_intelligence_root=_optional_path(arguments.get("debt_intelligence_root")),
        graphiti_client_path=_optional_path(arguments.get("graphiti_client")),
        graphiti_group_id=arguments.get("graphiti_group_id"),
        structural_context_path=_optional_path(arguments.get("structural_context")),
    )


def _request_from_args(arguments: dict[str, Any]) -> ContractRequest:
    repo = str(arguments.get("repo") or "")
    task = arguments.get("task")
    if not repo:
        raise ValueError("repo is required")
    if not isinstance(task, dict):
        raise ValueError("task object is required")
    return ContractRequest.from_mapping(repo, task, agent=str(arguments.get("agent") or "unknown"))


def _optional_path(value: Any) -> Path | None:
    if not value:
        return None
    return Path(str(value))
