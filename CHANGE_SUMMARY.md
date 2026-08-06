<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [release-notes]
tags: [initial-commit, commit-pack]
owner: platform
status: active
/L9_META -->

# Change Summary

Initial GH-ready commit pack for `Quantum-L9/l9-tools`.

## Landed: audit engine (`l9-audit`)

* `l9_tools.audit` — deterministic, read-only, no-LLM/no-network repository audit
  engine producing canonical `Finding` records (the evidence layer feeding the
  contract compiler).
* `finding_schema` (canonical pydantic `Finding` + leverage gate);
  `engine/` (repo index, read-only guard, symbol index, tree-sitter TS/JS
  extractor, deterministic leverage, run orchestrator + CI gate);
  `engine/detectors/` (native + semantic dead-wiring/interface-drift/observability
  + read-only analyzer adapters + optional preflight bridge).
* `l9-audit` console script (`run` subcommand, `--fail-on` CI gate exit codes).
* MCP tools `l9_audit_run` and `l9_audit_gate`.
* `pydantic>=2` runtime dependency; optional `treesitter` extra for TS/JS
  interface-arity drift; `tree_sitter` mypy missing-import override.
* 50 audit unit tests ported to `unittest` (engine, semantic detectors, TS/JS
  interface drift, CI gate, finding schema, MCP activation). `make validate`
  passes with the full suite (60 tests); existing tests unaffected.

## Added

* Python package `l9_tools`.
* `l9-contract` CLI.
* `l9-tools-mcp` stdio JSON-RPC MCP-style tool server.
* Contract compiler.
* Risk, profile, agent, and repair-policy routers.
* Debt-intelligence, Graphiti, and code-graph retrieval adapters.
* Retrieval ranking module.
* Contract schema helper module.
* JSON schemas.
* YAML policy files matching the original spec.
* Markdown contract templates.
* Executable examples.
* Deterministic unit tests.
* Validation, runbook, manifest, unknown register, final tree, regression guard, and traceability artifacts.

## Fixed from prior pasted pack

* Replaced rich-text quotes with ASCII quotes.
* Replaced en dashes with ASCII hyphens.
* Preserved Makefile tabs through Python-generated file writes.
* Closed Markdown fences.
* Added missing original-spec modules and tests.
* Added `l9_contract_select_agent`.
* Added required validation-governance artifacts.

## Not included

* Live Graphiti network writes.
* Live code-graph server calls.
* GitHub write operations.
* Hosted HTTP API.
