"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [retrieval]
tags: [debt-intelligence, repo-health]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_tools.contracts.models import ContractRequest, RetrievalEvidence
from l9_tools.retrieval.ranking import rank_evidence
from l9_tools.utils.jsonio import read_json, read_jsonl


class DebtIntelligenceAdapter:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def available(self) -> bool:
        return self.root is not None and self.root.exists()

    def retrieve(self, request: ContractRequest, limit: int = 10) -> list[RetrievalEvidence]:
        if not self.available() or self.root is None:
            return [
                RetrievalEvidence(
                    source="l9-ci-debt-intelligence",
                    kind="unknown",
                    title="Debt intelligence unavailable",
                    summary="No debt intelligence root was provided or the path does not exist.",
                    data={"root": str(self.root) if self.root else "Unknown"},
                )
            ]

        evidence: list[RetrievalEvidence] = []

        fingerprint = self._load_repo_fingerprint(request.repo)
        if fingerprint:
            evidence.append(
                RetrievalEvidence(
                    source="l9-ci-debt-intelligence",
                    kind="repo_fingerprint",
                    title=f"Repo fingerprint: {request.repo}",
                    summary=self._summarize_fingerprint(fingerprint),
                    data=fingerprint,
                )
            )

        for pattern in self._load_repair_patterns():
            evidence.append(
                RetrievalEvidence(
                    source="l9-ci-debt-intelligence",
                    kind="repair_pattern",
                    title=str(pattern.get("pattern_id", "repair-pattern")),
                    summary=str(pattern.get("recommended_action") or pattern.get("root_cause") or "Unknown"),
                    data=pattern,
                )
            )

        for playbook in self._load_playbooks():
            evidence.append(
                RetrievalEvidence(
                    source="l9-ci-debt-intelligence",
                    kind="pr_repair_playbook",
                    title=str(playbook.get("playbook_id", "playbook")),
                    summary=str(playbook.get("recommended_action") or playbook.get("preferred_patch_type") or "Unknown"),
                    data=playbook,
                )
            )

        ranked = rank_evidence(request.objective + " " + " ".join(request.expected_paths), evidence)
        return ranked[:limit] or [
            RetrievalEvidence(
                source="l9-ci-debt-intelligence",
                kind="unknown",
                title="No matching debt intelligence",
                summary="Debt intelligence was available but no matching patterns were found.",
                data={"root": str(self.root)},
            )
        ]

    def _load_repo_fingerprint(self, repo: str) -> dict[str, Any]:
        if self.root is None:
            return {}
        safe_names = [repo.replace("/", "__"), repo.replace("/", "_"), repo.split("/")[-1]]
        for name in safe_names:
            for base in (
                self.root / "outputs/repo-fingerprints",
                self.root / "outputs/defense/repo-fingerprints",
                self.root / "repo-fingerprints",
                self.root / "examples/repo-fingerprints",
            ):
                path = base / f"{name}.json"
                value = read_json(path, default=None)
                if isinstance(value, dict):
                    return value
        return {}

    def _load_repair_patterns(self) -> list[dict[str, Any]]:
        if self.root is None:
            return []
        data = read_json(self.root / "outputs/offense/repair_pattern_library.json", default={})
        if isinstance(data, dict) and isinstance(data.get("patterns"), list):
            return [p for p in data["patterns"] if isinstance(p, dict)]
        return []

    def _load_playbooks(self) -> list[dict[str, Any]]:
        if self.root is None:
            return []
        data = read_json(self.root / "outputs/defense/pr-repair/playbooks.json", default={})
        if isinstance(data, dict) and isinstance(data.get("playbooks"), list):
            return [p for p in data["playbooks"] if isinstance(p, dict)]
        return read_jsonl(self.root / "outputs/defense/pr-repair/playbooks.jsonl")

    @staticmethod
    def _summarize_fingerprint(fingerprint: dict[str, Any]) -> str:
        risks = fingerprint.get("primary_risks") or fingerprint.get("risks") or []
        strictness = fingerprint.get("contract_strictness", "Unknown")
        risk_text = ", ".join(map(str, risks[:5])) if isinstance(risks, list) else str(risks)
        return f"contract_strictness={strictness}; primary_risks={risk_text}"
