"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [retrieval]
tags: [graphiti, episodic-memory]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence


class GraphitiAdapter:
    def __init__(self, client_path: Path | None = None, group_id: str | None = None) -> None:
        self.client_path = client_path
        self.group_id = group_id

    def retrieve(self, request: ContractRequest, limit: int = 5) -> list[RetrievalEvidence]:
        if not self.client_path or not self.client_path.exists():
            return [
                RetrievalEvidence(
                    source="graphiti",
                    kind="unknown",
                    title="Graphiti adapter not configured",
                    summary="No Graphiti client path was provided. Episodic memory retrieval skipped.",
                    data={"client_path": str(self.client_path) if self.client_path else "Unknown"},
                )
            ]

        command = [
            os.environ.get("PYTHON", "python"),
            str(self.client_path),
            "search",
            request.objective,
            "--limit",
            str(limit),
        ]
        if self.group_id:
            command.extend(["--group-id", self.group_id])

        try:
            result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=30)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return [
                RetrievalEvidence(
                    source="graphiti",
                    kind="unknown",
                    title="Graphiti search failed to execute",
                    summary=f"Graphiti subprocess error: {exc}",
                    data={"error": str(exc)},
                )
            ]
        if result.returncode != 0:
            return [
                RetrievalEvidence(
                    source="graphiti",
                    kind="unknown",
                    title="Graphiti search failed",
                    summary=result.stderr.strip()[:500] or "Unknown Graphiti search error",
                    data={"returncode": result.returncode},
                )
            ]

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"raw": result.stdout[:2000]}

        return [
            RetrievalEvidence(
                source="graphiti",
                kind="episodic_memory",
                title="Graphiti search result",
                summary="Graphiti returned episodic memory results for the task.",
                data=payload if isinstance(payload, dict) else {"result": payload},
            )
        ]
