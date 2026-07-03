"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [routing, profile]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import unittest

from l9_tools.contracts.models import ContractRequest
from l9_tools.routing.profile_router import select_profile


class ProfileRouterTests(unittest.TestCase):
    def test_release_profile_for_package_metadata(self) -> None:
        request = ContractRequest(repo="x/y", objective="Update package", expected_paths=["pyproject.toml"])
        profile, reasons = select_profile(request, "high")
        self.assertEqual(profile, "release")
        self.assertTrue(reasons)

    def test_security_profile_for_workflow(self) -> None:
        request = ContractRequest(repo="x/y", objective="Change dispatch", expected_paths=[".github/workflows/ci.yml"])
        profile, reasons = select_profile(request, "high")
        self.assertEqual(profile, "security")
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
