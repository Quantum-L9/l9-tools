"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [retrieval]
tags: [ranking, evidence]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from l9_tools.contracts.models import RetrievalEvidence
from l9_tools.utils.text import normalize_words


KIND_PRIORITY = {
    "repo_fingerprint": 100,
    "contract_clause": 90,
    "repair_pattern": 80,
    "pr_repair_playbook": 70,
    "error_taxonomy": 60,
    "episodic_memory": 50,
    "structural_context": 50,
    "unknown": 0,
}


def rank_evidence(query: str, evidence: list[RetrievalEvidence]) -> list[RetrievalEvidence]:
    words = normalize_words(query)

    def score(item: RetrievalEvidence) -> tuple[int, int]:
        text = f"{item.title} {item.summary} {item.data}".lower()
        lexical = sum(1 for word in words if word and word in text)
        return (KIND_PRIORITY.get(item.kind, 10), lexical)

    return sorted(evidence, key=score, reverse=True)
