<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [integration-doc]
tags: [pr-repair, repair-contract]
owner: platform
status: active
/L9_META -->

# PR_Repair Integration

PR_Repair can call `l9-tools` before patching to compile a bounded repair contract.

The repair contract should include:

* source failure payload
* matching repair playbooks
* max attempts
* blocked paths
* validation gates
* human escalation conditions

PR_Repair remains the patch worker. `l9-tools` remains the contract compiler.
