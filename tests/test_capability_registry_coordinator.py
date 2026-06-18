import asyncio

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capabilities import (
    Artifact,
    CapabilityKind,
    CapabilityManifest,
    CapabilityRegistry,
    CapabilitySearchFilters,
    CapabilitySelection,
    CoordinationMode,
    Coordinator,
    InMemoryTelemetrySink,
    PolicyDeniedError,
    PolicyEngine,
    SafetyPolicy,
    SideEffectLevel,
    TaskEnvelope,
    TaskNode,
    TaskPlan,
    ToolAdapter,
    render_compact_catalog,
    select_capabilities,
    wrap_agent,
    wrap_tool,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


def _manifest(
    capability_id: str,
    *,
    name: str = "Safe Search",
    kind: CapabilityKind = CapabilityKind.tool,
    side_effects: SideEffectLevel = SideEffectLevel.read,
    risk_level: RiskLevel = RiskLevel.low,
    modes: list[CoordinationMode] | None = None,
    tags: list[str] | None = None,
    auth_scopes: list[str] | None = None,
    concurrency_safe: bool | None = None,
    single_writer_required: bool | None = None,
) -> CapabilityManifest:
    is_read_only = side_effects in {SideEffectLevel.none, SideEffectLevel.read}
    single_writer = (not is_read_only) if single_writer_required is None else single_writer_required
    return CapabilityManifest(
        id=capability_id,
        version="1.0.0",
        kind=kind,
        name=name,
        description=f"{name} capability for bounded coordinator tests.",
        tags=tags or ["search", "metadata"],
        examples=[f"Use {capability_id} for its exact bounded task."],
        anti_examples=[f"Do not use {capability_id} for unrelated or broader authority."],
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
        input_modes=["text", "structured_ref"],
        output_modes=["artifact"],
        side_effects=side_effects,
        risk_level=risk_level,
        approval_required=None,
        auth_scopes=auth_scopes or [],
        data_classes=["project_private"],
        allowed_coordination_modes=modes or [CoordinationMode.direct_tool],
        concurrency_safe=is_read_only if concurrency_safe is None else concurrency_safe,
        single_writer_required=single_writer,
        safety=SafetyPolicy(
            allow_parallel=is_read_only,
            require_single_writer=single_writer,
            approval_required=False,
            max_risk_level=risk_level,
            max_side_effect_level=side_effects,
        ),
    )


def _tool_result(label: str):
    async def _call(envelope: TaskEnvelope, context: dict) -> Artifact:
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="test.result",
            content={"label": label, "objective": envelope.objective},
            summary=f"{label} completed.",
            confidence=0.9,
        )

    return _call


def _registry_with_readers() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        _manifest(
            "cap:search",
            name="Safe Retrieval",
            modes=[CoordinationMode.direct_tool, CoordinationMode.parallel_read_fanout],
            tags=["search", "retrieval"],
        ),
        wrap_tool("cap:search", _tool_result("search")),
    )
    registry.register(
        _manifest(
            "cap:review",
            name="Safe Reviewer",
            kind=CapabilityKind.reviewer,
            modes=[CoordinationMode.reviewer, CoordinationMode.parallel_read_fanout],
            tags=["review", "retrieval"],
        ),
        wrap_agent("cap:review", _tool_result("review")),
    )
    return registry


def test_manifest_validation_requires_examples_and_single_writer_for_mutation() -> None:
    with pytest.raises(ValidationError, match="positive example"):
        CapabilityManifest(
            id="cap:missing_examples",
            version="1.0.0",
            kind=CapabilityKind.tool,
            name="Missing Examples",
            description="Invalid manifest.",
            anti_examples=["Do not use for mutation."],
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            input_modes=["text"],
            output_modes=["artifact"],
            allowed_coordination_modes=[CoordinationMode.direct_tool],
        )

    with pytest.raises(ValidationError, match="single-writer"):
        _manifest(
            "cap:unsafe_writer",
            side_effects=SideEffectLevel.write,
            risk_level=RiskLevel.medium,
            single_writer_required=False,
        )


def test_registry_register_search_load_and_compact_catalog_rendering() -> None:
    registry = _registry_with_readers()

    results = registry.search("retrieval search", {}, CapabilitySearchFilters(require_read_only=True))
    assert [entry.id for entry in results][:1] == ["cap:search"]
    assert registry.load_manifest("cap:search").name == "Safe Retrieval"

    catalog = render_compact_catalog(results)
    assert "id=cap:search" in catalog
    assert "side_effects=read" in catalog
    assert "long_description" not in catalog


def test_policy_denies_missing_auth_scope() -> None:
    manifest = _manifest("cap:private_search", auth_scopes=["capability:private-read"])
    decision = PolicyEngine().can_select(manifest, {})

    assert decision.allowed is False
    assert "AUTH_SCOPE_MISSING" in decision.reason_codes


def test_json_manifest_export_import_round_trip() -> None:
    registry = CapabilityRegistry()
    manifest = _manifest("cap:json_roundtrip")
    registry.register(manifest, wrap_tool(manifest.id, _tool_result("json")))

    payload = registry.export_manifest_json("cap:json_roundtrip")
    imported = CapabilityRegistry()
    imported.import_manifest_json(payload, wrap_tool("cap:json_roundtrip", _tool_result("json")))

    assert imported.load_manifest("cap:json_roundtrip").model_dump(mode="json") == manifest.model_dump(mode="json")


def test_existing_tool_and_agent_can_be_wrapped_and_invoked() -> None:
    async def fake_tool(envelope: TaskEnvelope, context: dict) -> dict:
        return {"tool": context["capability_id"], "task": envelope.task_id}

    async def fake_agent(envelope: TaskEnvelope, context: dict) -> Artifact:
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="agent.fake",
            content={"handled": envelope.objective},
            summary="Agent handled the task.",
        )

    tool_adapter = wrap_tool("cap:tool", fake_tool)
    agent_adapter = wrap_agent("cap:agent", fake_agent)
    envelope = TaskEnvelope(user_request="Summarize refs", objective="Summarize refs")

    tool_artifact = asyncio.run(tool_adapter.invoke(envelope, {"capability_id": "cap:tool"}))
    agent_artifact = asyncio.run(agent_adapter.invoke(envelope, {"capability_id": "cap:agent"}))

    assert tool_artifact.kind == "tool.result"
    assert tool_artifact.content["tool"] == "cap:tool"
    assert agent_artifact.kind == "agent.fake"


def test_llm_selector_receives_small_candidate_set_and_returns_structured_selection() -> None:
    class FakeSelector:
            def select(self, query: str, candidates: list, context: dict) -> CapabilitySelection:
                assert len(candidates) == 2
                return CapabilitySelection(
                    query=query,
                    selected_capability_ids=[candidates[0].id],
                    rejected_capability_ids=[candidates[1].id],
                    candidate_scores={entry.id: entry.score for entry in candidates},
                    selector_kind="fake-llm",
                    reason_codes=["FAKE_STRUCTURED_SELECTION"],
                    requires_manifest_ids=[candidates[0].id],
                )

    registry = _registry_with_readers()
    selection = select_capabilities(
        "retrieval review",
        registry,
        {},
        CapabilitySearchFilters(limit=2),
        llm_selector=FakeSelector(),
        llm_candidate_limit=2,
    )

    assert selection.selector_kind == "fake-llm"
    assert selection.selected_capability_ids == ["cap:review"]
    assert selection.requires_manifest_ids == ["cap:review"]


def test_coordinator_runs_fake_request_through_selection_planning_execution_and_synthesis() -> None:
    registry = _registry_with_readers()
    telemetry = InMemoryTelemetrySink()
    coordinator = Coordinator(registry, telemetry=telemetry)

    artifact = coordinator.run("retrieval search", {"trace_id": "trace:test"})

    assert artifact.kind == "coordinator.final"
    assert artifact.metadata["artifact_count"] == 1
    assert artifact.content[0]["producer_capability_id"] == "cap:search"
    assert any(event.event_name == "capability.selection_completed" for event in telemetry.events)
    assert any(event.event_name == "capability.execution_completed" for event in telemetry.events)


def test_parallel_read_fanout_is_allowed() -> None:
    registry = _registry_with_readers()
    coordinator = Coordinator(registry)
    plan = coordinator.plan(
        "retrieval review",
        {"capability_ids": ["cap:search", "cap:review"], "parallel_read_fanout": True},
    )

    assert {node.parallel_group for node in plan.nodes} == {"read_fanout"}

    artifact = coordinator.execute(plan, {})
    assert artifact.kind == "coordinator.final"
    assert artifact.metadata["artifact_count"] == 2
    assert {item["content"]["label"] for item in artifact.content} == {"search", "review"}


def test_parallel_write_fanout_is_denied() -> None:
    registry = CapabilityRegistry()
    writer_a = _manifest(
        "cap:writer_a",
        name="Writer A",
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
    )
    writer_b = _manifest(
        "cap:writer_b",
        name="Writer B",
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
    )
    registry.register(writer_a, wrap_tool(writer_a.id, _tool_result("writer_a")))
    registry.register(writer_b, wrap_tool(writer_b.id, _tool_result("writer_b")))
    envelope = TaskEnvelope(user_request="write", objective="write")
    plan = TaskPlan(
        user_request="write",
        nodes=[
            TaskNode(
                capability_id=writer_a.id,
                mode=CoordinationMode.parallel_read_fanout,
                envelope=envelope,
                parallel_group="writers",
                expected_side_effects=SideEffectLevel.write,
                risk_level=RiskLevel.medium,
            ),
            TaskNode(
                capability_id=writer_b.id,
                mode=CoordinationMode.parallel_read_fanout,
                envelope=envelope,
                parallel_group="writers",
                expected_side_effects=SideEffectLevel.write,
                risk_level=RiskLevel.medium,
            ),
        ],
        safe_summary="Unsafe write fan-out.",
    )

    with pytest.raises(PolicyDeniedError) as exc_info:
        Coordinator(registry).execute(plan, {})

    assert "PARALLEL_MUTATION_DENIED" in exc_info.value.reason_codes
    assert "MULTIPLE_WRITER_NODES_DENIED" in exc_info.value.reason_codes


def test_single_writer_plan_is_accepted() -> None:
    registry = CapabilityRegistry()
    writer = _manifest(
        "cap:writer",
        name="Single Writer",
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
    )
    registry.register(writer, wrap_tool(writer.id, _tool_result("writer")))
    envelope = TaskEnvelope(user_request="write", objective="write")
    node = TaskNode(
        capability_id=writer.id,
        mode=CoordinationMode.direct_tool,
        envelope=envelope,
        expected_side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
    )
    plan = TaskPlan(
        user_request="write",
        nodes=[node],
        single_writer_node_id=node.node_id,
        safe_summary="Single writer plan.",
    )

    decision = PolicyEngine().validate_side_effects(plan, registry)
    artifact = Coordinator(registry).execute(plan, {})

    assert decision.allowed is True
    assert "PLAN_SIDE_EFFECTS_ALLOWED" in decision.reason_codes
    assert artifact.metadata["artifact_count"] == 1


def test_approval_gate_blocks_high_risk_without_approval_ref() -> None:
    registry = CapabilityRegistry()
    high_risk = _manifest(
        "cap:high_risk",
        name="High Risk Review",
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.high,
        modes=[CoordinationMode.direct_tool],
    ).model_copy(update={"approval_required": "High-risk review requires explicit human approval."})
    high_risk = CapabilityManifest.model_validate(high_risk.model_dump())
    registry.register(high_risk, ToolAdapter(high_risk.id, _tool_result("high_risk")))
    coordinator = Coordinator(registry)
    plan = coordinator.plan("high risk review", {"capability_ids": [high_risk.id]})

    with pytest.raises(PolicyDeniedError) as exc_info:
        coordinator.execute(plan, {})

    assert "HIGH_RISK_REQUIRES_APPROVAL" in exc_info.value.reason_codes
