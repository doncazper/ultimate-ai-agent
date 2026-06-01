# README Import v0.13.2

Status: Active baseline after M9.5 Loopback Runtime Hardening and Approval API Cleanup.

## Import Target

Use this repository as the canonical planning/source-of-truth repo for the local/dev loopback runtime policy harness, simulated fallback behavior, approval-gated runtime authorization boundary, loopback-only endpoint hardening, and local approval validation API contracts.

## Start Files

```text
README.md
VERSION.md
AGENTS.md
README_IMPORT_v0_13_2.md
ultimate_ai_agent_master_plan_v0_13_2.md
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
docs/implementation/foundation_gate_implementation_plan_v0_13_2.md
```

## v0.13.2 Change

v0.13.2 is an M9.5 patch. It rejects `deny_non_loopback=false` and non-loopback `allowed_hosts` in `LoopbackRuntimePolicy`, keeps adapter-level non-loopback denial as defense in depth, adds public/private IP denial coverage, and updates `/approvals/validate` to use a public LocalApprovalAuthority helper instead of private state mutation.

## Still Local/Dev Only

Real local loopback execution is opt-in and library-level only. It requires loopback-only endpoint validation, explicit `allow_real_loopback_execution`, no credentials or secret handles, selected route metadata, validated local approval, and an explicitly injected transport. Tests and Foundation Gate use fake transport and make no real network/model calls.

## Do Not Build Yet

```text
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
