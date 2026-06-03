Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.12.2

Status: Active baseline after M8.5 Approval Authority + Runtime Authorization Bridge.

## Import Target

Use this repository as the canonical planning/source-of-truth repo for the local/dev approval authority bridge, simulated model runtime boundary, and sanitized API validation behavior.

## Start Files

```text
README.md
VERSION.md
AGENTS.md
README_IMPORT_v0_12_2.md
ultimate_ai_agent_master_plan_v0_12_2.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/security/approval_authority.md
docs/runtime/model_runtime_adapter_harness.md
docs/canonical/09_roadmap.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/48_actor_authority_and_identity.md
docs/canonical/52_service_boundaries_and_dependency_injection.md
docs/implementation/foundation_gate_implementation_plan_v0_12_2.md
```

## v0.12.2 Change

v0.12.2 implements M8.5. It adds typed local/dev approval requests, grants, validation decisions, and receipts; a local in-memory `LocalApprovalAuthority`; and approval validation integration for Model Router, Model Runtime request creation, Tool Broker policy checks, and Kernel local/dev mutation paths.

## Still Local/Dev Only

`approval_test_` remains compatibility/test-only and is not real authority. Production approval will require future user auth, sessions, UI, durable storage, and revocation workflows.

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
production auth or OAuth
real SDK/A2A runtime delegation
production secret vaults
production truth connectors
high-autonomy execution
```
