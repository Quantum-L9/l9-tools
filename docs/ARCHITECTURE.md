<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [architecture]
tags: [boundaries, constellation]
owner: platform
status: active
/L9_META -->

# Architecture

`l9-tools` is the reusable tool layer between memory, planning, coding agents, CI, review, and repair.

## Compiler flow

```text
task request
  -> retrieval adapters
  -> ranking
  -> routing policies
  -> contract clause selection
  -> compiled contract bundle
  -> Markdown contract + JSON bundle
```

## Retrieval lanes

| Lane           | Adapter                 | Answers                                                 |
| -------------- | ----------------------- | ------------------------------------------------------- |
| Episodic       | Graphiti                | decisions, ADRs, constraints, CI gotchas                |
| Structural     | code-graph              | imports, file blast radius, symbol location             |
| Health library | l9-ci-debt-intelligence | repo fingerprints, repair patterns, playbooks, taxonomy |

## Runtime boundary

The compiler reads evidence and writes contracts. It does not patch code, merge PRs, call GitHub write APIs, or decide CI truth.
