Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.12.1

Status: Active patch baseline after M8 API validation redaction hardening.

## Import Target

Use this repository as the canonical planning/source-of-truth repo for the simulated model runtime boundary and its sanitized API validation behavior.

## Start Files

```text
README.md
VERSION.md
AGENTS.md
README_IMPORT_v0_12_1.md
ultimate_ai_agent_master_plan_v0_12_1.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/runtime/model_runtime_adapter_harness.md
docs/canonical/09_roadmap.md
docs/canonical/25_cost_and_resource_governor.md
docs/canonical/26_model_routing_strategy.md
docs/canonical/38_scalable_stack_and_ui_strategy.md
docs/canonical/52_service_boundaries_and_dependency_injection.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md
docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md
docs/implementation/foundation_gate_implementation_plan_v0_12_1.md
```

## v0.12.1 Change

v0.12.1 hardens M8 API validation redaction. FastAPI/Pydantic validation errors no longer echo raw invalid input values, secret-like values, or sensitive validation field names. Model runtime manifest, request-validation, response-validation, and simulate payload failures return sanitized errors.

## Do Not Build Yet

```text
real model calls
provider SDK calls
OpenAI-compatible endpoint calls
local runtime calls
tokenizer integrations
billing API code
network calls
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
browser automation
production persistence
real SDK/A2A runtime delegation
production secret vaults
production truth connectors
high-autonomy execution
```
