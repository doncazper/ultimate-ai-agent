"""Canonical default assembly for the UAA system map."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ultimate_ai_agent.core.authority import build_existing_lane_authority_mappings
from ultimate_ai_agent.core.capabilities.models import CapabilityManifest
from ultimate_ai_agent.core.system_map.builder import SystemMapBuilder
from ultimate_ai_agent.core.system_map.catalog import (
    SYSTEM_MAP_CAPABILITY_SOURCE_MODULES,
    SYSTEM_MAP_FEATURE_CATALOG,
)
from ultimate_ai_agent.core.system_map.models import SystemMapSnapshot


def build_default_system_map_snapshot(
    *,
    manifests: Iterable[CapabilityManifest] = (),
    created_at: datetime | None = None,
    max_opportunities: int = 30,
) -> SystemMapSnapshot:
    """Build from canonical ownership, authority lanes, and supplied manifests."""

    return SystemMapBuilder().build_snapshot(
        manifests=manifests,
        authority_mappings=build_existing_lane_authority_mappings(),
        feature_declarations=SYSTEM_MAP_FEATURE_CATALOG,
        capability_source_modules=SYSTEM_MAP_CAPABILITY_SOURCE_MODULES,
        include_ecosystem=True,
        created_at=created_at,
        max_opportunities=max_opportunities,
    )
