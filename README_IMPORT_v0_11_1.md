# README Import v0.11.1

Status: Active project baseline after the M7 policy-correctness patch.

## Import target

Use this repository as the canonical planning/source-of-truth repo for the post-Foundation-Gate M7 policy layer.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_11_1.md
ultimate_ai_agent_master_plan_v0_11_1.md
docs/canonical/09_roadmap.md
docs/canonical/25_cost_and_resource_governor.md
docs/canonical/26_model_routing_strategy.md
docs/canonical/37_tool_broker.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/50_data_classification_policy.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/57_local_runtime_optimization_profiles.md
docs/implementation/foundation_gate_implementation_plan_v0_11_1.md
```

## v0.11.1 change

v0.11.1 hardens M7 policy correctness. Arbitrary approval refs no longer satisfy sensitive cloud approval, context budget available-history checks are enforced, soft budget overages allow with warning instead of denying, and Foundation Gate now covers these M7 policy semantics.

The router and governor remain policy/decision infrastructure only. They do not execute models, call providers, tokenize content through external APIs, resolve raw credentials, call billing APIs, fetch network resources, or run external tools.

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
high-autonomy execution
```
