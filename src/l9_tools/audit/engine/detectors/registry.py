#!/usr/bin/env python3
"""L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, registry]
owner: platform
status: active
/L9_META

Detector registry: always-on native detectors + opt-in analyzer adapters +
optional preflight bridge."""
from __future__ import annotations

from .native import ALL_DETECTORS as _NATIVE
from .semantic import detect_semantic
from .adapters import ADAPTERS
from .preflight_bridge import preflight_bridge

# Always-on deterministic detectors: pattern-based (native) + precision-gated
# semantic (dead-wiring / interface-drift / observability).
NATIVE_DETECTORS = _NATIVE + [detect_semantic]

__all__ = ["NATIVE_DETECTORS", "ADAPTERS", "preflight_bridge"]
