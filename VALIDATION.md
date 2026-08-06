<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [validation]
tags: [quality, gates]
owner: platform
status: active
/L9_META -->

# Validation

Run from repo root:

```bash
./run_validation.sh
```

Equivalent expanded commands:

```bash
python -m compileall -q src tests
python -m json.tool schemas/coding_contract.schema.json >/dev/null
python -m json.tool schemas/contract_clause.schema.json >/dev/null
python -m json.tool schemas/repo_fingerprint.schema.json >/dev/null
python -m json.tool schemas/agent_behavior_profile.schema.json >/dev/null
python -m json.tool schemas/retrieval_result.schema.json >/dev/null
python -m json.tool schemas/compiled_contract_bundle.schema.json >/dev/null
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'
PYTHONPATH=src python -m l9_tools.cli compile --repo Quantum-L9/PR_Repair --task examples/task.github-workflow.json --agent codex --debt-intelligence-root examples/debt-intelligence --out-dir out/example
PYTHONPATH=src python -m l9_tools.cli validate out/example/contract_bundle.json
PYTHONPATH=src python -m l9_tools.cli select-agent --agent codex
PYTHONPATH=src python -m l9_tools.audit.cli run . --out out/audit-findings.json
```

The audit engine is deterministic and read-only: two runs over the same repo
state produce a byte-identical findings envelope, and `--fail-on` returns a
non-zero exit code only when findings meet the threshold.

No validation pass is claimed until these commands are run in the target environment.
