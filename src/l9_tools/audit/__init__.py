"""L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, package]
tags: [audit, init]
owner: platform
status: active
/L9_META

l9_tools.audit -- deterministic, no-LLM repository audit engine.

Produces canonical `Finding` records (finding_schema) from a repository via
static detectors + read-only external-analyzer adapters. No network, no LLM;
every finding is grounded in a real ``path:line``. Activated through the
``l9-audit`` console script and the ``l9_audit_run`` MCP tool.
"""
from __future__ import annotations

__all__ = ["run_audit", "gate_exit_code"]


def run_audit(*args, **kwargs):  # pragma: no cover - thin re-export
    from l9_tools.audit.engine.run import run_audit as _run_audit
    return _run_audit(*args, **kwargs)


def gate_exit_code(*args, **kwargs):  # pragma: no cover - thin re-export
    from l9_tools.audit.engine.run import gate_exit_code as _gate
    return _gate(*args, **kwargs)
