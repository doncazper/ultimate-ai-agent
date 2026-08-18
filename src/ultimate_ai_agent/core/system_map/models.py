"""Typed, content-addressed contracts for UAA's machine-readable system map.

The system map describes product structure and possible compositions. It is a
read-only planning artifact: nodes and edges never grant runtime authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


SYSTEM_MAP_GRAPH_SCHEMA_VERSION = "uaa-system-capability-graph.v1"
SYSTEM_MAP_SNAPSHOT_SCHEMA_VERSION = "uaa-system-capability-snapshot.v1"
_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/#{}-]{2,240}$")
_RAW_LOCAL_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`])(?:~[/\\]|/(?:users|home|private|tmp|etc)(?:/|$)|[a-z]:[\\/])"
)
_FORBIDDEN_FIELD_PARTS = (
    "raw_prompt",
    "raw_response",
    "raw_provider_payload",
    "credential_material",
    "secret_value",
    "local_path",
    "raw_log",
    "raw_content",
)


class SystemMapNodeKind(str, Enum):
    domain = "domain"
    entity = "entity"
    surface = "surface"
    capability = "capability"
    route = "route"
    cli = "cli"
    boundary = "boundary"
    workflow = "workflow"
    source = "source"


class SystemMapTruthStatus(str, Enum):
    implemented = "implemented"
    partial = "partial"
    declared = "declared"
    proposal_only = "proposal_only"
    planned = "planned"
    blocked = "blocked"
    missing = "missing"
    unknown = "unknown"


class SystemMapEdgeKind(str, Enum):
    owned_by = "owned_by"
    owns_legacy = "owns"
    exposed_by = "exposed_by"
    operates_in = "operates_in"
    depends_on = "depends_on"
    conflicts_with = "conflicts_with"
    compatible_with = "compatible_with"
    governed_by = "governed_by"
    evidenced_by = "evidenced_by"
    projects_to = "projects_to"
    participates_in = "participates_in"


class SystemMapEdgeOrigin(str, Enum):
    canonical = "canonical"
    declared = "declared"
    inferred = "inferred"


class _SystemMapModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def validate_safe_content(self) -> "_SystemMapModel":
        _validate_safe_payload(self.model_dump(mode="json"))
        return self


class SystemMapFeatureDeclaration(_SystemMapModel):
    """A product feature that must remain visible in every default map."""

    feature_ref: str
    name: str = Field(..., min_length=1, max_length=240)
    safe_summary: str = Field(..., min_length=1, max_length=600)
    truth_status: SystemMapTruthStatus
    related_node_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = Field(..., min_length=1)
    grants_authority: Literal[False] = False

    @field_validator("feature_ref")
    @classmethod
    def validate_feature_ref(cls, value: str) -> str:
        value = _validate_ref(value, "SYSTEM_MAP_FEATURE_REF_INVALID")
        if not value.startswith("feature:"):
            raise ValueError("SYSTEM_MAP_FEATURE_REF_INVALID")
        return value

    @field_validator("related_node_ids", "source_refs")
    @classmethod
    def validate_feature_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("SYSTEM_MAP_FEATURE_DUPLICATE_REF")
        return tuple(
            _validate_ref(value, "SYSTEM_MAP_FEATURE_ITEM_REF_INVALID")
            for value in values
        )


class SystemMapNode(_SystemMapModel):
    node_id: str
    kind: SystemMapNodeKind
    name: str = Field(..., min_length=1, max_length=240)
    safe_summary: str = Field(..., min_length=1, max_length=600)
    truth_status: SystemMapTruthStatus
    source_refs: tuple[str, ...] = ()
    attributes: dict[str, Any] = Field(default_factory=dict)
    grants_authority: Literal[False] = False

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, value: str) -> str:
        return _validate_ref(value, "SYSTEM_MAP_NODE_ID_INVALID")

    @field_validator("source_refs")
    @classmethod
    def validate_source_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_SOURCE_REF")
        return tuple(
            _validate_ref(value, "SYSTEM_MAP_SOURCE_REF_INVALID") for value in values
        )


class SystemMapEdge(_SystemMapModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    kind: SystemMapEdgeKind
    origin: SystemMapEdgeOrigin
    safe_summary: str = Field(..., min_length=1, max_length=480)
    evidence_refs: tuple[str, ...] = ()
    grants_authority: Literal[False] = False

    @field_validator("edge_id", "source_node_id", "target_node_id")
    @classmethod
    def validate_edge_refs(cls, value: str) -> str:
        return _validate_ref(value, "SYSTEM_MAP_EDGE_REF_INVALID")

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_EVIDENCE_REF")
        return tuple(
            _validate_ref(value, "SYSTEM_MAP_EVIDENCE_REF_INVALID") for value in values
        )

    @model_validator(mode="after")
    def validate_edge_identity(self) -> "SystemMapEdge":
        expected = system_map_edge_id(
            self.source_node_id, self.kind, self.target_node_id
        )
        if self.edge_id != expected:
            raise ValueError("SYSTEM_MAP_EDGE_ID_MISMATCH")
        if self.source_node_id == self.target_node_id:
            raise ValueError("SYSTEM_MAP_SELF_EDGE_DENIED")
        return self


class SystemCapabilityGraph(_SystemMapModel):
    schema_version: Literal["uaa-system-capability-graph.v1"] = (
        SYSTEM_MAP_GRAPH_SCHEMA_VERSION
    )
    graph_ref: str
    nodes: tuple[SystemMapNode, ...] = Field(..., min_length=1)
    edges: tuple[SystemMapEdge, ...] = ()

    @field_validator("graph_ref")
    @classmethod
    def validate_graph_ref(cls, value: str) -> str:
        return _validate_ref(value, "SYSTEM_MAP_GRAPH_REF_INVALID")

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "SystemCapabilityGraph":
        node_ids = [node.node_id for node in self.nodes]
        edge_ids = [edge.edge_id for edge in self.edges]
        if node_ids != sorted(node_ids) or edge_ids != sorted(edge_ids):
            raise ValueError("SYSTEM_MAP_CANONICAL_ORDER_REQUIRED")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_NODE")
        if len(edge_ids) != len(set(edge_ids)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_EDGE")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source_node_id not in known or edge.target_node_id not in known:
                raise ValueError("SYSTEM_MAP_EDGE_ENDPOINT_MISSING")
        _validate_dependency_acyclic(self.edges)
        expected = system_map_graph_ref(self.nodes, self.edges)
        if self.graph_ref != expected:
            raise ValueError("SYSTEM_MAP_GRAPH_REF_MISMATCH")
        return self


class SystemMapOpportunity(_SystemMapModel):
    opportunity_ref: str
    graph_ref: str
    title: str = Field(..., min_length=1, max_length=180)
    safe_summary: str = Field(..., min_length=1, max_length=600)
    capability_node_ids: tuple[str, ...] = Field(..., min_length=2, max_length=80)
    supporting_edge_ids: tuple[str, ...] = ()
    gap_refs: tuple[str, ...] = ()
    truth_status: Literal["proposal_only", "blocked"] = "proposal_only"
    confidence: float = Field(..., ge=0, le=1)
    requires_operator_review: Literal[True] = True
    grants_authority: Literal[False] = False

    @field_validator(
        "opportunity_ref",
        "graph_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validate_ref(value, "SYSTEM_MAP_OPPORTUNITY_REF_INVALID")

    @field_validator("capability_node_ids", "supporting_edge_ids", "gap_refs")
    @classmethod
    def validate_ref_lists(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("SYSTEM_MAP_OPPORTUNITY_DUPLICATE_REF")
        return tuple(
            _validate_ref(value, "SYSTEM_MAP_OPPORTUNITY_ITEM_REF_INVALID")
            for value in values
        )

    @model_validator(mode="after")
    def validate_opportunity_identity(self) -> "SystemMapOpportunity":
        current = system_map_opportunity_ref(
            self.graph_ref,
            self.capability_node_ids,
            self.supporting_edge_ids,
            self.gap_refs,
        )
        legacy = _legacy_system_map_opportunity_ref(
            self.graph_ref,
            self.capability_node_ids,
            self.gap_refs,
        )
        if self.opportunity_ref not in {current, legacy}:
            raise ValueError("SYSTEM_MAP_OPPORTUNITY_REF_MISMATCH")
        return self


class SystemMapSnapshot(_SystemMapModel):
    schema_version: Literal["uaa-system-capability-snapshot.v1"] = (
        SYSTEM_MAP_SNAPSHOT_SCHEMA_VERSION
    )
    snapshot_ref: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    graph: SystemCapabilityGraph
    opportunities: tuple[SystemMapOpportunity, ...] = ()
    source_refs: tuple[str, ...] = ()
    read_only: Literal[True] = True
    proposal_only_discovery: Literal[True] = True
    grants_authority: Literal[False] = False

    @field_validator("snapshot_ref")
    @classmethod
    def validate_snapshot_ref(cls, value: str) -> str:
        return _validate_ref(value, "SYSTEM_MAP_SNAPSHOT_REF_INVALID")

    @field_validator("source_refs")
    @classmethod
    def validate_snapshot_sources(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("SYSTEM_MAP_SNAPSHOT_DUPLICATE_SOURCE")
        return tuple(
            _validate_ref(value, "SYSTEM_MAP_SNAPSHOT_SOURCE_INVALID")
            for value in values
        )

    @model_validator(mode="after")
    def validate_snapshot_integrity(self) -> "SystemMapSnapshot":
        if self.created_at.tzinfo is None:
            raise ValueError("SYSTEM_MAP_SNAPSHOT_TIMEZONE_REQUIRED")
        if any(item.graph_ref != self.graph.graph_ref for item in self.opportunities):
            raise ValueError("SYSTEM_MAP_OPPORTUNITY_GRAPH_REF_MISMATCH")
        opportunity_refs = [item.opportunity_ref for item in self.opportunities]
        if opportunity_refs != sorted(opportunity_refs):
            raise ValueError("SYSTEM_MAP_OPPORTUNITY_ORDER_REQUIRED")
        if len(opportunity_refs) != len(set(opportunity_refs)):
            raise ValueError("SYSTEM_MAP_DUPLICATE_OPPORTUNITY")
        expected = system_map_snapshot_ref(
            created_at=self.created_at,
            graph=self.graph,
            opportunities=self.opportunities,
            source_refs=self.source_refs,
        )
        if self.snapshot_ref != expected:
            raise ValueError("SYSTEM_MAP_SNAPSHOT_REF_MISMATCH")
        return self


def system_map_edge_id(
    source_node_id: str,
    kind: SystemMapEdgeKind,
    target_node_id: str,
) -> str:
    payload = f"{source_node_id}|{kind.value}|{target_node_id}".encode("utf-8")
    return f"system-map-edge:{hashlib.sha256(payload).hexdigest()[:32]}"


def system_map_graph_ref(
    nodes: tuple[SystemMapNode, ...],
    edges: tuple[SystemMapEdge, ...],
) -> str:
    payload = {
        "schema_version": SYSTEM_MAP_GRAPH_SCHEMA_VERSION,
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "edges": [edge.model_dump(mode="json") for edge in edges],
    }
    return f"system-map-graph:sha256:{_fingerprint(payload)}"


def system_map_opportunity_ref(
    graph_ref: str,
    capability_node_ids: tuple[str, ...],
    supporting_edge_ids: tuple[str, ...],
    gap_refs: tuple[str, ...],
) -> str:
    payload = {
        "graph_ref": graph_ref,
        "capability_node_ids": capability_node_ids,
        "supporting_edge_ids": supporting_edge_ids,
        "gap_refs": gap_refs,
    }
    return f"system-map-opportunity:sha256:{_fingerprint(payload)}"


def _legacy_system_map_opportunity_ref(
    graph_ref: str,
    capability_node_ids: tuple[str, ...],
    gap_refs: tuple[str, ...],
) -> str:
    """Validate snapshots written by the pre-release v1 prototype."""

    payload = {
        "graph_ref": graph_ref,
        "capability_node_ids": capability_node_ids,
        "gap_refs": gap_refs,
    }
    return f"system-map-opportunity:sha256:{_fingerprint(payload)}"


def system_map_snapshot_ref(
    *,
    created_at: datetime,
    graph: SystemCapabilityGraph,
    opportunities: tuple[SystemMapOpportunity, ...],
    source_refs: tuple[str, ...],
) -> str:
    payload = {
        "schema_version": SYSTEM_MAP_SNAPSHOT_SCHEMA_VERSION,
        "created_at": created_at.isoformat(),
        "graph_ref": graph.graph_ref,
        "opportunities": [item.model_dump(mode="json") for item in opportunities],
        "source_refs": source_refs,
    }
    return f"system-map-snapshot:sha256:{_fingerprint(payload)}"


def _fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_dependency_acyclic(edges: tuple[SystemMapEdge, ...]) -> None:
    dependency_edges = [
        edge for edge in edges if edge.kind == SystemMapEdgeKind.depends_on
    ]
    dependencies: dict[str, set[str]] = {}
    for edge in dependency_edges:
        dependencies.setdefault(edge.source_node_id, set()).add(edge.target_node_id)
        dependencies.setdefault(edge.target_node_id, set())
    active: set[str] = set()
    complete: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in active:
            raise ValueError("SYSTEM_MAP_DEPENDENCY_CYCLE")
        if node_id in complete:
            return
        active.add(node_id)
        for dependency in dependencies.get(node_id, set()):
            visit(dependency)
        active.remove(node_id)
        complete.add(node_id)

    for node_id in sorted(dependencies):
        visit(node_id)


def _validate_ref(value: str, reason: str) -> str:
    if not _REF_RE.fullmatch(value):
        raise ValueError(reason)
    if _RAW_LOCAL_PATH_RE.search(value) or contains_obvious_secret(value):
        raise ValueError(reason)
    return value


def _validate_safe_payload(value: Any, *, field_name: str = "root") -> None:
    lowered = field_name.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_FIELD_PARTS):
        if value not in (None, False, "", (), [], {}):
            raise ValueError("SYSTEM_MAP_RAW_OR_SECRET_FIELD_DENIED")
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_safe_payload(item, field_name=str(key))
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_safe_payload(item, field_name=field_name)
        return
    if isinstance(value, str):
        if _RAW_LOCAL_PATH_RE.search(value) or contains_obvious_secret(value):
            raise ValueError("SYSTEM_MAP_UNSAFE_TEXT_DENIED")
