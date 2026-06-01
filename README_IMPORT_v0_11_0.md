# README Import v0.11.0

Status: Active project baseline after Milestone M7 (Model Router and Cost/Resource Governor policy foundation).

## Import target

Use this repository as the canonical planning/source-of-truth repo for the post-Foundation-Gate M7 policy layer.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_11_0.md
ultimate_ai_agent_master_plan_v0_11_0.md
docs/canonical/09_roadmap.md
docs/canonical/25_cost_and_resource_governor.md
docs/canonical/26_model_routing_strategy.md
docs/canonical/37_tool_broker.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/50_data_classification_policy.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/57_local_runtime_optimization_profiles.md
docs/implementation/foundation_gate_implementation_plan_v0_11_0.md
```

## v0.11.0 change

v0.11.0 implements M7 as policy/decision infrastructure only. It adds model capability profiles, model routing policies, route requests, deterministic route decisions, privacy enforcement, context-budget compatibility checks, cost/resource budgets, cost estimates, cost decisions, a cost governor, non-executing API validation/preview endpoints, and Foundation Gate checks for the M7 surface.

The router and governor do not execute models, call providers, tokenize content through external APIs, resolve raw credentials, call billing APIs, fetch network resources, or run external tools.

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
