# README Import v0.11.2

Status: Active project baseline after the M7.5 API boundary stabilization patch.

## Import target

Use this repository as the canonical planning/source-of-truth repo for the post-Foundation-Gate API boundary layer.

## Start files

```text
README.md
VERSION.md
AGENTS.md
README_IMPORT_v0_11_2.md
ultimate_ai_agent_master_plan_v0_11_2.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/standards/agents_md_support.md
docs/canonical/09_roadmap.md
docs/canonical/25_cost_and_resource_governor.md
docs/canonical/26_model_routing_strategy.md
docs/canonical/37_tool_broker.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/implementation/foundation_gate_implementation_plan_v0_11_2.md
```

## v0.11.2 change

v0.11.2 stabilizes the M7.5 API boundary. It adds typed `/api/manifest` metadata, deterministic OpenAPI operation IDs, OpenAPI export and verification scripts, AGENTS.md workspace guidance, API boundary docs, CI contract verification, and Foundation Gate checks for API contract hygiene.

The API layer remains metadata, validation, preview, and policy evaluation only. It does not execute models, call providers, fetch web resources, load runtime agent config, run browser automation, or perform production persistence.

## Do not build yet

```text
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
real provider integrations
web fetching
real model calls
real tools / external actions
production memory storage
pgvector or embedding execution
broad local filesystem scanning
real SDK/A2A runtime delegation
browser automation
OAuth flows
production secret vaults
production truth connectors
runtime agent config loading
high-autonomy execution
```
