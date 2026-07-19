from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

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
from ultimate_ai_agent.core.time import utc_now


def _pinned(prefix: str, suffix: str) -> str:
    return stable_governed_browser_ref(prefix, {"suffix": suffix})


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
    with pytest.raises(AttributeError):
        result.receipt.evidence_refs.append(  # type: ignore[attr-defined]
            recipe.recipe_ref
        )
    assert result.plan is not None
    assert [step.ordinal for step in result.plan.steps] == [1, 2]
    assert result.plan.steps[1].depends_on_step_refs == (
        result.plan.steps[0].step_ref,
    )
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
        "source_contract_ref": _pinned(
            "source-contract-ref:source-system", "exact"
        ),
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
    for broad_authority_ref in (
        _pinned("capabilities:any", "broad-source"),
        _pinned("authorities:all", "broad-source"),
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
    assert result.plan is None
    assert not result.receipt.automatic_retry_allowed


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
                    update={"idempotency_ref": _ref("idempotency", "drifted")}
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
    rebound_plan = GovernedTaskCompositionPlan.model_validate(proof_ref_drift)
    assert rebound_plan.plan_ref != result.plan.plan_ref

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
