"""Machine-readable, durable, proposal-only UAA system map."""

from ultimate_ai_agent.core.system_map.builder import (
    SystemMapBuilder,
    discover_system_map_opportunities,
)
from ultimate_ai_agent.core.system_map.catalog import (
    SYSTEM_MAP_CAPABILITY_SOURCE_MODULES,
    SYSTEM_MAP_FEATURE_CATALOG,
    SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES,
)
from ultimate_ai_agent.core.system_map.defaults import build_default_system_map_snapshot
from ultimate_ai_agent.core.system_map.models import (
    SYSTEM_MAP_GRAPH_SCHEMA_VERSION,
    SYSTEM_MAP_SNAPSHOT_SCHEMA_VERSION,
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
)
from ultimate_ai_agent.core.system_map.store import SystemMapSnapshotStore

__all__ = [
    "SYSTEM_MAP_CAPABILITY_SOURCE_MODULES",
    "SYSTEM_MAP_FEATURE_CATALOG",
    "SYSTEM_MAP_GRAPH_SCHEMA_VERSION",
    "SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES",
    "SYSTEM_MAP_SNAPSHOT_SCHEMA_VERSION",
    "SystemCapabilityGraph",
    "SystemMapBuilder",
    "SystemMapEdge",
    "SystemMapEdgeKind",
    "SystemMapEdgeOrigin",
    "SystemMapFeatureDeclaration",
    "SystemMapNode",
    "SystemMapNodeKind",
    "SystemMapOpportunity",
    "SystemMapSnapshot",
    "SystemMapSnapshotStore",
    "SystemMapTruthStatus",
    "build_default_system_map_snapshot",
    "discover_system_map_opportunities",
]
