from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.authority import build_existing_lane_authority_mappings
from ultimate_ai_agent.core.capabilities import (
    CapabilityKind,
    CapabilityManifest,
    CapabilityRegistry,
    CoordinationMode,
    SafetyPolicy,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel
from ultimate_ai_agent.core.system_map import (
    SystemMapBuilder,
    SystemMapEdge,
    SystemMapEdgeKind,
    SystemMapEdgeOrigin,
    SystemMapFeatureDeclaration,
    SystemMapNode,
    SystemMapNodeKind,
    SystemMapOpportunity,
    SystemMapSnapshot,
    SystemMapSnapshotStore,
    SystemMapTruthStatus,
    build_default_system_map_snapshot,
)
from ultimate_ai_agent.core.system_map.models import (
    _validate_dependency_acyclic,
    system_map_edge_id,
    system_map_opportunity_ref,
    system_map_snapshot_ref,
)
from ultimate_ai_agent.core.system_map import store as system_map_store_module
from scripts.dev import uaa_system_map
from scripts import verify_system_map_currentness


FIXED_TIME = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def _manifest(
    capability_id: str,
    *,
    input_modes: list[str],
    output_modes: list[str],
    dependencies: list[str] | None = None,
    conflicts_with: list[str] | None = None,
) -> CapabilityManifest:
    return CapabilityManifest(
        id=capability_id,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name=capability_id.replace("cap:", "").replace("_", " ").title(),
        description="Typed test capability for system map verification.",
        tags=["system-map-test"],
        examples=["Use for bounded system map contract testing."],
        anti_examples=["Do not use as runtime authority."],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        input_modes=input_modes,
        output_modes=output_modes,
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.low,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=True,
        dependencies=dependencies or [],
        conflicts_with=conflicts_with or [],
        safety=SafetyPolicy(
            allow_parallel=True,
            max_risk_level=RiskLevel.low,
            max_side_effect_level=SideEffectLevel.read,
        ),
    )


def test_graph_uses_canonical_ecosystem_ownership() -> None:
    graph = SystemMapBuilder().build_graph(include_ecosystem=True)
    nodes = {node.node_id: node for node in graph.nodes}
    edges = {
        (edge.source_node_id, edge.kind, edge.target_node_id) for edge in graph.edges
    }

    assert nodes["entity:task"].attributes["canonical_owner"] == "tasks"
    assert (
        "entity:task",
        SystemMapEdgeKind.owned_by,
        "domain:tasks",
    ) in edges
    assert (
        "domain:tasks",
        SystemMapEdgeKind.projects_to,
        "surface:today",
    ) in edges
    assert all(node.grants_authority is False for node in graph.nodes)
    assert all(edge.grants_authority is False for edge in graph.edges)


def test_manifest_dependencies_conflicts_and_missing_nodes_are_durable_graph_truth() -> (
    None
):
    producer = _manifest(
        "cap:producer",
        input_modes=["request_ref"],
        output_modes=["artifact_ref"],
    )
    consumer = _manifest(
        "cap:consumer",
        input_modes=["artifact_ref"],
        output_modes=["review_ref"],
        dependencies=["cap:producer", "cap:missing-reviewer"],
        conflicts_with=["cap:conflict"],
    )
    graph = SystemMapBuilder().build_graph(
        manifests=[consumer, producer],
        include_ecosystem=False,
    )
    nodes = {node.node_id: node for node in graph.nodes}
    edges = {
        (edge.source_node_id, edge.kind, edge.target_node_id, edge.origin.value)
        for edge in graph.edges
    }

    assert nodes["cap:missing-reviewer"].truth_status == SystemMapTruthStatus.missing
    assert nodes["cap:conflict"].truth_status == SystemMapTruthStatus.missing
    assert (
        "cap:consumer",
        SystemMapEdgeKind.depends_on,
        "cap:producer",
        "declared",
    ) in edges
    assert (
        "cap:consumer",
        SystemMapEdgeKind.conflicts_with,
        "cap:conflict",
        "declared",
    ) in edges
    assert (
        "cap:producer",
        SystemMapEdgeKind.compatible_with,
        "cap:consumer",
        "inferred",
    ) in edges


def test_graph_ref_is_deterministic_for_input_order() -> None:
    first = _manifest("cap:first", input_modes=["request"], output_modes=["artifact"])
    second = _manifest("cap:second", input_modes=["artifact"], output_modes=["result"])
    builder = SystemMapBuilder()

    graph_a = builder.build_graph(manifests=[first, second], include_ecosystem=False)
    graph_b = builder.build_graph(manifests=[second, first], include_ecosystem=False)

    assert graph_a == graph_b
    assert graph_a.graph_ref == graph_b.graph_ref


def test_builder_rejects_duplicate_manifest_ids() -> None:
    first = _manifest(
        "cap:duplicate", input_modes=["request"], output_modes=["artifact"]
    )
    second = _manifest(
        "cap:duplicate",
        input_modes=["request"],
        output_modes=["artifact"],
        dependencies=["cap:other"],
    )

    with pytest.raises(ValueError, match="SYSTEM_MAP_DUPLICATE_MANIFEST_ID"):
        SystemMapBuilder().build_graph(
            manifests=[first, second], include_ecosystem=False
        )


def test_feature_source_order_does_not_change_graph_ref() -> None:
    def feature(source_refs: tuple[str, ...]) -> SystemMapFeatureDeclaration:
        return SystemMapFeatureDeclaration(
            feature_ref="feature:source-order-test",
            name="Source order test",
            safe_summary="Equivalent provenance order must remain canonical.",
            truth_status=SystemMapTruthStatus.declared,
            source_refs=source_refs,
        )

    builder = SystemMapBuilder()
    graph_a = builder.build_graph(
        feature_declarations=[feature(("source-ref:zeta", "source-ref:alpha"))],
        include_ecosystem=False,
    )
    graph_b = builder.build_graph(
        feature_declarations=[feature(("source-ref:alpha", "source-ref:zeta"))],
        include_ecosystem=False,
    )

    assert graph_a == graph_b


def test_opportunity_discovery_is_bounded_proposal_only() -> None:
    first = _manifest("cap:first", input_modes=["request"], output_modes=["artifact"])
    second = _manifest("cap:second", input_modes=["artifact"], output_modes=["result"])

    snapshot = SystemMapBuilder().build_snapshot(
        manifests=[first, second],
        include_ecosystem=False,
        created_at=FIXED_TIME,
        max_opportunities=1,
    )

    assert len(snapshot.opportunities) == 1
    opportunity = snapshot.opportunities[0]
    assert opportunity.truth_status == "proposal_only"
    assert opportunity.requires_operator_review is True
    assert opportunity.grants_authority is False
    assert opportunity.graph_ref == snapshot.graph.graph_ref
    assert snapshot.grants_authority is False


def test_opportunity_is_blocked_by_transitive_missing_prerequisite() -> None:
    producer = _manifest(
        "cap:producer", input_modes=["request"], output_modes=["artifact"]
    )
    consumer = _manifest(
        "cap:consumer",
        input_modes=["artifact"],
        output_modes=["result"],
        dependencies=["cap:missing-prerequisite"],
    )

    snapshot = SystemMapBuilder().build_snapshot(
        manifests=[producer, consumer],
        include_ecosystem=False,
        created_at=FIXED_TIME,
    )

    opportunity = next(
        item
        for item in snapshot.opportunities
        if set(item.capability_node_ids) == {"cap:producer", "cap:consumer"}
    )
    assert opportunity.truth_status == "blocked"


def test_generated_opportunity_title_is_bounded() -> None:
    producer = _manifest(
        "cap:long-producer", input_modes=["request"], output_modes=["artifact"]
    ).model_copy(update={"name": "Producer " + "A" * 130})
    consumer = _manifest(
        "cap:long-consumer", input_modes=["artifact"], output_modes=["result"]
    ).model_copy(update={"name": "Consumer " + "B" * 130})

    snapshot = SystemMapBuilder().build_snapshot(
        manifests=[producer, consumer],
        include_ecosystem=False,
        created_at=FIXED_TIME,
        max_opportunities=1,
    )

    assert len(snapshot.opportunities[0].title) == 180
    assert snapshot.opportunities[0].title.endswith("...")


def test_snapshot_rejects_opportunity_evidence_outside_bound_graph() -> None:
    first = _manifest("cap:first", input_modes=["request"], output_modes=["artifact"])
    second = _manifest("cap:second", input_modes=["artifact"], output_modes=["result"])
    snapshot = SystemMapBuilder().build_snapshot(
        manifests=[first, second],
        include_ecosystem=False,
        created_at=FIXED_TIME,
        max_opportunities=1,
    )
    original = snapshot.opportunities[0]
    bad_capabilities = (original.capability_node_ids[0], "cap:not-in-graph")
    bad_ref = system_map_opportunity_ref(
        snapshot.graph.graph_ref,
        bad_capabilities,
        original.supporting_edge_ids,
        original.gap_refs,
    )
    bad = original.model_copy(
        update={
            "capability_node_ids": bad_capabilities,
            "opportunity_ref": bad_ref,
        }
    )
    snapshot_ref = system_map_snapshot_ref(
        created_at=FIXED_TIME,
        graph=snapshot.graph,
        opportunities=(bad,),
        source_refs=snapshot.source_refs,
    )

    with pytest.raises(
        ValueError, match="SYSTEM_MAP_OPPORTUNITY_CAPABILITY_NODE_INVALID"
    ):
        SystemMapSnapshot(
            snapshot_ref=snapshot_ref,
            created_at=FIXED_TIME,
            graph=snapshot.graph,
            opportunities=(bad,),
            source_refs=snapshot.source_refs,
        )

    missing_edges = ("system-map-edge:" + "0" * 32,)
    bad_edge_ref = system_map_opportunity_ref(
        snapshot.graph.graph_ref,
        original.capability_node_ids,
        missing_edges,
        original.gap_refs,
    )
    bad_edge = original.model_copy(
        update={
            "supporting_edge_ids": missing_edges,
            "opportunity_ref": bad_edge_ref,
        }
    )
    bad_edge_snapshot_ref = system_map_snapshot_ref(
        created_at=FIXED_TIME,
        graph=snapshot.graph,
        opportunities=(bad_edge,),
        source_refs=snapshot.source_refs,
    )
    with pytest.raises(
        ValueError, match="SYSTEM_MAP_OPPORTUNITY_SUPPORTING_EDGE_INVALID"
    ):
        SystemMapSnapshot(
            snapshot_ref=bad_edge_snapshot_ref,
            created_at=FIXED_TIME,
            graph=snapshot.graph,
            opportunities=(bad_edge,),
            source_refs=snapshot.source_refs,
        )


def test_only_canonical_opportunity_ref_is_accepted() -> None:
    graph = SystemMapBuilder().build_graph(
        manifests=[
            _manifest("cap:first", input_modes=["request"], output_modes=["artifact"]),
            _manifest("cap:second", input_modes=["artifact"], output_modes=["result"]),
        ],
        include_ecosystem=False,
    )
    capability_ids = ("cap:first", "cap:second")
    supporting_edges = (graph.edges[0].edge_id,)
    gap_refs = ("gap-ref:test",)
    legacy_payload = {
        "graph_ref": graph.graph_ref,
        "capability_node_ids": capability_ids,
        "gap_refs": gap_refs,
    }
    legacy_digest = hashlib.sha256(
        json.dumps(legacy_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    legacy_ref = f"system-map-opportunity:sha256:{legacy_digest}"

    with pytest.raises(ValueError, match="SYSTEM_MAP_OPPORTUNITY_REF_MISMATCH"):
        SystemMapOpportunity(
            opportunity_ref=legacy_ref,
            graph_ref=graph.graph_ref,
            title="Legacy evidence mismatch",
            safe_summary="Supporting evidence must remain content addressed.",
            capability_node_ids=capability_ids,
            supporting_edge_ids=supporting_edges,
            gap_refs=gap_refs,
            confidence=0.5,
        )


def test_snapshot_store_round_trip_history_and_tamper_detection(tmp_path) -> None:
    snapshot = SystemMapBuilder().build_snapshot(
        include_ecosystem=True,
        created_at=FIXED_TIME,
    )
    store = SystemMapSnapshotStore(tmp_path / "system-map")

    assert store.save(snapshot) == snapshot.snapshot_ref
    assert store.load_current() == snapshot
    assert store.load(snapshot.snapshot_ref) == snapshot
    assert store.list_snapshot_refs() == (snapshot.snapshot_ref,)

    payload = json.loads(store.current_path.read_text(encoding="utf-8"))
    payload["graph"]["nodes"][0]["name"] = "Tampered"
    store.current_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="SYSTEM_MAP_GRAPH_REF_MISMATCH"):
        store.load_current()


def test_snapshot_store_binds_history_payload_to_filename_ref(tmp_path) -> None:
    store = SystemMapSnapshotStore(tmp_path / "system-map")
    first = SystemMapBuilder().build_snapshot(
        include_ecosystem=True,
        created_at=FIXED_TIME,
    )
    second = SystemMapBuilder().build_snapshot(
        include_ecosystem=True,
        created_at=FIXED_TIME.replace(minute=1),
    )
    store.save(first)
    store.save(second)
    store.snapshot_path(first.snapshot_ref).write_text(
        store.snapshot_path(second.snapshot_ref).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="SYSTEM_MAP_HISTORY_REF_MISMATCH"):
        store.load(first.snapshot_ref)
    with pytest.raises(ValueError, match="SYSTEM_MAP_HISTORY_REF_MISMATCH"):
        store.list_snapshot_refs()


def test_snapshot_store_fails_closed_without_cross_process_lock(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(system_map_store_module, "fcntl", None)
    store = SystemMapSnapshotStore(tmp_path / "system-map")

    with pytest.raises(RuntimeError, match="SYSTEM_MAP_FILE_LOCK_UNAVAILABLE"):
        store.list_snapshot_refs()


def test_default_snapshot_converges_authority_lanes_and_ecosystem() -> None:
    snapshot = build_default_system_map_snapshot(
        created_at=FIXED_TIME,
        max_opportunities=5,
    )
    nodes = {node.node_id: node for node in snapshot.graph.nodes}

    assert "entity:task" in nodes
    assert "boundary:policy-engine" in nodes
    assert "lane-ref:today-loop-read" in nodes
    assert "feature:finance-compliance-program" in nodes
    assert (
        nodes["feature:finance-compliance-program"].truth_status
        == SystemMapTruthStatus.planned
    )
    assert "feature:durable-system-capability-map" in nodes
    assert "feature:local-knowledge-dump" in nodes
    assert "capability-source:ultimate_ai_agent.core.capabilities.registry" in nodes
    assert any(node.kind.value == "route" for node in snapshot.graph.nodes)
    assert snapshot.opportunities


def test_currentness_gate_covers_repository_and_detects_new_manifest_source(
    tmp_path,
) -> None:
    assert verify_system_map_currentness.verify_repository() == []

    source = tmp_path / "src/ultimate_ai_agent/new_capability.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from ultimate_ai_agent.core.capabilities.models import CapabilityManifest\n\n"
        "def build():\n    return CapabilityManifest()\n",
        encoding="utf-8",
    )
    alias_source = tmp_path / "src/ultimate_ai_agent/aliased_capability.py"
    alias_source.write_text(
        "from ultimate_ai_agent.core.capabilities.models import "
        "CapabilityManifest as Manifest\n\n"
        "def build():\n    return Manifest()\n",
        encoding="utf-8",
    )
    unrelated = tmp_path / "src/ultimate_ai_agent/unrelated_factory.py"
    unrelated.write_text(
        "def build(factory):\n    return factory.CapabilityManifest()\n",
        encoding="utf-8",
    )
    module_alias = tmp_path / "src/ultimate_ai_agent/module_alias_capability.py"
    module_alias.write_text(
        "import ultimate_ai_agent.core.capabilities.models as capability_models\n\n"
        "def build():\n    return capability_models.CapabilityManifest()\n",
        encoding="utf-8",
    )

    assert verify_system_map_currentness.discover_manifest_constructor_modules(
        tmp_path
    ) == (
        "ultimate_ai_agent.aliased_capability",
        "ultimate_ai_agent.module_alias_capability",
        "ultimate_ai_agent.new_capability",
    )


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "/" + "workspace/project/file",
        "/" + "root/private.json",
        "/" + "var/data",
        "/" + "opt/app",
        "configured=" + "/" + "workspace/private.json",
        "/" + "root",
    ],
)
def test_system_map_rejects_raw_absolute_paths(unsafe_text: str) -> None:
    with pytest.raises(ValueError, match="SYSTEM_MAP_UNSAFE_TEXT_DENIED"):
        SystemMapNode(
            node_id="source:absolute-path-test",
            kind=SystemMapNodeKind.source,
            name="Unsafe path test",
            safe_summary=f"Durable payload included {unsafe_text}",
            truth_status=SystemMapTruthStatus.declared,
        )


def test_system_map_node_attributes_are_deeply_immutable() -> None:
    node = SystemMapNode(
        node_id="source:immutable-attributes-test",
        kind=SystemMapNodeKind.source,
        name="Immutable attributes",
        safe_summary="Fingerprint-bound attributes cannot drift in memory.",
        truth_status=SystemMapTruthStatus.declared,
        attributes={"nested": {"items": ["alpha", "beta"]}},
    )

    with pytest.raises(TypeError, match="SYSTEM_MAP_ATTRIBUTES_IMMUTABLE"):
        node.attributes["new"] = "value"
    with pytest.raises(TypeError, match="SYSTEM_MAP_ATTRIBUTES_IMMUTABLE"):
        node.attributes["nested"]["new"] = "value"
    assert node.attributes["nested"]["items"] == ("alpha", "beta")


@pytest.mark.parametrize(
    "field_name",
    ["password", "api_key", "auth_token", "service_client_secret"],
)
def test_system_map_rejects_nonempty_credential_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match="SYSTEM_MAP_RAW_OR_SECRET_FIELD_DENIED"):
        SystemMapNode(
            node_id="source:credential-field-test",
            kind=SystemMapNodeKind.source,
            name="Credential field test",
            safe_summary="Credential-shaped fields cannot enter durable maps.",
            truth_status=SystemMapTruthStatus.declared,
            attributes={field_name: "abcdefghijklmnop"},
        )


def test_blocking_adapter_posture_overrides_implemented_status() -> None:
    mapping = next(
        item
        for item in build_existing_lane_authority_mappings()
        if item.unsupported_adapter_blocks_capability
    ).model_copy(update={"status": "implemented"})

    graph = SystemMapBuilder().build_graph(
        authority_mappings=[mapping], include_ecosystem=False
    )
    node = next(item for item in graph.nodes if item.node_id == mapping.lane_ref)

    assert node.truth_status == SystemMapTruthStatus.blocked


def test_manifest_ids_fail_at_contract_boundary_before_registry_use() -> None:
    for invalid_id in ("x", "image caption", "cap:" + "/" + "root/private"):
        with pytest.raises(ValidationError, match="bounded safe reference"):
            _manifest(invalid_id, input_modes=["request"], output_modes=["result"])

    with pytest.raises(ValidationError, match="references must be bounded"):
        _manifest(
            "cap:valid",
            input_modes=["request"],
            output_modes=["result"],
            dependencies=["invalid dependency"],
        )


def test_dependency_cycle_check_handles_long_acyclic_chains_iteratively() -> None:
    edges = tuple(
        SystemMapEdge(
            edge_id=system_map_edge_id(
                f"cap:node-{index}",
                SystemMapEdgeKind.depends_on,
                f"cap:node-{index + 1}",
            ),
            source_node_id=f"cap:node-{index}",
            target_node_id=f"cap:node-{index + 1}",
            kind=SystemMapEdgeKind.depends_on,
            origin=SystemMapEdgeOrigin.declared,
            safe_summary="Long-chain dependency remains valid without recursion.",
        )
        for index in range(1_200)
    )

    _validate_dependency_acyclic(edges)


def test_registry_lists_defensive_manifest_copies() -> None:
    registry = CapabilityRegistry()
    manifest = _manifest(
        "cap:listed", input_modes=["request"], output_modes=["artifact"]
    )

    class Adapter:
        pass

    registry.register(manifest, Adapter())
    listed = registry.list_manifests()

    assert listed == [manifest]
    assert listed[0] is not registry.load_manifest(manifest.id)


def test_cli_build_inspect_and_verify_share_the_durable_snapshot(
    tmp_path, capsys
) -> None:
    store = tmp_path / "system-map-cli"

    assert (
        uaa_system_map.main(
            ["--store", str(store), "build", "--max-opportunities", "2"]
        )
        == 0
    )
    build_output = capsys.readouterr().out
    assert "UAA durable system capability map" in build_output
    assert "opportunities: 2" in build_output

    assert uaa_system_map.main(["--store", str(store), "inspect"]) == 0
    inspect_output = capsys.readouterr().out
    assert "Read-only structure" in inspect_output

    assert uaa_system_map.main(["--store", str(store), "verify", "--json"]) == 0
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["status"] == "verified"
    assert verify_payload["grants_authority"] is False
    assert verify_payload["history_count"] == 1
