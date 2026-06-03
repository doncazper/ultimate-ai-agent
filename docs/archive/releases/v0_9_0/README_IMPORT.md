Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.9.0

Status: Active project baseline after Milestone M5 (Minimum Lovable Kernel foundation).

## Import target

Use this repository as the canonical planning/source-of-truth repo for M5 coding and validation.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_9_0.md
ultimate_ai_agent_master_plan_v0_9_0.md
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
docs/implementation/foundation_gate_implementation_plan_v0_9_0.md
```

## v0.9.0 change

v0.9.0 implements M5 as a local/dev kernel slice. A `MinimumKernelRunner` can create, update, dry-run, or roll back a file inside an explicit workspace root after composing the existing Execution Contract, Context Pack, Consent Ledger, Tool Broker, Event Ledger, World State, LocalFileManager, optional MemoryStore, and receipt primitives.

The only real side effect is a LocalFileManager write inside the caller-supplied local/dev workspace root. The kernel never calls models, providers, network APIs, scanners, external tools, browser automation, SDK/A2A runtimes, production databases, pgvector, embeddings, or production secret stores.

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
```
