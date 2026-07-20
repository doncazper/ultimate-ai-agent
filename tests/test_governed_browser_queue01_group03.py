from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.verify_governed_browser_queue01_group03 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _lease,
    _readiness,
    _request,
    _ref,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.governed_browser import (
    EvidenceRecipeObservationTransportResult,
    ExactBrowserObservationRequest,
    ExactBrowserObservationReceipt,
    ExactBrowserObservationService,
    ExactBrowserObservationStatus,
    ExternalActionAuthorityBinding,
    ExternalActionState,
    ExternalActionTargetKind,
    ExternalActionTransactionConflict,
    ExternalActionTransactionStore,
    GovernedBrowserEvidenceRecipe,
    GovernedBrowserEvidenceRecipeRegistry,
    GovernedExternalActionKernel,
    IsolatedBrowserBrokerAdapter,
    build_governed_browser_evidence_recipe,
    create_isolated_browser_broker_gateway,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    governed_receipt_identity_payload,
)
from ultimate_ai_agent.core.governed_browser.evidence_recipes import (
    _browser_observation_kernel_execution,
    _browser_observation_replay_expectation,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    _build_external_action_replay_validation_context,
    replay_validation_context,
)
from ultimate_ai_agent.core.governed_browser.transaction import BudgetSettlement


TARGET_REF = "browser-target-ref:governed-browser:evidence-panel"
SAFE_URL_REF = "browser-url:governed-browser/local-evidence-panel"


def _exact_request(*, suffix: str = "evidence"):  # type: ignore[no-untyped-def]
    base = _binding(suffix=suffix)
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "resource_refs": [
                _ref("resource", suffix),
                TARGET_REF,
                SAFE_URL_REF,
            ],
        }
    )
    return _request(binding)


def _recipe(request):  # type: ignore[no-untyped-def]
    return build_governed_browser_evidence_recipe(
        request,
        target_ref=TARGET_REF,
        safe_url_ref=SAFE_URL_REF,
        max_preview_chars=512,
        max_visible_text_bytes=4096,
    )


class _ExactEvidenceTransport:
    def __init__(self, **overrides: Any) -> None:
        self.overrides = overrides
        self.calls = 0
        self.profile_directories: list[Path] = []

    def observe(self, *, request, profile_directory, profile_ref):  # type: ignore[no-untyped-def]
        del profile_ref
        self.calls += 1
        self.profile_directories.append(profile_directory)
        assert profile_directory.exists()
        payload = {
            "recipe_ref": request.metadata["recipe_ref"],
            "binding_ref": request.metadata["binding_ref"],
            "origin_ref": request.metadata["exact_origin_ref"],
            "page_snapshot_ref": request.metadata["page_snapshot_ref"],
            "target_ref": request.metadata["target_ref"],
            "safe_url_ref": request.metadata["safe_url_ref"],
            "safe_title": "Local evidence fixture",
            "redacted_text_preview": (
                "Visible local status [REDACTED:SECRET_ASSIGNMENT]"
            ),
            "visible_text_bytes": 96,
            "redaction_summary_ref": (
                "redaction-summary-ref:governed-browser:evidence-fixture"
            ),
        }
        payload.update(self.overrides)
        return payload


def _service(
    *,
    request,
    recipe,
    kernel,
    transport: _ExactEvidenceTransport,
):  # type: ignore[no-untyped-def]
    broker = IsolatedBrowserBrokerAdapter(
        transport=transport,
        allowed_origin_refs={request.binding.origin_ref},
    )
    service = ExactBrowserObservationService(
        registry=GovernedBrowserEvidenceRecipeRegistry([recipe]),
        kernel=kernel,
        gateway=create_isolated_browser_broker_gateway(broker),
    )
    return service, broker


def _observe(service, request, recipe_ref):  # type: ignore[no-untyped-def]
    return service.observe(
        ExactBrowserObservationRequest(
            recipe_ref=recipe_ref,
            execution_request=request,
        )
    )


def _rehash_observation_replay(payload: dict[str, Any]) -> dict[str, Any]:
    external_payload = {
        "transaction_ref": payload["transaction_ref"],
        "intent_ref": payload["intent_ref"],
        "binding_ref": payload["binding_ref"],
        "state": payload["external_action_state"],
        "approval_validation_ref": payload["approval_validation_ref"],
        "authority_decision_ref": payload["authority_decision_ref"],
        "budget_reservation_ref": payload["budget_reservation_ref"],
        "budget_settlement_ref": payload["budget_settlement_ref"],
        "evidence_refs": payload["evidence_refs"],
        "reason_refs": payload["reason_refs"],
    }
    if payload["budget_release_ref"] is not None:
        external_payload["budget_release_ref"] = payload["budget_release_ref"]
    payload["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_payload,
    )
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        governed_receipt_identity_payload(
            ExactBrowserObservationReceipt.model_construct(**payload)
        ),
    )
    return payload


def test_registered_recipe_observes_exact_local_fixture_through_all_governance(
    tmp_path: Path,
) -> None:
    request = _exact_request()
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport()
    service, broker = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)

    assert (
        result.receipt.status == ExactBrowserObservationStatus.observation_ready.value
    )
    assert result.receipt.external_action_state == ExternalActionState.succeeded.value
    assert result.receipt.approval_validation_ref is not None
    assert result.receipt.authority_decision_ref is not None
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_settlement_ref is not None
    assert result.receipt.content_free is True
    assert result.receipt.automatic_retry_allowed is False
    assert result.evidence is not None
    assert result.evidence.recipe_ref == recipe.recipe_ref
    assert result.evidence.binding_ref == request.binding.binding_ref
    assert result.evidence.origin_ref == request.binding.origin_ref
    assert result.evidence.page_snapshot_ref == request.binding.page_snapshot_ref
    assert result.evidence.profile_ephemeral is True
    assert result.evidence.ordinary_profile_used is False
    assert result.evidence.content_untrusted is True
    assert result.evidence.web_content_instruction_use_allowed is False
    assert result.evidence.injected_observation_performed is True
    assert result.evidence.live_browser_observation_performed is False
    assert result.evidence.navigation_performed is False
    assert result.evidence.browser_action_performed is False
    assert result.evidence.authenticated_profile_used is False
    assert result.evidence.live_network_performed is False
    assert result.evidence.external_mutation_performed is False
    assert result.evidence.real_external_target_used is False
    assert transport.calls == 1
    assert broker.closed_profile_refs
    assert all(not path.exists() for path in transport.profile_directories)


def test_unknown_recipe_is_content_free_and_blocked_before_gateway(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="unknown-recipe")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(
        service,
        request,
        "evidence-recipe-ref:governed-browser:unregistered",
    )

    assert (
        result.receipt.status == ExactBrowserObservationStatus.preflight_blocked.value
    )
    assert result.receipt.external_action_receipt_ref is None
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-evidence:recipe-unregistered"
    ]
    assert result.evidence is None
    assert transport.calls == 0
    assert result.receipt.content_free is True


def test_approval_identifier_alone_grants_no_observation_authority(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="approval-only")
    recipe = _recipe(request)
    lease = _lease(request)
    authority = LocalApprovalAuthority()
    authority.issue_authority_lease(lease)
    kernel = GovernedExternalActionKernel(
        store=ExternalActionTransactionStore(tmp_path / "transactions.sqlite3"),
        approval_authority=authority,
        authority_leases_provider=lambda: [lease],
        readiness_provider=lambda item: _readiness(item),
        local_validation_enabled=True,
    )
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)

    assert (
        result.receipt.status == ExactBrowserObservationStatus.transaction_blocked.value
    )
    assert result.receipt.external_action_state == ExternalActionState.blocked.value
    assert result.receipt.approval_validation_ref is not None
    assert result.receipt.authority_decision_ref is None
    assert result.evidence is None
    assert transport.calls == 0
    assert request.approval_ref not in result.receipt.model_dump_json()


@pytest.mark.parametrize("mode", ["safe_disable", "kill_switch", "snapshot"])
def test_revalidation_denies_before_observation(
    tmp_path: Path,
    mode: str,
) -> None:
    request = _exact_request(suffix=mode)
    recipe = _recipe(request)

    def readiness(item):  # type: ignore[no-untyped-def]
        return _readiness(
            item,
            safe_disable=mode == "safe_disable",
            kill_switch=mode == "kill_switch",
            snapshot_ref=(
                _ref("page-snapshot", "changed") if mode == "snapshot" else None
            ),
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)

    assert (
        result.receipt.status == ExactBrowserObservationStatus.transaction_blocked.value
    )
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_release_ref is not None
    assert result.receipt.budget_settlement_ref is None
    assert result.evidence is None
    assert transport.calls == 0


def test_recipe_scope_is_exact_and_cannot_be_reused_for_another_binding(
    tmp_path: Path,
) -> None:
    original = _exact_request(suffix="original-recipe")
    recipe = _recipe(original)
    drifted = _exact_request(suffix="drifted-recipe")
    kernel, _ = _authorized_kernel(tmp_path, drifted)
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=drifted,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, drifted, recipe.recipe_ref)

    assert (
        result.receipt.status == ExactBrowserObservationStatus.preflight_blocked.value
    )
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-evidence:binding-mismatch"
    ]
    assert result.evidence is None
    assert transport.calls == 0

    base = _binding(suffix="missing-target")
    missing_target = _request(base)
    with pytest.raises(ValueError, match="TARGET_NOT_AUTHORITY_BOUND"):
        build_governed_browser_evidence_recipe(
            missing_target,
            target_ref=TARGET_REF,
            safe_url_ref=base.resource_refs[0],
        )


def test_observation_is_at_most_once_and_replay_is_content_free(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="replay")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    first = _observe(service, request, recipe.recipe_ref)
    replay = _observe(service, request, recipe.recipe_ref)

    assert first.evidence is not None
    assert (
        replay.receipt.status
        == ExactBrowserObservationStatus.replayed_content_free.value
    )
    assert replay.receipt.replayed is True
    assert replay.evidence is None
    assert transport.calls == 1
    payload = replay.receipt.model_dump_json()
    assert "Visible local status" not in payload
    assert "127.0.0.1" not in payload
    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        ExactBrowserObservationReceipt.model_validate_json(payload)


@pytest.mark.parametrize("terminal_state", ("blocked", "failed"))
def test_observation_blocked_and_failed_terminals_replay_content_free(
    tmp_path: Path,
    terminal_state: str,
) -> None:
    request = _exact_request(suffix=f"terminal-replay-{terminal_state}")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=lambda item: _readiness(
            item,
            safe_disable=terminal_state == "blocked",
        ),
    )
    transport = _ExactEvidenceTransport(
        **(
            {"raw_dom": "<html>terminal replay private content</html>"}
            if terminal_state == "failed"
            else {}
        )
    )
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    first = _observe(service, request, recipe.recipe_ref)
    replay = _observe(service, request, recipe.recipe_ref)

    expected_state = {
        "blocked": ExternalActionState.blocked.value,
        "failed": ExternalActionState.failed.value,
    }[terminal_state]
    expected_first_status = {
        "blocked": ExactBrowserObservationStatus.transaction_blocked.value,
        "failed": ExactBrowserObservationStatus.failed.value,
    }[terminal_state]
    assert first.receipt.status == expected_first_status
    assert replay.receipt.status == (
        ExactBrowserObservationStatus.replayed_content_free.value
    )
    assert replay.receipt.external_action_state == expected_state
    assert (
        replay.receipt.external_action_receipt_ref
        == first.receipt.external_action_receipt_ref
    )
    assert replay.receipt.replayed is True
    assert replay.receipt.content_free is True
    assert replay.receipt.automatic_retry_allowed is False
    assert replay.evidence is None
    assert transport.calls == {"blocked": 0, "failed": 1}[terminal_state]
    assert "terminal replay private content" not in replay.model_dump_json()


def test_observation_kernel_ambiguous_terminal_replays_content_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _exact_request(suffix="kernel-ambiguous-terminal-replay")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)

    def fail_capacity_check(_request):  # type: ignore[no-untyped-def]
        raise RuntimeError("raw capacity diagnostic")

    monkeypatch.setattr(kernel._store, "claim_dispatch_slot", fail_capacity_check)
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    first = _observe(service, request, recipe.recipe_ref)
    replay = _observe(service, request, recipe.recipe_ref)

    assert (
        first.receipt.status
        == ExactBrowserObservationStatus.outcome_ambiguous.value
    )
    assert "dispatch-capacity-check-failed" in " ".join(first.receipt.reason_refs)
    assert replay.receipt.status == (
        ExactBrowserObservationStatus.replayed_content_free.value
    )
    assert (
        replay.receipt.external_action_state
        == ExternalActionState.outcome_ambiguous.value
    )
    assert (
        replay.receipt.external_action_receipt_ref
        == first.receipt.external_action_receipt_ref
    )
    assert replay.receipt.replayed is True
    assert replay.receipt.content_free is True
    assert replay.receipt.automatic_retry_allowed is False
    assert replay.evidence is None
    assert transport.calls == 0
    assert "raw capacity diagnostic" not in replay.model_dump_json()


@pytest.mark.parametrize(
    "mutation",
    (
        "evidence_substitution",
        "evidence_order",
        "evidence_arity_drop",
        "evidence_arity_extra",
        "cross_lane",
        "cross_operation",
        "cross_recipe",
        "cross_transaction",
    ),
)
def test_observation_replay_requires_exact_durable_provenance(
    tmp_path: Path,
    mutation: str,
) -> None:
    request = _exact_request(suffix=f"replay-provenance-{mutation}")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    _observe(service, request, recipe.recipe_ref)
    replay = _observe(service, request, recipe.recipe_ref)
    kernel_request = _browser_observation_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = kernel.replay_if_terminal(kernel_request)
    assert replay_receipt is not None
    expectation = _browser_observation_replay_expectation(
        recipe,
        replay_receipt,
        kernel=kernel,
        expected_execution=kernel_request,
    )
    provenance = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=kernel_request,
        replay_receipt=replay_receipt,
        expectation=expectation,
    )
    context = replay_validation_context(provenance)
    payload = replay.receipt.model_dump(mode="json")

    with pytest.raises(
        ValidationError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
    ):
        ExactBrowserObservationReceipt.model_validate(payload)
    assert (
        ExactBrowserObservationReceipt.model_validate(payload, context=context)
        == replay.receipt
    )

    if mutation in {"cross_lane", "cross_operation"}:
        wrong_expectation = ExternalActionReplayEvidenceExpectation(
            lane_ref=(
                "replay-lane-ref:governed-browser-action:v1"
                if mutation == "cross_lane"
                else expectation.lane_ref
            ),
            operation_ref=(
                expectation.operation_ref
                if mutation == "cross_lane"
                else _ref("replay-operation", "observation-cross")
            ),
            scope_refs=expectation.scope_refs,
            evidence_refs=expectation.evidence_refs,
            operation_proof_ref=expectation.operation_proof_ref,
        )
        with pytest.raises(
            ValueError,
            match="GOVERNED_EXTERNAL_ACTION_REPLAY_OPERATION_PROOF_INVALID",
        ):
            _build_external_action_replay_validation_context(
                kernel,
                expected_execution=kernel_request,
                replay_receipt=replay_receipt,
                expectation=wrong_expectation,
            )
        return
    elif mutation == "evidence_substitution":
        payload["evidence_refs"] = [
            _ref("evidence", "observation-replay-provenance-substitute")
        ]
    elif mutation == "evidence_order":
        payload["evidence_refs"] = [
            _ref("evidence", "observation-replay-provenance-extra"),
            *payload["evidence_refs"],
        ]
    elif mutation == "evidence_arity_drop":
        payload["evidence_refs"] = []
    elif mutation == "evidence_arity_extra":
        payload["evidence_refs"].append(
            _ref("evidence", "observation-replay-provenance-extra")
        )
    elif mutation == "cross_recipe":
        payload["recipe_ref"] = _ref(
            "recipe",
            "observation-replay-provenance-cross",
        )
    else:
        foreign_request = _exact_request(
            suffix="observation-replay-provenance-foreign"
        )
        foreign_recipe = _recipe(foreign_request)
        foreign_kernel, _ = _authorized_kernel(
            tmp_path / "foreign",
            foreign_request,
        )
        foreign_service, _ = _service(
            request=foreign_request,
            recipe=foreign_recipe,
            kernel=foreign_kernel,
            transport=_ExactEvidenceTransport(),
        )
        _observe(foreign_service, foreign_request, foreign_recipe.recipe_ref)
        foreign_kernel_request = _browser_observation_kernel_execution(
            foreign_request,
            recipe_ref=foreign_recipe.recipe_ref,
        )
        foreign = foreign_kernel.replay_if_terminal(foreign_kernel_request)
        assert foreign is not None
        payload.update(
            {
                "transaction_ref": foreign.transaction_ref,
                "intent_ref": foreign.intent_ref,
                "binding_ref": foreign.binding_ref,
                "external_action_state": foreign.state,
                "approval_validation_ref": foreign.approval_validation_ref,
                "authority_decision_ref": foreign.authority_decision_ref,
                "budget_reservation_ref": foreign.budget_reservation_ref,
                "budget_release_ref": foreign.budget_release_ref,
                "budget_settlement_ref": foreign.budget_settlement_ref,
                "evidence_refs": list(foreign.evidence_refs),
                "reason_refs": list(foreign.reason_refs),
                "replayed": foreign.replayed,
            }
        )
    forged = _rehash_observation_replay(payload)

    with pytest.raises(
        ValidationError,
        match=(
            "GOVERNED_(EXTERNAL_ACTION_REPLAY_PROVENANCE_|"
            "BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE)"
        ),
    ):
        ExactBrowserObservationReceipt.model_validate(forged, context=context)


@pytest.mark.parametrize(
    "state",
    (
        ExternalActionState.prepared,
        ExternalActionState.started,
        ExternalActionState.outcome_ambiguous,
    ),
)
def test_observation_replay_expectation_rejects_nonterminal_or_arbitrary_ambiguity(
    tmp_path: Path,
    state: ExternalActionState,
) -> None:
    request = _exact_request(suffix=f"replay-envelope-reject-{state.value}")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    _observe(service, request, recipe.recipe_ref)
    kernel_request = _browser_observation_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    durable = kernel.replay_if_terminal(kernel_request)
    assert durable is not None
    evidence_refs = (
        (_ref("evidence", "arbitrary-observation-ambiguity"),)
        if state == ExternalActionState.outcome_ambiguous
        else durable.evidence_refs
    )
    malformed = durable.model_copy(
        update={
            "state": state.value,
            "evidence_refs": evidence_refs,
        }
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_OBSERVATION_REPLAY_EVIDENCE_PROVENANCE_REQUIRED",
    ):
        _browser_observation_replay_expectation(
            recipe,
            malformed,
            kernel=kernel,
            expected_execution=kernel_request,
        )


def test_observation_recipe_identity_conflicts_on_same_transaction(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="recipe-fingerprint-conflict")
    first_recipe = _recipe(request)
    second_recipe = build_governed_browser_evidence_recipe(
        request,
        target_ref=TARGET_REF,
        safe_url_ref=SAFE_URL_REF,
        max_preview_chars=256,
        max_visible_text_bytes=4096,
    )
    assert first_recipe.recipe_ref != second_recipe.recipe_ref
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport()
    broker = IsolatedBrowserBrokerAdapter(
        transport=transport,
        allowed_origin_refs={request.binding.origin_ref},
    )
    service = ExactBrowserObservationService(
        registry=GovernedBrowserEvidenceRecipeRegistry(
            [first_recipe, second_recipe]
        ),
        kernel=kernel,
        gateway=create_isolated_browser_broker_gateway(broker),
    )

    first = _observe(service, request, first_recipe.recipe_ref)
    assert (
        first.receipt.status
        == ExactBrowserObservationStatus.observation_ready.value
    )

    with pytest.raises(
        ExternalActionTransactionConflict,
        match="GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT",
    ):
        _observe(service, request, second_recipe.recipe_ref)
    assert transport.calls == 1


def test_observation_receipt_rejects_rehashed_conflicting_kernel_proofs(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="conflicting-kernel-proofs")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
    forged["budget_release_ref"] = _ref(
        "budget-release",
        "conflicting-kernel-proofs",
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
        "receipt-ref:governed-browser-observation",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_observation_non_preflight_receipt_requires_kernel_context(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="kernel-context-required")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
    forged.update(
        {
            "status": ExactBrowserObservationStatus.failed.value,
            "external_action_state": ExternalActionState.failed.value,
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": None,
            "budget_settlement_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-browser-evidence:observation-dispatch-failed"
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
        "receipt-ref:governed-browser-observation",
        identity_payload,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_REQUIRED",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_observation_non_preflight_rejects_orphan_kernel_proof(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="non-preflight-orphan-proof")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
    forged.update(
        {
            "status": ExactBrowserObservationStatus.failed.value,
            "external_action_state": ExternalActionState.failed.value,
            "external_action_receipt_ref": None,
            "approval_validation_ref": None,
            "authority_decision_ref": None,
            "budget_reservation_ref": None,
            "budget_release_ref": _ref(
                "budget-release",
                "observation-non-preflight-orphan-proof",
            ),
            "budget_settlement_ref": None,
            "evidence_refs": [],
            "reason_refs": [
                "reason-ref:governed-browser-evidence:observation-dispatch-failed"
            ],
            "replayed": False,
        }
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_observation_preflight_rejects_orphan_kernel_proof(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="preflight-orphan-proof")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(
        service,
        request,
        "evidence-recipe-ref:governed-browser:unknown",
    ).receipt.model_dump(mode="json")
    forged["budget_release_ref"] = _ref(
        "budget-release",
        "observation-preflight-orphan-proof",
    )
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        {key: value for key, value in forged.items() if key != "receipt_ref"},
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_PREFLIGHT_EXTERNAL_PROOF_DENIED",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_observation_receipt_rejects_kernel_state_status_mismatch(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="state-status-mismatch")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
    forged["status"] = ExactBrowserObservationStatus.failed.value
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        identity_payload,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_RECEIPT_STATE_MISMATCH",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_observation_non_replay_status_rejects_replay_flag(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="replay-status-mismatch")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=lambda item: _readiness(item, safe_disable=True),
    )
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
    assert forged["status"] == "transaction_blocked"
    forged["replayed"] = True
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        identity_payload,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_REPLAY_STATUS_MISMATCH",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


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
def test_observation_replayed_success_requires_complete_kernel_proof(
    tmp_path: Path,
    missing_field: str,
) -> None:
    request = _exact_request(suffix="proofless-replayed-success")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=_ExactEvidenceTransport(),
    )
    _observe(service, request, recipe.recipe_ref)
    forged = _observe(service, request, recipe.recipe_ref).receipt.model_dump(
        mode="json"
    )
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
    identity_payload = {
        key: value
        for key, value in forged.items()
        if key not in {"receipt_ref", "budget_release_ref"}
    }
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        identity_payload,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE",
    ):
        ExactBrowserObservationReceipt.model_validate(forged)


def test_settlement_failure_returns_ambiguous_receipt_without_evidence_or_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _exact_request(suffix="settlement-ambiguous")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    monkeypatch.setattr(
        kernel._budget_gate,
        "settle",
        lambda _request, _reservation_ref, _outcome, _evidence_refs: BudgetSettlement(
            allowed=False,
            reason_refs=["reason-ref:governed-browser-evidence:settlement-unconfirmed"],
        ),
    )
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)

    assert (
        result.receipt.status == ExactBrowserObservationStatus.outcome_ambiguous.value
    )
    assert (
        result.receipt.external_action_state
        == ExternalActionState.outcome_ambiguous.value
    )
    assert result.receipt.automatic_retry_allowed is False
    assert result.evidence is None
    assert transport.calls == 1


@pytest.mark.parametrize(
    "override",
    [
        {"raw_dom": "<html>raw private data</html>"},
        {"redacted_text_preview": "api_key=super-secret-value"},
        {"redacted_text_preview": "A" * 40},
        {"target_ref": "browser-target-ref:governed-browser:drifted"},
        {"navigation_performed": True},
    ],
)
def test_unregistered_raw_or_drifted_transport_output_fails_content_free(
    tmp_path: Path,
    override: dict[str, Any],
) -> None:
    request = _exact_request(suffix=f"unsafe-{len(override)}-{next(iter(override))}")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport(**override)
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)

    assert result.receipt.status == ExactBrowserObservationStatus.failed.value
    assert result.receipt.external_action_state == ExternalActionState.failed.value
    assert result.receipt.reason_refs == [
        "reason-ref:governed-browser-evidence:observation-dispatch-failed"
    ]
    assert result.evidence is None
    assert transport.calls == 1
    payload = result.receipt.model_dump_json()
    assert "super-secret-value" not in payload
    assert "<html>" not in payload


def test_recipe_and_transport_contracts_reject_authority_broadening() -> None:
    request = _exact_request(suffix="broadening")
    recipe = _recipe(request)
    payload = recipe.model_dump(mode="json")

    with pytest.raises(ValidationError):
        GovernedBrowserEvidenceRecipe.model_validate(
            {**payload, "live_network_allowed": True}
        )
    with pytest.raises(ValidationError):
        GovernedBrowserEvidenceRecipe.model_validate(
            {**payload, "browser_action_allowed": True}
        )
    with pytest.raises(ValidationError, match="SAFE_URL_REF_REQUIRED"):
        GovernedBrowserEvidenceRecipe.model_validate(
            {
                **payload,
                "safe_url_ref": "resource-ref:governed-browser:not-a-browser-url",
            }
        )
    with pytest.raises(ValidationError):
        GovernedBrowserEvidenceRecipeRegistry(
            [
                recipe.model_copy(
                    update={
                        "target_ref": (
                            "browser-target-ref:governed-browser:unbound-copy"
                        )
                    }
                )
            ]
        )

    transport_payload = {
        "recipe_ref": recipe.recipe_ref,
        "binding_ref": recipe.binding_ref,
        "origin_ref": recipe.exact_origin_ref,
        "page_snapshot_ref": recipe.page_snapshot_ref,
        "target_ref": recipe.target_ref,
        "safe_url_ref": recipe.safe_url_ref,
        "safe_title": "Local evidence fixture",
        "redacted_text_preview": "Visible safe status",
        "visible_text_bytes": 19,
        "redaction_summary_ref": (
            "redaction-summary-ref:governed-browser:no-redactions"
        ),
    }
    with pytest.raises(ValidationError):
        EvidenceRecipeObservationTransportResult.model_validate(
            {**transport_payload, "authenticated_profile_used": True}
        )


def test_real_external_target_cannot_create_an_evidence_recipe() -> None:
    external = _request(
        _binding(
            suffix="external-evidence",
            target_kind=ExternalActionTargetKind.external,
        )
    )

    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        build_governed_browser_evidence_recipe(
            external,
            target_ref=external.binding.resource_refs[0],
            safe_url_ref=external.binding.resource_refs[0],
        )


def test_queue01_group03_verifier() -> None:
    assert verify() == []


def test_observation_receipt_never_serializes_raw_origin_or_approval_identifier(
    tmp_path: Path,
) -> None:
    request = _exact_request(suffix="content-free")
    recipe = _recipe(request)
    kernel, _ = _authorized_kernel(tmp_path, request)
    transport = _ExactEvidenceTransport()
    service, _ = _service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )

    result = _observe(service, request, recipe.recipe_ref)
    receipt_payload = json.dumps(result.receipt.model_dump(mode="json"), sort_keys=True)

    assert request.binding.origin not in receipt_payload
    assert request.approval_ref not in receipt_payload
    assert "raw_gateway_result" not in receipt_payload
    assert result.raw_gateway_result_returned is False
    assert result.raw_transport_result_returned is False
