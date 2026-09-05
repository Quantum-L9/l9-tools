"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [mcp]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import unittest

from l9_tools.mcp.server import handle_request


class McpToolsTests(unittest.TestCase):
    def test_tools_list(self) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}})
        self.assertIn("result", response)
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertIn("l9_contract_select_agent", names)

    def test_compile_tool(self) -> None:
        response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tools/call",
                "params": {
                    "name": "l9_contract_compile",
                    "arguments": {
                        "repo": "Quantum-L9/l9-pr-repair",
                        "agent": "codex",
                        "debt_intelligence_root": "examples/debt-intelligence",
                        "task": {
                            "objective": "Touch workflow token dispatch",
                            "expected_paths": [".github/workflows/ci.yml"],
                        },
                    },
                },
            }
        )
        self.assertIn("result", response)
        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["routing"]["risk"], "high")

    def test_select_agent_tool(self) -> None:
        response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "tools/call",
                "params": {"name": "l9_contract_select_agent", "arguments": {"agent": "codex"}},
            }
        )
        self.assertIn("result", response)
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertTrue(payload["known"])


if __name__ == "__main__":
    unittest.main()
