#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.memory import (  # noqa: E402
    MEMORY_RANKING_BLOCKED_STATE_REFS,
    MEMORY_RANKING_COMPONENT_BOUNDS,
    MEMORY_RANKING_CONTRACT_REF,
    ManualMemoryCandidateRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "FCC-MEM-022 Ranked Retrieval / Recall Tuning verification passed."

DOC_PATH = "docs/control_center/FCC_MEM_022_RANKED_RETRIEVAL_RECALL_TUNING.md"
DOC_INDEX_PATH = "docs/DOCUMENTATION_INDEX.md"
DOCS_README_PATH = "docs/README.md"
CURRENT_BOARD_PATH = "docs/kanban/current_board.md"
ROADMAP_PATH = "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
TRUTH_PACKET_PATH = "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
WORKBENCH_PATH = "src/ultimate_ai_agent/core/memory/workbench.py"
STORAGE_PATH = "src/ultimate_ai_agent/core/storage/founder_loop.py"
MANIFEST_PATH = "src/ultimate_ai_agent/api/manifest.py"
FRONTEND_TYPES_PATH = "apps/control-center/src/api/types.ts"
FRONTEND_PANEL_PATH = "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK_PATH = "apps/control-center/src/mocks/controlCenterData.ts"
TEST_PATH = "tests/test_fcc_mem_022_ranked_retrieval_recall_tuning.py"

REQUIRED_DOC_SNIPPETS = {
    DOC_PATH: [
        "Status: implemented ranked recall read-model slice",
        "FCC-MEM-022",
        "lexical/tag/ref-only",
        "No embeddings, vector DB, semantic provider, model/provider calls, context injection, memory writes, auto-maintenance, or action execution",
        "scripts/verify_fcc_mem_022_ranked_retrieval_recall_tuning.py",
    ],
    DOC_INDEX_PATH: ["FCC-MEM-022", DOC_PATH],
    DOCS_README_PATH: ["Ranked Retrieval / Recall Tuning", DOC_PATH],
    CURRENT_BOARD_PATH: ["FCC-MEM-022 Ranked Retrieval / Recall Tuning", "Done"],
    ROADMAP_PATH: ["FCC-MEM-022` Done: Ranked Retrieval / Recall Tuning"],
    TRUTH_PACKET_PATH: ["FCC-MEM-022 adds deterministic ranked recall diagnostics"],
}

FORBIDDEN_CLAIMS = [
    "semantic search is implemented",
    "vector db is implemented",
    "embeddings are enabled",
    "context injection is authorized",
    "memory ranking writes memory",
    "memory ranking applies maintenance",
    "memory ranking executes actions",
    "production ready",
    "public beta ready",
]

FORBIDDEN_ACTIVE_IMPORTS = [
    "chromadb",
    "qdrant",
    "weaviate",
    "pinecone",
    "faiss",
    "milvus",
    "lancedb",
    "pgvector",
    "sentence_transformers",
    "transformers",
    "openai",
    "anthropic",
    "cohere",
    "langchain",
    "llama_index",
    "requests",
    "httpx",
    "urllib.request",
    "subprocess",
    "selenium",
    "playwright",
]

REQUIRED_MANIFEST_BLOCKERS = [
    "control_center_memory_ranked_retrieval_embeddings",
    "control_center_memory_ranked_retrieval_vector_db",
    "control_center_memory_ranked_retrieval_provider_calls",
    "control_center_memory_ranked_retrieval_context_injection",
    "control_center_memory_ranked_retrieval_memory_writes",
    "control_center_memory_ranked_retrieval_auto_maintenance",
    "control_center_memory_ranked_retrieval_action_execution",
    "control_center_memory_ranked_retrieval_connector_writes",
    "control_center_memory_ranked_retrieval_background_indexing",
    "control_center_memory_ranked_retrieval_truth_authority",
    "control_center_memory_ranked_retrieval_production_authority",
]


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _append_required_file_failures(failures, root)
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [
            DOC_PATH,
            DOC_INDEX_PATH,
            DOCS_README_PATH,
            CURRENT_BOARD_PATH,
            ROADMAP_PATH,
            TRUTH_PACKET_PATH,
            FRONTEND_PANEL_PATH,
        ],
        FORBIDDEN_CLAIMS,
    )
    _append_manifest_failures(failures)
    _append_static_failures(failures)
    _append_behavior_failures(failures, root)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        WORKBENCH_PATH,
        STORAGE_PATH,
        MANIFEST_PATH,
        FRONTEND_TYPES_PATH,
        FRONTEND_PANEL_PATH,
        FRONTEND_MOCK_PATH,
        TEST_PATH,
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-MEM-022 file: {rel_path}")


def _append_manifest_failures(failures: list[str]) -> None:
    manifest = build_api_manifest(app)
    if (
        "control_center_memory_ranked_retrieval_read_model"
        not in manifest.capabilities_declared
    ):
        failures.append("/api/manifest missing ranked retrieval read-model capability")
    for blocked in REQUIRED_MANIFEST_BLOCKERS:
        if blocked not in manifest.capabilities_blocked:
            failures.append(f"/api/manifest missing blocked capability {blocked}")


def _append_static_failures(failures: list[str]) -> None:
    workbench_text = read_text(WORKBENCH_PATH)
    panel_text = read_text(FRONTEND_PANEL_PATH)
    types_text = read_text(FRONTEND_TYPES_PATH)
    mock_text = read_text(FRONTEND_MOCK_PATH)
    test_text = read_text(TEST_PATH)

    for token in [
        "MEMORY_RANKING_CONTRACT_REF",
        "MEMORY_RANKING_COMPONENT_BOUNDS",
        "lexical_tag_ref_only",
        "embedding_search_enabled\": False",
        "vector_db_enabled\": False",
        "semantic_provider_enabled\": False",
        "memory_write_performed\": False",
        "auto_maintenance_performed\": False",
        "action_execution_authorized\": False",
    ]:
        if token not in workbench_text:
            failures.append(f"{WORKBENCH_PATH} missing static token {token}")

    for forbidden in FORBIDDEN_ACTIVE_IMPORTS:
        import_fragment = f"import {forbidden}"
        from_fragment = f"from {forbidden}"
        if import_fragment in workbench_text or from_fragment in workbench_text:
            failures.append(f"{WORKBENCH_PATH} imports forbidden dependency {forbidden}")

    ranking_section = workbench_text.split("def _ranked_memory_payload", 1)[-1]
    for mutation_token in [
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
        "record_memory_review_decision",
        "record_manual_memory_candidate",
        "record_memory_context_pack_action_proposal",
    ]:
        if mutation_token in ranking_section:
            failures.append(f"ranking helper section contains mutation token {mutation_token}")

    for token in [
        "FounderLoopMemoryRankingSummary",
        "rank_components",
        "ranking_blocked_authority_refs",
    ]:
        if token not in types_text:
            failures.append(f"{FRONTEND_TYPES_PATH} missing {token}")

    for token in [
        "Ranked recall diagnostics",
        "Recall rank",
        "Why ranked refs",
        "Rank components",
        "ranking_blocked_authority_refs",
    ]:
        if token not in panel_text and token not in mock_text:
            failures.append(f"frontend missing MEM-022 display token {token}")
    if "<pre" in panel_text:
        failures.append(f"{FRONTEND_PANEL_PATH} renders raw JSON as primary UI")
    if "Quality score" in panel_text:
        failures.append(f"{FRONTEND_PANEL_PATH} still labels ranking as quality score")

    for token in [
        "deterministic",
        "storage_counts",
        "embedding_search_enabled",
        "context_injection_authorized",
        "memory_write_performed",
    ]:
        if token not in test_text:
            failures.append(f"{TEST_PATH} missing test token {token}")


def _append_behavior_failures(failures: list[str], root: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        before_counts = _storage_counts(repo)
        first = repo.memory_workbench(limit=20)
        second = repo.memory_workbench(limit=20)
        if _stable_json(first["ranking"]) != _stable_json(second["ranking"]):
            failures.append("memory workbench ranking is not deterministic")
        if _storage_counts(repo) != before_counts:
            failures.append("memory workbench ranking mutated repository storage")
        _append_ranking_payload_failures(failures, first)

        _record_manual_candidate(repo, "ranked-alpha")
        _record_manual_candidate(repo, "ranked-beta")
        before_query_counts = _storage_counts(repo)
        queried = repo.memory_workbench(
            query_ref="source-ref:manual-note:ranked-alpha",
            limit=20,
        )
        search = repo.memory_search(
            query_ref="source-ref:manual-note:ranked-alpha",
            limit=20,
        )
        if _storage_counts(repo) != before_query_counts:
            failures.append("memory query ranking/search mutated repository storage")
        by_title = {item["title"]: item for item in queried["items"]}
        alpha = by_title.get("ranked-alpha review candidate")
        beta = by_title.get("ranked-beta review candidate")
        if not alpha or not beta:
            failures.append("manual ranked candidates missing from workbench")
        elif int(alpha["rank_score"]) <= int(beta["rank_score"]):
            failures.append("query ref did not improve matching ranked-alpha candidate")
        if search["count"] != 1:
            failures.append("memory search did not keep exact safe-ref filter behavior")


def _append_ranking_payload_failures(
    failures: list[str],
    payload: dict[str, Any],
) -> None:
    ranking = payload["ranking"]
    if ranking["contract_ref"] != MEMORY_RANKING_CONTRACT_REF:
        failures.append("ranking contract ref mismatch")
    if ranking["score_component_bounds"] != MEMORY_RANKING_COMPONENT_BOUNDS:
        failures.append("ranking score component bounds mismatch")
    if ranking["candidate_count"] != len(payload["items"]):
        failures.append("ranking candidate count mismatch")
    included_set = set(ranking.get("included_ranked_refs") or [])
    excluded_set = {
        entry.get("memory_ref")
        for entry in ranking.get("excluded_refs") or []
        if isinstance(entry, dict)
    }
    if included_set.intersection(excluded_set):
        failures.append("ranking included refs overlap excluded refs")
    for blocked_ref in MEMORY_RANKING_BLOCKED_STATE_REFS:
        if blocked_ref not in ranking["blocked_authority_refs"]:
            failures.append(f"ranking missing blocked ref {blocked_ref}")
    for field_name in [
        "embedding_search_enabled",
        "vector_db_enabled",
        "semantic_provider_enabled",
        "context_injection_authorized",
        "memory_write_performed",
        "auto_maintenance_performed",
        "action_execution_authorized",
        "production_authority_enabled",
    ]:
        if ranking.get(field_name) is not False:
            failures.append(f"ranking field {field_name} must be false")
    if not ranking["excluded_refs"]:
        failures.append("ranking missing excluded refs with reason refs")

    for item in payload["items"]:
        components = item.get("rank_components") or {}
        if set(components) != set(MEMORY_RANKING_COMPONENT_BOUNDS):
            failures.append(f"{item.get('memory_ref')} has incomplete rank components")
            continue
        for key, value in components.items():
            if not isinstance(value, int):
                failures.append(f"{item.get('memory_ref')} component {key} is not integer")
            elif not 0 <= value <= MEMORY_RANKING_COMPONENT_BOUNDS[key]:
                failures.append(f"{item.get('memory_ref')} component {key} out of bounds")
        expected_score = min(
            sum(int(value) for value in components.values()),
            sum(MEMORY_RANKING_COMPONENT_BOUNDS.values()),
        )
        if item.get("rank_score") != expected_score:
            failures.append(f"{item.get('memory_ref')} rank score is not deterministic")
        if not item.get("why_ranked_refs"):
            failures.append(f"{item.get('memory_ref')} missing why ranked refs")
        if not item.get("excluded_reason_refs"):
            failures.append(f"{item.get('memory_ref')} missing excluded reason refs")
        elif (
            "rank-include-ref:visible-but-recall-use-blocked"
            not in item.get("included_reason_refs", [])
        ):
            failures.append(
                f"{item.get('memory_ref')} missing visible-but-blocked include reason"
            )


def _storage_counts(repo: FounderLoopRepository) -> dict[str, int]:
    counts = dict(repo.storage_status()["counts"])
    counts["memory_review_recall_records"] = len(
        repo.list_memory_review_recall_records()
    )
    return counts


def _record_manual_candidate(repo: FounderLoopRepository, slug: str) -> None:
    repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"{slug} review candidate",
            safe_summary=f"{slug} safe summary for review only.",
            source_refs=[f"source-ref:manual-note:{slug}"],
            provenance_refs=[f"provenance-ref:manual-note:{slug}"],
            missing_evidence_refs=[f"missing-evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:manual-memory-{slug}",
    )


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
