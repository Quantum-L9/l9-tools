<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [integration-doc]
tags: [openclaw, orchestration]
owner: platform
status: active
/L9_META -->

# OpenClaw Integration

OpenClaw should request a contract before dispatching coding work.

```text
OpenClaw planning event
  -> l9_contract_compile
  -> selected risk/profile/agent/repair policy
  -> dispatch contract to coding agent
  -> observe CI/review/repair outcome
  -> emit outcome to debt intelligence
```

OpenClaw owns orchestration. `l9-tools` owns compilation.
