"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [contracts, validation]
tags: [validation, contract]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from typing import Any


REQUIRED_BUNDLE_FIELDS = {
    "schema_version",
    "contract_id",
    "request",
    "routing",
    "must",
    "must_not",
    "validation",
    "output_evidence",
    "retrieved_evidence",
    "remaining_unknowns",
    "contract_markdown",
}


def validate_contract_bundle(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_BUNDLE_FIELDS - set(bundle))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    if bundle.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")

    for list_field in ("must", "must_not", "validation", "output_evidence", "retrieved_evidence", "remaining_unknowns"):
        if list_field in bundle and not isinstance(bundle[list_field], list):
            errors.append(f"{list_field} must be a list")

    routing = bundle.get("routing")
    if not isinstance(routing, dict):
        errors.append("routing must be an object")
    else:
        for key in ("risk", "ci_profile", "agent_review", "human_approval"):
            if not routing.get(key):
                errors.append(f"routing.{key} is required")

    if not str(bundle.get("contract_markdown", "")).strip():
        errors.append("contract_markdown must be non-empty")

    if not bundle.get("validation"):
        errors.append("validation must include at least one validation command")

    return errors
