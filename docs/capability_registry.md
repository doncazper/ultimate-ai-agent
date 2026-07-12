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

Preparation inputs are durably recoverable as bounded safe refs and hashes,
but no public API, mutating CLI, or Control Center execution control is exposed
in this phase. The existing read-only API, CLI, and macOS panel inspect
completion truth only. Operator initiation remains a Python-core integration
surface until the later parity phase binds one protected contract without
allowing the shell to mint approval or lease authority.

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
