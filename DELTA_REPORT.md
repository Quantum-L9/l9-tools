<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [delta-report]
tags: [before-after]
owner: platform
status: active
/L9_META -->

# Delta Report

## Before

The prior transmitted pack was not safe to execute because it contained rich-text formatting and missing required files.

## After

Pack v2 is ASCII-only and adds the missing original-spec and validation-governance artifacts.

## Added items

* `src/l9_tools/contracts/schemas.py`
* `src/l9_tools/retrieval/ranking.py`
* `l9_contract_select_agent`
* Additional examples and tests
* Required governance artifacts

## Preserved items

* Node-neutral l9-tools boundary
* CLI
* MCP
* Routing
* Retrieval adapters
* Debt-intelligence sample data

## Rejected changes

* HTTP API in initial milestone
* Live network requirements in tests
* Cursor-Governance compiler ownership
