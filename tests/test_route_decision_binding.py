import json
from datetime import timedelta

from scripts.dev import uaa_turn_router
from ultimate_ai_agent.core.decision_router import (
    ROUTE_DECISION_BINDING_POLICY_VERSION_REF,
    TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS,
    RouteDecisionValidationStatus,
    build_route_decision_binding,
    classify_turn_contract,
    compile_invocation_policy,
    context_from_route_decision_binding,
    route_decision_binding_fingerprint_ref,
    safe_content_fingerprint_ref,
    validate_route_decision_binding,
)


def _binding(sample_text: str | None = None):
    resolved_text = sample_text or TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS["card-pickup"]
    decision = classify_turn_contract(
        resolved_text,
        decision_ref="turn-decision:route-binding-test",
    )
    policy = compile_invocation_policy(decision)
    return build_route_decision_binding(
        policy,
        actor_ref="actor-ref:test-operator",
        session_ref="session-ref:route-binding-test",
        turn_ref="turn-ref:route-binding-test",
        route_ref="/v1/chat/completions",
        side_effect_class="validation_only",
        idempotency_key="idempotency-key:route-binding-test",
        content_fingerprint_ref=safe_content_fingerprint_ref(resolved_text),
        context_fingerprint_ref="context-fingerprint:safe-route-binding-test",
        provider_ref="provider-ref:local-disabled",
        model_ref="model-ref:local-disabled",
        resource_refs=["resource-ref:route-binding-test"],
    )


def test_route_decision_binding_validates_current_scope_without_authority() -> None:
    binding = _binding()
    result = validate_route_decision_binding(binding, context_from_route_decision_binding(binding))

    assert result.status == RouteDecisionValidationStatus.valid.value
    assert result.allowed is True
    assert result.route_decision_is_approval is False
    assert result.authority_granted is False
    assert result.execution_performed is False
    assert result.binding_fingerprint_ref == route_decision_binding_fingerprint_ref(binding)


def test_route_decision_binding_rejects_expired_decision() -> None:
    binding = _binding()
    result = validate_route_decision_binding(
        binding,
        context_from_route_decision_binding(binding),
        now=binding.expires_at + timedelta(seconds=1),
    )

    assert result.status == RouteDecisionValidationStatus.expired.value
    assert result.allowed is False


def test_route_decision_binding_rejects_actor_turn_or_session_mismatch() -> None:
    binding = _binding()
    context = context_from_route_decision_binding(binding).model_copy(
        update={"actor_ref": "actor-ref:different-operator"}
    )

    result = validate_route_decision_binding(binding, context)

    assert result.status == RouteDecisionValidationStatus.scope_changed.value
    assert result.allowed is False


def test_route_decision_binding_rejects_side_effect_class_mismatch() -> None:
    binding = _binding()
    context = context_from_route_decision_binding(binding).model_copy(
        update={"side_effect_class": "local_dev_workspace_only"}
    )

    result = validate_route_decision_binding(binding, context)

    assert result.status == RouteDecisionValidationStatus.scope_changed.value


def test_route_decision_binding_rejects_policy_version_drift() -> None:
    binding = _binding()
    context = context_from_route_decision_binding(binding).model_copy(
        update={"policy_version_ref": "policy-version-ref:route-decision-binding:v2"}
    )

    result = validate_route_decision_binding(binding, context)

    assert binding.policy_version_ref == ROUTE_DECISION_BINDING_POLICY_VERSION_REF
    assert result.status == RouteDecisionValidationStatus.policy_changed.value


def test_route_decision_binding_rejects_approval_scope_mismatch() -> None:
    binding = _binding().model_copy(
        update={"approval_scope_ref": "approval-scope-ref:original"}
    )
    context = context_from_route_decision_binding(binding).model_copy(
        update={"approval_scope_ref": "approval-scope-ref:changed"}
    )

    result = validate_route_decision_binding(binding, context)

    assert result.status == RouteDecisionValidationStatus.scope_changed.value


def test_route_decision_binding_rejects_provider_model_mismatch() -> None:
    binding = _binding()
    context = context_from_route_decision_binding(binding).model_copy(
        update={"provider_ref": "provider-ref:other-disabled"}
    )

    result = validate_route_decision_binding(binding, context)

    assert result.status == RouteDecisionValidationStatus.scope_changed.value


def test_route_decision_binding_rejects_idempotency_replay_conflict() -> None:
    binding = _binding()

    result = validate_route_decision_binding(
        binding,
        context_from_route_decision_binding(binding),
        idempotency_ledger={binding.idempotency_key: "route-decision-binding-fingerprint:safe-conflict"},
    )

    assert result.status == RouteDecisionValidationStatus.replay_conflict.value


def test_route_decision_binding_rejects_safe_disable_activation() -> None:
    binding = _binding().model_copy(
        update={
            "safe_disable_active": True,
            "safe_disable_ref": "safe-disable-ref:route-binding-test",
        }
    )

    result = validate_route_decision_binding(binding, context_from_route_decision_binding(binding))

    assert result.status == RouteDecisionValidationStatus.authority_blocked.value


def test_route_decision_binding_rejects_unsafe_payload_flags() -> None:
    binding = _binding().model_copy(update={"raw_content_included": True})

    result = validate_route_decision_binding(binding, context_from_route_decision_binding(binding))

    assert result.status == RouteDecisionValidationStatus.unsafe_payload.value


def test_turn_router_cli_route_binding_outputs_safe_json(capsys) -> None:
    exit_code = uaa_turn_router.main(["route-binding", "--sample", "card-pickup"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["validation"]["status"] == "valid"
    assert payload["validation"]["allowed"] is True
    assert payload["binding"]["route_decision_is_approval"] is False
    assert TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS["card-pickup"].split(" and ", 1)[0] not in output
    assert "runtime/model/provider/tool authority" in payload["operator_note"]
