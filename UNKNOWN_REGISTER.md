<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [unknown-register]
tags: [unknowns, validation]
owner: platform
status: active
/L9_META -->

# Unknown Register

## Known Unknowns

| ID    | Unknown                                                                    | Impact                                      | Handling                                |
| ----- | -------------------------------------------------------------------------- | ------------------------------------------- | --------------------------------------- |
| U-001 | Live Graphiti MCP endpoint availability                                    | Episodic retrieval may be unavailable       | Adapter emits explicit Unknown evidence |
| U-002 | Live code-graph endpoint availability                                      | Structural retrieval may be unavailable     | Adapter emits explicit Unknown evidence |
| U-003 | Actual external l9-ci-debt-intelligence repo path in consuming environment | Health-library retrieval may be unavailable | CLI accepts explicit root path          |
| U-004 | Hosted HTTP API requirements                                               | Not required for initial milestone          | Deferred until MCP and CLI prove useful |

No credentials, services, or external facts are invented.
