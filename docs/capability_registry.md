# Capability Registry And Coordinator

The capability registry is an additive, contract-first layer for coordinating tools, local agents, deterministic workflows, reviewer steps, and future adapter families. It does not add backend routes, production authority, provider calls, network access, shell execution, browser automation, plugin execution, memory writes, context injection, or new dependencies.

The existing `CapabilitySpec` registry remains available for decorator-style Python capabilities. The new `CapabilityManifest` lane adds typed manifests, compact catalog disclosure, structured task envelopes, policy checks, telemetry hooks, and bounded in-process adapters. The live-local testing runtime intentionally remains local/dev-only and does not grant production authority.

## Architecture

- `CapabilityRegistry` stores two compatible lanes:
  - Existing `CapabilitySpec` registrations for current framework callers.
  - New `CapabilityManifest` registrations with explicit adapters.
- `Coordinator` owns planning, routing, policy checks, state, and final synthesis.
- Specialists run as bounded agents-as-tools through `ToolAdapter`, `AgentAdapter`, `WorkflowAdapter`, `ReviewerAdapter`, `HandoffAdapter`, or `HumanGateAdapter`.
- `PolicyEngine` gates selection, execution, approval requirements, read-only fan-out, and single-writer behavior.
- `TaskEnvelope`, `TaskPlan`, `TaskNode`, and `Artifact` carry structured data instead of freeform inter-agent chat.
- `TelemetrySink` receives selection, execution, latency, success/failure, estimated cost, and policy denial events.

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
    allowed_coordination_modes=[CoordinationMode.agent_as_tool],
    concurrency_safe=False,
    single_writer_required=True,
    safety=SafetyPolicy(require_single_writer=True, max_side_effect_level=SideEffectLevel.write),
)
```

## Registering Existing Tools Or Agents

```python
from ultimate_ai_agent.core.capabilities import CapabilityRegistry, Coordinator, wrap_agent, wrap_tool

registry = CapabilityRegistry()
registry.register(search_manifest, wrap_tool(search_manifest.id, existing_search_tool))
registry.register(writer_manifest, wrap_agent(writer_manifest.id, existing_writer_agent))

coordinator = Coordinator(registry)
artifact = coordinator.run("Search safe metadata refs", {"capability_ids": [search_manifest.id]})
```

The callable receives `(TaskEnvelope, context)` and may return either an `Artifact` or any structured value. Non-artifact values are wrapped into a typed artifact.

## Live Local Testing Runtime

`build_live_local_testing_runtime(workspace_root)` creates a coordinator-ready registry for local user testing without granting production authority. It registers five concrete capabilities:

- `cap:live.local_file_metadata` uses `LocalFileManager.build_file_ref()` and optional bounded redacted preview reads. It is read-only and concurrency-safe.
- `cap:live.local_file_write` uses `LocalFileManager.propose_write()` and `apply_write()` for one approved local workspace write. It requires an `approval_ref`, an `idempotency_key`, `apply_write=True`, and single-writer planning.
- `cap:live.deterministic_workflow` runs an in-process deterministic workflow node over structured inputs and returns a stable digest.
- `cap:live.m23_local_model_loopback` wraps the existing M23 fixed-prompt local loopback model call policy. It remains high-risk, approval-required, fixed-prompt only, loopback-only, non-authoritative, and independently validates approval evidence before any transport contact.
- `cap:live.external_action_gate` returns a structured denial for provider, browser, network, plugin, remote, or other external authority that has no reviewed adapter.

Example:

```python
from ultimate_ai_agent.core.capabilities import (
    LOCAL_FILE_WRITE_CAPABILITY_ID,
    Coordinator,
    build_live_local_testing_runtime,
)

runtime = build_live_local_testing_runtime("/path/to/dev-workspace")
coordinator = Coordinator(runtime.registry)

artifact = coordinator.run(
    "Write one approved local test file",
    {
        "capability_ids": [LOCAL_FILE_WRITE_CAPABILITY_ID],
        "target_path": "out/live.txt",
        "new_content": "live write complete\n",
        "idempotency_key": "manual-smoke-1",
        "approval_ref": "approval_live_local_write",
        "apply_write": True,
    },
)
```

This path performs real local metadata reads and approved local file writes, but it still does not add shell execution, arbitrary filesystem authority, backend routes, Control Center controls, provider calls, browser automation, network tools, plugins, remote dispatch, memory writes, context injection, commits, or production authority.

## Routing Rules

- The coordinator plans centrally and synthesizes final output.
- Direct tool, agent-as-tool, workflow, reviewer, human-gate, and handoff modes are explicit `CoordinationMode` values.
- Handoff is only valid when a registered specialist is meant to own the next user-facing turn.
- Parallel fan-out is limited to read-only, concurrency-safe capabilities.
- Mutating work is serialized through exactly one writer node.
- High and critical risk capabilities require approval unless an approval ref is already present in task or run context.
- Missing auth scopes, unhealthy capabilities, and deprecated capabilities are denied or filtered by default.

## MCP And A2A Extension Points

Use `manifest_from_mcp_tool_spec()` and `manifest_from_a2a_agent_card()` to convert external metadata into local manifests. These helpers do not create live remote dispatch, network access, provider calls, or plugin execution. A future adapter can be registered only after its manifest, policy, and authority boundary are reviewed.

## Local Smoke Harness

Run the contract-only smoke harness to prove registry resolution and schema export without adding live authority:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/capability_registry_smoke.py
```

The harness registers one deterministic in-process echo capability, resolves it for a test run context, executes it, and prints OpenAI/MCP schemas. It does not add backend routes, provider calls, plugin loading, shell/network authority, or production authority.

Run the live-local smoke harness to exercise the graduated local testing path:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/live_local_capability_smoke.py
```

That harness uses a temporary workspace, performs a real metadata read and approved local file write, runs a deterministic workflow node, exercises the M23 fake loopback transport through existing approval validation, and verifies external authority remains gated.

## Testing

Run the focused suite:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py tests/test_live_local_capability_testing.py
```

The tests cover manifest validation, registry search/load, compact catalog rendering, policy denials, single-writer validation, read-only fan-out, fake tool/agent adapters, mocked structured selection, and JSON import/export.
The live-local tests also create a temporary file, read its metadata, apply an approved single-writer local file write, prove multiple writers are rejected, run the deterministic workflow node, exercise the M23 fake loopback transport through existing approval validation, and verify external actions remain gated.
