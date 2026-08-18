"""Deterministic construction of UAA's system capability graph."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
import hashlib

from ultimate_ai_agent.core.authority.contracts import AuthorityCapabilityMapping
from ultimate_ai_agent.core.capabilities.models import CapabilityManifest
from ultimate_ai_agent.core.ecosystem import (
    AppId,
    CANONICAL_OWNERSHIP_REGISTRY,
    CanonicalOwnerId,
)
from ultimate_ai_agent.core.system_map.models import (
    SystemCapabilityGraph,
    SystemMapEdge,
    SystemMapEdgeKind,
    SystemMapEdgeOrigin,
    SystemMapFeatureDeclaration,
    SystemMapNode,
    SystemMapNodeKind,
    SystemMapOpportunity,
    SystemMapSnapshot,
    SystemMapTruthStatus,
    system_map_edge_id,
    system_map_graph_ref,
    system_map_opportunity_ref,
    system_map_snapshot_ref,
)


_OWNER_TO_SURFACES: dict[CanonicalOwnerId, tuple[AppId, ...]] = {
    CanonicalOwnerId.calendar: (AppId.calendar, AppId.today),
    CanonicalOwnerId.tasks: (AppId.tasks, AppId.today, AppId.boards),
    CanonicalOwnerId.plans: (AppId.plans, AppId.today, AppId.boards),
    CanonicalOwnerId.boards: (AppId.boards, AppId.today),
    CanonicalOwnerId.crm: (AppId.crm, AppId.today, AppId.boards),
    CanonicalOwnerId.inbox: (AppId.inbox, AppId.action_inbox, AppId.today),
    CanonicalOwnerId.organizer: (AppId.organizer, AppId.today),
    CanonicalOwnerId.governance: (
        AppId.action_inbox,
        AppId.evidence,
        AppId.trust_settings,
    ),
    CanonicalOwnerId.memory: (AppId.memory, AppId.today),
}

_BOUNDARIES = (
    (
        "boundary:policy-engine",
        "PolicyEngine",
        "Every capability remains subject to current request-scoped policy evaluation.",
    ),
    (
        "boundary:local-approval-authority",
        "LocalApprovalAuthority",
        "Approval references authorize nothing until their exact scope is validated.",
    ),
    (
        "boundary:evidence-and-receipts",
        "Evidence and receipts",
        "Execution truth requires lane-specific terminal receipts and redacted evidence.",
    ),
    (
        "boundary:foundation-gate",
        "Foundation Gate",
        "High-authority capability promotion remains gated by repository verification.",
    ),
)


class SystemMapBuilder:
    """Build a canonical graph from typed registries, never from runtime output."""

    def build_graph(
        self,
        *,
        manifests: Iterable[CapabilityManifest] = (),
        authority_mappings: Sequence[AuthorityCapabilityMapping] = (),
        feature_declarations: Sequence[SystemMapFeatureDeclaration] = (),
        capability_source_modules: Sequence[str] = (),
        include_ecosystem: bool = True,
    ) -> SystemCapabilityGraph:
        nodes: dict[str, SystemMapNode] = {}
        edges: dict[str, SystemMapEdge] = {}

        for node_id, name, summary in _BOUNDARIES:
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=node_id,
                    kind=SystemMapNodeKind.boundary,
                    name=name,
                    safe_summary=summary,
                    truth_status=SystemMapTruthStatus.implemented,
                    source_refs=("source-ref:workspace-invariants",),
                ),
            )

        if include_ecosystem:
            self._add_ecosystem(nodes, edges)

        manifest_list = sorted(manifests, key=lambda item: item.id)
        manifest_ids = [manifest.id for manifest in manifest_list]
        if len(manifest_ids) != len(set(manifest_ids)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_MANIFEST_ID")
        self._add_manifests(nodes, edges, manifest_list)
        self._add_authority_mappings(nodes, edges, authority_mappings)
        self._add_capability_sources(nodes, edges, capability_source_modules)
        self._add_features(nodes, edges, feature_declarations)
        self._add_manifest_compatibility(edges, manifest_list)

        canonical_nodes = tuple(sorted(nodes.values(), key=lambda item: item.node_id))
        canonical_edges = tuple(sorted(edges.values(), key=lambda item: item.edge_id))
        return SystemCapabilityGraph(
            graph_ref=system_map_graph_ref(canonical_nodes, canonical_edges),
            nodes=canonical_nodes,
            edges=canonical_edges,
        )

    def build_snapshot(
        self,
        *,
        manifests: Iterable[CapabilityManifest] = (),
        authority_mappings: Sequence[AuthorityCapabilityMapping] = (),
        feature_declarations: Sequence[SystemMapFeatureDeclaration] = (),
        capability_source_modules: Sequence[str] = (),
        include_ecosystem: bool = True,
        created_at: datetime | None = None,
        max_opportunities: int = 30,
    ) -> SystemMapSnapshot:
        manifest_list = tuple(manifests)
        authority_mapping_list = tuple(authority_mappings)
        graph = self.build_graph(
            manifests=manifest_list,
            authority_mappings=authority_mapping_list,
            feature_declarations=feature_declarations,
            capability_source_modules=capability_source_modules,
            include_ecosystem=include_ecosystem,
        )
        opportunities = discover_system_map_opportunities(
            graph,
            max_opportunities=max_opportunities,
        )
        timestamp = created_at or datetime.now(timezone.utc)
        source_refs = tuple(
            ref
            for ref, included in (
                ("source-ref:eco-000-canonical-ownership", include_ecosystem),
                ("source-ref:authority-lane-registry", bool(authority_mapping_list)),
                ("source-ref:capability-manifest-registry", bool(manifest_list)),
                (
                    "source-ref:system-map-capability-source-catalog",
                    bool(capability_source_modules),
                ),
                (
                    "source-ref:system-map-feature-catalog",
                    bool(feature_declarations),
                ),
            )
            if included
        )
        snapshot_ref = system_map_snapshot_ref(
            created_at=timestamp,
            graph=graph,
            opportunities=opportunities,
            source_refs=source_refs,
        )
        return SystemMapSnapshot(
            snapshot_ref=snapshot_ref,
            created_at=timestamp,
            graph=graph,
            opportunities=opportunities,
            source_refs=source_refs,
        )

    def _add_ecosystem(
        self,
        nodes: dict[str, SystemMapNode],
        edges: dict[str, SystemMapEdge],
    ) -> None:
        for owner in CanonicalOwnerId:
            node_id = f"domain:{owner.value}"
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=node_id,
                    kind=SystemMapNodeKind.domain,
                    name=owner.value.replace("_", " ").title(),
                    safe_summary="Canonical ecosystem ownership domain.",
                    truth_status=SystemMapTruthStatus.declared,
                    source_refs=("source-ref:eco-000-canonical-ownership",),
                    attributes={"canonical_owner": owner.value},
                ),
            )

        for app in AppId:
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=f"surface:{app.value}",
                    kind=SystemMapNodeKind.surface,
                    name=app.value.replace("_", " ").title(),
                    safe_summary="Control Center product surface in the coherent app ecosystem.",
                    truth_status=SystemMapTruthStatus.declared,
                    source_refs=("source-ref:eco-000-app-portfolio",),
                    attributes={"app_id": app.value},
                ),
            )

        for assignment in CANONICAL_OWNERSHIP_REGISTRY.assignments:
            entity_id = f"entity:{assignment.entity_kind.value}"
            owner_id = f"domain:{assignment.canonical_owner.value}"
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=entity_id,
                    kind=SystemMapNodeKind.entity,
                    name=assignment.entity_kind.value.replace("_", " ").title(),
                    safe_summary="Canonical entity kind with exactly one owning domain.",
                    truth_status=SystemMapTruthStatus.declared,
                    source_refs=("source-ref:eco-000-canonical-ownership",),
                    attributes={
                        "entity_kind": assignment.entity_kind.value,
                        "canonical_owner": assignment.canonical_owner.value,
                    },
                ),
            )
            self._add_edge(
                edges,
                entity_id,
                owner_id,
                SystemMapEdgeKind.owned_by,
                SystemMapEdgeOrigin.canonical,
                "Entity truth is owned by exactly one canonical domain.",
                ("source-ref:eco-000-canonical-ownership",),
            )

        for owner, surfaces in _OWNER_TO_SURFACES.items():
            for surface in surfaces:
                self._add_edge(
                    edges,
                    f"domain:{owner.value}",
                    f"surface:{surface.value}",
                    SystemMapEdgeKind.projects_to,
                    SystemMapEdgeOrigin.canonical,
                    "Canonical domain state may be projected into this product surface.",
                    ("source-ref:eco-000-cross-app-projection",),
                )

    def _add_manifests(
        self,
        nodes: dict[str, SystemMapNode],
        edges: dict[str, SystemMapEdge],
        manifests: Sequence[CapabilityManifest],
    ) -> None:
        known_ids = {manifest.id for manifest in manifests}
        referenced_ids = {
            ref
            for manifest in manifests
            for ref in (*manifest.dependencies, *manifest.conflicts_with)
        }
        for missing_id in sorted(referenced_ids - known_ids):
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=missing_id,
                    kind=SystemMapNodeKind.capability,
                    name=missing_id,
                    safe_summary="Referenced capability is absent from this graph snapshot.",
                    truth_status=SystemMapTruthStatus.missing,
                    source_refs=("source-ref:capability-manifest-registry",),
                    attributes={"placeholder": True},
                ),
            )

        for manifest in manifests:
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=manifest.id,
                    kind=SystemMapNodeKind.capability,
                    name=manifest.name,
                    safe_summary=manifest.description,
                    truth_status=_manifest_truth_status(manifest),
                    source_refs=("source-ref:capability-manifest-registry",),
                    attributes={
                        "capability_kind": manifest.kind.value,
                        "version": manifest.version,
                        "side_effects": manifest.side_effects.value,
                        "risk_level": manifest.risk_level.value,
                        "authority_level": manifest.authority_level.value,
                        "approval_required": bool(manifest.approval_required),
                        "rollback_supported": manifest.rollback_supported,
                        "receipt_required": manifest.receipt_required,
                        "evidence_required": manifest.evidence_required,
                        "input_modes": sorted(manifest.input_modes),
                        "output_modes": sorted(manifest.output_modes),
                        "tags": sorted(manifest.tags),
                    },
                ),
            )
            self._add_edge(
                edges,
                manifest.id,
                "boundary:policy-engine",
                SystemMapEdgeKind.governed_by,
                SystemMapEdgeOrigin.canonical,
                "Capability selection and invocation remain policy-gated.",
            )
            if manifest.approval_required:
                self._add_edge(
                    edges,
                    manifest.id,
                    "boundary:local-approval-authority",
                    SystemMapEdgeKind.governed_by,
                    SystemMapEdgeOrigin.declared,
                    "Capability requires exact-scope local approval validation.",
                )
            if manifest.receipt_required or manifest.evidence_required:
                self._add_edge(
                    edges,
                    manifest.id,
                    "boundary:evidence-and-receipts",
                    SystemMapEdgeKind.evidenced_by,
                    SystemMapEdgeOrigin.declared,
                    "Capability outcome truth requires receipts or evidence.",
                )
            for dependency in sorted(manifest.dependencies):
                self._add_edge(
                    edges,
                    manifest.id,
                    dependency,
                    SystemMapEdgeKind.depends_on,
                    SystemMapEdgeOrigin.declared,
                    "Capability manifest declares this prerequisite.",
                )
            for conflict in sorted(manifest.conflicts_with):
                self._add_edge(
                    edges,
                    manifest.id,
                    conflict,
                    SystemMapEdgeKind.conflicts_with,
                    SystemMapEdgeOrigin.declared,
                    "Capability manifest declares this incompatibility.",
                )

    def _add_authority_mappings(
        self,
        nodes: dict[str, SystemMapNode],
        edges: dict[str, SystemMapEdge],
        mappings: Sequence[AuthorityCapabilityMapping],
    ) -> None:
        for mapping in sorted(mappings, key=lambda item: item.lane_ref):
            domain_value = _enum_text(mapping.domain)
            capability_value = _enum_text(mapping.capability)
            required_mode_value = _enum_text(mapping.required_mode)
            domain_id = f"authority-domain:{domain_value}"
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=domain_id,
                    kind=SystemMapNodeKind.domain,
                    name=domain_value.replace("_", " ").title(),
                    safe_summary="AuthorityLease request domain.",
                    truth_status=SystemMapTruthStatus.declared,
                    source_refs=("source-ref:authority-lane-registry",),
                    attributes={"authority_domain": domain_value},
                ),
            )
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=mapping.lane_ref,
                    kind=SystemMapNodeKind.capability,
                    name=mapping.label,
                    safe_summary=mapping.operator_copy,
                    truth_status=(
                        SystemMapTruthStatus.blocked
                        if mapping.unsupported_adapter_blocks_capability
                        else _mapping_truth_status(mapping.status)
                    ),
                    source_refs=tuple(sorted(mapping.evidence_refs)),
                    attributes={
                        "authority_domain": domain_value,
                        "authority_capability": capability_value,
                        "required_mode": required_mode_value,
                        "lane_status": mapping.status,
                        "unsupported_adapter_blocks_capability": (
                            mapping.unsupported_adapter_blocks_capability
                        ),
                        "unsupported_adapter_refs": sorted(
                            mapping.unsupported_adapter_refs
                        ),
                    },
                ),
            )
            self._add_edge(
                edges,
                mapping.lane_ref,
                domain_id,
                SystemMapEdgeKind.operates_in,
                SystemMapEdgeOrigin.canonical,
                "Capability lane is scoped to this authority domain.",
                tuple(sorted(mapping.evidence_refs)),
            )
            self._add_edge(
                edges,
                mapping.lane_ref,
                "boundary:policy-engine",
                SystemMapEdgeKind.governed_by,
                SystemMapEdgeOrigin.canonical,
                "Authority lane remains subject to current policy evaluation.",
            )
            if required_mode_value != "read_only":
                self._add_edge(
                    edges,
                    mapping.lane_ref,
                    "boundary:local-approval-authority",
                    SystemMapEdgeKind.governed_by,
                    SystemMapEdgeOrigin.canonical,
                    "Non-read-only authority requires an explicit scoped trust mode.",
                )
            if mapping.evidence_refs:
                self._add_edge(
                    edges,
                    mapping.lane_ref,
                    "boundary:evidence-and-receipts",
                    SystemMapEdgeKind.evidenced_by,
                    SystemMapEdgeOrigin.declared,
                    "Authority lane declares evidence references.",
                    tuple(sorted(mapping.evidence_refs)),
                )
            for route in sorted(mapping.route_refs):
                route_id = _surface_node_id("route", route)
                self._add_node(
                    nodes,
                    SystemMapNode(
                        node_id=route_id,
                        kind=SystemMapNodeKind.route,
                        name=route,
                        safe_summary="API exposure declared by an authority capability mapping.",
                        truth_status=_mapping_truth_status(mapping.status),
                        source_refs=(mapping.lane_ref,),
                        attributes={"route_ref": route},
                    ),
                )
                self._add_edge(
                    edges,
                    mapping.lane_ref,
                    route_id,
                    SystemMapEdgeKind.exposed_by,
                    SystemMapEdgeOrigin.declared,
                    "Capability lane is inspectable or invokable through this declared route.",
                )
            for cli in sorted(mapping.cli_refs):
                cli_id = _surface_node_id("cli", cli)
                self._add_node(
                    nodes,
                    SystemMapNode(
                        node_id=cli_id,
                        kind=SystemMapNodeKind.cli,
                        name=cli,
                        safe_summary="CLI inspection path declared by an authority capability mapping.",
                        truth_status=_mapping_truth_status(mapping.status),
                        source_refs=(mapping.lane_ref,),
                        attributes={"cli_ref": cli},
                    ),
                )
                self._add_edge(
                    edges,
                    mapping.lane_ref,
                    cli_id,
                    SystemMapEdgeKind.exposed_by,
                    SystemMapEdgeOrigin.declared,
                    "Capability lane has a repo-local CLI inspection path.",
                )

    def _add_manifest_compatibility(
        self,
        edges: dict[str, SystemMapEdge],
        manifests: Sequence[CapabilityManifest],
    ) -> None:
        consumers_by_mode: dict[str, list[CapabilityManifest]] = defaultdict(list)
        for consumer in manifests:
            for mode in set(consumer.input_modes):
                consumers_by_mode[mode].append(consumer)
        for producer in manifests:
            candidates = {
                consumer.id: consumer
                for mode in producer.output_modes
                for consumer in consumers_by_mode.get(mode, ())
            }
            producer_modes = set(producer.output_modes)
            for consumer in sorted(candidates.values(), key=lambda item: item.id):
                if producer.id == consumer.id:
                    continue
                shared_modes = sorted(producer_modes.intersection(consumer.input_modes))
                if (
                    not shared_modes
                    or consumer.id in producer.conflicts_with
                    or producer.id in consumer.conflicts_with
                ):
                    continue
                self._add_edge(
                    edges,
                    producer.id,
                    consumer.id,
                    SystemMapEdgeKind.compatible_with,
                    SystemMapEdgeOrigin.inferred,
                    "Declared output and input modes are structurally compatible for proposal review.",
                    tuple(f"mode-ref:{mode}" for mode in shared_modes),
                )

    def _add_capability_sources(
        self,
        nodes: dict[str, SystemMapNode],
        edges: dict[str, SystemMapEdge],
        modules: Sequence[str],
    ) -> None:
        if len(modules) != len(set(modules)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_CAPABILITY_SOURCE")
        for module in sorted(modules):
            node_id = f"capability-source:{module}"
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=node_id,
                    kind=SystemMapNodeKind.source,
                    name=module.rsplit(".", 1)[-1].replace("_", " ").title(),
                    safe_summary=(
                        "Registered Python Core source family that constructs typed "
                        "capability manifests."
                    ),
                    truth_status=SystemMapTruthStatus.declared,
                    source_refs=(f"source-ref:python-module:{module}",),
                    attributes={"module_ref": module},
                ),
            )
            self._add_edge(
                edges,
                node_id,
                "boundary:policy-engine",
                SystemMapEdgeKind.governed_by,
                SystemMapEdgeOrigin.canonical,
                "Capability declarations from this source remain policy-gated.",
            )

    def _add_features(
        self,
        nodes: dict[str, SystemMapNode],
        edges: dict[str, SystemMapEdge],
        features: Sequence[SystemMapFeatureDeclaration],
    ) -> None:
        feature_refs = [feature.feature_ref for feature in features]
        if len(feature_refs) != len(set(feature_refs)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_FEATURE")
        for feature in sorted(features, key=lambda item: item.feature_ref):
            source_refs = tuple(sorted(feature.source_refs))
            missing = sorted(set(feature.related_node_ids) - set(nodes))
            if missing:
                raise ValueError(
                    f"SYSTEM_MAP_FEATURE_RELATED_NODE_MISSING:{feature.feature_ref}"
                )
            self._add_node(
                nodes,
                SystemMapNode(
                    node_id=feature.feature_ref,
                    kind=SystemMapNodeKind.workflow,
                    name=feature.name,
                    safe_summary=feature.safe_summary,
                    truth_status=feature.truth_status,
                    source_refs=source_refs,
                    attributes={"catalogued_feature": True},
                ),
            )
            for related_node_id in sorted(feature.related_node_ids):
                self._add_edge(
                    edges,
                    related_node_id,
                    feature.feature_ref,
                    SystemMapEdgeKind.participates_in,
                    SystemMapEdgeOrigin.declared,
                    "Canonical node participates in this catalogued product feature.",
                    source_refs,
                )

    @staticmethod
    def _add_node(nodes: dict[str, SystemMapNode], node: SystemMapNode) -> None:
        existing = nodes.get(node.node_id)
        if existing is not None and existing != node:
            if existing.truth_status == SystemMapTruthStatus.missing:
                nodes[node.node_id] = node
                return
            same_definition = (
                existing.kind == node.kind
                and existing.name == node.name
                and existing.safe_summary == node.safe_summary
                and existing.attributes == node.attributes
            )
            if same_definition:
                merged_status = (
                    existing.truth_status
                    if existing.truth_status == node.truth_status
                    else SystemMapTruthStatus.declared
                )
                nodes[node.node_id] = existing.model_copy(
                    update={
                        "truth_status": merged_status,
                        "source_refs": tuple(
                            sorted(set(existing.source_refs) | set(node.source_refs))
                        ),
                    }
                )
                return
            raise ValueError(f"SYSTEM_MAP_NODE_DEFINITION_CONFLICT:{node.node_id}")
        nodes[node.node_id] = node

    @staticmethod
    def _add_edge(
        edges: dict[str, SystemMapEdge],
        source: str,
        target: str,
        kind: SystemMapEdgeKind,
        origin: SystemMapEdgeOrigin,
        summary: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> None:
        edge = SystemMapEdge(
            edge_id=system_map_edge_id(source, kind, target),
            source_node_id=source,
            target_node_id=target,
            kind=kind,
            origin=origin,
            safe_summary=summary,
            evidence_refs=evidence_refs,
        )
        existing = edges.get(edge.edge_id)
        if existing is not None and existing != edge:
            raise ValueError(f"SYSTEM_MAP_EDGE_DEFINITION_CONFLICT:{edge.edge_id}")
        edges[edge.edge_id] = edge


def discover_system_map_opportunities(
    graph: SystemCapabilityGraph,
    *,
    max_opportunities: int = 30,
) -> tuple[SystemMapOpportunity, ...]:
    """Find bounded proposal candidates without activating or executing anything."""

    if max_opportunities < 0:
        raise ValueError("SYSTEM_MAP_OPPORTUNITY_LIMIT_INVALID")
    node_by_id = {node.node_id: node for node in graph.nodes}
    dependencies: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        if edge.kind == SystemMapEdgeKind.depends_on:
            dependencies[edge.source_node_id].add(edge.target_node_id)

    def has_blocking_prerequisite(node_id: str) -> bool:
        pending = list(dependencies.get(node_id, ()))
        visited: set[str] = set()
        while pending:
            dependency_id = pending.pop()
            if dependency_id in visited:
                continue
            visited.add(dependency_id)
            dependency = node_by_id[dependency_id]
            if dependency.truth_status in {
                SystemMapTruthStatus.blocked,
                SystemMapTruthStatus.missing,
            }:
                return True
            pending.extend(dependencies.get(dependency_id, ()))
        return False

    proposals: dict[str, SystemMapOpportunity] = {}

    for edge in graph.edges:
        if (
            edge.kind != SystemMapEdgeKind.compatible_with
            or edge.origin != SystemMapEdgeOrigin.inferred
        ):
            continue
        source = node_by_id[edge.source_node_id]
        target = node_by_id[edge.target_node_id]
        node_ids = tuple(sorted((source.node_id, target.node_id)))
        blocked = any(
            node.truth_status
            in {SystemMapTruthStatus.blocked, SystemMapTruthStatus.missing}
            for node in (source, target)
        ) or any(has_blocking_prerequisite(node.node_id) for node in (source, target))
        opportunity = _opportunity(
            graph,
            title=_bounded_opportunity_title(
                f"{source.name} to {target.name} workflow"
            ),
            summary=(
                "Typed output and input modes suggest a reviewable composition. "
                "Schema, policy, availability, authority, and outcome proof still require validation."
            ),
            capability_ids=node_ids,
            supporting_edges=(edge.edge_id,),
            gap_refs=(
                "gap-ref:composition-validation",
                "gap-ref:operator-product-review",
            ),
            blocked=blocked,
            confidence=0.72,
        )
        proposals[opportunity.opportunity_ref] = opportunity

    domain_groups: dict[str, list[SystemMapNode]] = defaultdict(list)
    domain_edges: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.kind != SystemMapEdgeKind.operates_in:
            continue
        source = node_by_id[edge.source_node_id]
        if source.kind != SystemMapNodeKind.capability:
            continue
        domain_groups[edge.target_node_id].append(source)
        domain_edges[edge.target_node_id].append(edge.edge_id)

    authority_ladder = ("observe", "read", "draft", "prepare", "write", "execute")
    for domain_id, capabilities in sorted(domain_groups.items()):
        distinct_effects = {
            str(node.attributes.get("authority_capability"))
            for node in capabilities
            if node.attributes.get("authority_capability")
        }
        if len(capabilities) < 2 or len(distinct_effects) < 2:
            continue
        domain = node_by_id[domain_id]
        gap_refs = tuple(
            f"gap-ref:authority-stage:{domain.attributes.get('authority_domain', 'unknown')}:{stage}"
            for stage in authority_ladder
            if stage not in distinct_effects
        )
        blocked = any(
            node.truth_status
            in {SystemMapTruthStatus.blocked, SystemMapTruthStatus.missing}
            for node in capabilities
        )
        opportunity = _opportunity(
            graph,
            title=f"{domain.name} delegated workflow",
            summary=(
                "Multiple exact authority lanes in one domain may support a coherent end-to-end "
                "operator workflow after missing stages and product semantics are reviewed."
            ),
            capability_ids=tuple(sorted(node.node_id for node in capabilities)),
            supporting_edges=tuple(sorted(domain_edges[domain_id])),
            gap_refs=gap_refs,
            blocked=blocked,
            confidence=0.61,
        )
        proposals[opportunity.opportunity_ref] = opportunity

    return tuple(
        sorted(proposals.values(), key=lambda item: item.opportunity_ref)[
            :max_opportunities
        ]
    )


def _opportunity(
    graph: SystemCapabilityGraph,
    *,
    title: str,
    summary: str,
    capability_ids: tuple[str, ...],
    supporting_edges: tuple[str, ...],
    gap_refs: tuple[str, ...],
    blocked: bool,
    confidence: float,
) -> SystemMapOpportunity:
    opportunity_ref = system_map_opportunity_ref(
        graph.graph_ref,
        capability_ids,
        supporting_edges,
        gap_refs,
    )
    return SystemMapOpportunity(
        opportunity_ref=opportunity_ref,
        graph_ref=graph.graph_ref,
        title=title,
        safe_summary=summary,
        capability_node_ids=capability_ids,
        supporting_edge_ids=supporting_edges,
        gap_refs=gap_refs,
        truth_status="blocked" if blocked else "proposal_only",
        confidence=confidence,
    )


def _surface_node_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]
    return f"{kind}:sha256:{digest}"


def _bounded_opportunity_title(value: str) -> str:
    if len(value) <= 180:
        return value
    return f"{value[:177].rstrip()}..."


def _manifest_truth_status(manifest: CapabilityManifest) -> SystemMapTruthStatus:
    declared = str(manifest.metadata.get("system_map_status") or "").strip().lower()
    if declared:
        try:
            return SystemMapTruthStatus(declared)
        except ValueError as exc:
            raise ValueError("SYSTEM_MAP_MANIFEST_STATUS_INVALID") from exc
    if manifest.quality.deprecated:
        return SystemMapTruthStatus.blocked
    return SystemMapTruthStatus.declared


def _mapping_truth_status(status: str) -> SystemMapTruthStatus:
    lowered = status.lower()
    if lowered.startswith("implemented"):
        return SystemMapTruthStatus.implemented
    if "blocked" in lowered or "unsupported" in lowered:
        return SystemMapTruthStatus.blocked
    if lowered.startswith("partial") or lowered.startswith("approval_required"):
        return SystemMapTruthStatus.partial
    if lowered.startswith("proposal"):
        return SystemMapTruthStatus.proposal_only
    if lowered.startswith("planned"):
        return SystemMapTruthStatus.planned
    return SystemMapTruthStatus.unknown


def _enum_text(value: object) -> str:
    enum_value = getattr(value, "value", value)
    return str(enum_value)
