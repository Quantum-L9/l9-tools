<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [integration-doc]
tags: [cursor-governance, graphiti, mcp]
owner: platform
status: active
/L9_META -->

# Cursor-Governance Integration

Cursor-Governance should call `l9-tools`; it should not own the compiler runtime.

## Recommended thin adapter

```text
GlobalCommands/tools/l9-tools/
├── README.md
├── mcp.json.example
├── cursor_usage.md
└── contract_request_template.yaml
```

## Rule to add in Cursor-Governance

```text
Before non-trivial coding work:
1. Resolve Graphiti memory group.
2. Retrieve relevant episodic constraints.
3. Call l9-tools contract compiler.
4. Execute the generated contract, not a raw prompt.
```

## Graphiti boundary

Graphiti is episodic memory. It should provide decisions, ADRs, constraints, CI gotchas, and prior outcomes.

It should not be used for symbol location, import graph, or blast-radius questions. That belongs to code-graph.
