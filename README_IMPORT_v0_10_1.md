# README Import v0.10.1

Status: Active project baseline after M6.1 (Foundation Gate hardening, CI polish, warning cleanup, and release hygiene).

## Import target

Use this repository as the canonical planning/source-of-truth repo for M6 Foundation Gate validation and M6.1 release hygiene.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_10_1.md
ultimate_ai_agent_master_plan_v0_10_1.md
docs/canonical/09_roadmap.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/22_observability_and_event_ledger.md
docs/canonical/35_execution_contract.md
docs/canonical/36_context_pack.md
docs/canonical/37_tool_broker.md
docs/canonical/41_memory_retrieval_v1.md
docs/canonical/43_minimum_lovable_kernel.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/53_structured_world_state.md
docs/canonical/59_truth_grounding_and_evidence_governance.md
docs/implementation/foundation_gate_implementation_plan_v0_10_1.md
```

## v0.10.1 change

v0.10.1 hardens the M6 Foundation Gate baseline without expanding agent capabilities. It reduces project-owned `datetime.utcnow()` deprecation warnings by using timezone-aware UTC timestamps, strengthens verifier summary output, adds gate runner `--output` support, stabilizes Foundation Gate report ordering, adds CI verification, and updates release hygiene documents.

The gate remains verification-only. API routes validate supplied gate reports and shadow-replay scenarios only; they do not run tests, shell commands, replay execution, providers, models, network calls, or external tools.

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
