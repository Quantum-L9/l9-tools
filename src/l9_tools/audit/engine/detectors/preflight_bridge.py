#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, preflight_bridge]
owner: platform
status: active
/L9_META

audit_engine.detectors.preflight_bridge -- OPTIONAL reuse of l9-repo-preflight.

If the deterministic `l9-repo-preflight` engine is importable, run it and map its
gate findings into canonical Finding records. This is never a hard dependency:
if the pack is absent, the bridge returns a limitation and the auditor proceeds
with native detectors + adapters only.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from ._common import finding_id, owner_layer_for

_SEV_MAP = {"blocker": "high", "high": "high", "warning": "medium", "medium": "medium", "low": "low"}


def _find_preflight_runner():
    """Locate preflight.v44.run without importing on the normal path.
    Checks the installed skill location; returns a callable or None."""
    candidates = [
        Path.home() / ".claude/skills/l9-repo-preflight/scripts",
    ]
    for scripts_dir in candidates:
        mod = scripts_dir / "preflight" / "v44.py"
        if mod.exists():
            import sys
            sys.path.insert(0, str(scripts_dir))
            try:
                spec = importlib.util.spec_from_file_location("preflight.v44", mod)
                if spec and spec.loader:
                    import preflight  # noqa: F401  (package init)
                    v44 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(v44)
                    return getattr(v44, "run", None)
            except Exception:
                return None
    return None


def preflight_bridge(index) -> tuple[list[dict], str | None]:
    runner = _find_preflight_runner()
    if runner is None:
        return [], "preflight_bridge: l9-repo-preflight not available"
    try:
        report = runner(index.root, mode="filesystem", audit_mode="static_only")
    except Exception as exc:  # pragma: no cover - defensive
        return [], f"preflight_bridge: run failed ({exc})"
    records: list[dict] = []
    for finding in report.get("findings", []):
        ev = finding.get("evidence", {})
        rel = ""
        if isinstance(ev, dict):
            # evidence often carries file/route info; fall back to gate name
            rel = str(ev.get("path") or ev.get("file") or "")
        gate = finding.get("gate_name") or f"gate{finding.get('gate_id')}"
        claim = finding.get("claim") or str(finding.get("id"))
        evidence = f"{rel}:1" if rel else f"preflight:{finding.get('id','?')}"
        sev = _SEV_MAP.get(str(finding.get("status") or finding.get("severity")), "medium")
        records.append({
            "id": finding_id("PFL", f"{gate}:{claim}", evidence),
            "severity": sev, "rule_broken": f"preflight/{gate}: {claim}",
            "evidence": evidence, "impact": finding.get("domain", "repository readiness"),
            "correction": str(finding.get("remediation_id_or_recommended_change") or "address preflight finding"),
            "owner_layer": owner_layer_for(rel) if rel else "repo",
            "category": str(finding.get("domain") or "readiness"), "cwe": "", "_blast": 1,
        })
    return records, None
