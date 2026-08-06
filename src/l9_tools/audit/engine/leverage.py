#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, engine, leverage]
owner: platform
status: active
/L9_META

l9_tools.audit.engine.leverage -- deterministic LeveragePreflight estimation.

The canonical schema requires every finding to carry a LeveragePreflight block;
`leverage_gate` (threshold 2.5) defers low-leverage findings rather than
promoting them to tasks. An auditor that left the block at defaults would score
0.0 and every finding would be gated out. This computes the sub-scores
deterministically from severity + blast radius + blocks_release -- no hand-typed
numbers, no LLM -- so real findings clear the gate and low-severity noise is
deferred by design.
"""
from __future__ import annotations

from l9_tools.audit.finding_schema import Finding, LeveragePreflight, Severity


_SEV_BASE = {
    Severity.critical: 5,
    Severity.high: 4,
    Severity.medium: 3,
    Severity.low: 2,
    Severity.unknown: 2,
}


def _clamp(n: int) -> int:
    return max(0, min(5, n))


def estimate_leverage(finding: Finding, *, blast: int = 1) -> LeveragePreflight:
    """Deterministic leverage sub-scores. `blast` = number of distinct files/refs
    the finding touches (higher → more compounding leverage)."""
    base = _SEV_BASE.get(finding.severity, 2)
    blast_bonus = 1 if blast >= 3 else 0
    release_bonus = 1 if finding.blocks_release else 0
    return LeveragePreflight(
        future_nodes_accelerated=_clamp(base + release_bonus),
        existing_nodes_strengthened=_clamp(base),
        reusable_primitive_created=_clamp(base - 1 + blast_bonus),
        graphable_outputs=3,          # every finding is a graphable node
        maintenance_load_risk=4,      # inverse-scored: fixing reduces future load
    )
