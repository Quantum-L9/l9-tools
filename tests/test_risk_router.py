"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [routing, risk]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import unittest

from l9_tools.contracts.models import ContractRequest
from l9_tools.routing.risk_router import route_risk


class RiskRouterTests(unittest.TestCase):
    def test_workflow_token_task_is_high_risk(self) -> None:
        request = ContractRequest(
            repo="x/y",
            objective="Change workflow token permissions",
            expected_paths=[".github/workflows/ci.yml"],
        )
        risk, reasons = route_risk(request, [])
        self.assertEqual(risk, "high")
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
