"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, package]
tags: [audit, engine, init]
owner: platform
status: active
/L9_META

l9_tools.audit.engine -- deterministic repository audit engine.

Produces canonical `finding_schema.Finding` records from a repository using
static detectors + read-only external-analyzer adapters. Contains NO LLM and
NO network calls. Every finding is grounded in a real `path:line`.
"""
from __future__ import annotations

__all__ = ["run_audit"]

# Re-exported lazily to keep `import audit_engine` cheap and side-effect free.
def run_audit(*args, **kwargs):  # pragma: no cover - thin re-export
    from .run import run_audit as _run_audit
    return _run_audit(*args, **kwargs)
