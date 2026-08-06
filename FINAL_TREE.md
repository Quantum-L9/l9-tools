<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [final-tree]
tags: [manifest, tree]
owner: platform
status: active
/L9_META -->

# Final Tree

```text
l9-tools/
├── AGENTS.md
├── CHANGE_SUMMARY.md
├── CONVERGENCE_REPORT.yaml
├── DELTA_REPORT.md
├── FINAL_TREE.md
├── IMPROVEMENT_REPORT.md
├── MANIFEST.md
├── Makefile
├── README.md
├── REGRESSION_GUARD.md
├── RUNBOOK.md
├── TRACEABILITY_MAP.yaml
├── UNKNOWN_REGISTER.md
├── VALIDATION.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CURSOR_GOVERNANCE_INTEGRATION.md
│   ├── OPENCLAW_INTEGRATION.md
│   └── PR_REPAIR_INTEGRATION.md
├── examples/
│   ├── compiled_contract.example.md
│   ├── task.github-workflow.json
│   ├── task.schema-change.json
│   └── debt-intelligence/
├── policies/
│   ├── agent_router.yaml
│   ├── profile_router.yaml
│   ├── repair_policy_router.yaml
│   ├── retrieval_policy.yaml
│   └── risk_router.yaml
├── schemas/
│   ├── agent_behavior_profile.schema.json
│   ├── coding_contract.schema.json
│   ├── compiled_contract_bundle.schema.json
│   ├── contract_clause.schema.json
│   ├── repo_fingerprint.schema.json
│   └── retrieval_result.schema.json
├── src/
│   └── l9_tools/
│       ├── __init__.py
│       ├── cli.py
│       ├── audit/
│       │   ├── __init__.py
│       │   ├── cli.py
│       │   ├── finding_schema.py
│       │   └── engine/
│       │       ├── repo_index.py
│       │       ├── readonly.py
│       │       ├── symbols.py
│       │       ├── ts_syntax.py
│       │       ├── leverage.py
│       │       ├── run.py
│       │       └── detectors/
│       ├── contracts/
│       ├── mcp/
│       ├── retrieval/
│       ├── routing/
│       └── utils/
├── templates/
├── tests/
├── improvement_log.jsonl
├── run_validation.sh
└── pyproject.toml
```
