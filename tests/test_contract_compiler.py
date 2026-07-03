"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [contract-compiler]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import unittest
from pathlib import Path

from l9_tools.contracts.compiler import compile_contract
from l9_tools.contracts.models import ContractRequest
from l9_tools.contracts.validators import validate_contract_bundle


class ContractCompilerTests(unittest.TestCase):
    def test_compile_workflow_contract_uses_security_profile(self) -> None:
        request = ContractRequest(
            repo="Quantum-L9/PR_Repair",
            objective="Add dispatch validation with token permissions and artifact coordinates.",
            agent="codex",
            expected_paths=[".github/workflows/dispatch-intelligence.yml"],
        )
        bundle = compile_contract(request, debt_intelligence_root=Path("examples/debt-intelligence"))
        data = bundle.to_dict()
        self.assertEqual(data["routing"]["risk"], "high")
        self.assertEqual(data["routing"]["ci_profile"], "security")
        self.assertEqual(data["routing"]["pr_repair_max_attempts"], 2)
        self.assertFalse(validate_contract_bundle(data))
        self.assertIn("source_repo", bundle.contract_markdown)

    def test_unknowns_are_explicit_when_memory_missing(self) -> None:
        request = ContractRequest(repo="Example/Missing", objective="Update docs", agent="unknown")
        bundle = compile_contract(request)
        self.assertTrue(bundle.remaining_unknowns)
        self.assertIn("Unknown", bundle.contract_markdown)


if __name__ == "__main__":
    unittest.main()
