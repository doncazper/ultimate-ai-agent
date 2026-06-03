Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.8.1

Status: Active project baseline after Milestone M4.5 (Truth Source Router + Evidence Governance foundation).

## Import target

Use this repository as the canonical planning/source-of-truth repo for M4.5 coding and validation.

## Start files

```text
README.md
VERSION.md
README_IMPORT_v0_8_1.md
ultimate_ai_agent_master_plan_v0_8_1.md
docs/canonical/03_memory_system.md
docs/canonical/09_roadmap.md
docs/canonical/10_file_management.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/37_tool_broker.md
docs/canonical/40_credentials_secret_broker_and_provider_registry.md
docs/canonical/41_memory_retrieval_v1.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/59_truth_source_governance.md
docs/canonical/60_evidence_manifest.md
docs/canonical/61_source_conflict_resolution.md
docs/canonical/62_freshness_and_staleness_policy.md
docs/implementation/foundation_gate_implementation_plan_v0_8_1.md
```

## v0.8.1 change

v0.8.1 implements M4.5 as deterministic, non-executing foundation infrastructure. Truth sources, grounding policies, claim evidence, evidence manifests, source conflicts, freshness checks, retrieval logs, and route decisions are represented as contracts and validators. The router selects among caller-supplied manifests only; it does not fetch, call providers, invoke models, run embeddings, use a production database, or execute tools.

## Do not build yet

```text
M5 Minimum Lovable Kernel
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
