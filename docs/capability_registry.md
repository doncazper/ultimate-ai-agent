# Capability Registry And Coordinator

The capability registry is an additive, contract-first layer for coordinating tools, local agents, deterministic workflows, reviewer steps, and future adapter families. It does not add backend routes, production authority, provider calls, network access, shell execution, browser automation, plugin execution, memory writes, context injection, or new dependencies.

The existing `CapabilitySpec` registry remains available for decorator-style Python capabilities. The new `CapabilityManifest` lane adds typed manifests, compact catalog disclosure, structured task envelopes, policy checks, telemetry hooks, bounded in-process adapters, durable local coordinator state, exact approval validation, timeout/retry enforcement, adapter health checks, output-schema checks, single-writer locking, and agent-runtime compatibility metadata. Concrete live file/model/provider adapters remain outside this registry boundary unless a reviewed capability manifest and adapter are registered.

## Architecture

- `CapabilityRegistry` stores two compatible lanes:
  - Existing `CapabilitySpec` registrations for current framework callers.
  - New `CapabilityManifest` registrations with explicit adapters.
- `Coordinator` owns planning, routing, policy checks, state, and final synthesis.
- Specialists run as bounded agents-as-tools through `ToolAdapter`, `AgentAdapter`, `WorkflowAdapter`, `ReviewerAdapter`, `HandoffAdapter`, or `HumanGateAdapter`.
- `PolicyEngine` gates selection, execution, approval requirements, read-only fan-out, and single-writer behavior.
- `TaskEnvelope`, `TaskPlan`, `TaskNode`, and `Artifact` carry structured data instead of freeform inter-agent chat.
- `CapabilityManifest` is the single registry language for tools, agents, workflows, reviewers, human gates, and future runtime adapters.
- Agent-runtime compatibility fields describe authority, approval, determinism, rollback, receipts, evidence, privacy, latency, cost, memory writes, context injection, provider runtime, browser runtime, and connector writes without granting those authorities.
- `TelemetrySink` receives selection, execution, latency, success/failure, estimated cost, and policy denial events.
- `FileCoordinatorStateStore` or `InMemoryCoordinatorStateStore` records plans, run status, audit events, telemetry events, and artifacts.
- `LocalApprovalAuthority` validates exact approval grants for high-risk or explicit-approval capabilities.
- `SingleWriterLockManager` and `FileSingleWriterLockManager` serialize mutating nodes through a single writer lease.

## Capability Availability Truth Model

`ultimate_ai_agent.core.capability_availability` is an additive normalization
layer over the existing capability, provider, runtime-readiness, and extension
contracts. It is not another registry and does not replace their domain models.
The four truth layers remain structurally separate:

```text
CapabilityManifest
    -> stable declaration

CapabilityAvailabilitySnapshot
    -> observed environment readiness

CapabilityInvocationDecision
    -> one exact request authority evaluation

ExecutionReceipt (lane-specific)
    -> actual outcome evidence
```

The legacy `ExecutionReceiptPlan` remains a no-effect planning receipt and does
not prove that execution occurred. Only a lane-specific post-attempt execution
receipt may satisfy the outcome-evidence layer.

The snapshot records typed catalog, compatibility, configuration, health,
resource/budget, safe-disable, freshness, and derived runtime-readiness states.
Its pure derivation function evaluates environment readiness only. Unknown or
stale compatibility and health fail closed, degraded health stays unavailable,
unknown metered budgets block use, and active safe-disable posture overrides
every otherwise-positive input.

The snapshot has no global authorization or callable flag. A runtime-ready row
means only that one exact request may proceed to immediate policy evaluation.
The separate invocation decision consumes the existing `PolicyEngine`
decision, exact `AuthorityLease` decision, exact `LocalApprovalAuthority`
result when required, `CostDecision`, safe-disable state, and idempotency
posture. Approval refs remain identifiers, the decision is not cacheable, and a
separate redacted execution receipt remains required after any attempt.

Narrow adapters normalize `CapabilityManifest`, `CapabilityCatalogEntry`,
`ProviderManifest`, existing provider-readiness posture, and inspectable
extension entries. Missing source evidence remains unknown or blocked; adapter
mapping never invents configuration, compatibility, health, budget, or
authority. The protected read-only API route
`GET /control-center/capabilities/availability` and repo-local
`uaa_runtime.py capability-availability` command render the same backend-owned
read model. No live probe, provider call, network access, background polling,
or runtime execution is added.

The extension catalog now projects every declared extension capability through
this same availability contract. Reviewed repository metadata uses pinned,
bounded, no-follow SHA-256 observations; unknown versions, provenance, hash
state, configuration, health, budget, or safe-disable posture remain unknown or
blocked. `GET /extensions/catalog`, the human-readable `inspect-catalog` CLI,
and the macOS-first Plugin Governance panel expose deterministic developer
validation and rollback/safe-disable refs. Catalog and activation metadata
explicitly grant no invocation authority. Client-supplied approval-grant
payloads are rejected by the disabled-install mutation surface.

## Communications Contracts And Matrix Runtime Truth

`ultimate_ai_agent.core.communications` is the normalized communications
contract boundary for MSG-MX-003. It reuses `CapabilityAvailabilitySnapshot`
for environment truth and adds an immutable provider-adapter declaration
registry, deterministic injected `CommunicationsService`, safe-ref projections,
bounded pagination, room AI policy, proposal-only action envelopes, and
content-free receipts. It is not a competing capability registry.

MSG-MX-003 retains its disabled provider declaration for account, room,
message, crypto, and media capabilities. MSG-MX-005 adds a separate, exact
Matrix-session catalog with two implemented read lanes and eight blocked
mutation lanes. MSG-MX-006 adds twelve exact read, protected-cache, and
cache-key lifecycle lanes. MSG-MX-007 adds seventeen exact crypto-store,
verification, cross-signing, backup, recovery, and reset lanes whose live
executors remain adapter-required. MSG-MX-008 adds fifteen exact manual-message,
encrypted-outbox, and generic-notification lanes backed by a loopback-only
one-use Rust broker and a dedicated Keychain-protected outbox store. MSG-MX-009
adds twenty exact DM, room, membership, administration, Space, encrypted-
search, and bounded-media lanes; media upload and download require exact
conjunctive `messages` plus `files` domain scopes. The
MSG-MX-006 primitives are implemented and loopback-tested, but live account
sync and manual messaging remain configuration-required.
Catalog visibility and accepted
lease schemas never imply callability; current request-scoped policy, target,
lease, budget, readiness, kill switch, safe-disable, and replay evaluation
remain mandatory.

Eight protected `Cache-Control: no-store` GET routes under
`/control-center/communications`, the human-readable
`scripts/dev/uaa_communications.py` CLI, and fail-closed TypeScript bindings
project the same backend-owned truth. A validation-only crypto proposal route
checks one exact fingerprinted request but cannot execute it. MSG-MX-008 adds
content-free posture, validation-only proposal, and fifteen exact authority-
required operation routes; default API composition deliberately binds no live
runtime. MSG-MX-009 adds another content-free posture route, validation-only
proposal route, and twenty idempotency-gated exact operation routes with their
real local, network, or destructive side effects. Posture routes are connector-
adjacent `local_sensitive` reads with no side effects. The `/messenger` UI
loads content-free Matrix sync, crypto, manual-messaging, and rooms/media
posture; its room and message content remains
synthetic. The approved adapter may perform exact discovery, authentication-
method, sync, and timeline-pagination reads only after exact request-scoped
authority and configuration checks. No enrolled account, protected message
response, decrypted event materialization, UI-bound live room/message/media
content, raw durable evidence content, or UI authority is present.

## Exact Repo-Owned Extension Metadata Adapter

One exact repo-owned registration now binds the reviewed
`capability:extension-metadata-inspection` declaration to UAA's bounded
filesystem metadata tool. It never imports extension package code and executes
only through `AuthorityDispatcher` after current policy, exact `AuthorityLease`,
safe-root target, budget, deadline, kill-switch, safe-disable, and idempotency
checks. The existing capability-availability API and CLI show unknown current
runtime posture until those request-scoped observations exist; the canonical
extension CLI adds `inspect-exact-adapter` for the registration manifest and
blockers. See `docs/tooling/EXACT_EXTENSION_ADAPTER.md`.

## Sealed Deterministic Calculation

The exact `calculation.sandbox.arithmetic.exact_lease` lane is implemented as bounded
arithmetic, not general CodeAct or Python. Its declaration appears in the shared
availability and Action/Tool/Code catalogs, while current platform,
configuration, image, health, safe-disable, budget, and lease truth remains
request-scoped. Execution requires the canonical mission orchestrator, runner,
dispatcher, exact `workspace/execute` mission lease, policy and budget checks,
and atomic container start/input-commit evidence. Raw expressions are transient;
durable state stores hashes and safe refs only. See
`docs/runtime/UAA_SEALED_CALCULATION_ADAPTER.md`.

## Intent Reasoning And Plan Revision Truth

`ultimate_ai_agent.core.intent.reasoning_truth` provides the deterministic,
no-effect reasoning contract for one current request. Raw request text is a
bounded transient function input only. The returned `IntentReasoningTruth`
contains a request fingerprint, safe intent ref and fingerprint, separate
facts, assumptions, and unknowns, confidence and ambiguity posture,
contradiction refs, operator questions, source/evidence refs, and explicit
instruction-shaped-content posture. All input remains untrusted data. The
contract cannot carry approval, lease, callable, tool, memory, provider, web,
shell, or execution authority.

`ultimate_ai_agent.core.planning.revisions` adds an immutable projection over
existing plan rows; it is not a third planner. Tuple-bound ordered membership,
dependencies, targets, sources, step definitions, and intent binding are
covered by SHA-256 safe refs. An unchanged revision replays only when the
complete revision fingerprint matches. Any membership, order, dependency,
definition, or target change requires a new, contiguous revision bound to the
exact predecessor ref and fingerprint plus a safe reason. Every revision
invalidates downstream approval, lease, dispatch, and budget assumptions; it
does not mint replacements.

The existing protected `GET /control-center/agent-loop/thread` route exposes
this backend-owned truth without changing its operation ID or read-only route
classification. `scripts/dev/uaa_founder_loop.py inspect-reasoning` renders a
human-readable explanation by default and optional redacted JSON from the same
object. The macOS-first Today cockpit renders the same facts, assumptions,
unknowns, questions, and revision fingerprints. The older canned user-intent
proposal catalog remains a compatibility surface and is not mislabeled as the
current-request assessment. Because this read surface is stateless, its current
plan is labeled as a content-addressed initial snapshot: any definition,
membership, order, dependency, or target change produces new decomposition and
revision refs. It does not claim predecessor lineage unless a prior revision is
supplied to the core revision validator.

## Progressive Disclosure

Use `registry.list_catalog(context)` or `registry.search(query, context, filters)` to expose compact `CapabilityCatalogEntry` records. Load the full manifest only after selection:

```python
entries = registry.search("project metadata search", context, filters)
manifest = registry.load_manifest(entries[0].id)
```

Optional LLM selectors receive only a small candidate set and must return a structured `CapabilitySelection`. The core does not hardcode or call any model provider.

## Read-Only Manifest Example

```python
from ultimate_ai_agent.core.capabilities import (
    CapabilityKind,
    CapabilityManifest,
    CoordinationMode,
    SafetyPolicy,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel

search_manifest = CapabilityManifest(
    id="cap:project_search",
    version="1.0.0",
    kind=CapabilityKind.tool,
    name="Project Search",
    description="Searches safe project metadata refs and returns structured summaries.",
    tags=["search", "retrieval", "metadata"],
    examples=["Use for read-only lookup across safe project refs."],
    anti_examples=["Do not use for file writes, commits, or external requests."],
    input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
    input_modes=["text", "structured_ref"],
    output_modes=["artifact"],
    side_effects=SideEffectLevel.read,
    risk_level=RiskLevel.low,
    authority_level="read_only",
    deterministic=True,
    rollback_supported=False,
    receipt_required=True,
    evidence_required=True,
    memory_write_allowed=False,
    context_injection_allowed=False,
    provider_runtime_allowed=False,
    browser_runtime_allowed=False,
    connector_write_allowed=False,
    allowed_coordination_modes=[
        CoordinationMode.direct_tool,
        CoordinationMode.parallel_read_fanout,
    ],
    concurrency_safe=True,
    single_writer_required=False,
    safety=SafetyPolicy(allow_parallel=True),
)
```

## Mutating Writer Manifest Example

```python
writer_manifest = CapabilityManifest(
    id="cap:code_writer",
    version="1.0.0",
    kind=CapabilityKind.agent,
    name="Code Writer",
    description="Applies one reviewed local code mutation scope through a single writer.",
    tags=["code", "writer"],
    examples=["Use for one serialized approved code edit scope."],
    anti_examples=["Do not run in parallel with another writer or external action."],
    input_schema={"type": "object"},
    output_schema={"type": "object"},
    input_modes=["structured_ref"],
    output_modes=["artifact"],
    side_effects=SideEffectLevel.write,
    risk_level=RiskLevel.medium,
    authority_level="mutating",
    deterministic=False,
    rollback_supported=True,
    receipt_required=True,
    evidence_required=True,
    memory_write_allowed=False,
    context_injection_allowed=False,
    provider_runtime_allowed=False,
    browser_runtime_allowed=False,
    connector_write_allowed=False,
    allowed_coordination_modes=[CoordinationMode.agent_as_tool],
    concurrency_safe=False,
    single_writer_required=True,
    safety=SafetyPolicy(require_single_writer=True, max_side_effect_level=SideEffectLevel.write),
)
```

## Registering Existing Tools Or Agents

```python
from ultimate_ai_agent.core.capabilities import (
    CapabilityRegistry,
    Coordinator,
    FileCoordinatorStateStore,
    LocalApprovalAuthority,
    wrap_agent,
    wrap_tool,
)

registry = CapabilityRegistry()
registry.register(search_manifest, wrap_tool(search_manifest.id, existing_search_tool))
registry.register(writer_manifest, wrap_agent(writer_manifest.id, existing_writer_agent))

coordinator = Coordinator(
    registry,
    state_store=FileCoordinatorStateStore(".uaa/capability_coordinator_state.json"),
    approval_authority=LocalApprovalAuthority(),
)
artifact = coordinator.run("Search safe metadata refs", {"capability_ids": [search_manifest.id]})
```

The callable receives `(TaskEnvelope, context)` and may return either an `Artifact` or any structured value. Non-artifact values are wrapped into a typed artifact.

## Routing Rules

- The coordinator plans centrally and synthesizes final output.
- Direct tool, agent-as-tool, workflow, reviewer, human-gate, and handoff modes are explicit `CoordinationMode` values.
- Handoff is only valid when a registered specialist is meant to own the next user-facing turn.
- Parallel fan-out is limited to read-only capabilities that also declare `concurrency_safe=True` and `safety.allow_parallel=True`.
- Mutating work is serialized through exactly one writer node.
- High and critical risk capabilities require approval, and approval refs must validate against an exact local approval grant.
- Missing auth scopes, unhealthy capabilities, and deprecated capabilities are denied or filtered by default.
- Manifest `dependencies`, `conflicts_with`, runtime timeout, retry limits, idempotency requirements, adapter health, and required output-schema keys are enforced before or during execution.
- Runtime callers can request a structured `coordinator.failure` artifact instead of exceptions by setting `return_failure_artifact=True`.

## Production-Readiness Hardening

The coordinator is now suitable for governed local production-readiness testing of registered in-process capabilities:

- Durable local state: `FileCoordinatorStateStore` writes atomic JSON state with run records, artifacts, audit events, and telemetry events.
- Approval gates: `LocalApprovalAuthority` denies missing, mismatched, revoked, expired, or out-of-scope approval grants.
- Single writer: mutating nodes acquire a single-writer lease before adapter invocation.
- Failure semantics: timeout, retry attempts, cancellation, policy denial, rollback-hook completion/failure, and optional structured failure artifacts are recorded.
- Adapter hardening: unhealthy adapters are denied before invocation, and required output-schema keys are checked on returned artifacts.
- Security posture: model/provider calls, network access, shell execution, browser automation, plugin execution, remote dispatch, memory writes, and context injection are still not created by this layer.

## Agent Runtime Compatibility

`docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md` defines the P2
compatibility boundary. Agent runtimes are adapters, not authority. The
`ultimate_ai_agent.core.agent_runtime` contracts carry safe refs, safe
summaries, blocked authority refs, trace refs, receipt refs, and evidence refs
only. Adapter output is not truth, memory, approval evidence, or execution
authority.

Static OpenAI/MCP-shaped schema export may expose UAA authority metadata under
`x-uaa-authority`, including `dispatch_authorized=false`. These exports are
metadata only; they do not import SDKs, create MCP clients, perform A2A
delegation, call providers, fetch the web, or dispatch tools.

## Exact Metadata Mission Core

The exact `founder-loop-filesystem-metadata-v1` capability is the first
end-to-end synchronous Founder Loop core lane. It accepts only a
backend-predeclared target ref under one injected repository root, runs one
metadata-only stat through `MissionOrchestrator -> MissionRunner ->
AuthorityDispatcher`, and requires a fresh `PolicyEngine` approval posture,
exact `LocalApprovalAuthority` validation, one shared mission-scoped
`AuthorityLease`, exact path/operation/cost claims, ready safe-disable and root
identity posture, and immutable request/target/deadline/idempotency bindings.

Success records a bounded hash-chained completion manifest covering the plan,
lease, approval validation, step and dispatch receipts, settled budgets,
evidence refs, and a review-required recall-only memory-candidate ref. The
manifest is execution evidence, not reusable authority. It stores no file
content, relative or absolute path, raw operator input, provider payload, or
model output. Broad filesystem reads, directory traversal, content reads,
mutation, shell execution, automatic memory write, and context injection remain
blocked.

Runtime Capability Foundation Phase 06 derives a bounded portable evidence
bundle from the complete locally readable mission-completion chain and the
exact referenced terminal dispatch records. Each
entry binds plan/run/step, full lease-scope fingerprint, exact approval-scope
fingerprint, policy, budget settlement, capability, adapter, truthful provider
posture, target/resource binding, request fingerprint, terminal outcome,
predecessor hash, redaction posture, and verifier version. The unchanged v1
bundle provides local SHA-256 hash-chain integrity only. A separate signed
artifact wrapper may now bind that verified bundle to an exact Ed25519 key
through the request-scoped `evidence_signing` dispatcher lanes. Signing requires
a pinned macOS Keychain helper, exact approval and resource-scoped
AuthorityLease, budget, kill-switch, safe-disable, readiness, and replay checks.
Structural dispatcher preflight performs no helper execution or Keychain probe;
those occur only after request-scoped authority succeeds and are rechecked at
the adapter start boundary.
Offline verification requires independently pinned public trust metadata. It
does not establish signer identity, non-repudiation, external anchoring, current
revocation truth, or source-ledger availability; evidence never grants
authority. See `docs/runtime/UAA_PORTABLE_MISSION_EVIDENCE_SIGNING.md`.

Runtime Capability Foundation Phase 04 projects this proven lane into the
canonical capability-availability snapshot and Action/Tool/Code catalog. The
snapshot separates supported declaration, unknown current-environment readiness,
and approval-required request authority. Current root, resource, health, and
safe-disable truth is evaluated only for the exact request; implementation
availability never means globally callable or authorized.

Preparation inputs are durably recoverable as bounded safe refs and hashes.
The protected Founder Loop exact-action API and repo-local CLI expose this one
predeclared metadata target as status → receipt-backed source-ref review →
source-bound prepare → exact approval → dispatcher execution → receipt → Today
refresh. Inspect, prepare, and approval recording each require the same current
exact mission lease; every adapter start still performs fresh request-scoped
authority, approval, budget, readiness, and kill-switch evaluation. Terminal
status is derived from the hash-chain-valid completion and exact terminal
dispatch ledgers, not from the mutable Today projection. The workflow preserves
the source-review receipt but does not create a business-memory candidate
from a metadata stat. No generic
filesystem target, path, content read, shell, provider, connector, automatic
memory write, or production authority was added. The macOS UI control remains
pending the separate control-registry wiring pass; it must not appear enabled
until it invokes these backend contracts, and the shell cannot mint approval or
lease authority.

Pre-Phase02 unfinished durable plans that bind more than one mission lease fail
closed at the new whole-plan single-lease preflight. They are not silently
migrated or resumed; a future persisted-state migration must classify them as
recovery-required before cross-version replay is supported.

## Governed Memory Context And Lifecycle

`GET /control-center/memory/context-manifest` includes the typed
`contract-ref:governed-memory-context-manifest:v1` preview with exact
included/excluded refs, freshness/conflict/sensitivity posture, content-free
receipt and fingerprint refs, and reconciled item/capacity budgets. L1 recall
excludes stale, conflicting, expired, inactive, malformed, or unknown lifecycle
posture before L2/L3/context proposal derivation.

Accept/correct writes use `lane-ref:memory-review-accept-correct`.
Reject/merge/supersede/expire/forget-request use
`lane-ref:memory-review-lifecycle-suppression` only when exact existing recall
records must be suppressed; current approval, AuthorityLease, safe-disable, and
exact record refs are re-evaluated before mutation. Context materialization,
automatic memory truth, action authority, connector writes, provider/model
calls, and hidden injection remain blocked.

## MCP And A2A Extension Points

Use `manifest_from_mcp_tool_spec()` and `manifest_from_a2a_agent_card()` to convert external metadata into local manifests. These helpers do not create live remote dispatch, network access, provider calls, or plugin execution. MCP and A2A imports fail closed by default: unknown MCP tools and unknown A2A agents become blocked, review-required UAA capability candidates, not read-only or delegation-ready capabilities. A future adapter can be registered only after its manifest, policy, exact approval, receipt, replay, revocation, and authority boundary are reviewed.

## Disposable Matrix Harness

MSG-MX-004 registers six exact local-development capabilities for inspect,
smoke, start, fixture seed, stop, and reset. Declaration or implemented-adapter
status does not mean global callability: every call flows through Python Core's
dispatcher with an exact current mission lease, request fingerprint, lifecycle
generation, target, budget, readiness, kill-switch, safe-disable, and replay
evaluation. Start, seed, stop, and reset additionally require fresh exact
LocalApprovalAuthority validation. Image availability, configuration, and
health remain current environment/request truth.

The backend is preprovision-only and cannot pull images. It produces
content-free receipts and retains `recovery_required` when cleanup cannot be
proved. No Matrix connector, account/session, sync/read, send/write, crypto,
media, React authority, standing harness switch, or production authority is
created. Canonical truth: `docs/connectors/MESSENGER_MATRIX_LOCAL_HARNESS.md`.

## Matrix Discovery And Session Read Lanes

MSG-MX-005 registers ten exact Matrix session capabilities. Homeserver
discovery and authentication-method inspection are implemented through
`AuthorityDispatcher`, the pinned `matrix-js-sdk` adapter, exact GET-path
allowlists, and bounded content-free observations. The second read requires a
current successful discovery observation bound to the same target.

Credential authentication, browser SSO/callback, refresh, logout, revoke-all,
credential rotation, and credential deletion are blocked in both Python and
the Node adapter. They require an authenticated one-use credential handoff or a
socket-owning SSO broker before runtime implementation can be accepted. The
native macOS helper is version-only. No session, sync, room, message, crypto,
media, issuer discovery, React authority, or standing Matrix enable switch is
created. Canonical truth: `docs/connectors/MESSENGER_MATRIX_SESSION.md`.

## Matrix Read-Only Sync And Protected Cache Lanes

MSG-MX-006 registers twelve exact Matrix sync, pagination, room-state, local
projection, encrypted-cache, and cache-key lifecycle authority declarations.
Two exact GET transports and the protected-cache/key primitives are implemented
and loopback-tested; ten canonical dispatch executors remain uncomposed and
fail closed. Network reads
are GET-only and credentials cross a one-use file descriptor; raw provider
responses remain transient. Cache and key changes require exact approval plus a
current lease. The whole-file AES-GCM container has no WAL, journal, temp query
store, or backup, and the macOS Keychain helper never returns key material.
The Node transport is bound to one repository-reviewed Node 22 profile and its
privately copied, hash-verified non-system Mach-O loader closure, then must pass
a bounded functional permission probe as defense in depth. Its content-free
runtime profile, exact credential-writer and per-instance registry owners,
implementation, and pseudonymized target scope derive one factory-registered
transport-owned executor/adapter binding. Callers cannot substitute an
executor subclass, unreviewed writer, registry subclass, result mapper, or
independently asserted ref.

Live account sync is `configuration_required` until an account credential broker
is enrolled and the hash-bound helper is installed and unlocked. The Messenger
desktop shell exposes backend posture only. Encrypted event materialization,
protected UI message reads, sends, typing/receipt writes, room mutations, media,
Memory writes, public release, and production authority remain blocked.
Canonical truth: `docs/connectors/MESSENGER_MATRIX_READ_ONLY_SYNC.md`.

## Matrix Crypto, Verification, Backup, And Recovery Lanes

MSG-MX-007 registers seventeen exact Matrix crypto authority bindings. Each
binds complete account, device, store, key, verification, cross-signing,
backup, recovery, generation, deadline, zero-cost budget, kill-switch,
safe-disable, rollback, lease, idempotency, and request-fingerprint scope.
Mutation and destructive proposals require fresh exact approval; the backup
status read still requires an exact current session lease. Approval refs grant
nothing.

The current one-shot Node adapter cannot provide persistent Rust crypto because
the pinned SDK requires IndexedDB durability and the approved Node boundary has
none. Every authority action is therefore marked unsupported-adapter, all
seventeen live operations are blocked, and no ephemeral shim is treated as a
persistent store. Protected posture/proposal API, human-readable CLI, and the
macOS Sessions & Recovery surface expose the same backend truth without key or
recovery material. Canonical truth:
`docs/connectors/MESSENGER_MATRIX_CRYPTO_RECOVERY.md`.

## Matrix Human-Commanded Messaging And Encrypted Outbox

MSG-MX-008 registers fifteen exact request-scoped authority bindings for send,
reply, thread, reaction, edit, redaction, typing, read receipt, draft write/read,
outbox enqueue/read/transition/discard, and generic desktop notification. Each
command binds complete account, loopback homeserver, device, room/event/
transaction, content fingerprint, outbox generation, notification policy,
deadline, zero-cost budget, readiness, kill switch, safe-disable, approval,
lease, idempotency, and compensation or rollback-readiness scope. An approval
ref is still only an identifier, and autonomous or AI sending is denied.

The native boundary pins `matrix-sdk` 0.18.0, uses a one-use HMAC-authenticated
loopback broker process, stores session and crypto-store material in the macOS
Keychain plus encrypted SQLite, and keeps drafts/outbox records in a separate
TTL-bounded encrypted store. A stable transaction and complete request
fingerprint drive both Core and native replay ledgers. Unknown execution truth
enters `outcome_uncertain` and cannot retry automatically.

Protected API, human-readable CLI, and the macOS Messenger shell expose the
same content-free posture. The default composition remains
`configuration_required`; synthetic fixture rooms never become authorized
targets. Remote homeservers, broad connector authority, background workers,
automatic retry, raw durable content, public release, and production authority
remain blocked. Canonical truth:
`docs/connectors/MESSENGER_MATRIX_MANUAL_MESSAGING.md`.

## Matrix Rooms, Encrypted Search, And Bounded Media

MSG-MX-009 registers twenty exact request-scoped bindings for direct-message
and room creation, join/leave, invitation transitions, power roles, Space
mapping, notification/history/pin/account-room settings, encrypted local
search, and bounded upload/download-quarantine/materialize/preview/cleanup.
Every command binds its complete safe target, transient raw-value projection,
fresh state where applicable, deadline, budget, readiness, approval, lease,
idempotency, safe-disable, and rollback or compensation posture. Upload and
download validate the complete exact composite domain map rather than treating
either domain independently.

Search stores only an AES-GCM index and HMAC token hashes. Media is limited to
24,576 bytes and four inspected types, stays under verified app-owned roots,
enters quarantine before use, and uses a fixed metadata-only parser. Transfer
progress is content-free; cancellation after broker send is uncertain, and
retry is manual with the same idempotency ref. The one-use loopback Rust broker
implements the sixteen network lanes; the four local lanes remain Python Core
operations. API, CLI, and Messenger posture default to
`configuration_required`, and synthetic UI content cannot authorize a target.
Canonical truth:
`docs/connectors/MESSENGER_MATRIX_ROOMS_SEARCH_MEDIA.md`.

## Local Smoke Harness

Run the dev-only smoke harness to prove registry resolution and schema export without adding live authority:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/capability_registry_smoke.py
```

The harness registers one deterministic in-process echo capability, resolves it for a test run context, executes it, prints OpenAI/MCP schemas, runs a bounded manifest/coordinator capability path, validates an exact local approval grant for a high-risk manifest, and reloads the durable coordinator state file. It does not add backend routes, provider calls, plugin loading, shell/network authority, or production authority. The master verifier runs this smoke explicitly so the runnable example remains covered even when pytest is skipped in split CI jobs.

## Testing

Run the focused suite:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py
```

The tests cover manifest validation, registry search/load, compact catalog rendering, policy denials, exact approval grants, durable state persistence, single-writer validation, read-only fan-out, partial fan-out failure artifacts, retries, idempotency enforcement, adapter health denial, output-schema checks, fake tool/agent adapters, mocked structured selection, and JSON import/export.
