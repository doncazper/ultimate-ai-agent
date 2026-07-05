from ultimate_ai_agent.core.decision_router import (
    ApprovedExecutionScope,
    ExecutorFenceRequest,
    TurnContractKind,
    TurnDecision,
    compile_invocation_policy,
    evaluate_executor_fence,
)
from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    ApprovalValidationRequest,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.decision_router.executor_fence import (
    EXECUTOR_FENCE_APPROVAL_ACTION,
    LOCAL_APPROVAL_AUTHORITY_REF,
    LOCAL_APPROVAL_VALIDATION_STATUS,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification


def _scope() -> ApprovedExecutionScope:
    return ApprovedExecutionScope(
        scope_ref="approved-scope:executor-fence:test",
        approval_scope_ref="approval-scope:executor-fence:test",
        action_scope_ref="action-scope:executor-fence:test",
        tool_ref="tool-ref:executor-fence:test",
        arguments_ref="arguments-ref:executor-fence:test",
        merchant_ref="merchant-ref:executor-fence:test",
        recipient_ref="recipient-ref:executor-fence:test",
        account_ref="account-ref:executor-fence:test",
        cost_ref="cost-ref:executor-fence:test",
        credential_broker_ref="credential-broker-ref:executor-fence:test",
        risk_ref="risk-ref:executor-fence:test",
    )


def _policy():
    scope = _scope()
    decision = TurnDecision(
        decision_ref="turn-decision:executor-fence:test",
        turn_contract=TurnContractKind.execute_approved_action,
        confidence=0.99,
        safe_summary="Reviewed exact execution posture.",
        reason_refs=["reason-ref:executor-fence:test"],
        source_refs=["source:executor-fence:test"],
        evidence_refs=["evidence:executor-fence:test"],
        approval_scope_ref=scope.approval_scope_ref,
        action_scope_ref=scope.action_scope_ref,
        approved_tool_ref=scope.tool_ref,
        approved_arguments_ref=scope.arguments_ref,
        approved_execution_scope=scope,
    )
    return compile_invocation_policy(decision)


def _actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="actor:executor-fence:test",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _data_classification() -> DataClassification:
    return DataClassification(
        classification=ClassificationValue.project_private,
        source="executor-fence-test",
    )


def _approval_resource_refs(policy) -> list[str]:
    return [
        ref
        for ref in (
            policy.approval_scope_ref,
            policy.action_scope_ref,
            policy.allowed_tool_ref,
            policy.allowed_arguments_ref,
            policy.allowed_merchant_ref,
            policy.allowed_recipient_ref,
            policy.allowed_account_ref,
            policy.allowed_cost_ref,
            policy.allowed_credential_broker_ref,
            policy.allowed_risk_ref,
        )
        if ref is not None
    ]


def _approval_validation_request(policy, approval_ref: str) -> ApprovalValidationRequest:
    return ApprovalValidationRequest(
        approval_ref=approval_ref,
        run_id="run:executor-fence:test",
        subject_type=ApprovalSubjectType.external_action,
        subject_id="subject:executor-fence:test",
        requested_action=EXECUTOR_FENCE_APPROVAL_ACTION,
        actor_context=_actor_context(),
        resource_refs=_approval_resource_refs(policy),
        risk_level=ApprovalRiskLevel.high,
        data_classification=_data_classification(),
        purpose="Validate exact executor fence scope.",
        event_ref="event:executor-fence:test",
    )


def _authority_for_request(request: ExecutorFenceRequest) -> LocalApprovalAuthority:
    validation_request = request.approval_validation_request
    authority = LocalApprovalAuthority()
    approval_request = ApprovalRequest(
        approval_request_id="approval-request:executor-fence:test",
        run_id=validation_request.run_id,
        subject_type=validation_request.subject_type,
        subject_id=validation_request.subject_id,
        actor_context=validation_request.actor_context,
        requested_action=validation_request.requested_action,
        purpose=validation_request.purpose,
        risk_level=validation_request.risk_level,
        data_classification=validation_request.data_classification,
        resource_refs=validation_request.resource_refs,
        event_ref=validation_request.event_ref,
        trace_id="trace:executor-fence:test",
    )
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="actor:executor-fence:approver",
        approval_ref=request.approval_ref,
    )
    return authority


def _request(**overrides: object) -> ExecutorFenceRequest:
    scope = _scope()
    policy = overrides.pop("invocation_policy", None) or _policy()
    approval_ref = "approval-ref:executor-fence:test"
    values = {
        "fence_request_ref": "executor-fence-request:test",
        "invocation_policy": policy,
        "local_approval_authority_ref": LOCAL_APPROVAL_AUTHORITY_REF,
        "approval_ref": approval_ref,
        "approval_validation_request": _approval_validation_request(policy, approval_ref),
        "approval_validation_receipt_ref": "approval-validation-receipt:executor-fence:test:test",
        "approval_validation_scope_ref": scope.approval_scope_ref,
        "approval_validation_status": LOCAL_APPROVAL_VALIDATION_STATUS,
        "requested_approval_scope_ref": scope.approval_scope_ref,
        "requested_action_scope_ref": scope.action_scope_ref,
        "requested_tool_ref": scope.tool_ref,
        "requested_arguments_ref": scope.arguments_ref,
        "requested_merchant_ref": scope.merchant_ref,
        "requested_recipient_ref": scope.recipient_ref,
        "requested_account_ref": scope.account_ref,
        "requested_cost_ref": scope.cost_ref,
        "requested_credential_broker_ref": scope.credential_broker_ref,
        "requested_risk_ref": scope.risk_ref,
    }
    values.update(overrides)
    return ExecutorFenceRequest(**values)


def test_executor_fence_passes_exact_approved_scope_without_execution() -> None:
    request = _request()
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is True
    assert decision.reason_refs == ["reason-ref:executor-fence:exact-approved-scope-validated"]
    assert decision.receipt_required is True
    assert decision.action_log_required is True
    assert decision.execution_performed is False
    assert decision.no_tool_execution_performed is True
    assert decision.no_action_execution_performed is True


def test_executor_fence_rejects_execution_when_approval_missing() -> None:
    approval_policy = compile_invocation_policy(
        TurnDecision(
            decision_ref="turn-decision:approval-required:test",
            turn_contract=TurnContractKind.approval_required,
            confidence=0.8,
            safe_summary="Reviewed approval boundary.",
            reason_refs=["reason-ref:executor-fence:approval-required"],
            source_refs=["source:executor-fence:test"],
            evidence_refs=["evidence:executor-fence:test"],
        )
    )
    request = _request(invocation_policy=approval_policy)
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:approval-missing" in decision.reason_refs


def test_executor_fence_rejects_action_id_mismatch() -> None:
    request = _request(requested_action_scope_ref="action-scope:executor-fence:other")
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:action-scope-mismatch" in decision.reason_refs


def test_executor_fence_rejects_missing_local_approval_validation() -> None:
    request = _request(approval_validation_status="approval_ref_only")
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert (
        "reason-ref:executor-fence:local-approval-authority-validation-missing"
        in decision.reason_refs
    )


def test_executor_fence_rejects_without_local_approval_authority() -> None:
    request = _request()
    decision = evaluate_executor_fence(request)

    assert decision.fence_passed is False
    assert (
        "reason-ref:executor-fence:local-approval-authority-validation-missing"
        in decision.reason_refs
    )


def test_executor_fence_rejects_unknown_local_approval_ref() -> None:
    request = _request()
    decision = evaluate_executor_fence(request, approval_authority=LocalApprovalAuthority())

    assert decision.fence_passed is False
    assert (
        "reason-ref:executor-fence:local-approval-authority-validation-missing"
        in decision.reason_refs
    )


def test_executor_fence_rejects_unbound_approval_validation_receipt_ref() -> None:
    request = _request(approval_validation_receipt_ref="approval-validation-receipt:executor-fence:other")
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert (
        "reason-ref:executor-fence:local-approval-authority-validation-missing"
        in decision.reason_refs
    )


def test_executor_fence_rejects_approval_validation_scope_mismatch() -> None:
    request = _request(approval_validation_scope_ref="approval-scope:executor-fence:other")
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:approval-validation-scope-mismatch" in decision.reason_refs


def test_executor_fence_rejects_tool_or_arguments_mismatch() -> None:
    tool_request = _request(requested_tool_ref="tool-ref:executor-fence:other")
    args_request = _request(requested_arguments_ref="arguments-ref:executor-fence:other")
    tool_decision = evaluate_executor_fence(
        tool_request,
        approval_authority=_authority_for_request(tool_request),
    )
    args_decision = evaluate_executor_fence(
        args_request,
        approval_authority=_authority_for_request(args_request),
    )

    assert tool_decision.fence_passed is False
    assert "reason-ref:executor-fence:tool-mismatch" in tool_decision.reason_refs
    assert args_decision.fence_passed is False
    assert "reason-ref:executor-fence:arguments-mismatch" in args_decision.reason_refs


def test_executor_fence_rejects_payment_booking_or_order_expansion() -> None:
    request = _request(
        requested_merchant_ref="merchant-ref:executor-fence:expanded",
        requested_cost_ref="cost-ref:executor-fence:expanded",
        requested_credential_broker_ref="credential-broker-ref:executor-fence:expanded",
    )
    decision = evaluate_executor_fence(
        request,
        approval_authority=_authority_for_request(request),
    )

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:merchant-expansion" in decision.reason_refs
    assert "reason-ref:executor-fence:cost-expansion" in decision.reason_refs
    assert "reason-ref:executor-fence:credential-broker-expansion" in decision.reason_refs


def test_executor_fence_rejects_recipient_or_account_expansion() -> None:
    request = _request(
        requested_recipient_ref="recipient-ref:executor-fence:expanded",
        requested_account_ref="account-ref:executor-fence:expanded",
    )
    decision = evaluate_executor_fence(
        request,
        approval_authority=_authority_for_request(request),
    )

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:recipient-expansion" in decision.reason_refs
    assert "reason-ref:executor-fence:account-expansion" in decision.reason_refs


def test_executor_fence_requires_receipt_action_log_posture() -> None:
    approval_policy = compile_invocation_policy(
        TurnDecision(
            decision_ref="turn-decision:approval-envelope:test",
            turn_contract=TurnContractKind.approval_required,
            confidence=0.8,
            safe_summary="Reviewed approval boundary.",
            reason_refs=["reason-ref:executor-fence:approval-envelope"],
            source_refs=["source:executor-fence:test"],
            evidence_refs=["evidence:executor-fence:test"],
        )
    )
    request = _request(invocation_policy=approval_policy)
    decision = evaluate_executor_fence(request, approval_authority=_authority_for_request(request))

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:receipt-action-log-required" in decision.reason_refs
