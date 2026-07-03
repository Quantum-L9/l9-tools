"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [contracts, compiler]
tags: [contract-compiler, rag, routing]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from l9_tools.contracts.models import CompiledContractBundle, ContractRequest, RetrievalEvidence, RoutingDecision
from l9_tools.contracts.renderers import render_contract_markdown
from l9_tools.retrieval.retrieval_policy import retrieve_context
from l9_tools.routing.agent_router import agent_clauses
from l9_tools.routing.profile_router import select_profile
from l9_tools.routing.repair_policy_router import select_repair_policy
from l9_tools.routing.risk_router import route_risk


BASE_MUST = [
    "Inspect relevant repo files before editing.",
    "Preserve existing architecture boundaries.",
    "Touch only files required by the contract.",
    "Use existing repo patterns before introducing new patterns.",
    "Label missing or unverifiable values as Unknown.",
]

BASE_MUST_NOT = [
    "Do not weaken CI, tests, security checks, or validation gates.",
    "Do not invent credentials, secrets, approvals, APIs, or test results.",
    "Do not ship TODOs, placeholders, or stub-only behavior as complete.",
    "Do not auto-merge or mutate protected branches.",
]

BASE_VALIDATION = [
    "Run repo-native format/lint/type/test gates when available.",
    "Run focused tests for changed behavior.",
    "Report any validation that could not be run with exact blocker.",
]

BASE_OUTPUT_EVIDENCE = [
    "changed_files",
    "validation_results",
    "remaining_unknowns",
    "risk_notes",
    "deferred_items",
]


def compile_contract(
    request: ContractRequest,
    *,
    debt_intelligence_root: Path | None = None,
    graphiti_client_path: Path | None = None,
    graphiti_group_id: str | None = None,
    structural_context_path: Path | None = None,
) -> CompiledContractBundle:
    evidence = retrieve_context(
        request,
        debt_intelligence_root=debt_intelligence_root,
        graphiti_client_path=graphiti_client_path,
        graphiti_group_id=graphiti_group_id,
        structural_context_path=structural_context_path,
    )

    risk, risk_reasons = route_risk(request, evidence)
    ci_profile, profile_reasons = select_profile(request, risk)
    repair_enabled, repair_attempts, human_approval, repair_reasons = select_repair_policy(risk, ci_profile)
    agent_must, agent_must_not, agent_reasons = agent_clauses(request.agent)

    must = list(dict.fromkeys(BASE_MUST + _evidence_must_clauses(evidence) + agent_must))
    must_not = list(dict.fromkeys(BASE_MUST_NOT + _evidence_must_not_clauses(evidence) + agent_must_not))
    validation = list(dict.fromkeys(BASE_VALIDATION + _profile_validation(ci_profile)))
    output_evidence = list(dict.fromkeys(BASE_OUTPUT_EVIDENCE))
    remaining_unknowns = _remaining_unknowns(evidence)

    routing = RoutingDecision(
        risk=risk,
        ci_profile=ci_profile,
        agent_review="required" if risk == "high" or ci_profile in {"security", "release", "agent-review"} else "recommended",
        human_approval=human_approval,
        pr_repair_enabled=repair_enabled,
        pr_repair_max_attempts=repair_attempts,
        reasons=risk_reasons + profile_reasons + repair_reasons + agent_reasons,
    )

    contract_id = _contract_id(request, routing)
    markdown = render_contract_markdown(
        contract_id=contract_id,
        request=request,
        routing=routing,
        must=must,
        must_not=must_not,
        validation=validation,
        output_evidence=output_evidence,
        retrieved_evidence=evidence,
        remaining_unknowns=remaining_unknowns,
    )
    return CompiledContractBundle(
        contract_id=contract_id,
        request=request,
        routing=routing,
        must=must,
        must_not=must_not,
        validation=validation,
        output_evidence=output_evidence,
        retrieved_evidence=evidence,
        remaining_unknowns=remaining_unknowns,
        contract_markdown=markdown,
    )


def _contract_id(request: ContractRequest, routing: RoutingDecision) -> str:
    raw = "|".join([request.repo, request.objective, request.agent, routing.risk, routing.ci_profile])
    return "l9-contract-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _evidence_must_clauses(evidence: list[RetrievalEvidence]) -> list[str]:
    clauses: list[str] = []
    for item in evidence:
        if item.kind == "repair_pattern" and item.data.get("recommended_action"):
            clauses.append(str(item.data["recommended_action"]))
        if item.kind == "repo_fingerprint":
            for clause in item.data.get("required_contract_clauses", []) or []:
                clauses.append(str(clause))
    return clauses


def _evidence_must_not_clauses(evidence: list[RetrievalEvidence]) -> list[str]:
    clauses: list[str] = []
    for item in evidence:
        if item.kind == "repo_fingerprint":
            for clause in item.data.get("forbidden_contract_clauses", []) or []:
                clauses.append(str(clause))
    return clauses


def _profile_validation(ci_profile: str) -> list[str]:
    if ci_profile == "security":
        return [
            "Validate workflow permissions if workflows are touched.",
            "Prove no secret values are written to logs or artifacts.",
            "Run security/dependency checks when available.",
        ]
    if ci_profile == "release":
        return [
            "Run package build or dry-run release validation.",
            "Prove publish behavior is disabled for pull_request events.",
            "Validate version/package metadata.",
        ]
    if ci_profile == "agent-review":
        return [
            "Validate schema changes against examples and generated artifacts.",
            "Run contract or payload validation scripts when available.",
        ]
    if ci_profile == "minimal":
        return ["Run documentation or metadata validation available in repo."]
    return ["Run standard repo validation: lint, typecheck, test, gate if available."]


def _remaining_unknowns(evidence: list[RetrievalEvidence]) -> list[str]:
    return [f"{item.source}: {item.summary}" for item in evidence if item.kind == "unknown"]
