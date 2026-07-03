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
