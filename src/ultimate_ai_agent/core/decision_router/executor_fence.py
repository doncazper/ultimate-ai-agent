from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalValidationRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.decision_router.turn_contracts import (
    ApprovalPolicy,
    InvocationPolicy,
    StatePolicy,
    ToolChoicePolicy,
    ToolPolicy,
    TurnContractKind,
    TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


EXECUTOR_FENCE_CONTRACT_REF = "contract-ref:turn-contract-router:executor-fence:v1"
LOCAL_APPROVAL_AUTHORITY_REF = "local-approval-authority:exact-scope"
LOCAL_APPROVAL_VALIDATION_STATUS = "local_approval_authority_exact_scope_validated"
EXECUTOR_FENCE_APPROVAL_ACTION = "execute_turn_contract_action"


class ExecutorFenceRequest(BaseModel):
    contract_ref: str = EXECUTOR_FENCE_CONTRACT_REF
    fence_request_ref: str = Field(..., min_length=1)
    invocation_policy: InvocationPolicy
    local_approval_authority_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_validation_request: ApprovalValidationRequest
    approval_validation_receipt_ref: str = Field(..., min_length=1)
    approval_validation_scope_ref: str = Field(..., min_length=1)
    approval_validation_status: str = Field(..., min_length=1)
    requested_approval_scope_ref: str = Field(..., min_length=1)
    requested_action_scope_ref: str = Field(..., min_length=1)
    requested_tool_ref: str = Field(..., min_length=1)
    requested_arguments_ref: str = Field(..., min_length=1)
    requested_merchant_ref: str = Field(..., min_length=1)
    requested_recipient_ref: str = Field(..., min_length=1)
    requested_account_ref: str = Field(..., min_length=1)
    requested_cost_ref: str = Field(..., min_length=1)
    requested_credential_broker_ref: str = Field(..., min_length=1)
    requested_risk_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "ExecutorFenceRequest":
        if self.contract_ref != EXECUTOR_FENCE_CONTRACT_REF:
            raise ValueError("unexpected executor fence contract ref")
        for field_name in (
            "contract_ref",
            "fence_request_ref",
            "local_approval_authority_ref",
            "approval_ref",
            "approval_validation_receipt_ref",
            "approval_validation_scope_ref",
            "requested_approval_scope_ref",
            "requested_action_scope_ref",
            "requested_tool_ref",
            "requested_arguments_ref",
            "requested_merchant_ref",
            "requested_recipient_ref",
            "requested_account_ref",
            "requested_cost_ref",
            "requested_credential_broker_ref",
            "requested_risk_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        validate_safe_task_text(self.approval_validation_status, "approval_validation_status")
        if self.approval_validation_request.approval_ref != self.approval_ref:
            raise ValueError("approval validation request ref must match executor fence approval ref")
        if self.approval_validation_request.requested_action != EXECUTOR_FENCE_APPROVAL_ACTION:
            raise ValueError("approval validation request action must match executor fence action")
        expected_resource_refs = _expected_approval_resource_refs(self.invocation_policy)
        missing_resource_refs = sorted(
            set(expected_resource_refs).difference(self.approval_validation_request.resource_refs)
        )
        if missing_resource_refs:
            raise ValueError(f"approval validation request missing exact resource ref: {missing_resource_refs[0]}")
        return self


class ExecutorFenceDecision(BaseModel):
    contract_ref: str = EXECUTOR_FENCE_CONTRACT_REF
    fence_decision_ref: str = Field(..., min_length=1)
    fence_request_ref: str = Field(..., min_length=1)
    fence_passed: bool
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_CONTRACT_ROUTER_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    receipt_required: bool = False
    action_log_required: bool = False
    execution_performed: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> "ExecutorFenceDecision":
        if self.contract_ref != EXECUTOR_FENCE_CONTRACT_REF:
            raise ValueError("unexpected executor fence contract ref")
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.fence_decision_ref, "fence_decision_ref")
        validate_task_ref(self.fence_request_ref, "fence_request_ref")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for ref in self.reason_refs:
            validate_task_ref(ref, "reason_refs")
        for ref in self.blocked_authority_refs:
            validate_task_ref(ref, "blocked_authority_refs")
        if self.execution_performed:
            raise ValueError("executor fence must not perform execution")
        if not all(
            (
                self.no_runtime_model_call_performed,
                self.no_provider_call_performed,
                self.no_tool_execution_performed,
                self.no_action_execution_performed,
                self.no_shell_subprocess_performed,
                self.no_browser_network_performed,
                self.no_connector_write_performed,
            )
        ):
            raise ValueError("executor fence decision must remain no-effect")
        if self.fence_passed and not all((self.receipt_required, self.action_log_required)):
            raise ValueError("executor fence pass requires receipt and action log posture")
        return self


def evaluate_executor_fence(
    request: ExecutorFenceRequest,
    *,
    approval_authority: LocalApprovalAuthority | None = None,
) -> ExecutorFenceDecision:
    parsed = request if isinstance(request, ExecutorFenceRequest) else ExecutorFenceRequest(**request)
    policy = parsed.invocation_policy
    reason_refs: list[str] = []

    if policy.turn_contract != TurnContractKind.execute_approved_action.value:
        reason_refs.append("reason-ref:executor-fence:approval-missing")
    if policy.approval_policy != ApprovalPolicy.already_approved_exact_scope.value:
        reason_refs.append("reason-ref:executor-fence:approval-scope-not-approved")
    if policy.tool_policy != ToolPolicy.exact_approved_tool_only.value:
        reason_refs.append("reason-ref:executor-fence:tool-policy-not-exact")
    if policy.tool_choice != ToolChoicePolicy.exact_approved.value:
        reason_refs.append("reason-ref:executor-fence:tool-choice-not-exact")
    if not all((policy.receipt_required, policy.durable_state, policy.state_policy == StatePolicy.receipt_action_log.value)):
        reason_refs.append("reason-ref:executor-fence:receipt-action-log-required")
    if not policy.execution_ready:
        reason_refs.append("reason-ref:executor-fence:execution-not-ready")
    if policy.tools != [policy.allowed_tool_ref]:
        reason_refs.append("reason-ref:executor-fence:policy-tool-list-mismatch")
    if (
        parsed.local_approval_authority_ref != LOCAL_APPROVAL_AUTHORITY_REF
        or parsed.approval_validation_status != LOCAL_APPROVAL_VALIDATION_STATUS
        or parsed.approval_validation_receipt_ref != _expected_approval_validation_receipt_ref(parsed)
    ):
        reason_refs.append("reason-ref:executor-fence:local-approval-authority-validation-missing")
    if approval_authority is None:
        reason_refs.append("reason-ref:executor-fence:local-approval-authority-validation-missing")
    else:
        validation_decision = approval_authority.validate(parsed.approval_validation_request)
        if not validation_decision.allowed or validation_decision.matched_grant_ref != parsed.approval_ref:
            reason_refs.append("reason-ref:executor-fence:local-approval-authority-validation-missing")
    _append_mismatch(
        reason_refs,
        parsed.approval_validation_scope_ref,
        policy.approval_scope_ref,
        "reason-ref:executor-fence:approval-validation-scope-mismatch",
    )

    _append_mismatch(
        reason_refs,
        parsed.requested_approval_scope_ref,
        policy.approval_scope_ref,
        "reason-ref:executor-fence:approval-scope-mismatch",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_action_scope_ref,
        policy.action_scope_ref,
        "reason-ref:executor-fence:action-scope-mismatch",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_tool_ref,
        policy.allowed_tool_ref,
        "reason-ref:executor-fence:tool-mismatch",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_arguments_ref,
        policy.allowed_arguments_ref,
        "reason-ref:executor-fence:arguments-mismatch",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_merchant_ref,
        policy.allowed_merchant_ref,
        "reason-ref:executor-fence:merchant-expansion",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_recipient_ref,
        policy.allowed_recipient_ref,
        "reason-ref:executor-fence:recipient-expansion",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_account_ref,
        policy.allowed_account_ref,
        "reason-ref:executor-fence:account-expansion",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_cost_ref,
        policy.allowed_cost_ref,
        "reason-ref:executor-fence:cost-expansion",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_credential_broker_ref,
        policy.allowed_credential_broker_ref,
        "reason-ref:executor-fence:credential-broker-expansion",
    )
    _append_mismatch(
        reason_refs,
        parsed.requested_risk_ref,
        policy.allowed_risk_ref,
        "reason-ref:executor-fence:risk-class-mismatch",
    )

    deduped_reasons = _dedupe(reason_refs)
    fence_passed = not deduped_reasons
    return ExecutorFenceDecision(
        fence_decision_ref=f"executor-fence-decision:{parsed.fence_request_ref.rsplit(':', 1)[-1]}",
        fence_request_ref=parsed.fence_request_ref,
        fence_passed=fence_passed,
        safe_summary=(
            "Executor fence validated exact approved scope without execution."
            if fence_passed
            else "Executor fence blocked execution because exact approved scope validation failed."
        ),
        reason_refs=deduped_reasons or ["reason-ref:executor-fence:exact-approved-scope-validated"],
        receipt_required=bool(policy.receipt_required),
        action_log_required=bool(policy.durable_state and policy.state_policy == StatePolicy.receipt_action_log.value),
    )


def _append_mismatch(
    reason_refs: list[str],
    requested_ref: str,
    approved_ref: str | None,
    reason_ref: str,
) -> None:
    if approved_ref is None or requested_ref != approved_ref:
        reason_refs.append(reason_ref)


def _expected_approval_resource_refs(policy: InvocationPolicy) -> list[str]:
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


def _expected_approval_validation_receipt_ref(request: ExecutorFenceRequest) -> str:
    approval_suffix = request.approval_ref.rsplit(":", 1)[-1]
    scope_suffix = request.approval_validation_scope_ref.rsplit(":", 1)[-1]
    return f"approval-validation-receipt:executor-fence:{approval_suffix}:{scope_suffix}"


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
