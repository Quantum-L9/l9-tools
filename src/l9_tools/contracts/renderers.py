"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [contracts, rendering]
tags: [markdown, contract]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence, RoutingDecision


def render_contract_markdown(
    *,
    contract_id: str,
    request: ContractRequest,
    routing: RoutingDecision,
    must: list[str],
    must_not: list[str],
    validation: list[str],
    output_evidence: list[str],
    retrieved_evidence: list[RetrievalEvidence],
    remaining_unknowns: list[str],
) -> str:
    lines: list[str] = [
        "<!-- L9_META",
        "l9_schema: 1",
        "origin: l9-tools",
        "layer: [generated-contract]",
        "tags: [coding-contract, agent-work-order]",
        "owner: platform",
        "status: active",
        "/L9_META -->",
        "",
        f"# L9 Coding Contract: {contract_id}",
        "",
        "## Task",
        "",
        f"- Repo: `{request.repo}`",
        f"- Objective: {request.objective}",
        f"- Agent: `{request.agent}`",
        f"- Task type: `{request.task_type}`",
        f"- Expected paths: {', '.join(request.expected_paths) if request.expected_paths else 'Unknown'}",
        "",
        "## Routing",
        "",
        f"- Risk: `{routing.risk}`",
        f"- CI profile: `{routing.ci_profile}`",
        f"- Agent review: `{routing.agent_review}`",
        f"- Human approval: `{routing.human_approval}`",
        f"- PR_Repair enabled: `{routing.pr_repair_enabled}`",
        f"- PR_Repair max attempts: `{routing.pr_repair_max_attempts}`",
        "",
        "### Routing reasons",
        "",
    ]
    lines.extend([f"- {reason}" for reason in routing.reasons] or ["- Unknown"])

    lines.extend(["", "## Retrieved Evidence", ""])
    if retrieved_evidence:
        for item in retrieved_evidence:
            lines.extend(
                [
                    f"### {item.kind}: {item.title}",
                    "",
                    f"- Source: `{item.source}`",
                    f"- Summary: {item.summary}",
                    "",
                ]
            )
    else:
        lines.append("- Unknown: no retrieval evidence available.")

    def section(title: str, values: list[str]) -> None:
        lines.extend(["", f"## {title}", ""])
        lines.extend([f"- {value}" for value in values] or ["- Unknown"])

    section("MUST", must)
    section("MUST NOT", must_not)
    section("VALIDATE", validation)
    section("OUTPUT EVIDENCE", output_evidence)
    section("Remaining Unknowns", remaining_unknowns)

    lines.extend(
        [
            "",
            "## Merge Readiness Rule",
            "",
            "Do not claim merge readiness unless the listed validation commands were run honestly or explicitly marked blocked with reason.",
            "",
        ]
    )
    return "\n".join(lines)
