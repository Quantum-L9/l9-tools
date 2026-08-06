#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit]
tags: [audit, finding_schema]
owner: platform
status: active
/L9_META

l9_audit_suite.finding_schema
==============================

Canonical finding-record schema for the L9 audit suite.

This module is the SINGLE SOURCE OF TRUTH for the shape of a "finding"
emitted by any audit directive (01-07) in this pack. Every audit markdown
file MUST reference this module instead of restating the field list.
Every downstream consumer (audit_to_contract.py, one_command_chain.py,
audit 07 Recursive Alignment conformance pass) MUST import and validate
against this model rather than re-deriving field names with ad hoc
dict.get() defaults.

Schema version is tracked explicitly (SCHEMA_VERSION). Any breaking change
to field names or required-ness is a MAJOR version bump and must be
reflected in CHANGELOG.md at the package root.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

# Path/evidence token matcher, shared with the task-emission helpers so every
# consumer (audit_to_contract, one_command_chain) derives allowed_paths identically.
PATH_RE = re.compile(r"[\w./\-]+\.\w+(?::\d+)?")

try:
    from pydantic import BaseModel, Field, field_validator
    _PYDANTIC = True
except ImportError:  # pragma: no cover - allow schema import without pydantic installed
    _PYDANTIC = False
    BaseModel = object  # type: ignore[assignment,misc]

SCHEMA_VERSION = "1.0.0"
UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    unknown = UNKNOWN


class LeveragePreflight(BaseModel):  # type: ignore[misc]
    """
    Leverage self-score block. Required on every finding per the
    Compounding Leverage Kernel (L9-Leverage.md). A finding scoring below
    the reject threshold (2.5) should be deferred rather than promoted to
    a task, per l9_audit_suite.finding_schema.leverage_gate().
    """

    future_nodes_accelerated: int = Field(
        default=0, ge=0, le=5,
        description="Does resolving this finding make future findings/nodes easier? 0-5.",
    )
    existing_nodes_strengthened: int = Field(
        default=0, ge=0, le=5,
        description="Does this strengthen an existing node/repo? 0-5.",
    )
    reusable_primitive_created: int = Field(
        default=0, ge=0, le=5,
        description="Does the fix create a reusable primitive/pattern? 0-5.",
    )
    graphable_outputs: int = Field(
        default=0, ge=0, le=5,
        description="Does the fix/finding produce state that can be written to a graph store? 0-5.",
    )
    maintenance_load_risk: int = Field(
        default=0, ge=0, le=5,
        description="Inverse-scored: 0 = high maintenance risk, 5 = low/no added maintenance load.",
    )

    def score(self) -> float:
        weights = {
            "future_nodes_accelerated": 0.22,
            "existing_nodes_strengthened": 0.20,
            "reusable_primitive_created": 0.18,
            "graphable_outputs": 0.12,
            "maintenance_load_risk": 0.08,
        }
        total = sum(getattr(self, k) * w for k, w in weights.items())
        norm = sum(weights.values())
        return round(total / norm, 3) if norm else 0.0


class Finding(BaseModel):  # type: ignore[misc]
    """
    Canonical finding record. All audit directives (01-07) emit findings
    conforming to this shape. Do not restate this field list in any
    audit markdown file — reference this module instead:

        Use the canonical finding schema (see finding_schema.py);
        do not restate fields here.
    """

    id: str = Field(..., description="Stable finding identifier, e.g. AUD-003.")
    severity: Severity = Field(default=Severity.unknown)
    rule_broken: str = Field(default=UNKNOWN)
    evidence: str = Field(default=UNKNOWN, description="File path(s) / line refs / excerpt proving the finding.")
    impact: str = Field(default=UNKNOWN, description="Regression target / what breaks if unresolved.")
    correction: str = Field(default=UNKNOWN, description="Required fix / residual action.")
    owner_layer: str = Field(default=UNKNOWN, description="Repo/module/layer that owns the fix.")
    blocks_release: bool = Field(default=False)
    cwe: str = Field(default="")
    category: str = Field(default="")
    duplicate_of: str = Field(default="", description="id of the canonical finding this duplicates, if any.")
    leverage_preflight: LeveragePreflight = Field(default_factory=LeveragePreflight)
    raw: dict[str, Any] = Field(default_factory=dict, description="Original unparsed record, preserved for audit trail.")

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, v: Any) -> str:
        if v is None:
            return UNKNOWN
        v = str(v).lower()
        return v if v in {s.value for s in Severity} else UNKNOWN

    @classmethod
    def parse_obj_loose(cls, d: dict[str, Any]) -> "Finding":
        """
        Tolerant constructor for legacy/loose finding dicts (e.g. records
        using 'prior_id' instead of 'id', or 'residual_action' instead of
        'correction'). Prefer Finding.model_validate(d) / Finding(**d) for
        records already conforming to the canonical shape.
        """
        fid = d.get("id") or d.get("prior_id") or UNKNOWN
        payload = {
            "id": str(fid),
            "severity": d.get("severity", UNKNOWN),
            "rule_broken": str(d.get("rule_broken", UNKNOWN)),
            "evidence": str(d.get("evidence", UNKNOWN)),
            "impact": str(d.get("impact", UNKNOWN)),
            "correction": str(d.get("correction", d.get("residual_action", UNKNOWN))),
            "owner_layer": str(d.get("owner_layer", UNKNOWN)),
            "blocks_release": bool(d.get("blocks_release", False)),
            "cwe": str(d.get("cwe", "")),
            "category": str(d.get("category", "")),
            "duplicate_of": str(d.get("duplicate_of", "")),
            "leverage_preflight": d.get("leverage_preflight", {}),
            "raw": d,
        }
        return cls(**payload)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Finding":
        """Alias for parse_obj_loose (name kept for the one_command_chain kernel)."""
        return cls.parse_obj_loose(d)

    def leverage_score(self) -> float:
        return self.leverage_preflight.score()

    # --- task-emission helpers (SSOT: kernel + audit_to_contract share these) ---
    def allowed_paths(self) -> list[str]:
        found = PATH_RE.findall(self.evidence or "")
        out: list[str] = []
        seen: set[str] = set()
        for tok in found:
            p = tok.split(":", 1)[0]
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out or [UNKNOWN]

    def inspect_first(self) -> list[str]:
        return PATH_RE.findall(self.evidence or "") or [UNKNOWN]

    def constraint(self) -> str:
        parts = [self.rule_broken]
        if self.cwe:
            parts.append(f"CWE={self.cwe}")
        if self.category:
            parts.append(f"category={self.category}")
        return " | ".join(p for p in parts if p and p != UNKNOWN) or UNKNOWN

    def severity_str(self) -> str:
        return self.severity.value if hasattr(self.severity, "value") else str(self.severity)


LEVERAGE_REJECT_THRESHOLD = 2.5


def leverage_gate(finding: "Finding") -> tuple[bool, str]:
    """
    Returns (eligible, reason). A finding scoring below
    LEVERAGE_REJECT_THRESHOLD should be deferred, not promoted to a
    Flawless-Victory task, per the Compounding Leverage Kernel decision
    rules.
    """
    score = finding.leverage_score()
    if score < LEVERAGE_REJECT_THRESHOLD:
        return False, f"leverage_score {score} below reject threshold {LEVERAGE_REJECT_THRESHOLD}"
    return True, f"leverage_score {score} meets threshold"


def schema_json_schema() -> dict[str, Any]:
    """Language-agnostic JSON Schema export, for non-Python consumers."""
    return Finding.model_json_schema()


if not _PYDANTIC:  # pragma: no cover
    raise ImportError(
        "l9_audit_suite.finding_schema requires pydantic>=2. "
        "Install with: pip install pydantic>=2 or uv add pydantic"
    )
