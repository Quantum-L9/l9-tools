# --- L9_META ---
# l9_schema: 1
# origin: l9-tools
# layer: [developer-commands]
# tags: [make, validation]
# owner: platform
# status: active
# --- /L9_META ---

.PHONY: validate test pycompile json examples clean

validate: pycompile json test examples

pycompile:
	python -m compileall -q src tests

json:
	python -m json.tool schemas/coding_contract.schema.json >/dev/null
	python -m json.tool schemas/contract_clause.schema.json >/dev/null
	python -m json.tool schemas/repo_fingerprint.schema.json >/dev/null
	python -m json.tool schemas/agent_behavior_profile.schema.json >/dev/null
	python -m json.tool schemas/retrieval_result.schema.json >/dev/null
	python -m json.tool schemas/compiled_contract_bundle.schema.json >/dev/null

test:
	PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py'

examples:
	PYTHONPATH=src python -m l9_tools.cli compile --repo Quantum-L9/PR_Repair --task examples/task.github-workflow.json --agent codex --debt-intelligence-root examples/debt-intelligence --out-dir out/example
	PYTHONPATH=src python -m l9_tools.cli validate out/example/contract_bundle.json
	PYTHONPATH=src python -m l9_tools.cli explain-risk --repo Quantum-L9/PR_Repair --task examples/task.github-workflow.json --debt-intelligence-root examples/debt-intelligence
	PYTHONPATH=src python -m l9_tools.audit.cli run . --out out/audit-findings.json

clean:
	rm -rf out .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
