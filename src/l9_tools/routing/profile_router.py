"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [routing]
tags: [ci-profile, contract-compiler]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from l9_tools.contracts.models import ContractRequest
from l9_tools.utils.text import contains_any, path_matches_any


def select_profile(request: ContractRequest, risk: str) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if path_matches_any(request.expected_paths, [".github/workflows/**"]):
        reasons.append("workflow path touched")
        if contains_any(request.objective, ["release", "publish", "package", "pypi"]):
            return "release", reasons + ["release/publish objective"]
        return "security", reasons + ["workflow changes require security profile"]

    if path_matches_any(request.expected_paths, ["pyproject.toml", "package.json"]):
        reasons.append("package metadata touched")
        return "release", reasons

    if path_matches_any(request.expected_paths, ["schemas/**"]) or contains_any(request.objective, ["schema"]):
        reasons.append("schema change")
        return "agent-review", reasons

    if risk == "high":
        reasons.append("high risk")
        return "security", reasons

    if risk == "low" and contains_any(request.objective, ["docs", "readme", "comment"]):
        reasons.append("low-risk documentation-like change")
        return "minimal", reasons

    reasons.append("default standard profile")
    return "standard", reasons
