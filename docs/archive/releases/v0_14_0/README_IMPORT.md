Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.14.0

Status: Active baseline after M10 Manual Local Loopback Smoke Transport + Runtime Readiness Harness.

## Import Target

Use this repository as the canonical planning/source-of-truth repo for the local/dev loopback runtime policy harness, simulated fallback behavior, approval-gated runtime authorization boundary, loopback-only endpoint hardening, local approval validation API contracts, and manual local loopback smoke readiness checks.

## Start Files

```text
README.md
VERSION.md
AGENTS.md
README_IMPORT_v0_14_0.md
ultimate_ai_agent_master_plan_v0_14_0.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/security/approval_authority.md
docs/canonical/09_roadmap.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/48_actor_authority_and_identity.md
docs/canonical/52_service_boundaries_and_dependency_injection.md
docs/implementation/foundation_gate_implementation_plan_v0_14_0.md
```

## v0.14.0 Change

v0.14.0 implements M10. It adds a manual-only, disabled-by-default, approval-gated, loopback-only smoke transport and CLI script for local runtime readiness checks. The smoke path uses a fixed non-sensitive prompt only and must not process user prompts, memory, files, context packs, secrets, or task content.

## Still Not General Runtime Execution

The public API exposes smoke validation only. The real stdlib HTTP smoke transport is isolated to `src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py` and the manual CLI script. Tests and Foundation Gate use fake transport only.

## Do Not Build Yet

```text
general agent model execution
cloud model calls
provider SDK calls
remote OpenAI-compatible calls
API keys
secret reads
tokenizer integrations
billing API code
remote hosts
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
browser automation
production persistence
production auth or OAuth
real SDK/A2A runtime delegation
production truth connectors
high-autonomy execution
```
