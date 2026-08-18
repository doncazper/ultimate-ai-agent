from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

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
    SystemMapEdgeKind,
    SystemMapSnapshotStore,
    SystemMapTruthStatus,
    build_default_system_map_snapshot,
)
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


def test_default_snapshot_converges_authority_lanes_and_ecosystem() -> None:
    snapshot = build_default_system_map_snapshot(
        created_at=FIXED_TIME,
        max_opportunities=5,
    )
    nodes = {node.node_id: node for node in snapshot.graph.nodes}

    assert "entity:task" in nodes
    assert "boundary:policy-engine" in nodes
    assert "lane-ref:today-loop-read" in nodes
    assert "feature:durable-system-capability-map" in nodes
    assert (
        "capability-source:ultimate_ai_agent.core.capabilities.registry" in nodes
    )
    assert any(node.kind.value == "route" for node in snapshot.graph.nodes)
    assert snapshot.opportunities


def test_currentness_gate_covers_repository_and_detects_new_manifest_source(
    tmp_path,
) -> None:
    assert verify_system_map_currentness.verify_repository() == []

    source = tmp_path / "src/ultimate_ai_agent/new_capability.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "def build():\n    return CapabilityManifest()\n",
        encoding="utf-8",
    )

    assert verify_system_map_currentness.discover_manifest_constructor_modules(
        tmp_path
    ) == ("ultimate_ai_agent.new_capability",)


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
