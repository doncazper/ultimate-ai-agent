from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

import ultimate_ai_agent.core.governed_browser.task_composer as task_composer_module
from scripts.verify_governed_browser_queue01_group11 import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _ref,
    _request,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedTaskComposer,
    ExactGovernedTaskCompositionRequest,
    ExternalActionAuthorityBinding,
    ExternalActionReceipt,
    ExternalActionTargetKind,
    ExternalActionTransactionStore,
    GovernedExternalActionKernel,
    GovernedTaskCompositionPlan,
    GovernedTaskCompositionReceipt,
    GovernedTaskCompositionRecipe,
    GovernedTaskCompositionRecipeRegistry,
    GovernedTaskCompositionStep,
    GovernedTaskOperationKind,
    GovernedTaskOperationRegistry,
    RegisteredGovernedTaskOperation,
    build_governed_task_composition_recipe,
    build_governed_task_composition_step,
    build_registered_governed_task_operation,
    governed_task_broad_intent_ref,
    governed_task_composer_authority_ref,
    governed_task_composition_envelope_ref,
    governed_task_composition_plan_payload_ref,
    governed_task_composition_plan_ref,
    governed_task_composition_schema_ref,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    replay_validation_context,
)
from ultimate_ai_agent.core.governed_browser.transaction import BudgetSettlement
from ultimate_ai_agent.core.time import utc_now


def _pinned(prefix: str, suffix: str) -> str:
    return stable_governed_browser_ref(prefix, {"suffix": suffix})


def _rehash_task_composition_receipt(
    payload: dict[str, object],
) -> dict[str, object]:
    identity_payload = {
        key: value for key, value in payload.items() if key != "receipt_ref"
    }
    if identity_payload.get("budget_release_ref") is None:
        identity_payload.pop("budget_release_ref", None)
    external_snapshot = identity_payload.get("external_receipt_snapshot")
    if isinstance(external_snapshot, dict):
        external_snapshot = dict(external_snapshot)
        if external_snapshot.get("budget_release_ref") is None:
            external_snapshot.pop("budget_release_ref", None)
        identity_payload["external_receipt_snapshot"] = external_snapshot
    payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        identity_payload,
    )
    return payload


def _rehash_task_external_projection(
    payload: dict[str, object],
) -> dict[str, object]:
    external_value = payload["external_receipt_snapshot"]
    assert isinstance(external_value, dict)
    external = dict(external_value)
    external_identity = {
        "transaction_ref": external["transaction_ref"],
        "intent_ref": external["intent_ref"],
        "binding_ref": external["binding_ref"],
        "state": external["state"],
        "approval_validation_ref": external["approval_validation_ref"],
        "authority_decision_ref": external["authority_decision_ref"],
        "budget_reservation_ref": external["budget_reservation_ref"],
        "budget_settlement_ref": external["budget_settlement_ref"],
        "evidence_refs": external["evidence_refs"],
        "reason_refs": external["reason_refs"],
    }
    if external.get("budget_release_ref") is not None:
        external_identity["budget_release_ref"] = external["budget_release_ref"]
    external_receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_identity,
    )
    external["external_action_receipt_ref"] = external_receipt_ref
    snapshot_identity = {
        key: value for key, value in external.items() if key != "snapshot_ref"
    }
    if snapshot_identity.get("budget_release_ref") is None:
        snapshot_identity.pop("budget_release_ref", None)
    external["snapshot_ref"] = stable_governed_browser_ref(
        "external-receipt-snapshot-ref:governed-task-composer",
        snapshot_identity,
    )
    payload["external_action_receipt_ref"] = external_receipt_ref
    payload["evidence_refs"] = external["evidence_refs"]
    payload["external_receipt_snapshot"] = external
    return _rehash_task_composition_receipt(payload)


def _task_replay_validation_context(
    *,
    composer: ExactGovernedTaskComposer,
    request,
    recipe,
):  # type: ignore[no-untyped-def]
    expected_execution = task_composer_module._composer_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    replay_receipt = composer._kernel.replay_if_terminal(expected_execution)
    assert replay_receipt is not None
    return task_composer_module._task_composer_replay_context(
        composer._kernel,
        expected_execution=expected_execution,
        recipe=recipe,
        replay_receipt=replay_receipt,
    )


def _operation(
    *,
    suffix: str,
    kind: GovernedTaskOperationKind,
    capability: AuthorityCapability,
    authority_ref: str | None = None,
) -> RegisteredGovernedTaskOperation:
    return build_registered_governed_task_operation(
        kind=kind,
        source_recipe_ref=_pinned(
            "source-recipe-ref:governed-task-composer",
            suffix,
        ),
        source_contract_ref=_pinned(
            "source-contract-ref:governed-task-composer",
            suffix,
        ),
        source_binding_ref=_pinned(
            "source-binding-ref:governed-task-composer",
            suffix,
        ),
        operation_authority_ref=authority_ref
        or _pinned(
            "source-authority-ref:governed-task-composer",
            suffix,
        ),
        required_capability=capability,
        target_ref=_pinned("source-target-ref:governed-task-composer", suffix),
        schema_ref=_pinned("source-schema-ref:governed-task-composer", suffix),
    )


def _composition_context(
    *,
    suffix: str = "exact",
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    human_present: bool = True,
    created_at=None,  # type: ignore[no-untyped-def]
    expires_at=None,  # type: ignore[no-untyped-def]
):
    operations = [
        _operation(
            suffix=f"{suffix}-send",
            kind=GovernedTaskOperationKind.external_operation,
            capability=AuthorityCapability.send,
        ),
        _operation(
            suffix=f"{suffix}-purchase",
            kind=GovernedTaskOperationKind.financial_operation,
            capability=AuthorityCapability.purchase,
        ),
    ]
    operation_registry = GovernedTaskOperationRegistry(operations)
    first = build_governed_task_composition_step(
        ordinal=1,
        operation_ref=operations[0].operation_ref,
    )
    second = build_governed_task_composition_step(
        ordinal=2,
        operation_ref=operations[1].operation_ref,
        depends_on_step_refs=[first.step_ref],
    )
    steps = [first, second]
    base = _binding(
        suffix=suffix,
        target_kind=target_kind,
        human_present=human_present,
    )
    exact_created_at = created_at or utc_now()
    exact_expires_at = expires_at or min(
        exact_created_at + timedelta(minutes=5),
        base.start_deadline - timedelta(seconds=1),
    )
    broad_intent_ref = governed_task_broad_intent_ref(
        intent_fingerprint=_pinned(
            "intent-fingerprint-ref:governed-task-composer",
            suffix,
        )
    )
    schema_ref = governed_task_composition_schema_ref(
        registry_ref=operation_registry.registry_ref,
        steps=steps,
    )
    plan_payload_ref = governed_task_composition_plan_payload_ref(
        broad_intent_ref=broad_intent_ref,
        registry_ref=operation_registry.registry_ref,
        steps=steps,
        created_at=exact_created_at,
        expires_at=exact_expires_at,
    )
    composer_authority_ref = governed_task_composer_authority_ref(
        origin_ref=base.origin_ref,
        page_snapshot_ref=base.page_snapshot_ref,
        plan_payload_ref=plan_payload_ref,
        registry_ref=operation_registry.registry_ref,
    )
    binding = ExternalActionAuthorityBinding.model_validate(
        {
            **base.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.prepare,
            "transaction_ref": _pinned(
                "transaction-ref:governed-task-composer",
                suffix,
            ),
            "recipient_ref": plan_payload_ref,
            "field_schema_ref": schema_ref,
            "artifact_refs": [operation.operation_ref for operation in operations],
            "resource_refs": sorted(
                {
                    broad_intent_ref,
                    operation_registry.registry_ref,
                    plan_payload_ref,
                    composer_authority_ref,
                }
            ),
        }
    )
    request = _request(binding)
    recipe = build_governed_task_composition_recipe(
        request,
        broad_intent_ref=broad_intent_ref,
        registry=operation_registry,
        steps=steps,
        created_at=exact_created_at,
        expires_at=exact_expires_at,
    )
    return (
        request,
        recipe,
        operation_registry,
        GovernedTaskCompositionRecipeRegistry([recipe]),
    )


def _exact(request, recipe) -> ExactGovernedTaskCompositionRequest:  # type: ignore[no-untyped-def]
    return ExactGovernedTaskCompositionRequest(
        execution_request=request,
        recipe_ref=recipe.recipe_ref,
        plan_ref=recipe.plan_ref,
        broad_intent_ref=recipe.broad_intent_ref,
        registry_ref=recipe.registry_ref,
    )


def _composer(
    tmp_path: Path,
    *,
    request,
    operation_registry,
    recipe_registry,
    readiness_provider=None,  # type: ignore[no-untyped-def]
    clock=utc_now,  # type: ignore[no-untyped-def]
):
    kernel, authority = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness_provider,
        clock=clock,
    )
    return (
        ExactGovernedTaskComposer(
            operation_registry=operation_registry,
            recipe_registry=recipe_registry,
            kernel=kernel,
            clock=clock,
        ),
        authority,
    )


def test_registered_operations_compose_into_exact_plan_only_projection(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context()
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )

    result = composer.compose(_exact(request, recipe))

    assert result.receipt.status == "plan_ready"
    assert result.receipt.external_action_state == "succeeded"
    assert result.receipt.operation_refs == tuple(
        step.operation_ref for step in recipe.steps
    )
    assert result.receipt.evidence_refs == (
        recipe.recipe_ref,
        recipe.plan_ref,
        recipe.registry_ref,
        recipe.composer_authority_ref,
        *result.receipt.operation_refs,
    )
    assert result.receipt.recipe_snapshot == recipe
    assert result.receipt.recipe_snapshot is not None
    with pytest.raises(AttributeError):
        result.receipt.recipe_snapshot.steps.append(  # type: ignore[attr-defined]
            recipe.steps[0]
        )
    with pytest.raises(AttributeError):
        result.receipt.evidence_refs.append(  # type: ignore[attr-defined]
            recipe.recipe_ref
        )
    assert result.plan is not None
    assert [step.ordinal for step in result.plan.steps] == [1, 2]
    assert result.plan.steps[1].depends_on_step_refs == (result.plan.steps[0].step_ref,)
    with pytest.raises(AttributeError):
        result.plan.steps.append(result.plan.steps[0])  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        result.plan.steps[1].depends_on_step_refs.append(  # type: ignore[attr-defined]
            result.plan.steps[0].step_ref
        )
    assert [step.required_capability for step in result.plan.steps] == [
        "send",
        "purchase",
    ]
    assert all(not step.operation_authorized for step in result.plan.steps)
    assert all(not step.composer_authority_inherited for step in result.plan.steps)
    assert not result.plan.complete_any_task_granted
    assert not result.plan.model_call_performed
    assert not result.plan.browser_action_performed
    assert not result.plan.network_call_performed
    assert not result.plan.external_mutation_performed
    assert not result.plan.automatic_execution_performed


@pytest.mark.parametrize(
    ("kind", "capability"),
    [
        (GovernedTaskOperationKind.evidence_observation, AuthorityCapability.observe),
        (GovernedTaskOperationKind.visible_click, AuthorityCapability.click),
        (GovernedTaskOperationKind.get_form_plan, AuthorityCapability.form_fill),
        (GovernedTaskOperationKind.post_form_plan, AuthorityCapability.form_fill),
        (GovernedTaskOperationKind.credential_lifecycle, AuthorityCapability.execute),
        (GovernedTaskOperationKind.challenge_handoff, AuthorityCapability.prepare),
        (GovernedTaskOperationKind.download_quarantine, AuthorityCapability.download),
        (GovernedTaskOperationKind.upload_plan, AuthorityCapability.upload),
        (GovernedTaskOperationKind.external_operation, AuthorityCapability.destructive),
        (
            GovernedTaskOperationKind.financial_operation,
            AuthorityCapability.purchase_under_budget,
        ),
    ],
)
def test_bounded_operation_families_accept_only_their_exact_capability(
    kind: GovernedTaskOperationKind,
    capability: AuthorityCapability,
) -> None:
    operation = _operation(suffix=kind.value, kind=kind, capability=capability)

    assert operation.kind == kind.value
    assert operation.required_capability == capability.value
    with pytest.raises(
        ValidationError,
        match="OPERATION_CAPABILITY_MISMATCH",
    ):
        RegisteredGovernedTaskOperation.model_validate(
            {
                **operation.model_dump(mode="json"),
                "required_capability": AuthorityCapability.commit,
            }
        )
    if kind == GovernedTaskOperationKind.credential_lifecycle:
        with pytest.raises(ValidationError, match="OPERATION_CAPABILITY_MISMATCH"):
            RegisteredGovernedTaskOperation.model_validate(
                {
                    **operation.model_dump(mode="json"),
                    "required_capability": AuthorityCapability.prepare,
                }
            )


def test_raw_or_broad_intent_cannot_enter_the_composer() -> None:
    with pytest.raises(ValueError):
        governed_task_broad_intent_ref(intent_fingerprint="finish my whole task")
    with pytest.raises(ValueError, match="BROAD_INTENT"):
        governed_task_broad_intent_ref(
            intent_fingerprint="capability:complete_any_task"
        )
    with pytest.raises(ValueError, match="BROAD_INTENT"):
        governed_task_broad_intent_ref(intent_fingerprint="capability:*")
    for disguised_grant in (
        "capability:complete/any/task",
        "capability:completeanytask",
        "authority.complete-any-task",
        "capability/all",
        "capabilities.any",
        "authority.any",
        "authorities/all",
        "cap.ability:all",
        "any:auth.orities",
        "authority:wild.card",
    ):
        with pytest.raises(ValueError, match="BROAD_INTENT"):
            governed_task_broad_intent_ref(intent_fingerprint=disguised_grant)


def test_operation_registration_is_hash_bound_and_authority_unique() -> None:
    shared_authority_ref = _pinned(
        "source-authority-ref:governed-task-composer",
        "shared",
    )
    operation = _operation(
        suffix="bound",
        kind=GovernedTaskOperationKind.external_operation,
        capability=AuthorityCapability.send,
        authority_ref=shared_authority_ref,
    )
    with pytest.raises(ValidationError, match="OPERATION_REF_MISMATCH"):
        RegisteredGovernedTaskOperation.model_validate(
            {
                **operation.model_dump(mode="json"),
                "target_ref": _pinned(
                    "source-target-ref:governed-task-composer",
                    "drifted",
                ),
            }
        )
    duplicate_authority = _operation(
        suffix="other",
        kind=GovernedTaskOperationKind.external_operation,
        capability=AuthorityCapability.send,
        authority_ref=shared_authority_ref,
    )
    with pytest.raises(ValueError, match="OPERATION_AUTHORITY_DUPLICATE"):
        GovernedTaskOperationRegistry([operation, duplicate_authority])
    exact_sources = {
        "source_recipe_ref": _pinned("source-recipe-ref:source-system", "exact"),
        "source_contract_ref": _pinned("source-contract-ref:source-system", "exact"),
        "source_binding_ref": _pinned("source-binding-ref:source-system", "exact"),
        "operation_authority_ref": _pinned(
            "source-authority-ref:source-system", "exact"
        ),
        "target_ref": _pinned("source-target-ref:source-system", "exact"),
        "schema_ref": _pinned("source-schema-ref:source-system", "exact"),
    }
    for label in exact_sources:
        unpinned_sources = {
            **exact_sources,
            label: f"{label.replace('_', '-')}:current",
        }
        with pytest.raises(ValueError, match="HASH_PIN_REQUIRED"):
            build_registered_governed_task_operation(
                kind=GovernedTaskOperationKind.external_operation,
                required_capability=AuthorityCapability.send,
                **unpinned_sources,
            )
    for narrow_authority_ref in (
        _pinned("small-authority-ref:source", "narrow-source"),
        _pinned("company-capabilities-ref:source", "narrow-source"),
        _pinned("authority:alliance", "narrow-source"),
        _pinned("capability:anycast", "narrow-source"),
        _pinned("source-authority-ref:wildcardness-policy", "narrow-source"),
        _pinned("source-authority-ref:completeanytaskforce", "narrow-source"),
    ):
        assert build_registered_governed_task_operation(
            kind=GovernedTaskOperationKind.external_operation,
            required_capability=AuthorityCapability.send,
            **{
                **exact_sources,
                "operation_authority_ref": narrow_authority_ref,
            },
        ).operation_authority_ref.startswith(
            "source-authority-ref:governed-task-composer:"
        )
    for broad_authority_ref in (
        _pinned("capabilities:any", "broad-source"),
        _pinned("authorities:all", "broad-source"),
        _pinned("all-authorities-ref:source", "broad-source"),
        _pinned("any-capabilities-ref:source", "broad-source"),
        _pinned("cap.ability:all", "broad-source"),
        _pinned("any:cap.abilities", "broad-source"),
        _pinned("source-authority-ref:wild.card", "broad-source"),
        _pinned("source-authority-ref:complete.any.task", "broad-source"),
    ):
        with pytest.raises(ValueError, match="BROAD_OPERATION_AUTHORITY_REF"):
            build_registered_governed_task_operation(
                kind=GovernedTaskOperationKind.external_operation,
                required_capability=AuthorityCapability.send,
                **{
                    **exact_sources,
                    "operation_authority_ref": broad_authority_ref,
                },
            )
    registry = GovernedTaskOperationRegistry([operation])
    with pytest.raises(AttributeError):
        registry.registry_ref = _pinned(
            "operation-registry-ref:governed-task-composer",
            "rebound",
        )


def test_recipe_rejects_unknown_operations_cycles_reuse_and_reordering() -> None:
    request, recipe, operations, _ = _composition_context(suffix="graph")
    unknown = build_governed_task_composition_step(
        ordinal=1,
        operation_ref=_pinned(
            "registered-operation-ref:governed-task-composer",
            "unknown",
        ),
    )
    with pytest.raises(ValueError, match="OPERATION_UNREGISTERED"):
        build_governed_task_composition_recipe(
            request,
            broad_intent_ref=recipe.broad_intent_ref,
            registry=operations,
            steps=[unknown],
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )
    cyclic_first = GovernedTaskCompositionStep.model_validate(
        {
            **recipe.steps[0].model_dump(mode="json"),
            "depends_on_step_refs": [recipe.steps[1].step_ref],
            "step_ref": stable_governed_browser_ref(
                "composition-step-ref:governed-task-composer",
                {
                    **recipe.steps[0].model_dump(mode="json", exclude={"step_ref"}),
                    "depends_on_step_refs": [recipe.steps[1].step_ref],
                },
            ),
        }
    )
    with pytest.raises(ValidationError, match="DEPENDENCY_NOT_PRIOR"):
        GovernedTaskCompositionRecipe.model_validate(
            {
                **recipe.model_dump(mode="json"),
                "steps": [
                    cyclic_first.model_dump(mode="json"),
                    recipe.steps[1].model_dump(mode="json"),
                ],
            }
        )
    duplicate = build_governed_task_composition_step(
        ordinal=2,
        operation_ref=recipe.steps[0].operation_ref,
        depends_on_step_refs=[recipe.steps[0].step_ref],
    )
    with pytest.raises(ValidationError, match="OPERATION_REUSE_DENIED"):
        GovernedTaskCompositionRecipe.model_validate(
            {
                **recipe.model_dump(mode="json"),
                "steps": [
                    recipe.steps[0].model_dump(mode="json"),
                    duplicate.model_dump(mode="json"),
                ],
            }
        )


def test_exact_binding_rejects_capability_scope_and_target_drift() -> None:
    request, recipe, operations, _ = _composition_context(suffix="binding")
    wrong_capability_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **request.binding.model_dump(mode="json"),
            "authority_capability": AuthorityCapability.execute,
        }
    )
    with pytest.raises(ValueError, match="PREPARE_CAPABILITY_REQUIRED"):
        build_governed_task_composition_recipe(
            _request(wrong_capability_binding),
            broad_intent_ref=recipe.broad_intent_ref,
            registry=operations,
            steps=recipe.steps,
            created_at=recipe.created_at,
            expires_at=recipe.expires_at,
        )
    for field, value, reason in (
        ("recipient_ref", _ref("plan", "wrong"), "PLAN_NOT_AUTHORITY_BOUND"),
        ("field_schema_ref", _ref("schema", "wrong"), "SCHEMA_NOT_AUTHORITY_BOUND"),
        (
            "artifact_refs",
            list(reversed(request.binding.artifact_refs)),
            "OPERATIONS_NOT_EXACTLY_BOUND",
        ),
        ("resource_refs", [_ref("resource", "wrong")], "RESOURCE_NOT_EXACTLY_BOUND"),
    ):
        drifted_binding = ExternalActionAuthorityBinding.model_validate(
            {
                **request.binding.model_dump(mode="json"),
                field: value,
            }
        )
        with pytest.raises(ValueError, match=reason):
            build_governed_task_composition_recipe(
                _request(drifted_binding),
                broad_intent_ref=recipe.broad_intent_ref,
                registry=operations,
                steps=recipe.steps,
                created_at=recipe.created_at,
                expires_at=recipe.expires_at,
            )


def test_unknown_recipe_and_exact_request_drift_are_preflight_blocked(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="request")
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    unknown = composer.compose(
        exact.model_copy(
            update={
                "recipe_ref": _pinned(
                    "composition-recipe-ref:governed-task-composer",
                    "unknown",
                )
            }
        )
    )
    drifted = composer.compose(
        exact.model_copy(
            update={
                "plan_ref": _pinned(
                    "composition-plan-ref:governed-task-composer",
                    "wrong",
                )
            }
        )
    )

    assert unknown.receipt.status == "preflight_blocked"
    assert unknown.receipt.reason_refs == (
        "reason-ref:governed-task-composer:recipe-unregistered",
    )
    assert drifted.receipt.status == "preflight_blocked"
    assert drifted.receipt.reason_refs == (
        "reason-ref:governed-task-composer:request-scope-mismatch",
    )
    assert unknown.plan is None
    assert drifted.plan is None

    forged_release = unknown.receipt.model_dump(mode="json")
    forged_release["budget_release_ref"] = _pinned(
        "receipt-ref:authority-budget",
        "unrelated-preflight-release",
    )
    forged_release["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {
            key: value
            for key, value in forged_release.items()
            if key != "receipt_ref"
        },
    )
    with pytest.raises(ValidationError, match="EXTERNAL_PROOF_CONTEXT_INVALID"):
        GovernedTaskCompositionReceipt.model_validate(forged_release)


def test_composition_request_rejects_contentful_refs_and_transaction_ids() -> None:
    request, recipe, _, _ = _composition_context(suffix="opaque-request")
    exact = _exact(request, recipe)
    with pytest.raises(ValidationError, match="PLAN_REF_REQUIRED"):
        ExactGovernedTaskCompositionRequest.model_validate(
            {
                **exact.model_dump(mode="json"),
                "plan_ref": "plan-ref:send-alice@example.com",
            }
        )
    descriptive_binding = ExternalActionAuthorityBinding.model_validate(
        {
            **request.binding.model_dump(mode="json"),
            "transaction_ref": "transaction-ref:governed-browser:send-alice@example.com",
        }
    )
    with pytest.raises(ValidationError, match="TRANSACTION_REF_REQUIRED"):
        ExactGovernedTaskCompositionRequest(
            execution_request=_request(descriptive_binding),
            recipe_ref=recipe.recipe_ref,
            plan_ref=recipe.plan_ref,
            broad_intent_ref=recipe.broad_intent_ref,
            registry_ref=recipe.registry_ref,
        )


def test_approval_identifier_alone_grants_no_composition_plan(tmp_path: Path) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="approval")
    kernel = GovernedExternalActionKernel(
        store=ExternalActionTransactionStore(tmp_path / "transactions.sqlite3"),
        approval_authority=LocalApprovalAuthority(),
        authority_leases_provider=lambda: [],
        readiness_provider=lambda item: _readiness(item),
        local_validation_enabled=True,
    )
    composer = ExactGovernedTaskComposer(
        operation_registry=operations,
        recipe_registry=recipes,
        kernel=kernel,
    )

    result = composer.compose(_exact(request, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.plan is None
    assert any("approval" in ref for ref in result.receipt.reason_refs)


@pytest.mark.parametrize(
    ("safe_disable", "kill_switch"), [(True, False), (False, True)]
)
def test_safe_disable_and_kill_switch_deny_composition(
    tmp_path: Path,
    safe_disable: bool,
    kill_switch: bool,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix=f"stop-{safe_disable}-{kill_switch}"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
        readiness_provider=lambda item: _readiness(
            item,
            safe_disable=safe_disable,
            kill_switch=kill_switch,
        ),
    )

    result = composer.compose(_exact(request, recipe))

    assert result.receipt.status == "transaction_blocked"
    assert result.receipt.budget_reservation_ref is not None
    assert result.receipt.budget_release_ref is not None
    assert result.receipt.budget_settlement_ref is None
    assert result.plan is None
    assert not result.receipt.automatic_retry_allowed


def test_ambiguous_kernel_outcome_receives_content_free_composer_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="ambiguous-reason"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )

    def fail_plan_build(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise RuntimeError("injected local plan failure")

    monkeypatch.setattr(task_composer_module, "_build_plan", fail_plan_build)
    result = composer.compose(_exact(request, recipe))

    assert result.receipt.status == "outcome_ambiguous"
    assert result.receipt.external_action_reason_refs == (
        "reason-ref:governed-external-action:dispatch-exception",
    )
    assert result.receipt.reason_refs == (
        "reason-ref:governed-external-action:dispatch-exception",
    )
    assert result.plan is None


def test_success_replay_is_content_free_and_idempotency_drift_is_denied(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="replay")
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)

    first = composer.compose(exact)
    replay = composer.compose(exact)
    drifted = composer.compose(
        exact.model_copy(
            update={
                "execution_request": request.model_copy(
                    update={
                        "idempotency_ref": stable_governed_browser_ref(
                            "idempotency-ref:governed-task-composer:drifted",
                            {"source_idempotency_ref": request.idempotency_ref},
                        )
                    }
                )
            }
        )
    )

    assert first.receipt.status == "plan_ready"
    assert first.plan is not None
    assert replay.receipt.status == "replayed_content_free"
    assert replay.receipt.replayed
    assert replay.plan is None
    assert drifted.receipt.status == "preflight_blocked"
    assert drifted.receipt.reason_refs == (
        "reason-ref:governed-task-composer:idempotency-conflict",
    )


def test_task_composer_replay_wrappers_require_exact_terminal_provenance(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="replay-provenance"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    composer.compose(exact)
    replay = composer.compose(exact)
    payload = replay.receipt.model_dump(mode="json")
    context = _task_replay_validation_context(
        composer=composer,
        request=request,
        recipe=recipe,
    )

    restored = GovernedTaskCompositionReceipt.model_validate(
        payload,
        context=replay_validation_context(context),
    )
    assert restored == replay.receipt
    external_payload = payload["external_receipt_snapshot"]
    assert isinstance(external_payload, dict)
    restored_external = (
        task_composer_module.GovernedTaskCompositionExternalReceiptSnapshot.model_validate(
            external_payload,
            context=replay_validation_context(context),
        )
    )
    assert restored_external == replay.receipt.external_receipt_snapshot
    for model, candidate in (
        (GovernedTaskCompositionReceipt, payload),
        (
            task_composer_module.GovernedTaskCompositionExternalReceiptSnapshot,
            external_payload,
        ),
    ):
        with pytest.raises(
            ValueError,
            match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_CONTEXT_REQUIRED",
        ):
            model.model_validate(candidate)


@pytest.mark.parametrize(
    ("terminal_state", "first_status", "replay_status"),
    (
        ("blocked", "transaction_blocked", "transaction_blocked"),
        ("failed", "failed", "failed"),
        ("outcome_ambiguous", "outcome_ambiguous", "outcome_ambiguous"),
    ),
)
def test_task_composer_non_success_terminal_replays_use_complete_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_state: str,
    first_status: str,
    replay_status: str,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix=f"replay-terminal-{terminal_state}"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
        readiness_provider=(
            (lambda item: _readiness(item, safe_disable=True))
            if terminal_state == "blocked"
            else None
        ),
    )
    if terminal_state == "failed":
        clock_results = iter(
            (
                (recipe.created_at, None),
                (
                    None,
                    "reason-ref:governed-task-composer:trusted-clock-invalid",
                ),
            )
        )
        monkeypatch.setattr(
            task_composer_module,
            "_read_clock",
            lambda clock: next(clock_results),
        )
    elif terminal_state == "outcome_ambiguous":

        def fail_plan_build(*args, **kwargs):  # type: ignore[no-untyped-def]
            del args, kwargs
            raise RuntimeError("injected local plan failure")

        monkeypatch.setattr(
            task_composer_module,
            "_build_plan",
            fail_plan_build,
        )
    exact = _exact(request, recipe)

    first = composer.compose(exact)
    replay = composer.compose(exact)

    assert first.receipt.status == first_status
    assert first.receipt.external_action_state == terminal_state
    assert first.receipt.replayed is False
    assert replay.receipt.status == replay_status
    assert replay.receipt.external_action_state == terminal_state
    assert replay.receipt.replayed is True
    assert replay.receipt.external_receipt_snapshot is not None
    assert replay.plan is None
    context = _task_replay_validation_context(
        composer=composer,
        request=request,
        recipe=recipe,
    )
    assert (
        GovernedTaskCompositionReceipt.model_validate(
            replay.receipt.model_dump(mode="json"),
            context=replay_validation_context(context),
        )
        == replay.receipt
    )


@pytest.mark.parametrize(
    ("state", "evidence_mode"),
    (
        ("blocked", "arbitrary"),
        ("failed", "arbitrary"),
        ("outcome_ambiguous", "arbitrary"),
        ("started", "success"),
        ("prepared", "empty"),
    ),
)
def test_task_composer_replay_expectation_rejects_invalid_non_success_envelopes(
    tmp_path: Path,
    state: str,
    evidence_mode: str,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix=f"replay-invalid-envelope-{state}-{evidence_mode}"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    composer.compose(exact)
    composer.compose(exact)
    expected_execution = task_composer_module._composer_kernel_execution(
        request,
        recipe_ref=recipe.recipe_ref,
    )
    baseline = composer._kernel.replay_if_terminal(expected_execution)
    assert baseline is not None
    evidence_refs = {
        "arbitrary": (_ref("evidence", f"composer-{state}-arbitrary"),),
        "success": tuple(baseline.evidence_refs),
        "empty": (),
    }[evidence_mode]
    candidate = baseline.model_copy(
        update={
            "state": state,
            "evidence_refs": evidence_refs,
        }
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_TASK_COMPOSER_REPLAY_EVIDENCE_ENVELOPE_MISMATCH",
    ):
        task_composer_module._task_composer_replay_context(
            composer._kernel,
            expected_execution=expected_execution,
            recipe=recipe,
            replay_receipt=candidate,
        )


@pytest.mark.parametrize(
    "tamper_mode",
    (
        0,
        1,
        2,
        3,
        4,
        5,
        "cross-operation",
        "order",
        "drop",
        "append",
    ),
)
def test_task_composer_replay_rejects_fully_rehashed_evidence_tampering(
    tmp_path: Path,
    tamper_mode: int | str,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix=f"replay-tamper-{tamper_mode}"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    composer.compose(exact)
    replay = composer.compose(exact)
    context = _task_replay_validation_context(
        composer=composer,
        request=request,
        recipe=recipe,
    )
    forged = replay.receipt.model_dump(mode="json")
    external = forged["external_receipt_snapshot"]
    assert isinstance(external, dict)
    evidence_refs = list(external["evidence_refs"])
    if isinstance(tamper_mode, int):
        ref_prefix = evidence_refs[tamper_mode].rsplit(":sha256:", 1)[0]
        evidence_refs[tamper_mode] = stable_governed_browser_ref(
            ref_prefix,
            {"tamper": tamper_mode},
        )
    elif tamper_mode == "cross-operation":
        evidence_refs[4], evidence_refs[5] = (
            evidence_refs[5],
            evidence_refs[4],
        )
    elif tamper_mode == "order":
        evidence_refs.reverse()
    elif tamper_mode == "drop":
        evidence_refs.pop()
    else:
        evidence_refs.append(
            _pinned(
                "registered-operation-ref:governed-task-composer",
                "replay-extra",
            )
        )
    external["evidence_refs"] = evidence_refs
    forged["external_receipt_snapshot"] = external
    _rehash_task_external_projection(forged)

    with pytest.raises(
        ValueError,
        match=(
            "GOVERNED_TASK_COMPOSER_SUCCESS_EVIDENCE_MISMATCH"
            "|GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_RECEIPT_MISMATCH"
        ),
    ):
        GovernedTaskCompositionReceipt.model_validate(
            forged,
            context=replay_validation_context(context),
        )


def test_task_composer_replay_rejects_cross_transaction_recipe_context(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="replay-context-a"
    )
    composer, _ = _composer(
        tmp_path / "a",
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    composer.compose(exact)
    composer.compose(exact)
    context = _task_replay_validation_context(
        composer=composer,
        request=request,
        recipe=recipe,
    )

    other_request, other_recipe, other_operations, other_recipes = (
        _composition_context(suffix="replay-context-b")
    )
    other_composer, _ = _composer(
        tmp_path / "b",
        request=other_request,
        operation_registry=other_operations,
        recipe_registry=other_recipes,
    )
    other_exact = _exact(other_request, other_recipe)
    other_composer.compose(other_exact)
    other_replay = other_composer.compose(other_exact)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_PROVENANCE_OPERATION_MISMATCH",
    ):
        GovernedTaskCompositionReceipt.model_validate(
            other_replay.receipt.model_dump(mode="json"),
            context=replay_validation_context(context),
        )


def test_external_receipt_scope_must_match_current_composition_request(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="external-receipt-scope"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    exact = _exact(request, recipe)
    result = composer.compose(exact)
    assert result.plan is not None

    external_payload = {
        "transaction_ref": result.receipt.transaction_ref,
        "intent_ref": result.receipt.intent_ref,
        "binding_ref": result.receipt.binding_ref,
        "state": result.receipt.external_action_state,
        "approval_validation_ref": result.receipt.approval_validation_ref,
        "authority_decision_ref": result.receipt.authority_decision_ref,
        "budget_reservation_ref": result.receipt.budget_reservation_ref,
        "budget_settlement_ref": result.receipt.budget_settlement_ref,
        "evidence_refs": list(result.receipt.evidence_refs),
        "reason_refs": list(result.receipt.external_action_reason_refs),
    }
    for field, drifted_ref in (
        (
            "transaction_ref",
            _pinned("transaction-ref:governed-task-composer", "drifted"),
        ),
        (
            "intent_ref",
            _pinned("intent-ref:governed-external-action", "drifted"),
        ),
        (
            "binding_ref",
            _pinned("authority-binding-ref:governed-external-action", "drifted"),
        ),
    ):
        drifted_payload = {**external_payload, field: drifted_ref}
        external_receipt = ExternalActionReceipt(
            receipt_ref=stable_governed_browser_ref(
                "receipt-ref:governed-external-action",
                drifted_payload,
            ),
            **drifted_payload,
        )
        blocked = task_composer_module._result_from_external_receipt(
            request=exact,
            recipe=recipe,
            external_receipt=external_receipt,
            plan=result.plan,
        )
        assert blocked.receipt.status == "preflight_blocked"
        assert blocked.receipt.reason_refs == (
            "reason-ref:governed-task-composer:external-receipt-scope-mismatch",
        )
        assert blocked.plan is None


def test_serialized_success_receipt_is_bound_to_recipe_transaction_and_intent(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="serialized-success-scope"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.status == "plan_ready"

    for field, drifted_ref in (
        (
            "transaction_ref",
            _pinned("transaction-ref:governed-task-composer", "copied-success"),
        ),
        (
            "intent_ref",
            _pinned("intent-ref:governed-external-action", "copied-success"),
        ),
    ):
        drifted = result.receipt.model_dump(mode="json")
        drifted[field] = drifted_ref
        drifted["external_action_receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            {
                "transaction_ref": drifted["transaction_ref"],
                "intent_ref": drifted["intent_ref"],
                "binding_ref": drifted["binding_ref"],
                "state": drifted["external_action_state"],
                "approval_validation_ref": drifted["approval_validation_ref"],
                "authority_decision_ref": drifted["authority_decision_ref"],
                "budget_reservation_ref": drifted["budget_reservation_ref"],
                "budget_settlement_ref": drifted["budget_settlement_ref"],
                "evidence_refs": drifted["evidence_refs"],
                "reason_refs": drifted["external_action_reason_refs"],
            },
        )
        drifted["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {key: value for key, value in drifted.items() if key != "receipt_ref"},
        )
        with pytest.raises(ValidationError, match="RECIPE_SNAPSHOT_MISMATCH"):
            GovernedTaskCompositionReceipt.model_validate(drifted)

    for field, drifted_ref in (
        (
            "approval_validation_ref",
            _pinned(
                "approval-validation-ref:governed-external-action",
                "copied-success-proof",
            ),
        ),
        (
            "authority_decision_ref",
            f"authority-policy-decision-ref:sha256:{'0' * 24}",
        ),
        (
            "budget_reservation_ref",
            _pinned("authority-budget-reservation-ref", "copied-success-proof"),
        ),
        (
            "budget_settlement_ref",
            _pinned("receipt-ref:authority-budget", "copied-success-proof"),
        ),
    ):
        drifted = result.receipt.model_dump(mode="json")
        drifted[field] = drifted_ref
        drifted["external_action_receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            {
                "transaction_ref": drifted["transaction_ref"],
                "intent_ref": drifted["intent_ref"],
                "binding_ref": drifted["binding_ref"],
                "state": drifted["external_action_state"],
                "approval_validation_ref": drifted["approval_validation_ref"],
                "authority_decision_ref": drifted["authority_decision_ref"],
                "budget_reservation_ref": drifted["budget_reservation_ref"],
                "budget_settlement_ref": drifted["budget_settlement_ref"],
                "evidence_refs": drifted["evidence_refs"],
                "reason_refs": drifted["external_action_reason_refs"],
            },
        )
        drifted["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {key: value for key, value in drifted.items() if key != "receipt_ref"},
        )
        with pytest.raises(
            ValidationError,
            match="EXTERNAL_RECEIPT_SNAPSHOT_MISMATCH",
        ):
            GovernedTaskCompositionReceipt.model_validate(drifted)


def test_serialized_non_success_receipt_validates_retained_proof_scope(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="serialized-blocked-proof"
    )
    kernel = GovernedExternalActionKernel(
        store=ExternalActionTransactionStore(tmp_path / "transactions.sqlite3"),
        approval_authority=LocalApprovalAuthority(),
        authority_leases_provider=lambda: [],
        readiness_provider=lambda item: _readiness(item),
        local_validation_enabled=True,
    )
    composer = ExactGovernedTaskComposer(
        operation_registry=operations,
        recipe_registry=recipes,
        kernel=kernel,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.status == "transaction_blocked"
    assert result.receipt.recipe_snapshot == recipe
    assert result.receipt.external_action_receipt_ref is not None

    missing_context = result.receipt.model_dump(mode="json")
    for field in (
        "recipe_snapshot",
        "composer_authority_ref",
        "envelope_ref",
        "external_action_receipt_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
    ):
        missing_context[field] = None
    for field in (
        "operation_refs",
        "evidence_refs",
        "external_action_reason_refs",
    ):
        missing_context[field] = []
    missing_context["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {key: value for key, value in missing_context.items() if key != "receipt_ref"},
    )
    with pytest.raises(ValidationError, match="EXTERNAL_PROOF_CONTEXT_REQUIRED"):
        GovernedTaskCompositionReceipt.model_validate(missing_context)

    scope_drift = result.receipt.model_dump(mode="json")
    scope_drift["operation_refs"] = [
        _pinned(
            "registered-operation-ref:governed-task-composer",
            "unrelated-blocked-operation",
        )
    ]
    scope_drift["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {key: value for key, value in scope_drift.items() if key != "receipt_ref"},
    )
    with pytest.raises(ValidationError, match="RECEIPT_SCOPE_MISMATCH"):
        GovernedTaskCompositionReceipt.model_validate(scope_drift)

    for field, drifted_ref in (
        (
            "external_action_receipt_ref",
            _pinned("receipt-ref:governed-external-action", "unrelated-block"),
        ),
        (
            "approval_validation_ref",
            _pinned(
                "approval-validation-ref:governed-external-action",
                "unrelated-block",
            ),
        ),
    ):
        proof_drift = result.receipt.model_dump(mode="json")
        proof_drift[field] = drifted_ref
        proof_drift["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {key: value for key, value in proof_drift.items() if key != "receipt_ref"},
        )
        with pytest.raises(ValidationError, match="EXTERNAL_RECEIPT_REF_MISMATCH"):
            GovernedTaskCompositionReceipt.model_validate(proof_drift)

    denial_reason_drift = result.receipt.model_dump(mode="json")
    denial_reason_drift["reason_refs"] = [
        "reason-ref:governed-task-composer:unrelated-denial"
    ]
    denial_reason_drift["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {
            key: value
            for key, value in denial_reason_drift.items()
            if key != "receipt_ref"
        },
    )
    with pytest.raises(ValidationError, match="DENIAL_REASON_MISMATCH"):
        GovernedTaskCompositionReceipt.model_validate(denial_reason_drift)


def test_missing_success_settlement_proof_returns_governed_non_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="missing-success-proof"
    )
    kernel, _ = _authorized_kernel(tmp_path, request)

    def settlement_without_receipt(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        return BudgetSettlement(allowed=True)

    monkeypatch.setattr(kernel._budget_gate, "settle", settlement_without_receipt)
    composer = ExactGovernedTaskComposer(
        operation_registry=operations,
        recipe_registry=recipes,
        kernel=kernel,
    )

    result = composer.compose(_exact(request, recipe))

    assert result.receipt.status == "outcome_ambiguous"
    assert result.receipt.external_action_state == "outcome_ambiguous"
    assert result.receipt.budget_settlement_ref is None
    assert result.receipt.reason_refs == (
        "reason-ref:governed-external-action:budget-settlement-ambiguous",
    )
    assert result.receipt.external_action_reason_refs == (
        "reason-ref:governed-external-action:budget-settlement-ambiguous",
    )
    assert result.receipt.external_receipt_snapshot is not None
    assert result.plan is None


def test_legacy_external_receipt_snapshot_preserves_absent_release_hash(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="legacy-external-snapshot"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.external_receipt_snapshot is not None
    legacy_payload = result.receipt.external_receipt_snapshot.model_dump(mode="json")
    legacy_payload.pop("budget_release_ref", None)

    restored = (
        task_composer_module.GovernedTaskCompositionExternalReceiptSnapshot.model_validate(
            legacy_payload
        )
    )

    assert restored.budget_release_ref is None
    assert restored.snapshot_ref == legacy_payload["snapshot_ref"]
    assert (
        getattr(
            task_composer_module.GovernedTaskCompositionExternalReceiptSnapshot.model_fields[
                "budget_release_ref"
            ],
            "exclude_if",
            None,
        )
        is None
    )


def test_legacy_whole_receipt_preserves_absent_release_hash(tmp_path: Path) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="legacy-whole-receipt"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    legacy_payload = result.receipt.model_dump(mode="json")
    legacy_payload.pop("budget_release_ref", None)
    external_snapshot = legacy_payload["external_receipt_snapshot"]
    assert isinstance(external_snapshot, dict)
    external_snapshot.pop("budget_release_ref", None)
    legacy_payload["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {
            key: value
            for key, value in legacy_payload.items()
            if key != "receipt_ref"
        },
    )

    restored = GovernedTaskCompositionReceipt.model_validate(legacy_payload)

    assert restored.receipt_ref == result.receipt.receipt_ref
    assert restored.budget_release_ref is None
    assert restored.external_receipt_snapshot is not None
    assert restored.external_receipt_snapshot.budget_release_ref is None
    assert (
        getattr(
            GovernedTaskCompositionReceipt.model_fields["budget_release_ref"],
            "exclude_if",
            None,
        )
        is None
    )


def test_serialized_external_receipt_snapshot_rejects_conflicting_rehashed_kernel_proofs(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="snapshot-conflicting-kernel-proofs"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.external_receipt_snapshot is not None
    forged = result.receipt.external_receipt_snapshot.model_dump(mode="json")
    forged["budget_release_ref"] = _pinned(
        "receipt-ref:authority-budget",
        "snapshot-conflicting-budget-release",
    )
    external_payload = {
        "transaction_ref": forged["transaction_ref"],
        "intent_ref": forged["intent_ref"],
        "binding_ref": forged["binding_ref"],
        "state": forged["state"],
        "approval_validation_ref": forged["approval_validation_ref"],
        "authority_decision_ref": forged["authority_decision_ref"],
        "budget_reservation_ref": forged["budget_reservation_ref"],
        "budget_release_ref": forged["budget_release_ref"],
        "budget_settlement_ref": forged["budget_settlement_ref"],
        "evidence_refs": forged["evidence_refs"],
        "reason_refs": forged["reason_refs"],
    }
    forged["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_payload,
    )
    forged["snapshot_ref"] = stable_governed_browser_ref(
        "external-receipt-snapshot-ref:governed-task-composer",
        {key: value for key, value in forged.items() if key != "snapshot_ref"},
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        task_composer_module.GovernedTaskCompositionExternalReceiptSnapshot.model_validate(
            forged
        )


def test_serialized_task_composition_receipt_rejects_conflicting_rehashed_kernel_proofs(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="receipt-conflicting-kernel-proofs"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    forged = result.receipt.model_dump(mode="json")
    forged["budget_release_ref"] = _pinned(
        "receipt-ref:authority-budget",
        "receipt-conflicting-budget-release",
    )
    external_payload = {
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
        "reason_refs": forged["external_action_reason_refs"],
    }
    forged["external_action_receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-external-action",
        external_payload,
    )
    identity_payload = {
        key: value for key, value in forged.items() if key != "receipt_ref"
    }
    external_snapshot = dict(identity_payload["external_receipt_snapshot"])
    if external_snapshot.get("budget_release_ref") is None:
        external_snapshot.pop("budget_release_ref", None)
    identity_payload["external_receipt_snapshot"] = external_snapshot
    forged["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        identity_payload,
    )

    with pytest.raises(
        ValidationError,
        match="GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_REF_MISMATCH",
    ):
        GovernedTaskCompositionReceipt.model_validate(forged)


@pytest.mark.parametrize(
    "missing_field",
    (
        "approval_validation_ref",
        "authority_decision_ref",
        "budget_reservation_ref",
        "budget_settlement_ref",
    ),
)
def test_incomplete_succeeded_kernel_proof_is_content_free_without_plan(
    missing_field: str,
) -> None:
    request, recipe, _, _ = _composition_context(
        suffix=f"incomplete-succeeded-kernel-proof-{missing_field}"
    )
    external_payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": "succeeded",
        "approval_validation_ref": _pinned(
            "approval-validation-ref:governed-external-action",
            "complete-proof",
        ),
        "authority_decision_ref": (
            f"authority-policy-decision-ref:sha256:{'a' * 24}"
        ),
        "budget_reservation_ref": _pinned(
            "authority-budget-reservation-ref",
            "complete-proof",
        ),
        "budget_settlement_ref": _pinned(
            "receipt-ref:authority-budget",
            "complete-proof",
        ),
        "evidence_refs": [
            recipe.recipe_ref,
            recipe.plan_ref,
            recipe.registry_ref,
            recipe.composer_authority_ref,
            *[step.operation_ref for step in recipe.steps],
        ],
        "reason_refs": [],
    }
    external_payload[missing_field] = None
    external_receipt = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            external_payload,
        ),
        **external_payload,
    )

    result = task_composer_module._result_from_external_receipt(
        request=_exact(request, recipe),
        recipe=recipe,
        external_receipt=external_receipt,
        plan=None,
    )

    assert result.receipt.status == "proof_incomplete"
    assert result.receipt.external_action_state == "succeeded"
    assert result.receipt.external_receipt_snapshot is not None
    assert result.receipt.reason_refs == (
        "reason-ref:governed-task-composer:kernel-proof_incomplete",
    )
    assert result.plan is None


@pytest.mark.parametrize(
    "evidence_mode",
    ("missing", "rebound"),
)
def test_incomplete_succeeded_kernel_evidence_is_content_free_without_plan(
    tmp_path: Path,
    evidence_mode: str,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix=f"incomplete-succeeded-evidence-{evidence_mode}"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    complete = composer.compose(_exact(request, recipe)).receipt
    evidence_refs = (
        ()
        if evidence_mode == "missing"
        else (_pinned("evidence-ref:governed-task-composer", "rebound"),)
    )
    external_payload = {
        "transaction_ref": complete.transaction_ref,
        "intent_ref": complete.intent_ref,
        "binding_ref": complete.binding_ref,
        "state": "succeeded",
        "approval_validation_ref": complete.approval_validation_ref,
        "authority_decision_ref": complete.authority_decision_ref,
        "budget_reservation_ref": complete.budget_reservation_ref,
        "budget_settlement_ref": complete.budget_settlement_ref,
        "evidence_refs": list(evidence_refs),
        "reason_refs": [],
    }
    external_receipt = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            external_payload,
        ),
        **external_payload,
    )

    result = task_composer_module._result_from_external_receipt(
        request=_exact(request, recipe),
        recipe=recipe,
        external_receipt=external_receipt,
        plan=None,
    )

    assert result.receipt.status == "proof_incomplete"
    assert result.receipt.evidence_refs == evidence_refs
    assert result.plan is None


@pytest.mark.parametrize("state", ("started", "prepared"))
def test_started_or_prepared_kernel_state_is_outcome_ambiguous(
    state: str,
) -> None:
    request, recipe, _, _ = _composition_context(
        suffix=f"{state}-kernel-state"
    )
    external_payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": state,
        "approval_validation_ref": None,
        "authority_decision_ref": None,
        "budget_reservation_ref": None,
        "budget_settlement_ref": None,
        "evidence_refs": [],
        "reason_refs": [
            _pinned("reason-ref:governed-task-composer", state)
        ],
    }
    external_receipt = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            external_payload,
        ),
        **external_payload,
    )

    result = task_composer_module._result_from_external_receipt(
        request=_exact(request, recipe),
        recipe=recipe,
        external_receipt=external_receipt,
        plan=None,
    )

    assert result.receipt.status == "outcome_ambiguous"
    assert result.receipt.external_action_state == state
    forged = result.receipt.model_dump(mode="json")
    forged["status"] = "failed"
    _rehash_task_composition_receipt(forged)
    with pytest.raises(
        ValidationError,
        match="GOVERNED_TASK_COMPOSER_RECEIPT_STATE_MISMATCH",
    ):
        GovernedTaskCompositionReceipt.model_validate(forged)


def test_preflight_receipt_rejects_orphan_replay_flag(tmp_path: Path) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="preflight-orphan-replay"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    blocked = composer.compose(
        _exact(request, recipe).model_copy(
            update={
                "recipe_ref": _pinned(
                    "composition-recipe-ref:governed-task-composer",
                    "missing-replay",
                )
            }
        )
    )
    forged = blocked.receipt.model_dump(mode="json")
    forged["replayed"] = True
    _rehash_task_composition_receipt(forged)

    with pytest.raises(
        ValidationError,
        match="GOVERNED_TASK_COMPOSER_EXTERNAL_PROOF_CONTEXT_INVALID",
    ):
        GovernedTaskCompositionReceipt.model_validate(forged)


def test_complete_success_proof_cannot_downgrade_to_proof_incomplete(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(
        suffix="complete-proof-downgrade"
    )
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.status == "plan_ready"
    forged = result.receipt.model_dump(mode="json")
    forged.update(
        {
            "status": "proof_incomplete",
            "reason_refs": [
                "reason-ref:governed-task-composer:kernel-proof_incomplete"
            ],
        }
    )
    _rehash_task_composition_receipt(forged)

    with pytest.raises(
        ValidationError,
        match="GOVERNED_TASK_COMPOSER_PROOF_INCOMPLETE_STATE_MISMATCH",
    ):
        GovernedTaskCompositionReceipt.model_validate(forged)


def test_expired_recipe_and_invalid_clock_fail_before_composition(
    tmp_path: Path,
) -> None:
    now = utc_now()
    request, recipe, operations, recipes = _composition_context(
        suffix="expired",
        created_at=now - timedelta(minutes=6),
        expires_at=now - timedelta(minutes=1),
    )
    composer, _ = _composer(
        tmp_path / "expired",
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
        clock=lambda: now,
    )
    expired = composer.compose(_exact(request, recipe))
    assert expired.receipt.reason_refs == (
        "reason-ref:governed-task-composer:recipe-expired",
    )
    assert expired.plan is None

    request2, recipe2, operations2, recipes2 = _composition_context(suffix="clock")
    composer2, _ = _composer(
        tmp_path / "clock",
        request=request2,
        operation_registry=operations2,
        recipe_registry=recipes2,
        clock=lambda: "not-a-clock",
    )
    invalid = composer2.compose(_exact(request2, recipe2))
    assert invalid.receipt.reason_refs == (
        "reason-ref:governed-task-composer:trusted-clock-invalid",
    )
    assert invalid.plan is None


def test_real_target_absent_human_and_more_than_eight_steps_are_denied() -> None:
    with pytest.raises(ValueError, match="REAL_TARGETS_INACTIVE"):
        _composition_context(
            suffix="external",
            target_kind=ExternalActionTargetKind.external,
        )
    with pytest.raises(ValueError, match="HUMAN_PRESENCE_REQUIRED"):
        _composition_context(suffix="absent", human_present=False)
    operation = _operation(
        suffix="limit",
        kind=GovernedTaskOperationKind.challenge_handoff,
        capability=AuthorityCapability.prepare,
    )
    steps = [
        build_governed_task_composition_step(
            ordinal=ordinal,
            operation_ref=operation.operation_ref,
        )
        for ordinal in range(1, 9)
    ]
    with pytest.raises(ValidationError):
        GovernedTaskCompositionStep(
            step_ref=_pinned(
                "composition-step-ref:governed-task-composer",
                "nine",
            ),
            ordinal=9,
            operation_ref=operation.operation_ref,
        )
    assert len(steps) == 8


def test_receipt_and_plan_are_safe_ref_only_and_record_no_intent_content(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="redaction")
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )

    result = composer.compose(_exact(request, recipe))
    serialized = result.model_dump_json()

    assert "send this" not in serialized
    assert "buy this" not in serialized
    assert "/Users/" not in serialized
    assert "Bearer " not in serialized
    assert '"raw_intent_recorded":false' in serialized
    assert '"complete_any_task_granted":false' in serialized
    assert '"composer_authority_inherited":false' in serialized
    assert '"operation_authorized":false' in serialized
    assert '"operation_executed":false' in serialized


def test_serialized_plan_cannot_rebind_a_registered_operation_or_plan_ref(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="tamper")
    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.plan is not None
    payload = result.plan.model_dump(mode="json")
    payload["steps"][0]["target_ref"] = _pinned(
        "source-target-ref:governed-task-composer",
        "rebound",
    )
    with pytest.raises(ValidationError, match="OPERATION_REF_MISMATCH"):
        GovernedTaskCompositionPlan.model_validate(payload)

    plan_ref_drift = result.plan.model_dump(mode="json")
    plan_ref_drift["plan_ref"] = _pinned(
        "composition-plan-ref:governed-task-composer",
        "rebound",
    )
    with pytest.raises(ValidationError, match="PLAN_REF_MISMATCH"):
        GovernedTaskCompositionPlan.model_validate(plan_ref_drift)

    validity_drift = result.plan.model_dump(mode="json")
    validity_drift["created_at"] = (
        result.plan.created_at - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(ValidationError, match="PLAN_PAYLOAD_REF_MISMATCH"):
        GovernedTaskCompositionPlan.model_validate(validity_drift)

    registry_drift = result.plan.model_dump(mode="json")
    registry_drift["registry_ref"] = (
        "operation-registry-ref:governed-task-composer:descriptive-alias"
    )
    with pytest.raises(ValidationError, match="HASH_PIN_REQUIRED"):
        GovernedTaskCompositionPlan.model_validate(registry_drift)

    proof_ref_drift = result.plan.model_dump(mode="json")
    proof_ref_drift["binding_ref"] = _pinned(
        "authority-binding-ref:governed-external-action",
        "rebound",
    )
    proof_ref_drift["recipe_ref"] = _pinned(
        "composition-recipe-ref:governed-task-composer",
        "rebound",
    )
    proof_ref_drift["composer_authority_ref"] = _pinned(
        "composer-authority-ref:governed-task-composer",
        "rebound",
    )
    proof_ref_drift["envelope_ref"] = governed_task_composition_envelope_ref(
        plan_ref=proof_ref_drift["plan_ref"],
        recipe_ref=proof_ref_drift["recipe_ref"],
        composer_authority_ref=proof_ref_drift["composer_authority_ref"],
        binding_ref=proof_ref_drift["binding_ref"],
    )
    with pytest.raises(ValidationError, match="PLAN_REF_MISMATCH"):
        GovernedTaskCompositionPlan.model_validate(proof_ref_drift)

    proof_ref_drift["plan_ref"] = governed_task_composition_plan_ref(
        plan_payload_ref=proof_ref_drift["plan_payload_ref"],
        recipe_ref=proof_ref_drift["recipe_ref"],
        composer_authority_ref=proof_ref_drift["composer_authority_ref"],
        binding_ref=proof_ref_drift["binding_ref"],
    )
    proof_ref_drift["envelope_ref"] = governed_task_composition_envelope_ref(
        plan_ref=proof_ref_drift["plan_ref"],
        recipe_ref=proof_ref_drift["recipe_ref"],
        composer_authority_ref=proof_ref_drift["composer_authority_ref"],
        binding_ref=proof_ref_drift["binding_ref"],
    )
    with pytest.raises(ValidationError, match="PLAN_RECIPE_MISMATCH"):
        GovernedTaskCompositionPlan.model_validate(proof_ref_drift)

    duplicate_operation = result.plan.model_dump(mode="json")
    duplicate_operation["steps"][1] = {
        **duplicate_operation["steps"][0],
        "ordinal": 2,
        "depends_on_step_refs": [
            duplicate_operation["steps"][0]["step_ref"],
        ],
    }
    duplicate_operation["steps"][1]["step_ref"] = build_governed_task_composition_step(
        ordinal=2,
        operation_ref=duplicate_operation["steps"][0]["operation_ref"],
        depends_on_step_refs=[
            duplicate_operation["steps"][0]["step_ref"],
        ],
    ).step_ref
    with pytest.raises(ValidationError, match="OPERATION_REUSE_DENIED"):
        GovernedTaskCompositionPlan.model_validate(duplicate_operation)

    duplicate_authority = result.plan.model_dump(mode="json")
    first_step = duplicate_authority["steps"][0]
    second_step = duplicate_authority["steps"][1]
    registered_payload = {
        "kind": second_step["kind"],
        "source_recipe_ref": second_step["source_recipe_ref"],
        "source_contract_ref": second_step["source_contract_ref"],
        "source_binding_ref": second_step["source_binding_ref"],
        "operation_authority_ref": first_step["operation_authority_ref"],
        "required_capability": second_step["required_capability"],
        "target_ref": second_step["target_ref"],
        "schema_ref": second_step["schema_ref"],
    }
    provisional_operation = RegisteredGovernedTaskOperation.model_construct(
        operation_ref="registered-operation-ref:governed-task-composer:pending",
        **registered_payload,
    )
    second_step["operation_ref"] = stable_governed_browser_ref(
        "registered-operation-ref:governed-task-composer",
        provisional_operation.model_dump(mode="json", exclude={"operation_ref"}),
    )
    second_step["operation_authority_ref"] = first_step["operation_authority_ref"]
    second_step["step_ref"] = build_governed_task_composition_step(
        ordinal=second_step["ordinal"],
        operation_ref=second_step["operation_ref"],
        depends_on_step_refs=second_step["depends_on_step_refs"],
    ).step_ref
    with pytest.raises(ValidationError, match="OPERATION_AUTHORITY_DUPLICATE"):
        GovernedTaskCompositionPlan.model_validate(duplicate_authority)


def test_recipe_registry_returns_defensive_copies_and_receipt_states_are_exact(
    tmp_path: Path,
) -> None:
    request, recipe, operations, recipes = _composition_context(suffix="defensive-copy")
    resolved = recipes.resolve(recipe.recipe_ref)
    assert resolved is not None
    with pytest.raises(AttributeError):
        resolved.steps[0].depends_on_step_refs.append(  # type: ignore[attr-defined]
            recipe.steps[1].step_ref
        )
    fresh = recipes.resolve(recipe.recipe_ref)
    assert fresh is not None
    assert fresh.steps[0].depends_on_step_refs == ()

    composer, _ = _composer(
        tmp_path,
        request=request,
        operation_registry=operations,
        recipe_registry=recipes,
    )
    result = composer.compose(_exact(request, recipe))
    assert result.receipt.status == "plan_ready"

    scope_drift = result.receipt.model_dump(mode="json")
    scope_drift["operation_refs"] = [
        _pinned(
            "registered-operation-ref:governed-task-composer",
            "unrelated-operation",
        )
    ]
    scope_drift["evidence_refs"] = [
        scope_drift["recipe_ref"],
        scope_drift["plan_ref"],
        scope_drift["registry_ref"],
        scope_drift["composer_authority_ref"],
        *scope_drift["operation_refs"],
    ]
    scope_drift["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {key: value for key, value in scope_drift.items() if key != "receipt_ref"},
    )
    with pytest.raises(ValidationError, match="RECEIPT_SCOPE_MISMATCH"):
        GovernedTaskCompositionReceipt.model_validate(scope_drift)

    for field, same_prefix_ref in (
        (
            "external_action_receipt_ref",
            _pinned("receipt-ref:governed-external-action", "unrelated-proof"),
        ),
        (
            "approval_validation_ref",
            _pinned(
                "approval-validation-ref:governed-external-action",
                "unrelated-proof",
            ),
        ),
        (
            "authority_decision_ref",
            f"authority-policy-decision-ref:sha256:{'0' * 24}",
        ),
        (
            "budget_reservation_ref",
            _pinned("authority-budget-reservation-ref", "unrelated-proof"),
        ),
        (
            "budget_settlement_ref",
            _pinned("receipt-ref:authority-budget", "unrelated-proof"),
        ),
    ):
        proof_drift = result.receipt.model_dump(mode="json")
        proof_drift[field] = same_prefix_ref
        proof_drift["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {key: value for key, value in proof_drift.items() if key != "receipt_ref"},
        )
        with pytest.raises(ValidationError, match="EXTERNAL_RECEIPT_REF_MISMATCH"):
            GovernedTaskCompositionReceipt.model_validate(proof_drift)

    mismatched = result.receipt.model_dump(mode="json")
    mismatched["status"] = "preflight_blocked"
    with pytest.raises(ValidationError, match="RECEIPT_STATE_MISMATCH"):
        GovernedTaskCompositionReceipt.model_validate(mismatched)

    blocked = composer.compose(
        _exact(request, recipe).model_copy(
            update={
                "recipe_ref": _pinned(
                    "composition-recipe-ref:governed-task-composer",
                    "missing-for-unpinned-receipt",
                )
            }
        )
    )
    assert blocked.receipt.status == "preflight_blocked"
    reasonless_receipt = blocked.receipt.model_dump(mode="json")
    reasonless_receipt["reason_refs"] = []
    reasonless_receipt["receipt_ref"] = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        {
            key: value
            for key, value in reasonless_receipt.items()
            if key != "receipt_ref"
        },
    )
    with pytest.raises(ValidationError, match="RECEIPT_REASON_REQUIRED"):
        GovernedTaskCompositionReceipt.model_validate(reasonless_receipt)

    for field, unrelated_ref, error in (
        (
            "external_action_receipt_ref",
            _pinned("receipt-ref:unrelated-kernel", "proof"),
            "EXTERNAL_ACTION_RECEIPT_REF_REQUIRED",
        ),
        (
            "approval_validation_ref",
            _pinned("approval-validation-ref:unrelated-kernel", "proof"),
            "APPROVAL_VALIDATION_REF_REQUIRED",
        ),
        (
            "authority_decision_ref",
            _pinned("authority-policy-decision-ref:unrelated-kernel", "proof"),
            "AUTHORITY_DECISION_REF_REQUIRED",
        ),
        (
            "budget_reservation_ref",
            _pinned("budget-reservation-ref:unrelated-kernel", "proof"),
            "BUDGET_RESERVATION_REF_REQUIRED",
        ),
        (
            "budget_settlement_ref",
            _pinned("receipt-ref:unrelated-budget", "proof"),
            "BUDGET_SETTLEMENT_REF_REQUIRED",
        ),
    ):
        wrong_lineage_receipt = result.receipt.model_dump(mode="json")
        wrong_lineage_receipt[field] = unrelated_ref
        wrong_lineage_receipt["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {
                key: value
                for key, value in wrong_lineage_receipt.items()
                if key != "receipt_ref"
            },
        )
        with pytest.raises(ValidationError, match=error):
            GovernedTaskCompositionReceipt.model_validate(wrong_lineage_receipt)

    for field, unpinned_value in (
        (
            "broad_intent_ref",
            "broad-intent-ref:governed-task-composer:descriptive-alias",
        ),
        (
            "intent_ref",
            "intent-ref:governed-external-action:descriptive-alias",
        ),
        (
            "registry_ref",
            "operation-registry-ref:governed-task-composer:descriptive-alias",
        ),
    ):
        unpinned_receipt = blocked.receipt.model_dump(mode="json")
        unpinned_receipt[field] = unpinned_value
        unpinned_receipt["receipt_ref"] = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            {
                key: value
                for key, value in unpinned_receipt.items()
                if key != "receipt_ref"
            },
        )
        with pytest.raises(ValidationError, match="HASH_PIN_REQUIRED"):
            GovernedTaskCompositionReceipt.model_validate(unpinned_receipt)


def test_static_item13_verifier_passes() -> None:
    assert verify() == []
