<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [manifest]
tags: [commit-pack, file-inventory]
owner: platform
status: active
/L9_META -->

# Manifest

## Entrypoints

* `src/l9_tools/cli.py`: command line interface for compiling, validating, and risk inspection.
* `src/l9_tools/mcp/server.py`: stdio JSON-RPC MCP-style server.
* `src/l9_tools/contracts/compiler.py`: contract compilation orchestration.
* `src/l9_tools/audit/cli.py`: `l9-audit` deterministic repository audit engine.

## Core modules

* `contracts/`: models, schema helpers, compiler, rendering, validation.
* `audit/`: deterministic, read-only, no-LLM audit engine — `finding_schema` (canonical `Finding`), `engine/` (repo index, read-only guard, symbols, tree-sitter TS/JS, leverage, run orchestrator), `engine/detectors/` (native + semantic + adapters + preflight bridge).
* `retrieval/`: source adapters, ranking, and context normalization.
* `routing/`: risk/profile/agent/repair-policy selection.
* `mcp/`: stdio tool server and tool dispatcher.
* `utils/`: JSON and text helpers.

## Schemas

* `schemas/coding_contract.schema.json`
* `schemas/contract_clause.schema.json`
* `schemas/repo_fingerprint.schema.json`
* `schemas/agent_behavior_profile.schema.json`
* `schemas/retrieval_result.schema.json`
* `schemas/compiled_contract_bundle.schema.json`

## Required governance artifacts

* `CHANGE_SUMMARY.md`
* `VALIDATION.md`
* `UNKNOWN_REGISTER.md`
* `FINAL_TREE.md`
* `REGRESSION_GUARD.md`
* `TRACEABILITY_MAP.yaml`
* `IMPROVEMENT_REPORT.md`
* `DELTA_REPORT.md`
* `CONVERGENCE_REPORT.yaml`
* `improvement_log.jsonl`
