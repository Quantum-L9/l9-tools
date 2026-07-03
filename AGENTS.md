<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [agent-rules]
tags: [l9-tools, coding-contract, no-stubs]
owner: platform
status: active
/L9_META -->

# AGENTS.md

## Mission

Build and maintain `l9-tools` as a reusable, node-neutral tooling layer for L9 contract compilation and agent-accessible governance tools.

## Non-negotiables

* No fake validation.
* No placeholder behavior presented as complete.
* No network calls during tests.
* No hardcoded credentials.
* No direct repo mutation from contract compilation.
* Missing external memory is represented as `Unknown` or empty evidence, never invented.
* Compiler output must be both human-readable and machine-readable.
* Every generated contract must include validation gates and remaining unknowns.
* MCP tools must return structured JSON.

## Boundaries

* Cursor-specific hooks remain in Cursor-Governance.
* CI repair remains in PR_Repair and l9-ci-debt-resolver.
* Corpus mining remains in l9-ci-debt-intelligence.
* `l9-tools` may read exported artifacts from those systems, but must not assume it owns them.

## Validation

Before commit:

```bash
make validate
```
