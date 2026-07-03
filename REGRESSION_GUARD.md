<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [regression-guard]
tags: [validation, no-regression]
owner: platform
status: active
/L9_META -->

# Regression Guard

## Capabilities that must remain true

* CLI can compile a coding contract.
* CLI can validate a compiled contract bundle.
* CLI can explain risk/profile selection.
* MCP server can list tools.
* MCP server can compile a contract.
* MCP server exposes `l9_contract_select_agent`.
* Missing retrieval sources produce explicit Unknown evidence instead of invented facts.
* High-risk workflow/token tasks route to security profile and PR_Repair max attempts of 2.
* Generated contracts include MUST, MUST NOT, VALIDATE, OUTPUT EVIDENCE, and Remaining Unknowns sections.

## No-regression checks

Run:

```bash
./run_validation.sh
```
