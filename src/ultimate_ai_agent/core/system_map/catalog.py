"""Canonical feature and capability-source registrations for the system map.

Adding a first-party feature or a module that constructs capability manifests
requires updating this catalog. ``verify_system_map_currentness.py`` enforces
the capability-source half against the repository AST.
"""

from __future__ import annotations

from ultimate_ai_agent.core.system_map.models import (
    SystemMapFeatureDeclaration,
    SystemMapTruthStatus,
)


SYSTEM_MAP_CAPABILITY_SOURCE_MODULES = (
    "ultimate_ai_agent.core.agent_runtime.demo",
    "ultimate_ai_agent.core.capabilities.a2a_gateway",
    "ultimate_ai_agent.core.capabilities.mcp_gateway",
    "ultimate_ai_agent.core.capabilities.registry",
    "ultimate_ai_agent.core.capability_availability.read_model",
    "ultimate_ai_agent.core.communications.matrix_harness.adapter",
    "ultimate_ai_agent.core.communications.matrix_intelligence.adapter",
    "ultimate_ai_agent.core.communications.matrix_messaging.adapter",
    "ultimate_ai_agent.core.communications.matrix_rooms_media.adapter",
    "ultimate_ai_agent.core.communications.matrix_session.adapter",
    "ultimate_ai_agent.core.communications.matrix_sync.adapter",
    "ultimate_ai_agent.core.control_center.founder_loop_mission",
    "ultimate_ai_agent.core.device_capabilities.manifests",
    "ultimate_ai_agent.core.files.manager",
    "ultimate_ai_agent.core.finance.authority",
    "ultimate_ai_agent.core.governed_browser.contracts",
    "ultimate_ai_agent.core.knowledge_dump.store",
    "ultimate_ai_agent.core.providers.credential_validation",
    "ultimate_ai_agent.core.providers.invocation",
    "ultimate_ai_agent.core.sandbox_calculation.adapter",
    "ultimate_ai_agent.core.web_access.firecrawl_cloud",
    "ultimate_ai_agent.core.web_access.firecrawl_markdown",
    "ultimate_ai_agent.core.web_access.searxng_search",
)

SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES = frozenset(
    {"CapabilityManifest", "DeviceCapabilityManifest"}
)


SYSTEM_MAP_FEATURE_CATALOG = (
    SystemMapFeatureDeclaration(
        feature_ref="feature:founder-operator-loop",
        name="Founder Operator Loop",
        safe_summary=(
            "Single-user Today, Inbox, Plans, Actions, Memory, Evidence, and "
            "Settings loop with backend-owned truth and governed actions."
        ),
        truth_status=SystemMapTruthStatus.partial,
        related_node_ids=(
            "surface:today",
            "surface:inbox",
            "surface:plans",
            "surface:action_inbox",
            "surface:memory",
            "surface:evidence",
            "surface:trust_settings",
        ),
        source_refs=("source-ref:founder-command-center-product-spine",),
    ),
    SystemMapFeatureDeclaration(
        feature_ref="feature:coherent-app-ecosystem",
        name="Coherent App Ecosystem",
        safe_summary=(
            "Canonical ownership and projections connect product surfaces without "
            "duplicating source-of-truth state."
        ),
        truth_status=SystemMapTruthStatus.declared,
        related_node_ids=(
            "domain:identity",
            "domain:calendar",
            "domain:tasks",
            "domain:plans",
            "domain:boards",
            "domain:crm",
            "domain:inbox",
            "domain:organizer",
            "domain:governance",
            "domain:memory",
        ),
        source_refs=("source-ref:eco-000-canonical-ownership",),
    ),
    SystemMapFeatureDeclaration(
        feature_ref="feature:governed-authority-graduation",
        name="Governed Authority Graduation",
        safe_summary=(
            "Exact lanes graduate independently through policy, approval, evidence, "
            "safe-disable, rollback, and verification boundaries."
        ),
        truth_status=SystemMapTruthStatus.implemented,
        related_node_ids=(
            "boundary:policy-engine",
            "boundary:local-approval-authority",
            "boundary:evidence-and-receipts",
            "boundary:foundation-gate",
        ),
        source_refs=("source-ref:workspace-invariants",),
    ),
    SystemMapFeatureDeclaration(
        feature_ref="feature:finance-compliance-program",
        name="Finance and Compliance Program",
        safe_summary=(
            "Synthetic-only protected local books are implemented behind exact "
            "policy, approval, and session-lease gates; real-data ingestion, review, "
            "reconciliation, readiness, and sourced obligations remain planned."
        ),
        truth_status=SystemMapTruthStatus.partial,
        related_node_ids=(
            "surface:today",
            "surface:inbox",
            "surface:plans",
            "surface:action_inbox",
            "surface:memory",
            "surface:evidence",
            "boundary:policy-engine",
            "boundary:local-approval-authority",
        ),
        source_refs=("source-ref:finance-compliance-fin000",),
    ),
    SystemMapFeatureDeclaration(
        feature_ref="feature:durable-system-capability-map",
        name="Durable System Capability Map",
        safe_summary=(
            "Content-addressed graph of product truth, capability sources, authority "
            "lanes, dependencies, boundaries, and proposal-only compositions."
        ),
        truth_status=SystemMapTruthStatus.implemented,
        related_node_ids=(
            "boundary:policy-engine",
            "boundary:evidence-and-receipts",
            "boundary:foundation-gate",
        ),
        source_refs=("source-ref:system-capability-map-contract",),
    ),
    SystemMapFeatureDeclaration(
        feature_ref="feature:local-knowledge-dump",
        name="Local Knowledge Dump",
        safe_summary=(
            "Rights-gated local source ingestion, navigable inventory, cited lexical "
            "retrieval, and explicit bounded context preparation."
        ),
        truth_status=SystemMapTruthStatus.implemented,
        related_node_ids=(
            "surface:memory",
            "boundary:policy-engine",
            "boundary:local-approval-authority",
            "boundary:evidence-and-receipts",
        ),
        source_refs=("source-ref:local-knowledge-dump-contract",),
    ),
)
