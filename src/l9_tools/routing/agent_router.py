"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [routing]
tags: [agent-behavior, contract-compiler]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations


AGENT_MODIFIERS: dict[str, dict[str, list[str]]] = {
    "codex": {
        "must": [
            "List every changed file and justify why each file is in scope.",
            "Update package exports when adding public modules or entrypoints.",
            "Add regression tests that exercise changed behavior, not only import smoke tests.",
        ],
        "must_not": [
            "Do not modify unrelated files.",
            "Do not broad-refactor architecture unless the contract explicitly requires it.",
        ],
    },
    "claude_code": {
        "must": [
            "Prefer the smallest source-aligned implementation that satisfies the contract.",
            "Preserve existing architecture boundaries unless evidence requires a change.",
        ],
        "must_not": [
            "Do not introduce a new abstraction layer only for aesthetic consistency.",
        ],
    },
    "pr_repair": {
        "must": [
            "Consult repair playbooks before patching.",
            "Classify root cause before editing.",
            "Stop when the configured repair attempt cap is reached.",
        ],
        "must_not": [
            "Do not fix only the local symptom when a matching playbook exists.",
        ],
    },
}


def agent_clauses(agent: str) -> tuple[list[str], list[str], list[str]]:
    profile = AGENT_MODIFIERS.get(agent.lower(), {})
    reasons = [f"agent profile applied: {agent}"] if profile else [f"no known agent profile for {agent}"]
    return list(profile.get("must", [])), list(profile.get("must_not", [])), reasons


def select_agent_profile(agent: str) -> dict[str, object]:
    must, must_not, reasons = agent_clauses(agent)
    return {
        "agent": agent,
        "known": bool(AGENT_MODIFIERS.get(agent.lower())),
        "must": must,
        "must_not": must_not,
        "reasons": reasons,
    }
