<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [repo, readme]
tags: [l9-tools, contract-compiler, mcp, cli]
owner: platform
status: active
/L9_META -->

# l9-tools

Shared executable tooling layer for L9 agents, nodes, coding contracts, retrieval adapters, and governance compilers.

`l9-tools` is the reusable engine room. It does not own Cursor hooks, CI repair, or repo-health mining. It compiles evidence-backed work contracts from repo health memory, Graphiti episodic memory, structural code context, routing policy, and agent behavior profiles.

## Primary product

`l9-contract`

A deterministic coding-contract compiler that turns a task request into a governed coding contract:

- risk classification
- CI profile selection
- agent risk modifiers
- PR_Repair policy
- human approval requirement
- retrieved context summary
- MUST / MUST NOT / VALIDATE clauses
- machine-readable JSON bundle
- human-readable Markdown contract

## Audit engine

`l9-audit`

A deterministic (**no-LLM, no-network, read-only**) repository audit engine. It
turns a repository into canonical `Finding` records — the evidence layer that
feeds the contract compiler. Every finding is grounded in a real `path:line`;
absent tools/parsers degrade to a recorded limitation rather than a fabricated
result. Same repo state → byte-identical findings envelope.

- native static detectors (secrets/dangerous-calls, quality, missing-tests)
- semantic detectors: dead-wiring, interface-arity drift (Python `ast` + TS/JS
  via optional tree-sitter), observability gaps
- read-only external-analyzer adapters (opt-in; missing tool → limitation)
- deterministic leverage scoring per finding
- a CI gate: `--fail-on` returns a non-zero exit when findings meet a threshold

The audit engine produces findings; the `l9-contract` compiler remains the sole
owner of turning work into a governed contract. The forward edge (audit findings
→ `l9-contract compile`) is a one-way handoff, not a second pipeline.

## Boundary

| System | Owns |
|---|---|
| `l9-tools` | contract compiler, **audit engine**, routers, adapters, schemas, CLI, MCP tools |
| `Cursor-Governance` | Cursor rules, hooks, Graphiti client, memory gates, workspace symlinks |
| `l9-ci-debt-intelligence` | corpus, repair patterns, repo fingerprints, error taxonomy, playbooks |
| `OpenClaw` | orchestration, dispatch, execution lifecycle |
| `PR_Repair` | bounded same-PR patch attempts and repair evidence |
| `l9-ci-core` / `l9-ci-sdk` | deterministic CI and reusable checks |

## CLI

Compile a contract:

```bash
l9-contract compile \
  --repo Quantum-L9/PR_Repair \
  --task examples/task.github-workflow.json \
  --agent codex \
  --debt-intelligence-root examples/debt-intelligence \
  --out-dir out/contracts
```

Validate a bundle:

```bash
l9-contract validate out/contracts/contract_bundle.json
```

Explain risk without writing a contract:

```bash
l9-contract explain-risk \
  --repo Quantum-L9/PR_Repair \
  --task examples/task.github-workflow.json
```

Audit a repository (emit canonical findings + a CI gate exit code):

```bash
l9-audit run . --out findings.json --fail-on high
```

Optional TS/JS interface-arity drift needs the `treesitter` extra:

```bash
pip install "l9-tools[treesitter]"
```

Run the MCP stdio server:

```bash
l9-tools-mcp
```

## MCP tools

* `l9_contract_compile`
* `l9_contract_validate`
* `l9_contract_select_profile`
* `l9_contract_select_agent`
* `l9_contract_explain_risk`
* `l9_contract_fetch_context`
* `l9_contract_render`
* `l9_audit_run`
* `l9_audit_gate`

## Design law

RAG should not directly answer the coding task.

RAG should shape the coding contract.
