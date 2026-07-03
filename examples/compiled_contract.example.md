<!-- L9_META
l9_schema: 1
origin: l9-tools
layer: [example]
tags: [compiled-contract]
owner: platform
status: active
/L9_META -->

# Example Compiled Contract

This file is a static example of the expected human-readable contract shape.

## Task

- Repo: `Quantum-L9/PR_Repair`
- Objective: Add dispatch validation for PR repair corpus export.
- Agent: `codex`

## Routing

- Risk: `high`
- CI profile: `security`
- Agent review: `required`
- Human approval: `required`

## MUST

- Inspect relevant repo files before editing.
- Include deterministic artifact fetch coordinates.

## MUST NOT

- Do not auto-merge.
- Do not mutate protected branches.

## VALIDATE

- Validate workflow permissions if workflows are touched.
- Prove no secret values are written to logs or artifacts.

## Remaining Unknowns

- Live external memory availability is Unknown until configured.
