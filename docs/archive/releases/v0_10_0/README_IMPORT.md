Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.10.0

Status: Active project baseline after Milestone M6 (Contract Tests, Shadow Replay, and Foundation Gate evaluation).

## Import target

Use this repository as the canonical planning/source-of-truth repo for M6 validation and audit work.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_10_0.md
ultimate_ai_agent_master_plan_v0_10_0.md
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
docs/implementation/foundation_gate_implementation_plan_v0_10_0.md
```

## v0.10.0 change

v0.10.0 implements M6 as a verification/replay/audit baseline. It adds typed Foundation Gate criteria, results, and reports; static gate evaluators; M5 shadow replay with ordered event capture, receipt verification, memory source refs, world-state event refs, and rollback verification; cross-contract compatibility tests; validation-only API routes; a local gate runner; and sample gate reports.

The gate does not execute shell commands from runtime source or API routes. The runner script is local developer verification only.

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
