"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [retrieval]
tags: [retrieval-policy]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from pathlib import Path

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence
from l9_tools.retrieval.code_graph_adapter import CodeGraphAdapter
from l9_tools.retrieval.debt_intelligence_adapter import DebtIntelligenceAdapter
from l9_tools.retrieval.graphiti_adapter import GraphitiAdapter
from l9_tools.retrieval.ranking import rank_evidence


def retrieve_context(
    request: ContractRequest,
    *,
    debt_intelligence_root: Path | None = None,
    graphiti_client_path: Path | None = None,
    graphiti_group_id: str | None = None,
    structural_context_path: Path | None = None,
) -> list[RetrievalEvidence]:
    evidence: list[RetrievalEvidence] = []
    evidence.extend(DebtIntelligenceAdapter(debt_intelligence_root).retrieve(request))
    evidence.extend(GraphitiAdapter(graphiti_client_path, graphiti_group_id).retrieve(request))
    evidence.extend(CodeGraphAdapter(structural_context_path).retrieve(request))
    return rank_evidence(request.objective, evidence)
