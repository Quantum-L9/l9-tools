"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [contracts, schemas]
tags: [schema-paths, validation]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

from pathlib import Path


SCHEMA_FILENAMES = {
    "coding_contract": "coding_contract.schema.json",
    "contract_clause": "contract_clause.schema.json",
    "repo_fingerprint": "repo_fingerprint.schema.json",
    "agent_behavior_profile": "agent_behavior_profile.schema.json",
    "retrieval_result": "retrieval_result.schema.json",
    "compiled_contract_bundle": "compiled_contract_bundle.schema.json",
}


def repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[3]


def schema_path(name: str, root: Path | None = None) -> Path:
    if name not in SCHEMA_FILENAMES:
        raise KeyError(f"unknown schema name: {name}")
    base = root or repo_root_from_module()
    return base / "schemas" / SCHEMA_FILENAMES[name]


def schema_paths(root: Path | None = None) -> dict[str, Path]:
    return {name: schema_path(name, root=root) for name in SCHEMA_FILENAMES}
