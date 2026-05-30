# Ultimate AI Agent Master Plan v0.5.4

Status: Active pre-coding foundation baseline.

## Purpose

The Ultimate AI Agent is a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

v0.5.4 is a Runtime Hygiene Micro-Foundation release. It preserves v0.5.3's Claude remediation and adds small cross-cutting primitives that every later service should share.

## Source-of-truth rule

Canonical files define active truth. Versioned master plans are historical planning records.

```text
1. Current explicit user instruction
2. Active canonical files
3. Active feature spec
4. Accepted ADRs
5. Project memory
6. Historical master plans
7. Conversation history
```

The active roadmap is `docs/canonical/09_roadmap.md`. This master plan intentionally does not duplicate milestone definitions.

## v0.5.3 foundation retained

v0.5.3 already added:

```text
Verified Task Completion Framework
Durable execution ADR: custom event ledger + deterministic state machine first
Event-level cost attribution
Secret Broker + Provider Registry
Memory Retrieval V1
Autonomy Levels L0-L5
Minimum Lovable Kernel
Provisional Contract Policy
Trusted Computing Base
```

## v0.5.4 additions

v0.5.4 adds:

| Addition | Why it matters |
|---|---|
| Result and Error Envelope | Makes service responses consistent and debuggable. |
| Idempotency and Retry Policy | Prevents duplicate side effects when runs/tools are retried. |
| Actor/Authority Context | Records who or what initiated every meaningful operation. |
| Temporal Context and Freshness | Makes news, weather, memory, scanners, and reminders time-aware. |
| Data Classification Policy | Gives privacy, redaction, model routing, and logging a shared vocabulary. |
| Redaction and Safe Debugging | Prevents secrets/private data from leaking into prompts, logs, receipts, or debug bundles. |
| Service Boundaries and Dependency Injection | Protects the onion architecture from brittle internal coupling. |
| Capability Flags | Makes foundation-first blocking enforceable in code, not just docs. |
| Test Strategy v0 | Gives Codex/Hermes/agents consistent test categories and naming. |

## Runtime hygiene primitives

Every meaningful operation should carry or produce:

```text
result envelope
error envelope when applicable
actor context
temporal context
data classification
redaction metadata
idempotency key for mutable/retryable actions
trace_id / run_id / step_id / correlation_id
cost attribution when any model/tool/provider is used
rollback reference for mutable actions
```

## Foundation kernel

The Foundation Gate requires the following primitives before advanced modules:

```text
Execution Contract
Context Pack
Verified Task Completion contracts
Result/Error envelopes
Idempotency and retry policy
Actor/Authority context
Temporal/Freshness context
Data classification and redaction
Event Ledger and deterministic run state machine
Consent Ledger
Tool Broker
Secret Broker
Provider Registry
Model Router
Cost Governor
Memory Service and retrieval stack
File Manager
Rollback primitives
API boundary
Capability flags
Contract tests and shadow replay
Trusted Computing Base
```

## Advanced modules remain blocked

Do not build the following until the Foundation Gate passes:

```text
Reddit Scanner
News Scanner
Weather Module beyond safe provider-normalization prototype
Email Scanner
Message Scanner
Calendar Scanner
Companion proactivity
Skill Factory
Self-improving coding framework
Autopilot workflows
External high-autonomy execution
Provider-specific integrations that require credentials
```

## Implementation posture

Start with M0. Build validation scripts, stack skeleton, and runtime hygiene schemas. Preserve contracts as provisional until at least the Minimum Lovable Kernel exercises them. Do not add broad architecture modules after v0.5.4 unless a real M0/M1 implementation failure proves a gap.
