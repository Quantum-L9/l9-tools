"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [retrieval]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import unittest
from pathlib import Path

from l9_tools.contracts.models import ContractRequest
from l9_tools.retrieval.retrieval_policy import retrieve_context


class RetrievalPolicyTests(unittest.TestCase):
    def test_missing_sources_emit_unknowns(self) -> None:
        request = ContractRequest(repo="x/y", objective="Update docs")
        evidence = retrieve_context(request)
        kinds = [item.kind for item in evidence]
        self.assertIn("unknown", kinds)

    def test_debt_intelligence_fixture_returns_fingerprint(self) -> None:
        request = ContractRequest(repo="Quantum-L9/l9-pr-repair", objective="dispatch artifact", expected_paths=[".github/workflows/dispatch-intelligence.yml"])
        evidence = retrieve_context(request, debt_intelligence_root=Path("examples/debt-intelligence"))
        kinds = [item.kind for item in evidence]
        self.assertIn("repo_fingerprint", kinds)


if __name__ == "__main__":
    unittest.main()
