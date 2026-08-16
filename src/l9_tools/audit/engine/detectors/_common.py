#!/usr/bin/env python3
"""L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, common]
owner: platform
status: active
/L9_META

Shared helpers for detectors: deterministic finding-record construction.

Detectors emit plain dicts using the canonical `finding_schema.Finding` field
names. run.py validates them into Finding models and estimates leverage. Every
record is grounded in a real `path:line`.
"""
from __future__ import annotations

import hashlib


def finding_id(prefix: str, rule: str, evidence: str) -> str:
    """Stable, deterministic id derived from (rule, evidence) -- unchanged across
    runs and independent of how many other findings exist."""
    digest = hashlib.sha256(f"{rule}|{evidence}".encode("utf-8")).hexdigest()[:6]
    return f"{prefix}-{digest}"


def owner_layer_for(rel_path: str) -> str:
    """Heuristic owner layer = top-level directory of the evidence path."""
    top = rel_path.split("/", 1)[0]
    return top if "/" in rel_path else "root"


def make_record(
    *, prefix: str, rule_broken: str, rel_path: str, line: int,
    severity: str, impact: str, correction: str,
    cwe: str = "", category: str = "", blast: int = 1, blocks_release: bool = False,
) -> dict:
    evidence = f"{rel_path}:{line}"
    return {
        "id": finding_id(prefix, rule_broken, evidence),
        "severity": severity,
        "rule_broken": rule_broken,
        "evidence": evidence,
        "impact": impact,
        "correction": correction,
        "owner_layer": owner_layer_for(rel_path),
        "blocks_release": blocks_release,
        "cwe": cwe,
        "category": category,
        "_blast": blast,   # consumed by run.py leverage estimation, then stripped
    }


def line_of_offset(text: str, offset: int) -> int:
    """1-based line number of a character offset."""
    return text.count("\n", 0, offset) + 1
