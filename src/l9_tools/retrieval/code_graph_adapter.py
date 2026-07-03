"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [retrieval]
tags: [code-graph, structural-context]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from pathlib import Path

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence


class CodeGraphAdapter:
    def __init__(self, structural_context_path: Path | None = None) -> None:
        self.structural_context_path = structural_context_path

    def retrieve(self, request: ContractRequest) -> list[RetrievalEvidence]:
        if not self.structural_context_path or not self.structural_context_path.exists():
            return [
                RetrievalEvidence(
                    source="code-graph",
                    kind="unknown",
                    title="Structural context unavailable",
                    summary="No code-graph structural context file was provided.",
                    data={"path": str(self.structural_context_path) if self.structural_context_path else "Unknown"},
                )
            ]

        text = self.structural_context_path.read_text(encoding="utf-8")
        return [
            RetrievalEvidence(
                source="code-graph",
                kind="structural_context",
                title=self.structural_context_path.name,
                summary=text[:500] if text else "Empty structural context file.",
                data={"path": str(self.structural_context_path), "chars": len(text)},
            )
        ]
