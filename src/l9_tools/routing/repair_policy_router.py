"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [routing]
tags: [pr-repair, repair-policy]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations


def select_repair_policy(risk: str, ci_profile: str) -> tuple[bool, int, str, list[str]]:
    if risk == "high" or ci_profile in {"security", "release"}:
        return True, 2, "required", ["high-risk work limits PR_Repair to 2 attempts and requires human approval"]

    if ci_profile == "agent-review":
        return True, 3, "recommended", ["agent-review profile allows bounded PR_Repair"]

    return True, 3, "not_required", ["standard bounded PR_Repair policy"]
