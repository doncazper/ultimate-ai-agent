from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.memory.governed_context import (
    build_governed_memory_context_manifest,
)
from ultimate_ai_agent.core.memory.l1_index import build_l1_hot_memory_index


MEMORY_RETRIEVAL_BENCHMARK_CONTRACT_REF = (
    "contract-ref:governed-memory-retrieval-benchmark:v1"
)
MEMORY_RETRIEVAL_BENCHMARK_CHECKED_AT = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)


class GovernedMemoryRetrievalBenchmarkResult(BaseModel):
    contract_ref: str = MEMORY_RETRIEVAL_BENCHMARK_CONTRACT_REF
    benchmark_ref: str = "benchmark-ref:governed-memory-retrieval:phase03"
    query_ref: str
    selected_refs: list[str]
    expected_relevant_refs: list[str]
    excluded_refs: list[str]
    precision_at_limit: float = Field(ge=0.0, le=1.0)
    recall_at_limit: float = Field(ge=0.0, le=1.0)
    exclusion_correctness: float = Field(ge=0.0, le=1.0)
    content_free: bool = True
    raw_content_persisted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "GovernedMemoryRetrievalBenchmarkResult":
        if not self.content_free or self.raw_content_persisted:
            raise ValueError("memory retrieval benchmark must remain content-free")
        return self


def _record(
    slug: str,
    *,
    stale_state: str = "none",
    conflict_state: str = "none",
) -> dict[str, Any]:
    return {
        "memory_id": f"benchmark_{slug}",
        "status": "active",
        "review_state": "user_reviewed",
        "authority_level": "recall_only",
        "retention_state": "active",
        "stale_state": stale_state,
        "conflict_state": conflict_state,
        "safe_summary": f"Synthetic benchmark {slug} summary",
        "memory_kind": "structured_fact",
        "epistemic_role": "observation",
        "data_classification": "internal",
        "sensitivity": "project_private",
        "source_refs": [
            {
                "source_ref": f"source-ref:benchmark:{slug}",
                "source_kind": "reviewed_memory_source",
            }
        ],
        "evidence_refs": [f"evidence-ref:benchmark:{slug}"],
        "receipt_refs": [f"receipt-ref:benchmark:{slug}"],
        "event_refs": [],
        "metadata_refs": [],
        "tags": [slug],
        "metadata": {},
        "recall_metadata": {
            "context_pack_eligible": False,
            "injection_priority": 0,
        },
        "confidence_score": 0.9,
        "trust_score": 0.9,
        "created_at": MEMORY_RETRIEVAL_BENCHMARK_CHECKED_AT,
        "expires_at": None,
    }


def run_governed_memory_retrieval_benchmark() -> (
    GovernedMemoryRetrievalBenchmarkResult
):
    index = build_l1_hot_memory_index(
        [
            _record("relevant-alpha"),
            _record("stale-alpha", stale_state="stale"),
            _record("conflict-alpha", conflict_state="possible_conflict"),
            _record("unrelated-beta"),
        ],
        safe_query="relevant alpha",
        checked_at=MEMORY_RETRIEVAL_BENCHMARK_CHECKED_AT,
        limit=4,
    )
    manifest = build_governed_memory_context_manifest(
        l1_index=index,
        query_ref=index.query_ref,
        checked_at=MEMORY_RETRIEVAL_BENCHMARK_CHECKED_AT,
        max_items=2,
        max_tokens=512,
    )
    selected_refs = [selection.memory_ref for selection in manifest.selections]
    expected_refs = ["memory-record-ref:benchmark_relevant-alpha"]
    expected_excluded = {
        "memory-record-ref:benchmark_stale-alpha",
        "memory-record-ref:benchmark_conflict-alpha",
    }
    selected_relevant = len(set(selected_refs).intersection(expected_refs))
    precision = selected_relevant / len(selected_refs) if selected_refs else 0.0
    recall = selected_relevant / len(expected_refs)
    excluded_refs = [exclusion.memory_ref for exclusion in manifest.exclusions]
    exclusion_correctness = len(expected_excluded.intersection(excluded_refs)) / len(
        expected_excluded
    )
    return GovernedMemoryRetrievalBenchmarkResult(
        query_ref=str(index.safe_query_ref),
        selected_refs=selected_refs,
        expected_relevant_refs=expected_refs,
        excluded_refs=excluded_refs,
        precision_at_limit=precision,
        recall_at_limit=recall,
        exclusion_correctness=exclusion_correctness,
    )


__all__ = [
    "MEMORY_RETRIEVAL_BENCHMARK_CHECKED_AT",
    "MEMORY_RETRIEVAL_BENCHMARK_CONTRACT_REF",
    "GovernedMemoryRetrievalBenchmarkResult",
    "run_governed_memory_retrieval_benchmark",
]
