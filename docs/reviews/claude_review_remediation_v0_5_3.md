# Ultimate AI Agent — Claude v0.4.1 Review Remediation Plan v0.5.3

Status: Proposed patch set before deeper programming
Date: 2026-05-29

## Purpose

Claude's v0.4.1 review correctly identified several foundation issues. Versions v0.4.5 through v0.5.2 addressed some of them, especially model routing, execution contracts, context packs, event ledger, consent/tool broker, memory/file manager, stack strategy, prompts, and import readiness. However, several issues remain open or only partially addressed.

This plan defines the v0.5.3 remediation patch before moving beyond M0/M1 implementation.

## Summary

| ID | Status after v0.5.2 | v0.5.3 action |
|---|---|---|
| A1 Verified Task Completion not operationalized | Partially addressed via acceptance criteria, but no task-class verification contract | Add `docs/canonical/39_verified_task_completion_framework.md`, `verification_contract.schema.json`, and `verified_task_completion_eval.md` |
| A2 Durable-execution substrate undecided | Not addressed | Add ADR for build-vs-adopt: start with custom append-only event ledger + deterministic state machine; keep Temporal/LangGraph as later adapters |
| A3 Cost attribution only run-level | Mostly addressed with event-level cost fields, but attribution object needs strengthening | Add `cost_attribution` object to event schema with run/tool/scanner/skill/model/project dimensions |
| A4 Secret storage unspecified | Not addressed; discussed after v0.5.2 | Add Secret Broker + Provider Registry docs, schemas, ADR; no secrets in chat/memory/logs |
| A5 Memory retrieval/vector design underspecified | Partially addressed as optional pgvector; not enough | Add Memory Retrieval V1 spec: pgvector + full-text + reranking + chunking + poisoning controls |
| A6 Autonomy tiers referenced but undefined | Partially addressed by fields, not level semantics | Add autonomy-level definitions 0-5, risk mapping, standing approvals for low-risk recurring actions |
| A7 First vertical slice too text-only | Not addressed | Replace first slice with Minimum Lovable Kernel: real File Manager mutation + Event Ledger + Tool Broker + rollback + verification receipt; optional no-key provider read |
| A8 Contract-freezing too early | Not addressed | Mark M1 contracts `v0/provisional`; allow one breaking revision after first MLK slice; enforce strict compat only post Foundation Gate |
| A9 Self-improvement TCB not explicit | Not addressed | Add Trusted Computing Base doc: constitution, consent logic, tool broker policy, event ledger, secret broker, model routing policy, rollback policy are non-autonomous-modifiable |
| A10 Scope vs builder capacity | Partially addressed by foundation-first gating | Add Minimum Lovable Kernel smaller than M0-M6 and make it the first proof target |
| B1 Contradictory roadmaps | Partially addressed in canonical roadmap, but master plan still contains stale roadmap sections | Remove duplicate roadmap bodies from master plan; replace with pointer to `docs/canonical/09_roadmap.md` |
| B2 Empty template canonical docs | Partially addressed for several foundation docs; many still have TBD | Mark non-foundation templates as backlog or fill foundation-critical docs before coding |

## v0.5.3 deliverables

### 1. Verified Task Completion Framework

Files:
- `docs/canonical/39_verified_task_completion_framework.md`
- `docs/schemas/verification_contract.schema.json`
- `docs/schemas/verification_evidence.schema.json`
- `docs/evals/verified_task_completion_eval.md`

Task classes:
- answer
- research
- file mutation
- memory mutation
- code generation
- code execution
- provider read
- external action
- notification
- scanner output
- self-improvement patch

Each class defines:
- required acceptance criteria
- required evidence
- allowed verifier
- what counts as verified
- what counts as failed or unverifiable

### 2. Durable Execution ADR

Files:
- `docs/decisions/ADR-0040-use-custom-event-ledger-state-machine-first.md`
- update `docs/canonical/22_observability_and_event_ledger.md`

Decision:
- Use custom append-only event ledger + deterministic state machine for MVP.
- Store run state as derived from events.
- Keep Temporal/LangGraph adapters as future options after contracts stabilize.

### 3. Cost Attribution Upgrade

Files:
- update `docs/schemas/event_ledger_event.schema.json`
- update `docs/canonical/25_cost_and_resource_governor.md`

Add event-level `cost_attribution`:

```json
{
  "run_id": "run_123",
  "project_id": "project_123",
  "tool_id": "weather.open_meteo.forecast",
  "provider_id": "open_meteo",
  "scanner_id": null,
  "skill_id": null,
  "model_class": "fast_classifier",
  "actual_model": "provider/model",
  "estimated_cost_usd": 0,
  "actual_cost_usd": 0,
  "billable_units": {"tokens_in": 0, "tokens_out": 0, "api_calls": 1}
}
```

### 4. Secret Broker + Provider Registry

Files:
- `docs/canonical/40_credentials_secret_broker_and_provider_registry.md`
- `docs/decisions/ADR-0041-use-secret-broker-and-provider-registry.md`
- `docs/schemas/provider_manifest.schema.json`
- `docs/schemas/credential_reference.schema.json`
- `docs/schemas/provider_result_envelope.schema.json`
- `docs/schemas/weather_normalized.schema.json`
- `docs/schemas/news_normalized.schema.json`
- `docs/evals/secret_redaction_eval.md`
- `docs/evals/provider_normalization_eval.md`

Principles:
- Use free/no-key providers first.
- Do not ask users to paste API keys into chat.
- Local dev uses `.env.local` or OS keychain; production uses vault/secret store.
- LLM never sees raw secrets.
- Provider outputs normalize before agent use.

### 5. Memory Retrieval V1

Files:
- update `docs/canonical/03_memory_system.md`
- add `docs/canonical/41_memory_retrieval_v1.md`
- add `docs/evals/memory_retrieval_precision_eval.md`

Decision:
- Postgres as source of truth.
- pgvector for semantic retrieval.
- Postgres full-text search for lexical retrieval.
- Hybrid retrieval + reranking.
- Source-linked memory records.
- Retrieval poisoning controls.

### 6. Autonomy Levels and Approval Fatigue Controls

Files:
- `docs/canonical/42_autonomy_levels_and_standing_approvals.md`
- `docs/schemas/autonomy_policy.schema.json`
- update Consent Ledger and Tool Broker docs

Levels:
- L0 answer only
- L1 draft only
- L2 recommend
- L3 prepare and ask approval
- L4 execute reversible trusted actions
- L5 execute approved recurring workflows

Add standing approvals only for low-risk recurring actions, with expiration, scope, max frequency, audit, and revocation.

### 7. Minimum Lovable Kernel Vertical Slice

Files:
- `docs/canonical/43_minimum_lovable_kernel.md`
- update roadmap and Foundation Gate plan

MLK goal:
Prove one real end-to-end task with real side effects before building advanced systems.

Recommended first task:
- User asks agent to create a local project note/spec artifact.
- Execution Contract created.
- Context Pack created.
- Consent checked.
- Tool Broker calls File Manager.
- File is written to project workspace.
- Event Ledger logs action with cost attribution.
- Rollback plan generated.
- QA verifies file exists and receipt is valid.
- Memory writes source-linked summary.
- User receives receipt.

Optional second read-only provider task:
- Fetch weather from Open-Meteo with no key.
- Normalize response.
- Log provider result envelope.

### 8. Contract Provisional Policy

Files:
- `docs/canonical/44_contract_versioning_and_provisional_policy.md`
- update Execution Contract, Context Pack, Event Ledger schemas

Rules:
- M1 contracts are `v0/provisional`.
- One breaking revision allowed after first MLK slice.
- Strict backward compatibility only after Foundation Gate.
- Post-gate changes require migration plan + contract tests + shadow replay.

### 9. Trusted Computing Base

Files:
- `docs/canonical/45_trusted_computing_base.md`
- `docs/decisions/ADR-0042-designate-trusted-computing-base.md`

TCB includes:
- Agent Constitution
- Consent Ledger enforcement
- Tool Broker risk classifier
- Event Ledger append-only write path
- Secret Broker
- Model Router policy
- Cost Governor hard limits
- Rollback policy
- Approval rules
- Prompt-injection boundary rules

Self-improvement cannot autonomously modify TCB files or logic. TCB changes require human-authored issue, human approval, tests, and manual merge.

### 10. Roadmap Cleanup

Files:
- update master plan
- update README

Rules:
- `docs/canonical/09_roadmap.md` is the only roadmap source of truth.
- Master plan links to the roadmap instead of duplicating milestone definitions.
- Remove stale v0.3/v0.4 milestone sections.

### 11. Template Doc Cleanup

Files:
- fill foundation-critical docs:
  - `23_security_threat_model.md`
  - `24_data_lifecycle_and_privacy.md`
  - `25_cost_and_resource_governor.md`
  - `28_rollback_and_recovery.md`
  - `30_agent_constitution.md`
  - `33_shadow_mode_simulation_and_digital_twin_testing.md`
- mark non-foundation docs as `Status: Draft / Backlog; not implementation-authoritative yet`.

## Build decision

Do not expand advanced modules until v0.5.3 remediation is committed.

After v0.5.3:
- M0 can continue.
- M1 can implement provisional contracts.
- MLK becomes the first end-to-end proof target.
