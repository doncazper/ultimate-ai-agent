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
    ExactBrowserObservationService,
    ExactBrowserObservationStatus,
    ExternalActionAuthorityBinding,
    ExternalActionState,
    ExternalActionTargetKind,
    ExternalActionTransactionStore,
    GovernedBrowserEvidenceRecipe,
    GovernedBrowserEvidenceRecipeRegistry,
    GovernedExternalActionKernel,
    IsolatedBrowserBrokerAdapter,
    build_governed_browser_evidence_recipe,
    create_isolated_browser_broker_gateway,
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
