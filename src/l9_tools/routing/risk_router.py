"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [routing]
tags: [risk, contract-compiler]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence
from l9_tools.utils.text import contains_any, path_matches_any


HIGH_RISK_PATHS = [
    ".github/workflows/**",
    "pyproject.toml",
    "package.json",
    "schemas/**",
    "src/**/auth/**",
    "src/**/security/**",
]

HIGH_RISK_KEYWORDS = [
    "token",
    "secret",
    "permission",
    "dispatch",
    "artifact",
    "publish",
    "release",
    "workflow",
    "schema",
    "authentication",
    "authorization",
    "protected branch",
]

MEDIUM_RISK_KEYWORDS = [
    "refactor",
    "migration",
    "rename",
    "delete",
    "dependency",
    "export",
    "package",
]


def route_risk(request: ContractRequest, evidence: list[RetrievalEvidence]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    text = f"{request.objective} {' '.join(request.constraints)}"

    # Check evidence for explicit strictness signals
    for item in evidence:
        if item.kind == "repo_fingerprint":
            strictness = str(item.data.get("contract_strictness", "")).lower()
            if strictness in {"critical", "high"}:
                reasons.append(f"repo fingerprint contract_strictness={strictness}")
                return "high", reasons
            if strictness == "medium":
                reasons.append(f"repo fingerprint contract_strictness={strictness}")
                return "medium", reasons

    if request.risk_hint in {"high", "medium", "low"}:
        reasons.append(f"risk_hint={request.risk_hint}")
        return request.risk_hint, reasons

    if path_matches_any(request.expected_paths, HIGH_RISK_PATHS):
        reasons.append("expected paths match high-risk files")
        return "high", reasons

    if contains_any(text, HIGH_RISK_KEYWORDS):
        reasons.append("task objective contains high-risk keywords")
        return "high", reasons

    if contains_any(text, MEDIUM_RISK_KEYWORDS):
        reasons.append("task objective contains medium-risk keywords")
        return "medium", reasons

    if any(item.kind in {"repo_fingerprint", "repair_pattern"} for item in evidence):
        reasons.append("repo memory exists; defaulting to standard risk")
        return "medium", reasons

    reasons.append("no high-risk signals found")
    return "low", reasons
