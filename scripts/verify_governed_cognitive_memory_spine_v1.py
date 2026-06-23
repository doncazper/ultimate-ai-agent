#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import verify_fcc_v1_005_memory_review_decisions as fcc_v1_005  # noqa: E402
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
)
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV  # noqa: E402
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "Governed Cognitive Memory Spine V1 verification passed."
SPINE_DOC = "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md"
ROADMAP_DOC = "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md"
HANDOFF_DOC = "docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md"
FCC_DOC = "docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md"
MEMORY_WRITE_POLICY_DOC = "docs/memory/MEMORY_WRITE_POLICY.md"
MEMORY_REVIEW_PROVENANCE_DOC = "docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md"
MEMORY_RETENTION_DOC = "docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md"
DOC_INDEX = "docs/DOCUMENTATION_INDEX.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MEMORY_RECEIPT_ROUTE = (
    "GET",
    "/control-center/memory/review/{candidate_ref}/receipt",
)
MEMORY_L1_INDEX_ROUTE = (
    "GET",
    "/control-center/memory/l1-index",
)
MEMORY_L2_INDEX_ROUTE = (
    "GET",
    "/control-center/memory/l2-index",
)
MEMORY_L3_INDEX_ROUTE = (
    "GET",
    "/control-center/memory/l3-index",
)
MEMORY_DECISION_ROUTES = {
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"),
    ("POST", "/control-center/memory/review/{candidate_ref}/correct"),
    ("POST", "/control-center/memory/review/{candidate_ref}/reject"),
}
FORBIDDEN_CLAIMS = [
    "memory is truth authority",
    "hidden context injection is enabled",
    "automatic memory writes are enabled",
    "connector writes are enabled",
    "crm sync is enabled",
    "provider calls are enabled",
    "production ready memory",
    "public beta memory",
    "phase 5 is implemented",
    "phase 6 is implemented",
    "context packs are implemented",
    "context-pack proposals are implemented",
    "l3 memory is truth authority",
    "l3 context injection is enabled",
    "l3 crm sync is enabled",
    "l3 account sync is enabled",
    "l3 action execution is enabled",
    "embeddings are enabled",
    "vector db is enabled",
    "semantic search is enabled",
    "background indexing is enabled",
    "automatic recall is enabled",
]


def verify(
    root: Path = ROOT,
    *,
    context: ApiVerifierContext | None = None,
    release_surface: dict[str, Any] | None = None,
    route_status: dict[str, Any] | None = None,
    check_files: bool = True,
    check_behavior: bool = True,
) -> list[str]:
    failures: list[str] = []
    context = context or default_api_verifier_context()
    release_surface = release_surface or load_json(RELEASE_SURFACE_PATH)
    route_status = route_status or load_json(ROUTE_STATUS_PATH)
    if check_files:
        _append_required_file_failures(failures, root)
    _append_doc_failures(failures)
    _append_route_metadata_failures(failures, context)
    _append_release_surface_failures(failures, release_surface)
    _append_route_status_failures(failures, route_status)
    failures.extend(fcc_v1_005.verify(context=context, check_files=check_files))
    if check_behavior:
        _append_behavior_failures(failures, context)
    if check_files:
        append_forbidden_claims(
            failures,
            [SPINE_DOC, ROADMAP_DOC, HANDOFF_DOC, FCC_DOC],
            FORBIDDEN_CLAIMS,
        )
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        SPINE_DOC,
        ROADMAP_DOC,
        HANDOFF_DOC,
        FCC_DOC,
        MEMORY_WRITE_POLICY_DOC,
        MEMORY_REVIEW_PROVENANCE_DOC,
        MEMORY_RETENTION_DOC,
        DOC_INDEX,
        "scripts/verify_governed_cognitive_memory_spine_v1.py",
        "scripts/verify_fcc_v1_005_memory_review_decisions.py",
        "tests/test_fcc_v1_005_memory_review_decisions.py",
        "tests/test_governed_memory_l1_hot_index.py",
        "tests/test_governed_memory_l2_factual_graph_temporal_index.py",
        "tests/test_governed_memory_l3_identity_session_preference_commitment.py",
        "src/ultimate_ai_agent/core/memory/l1_index.py",
        "src/ultimate_ai_agent/core/memory/l2_index.py",
        "src/ultimate_ai_agent/core/memory/l3_index.py",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing governed memory spine file: {rel_path}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            SPINE_DOC: [
                "local-first, review-gated memory pipeline",
                "identity/session/preference/commitment layers",
                "L1 hot local memory",
                "L2 factual, graph, and temporal memory",
                "L3 identity and session memory",
                "GET /control-center/memory/review/{candidate_ref}/receipt",
                "GET /control-center/memory/l1-index",
                "GET /control-center/memory/l2-index",
                "GET /control-center/memory/l3-index",
                "reviewed_recall_record_ref",
                "Current Phase 4",
                "implemented read-only representation proposals",
                "Memory is recall, not authority",
                "hidden context injection",
                "deterministic ref projection",
            ],
            ROADMAP_DOC: [
                "Phase 2 L1 Hot Local Memory Index",
                "Implemented read-only derived preview",
                "Phase 3 L2 Factual / Graph / Temporal Indexing",
                "Deterministic ref projection only; no truth authority",
                "Phase 4 L3 Identity / Session / Preference / Commitment Modeling",
                "Implemented read-only representation proposals",
                "identity, session, preference, and commitment modeling",
                "Recall preview and index inspection only; no hidden context injection",
                "GET /control-center/memory/l2-index",
                "GET /control-center/memory/l3-index",
                "provider/model calls",
            ],
            HANDOFF_DOC: [
                "src/ultimate_ai_agent/core/storage/founder_loop.py",
                "There is no `src/ultimate_ai_agent/core/storage.py` file",
                "GET /control-center/memory/review/{candidate_ref}/receipt",
                "GET /control-center/memory/l1-index",
                "GET /control-center/memory/l2-index",
                "GET /control-center/memory/l3-index",
                "next safe phase is Phase 5 Context-Pack",
            ],
            DOC_INDEX: [SPINE_DOC, ROADMAP_DOC, HANDOFF_DOC],
            MEMORY_WRITE_POLICY_DOC: [
                "FCC-V1-005 adds one narrow later exception",
                "reviewed recall-only `LocalMemoryStore`",
                "context injection",
            ],
            MEMORY_REVIEW_PROVENANCE_DOC: [
                "FCC-V1-005 Memory Review decisions preserve this boundary",
                "reviewed recall-only records",
                "No decision stores raw corrected/source content",
            ],
            MEMORY_RETENTION_DOC: [
                "FCC-V1-005 Memory Review decision receipts do not add delete/export execution",
                "Retention, delete, and export execution remain future exact-scoped work",
            ],
        },
    )


def _append_route_metadata_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    route = context.routes_by_key.get(MEMORY_RECEIPT_ROUTE)
    if route is None:
        failures.append("missing governed memory receipt lookup route")
    elif route.get("route_classification") != "local_sensitive":
        failures.append("governed memory receipt lookup route classification drifted")
    elif route.get("idempotency_required") is not False:
        failures.append("governed memory receipt lookup must remain read-only")
    elif route.get("rate_limit_group") is not None:
        failures.append("governed memory receipt lookup must not be targeted rate-limited")

    l1_route = context.routes_by_key.get(MEMORY_L1_INDEX_ROUTE)
    if l1_route is None:
        failures.append("missing governed memory L1 hot local index route")
    elif l1_route.get("route_classification") != "local_sensitive":
        failures.append("governed memory L1 index route classification drifted")
    elif l1_route.get("idempotency_required") is not False:
        failures.append("governed memory L1 index must remain read-only")
    elif l1_route.get("rate_limit_group") is not None:
        failures.append("governed memory L1 index must not be targeted rate-limited")

    l2_route = context.routes_by_key.get(MEMORY_L2_INDEX_ROUTE)
    if l2_route is None:
        failures.append("missing governed memory L2 factual/graph/temporal index route")
    elif l2_route.get("route_classification") != "local_sensitive":
        failures.append("governed memory L2 index route classification drifted")
    elif l2_route.get("idempotency_required") is not False:
        failures.append("governed memory L2 index must remain read-only")
    elif l2_route.get("rate_limit_group") is not None:
        failures.append("governed memory L2 index must not be targeted rate-limited")

    l3_route = context.routes_by_key.get(MEMORY_L3_INDEX_ROUTE)
    if l3_route is None:
        failures.append("missing governed memory L3 identity/session/preference route")
    elif l3_route.get("route_classification") != "local_sensitive":
        failures.append("governed memory L3 index route classification drifted")
    elif l3_route.get("idempotency_required") is not False:
        failures.append("governed memory L3 index must remain read-only")
    elif l3_route.get("rate_limit_group") is not None:
        failures.append("governed memory L3 index must not be targeted rate-limited")

    for key in MEMORY_DECISION_ROUTES:
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing governed memory decision route {key}")
            continue
        if route.get("route_classification") != "mutating_requires_authority":
            failures.append(f"governed memory decision route {key} classification drifted")
        if route.get("idempotency_required") is not True:
            failures.append(f"governed memory decision route {key} must require idempotency")
        if route.get("rate_limit_group") != "memory_review_decision":
            failures.append(f"governed memory decision route {key} rate limit drifted")


def _append_release_surface_failures(
    failures: list[str],
    release_surface: dict[str, Any],
) -> None:
    memory = next(
        (
            route
            for route in release_surface.get("routes", [])
            if route.get("path") == "/memory"
        ),
        None,
    )
    if memory is None:
        failures.append("release surface missing /memory")
        return
    if not _has_route(memory.get("backend_routes", []), MEMORY_RECEIPT_ROUTE):
        failures.append("/memory release surface missing receipt lookup route")
    if not _has_route(memory.get("backend_routes", []), MEMORY_L1_INDEX_ROUTE):
        failures.append("/memory release surface missing L1 index route")
    if not _has_route(memory.get("backend_routes", []), MEMORY_L2_INDEX_ROUTE):
        failures.append("/memory release surface missing L2 index route")
    if not _has_route(memory.get("backend_routes", []), MEMORY_L3_INDEX_ROUTE):
        failures.append("/memory release surface missing L3 index route")
    for proof in [
        "scripts/verify_fcc_v1_005_memory_review_decisions.py",
        "scripts/verify_governed_cognitive_memory_spine_v1.py",
        "tests/test_fcc_v1_005_memory_review_decisions.py",
        "tests/test_governed_memory_l1_hot_index.py",
        "tests/test_governed_memory_l2_factual_graph_temporal_index.py",
        "tests/test_governed_memory_l3_identity_session_preference_commitment.py",
    ]:
        if proof not in set(memory.get("proof_lanes", [])):
            failures.append(f"/memory release surface missing proof lane {proof}")


def _append_route_status_failures(
    failures: list[str],
    route_status: dict[str, Any],
) -> None:
    surface = next(
        (
            item
            for item in route_status.get("surfaces", [])
            if item.get("surface") == "Memory Review"
        ),
        None,
    )
    action = next(
        (
            item
            for item in route_status.get("visible_actions", [])
            if item.get("action_id") == "navigate-memory"
        ),
        None,
    )
    for label, item, key in [
        ("Memory Review surface", surface, "current_backend_routes"),
        ("navigate-memory action", action, "backend_routes"),
    ]:
        if item is None:
            failures.append(f"route status missing {label}")
            continue
        if not _has_route(item.get(key, []), MEMORY_RECEIPT_ROUTE):
            failures.append(f"route status {label} missing receipt lookup route")
        if not _has_route(item.get(key, []), MEMORY_L1_INDEX_ROUTE):
            failures.append(f"route status {label} missing L1 index route")
        if not _has_route(item.get(key, []), MEMORY_L2_INDEX_ROUTE):
            failures.append(f"route status {label} missing L2 index route")
        if not _has_route(item.get(key, []), MEMORY_L3_INDEX_ROUTE):
            failures.append(f"route status {label} missing L3 index route")
        lowered = str(item).lower()
        for snippet in [
            "localmemorystore",
            "reviewed recall-only",
            "l1 hot local memory index",
            "recall preview",
            "l2 factual/graph/temporal",
            "l3 identity/session/preference",
            "representation proposal",
            "deterministic",
            "no automatic memory write",
            "context injection",
            "truth authority",
            "semantic search",
            "context-pack injection",
        ]:
            if snippet not in lowered:
                failures.append(f"route status {label} missing governed memory posture {snippet}")


def _append_behavior_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    old_state_dir = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
    old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
    bearer = "governed-memory-spine-local-bearer"
    auth_headers = {"Authorization": f"Bearer {bearer}"}
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = str(Path(temp_dir) / "founder_loop")
        os.environ[LOCAL_API_BEARER_ENV] = bearer
        try:
            candidate_ref = _candidate_ref(context, auth_headers)
            accept = _post_decision(context, candidate_ref, "accept", auth_headers)
            correct = _post_decision(context, candidate_ref, "correct", auth_headers)
            reject = _post_decision(context, candidate_ref, "reject", auth_headers)
            for label, receipt in [("accept", accept), ("correct", correct)]:
                if not receipt.get("reviewed_recall_record_ref"):
                    failures.append(f"governed memory {label} missing recall record ref")
            if reject.get("reviewed_recall_record_ref"):
                failures.append("governed memory reject must not create recall record ref")
            lookup = context.client.get(
                f"/control-center/memory/review/{candidate_ref}/receipt",
                headers=auth_headers,
            )
            if lookup.status_code != 200:
                failures.append("governed memory receipt lookup failed")
            elif lookup.json().get("data", {}).get("receipt_ref") != reject.get("receipt_ref"):
                failures.append("governed memory receipt lookup did not return latest receipt")
            repo = FounderLoopRepository.from_env()
            records = repo.list_memory_review_recall_records()
            if len(records) < 2:
                failures.append("governed memory accept/correct must create recall records")
            for record in records:
                if record.get("authority_level") != "recall_only":
                    failures.append("governed memory recall record authority drifted")
                if record.get("review_state") != "user_reviewed":
                    failures.append("governed memory recall record review state drifted")
                metadata = record.get("metadata") or {}
                if metadata.get("context_injection_authorized") is not False:
                    failures.append("governed memory recall record enabled context injection")
            l1_response = context.client.get(
                "/control-center/memory/l1-index",
                headers=auth_headers,
            )
            if l1_response.status_code != 200:
                failures.append("governed memory L1 index route failed")
            else:
                l1_data = l1_response.json().get("data", {})
                if l1_data.get("indexed_record_count", 0) < 2:
                    failures.append("governed memory L1 index must preview reviewed recall records")
                for flag in [
                    "context_injection_authorized",
                    "automatic_recall_authorized",
                    "automatic_memory_write_authorized",
                    "embedding_index_enabled",
                    "vector_db_enabled",
                    "semantic_search_enabled",
                    "background_indexing_enabled",
                    "source_truth_authority",
                    "connector_write_authorized",
                    "automatic_action_execution_authorized",
                    "production_authority_enabled",
                ]:
                    if l1_data.get(flag) is not False:
                        failures.append(f"governed memory L1 index enabled {flag}")
                for preview in l1_data.get("previews", []):
                    if not preview.get("match_reasons"):
                        failures.append("governed memory L1 preview missing match reasons")
                    if not preview.get("supporting_ref_groups", {}).get("receipt_refs"):
                        failures.append("governed memory L1 preview missing receipt refs")
                    if preview.get("context_injection_authorized") is not False:
                        failures.append("governed memory L1 preview enabled context injection")
            l2_response = context.client.get(
                "/control-center/memory/l2-index",
                headers=auth_headers,
            )
            if l2_response.status_code != 200:
                failures.append("governed memory L2 index route failed")
            else:
                l2_data = l2_response.json().get("data", {})
                if l2_data.get("fact_count", 0) < 2:
                    failures.append("governed memory L2 index must expose fact refs")
                if l2_data.get("relation_count", 0) < 2:
                    failures.append("governed memory L2 index must expose relation refs")
                if l2_data.get("temporal_count", 0) < 2:
                    failures.append("governed memory L2 index must expose temporal refs")
                for flag in [
                    "truth_authority_enabled",
                    "context_injection_authorized",
                    "automatic_recall_authorized",
                    "automatic_memory_write_authorized",
                    "embedding_index_enabled",
                    "vector_db_enabled",
                    "semantic_search_enabled",
                    "llm_entity_extraction_enabled",
                    "background_indexing_enabled",
                    "context_pack_injection_authorized",
                    "connector_write_authorized",
                    "external_crm_sync_authorized",
                    "account_sync_authorized",
                    "automatic_action_execution_authorized",
                    "production_authority_enabled",
                ]:
                    if l2_data.get(flag) is not False:
                        failures.append(f"governed memory L2 index enabled {flag}")
                if l2_data.get("semantic_extraction_used") is not False:
                    failures.append("governed memory L2 index used semantic extraction")
                for collection in ["facts", "graph_relations", "temporal_items"]:
                    for item in l2_data.get(collection, []):
                        if not item.get("derivation_reasons"):
                            failures.append(f"governed memory L2 {collection} item missing derivation reasons")
                        if not item.get("memory_record_ref"):
                            failures.append(f"governed memory L2 {collection} item missing memory record ref")
                        if not item.get("source_refs"):
                            failures.append(f"governed memory L2 {collection} item missing source refs")
                        if not item.get("evidence_refs"):
                            failures.append(f"governed memory L2 {collection} item missing evidence refs")
                        if not item.get("receipt_refs"):
                            failures.append(f"governed memory L2 {collection} item missing receipt refs")
                        if item.get("truth_authority_enabled") is not False:
                            failures.append(f"governed memory L2 {collection} item enabled truth authority")
                        if item.get("context_injection_authorized") is not False:
                            failures.append(f"governed memory L2 {collection} item enabled context injection")
            l3_response = context.client.get(
                "/control-center/memory/l3-index",
                headers=auth_headers,
            )
            if l3_response.status_code != 200:
                failures.append("governed memory L3 index route failed")
            else:
                l3_data = l3_response.json().get("data", {})
                if l3_data.get("source_l2_fact_count", 0) < 2:
                    failures.append("governed memory L3 index must source L2 fact refs")
                if l3_data.get("item_count", 0) < 2:
                    failures.append("governed memory L3 index must expose representation proposal refs")
                for flag in [
                    "truth_authority_enabled",
                    "crm_truth_authority_enabled",
                    "context_injection_authorized",
                    "automatic_recall_authorized",
                    "automatic_memory_write_authorized",
                    "embedding_index_enabled",
                    "vector_db_enabled",
                    "semantic_search_enabled",
                    "llm_extraction_enabled",
                    "background_indexing_enabled",
                    "context_pack_injection_authorized",
                    "phase5_context_pack_proposals_enabled",
                    "phase6_execution_hooks_enabled",
                    "connector_write_authorized",
                    "external_crm_sync_authorized",
                    "account_sync_authorized",
                    "automatic_action_execution_authorized",
                    "production_authority_enabled",
                ]:
                    if l3_data.get(flag) is not False:
                        failures.append(f"governed memory L3 index enabled {flag}")
                if l3_data.get("safe_refs_only") is not True:
                    failures.append("governed memory L3 index must stay safe-ref-only")
                if l3_data.get("representation_proposal_only") is not True:
                    failures.append("governed memory L3 index must stay proposal-only")
                if l3_data.get("deterministic_projection_only") is not True:
                    failures.append("governed memory L3 index must stay deterministic")
                if l3_data.get("semantic_extraction_used") is not False:
                    failures.append("governed memory L3 index used semantic extraction")
                for item in l3_data.get("items", []):
                    if not item.get("supporting_memory_record_refs"):
                        failures.append("governed memory L3 item missing memory record refs")
                    if not item.get("supporting_l1_preview_refs"):
                        failures.append("governed memory L3 item missing L1 preview refs")
                    if not item.get("supporting_l2_item_refs"):
                        failures.append("governed memory L3 item missing L2 item refs")
                    if not item.get("source_refs"):
                        failures.append("governed memory L3 item missing source refs")
                    if not item.get("evidence_refs"):
                        failures.append("governed memory L3 item missing evidence refs")
                    if not item.get("receipt_refs"):
                        failures.append("governed memory L3 item missing receipt refs")
                    if not item.get("derivation_reason_refs"):
                        failures.append("governed memory L3 item missing derivation reason refs")
                    if item.get("review_required") is not True:
                        failures.append("governed memory L3 item must remain review-required")
                    if item.get("truth_authority_enabled") is not False:
                        failures.append("governed memory L3 item enabled truth authority")
                    if item.get("crm_truth_authority_enabled") is not False:
                        failures.append("governed memory L3 item enabled CRM truth authority")
                    if item.get("context_injection_authorized") is not False:
                        failures.append("governed memory L3 item enabled context injection")
                    if item.get("phase5_context_pack_proposals_enabled") is not False:
                        failures.append("governed memory L3 item enabled Phase 5 context packs")
        finally:
            if old_state_dir is None:
                os.environ.pop("UAA_FOUNDER_LOOP_STATE_DIR", None)
            else:
                os.environ["UAA_FOUNDER_LOOP_STATE_DIR"] = old_state_dir
            if old_bearer is None:
                os.environ.pop(LOCAL_API_BEARER_ENV, None)
            else:
                os.environ[LOCAL_API_BEARER_ENV] = old_bearer


def _candidate_ref(context: ApiVerifierContext, auth_headers: dict[str, str]) -> str:
    response = context.client.get("/control-center/memory/review", headers=auth_headers)
    data = response.json().get("data", {}) if response.status_code == 200 else {}
    items = data.get("items") or []
    if not items:
        return "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    return str(
        items[0].get("business_memory_candidate_ref")
        or items[0].get("review_ref")
        or "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )


def _post_decision(
    context: ApiVerifierContext,
    candidate_ref: str,
    decision: str,
    auth_headers: dict[str, str],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "reviewer_ref": f"actor-ref:governed-memory-spine:{decision}",
        "source_refs": ["source-ref:manual-note:governed-memory-spine"],
        "evidence_refs": ["evidence-ref:governed-memory-spine"],
        "metadata_refs": [f"metadata-ref:governed-memory-spine:{decision}"],
    }
    if decision == "correct":
        body["corrected_summary_ref"] = "safe-summary-ref:governed-memory-spine-correction"
    response = context.client.post(
        f"/control-center/memory/review/{candidate_ref}/{decision}",
        json=body,
        headers={
            **auth_headers,
            "x-uaa-idempotency-key": (
                f"idempotency-ref:governed-memory-spine:{decision}"
            )
        },
    )
    if response.status_code != 200:
        return {"error_status": response.status_code, "decision": decision}
    return dict(response.json().get("data", {}))


def _has_route(
    routes: list[dict[str, Any]],
    route_key: tuple[str, str],
) -> bool:
    method, path = route_key
    return any(
        route.get("method") == method and route.get("path") == path
        for route in routes
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
