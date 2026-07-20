from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest

from scripts.verify_governed_browser_queue01_group07 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _lease,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.authority import AuthorityCapability, AuthorityDomain
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedHumanChallengeHandoff,
    ExactGovernedHumanChallengeHandoffRequest,
    ExactGovernedHumanChallengeHandoffResult,
    ExactGovernedHumanChallengeHandoffService,
    ExternalActionAuthorityBinding,
    ExternalActionExecutionRequest,
    ExternalActionTargetKind,
    GovernedHumanChallengeAction,
    GovernedHumanChallengeHandoffReceipt,
    GovernedHumanChallengeHandoffRecipe,
    GovernedHumanChallengeHandoffRecipeRegistry,
    GovernedHumanChallengeKind,
    ExternalActionTransactionConflict,
    build_external_action_approval_request,
    build_governed_human_challenge_handoff_recipe,
    governed_human_challenge_handoff_ref,
    governed_human_challenge_ref,
    governed_human_challenge_schema_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
)
from ultimate_ai_agent.core.time import utc_now


def _rehash_handoff_receipt(payload: dict[str, object]) -> dict[str, object]:
    identity_payload = {
        key: value for key, value in payload.items() if key != "receipt_ref"
    }
    if identity_payload.get("budget_release_ref") is None:
        identity_payload.pop("budget_release_ref", None)
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        identity_payload,
    )
    return payload


def _challenge_context(
    *,
    suffix: str = "human-challenge",
    kind: GovernedHumanChallengeKind = GovernedHumanChallengeKind.mfa,
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
):  # type: ignore[no-untyped-def]
    base = _binding(suffix=suffix, target_kind=target_kind)
    source_observation_ref = stable_governed_browser_ref(
        "browser-observe-output:governed-browser",
        {"kind": "observation", "suffix": suffix},
    )
    visibility_proof_ref = stable_governed_browser_ref(
        "visibility-proof-ref:governed-browser",
        {"kind": "visibility", "suffix": suffix},
    )
    handoff_surface_ref = stable_governed_browser_ref(
        "human-handoff-surface-ref:governed-browser",
        {"kind": "surface", "suffix": suffix},
    )
    created_at = utc_now()
    expires_at = min(
        created_at + timedelta(minutes=5),
        base.start_deadline - timedelta(seconds=1),
    )
    challenge_ref = governed_human_challenge_ref(
        kind=kind,
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        source_observation_ref=source_observation_ref,
        visibility_proof_ref=visibility_proof_ref,
    )
    schema_ref = governed_human_challenge_schema_ref(
        kind=kind,
        challenge_ref=challenge_ref,
    )
    handoff_ref = governed_human_challenge_handoff_ref(
        challenge_ref=challenge_ref,
        human_presence_ref=base.human_presence_ref,
        handoff_surface_ref=handoff_surface_ref,
        expires_at=expires_at,
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.prepare,
            "field_schema_ref": schema_ref,
            "resource_refs": [
                _ref("resource", suffix),
                challenge_ref,
                source_observation_ref,
                visibility_proof_ref,
                handoff_surface_ref,
                handoff_ref,
            ],
        }
    )
    request = _request(binding)
    recipe = build_governed_human_challenge_handoff_recipe(
        request,
        challenge_kind=kind,
        source_observation_ref=source_observation_ref,
        visibility_proof_ref=visibility_proof_ref,
        handoff_surface_ref=handoff_surface_ref,
        created_at=created_at,
        expires_at=expires_at,
    )
    registry = GovernedHumanChallengeHandoffRecipeRegistry([recipe])
    return request, recipe, registry


def _service(
    tmp_path: Path,
    *,
    request,
    registry,
    readiness_provider=None,  # type: ignore[no-untyped-def]
    clock=utc_now,  # type: ignore[no-untyped-def]
):  # type: ignore[no-untyped-def]
    kernel, authority = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness_provider,
    )
    return (
        ExactGovernedHumanChallengeHandoffService(
            registry=registry,
            kernel=kernel,
            clock=clock,
        ),
        authority,
    )


@pytest.mark.parametrize(
    ("kind", "expected_action"),
    [
        (
            GovernedHumanChallengeKind.mfa,
            "complete_mfa_on_external_surface",
        ),
        (
            GovernedHumanChallengeKind.passkey,
            "invoke_passkey_on_external_surface",
        ),
        (
            GovernedHumanChallengeKind.captcha,
            "complete_captcha_on_external_surface",
        ),
    ],
)
def test_registered_human_challenges_prepare_handoff_only(
    tmp_path: Path,
    kind: GovernedHumanChallengeKind,
    expected_action: str,
) -> None:
    request, recipe, registry = _challenge_context(
        suffix=kind.value,
        kind=kind,
    )
    service, _ = _service(
        tmp_path / kind.value,
        request=request,
        registry=registry,
    )

    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )

    assert result.receipt.status == "handoff_ready"
    assert result.receipt.external_action_state == "succeeded"
    assert result.receipt.approval_validation_ref
    assert result.receipt.authority_decision_ref
    assert result.receipt.budget_reservation_ref
    assert result.receipt.budget_settlement_ref
    assert result.handoff is not None
    assert result.handoff.required_human_action == expected_action
    assert result.handoff.human_present is True
    assert result.handoff.human_completion_required is True
    assert result.handoff.challenge_completed is False
    assert result.handoff.challenge_material_returned is False
    assert result.handoff.challenge_response_accepted is False
    assert result.handoff.credential_challenge_handled is False
    assert result.handoff.passkey_operation_performed is False
    assert result.handoff.captcha_solve_performed is False
    assert result.handoff.captcha_bypass_performed is False
    assert result.handoff.browser_opened is False
    assert result.handoff.browser_session_started is False
    assert result.handoff.authentication_performed is False
    assert result.handoff.navigation_performed is False
    assert result.handoff.cookies_used is False
    assert result.handoff.network_call_performed is False
    assert result.handoff.external_mutation_performed is False


def test_handoff_receipt_rejects_rehashed_conflicting_kernel_proofs(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="conflicting-proofs")
    service, _ = _service(tmp_path, request=request, registry=registry)
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    forged = result.receipt.model_dump(mode="json")
    forged["budget_release_ref"] = _ref(
        "budget-release",
        "human-conflicting-proofs",
    )
    forged["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        {
            "transaction_ref": forged["transaction_ref"],
            "intent_ref": forged["intent_ref"],
            "binding_ref": forged["binding_ref"],
            "state": forged["external_action_state"],
            "approval_validation_ref": forged["approval_validation_ref"],
            "authority_decision_ref": forged["authority_decision_ref"],
            "budget_reservation_ref": forged["budget_reservation_ref"],
            "budget_release_ref": forged["budget_release_ref"],
            "budget_settlement_ref": forged["budget_settlement_ref"],
            "evidence_refs": forged["evidence_refs"],
            "reason_refs": forged["reason_refs"],
        },
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="context-required")
    service, _ = _service(tmp_path, request=request, registry=registry)
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "failed",
            "external_action_state": "failed",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": None,
            "budget_settlement_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-human-challenge:handoff-preparation-failed"
            ],
            "replayed": False,
        }
    )
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_non_preflight_rejects_orphan_kernel_proof(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(
        suffix="non-preflight-orphan-proof"
    )
    service, _ = _service(tmp_path, request=request, registry=registry)
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "failed",
            "external_action_state": "failed",
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": _ref(
                "budget-release",
                "handoff-non-preflight-orphan-proof",
            ),
            "budget_settlement_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-human-challenge:handoff-preparation-failed"
            ],
            "replayed": False,
        }
    )
    _rehash_handoff_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_preflight_rejects_orphan_kernel_proof(tmp_path: Path) -> None:
    request, recipe, registry = _challenge_context(suffix="preflight-orphan-proof")
    service, _ = _service(tmp_path, request=request, registry=registry)
    forged = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=(
                "human-challenge-handoff-recipe-ref:governed-browser:unknown"
            ),
        )
    ).receipt.model_dump(mode="json")
    forged["budget_release_ref"] = _ref(
        "budget-release",
        "human-preflight-orphan-proof",
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_PREFLIGHT_EXTERNAL_PROOF_DENIED",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_receipt_rejects_kernel_state_status_mismatch(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="state-status-mismatch")
    service, _ = _service(tmp_path, request=request, registry=registry)
    forged = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    ).receipt.model_dump(mode="json")
    forged["status"] = "failed"
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_RECEIPT_STATE_MISMATCH",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_non_replay_status_rejects_replay_flag(tmp_path: Path) -> None:
    request, recipe, registry = _challenge_context(suffix="replay-status-mismatch")
    service, _ = _service(tmp_path, request=request, registry=registry)
    forged = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    ).receipt.model_dump(mode="json")
    forged["replayed"] = True
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        identity_payload,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_REPLAY_STATUS_MISMATCH",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


@pytest.mark.parametrize(
    "missing_field",
    (
        "external_action_receipt_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
        "evidence_refs",
    ),
)
def test_handoff_replayed_success_requires_complete_kernel_proof(
    tmp_path: Path,
    missing_field: str,
) -> None:
    request, recipe, registry = _challenge_context(suffix="proofless-replay")
    service, _ = _service(tmp_path, request=request, registry=registry)
    exact = ExactGovernedHumanChallengeHandoffRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
    )
    service.prepare(exact)
    forged = service.prepare(exact).receipt.model_dump(mode="json")
    assert forged["status"] == "replayed_content_free"
    forged[missing_field] = [] if missing_field == "evidence_refs" else None
    if missing_field != "external_action_receipt_ref":
        external_payload = {
            "transaction_ref": forged["transaction_ref"],
            "intent_ref": forged["intent_ref"],
            "binding_ref": forged["binding_ref"],
            "state": forged["external_action_state"],
            "approval_validation_ref": forged["approval_validation_ref"],
            "authority_decision_ref": forged["authority_decision_ref"],
            "budget_reservation_ref": forged["budget_reservation_ref"],
            "budget_settlement_ref": forged["budget_settlement_ref"],
            "evidence_refs": forged["evidence_refs"],
            "reason_refs": forged["reason_refs"],
        }
        if forged["budget_release_ref"] is not None:
            external_payload["budget_release_ref"] = forged["budget_release_ref"]
        forged["external_action_receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            external_payload,
        )
    _rehash_handoff_receipt(forged)

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_SUCCESS_KERNEL_PROOF_REQUIRED",
    ):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


def test_handoff_result_rejects_cross_projection_binding(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="result-projection")
    service, _ = _service(tmp_path, request=request, registry=registry)
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert result.handoff is not None
    forged_handoff = ExactGovernedHumanChallengeHandoff.model_validate(
        {
            **result.handoff.model_dump(mode="json"),
            "binding_ref": _ref("binding", "unrelated-handoff-projection"),
        }
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_RECEIPT_MISMATCH",
    ):
        ExactGovernedHumanChallengeHandoffResult(
            receipt=result.receipt,
            handoff=forged_handoff,
        )


def test_handoff_replay_is_content_free_and_at_most_once(tmp_path: Path) -> None:
    request, recipe, registry = _challenge_context(suffix="replay")
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    exact = ExactGovernedHumanChallengeHandoffRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
    )

    first = service.prepare(exact)
    replay = service.prepare(exact)

    assert first.receipt.status == "handoff_ready"
    assert first.handoff is not None
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.replayed is True
    assert replay.handoff is None
    ledger = (tmp_path / "transactions.sqlite3").read_bytes()
    assert recipe.challenge_ref.encode() in ledger
    assert b"challenge_material" not in ledger
    assert b"challenge_response" not in ledger


def test_unknown_recipe_and_approval_identifier_alone_do_not_prepare_handoff(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="authority")
    service, _ = _service(
        tmp_path / "unknown",
        request=request,
        registry=registry,
    )
    unknown = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref="human-challenge-handoff-recipe-ref:governed-browser:unknown",
        )
    )
    assert unknown.receipt.status == "preflight_blocked"
    assert unknown.handoff is None

    ungranted = request.model_copy(
        update={
            "approval_ref": ("approval-ref:governed-human-challenge:identifier-only")
        }
    )
    second_service, _ = _service(
        tmp_path / "approval",
        request=request,
        registry=registry,
    )
    blocked = second_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=ungranted,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert blocked.receipt.status == "transaction_blocked"
    assert blocked.receipt.approval_validation_ref
    assert blocked.receipt.authority_decision_ref is None
    assert blocked.receipt.budget_reservation_ref is None
    assert blocked.handoff is None

    missing_lease_ref = "authority-lease-ref:governed-browser:missing"
    missing_lease_approval_ref = "approval-ref:governed-human-challenge:missing-lease"
    missing_lease_intent_ref = stable_governed_browser_ref(
        "intent-ref:governed-external-action",
        {
            "binding_ref": request.binding.binding_ref,
            "run_ref": request.run_ref,
            "task_ref": request.task_ref,
            "lease_ref": missing_lease_ref,
        },
    )
    missing_lease = ExternalActionExecutionRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "lease_ref": missing_lease_ref,
            "intent_ref": missing_lease_intent_ref,
            "approval_ref": missing_lease_approval_ref,
        }
    )
    lease_service, lease_authority = _service(
        tmp_path / "lease",
        request=request,
        registry=registry,
    )
    approval_request = lease_authority.create_request(
        build_external_action_approval_request(missing_lease)
    )
    lease_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref=missing_lease_approval_ref,
    )
    lease_blocked = lease_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=missing_lease,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert lease_blocked.receipt.status == "transaction_blocked"
    assert lease_blocked.receipt.authority_decision_ref
    assert lease_blocked.receipt.budget_reservation_ref is None
    assert lease_blocked.handoff is None


@pytest.mark.parametrize(
    ("readiness", "reason_suffix"),
    [
        ({"safe_disable": True}, "safe-disable"),
        ({"kill_switch": True}, "kill-switch"),
        ({"ready": False}, "readiness"),
        ({"snapshot_ref": _ref("page-snapshot", "drift")}, "snapshot"),
    ],
)
def test_shared_revalidation_gates_block_before_handoff(
    tmp_path: Path,
    readiness: dict[str, object],
    reason_suffix: str,
) -> None:
    request, recipe, registry = _challenge_context(suffix=reason_suffix)
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        readiness_provider=lambda item: _readiness(item, **readiness),
    )

    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )

    assert result.receipt.status == "transaction_blocked"
    assert result.handoff is None
    assert result.receipt.budget_reservation_ref
    assert result.receipt.budget_release_ref
    assert result.receipt.budget_settlement_ref is None


def test_exact_scope_human_presence_and_real_targets_fail_closed(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="scope")
    drifted_base = _binding(suffix="scope-drift")
    drifted = ExternalActionAuthorityBinding.model_validate(
        {
            **drifted_base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.prepare,
        }
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=_request(drifted),
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert result.receipt.status == "preflight_blocked"
    assert result.handoff is None

    absent = ExternalActionAuthorityBinding.model_validate(
        {**request.binding.model_dump(mode="json"), "human_present": False}
    )
    with pytest.raises(
        ValueError,
        match="HUMAN_PRESENCE_REQUIRED",
    ):
        build_governed_human_challenge_handoff_recipe(
            _request(absent),
            challenge_kind=GovernedHumanChallengeKind.mfa,
            source_observation_ref=recipe.source_observation_ref,
            visibility_proof_ref=recipe.visibility_proof_ref,
            handoff_surface_ref=recipe.handoff_surface_ref,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )

    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _challenge_context(
            suffix="external",
            target_kind=ExternalActionTargetKind.external,
        )


def test_expiry_and_dispatch_revalidation_never_return_handoff(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="expiry")
    expired_service, _ = _service(
        tmp_path / "expired",
        request=request,
        registry=registry,
        clock=lambda: recipe.expires_at + timedelta(seconds=1),
    )
    expired = expired_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert expired.receipt.status == "failed"
    assert expired.handoff is None

    current_time = [recipe.created_at - timedelta(seconds=1)]
    future_service, _ = _service(
        tmp_path / "future",
        request=request,
        registry=registry,
        clock=lambda: current_time[0],
    )
    future = future_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert future.receipt.status == "preflight_blocked"
    assert future.handoff is None
    assert future.receipt.replayed is False
    current_time[0] = recipe.created_at
    valid = future_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert valid.receipt.status == "handoff_ready"
    assert valid.handoff is not None

    exact_expiry_service, _ = _service(
        tmp_path / "exact-expiry",
        request=request,
        registry=registry,
        clock=lambda: recipe.expires_at,
    )
    exact_expiry = exact_expiry_service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    assert exact_expiry.receipt.status == "failed"
    assert exact_expiry.receipt.external_action_state == "failed"
    assert exact_expiry.handoff is None
    assert exact_expiry.receipt.replayed is False


def test_successful_handoff_replay_preserves_durable_receipt_after_expiry(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="replay-expiry")
    current_time = [recipe.created_at]
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=lambda: current_time[0],
    )
    exact = ExactGovernedHumanChallengeHandoffRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
    )

    first = service.prepare(exact)
    current_time[0] = recipe.expires_at + timedelta(seconds=1)
    replay = service.prepare(exact)

    assert first.receipt.status == "handoff_ready"
    assert first.handoff is not None
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.external_action_state == "succeeded"
    assert replay.receipt.replayed is True
    assert replay.handoff is None


def test_terminal_handoff_replays_before_recipe_window_without_new_claim(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="replay-before-window")
    current_time = [recipe.created_at]
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=lambda: current_time[0],
    )
    exact = ExactGovernedHumanChallengeHandoffRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
    )

    first = service.prepare(exact)
    current_time[0] = recipe.created_at - timedelta(seconds=1)
    replay = service.prepare(exact)

    assert first.receipt.status == "handoff_ready"
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.external_action_state == "succeeded"
    assert replay.receipt.replayed is True
    assert replay.handoff is None


def test_registered_recipe_cannot_outlive_binding_deadline(tmp_path: Path) -> None:
    base = _binding(suffix="deadline", deadline_offset=timedelta(minutes=5))
    created_at = utc_now()
    expires_at = base.start_deadline + timedelta(seconds=1)
    source_observation_ref = stable_governed_browser_ref(
        "browser-observe-output:governed-browser",
        {"kind": "observation", "suffix": "deadline"},
    )
    visibility_proof_ref = stable_governed_browser_ref(
        "visibility-proof-ref:governed-browser",
        {"kind": "visibility", "suffix": "deadline"},
    )
    handoff_surface_ref = stable_governed_browser_ref(
        "human-handoff-surface-ref:governed-browser",
        {"kind": "surface", "suffix": "deadline"},
    )
    challenge_ref = governed_human_challenge_ref(
        kind=GovernedHumanChallengeKind.mfa,
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        source_observation_ref=source_observation_ref,
        visibility_proof_ref=visibility_proof_ref,
    )
    schema_ref = governed_human_challenge_schema_ref(
        kind=GovernedHumanChallengeKind.mfa,
        challenge_ref=challenge_ref,
    )
    handoff_ref = governed_human_challenge_handoff_ref(
        challenge_ref=challenge_ref,
        human_presence_ref=base.human_presence_ref,
        handoff_surface_ref=handoff_surface_ref,
        expires_at=expires_at,
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.prepare,
            "field_schema_ref": schema_ref,
            "resource_refs": [
                _ref("resource", "deadline"),
                challenge_ref,
                source_observation_ref,
                visibility_proof_ref,
                handoff_surface_ref,
                handoff_ref,
            ],
        }
    )
    request = _request(binding)
    recipe_payload = {
        "handoff_ref": handoff_ref,
        "challenge_ref": challenge_ref,
        "challenge_schema_ref": schema_ref,
        "binding_ref": binding.binding_ref,
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "source_observation_ref": source_observation_ref,
        "visibility_proof_ref": visibility_proof_ref,
        "human_presence_ref": binding.human_presence_ref,
        "handoff_surface_ref": handoff_surface_ref,
        "challenge_kind": GovernedHumanChallengeKind.mfa,
        "required_human_action": (
            GovernedHumanChallengeAction.complete_mfa_on_external_surface
        ),
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedHumanChallengeHandoffRecipe.model_construct(
        recipe_ref="human-challenge-handoff-recipe-ref:governed-browser:pending",
        **recipe_payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "human-challenge-handoff-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    recipe = GovernedHumanChallengeHandoffRecipe(
        recipe_ref=recipe_ref,
        **recipe_payload,
    )
    registry = GovernedHumanChallengeHandoffRecipeRegistry([recipe])
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=lambda: created_at,
    )

    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-human-challenge:handoff-outlives-deadline"
    ]
    assert result.handoff is None


def test_contracts_reject_raw_or_unbound_handoff_fields() -> None:
    request, recipe, _ = _challenge_context(suffix="validation")
    with pytest.raises(ValueError):
        governed_human_challenge_handoff_ref(
            challenge_ref=recipe.challenge_ref,
            human_presence_ref=request.binding.human_presence_ref,
            handoff_surface_ref="resource-ref:governed-browser:wrong-kind",
            expires_at=recipe.expires_at,
        )
    with pytest.raises(ValueError, match="RESOURCE_NOT_AUTHORITY_BOUND"):
        unbound = ExternalActionAuthorityBinding.model_validate(
            {
                **request.binding.model_dump(mode="json"),
                "resource_refs": [
                    ref
                    for ref in request.binding.resource_refs
                    if ref != recipe.handoff_ref
                ],
            }
        )
        build_governed_human_challenge_handoff_recipe(
            _request(unbound),
            challenge_kind=GovernedHumanChallengeKind.mfa,
            source_observation_ref=recipe.source_observation_ref,
            visibility_proof_ref=recipe.visibility_proof_ref,
            handoff_surface_ref=recipe.handoff_surface_ref,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )
    receipt_payload = {
        "recipe_ref": recipe.recipe_ref,
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "status": "preflight_blocked",
        "external_action_state": "blocked",
        "reason_refs": ["reason-ref:governed-human-challenge:test"],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        governed_receipt_identity_payload(
            GovernedHumanChallengeHandoffReceipt.model_construct(
                receipt_ref="receipt-ref:governed-human-challenge-handoff:pending",
                **receipt_payload,
            )
        ),
    )
    parsed = GovernedHumanChallengeHandoffReceipt(
        receipt_ref=receipt_ref,
        **receipt_payload,
    )
    forged = parsed.model_dump(mode="json")
    forged["receipt_ref"] = "receipt-ref:governed-human-challenge-handoff:forged"
    with pytest.raises(ValueError, match="RECEIPT_REF_MISMATCH"):
        GovernedHumanChallengeHandoffReceipt.model_validate(forged)


@pytest.mark.parametrize(
    ("field", "material_ref"),
    [
        (
            "source_observation_ref",
            "browser-observe-output:governed-browser:123456",
        ),
        (
            "source_observation_ref",
            "browser-observe-output:governed-browser:123456:sha256:" + ("a" * 64),
        ),
        (
            "visibility_proof_ref",
            "visibility-proof-ref:governed-browser:captcha-sitekey-raw-value",
        ),
        (
            "handoff_surface_ref",
            "human-handoff-surface-ref:governed-browser:webauthn-challenge-raw",
        ),
        (
            "handoff_surface_ref",
            "human-handoff-surface-ref:governed-browser:ABC123",
        ),
    ],
)
def test_challenge_material_cannot_hide_inside_handoff_refs(
    field: str,
    material_ref: str,
) -> None:
    request, recipe, _ = _challenge_context(suffix="material-denial")
    values = {
        "source_observation_ref": recipe.source_observation_ref,
        "visibility_proof_ref": recipe.visibility_proof_ref,
        "handoff_surface_ref": recipe.handoff_surface_ref,
    }
    values[field] = material_ref

    with pytest.raises(
        ValueError,
        match="GOVERNED_HUMAN_CHALLENGE_MATERIAL_REF_DENIED",
    ):
        build_governed_human_challenge_handoff_recipe(
            request,
            challenge_kind=GovernedHumanChallengeKind.mfa,
            source_observation_ref=values["source_observation_ref"],
            visibility_proof_ref=values["visibility_proof_ref"],
            handoff_surface_ref=values["handoff_surface_ref"],
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )


def test_prepare_handoff_rejects_lease_with_implied_broader_capability(
    tmp_path: Path,
) -> None:
    request, recipe, registry = _challenge_context(suffix="lease-capability")
    kernel, _ = _authorized_kernel(tmp_path, request)
    broader_lease = _lease(request).model_copy(
        update={
            "domains": {
                AuthorityDomain.browser: [AuthorityCapability.execute],
            }
        }
    )
    kernel._authority_leases_provider = lambda: [broader_lease]
    service = ExactGovernedHumanChallengeHandoffService(
        registry=registry,
        kernel=kernel,
    )

    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )

    assert result.receipt.status == "transaction_blocked"
    assert result.receipt.reason_refs == [
        "reason-ref:governed-external-action:exact-lease-required"
    ]
    assert result.receipt.budget_reservation_ref is None
    assert result.handoff is None


def test_replay_transaction_identity_is_bound_to_registered_recipe(
    tmp_path: Path,
) -> None:
    base = _binding(suffix="recipe-replay")
    source_observation_ref = stable_governed_browser_ref(
        "browser-observe-output:governed-browser",
        {"kind": "observation", "suffix": "recipe-replay"},
    )
    visibility_proof_ref = stable_governed_browser_ref(
        "visibility-proof-ref:governed-browser",
        {"kind": "visibility", "suffix": "recipe-replay"},
    )
    surfaces = [
        stable_governed_browser_ref(
            "human-handoff-surface-ref:governed-browser",
            {"kind": "surface", "suffix": suffix},
        )
        for suffix in ("recipe-alpha", "recipe-beta")
    ]
    created_at = utc_now()
    expires_at = min(
        created_at + timedelta(minutes=5),
        base.start_deadline - timedelta(seconds=1),
    )
    challenge_ref = governed_human_challenge_ref(
        kind=GovernedHumanChallengeKind.mfa,
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        source_observation_ref=source_observation_ref,
        visibility_proof_ref=visibility_proof_ref,
    )
    schema_ref = governed_human_challenge_schema_ref(
        kind=GovernedHumanChallengeKind.mfa,
        challenge_ref=challenge_ref,
    )
    handoff_refs = [
        governed_human_challenge_handoff_ref(
            challenge_ref=challenge_ref,
            human_presence_ref=base.human_presence_ref,
            handoff_surface_ref=surface,
            expires_at=expires_at,
        )
        for surface in surfaces
    ]
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.prepare,
            "field_schema_ref": schema_ref,
            "resource_refs": [
                _ref("resource", "recipe-replay"),
                challenge_ref,
                source_observation_ref,
                visibility_proof_ref,
                *surfaces,
                *handoff_refs,
            ],
        }
    )
    request = _request(binding)
    recipes = [
        build_governed_human_challenge_handoff_recipe(
            request,
            challenge_kind=GovernedHumanChallengeKind.mfa,
            source_observation_ref=source_observation_ref,
            visibility_proof_ref=visibility_proof_ref,
            handoff_surface_ref=surface,
            created_at=created_at,
            expires_at=expires_at,
        )
        for surface in surfaces
    ]
    registry = GovernedHumanChallengeHandoffRecipeRegistry(recipes)
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )

    first = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipes[0].recipe_ref,
        )
    )
    assert first.receipt.status == "handoff_ready"

    with pytest.raises(
        ExternalActionTransactionConflict,
        match="GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT",
    ):
        service.prepare(
            ExactGovernedHumanChallengeHandoffRequest(
                execution_request=request,
                recipe_ref=recipes[1].recipe_ref,
            )
        )


def test_receipts_are_content_free_and_verifier_passes(tmp_path: Path) -> None:
    request, recipe, registry = _challenge_context(suffix="redaction")
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
    )
    result = service.prepare(
        ExactGovernedHumanChallengeHandoffRequest(
            execution_request=request,
            recipe_ref=recipe.recipe_ref,
        )
    )
    payload = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    assert "123456" not in payload
    assert "webauthn" not in payload.lower()
    assert "sitekey" not in payload.lower()
    assert '"challenge_response":' not in payload
    assert "https://" not in payload
    assert "/Users/" not in payload
    assert verify() == []
