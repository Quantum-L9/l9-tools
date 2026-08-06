"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, mcp]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from l9_tools.mcp.server import handle_request


class AuditMcpTests(unittest.TestCase):
    def test_audit_tools_listed(self) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertIn("l9_audit_run", names)
        self.assertIn("l9_audit_gate", names)

    def test_audit_run_tool_returns_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "app").mkdir()
            (tmp / "app" / "m.py").write_text("def r(s):\n    return eval(s)\n", encoding="utf-8")
            response = handle_request({
                "jsonrpc": "2.0", "id": "2", "method": "tools/call",
                "params": {"name": "l9_audit_run", "arguments": {"repo": str(tmp)}},
            })
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertIn("findings", payload)
            self.assertTrue(any(f["severity"] == "high" for f in payload["findings"]))

    def test_audit_gate_tool_returns_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "app").mkdir()
            (tmp / "app" / "m.py").write_text("def r(s):\n    return eval(s)\n", encoding="utf-8")
            response = handle_request({
                "jsonrpc": "2.0", "id": "3", "method": "tools/call",
                "params": {"name": "l9_audit_gate",
                           "arguments": {"repo": str(tmp), "fail_on": "high"}},
            })
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertEqual(payload["exit_code"], 1)
            self.assertIs(payload["passed"], False)


if __name__ == "__main__":
    unittest.main()
