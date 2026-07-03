<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [runbook]
tags: [operator, cli, mcp]
owner: platform
status: active
/L9_META -->

# Runbook

## Compile a coding contract

```bash
l9-contract compile \
  --repo Quantum-L9/PR_Repair \
  --task task.json \
  --agent codex \
  --debt-intelligence-root /path/to/l9-ci-debt-intelligence \
  --out-dir out/contracts
```

## Select agent profile

```bash
l9-contract select-agent --agent codex
```

## Use with OpenClaw

OpenClaw should call `l9-contract compile` or MCP tool `l9_contract_compile` before dispatching work.

## Use with Cursor-Governance

Cursor-Governance should expose this repo through a thin adapter. It should not fork this compiler.

## Use with PR_Repair

PR_Repair can ask for a repair-specific contract by providing a task with expected paths and failure context.

## MCP stdio

Start:

```bash
l9-tools-mcp
```

List tools request:

```json
{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}
```

Call compile tool:

```json
{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"l9_contract_compile","arguments":{"repo":"Quantum-L9/PR_Repair","task":{"objective":"Add dispatch validation","expected_paths":[".github/workflows/**"]},"agent":"codex"}}}
```

## Unknown handling

If memory sources are missing, generated contracts still compile but contain explicit `Unknown` entries in `remaining_unknowns`.
