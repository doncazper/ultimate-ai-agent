from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
)
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)
from ultimate_ai_agent.core.runtime_gateway.sensitive_context import (
    SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS,
    SENSITIVE_CONTEXT_CLASSIFIER_REF,
    SENSITIVE_CONTEXT_GUARD_REF,
    validate_sensitive_context_candidate_allowed,
)


RUNTIME_SESSION_SEARCH_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-session-search:v1"
)
RUNTIME_SESSION_SEARCH_ROUTE_REF = "GET /api/runtime/session-search"
RUNTIME_SESSION_SEARCH_CLI_REF = "uaa runtime inspect-session-search"
RUNTIME_SESSION_SEARCH_SNAPSHOT_REF = "session-search-snapshot-ref:runtime:safe-ref"
RUNTIME_SESSION_SEARCH_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-12:session-search"
)

RUNTIME_SESSION_SEARCH_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:session-search-no-raw-transcript-persistence",
    "blocked-authority:session-search-no-raw-prompt-response-exposure",
    "blocked-authority:session-search-no-semantic-provider-call",
    "blocked-authority:session-search-no-embedding-vector-index",
    "blocked-authority:session-search-no-hidden-context-injection",
    "blocked-authority:session-search-no-memory-write",
    "blocked-authority:session-search-no-action-execution",
    "blocked-authority:session-search-no-provider-model-call",
    "blocked-authority:session-search-no-live-web-fetch",
    "blocked-authority:session-search-no-connector-write",
    "blocked-authority:session-search-no-background-indexing",
    "blocked-authority:session-search-no-production-authority",
]


class RuntimeSessionSearchResultKind(str, Enum):
    prepared_turn = "prepared_turn"
    runtime_run = "runtime_run"
    coding_session = "coding_session"
    proof_run = "proof_run"
    operator_loop = "operator_loop"


class RuntimeSessionSearchResult(BaseModel):
    result_ref: str
    result_kind: RuntimeSessionSearchResultKind
    session_ref: str
    run_ref: str | None = None
    title: str
    safe_summary: str
    status: str
    recency_state_ref: str
    source_surface_ref: str
    source_route_ref: str
    attachable_context_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    related_session_refs: list[str] = Field(default_factory=list)
    related_run_refs: list[str] = Field(default_factory=list)
    why_matched_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_transcript_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    semantic_provider_call_performed: bool = False
    embedding_vector_index_used: bool = False
    memory_write_performed: bool = False
    context_injection_authorized: bool = False
    action_execution_authorized: bool = False
    production_authority_enabled: bool = False
    sensitive_context_guard_ref: str = SENSITIVE_CONTEXT_GUARD_REF
    sensitive_context_classifier_ref: str = SENSITIVE_CONTEXT_CLASSIFIER_REF
    sensitive_context_guard_applied: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RuntimeSessionSearchResult":
        for value, field_name in [
            (self.result_ref, "result_ref"),
            (self.session_ref, "session_ref"),
            (self.recency_state_ref, "recency_state_ref"),
            (self.source_surface_ref, "source_surface_ref"),
            (self.attachable_context_ref, "attachable_context_ref"),
            (self.sensitive_context_guard_ref, "sensitive_context_guard_ref"),
            (
                self.sensitive_context_classifier_ref,
                "sensitive_context_classifier_ref",
            ),
        ]:
            validate_execution_ref(value, field_name)
        if self.run_ref is not None:
            validate_execution_ref(self.run_ref, "run_ref")
        for field_name in (
            "evidence_refs",
            "proof_refs",
            "receipt_refs",
            "related_session_refs",
            "related_run_refs",
            "why_matched_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.title, "title"),
            (self.safe_summary, "safe_summary"),
            (self.status, "status"),
            (self.source_route_ref, "source_route_ref"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        denied_flags = {
            "raw_transcript_persisted": self.raw_transcript_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "semantic_provider_call_performed": self.semantic_provider_call_performed,
            "embedding_vector_index_used": self.embedding_vector_index_used,
            "memory_write_performed": self.memory_write_performed,
            "context_injection_authorized": self.context_injection_authorized,
            "action_execution_authorized": self.action_execution_authorized,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_SEARCH_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.sensitive_context_guard_applied:
            raise ValueError("RUNTIME_SESSION_SEARCH_SENSITIVE_GUARD_REQUIRED")
        validate_sensitive_context_candidate_allowed(
            self.attachable_context_ref,
            candidate_kind="attachable-context-ref",
            status="included",
            preview_available=True,
            blocked_authority_refs=self.blocked_authority_refs,
        )
        if not self.why_matched_refs:
            raise ValueError("RUNTIME_SESSION_SEARCH_WHY_MATCHED_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SESSION_SEARCH_BLOCKERS_REQUIRED")
        return self


class RuntimeSessionSearchReadModel(BaseModel):
    schema_version: str = "runtime_session_search.v1"
    contract_ref: str = RUNTIME_SESSION_SEARCH_CONTRACT_REF
    status: str = "read_only_safe_ref_session_run_search"
    snapshot_ref: str = RUNTIME_SESSION_SEARCH_SNAPSHOT_REF
    snapshot_hash_ref: str
    route_ref: str = RUNTIME_SESSION_SEARCH_ROUTE_REF
    cli_ref: str = RUNTIME_SESSION_SEARCH_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    query_ref: str = "query-ref:runtime-session-search:all-safe-refs"
    query_mode: str = "safe_ref_match_only"
    safe_summary: str = (
        "Session and run search returns safe refs and bounded summaries only; "
        "it is separate from durable memory and never injects context by itself."
    )
    sensitive_context_guard_ref: str = SENSITIVE_CONTEXT_GUARD_REF
    sensitive_context_classifier_ref: str = SENSITIVE_CONTEXT_CLASSIFIER_REF
    sensitive_context_blocking_enabled: bool = True
    sensitive_context_bypass_enabled: bool = False
    sensitive_context_bypass_approval_required: bool = True
    sensitive_context_blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS)
    )
    results: list[RuntimeSessionSearchResult]
    result_count: int = 0
    session_ref_count: int = 0
    run_ref_count: int = 0
    attachable_context_ref_count: int = 0
    memory_separation_posture: dict[str, Any] = Field(default_factory=dict)
    raw_transcript_persistence_enabled: bool = False
    raw_prompt_response_exposure_enabled: bool = False
    semantic_provider_call_enabled: bool = False
    embedding_vector_index_enabled: bool = False
    hidden_context_injection_authorized: bool = False
    memory_write_authorized: bool = False
    action_execution_authorized: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "session_transcript_omitted",
                "prompt_response_omitted",
                "provider_payload_omitted",
                "raw_context_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSessionSearchReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.query_ref, "query_ref"),
            (self.sensitive_context_guard_ref, "sensitive_context_guard_ref"),
            (
                self.sensitive_context_classifier_ref,
                "sensitive_context_classifier_ref",
            ),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "sensitive_context_blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.query_mode, "query_mode"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        if self.result_count != len(self.results):
            raise ValueError("RUNTIME_SESSION_SEARCH_RESULT_COUNT_MISMATCH")
        if self.session_ref_count != len(
            {result.session_ref for result in self.results}
        ):
            raise ValueError("RUNTIME_SESSION_SEARCH_SESSION_COUNT_MISMATCH")
        if self.run_ref_count != len(
            {result.run_ref for result in self.results if result.run_ref}
        ):
            raise ValueError("RUNTIME_SESSION_SEARCH_RUN_COUNT_MISMATCH")
        if self.attachable_context_ref_count != len(
            {result.attachable_context_ref for result in self.results}
        ):
            raise ValueError("RUNTIME_SESSION_SEARCH_CONTEXT_COUNT_MISMATCH")
        denied_flags = {
            "raw_transcript_persistence_enabled": (
                self.raw_transcript_persistence_enabled
            ),
            "raw_prompt_response_exposure_enabled": (
                self.raw_prompt_response_exposure_enabled
            ),
            "semantic_provider_call_enabled": self.semantic_provider_call_enabled,
            "embedding_vector_index_enabled": self.embedding_vector_index_enabled,
            "hidden_context_injection_authorized": (
                self.hidden_context_injection_authorized
            ),
            "memory_write_authorized": self.memory_write_authorized,
            "action_execution_authorized": self.action_execution_authorized,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_SEARCH_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.sensitive_context_blocking_enabled:
            raise ValueError("RUNTIME_SESSION_SEARCH_SENSITIVE_GUARD_REQUIRED")
        if self.sensitive_context_bypass_enabled:
            raise ValueError("RUNTIME_SESSION_SEARCH_SENSITIVE_BYPASS_DENIED")
        if not self.sensitive_context_bypass_approval_required:
            raise ValueError("RUNTIME_SESSION_SEARCH_BYPASS_APPROVAL_REQUIRED")
        if set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS) - set(
            self.sensitive_context_blocked_authority_refs
        ):
            raise ValueError("RUNTIME_SESSION_SEARCH_SENSITIVE_BLOCKERS_REQUIRED")
        if RUNTIME_SESSION_SEARCH_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_SESSION_SEARCH_PHASE_PROOF_REQUIRED")
        if not self.memory_separation_posture:
            raise ValueError("RUNTIME_SESSION_SEARCH_MEMORY_POSTURE_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-session-search:{digest}"


def _result(
    *,
    slug: str,
    result_kind: RuntimeSessionSearchResultKind,
    session_ref: str,
    run_ref: str | None,
    title: str,
    safe_summary: str,
    status: str,
    source_surface_ref: str,
    source_route_ref: str,
    evidence_refs: list[str],
    proof_refs: list[str],
    receipt_refs: list[str],
    why_matched_refs: list[str],
) -> RuntimeSessionSearchResult:
    return RuntimeSessionSearchResult(
        result_ref=f"session-search-result-ref:{slug}",
        result_kind=result_kind,
        session_ref=session_ref,
        run_ref=run_ref,
        title=title,
        safe_summary=safe_summary,
        status=status,
        recency_state_ref=f"session-search-recency-ref:{slug}:current",
        source_surface_ref=source_surface_ref,
        source_route_ref=source_route_ref,
        attachable_context_ref=f"context-ref:session-search:{slug}",
        evidence_refs=evidence_refs,
        proof_refs=proof_refs,
        receipt_refs=receipt_refs,
        related_session_refs=[session_ref],
        related_run_refs=[run_ref] if run_ref else [],
        why_matched_refs=why_matched_refs,
        blocked_authority_refs=list(RUNTIME_SESSION_SEARCH_BLOCKED_AUTHORITY_REFS),
    )


def _all_results() -> list[RuntimeSessionSearchResult]:
    return [
        _result(
            slug="prepared-turn-local",
            result_kind=RuntimeSessionSearchResultKind.prepared_turn,
            session_ref="session-ref:prepared-turn:local",
            run_ref="run-ref:turn-run-approval-chain:sample",
            title="Prepared turn readiness",
            safe_summary=(
                "Prepared turn refs show route decision, durable-run readiness, "
                "approval posture, and blocked execution authority."
            ),
            status="read_only_prepared_turn_refs",
            source_surface_ref="surface-ref:runtime:prepared-turn",
            source_route_ref="GET /api/runtime/prepared-turn",
            evidence_refs=["evidence-ref:prepared-turn:local"],
            proof_refs=["proof-ref:prepared-turn:local"],
            receipt_refs=[],
            why_matched_refs=[
                "why-matched-ref:session-search:prepared-turn",
                "why-matched-ref:session-search:durable-run-linkage",
            ],
        ),
        _result(
            slug="runtime-run-events",
            result_kind=RuntimeSessionSearchResultKind.runtime_run,
            session_ref="runtime-session-ref:hermes-agent:sample",
            run_ref="runtime-run-ref:hermes-agent:mock-approval-wait",
            title="Runtime run event preview",
            safe_summary=(
                "Runtime run event refs show approval-wait posture and redacted "
                "event previews without live streaming transport."
            ),
            status="read_only_runtime_event_refs",
            source_surface_ref="surface-ref:runtime:run-events",
            source_route_ref="GET /api/runtime/run-events",
            evidence_refs=["evidence-ref:runtime-run-events:phase-03"],
            proof_refs=["proof-ref:hermes-runtime-adoption:phase-03:run-events"],
            receipt_refs=[],
            why_matched_refs=[
                "why-matched-ref:session-search:runtime-run-event",
                "why-matched-ref:session-search:approval-wait-state",
            ],
        ),
        _result(
            slug="coding-cockpit-session",
            result_kind=RuntimeSessionSearchResultKind.coding_session,
            session_ref="coding-session:mock-fallback",
            run_ref=None,
            title="Coding cockpit session posture",
            safe_summary=(
                "Coding session refs expose workspace, task, diff, proof, terminal, "
                "Git, and preview posture without patch apply or command execution."
            ),
            status="read_only_coding_session_refs",
            source_surface_ref="surface-ref:control-center:coding",
            source_route_ref="GET /control-center/coding/session",
            evidence_refs=["evidence-ref:coding-cockpit:read-model"],
            proof_refs=["proof-ref:coding-cockpit:session-read-model"],
            receipt_refs=[],
            why_matched_refs=[
                "why-matched-ref:session-search:coding-session",
                "why-matched-ref:session-search:workspace-safe-refs",
            ],
        ),
        _result(
            slug="proof-run-detail",
            result_kind=RuntimeSessionSearchResultKind.proof_run,
            session_ref="session-ref:proof:local",
            run_ref="run-ref:mock-fallback:proof",
            title="Proof run detail",
            safe_summary=(
                "Proof refs connect run, evidence, receipts, and blocked authority "
                "without exposing raw logs or granting rollback execution."
            ),
            status="read_only_proof_run_refs",
            source_surface_ref="surface-ref:control-center:proof",
            source_route_ref="GET /control-center/proof/{proof_ref}",
            evidence_refs=["evidence-ref:proof:index"],
            proof_refs=["proof-ref:control-center:local-loop"],
            receipt_refs=["receipt-ref:proof:local-loop"],
            why_matched_refs=[
                "why-matched-ref:session-search:proof-run",
                "why-matched-ref:session-search:receipt-linked",
            ],
        ),
        _result(
            slug="operator-loop",
            result_kind=RuntimeSessionSearchResultKind.operator_loop,
            session_ref="session-ref:founder-loop:local",
            run_ref="run-ref:founder-loop:daily-loop-v1",
            title="Founder/operator loop",
            safe_summary=(
                "Operator loop refs bind Today, Action Inbox, Evidence, Memory, "
                "Trust, and Proof surfaces without turning memory into authority."
            ),
            status="read_only_operator_loop_refs",
            source_surface_ref="surface-ref:control-center:today",
            source_route_ref="GET /control-center/today/summary",
            evidence_refs=["evidence-ref:founder-loop:daily-loop"],
            proof_refs=["proof-ref:founder-loop:daily-loop"],
            receipt_refs=[],
            why_matched_refs=[
                "why-matched-ref:session-search:operator-loop",
                "why-matched-ref:session-search:shared-run-ref",
            ],
        ),
    ]


def _matches_query(result: RuntimeSessionSearchResult, query_ref: str) -> bool:
    if query_ref == "query-ref:runtime-session-search:all-safe-refs":
        return True
    refs = [
        result.result_ref,
        result.session_ref,
        result.run_ref or "",
        result.source_surface_ref,
        result.attachable_context_ref,
        *result.evidence_refs,
        *result.proof_refs,
        *result.receipt_refs,
        *result.related_session_refs,
        *result.related_run_refs,
        *result.why_matched_refs,
    ]
    return query_ref in refs


def build_runtime_session_search_read_model(
    *,
    query_ref: str | None = None,
    limit: int = 20,
) -> RuntimeSessionSearchReadModel:
    resolved_query_ref = query_ref or "query-ref:runtime-session-search:all-safe-refs"
    validate_execution_ref(resolved_query_ref, "query_ref")
    validate_sensitive_context_candidate_allowed(
        resolved_query_ref,
        candidate_kind="query-ref",
        status="included",
        preview_available=True,
        blocked_authority_refs=RUNTIME_SESSION_SEARCH_BLOCKED_AUTHORITY_REFS,
    )
    bounded_limit = max(1, min(int(limit), 25))
    results = [
        result
        for result in _all_results()
        if _matches_query(result, resolved_query_ref)
    ][:bounded_limit]
    payload_for_hash = [
        result.model_dump(mode="json", exclude={"safe_summary", "title"})
        for result in results
    ]
    return RuntimeSessionSearchReadModel(
        snapshot_hash_ref=_hash_payload(payload_for_hash),
        query_ref=resolved_query_ref,
        results=results,
        result_count=len(results),
        session_ref_count=len({result.session_ref for result in results}),
        run_ref_count=len({result.run_ref for result in results if result.run_ref}),
        attachable_context_ref_count=len(
            {result.attachable_context_ref for result in results}
        ),
        memory_separation_posture={
            "status": "separate_from_durable_memory",
            "memory_route_ref": "GET /control-center/memory/workbench",
            "memory_write_performed": False,
            "memory_recall_used_as_truth": False,
            "hidden_context_injection_authorized": False,
            "raw_transcript_indexed": False,
            "operator_selected_attach_required": True,
            "next_safe_action_ref": (
                "next-safe-action-ref:session-search:operator-select-context-ref"
            ),
        },
        blocked_authority_refs=list(RUNTIME_SESSION_SEARCH_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_SESSION_SEARCH_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-12"],
        next_safe_action_refs=[
            "next-safe-action-ref:session-search:inspect-safe-refs",
            "next-safe-action-ref:session-search:attach-selected-context-explicitly",
        ],
    )
