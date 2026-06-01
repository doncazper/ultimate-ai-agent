# 09 — Roadmap v0.5.7

Status: Active foundation-first roadmap. This is the single roadmap source of truth.

## North Star

Build a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

## Stack baseline

```text
Python/FastAPI/Pydantic Agent Core
TypeScript Control Center later
OpenWebUI optional early chat shell
Postgres canonical database
Docker Compose local development
Stable Agent API Boundary
```

OpenWebUI is a window into the agent, not the agent brain.

## Current phase

Pre-coding foundation remediation, Runtime Hygiene Micro-Foundation, Local Runtime/Context Survival, Truth/Grounding/Evidence Governance, Observability Standards Mapping, and Minimum Lovable Kernel preparation.

## Accepted baseline through v0.16.0

The active accepted baseline is v0.16.0. It includes foundation modules through M10.5 plus documentation integrity synchronization, Codex plugin/external tooling governance, M11 runtime readiness/report validation, and M12 Control Center backend contract/API foundation. v0.16.0 adds read-only/preview-only Control Center contracts only; it does not add frontend UI or execution capability.

Recent accepted milestones:

```text
v0.14.0 — M10 manual local loopback smoke harness, manual-only and fixed-prompt-only
v0.14.1 — M10.5 remote worker foundation and planned tailnet transport metadata
v0.14.2 — M10.5 policy hardening for loopback/runtime and approval validation
v0.14.3 — open-source-first private mesh taxonomy with planned Headscale/generic WireGuard/Tailscale metadata
v0.14.4 — Mobile Companion and Device Capability Broker roadmap planning only
v0.14.5 — documentation integrity, canonical map, docs index, and documentation verifier
v0.14.6 — Codex plugin and external build tool governance inventory, docs/policy only
v0.15.0 — M11 runtime readiness gate, capability matrix, and manual smoke report validation
v0.15.1 — M11 runtime readiness taxonomy clarification for local loopback policy and fake smoke origins
v0.16.0 — M12 Control Center contract and read-only dashboard API foundation
```

## Minimum Lovable Kernel

Before committing to the full foundation build, prove one genuine end-to-end task:

```text
Create a local project artifact through the agent kernel.
Use Execution Contract + Context Pack.
Use Result/Error Envelope.
Use ActorContext and TemporalContext.
Use Data Classification and Redaction policy.
Use idempotency metadata for the file mutation.
Check Consent Ledger.
Route File Manager through Tool Broker.
Write an actual file.
Log event-level cost attribution.
Create rollback metadata.
Verify the artifact and receipt.
Write source-linked memory.
```

## Now: Foundation Gate sequence

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M0.5 — Runtime Hygiene Primitives: Result/Error, Idempotency, Actor, Time, Classification, Redaction, Boundaries
M1 — Kernel Contracts: Execution Contract + Context Pack, v0/provisional
M2 — Event Ledger, Deterministic Run State, Receipts, and Observability Standards Mapping
M2.5 — World State, Context Budget, Local Runtime, and SDK Adapter Boundaries
M3 — Consent Ledger + Tool Broker
M3.5 — Secret Broker + Provider Registry + Normalized Provider Envelopes
M4 — Memory Service + File Manager
M4.5 — Truth Source Router and Evidence Governance
M5 — Minimum Lovable Kernel Vertical Slice
M6 — Contract Tests, Shadow Replay, Foundation Gate Decision
```

## M0 acceptance

```text
Repo layout exists.
Python Agent Core skeleton exists.
JSON/schema validation command exists.
Prompt registry validation command exists.
FastAPI health/API boundary placeholder exists.
Docker Compose Postgres scaffold exists.
OpenWebUI config is present only as optional shell.
Foundation-first rule is visible.
No advanced modules are implemented.
```

## M0.5 acceptance

```text
ResultEnvelope and ErrorEnvelope schemas validate.
Idempotency/retry policy schema validates.
ActorContext schema validates.
TemporalContext schema validates.
Data classification schema validates.
Redaction policy schema validates.
Capability flag schema validates.
Service boundary rules are documented.
Test strategy v0 is documented.
```

## M1 acceptance

```text
Execution Contract and Context Pack schemas/models validate.
Contracts are marked v0/provisional.
Advanced modules are rejected until Foundation Gate.
Verification contract references are supported.
Runtime hygiene primitives are referenced by contracts.
```

## M2 acceptance

```text
Run/event records support append-only logging.
Event-level cost attribution exists.
Events include trace/correlation/actor/temporal/classification metadata.
Receipts can be generated without secrets.
Custom deterministic state machine is documented as initial durable-execution substrate.
Event Ledger records are mappable to OpenTelemetry GenAI spans/events/metrics without changing internal ledger semantics.
W3C Trace Context is documented as the trace propagation standard, and trace-compatible IDs can propagate across API, worker, model-router, Tool Broker, provider, MCP, SDK, and A2A boundaries.
CloudEvents export and AsyncAPI documentation are planned as future compatibility layers for event streams, not M2 implementation blockers.
Redaction policy applies before any telemetry export.
```

## M2.5 acceptance

```text
Structured World State schemas validate.
Context Budget Manager schemas validate.
Context-limit discovery policy is documented.
Token accounting and calibration schemas validate.
Tool-result retention/trimming policy is documented.
Prompt/tool bundle cache policy is documented.
Local runtime manifests and health profiles validate.
Privacy routing policy validates.
Agent SDK and A2A adapters are documented as boundary adapters only.
Long-running session survival eval is specified.
```

## M3 acceptance

```text
Consent grants can be created, checked, expired, revoked, and audited.
Tool calls are schema-validated, consent-checked, risk-classified, logged, and rollback-aware.
Autonomy levels L0-L5 map to risk and approval requirements.
Mutable tool calls require idempotency metadata.
```

## M3.5 acceptance

```text
Secrets are referenced by ID, not value.
Secret Broker interface exists.
Provider Registry manifests validate.
Provider result envelopes normalize weather/news/provider responses.
No secret can enter chat, prompts, memory, logs, canonical files, or git.
```

## M4 acceptance

```text
Memory writes are source-linked, scoped, supersedable, and retrieval-aware.
Memory Retrieval V1 uses Postgres + pgvector + full-text + reranking design.
File writes use diffs/atomic operations and produce rollback metadata.
Canonical files outrank memory.
```

## M4.5 acceptance

```text
Truth Source Router schemas validate.
GroundingPolicy schema validates.
EvidenceManifest and ClaimEvidence schemas validate.
SourceConflictReport schema validates.
RetrievalLog schema validates.
Hybrid retrieval and reranking policy is documented.
Truth-governance eval specs exist.
```

## M5 acceptance

```text
Minimum Lovable Kernel completes successfully.
One real file mutation is performed through Tool Broker and File Manager.
Event Ledger, rollback, QA receipt, and source-linked memory all work.
Runtime hygiene metadata, World State/Context Budget metadata, and Evidence Manifest references are present in the trace.
```

## M6 acceptance

```text
Contract tests pass.
Shadow replay can replay the Minimum Lovable Kernel trace.
OpenWebUI/API boundary bypass tests pass.
Foundation Gate review decides whether controlled expansion can begin.
```

## Controlled expansion after gate

Only after M6 passes:

```text
M7 — Web Research V1 and Source Credibility with Evidence Manifests
M8 — Code Workspace V1 with sandboxed execution
M9 — Weather Provider V1 using free/no-key provider first
M10 — News Provider V1 with normalized events/articles
M11 — Basic Scanner Framework, read-only/digest-only
M12 — Proactive Intelligence V1, digest-first, no interrupt alerts until tuned
```

## Future control surfaces and device capabilities

These items come after runtime readiness, API/control-center contract stabilization, and web Control Center foundation. They are planning entries only in v0.14.4.

```text
Mobile Companion Contract
Device Capability Broker
Mobile Device Registry
Mobile Sensor Permission Manifest
Mobile Approval/Receipt Surface
Mobile Capture Inbox
Camera/OCR Evidence Flow
Location Privacy Flow
Push-to-Talk Voice Capture
Emergency Stop / Kill Switch
```

Mobile is a future control, approval, capture, receipt, and status surface. It is not the agent brain. Device Capability Broker work must exist before any mobile sensor integration.

## Future Codex/plugin governance

v0.14.6 adds planning and policy docs for Codex plugins and external build tools. It does not enable any plugin or external runtime.

```text
Browser + Build Web Apps — future Web Control Center work only, with approval
Build iOS Apps / XcodeBuildMCP — disabled until Mobile Companion implementation milestone
Build macOS Apps — disabled until Desktop/macOS Companion milestone
Chrome authenticated profile control — disabled unless explicitly approved
Computer Use — disabled except explicit last-resort manual QA approval
CodeRabbit/GitHub read-only — allowed for release readiness with explicit review prompt
GitHub write/release — explicit approval or direct-push rules required
Hugging Face Jobs/uploads/training — disabled
Plugin/skill installers — disabled until Skill lifecycle security exists
```

No plugin enablement should occur during M11 unless a future prompt explicitly changes the tool boundary.

## Future milestone sequence notes

```text
M11 — Runtime Foundation Readiness Gate + Manual Smoke Report Validation
Future Web Control Center — after runtime/API readiness
Future Mobile Companion — after Control Center/mobile contracts
Future real local model execution — after readiness, approval, and gate criteria
Future remote worker/tailnet execution — after planned/disabled foundation and private mesh taxonomy mature
Future scanners/proactivity/Skill Factory/self-improvement — only after their security lifecycle exists
```

Do not treat runtime readiness, UI implementation, mobile implementation, private mesh execution, scanners, Skill Factory, or self-improvement as accepted until a reviewed milestone implements and gates them.

## Out-of-sequence parked work

Any parked local Control Center work must be reintroduced through a future reviewed milestone. Parked work is not accepted baseline merely because a local branch or local tag exists.

## Later

```text
Companion proactivity
Skill Factory
Self-improving coding framework
High-autonomy external execution
Autopilot workflows
Agent interoperability
Voice/mobile UX
```

## Non-negotiable sequencing rule

Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or high-autonomy external execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, observability standards mapping, Truth Source Router, Evidence Manifest, API boundary, and contract tests work.
