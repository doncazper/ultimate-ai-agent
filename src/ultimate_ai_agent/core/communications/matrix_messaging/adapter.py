from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from ultimate_ai_agent.core.authority import (
    AuthorityConstraintKind,
    AuthorityLease,
    AuthorityLeaseScope,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchAdapterResult,
    AuthorityDispatchFailureCategory,
    AuthorityDispatchRequest,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_execution_ref,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityLatencyClass,
    CapabilityPrivacyLevel,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    ContextPolicy,
    QualitySignals,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .constants import (
    NETWORK_OPERATIONS,
    MatrixMessagingOperation,
    matrix_messaging_lane,
    matrix_messaging_rollback_ref,
)
from .contracts import (
    MatrixMessagingCommand,
    MatrixMessagingDispatchMetadata,
    MatrixMessagingReadiness,
    matrix_messaging_exact_resource_refs,
    stable_matrix_messaging_ref,
)


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_matrix_messaging_capability_manifest(
    operation: MatrixMessagingOperation,
) -> CapabilityManifest:
    lane = matrix_messaging_lane(operation)
    destructive = lane.authority_capability.value == "destructive"
    external = operation in NETWORK_OPERATIONS and not destructive
    return CapabilityManifest(
        id=lane.capability_ref,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=f"Human-commanded Matrix {operation.value}",
        description="Execute one exact approved Matrix messaging or encrypted-outbox operation.",
        examples=["Send or persist one exact operator-authored message scope."],
        anti_examples=[
            "Autonomous or AI-triggered sends.",
            "Connector-wide or standing message authority.",
        ],
        input_schema={"type": "object", "required": ["request_fingerprint_ref"]},
        output_schema={"type": "object", "required": ["receipt_ref"]},
        input_modes=["safe_refs_plus_transient_private_material"],
        output_modes=["content_free_refs_and_status"],
        side_effects=(
            SideEffectLevel.destructive
            if destructive
            else SideEffectLevel.external
            if external
            else SideEffectLevel.write
        ),
        risk_level=RiskLevel.high,
        authority_level=(
            CapabilityAuthorityLevel.destructive
            if destructive
            else CapabilityAuthorityLevel.external
            if external
            else CapabilityAuthorityLevel.mutating
        ),
        approval_required=True,
        deterministic=False,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=operation in NETWORK_OPERATIONS,
        browser_runtime_allowed=False,
        connector_write_allowed=operation in NETWORK_OPERATIONS,
        sandbox_profile="matrix-rust-broker-loopback-keychain-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref", "request_fingerprint_ref"],
            max_context_refs=64,
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=300,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
            estimated_cost_usd=0,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=True,
            approval_required=True,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            deny_if_deprecated=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=(
                SideEffectLevel.destructive
                if destructive
                else SideEffectLevel.external
                if external
                else SideEffectLevel.write
            ),
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:msg-mx-008-messaging-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "lane_ref": lane.lane_ref,
            "adapter_ref": lane.adapter_ref,
            "provider_ref": "provider-ref:communications:matrix",
            "human_commanded": True,
            "autonomous_send": False,
            "request_scoped": True,
        },
    )


class _ImmediateMessagingHandle:
    def __init__(
        self,
        *,
        execution_ref: str,
        commit_validated_at: datetime,
    ) -> None:
        self._execution_ref = execution_ref
        self.commit_validated_at = commit_validated_at
        self._result: MatrixMessagingOperationResult | None = None
        self._collected = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    def bind_result(self, result: MatrixMessagingOperationResult) -> None:
        if self._result is not None or self._settled:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_RESULT_ALREADY_BOUND")
        self._result = result

    def abort(self) -> None:
        self._settled = True

    def finalize(self) -> None:
        if self._settled or self._finalized or not self._collected:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_FINALIZATION_INVALID")
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_SETTLEMENT_INVALID")
        self._settled = True

    def collect(self) -> AuthorityDispatchAdapterResult:
        if self._collected:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_ALREADY_COLLECTED")
        self._collected = True
        if self._result is None:
            raise RuntimeError("MATRIX_MESSAGING_HANDLE_RESULT_REQUIRED")
        return AuthorityDispatchAdapterResult(
            execution_ref=self._execution_ref,
            succeeded=self._result.succeeded,
            failure_category=(
                None
                if self._result.succeeded
                else AuthorityDispatchFailureCategory.permanent_adapter_error
            ),
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref=stable_matrix_messaging_ref(
                "actual-cost-ref:matrix-messaging",
                {"execution_ref": self._execution_ref, "cost_microusd": 0},
            ),
            evidence_refs=list(self._result.evidence_refs),
            safe_output=self._result.safe_output,
            safe_summary=self._result.safe_summary,
        )


class MatrixMessagingOperationResult:
    def __init__(
        self,
        *,
        succeeded: bool,
        safe_output: dict[str, object],
        evidence_refs: tuple[str, ...],
        safe_summary: str,
    ) -> None:
        self.succeeded = succeeded
        self.safe_output = safe_output
        self.evidence_refs = evidence_refs
        self.safe_summary = safe_summary


class MatrixMessagingAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        operation: MatrixMessagingOperation,
        executor: Callable[[MatrixMessagingCommand, str], MatrixMessagingOperationResult],
        executor_binding_ref: str,
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
        readiness_provider: Callable[[MatrixMessagingCommand], MatrixMessagingReadiness],
    ) -> None:
        self.operation = MatrixMessagingOperation(operation)
        self.lane = matrix_messaging_lane(operation)
        self._executor = executor
        self._executor_binding_ref = executor_binding_ref
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._manifest = build_matrix_messaging_capability_manifest(operation)
        self._policy = PolicyEngine(default_max_risk=RiskLevel.high)
        self.descriptor = AuthorityDispatchAdapterDescriptor(
            adapter_ref=self.lane.adapter_ref,
            domain=self.lane.authority_domain,
            capability=self.lane.authority_capability,
            capability_ref=self.lane.capability_ref,
            tool_ref=self.lane.tool_ref,
            approval_required=True,
            atomic_start_required=True,
            operation_count=1,
            estimated_cost_microusd=0,
            failure_cost_microusd=0,
            idempotent_replay_supported=True,
            rollback_ref=matrix_messaging_rollback_ref(operation),
            safe_disable_ref="safe-disable-ref:matrix-messenger:enabled",
            safe_summary=f"Execute one exact human-commanded Matrix {operation.value} operation.",
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:matrix-messaging",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "executor_binding_ref": executor_binding_ref,
                "manifest": self._manifest.model_dump(mode="json"),
            },
        )

    def _metadata(self, request: AuthorityDispatchRequest) -> MatrixMessagingDispatchMetadata:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        return MatrixMessagingDispatchMetadata.model_validate(tool_request.metadata)

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
            command = MatrixMessagingDispatchMetadata.model_validate(
                tool_request.metadata
            ).command
        except ValueError:
            return ["reason-ref:matrix-messaging:dispatch-metadata-invalid"]
        if command.operation != self.operation:
            reasons.append("reason-ref:matrix-messaging:operation-mismatch")
        if tool_request.tool_ref != self.lane.tool_ref:
            reasons.append("reason-ref:matrix-messaging:tool-ref-mismatch")
        if tool_request.tool_name != self.lane.tool_name:
            reasons.append("reason-ref:matrix-messaging:tool-name-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.matrix_messaging:
            reasons.append("reason-ref:matrix-messaging:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:matrix-messaging:embedded-authority-forbidden")
        expected_resources = set(matrix_messaging_exact_resource_refs(command))
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append("reason-ref:matrix-messaging:resource-binding-mismatch")
        if not self._has_exact_session_lease(request, expected_resources):
            reasons.append("reason-ref:matrix-messaging:exact-session-lease-required")
        try:
            policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:matrix-messaging:policy-denied")
        else:
            if request.action_request.constraints.get("policy_decision_ref") != policy_ref:
                reasons.append("reason-ref:matrix-messaging:policy-binding-mismatch")
        return list(dict.fromkeys(reasons))

    def runtime_prestart_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons = self.validate_request(request)
        command = self._metadata(request).command
        try:
            observation = MatrixMessagingReadiness.model_validate(
                self._readiness_provider(command)
            )
        except (TypeError, ValueError):
            reasons.append("reason-ref:matrix-messaging:readiness-invalid")
            return list(dict.fromkeys(reasons))
        if observation.request_fingerprint_ref != command.request_fingerprint_ref:
            reasons.append("reason-ref:matrix-messaging:readiness-request-mismatch")
        if observation.readiness_ref != command.readiness_ref:
            reasons.append("reason-ref:matrix-messaging:readiness-ref-mismatch")
        if observation.adapter_ref != self.lane.adapter_ref:
            reasons.append("reason-ref:matrix-messaging:readiness-adapter-mismatch")
        now = utc_now()
        if (
            observation.observed_at < command.request_created_at
            or observation.observed_at > now + timedelta(seconds=5)
            or observation.expires_at > command.start_deadline
        ):
            reasons.append("reason-ref:matrix-messaging:readiness-window-mismatch")
        if observation.status != "ready" or now >= observation.expires_at:
            reasons.append("reason-ref:matrix-messaging:readiness-fail-closed")
        if observation.kill_switch_engaged:
            reasons.append("reason-ref:matrix-messaging:kill-switch-engaged")
        if observation.safe_disable_active:
            reasons.append("reason-ref:matrix-messaging:safe-disable-active")
        if not observation.broker_integrity_verified:
            reasons.append("reason-ref:matrix-messaging:broker-integrity-required")
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        command = self._metadata(request).command
        task = TaskEnvelope(
            task_id=command.task_ref,
            user_request="Execute one exact human-commanded Matrix messaging operation.",
            objective="Produce content-free evidence for one exact approved message scope.",
            scope=[self.lane.capability_ref],
            out_of_scope=[
                "autonomous sends",
                "AI-triggered sends",
                "standing connector authority",
                "remote homeservers",
                "browser automation",
            ],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[self.lane.tool_ref],
            acceptance_criteria=["Return only safe refs and exact outcome state."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={
                "target_ref": command.target_ref,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        )
        decision = self._policy.can_execute(
            self._manifest,
            task,
            {
                "allowed_capability_ids": [self._manifest.id],
                "max_risk_level": RiskLevel.high.value,
                "capability_health": {self._manifest.id: "healthy"},
                "coordination_mode": CoordinationMode.workflow_node.value,
                "approval_available": True,
                "connector_write_allowed": True,
            },
        )
        approval = (
            decision.status == PolicyDecisionStatus.approval_required
            and decision.requires_approval
        )
        if not approval:
            raise ValueError("MATRIX_MESSAGING_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:matrix-messaging",
            {
                "decision": decision.model_dump(mode="json"),
                "operation": self.operation.value,
                "dispatch_ref": request.dispatch_ref,
                "lease_ref": request.lease_ref,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        )

    def claim_request_state(self, _dispatch_ref: str) -> None:
        return

    def release_request_state(self, _dispatch_ref: str) -> None:
        return

    def request_state_active(self, _dispatch_ref: str) -> bool:
        return False

    def start(
        self,
        request: AuthorityDispatchRequest,
        *,
        validate_commit_fence: Callable[[], tuple[list[str], datetime]],
        claim_handle: Callable[[_ImmediateMessagingHandle], _ImmediateMessagingHandle],
    ) -> _ImmediateMessagingHandle:
        reasons, validated_at = validate_commit_fence()
        if reasons:
            raise RuntimeError("MATRIX_MESSAGING_COMMIT_FENCE_DENIED")
        if request.approval_validation_request is None:
            raise RuntimeError("MATRIX_MESSAGING_APPROVAL_REQUIRED")
        command = self._metadata(request).command
        handle = _ImmediateMessagingHandle(
            execution_ref=authority_dispatch_execution_ref(request),
            commit_validated_at=validated_at,
        )
        claimed = claim_handle(handle)
        claimed.bind_result(
            self._executor(
                command, request.approval_validation_request.approval_ref
            )
        )
        return claimed

    def invoke(self, request: AuthorityDispatchRequest) -> AuthorityDispatchAdapterResult:
        del request
        raise RuntimeError("MATRIX_MESSAGING_ATOMIC_START_REQUIRED")

    def _has_exact_session_lease(
        self,
        request: AuthorityDispatchRequest,
        expected_resources: set[str],
    ) -> bool:
        lease = next(
            (
                item
                for item in self._authority_leases_provider()
                if item.lease_ref == request.lease_ref
            ),
            None,
        )
        if (
            lease is None
            or not lease.is_active()
            or lease.scope != AuthorityLeaseScope.session.value
        ):
            return False
        return any(
            AuthorityConstraintKind(constraint.kind)
            == AuthorityConstraintKind.resource_refs
            and set(constraint.allowed_refs) == expected_resources
            for constraint in lease.authority_constraints
        )


__all__ = [
    "MatrixMessagingAuthorityDispatchAdapter",
    "MatrixMessagingOperationResult",
    "build_matrix_messaging_capability_manifest",
]
