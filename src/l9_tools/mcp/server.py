"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [mcp]
tags: [stdio, json-rpc]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import sys
from typing import Any

from l9_tools.mcp.tools import TOOL_SCHEMAS, call_tool

SERVER_INFO = {"name": "l9-tools", "version": "1.0.0"}
CAPABILITIES = {"tools": {}}


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": CAPABILITIES,
                "serverInfo": SERVER_INFO,
            }
        elif method == "notifications/initialized":
            return {"jsonrpc": "2.0", "id": request_id, "result": None}
        elif method == "tools/list":
            result = {"tools": TOOL_SCHEMAS}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str):
                raise ValueError("tools/call requires string name")
            if not isinstance(arguments, dict):
                raise ValueError("tools/call arguments must be object")
            value = call_tool(name, arguments)
            result = {"content": [{"type": "text", "text": json.dumps(value, indent=2, sort_keys=True)}]}
        else:
            raise ValueError(f"unsupported method: {method}")

        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be object")
            response = handle_request(request)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        print(json.dumps(response, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
