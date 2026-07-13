from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path

import pytest

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    ManualMemoryCandidateRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
    build_governed_memory_context_manifest,
    run_governed_memory_retrieval_benchmark,
)
from ultimate_ai_agent.core.memory.l1_index import build_l1_hot_memory_index
from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
)
from ultimate_ai_agent.core.memory.local_store import LocalMemoryStore
from ultimate_ai_agent.core.memory.provider import MemoryProviderWriteRequest
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageError,
)
from ultimate_ai_agent.core.time import utc_now
import ultimate_ai_agent.core.storage.founder_loop as founder_loop_module


def _lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:phase03-memory-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.memory: [AuthorityCapability.write]},
        safe_summary="Phase 03 exact reviewed memory write test lease.",
    )


def _request(**updates: object) -> MemoryReviewDecisionRequest:
    payload: dict[str, object] = {
        "reviewer_ref": "actor-ref:phase03-local-operator",
        "source_refs": ["source-ref:manual-note:phase03"],
        "evidence_refs": ["evidence-ref:manual-note:phase03"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    payload.update(updates)
    return MemoryReviewDecisionRequest(**payload)


def _candidate(repo: FounderLoopRepository, slug: str) -> dict[str, object]:
    return repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"{slug} governed candidate",
            safe_summary=f"{slug} bounded reviewed summary.",
            source_refs=[f"source-ref:manual-note:{slug}"],
            provenance_refs=[f"provenance-ref:manual-note:{slug}"],
            evidence_refs=[f"evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:phase03-candidate:{slug}",
    )


def _record(slug: str, **updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "memory_id": f"mem_{slug}",
        "status": "active",
        "review_state": "user_reviewed",
        "authority_level": "recall_only",
        "retention_state": "active",
        "stale_state": "none",
        "conflict_state": "none",
        "safe_summary": f"{slug} synthetic reviewed summary",
        "summary": None,
        "memory_kind": "structured_fact",
        "epistemic_role": "observation",
        "data_classification": "internal",
        "sensitivity": "project_private",
        "source_refs": [
            {
                "source_ref": f"source-ref:synthetic:{slug}",
                "source_kind": "reviewed_memory_source",
            }
        ],
        "evidence_refs": [f"evidence-ref:synthetic:{slug}"],
        "receipt_refs": [f"receipt-ref:synthetic:{slug}"],
        "event_refs": [],
        "metadata_refs": [],
        "tags": [slug],
        "metadata": {},
        "recall_metadata": {
            "context_pack_eligible": False,
            "injection_priority": 0,
        },
        "confidence_score": 0.8,
        "trust_score": 0.8,
        "created_at": utc_now(),
        "expires_at": None,
    }
    payload.update(updates)
    return payload


def test_l1_fails_closed_for_stale_conflict_expiry_and_unknown_posture() -> None:
    checked_at = utc_now()
    records = [
        _record("eligible"),
        _record("stale", stale_state="stale"),
        _record("conflict", conflict_state="possible_conflict"),
        _record("expired", expires_at=checked_at - timedelta(seconds=1)),
        _record("unknown", stale_state=None),
    ]

    index = build_l1_hot_memory_index(records, checked_at=checked_at, limit=20)

    assert [preview.memory_record_ref for preview in index.previews] == [
        "memory-record-ref:mem_eligible"
    ]
    assert index.skipped_record_reasons == {
        "memory-record-ref:mem_conflict": "excluded-reason-ref:l1-memory:conflict",
        "memory-record-ref:mem_expired": "excluded-reason-ref:l1-memory:expired",
        "memory-record-ref:mem_stale": "excluded-reason-ref:l1-memory:stale",
        "memory-record-ref:mem_unknown": "excluded-reason-ref:l1-memory:stale",
    }


def test_l1_preserves_unique_exclusions_for_multiple_unsafe_records() -> None:
    first = _record("unsafe-first")
    second = _record("unsafe-second")
    first["memory_id"] = "raw unsafe identity"
    second["memory_id"] = "another raw unsafe identity"

    index = build_l1_hot_memory_index([first, second], checked_at=utc_now())

    assert index.preview_count == 0
    assert index.skipped_record_count == 2
    assert len(set(index.skipped_record_refs)) == 2


def test_governed_context_reconciles_budgets_and_omits_content() -> None:
    checked_at = utc_now()
    index = build_l1_hot_memory_index(
        [_record("alpha"), _record("beta")],
        checked_at=checked_at,
        limit=20,
    )

    item_limited = build_governed_memory_context_manifest(
        l1_index=index,
        query_ref=None,
        checked_at=checked_at,
        max_items=1,
        max_tokens=1000,
    )
    assert item_limited.selection_count == 1
    assert item_limited.exclusion_count == 1
    assert item_limited.budget.selected_items == 1
    assert item_limited.budget.capacity_excluded_items == 1
    assert item_limited.budget.status == "constrained"
    assert item_limited.budget.used_tokens == sum(
        item.token_estimate for item in item_limited.selections
    )
    assert item_limited.exclusions[0].reason_refs == [
        "excluded-reason-ref:memory-context:item-budget"
    ]
    serialized = json.dumps(item_limited.model_dump(mode="json"), sort_keys=True)
    assert "synthetic reviewed summary" not in serialized
    assert "alpha synthetic" not in serialized

    token_blocked = build_governed_memory_context_manifest(
        l1_index=index,
        query_ref=None,
        checked_at=checked_at,
        max_items=2,
        max_tokens=1,
    )
    assert token_blocked.status == "blocked_no_eligible_context"
    assert token_blocked.selection_count == 0
    assert token_blocked.budget.status == "exhausted"
    assert token_blocked.budget.capacity_excluded_items == 2
    assert all(
        exclusion.reason_refs == ["excluded-reason-ref:memory-context:capacity-budget"]
        for exclusion in token_blocked.exclusions
    )


def test_retrieval_benchmark_is_repeatable_and_content_free() -> None:
    first = run_governed_memory_retrieval_benchmark()
    second = run_governed_memory_retrieval_benchmark()

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.precision_at_limit == 1.0
    assert first.recall_at_limit == 1.0
    assert first.exclusion_correctness == 1.0
    assert first.raw_content_persisted is False
    serialized = json.dumps(first.model_dump(mode="json"), sort_keys=True)
    assert "Synthetic benchmark" not in serialized


def test_context_manifest_binds_query_snapshot_expiry_and_selection_evidence() -> None:
    checked_at = utc_now()
    source_expiry = checked_at + timedelta(minutes=3)
    index = build_l1_hot_memory_index(
        [_record("bound", expires_at=source_expiry)],
        query_ref="source-ref:synthetic:bound",
        checked_at=checked_at,
    )
    manifest = build_governed_memory_context_manifest(
        l1_index=index,
        query_ref="source-ref:synthetic:bound",
        checked_at=checked_at,
    )

    assert manifest.expires_at == source_expiry
    assert manifest.source_index_generated_at == checked_at
    assert manifest.context_receipt_status == "derived_preview_not_persisted"
    with pytest.raises(ValueError, match="query_ref must match"):
        build_governed_memory_context_manifest(
            l1_index=index,
            query_ref="query-ref:phase03:substitution",
            checked_at=checked_at,
        )
    with pytest.raises(ValueError, match="checked_at must match"):
        build_governed_memory_context_manifest(
            l1_index=index,
            query_ref="source-ref:synthetic:bound",
            checked_at=checked_at + timedelta(seconds=1),
        )

    changed = index.model_copy(deep=True)
    changed.previews[0].evidence_refs = ["evidence-ref:synthetic:changed"]
    changed_manifest = build_governed_memory_context_manifest(
        l1_index=changed,
        query_ref="source-ref:synthetic:bound",
        checked_at=checked_at,
    )
    assert (
        changed_manifest.manifest_fingerprint_ref != manifest.manifest_fingerprint_ref
    )


def test_context_manifest_binds_safe_query_and_rejects_contract_drift() -> None:
    checked_at = utc_now()
    index = build_l1_hot_memory_index(
        [_record("safe-query")],
        safe_query="synthetic",
        checked_at=checked_at,
    )
    manifest = build_governed_memory_context_manifest(
        l1_index=index,
        query_ref=index.safe_query_ref,
        checked_at=checked_at,
    )
    assert manifest.query_ref == index.safe_query_ref

    payload = manifest.model_dump(mode="json")
    for field, value in [
        ("schema_version", "governed_memory_context_manifest.v0"),
        ("contract_ref", "contract-ref:wrong-memory-context"),
        ("route_ref", "GET /wrong-memory-context"),
        ("blocked_state_refs", []),
        ("redaction_status", "unredacted"),
    ]:
        with pytest.raises(ValueError):
            type(manifest)(**{**payload, field: value})


def test_concurrent_identical_accept_creates_one_recall_record(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "concurrent-accept")
    candidate_ref = str(candidate["candidate_ref"])

    def accept() -> dict[str, object]:
        return repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="accept",
            request=_request(),
            idempotency_key_ref="idempotency-ref:phase03:concurrent-accept",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(pool.map(lambda _: accept(), range(8)))

    assert len({str(receipt["receipt_ref"]) for receipt in receipts}) == 1
    records = repo.list_memory_review_recall_records()
    assert len(records) == 1
    assert records[0]["status"] == "active"


def test_accept_crash_leaves_prepared_recall_ineligible_and_retry_activates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "crash-before-receipt")
    candidate_ref = str(candidate["candidate_ref"])
    original = repo._write_memory_review_recall_record

    def crash_after_prepare(**kwargs: object) -> str:
        original(**kwargs)  # type: ignore[arg-type]
        raise RuntimeError("injected-after-prepared-recall")

    monkeypatch.setattr(repo, "_write_memory_review_recall_record", crash_after_prepare)
    with pytest.raises(RuntimeError, match="injected-after-prepared-recall"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="accept",
            request=_request(),
            idempotency_key_ref="idempotency-ref:phase03:crash-before-receipt",
        )
    assert repo.memory_l1_hot_index()["preview_count"] == 0
    assert repo.list_memory_review_recall_records()[0]["status"] == "pending_review"
    assert repo.list_memory_review_decisions() == []

    monkeypatch.setattr(repo, "_write_memory_review_recall_record", original)
    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:crash-before-receipt",
    )
    assert receipt["reviewed_recall_record_ref"]
    assert repo.memory_l1_hot_index()["preview_count"] == 1


def test_terminal_projection_failure_keeps_suppressed_recall_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "terminal-crash")
    candidate_ref = str(candidate["candidate_ref"])
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:terminal-crash-accept",
    )

    original_projection = (
        founder_loop_module.update_memory_review_projection_after_decision
    )

    def fail_projection(**_kwargs: object) -> None:
        raise RuntimeError("injected-projection-failure")

    monkeypatch.setattr(
        founder_loop_module,
        "update_memory_review_projection_after_decision",
        fail_projection,
    )
    with pytest.raises(RuntimeError, match="injected-projection-failure"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="reject",
            request=_request(),
            idempotency_key_ref="idempotency-ref:phase03:terminal-crash-reject",
        )
    assert repo.memory_l1_hot_index()["preview_count"] == 0
    assert len(repo.list_memory_review_decisions()) == 1
    prepared = repo._fetch_all(
        """SELECT status, approval_scope_ref, authority_decision_ref,
                  authority_lease_ref, authority_action_ref, authority_lane_ref,
                  authority_scope_ref, safe_disable_ref, rollback_ref
           FROM memory_review_suppression_operations WHERE key_ref = ?""",
        ("idempotency-ref:phase03:terminal-crash-reject",),
    )
    assert prepared[0]["status"] == "prepared"
    assert prepared[0]["authority_lease_ref"] == _lease().lease_ref
    for field in [
        "approval_scope_ref",
        "authority_decision_ref",
        "authority_action_ref",
        "authority_lane_ref",
        "authority_scope_ref",
        "safe_disable_ref",
        "rollback_ref",
    ]:
        assert prepared[0][field]

    monkeypatch.setattr(
        founder_loop_module,
        "update_memory_review_projection_after_decision",
        original_projection,
    )
    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:terminal-crash-reject",
    )
    assert receipt["decision"] == "reject"
    settled = repo._fetch_all(
        "SELECT status FROM memory_review_suppression_operations WHERE key_ref = ?",
        ("idempotency-ref:phase03:terminal-crash-reject",),
    )
    assert settled[0]["status"] == "settled"


def test_lifecycle_suppression_fails_closed_when_lookup_bound_is_exceeded(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "bounded-suppression")
    candidate_ref = str(candidate["candidate_ref"])
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:bounded-suppression-accept",
    )
    store = LocalMemoryStore(storage_path=repo.memory_review_recall_db_path)
    try:
        for index in range(500):
            suffix = f"{index:04d}"
            result = store.put_record(
                MemoryProviderWriteRequest(
                    request_id=f"request-ref:phase03:filler:{suffix}",
                    provider_ref="provider-ref:phase03:filler",
                    memory_kind=MemoryRecordKind.structured_fact,
                    memory_layer=MemoryLayer.record,
                    provider_kind=MemoryProviderKind.local_sqlite,
                    safe_summary=f"Bounded filler record {suffix}.",
                    source_refs=[f"source-ref:phase03:filler:{suffix}"],
                    evidence_refs=[f"evidence-ref:phase03:filler:{suffix}"],
                    receipt_refs=[f"receipt-ref:phase03:filler:{suffix}"],
                    user_reviewed=True,
                    data_classification=MemoryDataClassification.internal,
                    dedup_key=f"dedup-ref:phase03:filler:{suffix}",
                )
            )
            assert result.allowed is True
        assert store.record_count() == 501
    finally:
        store.close()

    with pytest.raises(FounderLoopStorageError, match="LOOKUP_INCOMPLETE"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="expire",
            request=_request(),
            idempotency_key_ref="idempotency-ref:phase03:bounded-suppression-expire",
        )
    assert repo.latest_memory_review_receipt(candidate_ref)["decision"] == "accept"


def test_correction_replaces_lineage_and_receipt_is_content_free(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "correction")
    business_ref = str(candidate["candidate_ref"])
    review_ref = str(candidate["review_ref"])
    repo.record_memory_review_decision(
        candidate_ref=business_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:accept-before-correct",
    )

    corrected = repo.record_memory_review_decision(
        candidate_ref=review_ref,
        decision="correct",
        request=_request(
            corrected_summary_ref="safe-summary-ref:phase03:correction",
            corrected_safe_summary="Phase 03 corrected bounded safe summary.",
        ),
        idempotency_key_ref="idempotency-ref:phase03:correct",
    )

    assert "corrected_safe_summary" not in corrected
    records = repo.list_memory_review_recall_records()
    assert len(records) == 1
    assert records[0]["memory_kind"] == "correction"
    assert "corrected bounded safe summary" in records[0]["safe_summary"]
    assert repo.memory_l1_hot_index()["preview_count"] == 1


def test_concurrent_feedback_applies_once(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "feedback")
    accepted = repo.record_memory_review_decision(
        candidate_ref=str(candidate["candidate_ref"]),
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:feedback-accept",
    )
    memory_ref = str(accepted["reviewed_recall_record_ref"])
    request = MemoryFeedbackRequest(
        memory_record_ref=memory_ref,
        feedback_kind="helpful",
        reviewer_ref="actor-ref:phase03-local-operator",
        source_refs=["source-ref:memory-feedback:phase03"],
        evidence_refs=["evidence-ref:memory-feedback:phase03"],
        blocked_state_refs=MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    )

    def record_feedback() -> dict[str, object]:
        return repo.record_memory_feedback(
            request=request,
            idempotency_key_ref="idempotency-ref:phase03:feedback-once",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(pool.map(lambda _: record_feedback(), range(8)))

    assert len({str(receipt["receipt_ref"]) for receipt in receipts}) == 1
    record = repo.list_memory_review_recall_records()[0]
    assert record["trust_score"] == pytest.approx(0.75)


def test_feedback_crash_recovery_is_append_first_and_authority_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    accepted = repo.record_memory_review_decision(
        candidate_ref=str(_candidate(repo, "feedback-crash")["candidate_ref"]),
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:feedback-crash-accept",
    )
    request = MemoryFeedbackRequest(
        memory_record_ref=str(accepted["reviewed_recall_record_ref"]),
        feedback_kind="helpful",
        reviewer_ref="actor-ref:phase03-local-operator",
        source_refs=["source-ref:memory-feedback:phase03-crash"],
        evidence_refs=["evidence-ref:memory-feedback:phase03-crash"],
        blocked_state_refs=MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    )
    original_persist = founder_loop_module.persist_memory_feedback_receipt
    monkeypatch.setattr(
        founder_loop_module,
        "persist_memory_feedback_receipt",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("injected-feedback-crash")
        ),
    )
    with pytest.raises(RuntimeError, match="injected-feedback-crash"):
        repo.record_memory_feedback(
            request=request,
            idempotency_key_ref="idempotency-ref:phase03:feedback-crash",
        )
    prepared = repo._fetch_all(
        "SELECT * FROM memory_feedback_update_operations WHERE key_ref = ?",
        ("idempotency-ref:phase03:feedback-crash",),
    )[0]
    assert prepared["status"] == "prepared"
    assert prepared["authority_lease_ref"] == _lease().lease_ref
    assert repo.list_memory_review_recall_records()[0]["trust_score"] == pytest.approx(
        0.75
    )

    monkeypatch.setattr(
        founder_loop_module, "persist_memory_feedback_receipt", original_persist
    )
    receipt = repo.record_memory_feedback(
        request=request,
        idempotency_key_ref="idempotency-ref:phase03:feedback-crash",
    )
    assert receipt["authority_lease_ref"] == _lease().lease_ref
    assert repo.list_memory_review_recall_records()[0]["trust_score"] == pytest.approx(
        0.75
    )
    assert (
        repo._fetch_all(
            "SELECT status FROM memory_feedback_update_operations WHERE key_ref = ?",
            ("idempotency-ref:phase03:feedback-crash",),
        )[0]["status"]
        == "settled"
    )


def test_expire_is_idempotent_and_terminal(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[_lease()],
    )
    candidate = _candidate(repo, "expire")
    candidate_ref = str(candidate["candidate_ref"])
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:expire-accept",
    )
    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="expire",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:expire",
    )
    replay = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="expire",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:expire",
    )

    assert replay["receipt_ref"] == receipt["receipt_ref"]
    assert receipt["expire_ref"].startswith("expired-memory-ref:")
    assert repo.memory_l1_hot_index()["preview_count"] == 0
    assert repo.list_memory_review_recall_records()[0]["retention_state"] == "expired"
    with pytest.raises(FounderLoopStorageError, match="TERMINAL_STATE"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="accept",
            request=_request(),
            idempotency_key_ref="idempotency-ref:phase03:reactivate-denied",
        )


@pytest.mark.parametrize(
    ("decision", "receipt_field"),
    [("defer", "defer_ref"), ("merge", "merge_ref"), ("supersede", "supersede_ref")],
)
def test_receipt_only_lifecycle_without_recall_does_not_mint_write_authority(
    tmp_path: Path,
    decision: str,
    receipt_field: str,
) -> None:
    repo = FounderLoopRepository(tmp_path / f"receipt-only-{decision}")
    primary = _candidate(repo, f"primary-{decision}")
    related = _candidate(repo, f"related-{decision}")
    updates: dict[str, object] = {}
    if decision == "merge":
        updates["merge_refs"] = [str(related["candidate_ref"])]
    elif decision == "supersede":
        updates["supersedes_refs"] = [str(related["candidate_ref"])]
    receipt = repo.record_memory_review_decision(
        candidate_ref=str(primary["candidate_ref"]),
        decision=decision,  # type: ignore[arg-type]
        request=_request(**updates),
        idempotency_key_ref=f"idempotency-ref:phase03:receipt-only:{decision}",
    )

    assert receipt[receipt_field]
    assert receipt["suppressed_recall_record_refs"] == []
    assert receipt["authority_decision_ref"] is None
    assert repo.list_memory_review_recall_records() == []


@pytest.mark.parametrize(
    "decision,field", [("merge", "merge_refs"), ("supersede", "supersedes_refs")]
)
def test_related_lifecycle_refs_must_exist_and_cannot_be_self(
    tmp_path: Path,
    decision: str,
    field: str,
) -> None:
    repo = FounderLoopRepository(tmp_path / decision)
    candidate = _candidate(repo, decision)
    candidate_ref = str(candidate["candidate_ref"])
    with pytest.raises(FounderLoopStorageError, match="RELATED_REF_NOT_FOUND"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision=decision,  # type: ignore[arg-type]
            request=_request(**{field: ["memory-review:missing"]}),
            idempotency_key_ref=f"idempotency-ref:phase03:{decision}:missing",
        )
    with pytest.raises(FounderLoopStorageError, match="RELATED_REF_SELF_DENIED"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision=decision,  # type: ignore[arg-type]
            request=_request(**{field: [candidate_ref]}),
            idempotency_key_ref=f"idempotency-ref:phase03:{decision}:self",
        )
