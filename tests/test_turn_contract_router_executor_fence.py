from ultimate_ai_agent.core.decision_router import (
    ApprovedExecutionScope,
    ExecutorFenceRequest,
    TurnContractKind,
    TurnDecision,
    compile_invocation_policy,
    evaluate_executor_fence,
)


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


def _request(**overrides: str) -> ExecutorFenceRequest:
    scope = _scope()
    values = {
        "fence_request_ref": "executor-fence-request:test",
        "invocation_policy": _policy(),
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
    decision = evaluate_executor_fence(_request())

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
    decision = evaluate_executor_fence(request)

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:approval-missing" in decision.reason_refs


def test_executor_fence_rejects_action_id_mismatch() -> None:
    decision = evaluate_executor_fence(
        _request(requested_action_scope_ref="action-scope:executor-fence:other")
    )

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:action-scope-mismatch" in decision.reason_refs


def test_executor_fence_rejects_tool_or_arguments_mismatch() -> None:
    tool_decision = evaluate_executor_fence(_request(requested_tool_ref="tool-ref:executor-fence:other"))
    args_decision = evaluate_executor_fence(
        _request(requested_arguments_ref="arguments-ref:executor-fence:other")
    )

    assert tool_decision.fence_passed is False
    assert "reason-ref:executor-fence:tool-mismatch" in tool_decision.reason_refs
    assert args_decision.fence_passed is False
    assert "reason-ref:executor-fence:arguments-mismatch" in args_decision.reason_refs


def test_executor_fence_rejects_payment_booking_or_order_expansion() -> None:
    decision = evaluate_executor_fence(
        _request(
            requested_merchant_ref="merchant-ref:executor-fence:expanded",
            requested_cost_ref="cost-ref:executor-fence:expanded",
            requested_credential_broker_ref="credential-broker-ref:executor-fence:expanded",
        )
    )

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:merchant-expansion" in decision.reason_refs
    assert "reason-ref:executor-fence:cost-expansion" in decision.reason_refs
    assert "reason-ref:executor-fence:credential-broker-expansion" in decision.reason_refs


def test_executor_fence_rejects_recipient_or_account_expansion() -> None:
    decision = evaluate_executor_fence(
        _request(
            requested_recipient_ref="recipient-ref:executor-fence:expanded",
            requested_account_ref="account-ref:executor-fence:expanded",
        )
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
    decision = evaluate_executor_fence(_request(invocation_policy=approval_policy))

    assert decision.fence_passed is False
    assert "reason-ref:executor-fence:receipt-action-log-required" in decision.reason_refs
