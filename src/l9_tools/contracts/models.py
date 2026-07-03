"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [contracts, models]
tags: [coding-contract, dataclasses]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContractRequest:
    repo: str
    objective: str
    agent: str = "unknown"
    expected_paths: list[str] = field(default_factory=list)
    risk_hint: str = "unknown"
    task_type: str = "unknown"
    constraints: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, repo: str, data: dict[str, Any], agent: str = "unknown") -> "ContractRequest":
        objective = str(data.get("objective") or data.get("task") or data.get("description") or "").strip()
        if not objective:
            raise ValueError("task objective is required")
        expected_paths = list(data.get("expected_paths") or data.get("files_expected") or [])
        constraints = list(data.get("constraints") or [])
        return cls(
            repo=repo,
            objective=objective,
            agent=str(data.get("agent") or agent or "unknown"),
            expected_paths=[str(path) for path in expected_paths],
            risk_hint=str(data.get("risk_hint") or "unknown"),
            task_type=str(data.get("task_type") or "unknown"),
            constraints=[str(item) for item in constraints],
        )


@dataclass(frozen=True)
class RetrievalEvidence:
    source: str
    kind: str
    title: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDecision:
    risk: str
    ci_profile: str
    agent_review: str
    human_approval: str
    pr_repair_enabled: bool
    pr_repair_max_attempts: int
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompiledContractBundle:
    contract_id: str
    request: ContractRequest
    routing: RoutingDecision
    must: list[str]
    must_not: list[str]
    validation: list[str]
    output_evidence: list[str]
    retrieved_evidence: list[RetrievalEvidence]
    remaining_unknowns: list[str]
    contract_markdown: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "contract_id": self.contract_id,
            "request": asdict(self.request),
            "routing": self.routing.to_dict(),
            "must": self.must,
            "must_not": self.must_not,
            "validation": self.validation,
            "output_evidence": self.output_evidence,
            "retrieved_evidence": [item.to_dict() for item in self.retrieved_evidence],
            "remaining_unknowns": self.remaining_unknowns,
            "contract_markdown": self.contract_markdown,
        }
