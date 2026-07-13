import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import time

import pytest
import ultimate_ai_agent.core.execution.mission_completion as completion_module

from tests.test_authority_dispatcher import _constraints
from tests.test_authority_mission_orchestrator import (
    _orchestration_fixture,
)
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionCorruptionError,
    MissionCompletionManifest,
    MissionCompletionStore,
    verify_mission_completion,
)


def test_succeeded_mission_records_source_checked_content_free_completion(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, lease, request, root = _orchestration_fixture(
        tmp_path,
        suffix="completion",
    )

    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-completion:first",
    )
    replay = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-completion:replay",
    )
    manifests = orchestrator.completion_store.list_manifests()

    assert first.status == "succeeded"
    assert first.completion_offline_verified is True
    assert first.completion_manifest_ref == replay.completion_manifest_ref
    assert first.memory_candidate_ref == replay.memory_candidate_ref
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest.completion_ref == first.completion_manifest_ref
    assert manifest.plan_fingerprint_ref == first.plan_fingerprint_ref
    assert manifest.lease_ref == lease.lease_ref
    assert manifest.lease_scope == "mission"
    assert manifest.concurrency_limit == 1
    assert manifest.parallel_execution_performed is False
    assert manifest.status == "succeeded"
    assert len(manifest.step_bindings) == len(request.steps)
    assert len(manifest.dispatch_bindings) == len(request.steps)
    assert len(manifest.budget_bindings) == len(request.steps)
    assert all(item.settlement_status == "settled" for item in manifest.budget_bindings)
    assert all(item.unresolved_cost is False for item in manifest.budget_bindings)
    assert manifest.memory_candidate_posture == "review_required_recall_only"
    assert manifest.memory_truth_authority is False
    assert manifest.context_injection_authorized is False
    assert manifest.signature_present is False
    manifest_only = verify_mission_completion(manifest)
    assert manifest_only.valid is True
    assert manifest_only.source_ledgers_verified is False
    plan_receipt = orchestrator.plan_store.list_receipts()[0]
    _, latest = orchestrator.step_store.snapshot(plan_receipt.plan.topological_step_refs)
    source_verified = verify_mission_completion(
        manifest,
        plan_receipt=plan_receipt,
        lease=lease,
        step_receipts=[
            latest[step_ref] for step_ref in plan_receipt.plan.topological_step_refs
        ],
        dispatch_receipts=[
            receipt
            for receipt in dispatcher.list_receipts()
            if receipt.status == "succeeded"
        ],
        budget_receipts=dispatcher.budget_store.list_receipts(),
        control_receipts=orchestrator.control_store.receipts(),
    )
    assert source_verified.valid is True
    assert source_verified.source_ledgers_verified is True
    duplicate_step_bundle = verify_mission_completion(
        manifest,
        plan_receipt=plan_receipt,
        lease=lease,
        step_receipts=[latest[plan_receipt.plan.topological_step_refs[0]]] * 2,
        dispatch_receipts=[
            receipt
            for receipt in dispatcher.list_receipts()
            if receipt.status == "succeeded"
        ],
        budget_receipts=dispatcher.budget_store.list_receipts(),
        control_receipts=orchestrator.control_store.receipts(),
    )
    assert duplicate_step_bundle.valid is False
    assert duplicate_step_bundle.reason_refs == (
        "reason-ref:mission-completion:source-bundle-invalid",
    )
    assert manifest.integrity_posture == "content_free_hash_chain"
    assert sum(item.adapter_invocation_performed for item in dispatcher.list_receipts()) == 2
    persisted = orchestrator.completion_store.receipts_path.read_text(encoding="utf-8")
    assert str(root) not in persisted
    assert "sensitive body must not persist" not in persisted
    assert "relative_path" not in persisted
    assert "safe_output" not in persisted


def test_completion_offline_verifier_rejects_tamper_and_cross_run_substitution(
    tmp_path: Path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-tamper",
    )
    orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-completion:tamper",
    )
    payload = orchestrator.completion_store.list_manifests()[0].model_dump(mode="json")

    payload["run_ref"] = "run-ref:test-completion:substitution"
    result = verify_mission_completion(payload)

    assert result.valid is False
    assert result.reason_refs == ("reason-ref:mission-completion:contract-invalid",)

    payload = orchestrator.completion_store.list_manifests()[0].model_dump(mode="json")
    payload["step_bindings"][0]["dispatch_receipt_ref"] = (
        "authority-dispatch-receipt-ref:forged"
    )
    assert verify_mission_completion(payload).valid is False

    payload = orchestrator.completion_store.list_manifests()[0].model_dump(mode="json")
    payload["dispatch_bindings"][0]["budget_settlement_receipt_ref"] = (
        "authority-budget-receipt-ref:forged"
    )
    assert verify_mission_completion(payload).valid is False


def test_completion_contract_rejects_missing_redaction_or_authority_claim(
    tmp_path: Path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-redaction",
    )
    orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-completion:redaction",
    )
    payload = orchestrator.completion_store.list_manifests()[0].model_dump(mode="json")
    payload["redactions_applied"] = []
    with pytest.raises(ValueError, match="MISSION_COMPLETION_REQUIRED_REDACTIONS_MISSING"):
        MissionCompletionManifest.model_validate(payload)

    payload = orchestrator.completion_store.list_manifests()[0].model_dump(mode="json")
    payload["memory_truth_authority"] = True
    with pytest.raises(ValueError):
        MissionCompletionManifest.model_validate(payload)


def test_completion_ledger_rejects_symlink_substitution(tmp_path: Path) -> None:
    state_dir = tmp_path / "completion-state"
    state_dir.mkdir()
    target = tmp_path / "target.jsonl"
    target.write_text("", encoding="utf-8")
    ledger = state_dir / "mission_completion_receipts.jsonl"
    ledger.symlink_to(target)

    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_LEDGER_READ_FAILED",
    ):
        MissionCompletionStore(state_dir).list_manifests()


def test_completion_ledger_rejects_hardlink_and_symlinked_state_directory(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "completion-hardlink"
    state_dir.mkdir()
    external = tmp_path / "external-ledger.jsonl"
    external.touch()
    (state_dir / "mission_completion_receipts.jsonl").hardlink_to(external)
    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_LEDGER_REGULAR_FILE_REQUIRED",
    ):
        MissionCompletionStore(state_dir).list_manifests()

    real_state = tmp_path / "real-completion-state"
    real_state.mkdir()
    linked_state = tmp_path / "linked-completion-state"
    linked_state.symlink_to(real_state, target_is_directory=True)
    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_STATE_DIR_INVALID",
    ):
        MissionCompletionStore(linked_state).list_manifests()


def test_completion_ledger_rejects_state_directory_swap_on_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "completion-swap-read"
    state_dir.mkdir()
    moved = tmp_path / "completion-swap-read-original"
    outside = tmp_path / "completion-swap-read-outside"
    outside.mkdir()
    store = MissionCompletionStore(state_dir)
    original_open = completion_module.os.open
    swapped = False

    def swap_before_ledger_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and path == completion_module.MISSION_COMPLETION_LEDGER_FILE
            and dir_fd is not None
        ):
            swapped = True
            state_dir.rename(moved)
            state_dir.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(completion_module.os, "open", swap_before_ledger_open)
    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_STATE_DIR_INVALID",
    ):
        store.list_manifests()


def test_completion_ledger_rejects_state_directory_swap_on_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-swap-append",
        shared_state=True,
    )
    state_dir = orchestrator.completion_store.state_dir
    moved = tmp_path / "completion-swap-append-original"
    outside = tmp_path / "completion-swap-append-outside"
    outside.mkdir()
    original_open = completion_module.os.open
    swapped = False

    def swap_before_ledger_append(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and path == completion_module.MISSION_COMPLETION_LEDGER_FILE
            and dir_fd is not None
            and flags & completion_module.os.O_CREAT
        ):
            swapped = True
            state_dir.rename(moved)
            state_dir.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(completion_module.os, "open", swap_before_ledger_append)
    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_STATE_DIR_INVALID",
    ):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test-completion-swap-append",
        )
    assert not (outside / completion_module.MISSION_COMPLETION_LEDGER_FILE).exists()


def test_one_plan_cannot_fragment_budget_across_two_same_mission_leases(
    tmp_path: Path,
) -> None:
    orchestrator, _, lease_store, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-split-lease",
    )
    second_lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=request.mission_ref,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=_constraints(operation_limit=8),
            decision_reason_ref="reason-ref:test-completion-second-lease",
            safe_summary="Issue a second same-mission lease for denial proof.",
        ),
        idempotency_ref="idempotency-ref:test-completion-second-lease",
    )
    assert second_lease is not None
    assert receipt.status == "issued"
    second = request.steps[1]
    changed_definition = second.definition.model_copy(
        update={"lease_ref": second_lease.lease_ref}
    )
    changed_request = second.request.model_copy(
        update={"lease_ref": second_lease.lease_ref}
    )
    changed = request.model_copy(
        update={
            "steps": [
                request.steps[0],
                second.model_copy(
                    update={
                        "definition": changed_definition,
                        "request": changed_request,
                    }
                ),
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_SINGLE_MISSION_LEASE_REQUIRED",
    ):
        orchestrator.run(
            changed,
            owner_ref="mission-owner-ref:test-completion:split-lease",
        )
    assert not orchestrator.plan_store.list_receipts()
    assert not orchestrator.step_store._load()  # noqa: SLF001
    assert not orchestrator.completion_store.list_manifests()


def test_completion_ledger_history_tamper_fails_closed(tmp_path: Path) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-ledger-tamper",
    )
    orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-completion:ledger-tamper",
    )
    ledger = orchestrator.completion_store.receipts_path
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    payload["evidence_refs"] = ["evidence-ref:tampered"]
    ledger.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(
        MissionCompletionCorruptionError,
        match="MISSION_COMPLETION_LEDGER_HISTORY_INVALID",
    ):
        orchestrator.completion_store.list_manifests()


def test_mission_concurrency_fence_serializes_independent_steps_and_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="completion-concurrency",
        dependency_graph=[[], []],
    )
    adapter = dispatcher.adapters[request.steps[0].request.adapter_ref]
    original_invoke = adapter.invoke
    state_lock = threading.Lock()
    active = 0
    peak = 0
    invocation_count = 0

    def bounded_invoke(dispatch_request):
        nonlocal active, peak, invocation_count
        with state_lock:
            active += 1
            invocation_count += 1
            peak = max(peak, active)
        try:
            time.sleep(0.03)
            return original_invoke(dispatch_request)
        finally:
            with state_lock:
                active -= 1

    monkeypatch.setattr(adapter, "invoke", bounded_invoke)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda owner: orchestrator.run(request, owner_ref=owner),
                (
                    "mission-owner-ref:test-completion-concurrency:first",
                    "mission-owner-ref:test-completion-concurrency:second",
                ),
            )
        )

    assert [result.status for result in results] == ["succeeded", "succeeded"]
    assert peak == 1
    assert invocation_count == 2
    manifests = orchestrator.completion_store.list_manifests()
    assert len(manifests) == 1
    assert manifests[0].concurrency_limit == 1
    assert manifests[0].parallel_execution_performed is False


@pytest.mark.parametrize("cost_posture", ["overage", "unresolved"])
def test_unresolved_or_overage_cost_blocks_verified_completion_without_throwing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cost_posture: str,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix=f"completion-cost-{cost_posture}",
        dependency_graph=[[]],
    )
    adapter = dispatcher.adapters[request.steps[0].request.adapter_ref]
    original_invoke = adapter.invoke

    def changed_cost(dispatch_request):
        result = original_invoke(dispatch_request)
        return result.model_copy(
            update=(
                {
                    "actual_cost_microusd": 1,
                    "actual_cost_ref": "actual-cost-ref:test-completion-overage",
                }
                if cost_posture == "overage"
                else {
                    "actual_cost_microusd": None,
                    "actual_cost_ref": None,
                }
            )
        )

    monkeypatch.setattr(adapter, "invoke", changed_cost)
    result = orchestrator.run(
        request,
        owner_ref=f"mission-owner-ref:test-completion-cost:{cost_posture}",
    )

    assert result.status == "recovery_required"
    assert result.reason_refs == [
        "reason-ref:authority-mission-orchestration:"
        "completion-budget-review-required"
    ]
    assert result.completion_manifest_ref is None
    assert not orchestrator.completion_store.list_manifests()
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 1
