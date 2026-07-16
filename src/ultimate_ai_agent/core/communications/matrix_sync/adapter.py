from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

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
    AuthorityDispatchAtomicStartRecoveryRequired,
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
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind
from ultimate_ai_agent.core.time import utc_now

from .constants import (
    MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
    MatrixSyncLane,
    MatrixSyncOperation,
    matrix_sync_lane,
)
from .contracts import (
    MatrixSyncCommand,
    MatrixSyncDispatchMetadata,
    MatrixSyncReadinessObservation,
    MatrixSyncReadinessStatus,
    matrix_sync_exact_resource_refs,
    stable_matrix_sync_ref,
)


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class MatrixSyncOperationResult:
    succeeded: bool
    safe_output: dict[str, object]
    evidence_refs: tuple[str, ...]
    safe_summary: str
    abort_callback: Callable[[], None] | None = field(
        default=None,
        repr=False,
        compare=False,
    )


def build_matrix_sync_capability_manifest(
    operation: MatrixSyncOperation,
) -> CapabilityManifest:
    lane = matrix_sync_lane(operation)
    composed = operation in MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS
    mutation = lane.authority_capability.value in {"mutate", "write", "destructive"}
    destructive = lane.authority_capability.value == "destructive"
    return CapabilityManifest(
        id=lane.capability_ref,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=f"Governed Matrix {operation.value}",
        description=(
            "Execute one exact bounded Matrix GET read."
            if composed
            else "Declare one exact Matrix operation whose canonical executor is unavailable."
        ),
        examples=[
            "Read one exact Matrix scope or update one encrypted cache generation."
        ],
        anti_examples=[
            "Send events, mutate rooms, emit typing, or send read receipts."
        ],
        input_schema={"type": "object", "required": ["request_fingerprint_ref"]},
        output_schema={"type": "object", "required": ["result_ref"]},
        input_modes=["safe_refs_plus_transient_private_material"],
        output_modes=["content_free_refs_counts_and_status"],
        side_effects=(
            SideEffectLevel.destructive
            if destructive
            else SideEffectLevel.write
            if mutation
            else SideEffectLevel.read
        ),
        risk_level=RiskLevel.high if mutation else RiskLevel.low,
        authority_level=(
            CapabilityAuthorityLevel.destructive
            if destructive
            else CapabilityAuthorityLevel.mutating
            if mutation
            else CapabilityAuthorityLevel.read_only
        ),
        approval_required=lane.approval_required,
        deterministic=False,
        rollback_supported=operation in MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=composed and lane.network_read,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        sandbox_profile="matrix-read-and-protected-cache-macos-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref", "request_fingerprint_ref"],
            max_context_refs=128,
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=30,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
            estimated_cost_usd=0,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=True,
            approval_required=lane.approval_required,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            deny_if_deprecated=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=(
                SideEffectLevel.destructive
                if destructive
                else SideEffectLevel.write
                if mutation
                else SideEffectLevel.read
            ),
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:msg-mx-006-matrix-sync-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "lane_ref": lane.lane_ref,
            "adapter_ref": lane.adapter_ref,
            "provider_ref": "provider-ref:communications:matrix",
            "network_read": lane.network_read,
            "implementation_status": (
                "implemented_exact_get_transport"
                if composed
                else "blocked_canonical_executor_uncomposed"
            ),
            "external_write": False,
            "message_send": False,
        },
    )


class _ImmediateMatrixSyncHandle:
    def __init__(
        self,
        *,
        command: MatrixSyncCommand,
        execution_ref: str,
        commit_validated_at: datetime,
    ) -> None:
        self._command = command
        self._execution_ref = execution_ref
        self.commit_validated_at = commit_validated_at
        self._result: MatrixSyncOperationResult | None = None
        self._collected = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    def bind_result(self, result: MatrixSyncOperationResult) -> None:
        if self._result is not None or self._settled:
            raise RuntimeError("MATRIX_SYNC_HANDLE_RESULT_ALREADY_BOUND")
        if (
            result.succeeded
            and "batch_ref" in result.safe_output
            and result.abort_callback is None
        ):
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SYNC_TRANSIENT_BATCH_ABORT_CALLBACK_REQUIRED"
            )
        self._result = result

    def abort(self) -> None:
        if self._settled:
            return
        self._collected = True
        try:
            if self._result is not None and self._result.abort_callback is not None:
                self._result.abort_callback()
        except BaseException as exc:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SYNC_CONFIRMATION_ABORT_CLEANUP_UNCERTAIN"
            ) from exc
        finally:
            self._settled = True

    def finalize(self) -> None:
        if self._settled or self._finalized or not self._collected:
            raise RuntimeError("MATRIX_SYNC_HANDLE_FINALIZATION_INVALID")
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise RuntimeError("MATRIX_SYNC_HANDLE_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise RuntimeError("MATRIX_SYNC_HANDLE_SETTLEMENT_INVALID")
        self._settled = True

    def collect(self) -> AuthorityDispatchAdapterResult:
        if self._collected:
            raise RuntimeError("MATRIX_SYNC_HANDLE_ALREADY_COLLECTED")
        self._collected = True
        if self._result is None:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SYNC_HANDLE_RESULT_REQUIRED"
            )
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
            actual_cost_ref=stable_matrix_sync_ref(
                "actual-cost-ref:matrix-sync",
                {"execution_ref": self._execution_ref, "cost_microusd": 0},
            ),
            evidence_refs=list(self._result.evidence_refs),
            safe_output=self._result.safe_output,
            safe_summary=self._result.safe_summary,
        )


class MatrixSyncAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        operation: MatrixSyncOperation,
        executor: Callable[[MatrixSyncCommand], MatrixSyncOperationResult],
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
        readiness_provider: (
            Callable[[MatrixSyncCommand], MatrixSyncReadinessObservation] | None
        ) = None,
    ) -> None:
        self.operation = MatrixSyncOperation(operation)
        self.lane: MatrixSyncLane = matrix_sync_lane(operation)
        self._executor = executor
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._manifest = build_matrix_sync_capability_manifest(operation)
        self._policy = PolicyEngine(default_max_risk=RiskLevel.high)
        self.descriptor = AuthorityDispatchAdapterDescriptor(
            adapter_ref=self.lane.adapter_ref,
            domain=self.lane.authority_domain,
            capability=self.lane.authority_capability,
            capability_ref=self.lane.capability_ref,
            tool_ref=self.lane.tool_ref,
            approval_required=self.lane.approval_required,
            atomic_start_required=True,
            operation_count=1,
            estimated_cost_microusd=0,
            failure_cost_microusd=0,
            idempotent_replay_supported=True,
            rollback_ref=f"rollback-ref:matrix-sync:{operation.value}",
            safe_disable_ref="safe-disable-ref:communications:matrix-sync",
            safe_summary=(
                f"Execute one exact Matrix {operation.value} GET operation."
                if self.operation in MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS
                else f"Keep Matrix {operation.value} blocked until its canonical executor is composed."
            ),
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:matrix-sync",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "manifest": self._manifest.model_dump(mode="json"),
            },
        )

    def _metadata(
        self, request: AuthorityDispatchRequest
    ) -> MatrixSyncDispatchMetadata:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        return MatrixSyncDispatchMetadata.model_validate(tool_request.metadata)

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
            command = MatrixSyncDispatchMetadata.model_validate(
                tool_request.metadata
            ).command
        except ValueError:
            return ["reason-ref:matrix-sync:dispatch-metadata-invalid"]
        if command.operation != self.operation:
            reasons.append("reason-ref:matrix-sync:operation-mismatch")
        if tool_request.tool_ref != self.lane.tool_ref:
            reasons.append("reason-ref:matrix-sync:tool-ref-mismatch")
        if tool_request.tool_name != self.lane.tool_name:
            reasons.append("reason-ref:matrix-sync:tool-name-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.matrix_sync:
            reasons.append("reason-ref:matrix-sync:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:matrix-sync:embedded-authority-forbidden")
        expected_resources = set(matrix_sync_exact_resource_refs(command))
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append("reason-ref:matrix-sync:resource-binding-mismatch")
        if not self._has_exact_session_lease(request, expected_resources):
            reasons.append("reason-ref:matrix-sync:exact-session-lease-required")
        try:
            policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:matrix-sync:policy-denied")
        else:
            if (
                request.action_request.constraints.get("policy_decision_ref")
                != policy_ref
            ):
                reasons.append("reason-ref:matrix-sync:policy-binding-mismatch")
        return list(dict.fromkeys(reasons))

    def runtime_prestart_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons = self.validate_request(request)
        command = self._metadata(request).command
        if self.operation not in MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS:
            reasons.append("reason-ref:matrix-sync:canonical-executor-uncomposed")
        if self._readiness_provider is None:
            reasons.append("reason-ref:matrix-sync:readiness-observation-required")
            return list(dict.fromkeys(reasons))
        try:
            observation = MatrixSyncReadinessObservation.model_validate(
                self._readiness_provider(command)
            )
        except (TypeError, ValueError):
            reasons.append("reason-ref:matrix-sync:readiness-observation-invalid")
            return list(dict.fromkeys(reasons))
        if observation.request_fingerprint_ref != command.request_fingerprint_ref:
            reasons.append("reason-ref:matrix-sync:readiness-request-mismatch")
        if observation.readiness_ref != command.readiness_ref:
            reasons.append("reason-ref:matrix-sync:readiness-ref-mismatch")
        if observation.provider_ref != command.provider_ref:
            reasons.append("reason-ref:matrix-sync:readiness-provider-mismatch")
        if observation.adapter_ref != self.lane.adapter_ref:
            reasons.append("reason-ref:matrix-sync:readiness-adapter-mismatch")
        if observation.status != MatrixSyncReadinessStatus.ready:
            reasons.append("reason-ref:matrix-sync:readiness-fail-closed")
        if utc_now() >= observation.expires_at:
            reasons.append("reason-ref:matrix-sync:readiness-observation-stale")
        if observation.kill_switch_engaged:
            reasons.append("reason-ref:matrix-sync:kill-switch-engaged")
        if observation.safe_disable_active:
            reasons.append("reason-ref:matrix-sync:safe-disable-active")
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        command = self._metadata(request).command
        task = TaskEnvelope(
            task_id=command.task_ref,
            user_request="Execute one exact governed Matrix read or protected-cache operation.",
            objective="Return content-free evidence for one exact account and cache scope.",
            scope=[self.lane.capability_ref],
            out_of_scope=[
                "message sends",
                "room mutations",
                "typing writes",
                "receipt writes",
                "media transfer",
                "browser automation",
                "memory writes",
            ],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[self.lane.tool_ref],
            acceptance_criteria=[
                "Return only safe refs, counts, status, and reason codes."
            ],
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
            },
        )
        allowed = decision.status == PolicyDecisionStatus.allowed and decision.allowed
        approval = (
            self.lane.approval_required
            and decision.status == PolicyDecisionStatus.approval_required
            and decision.requires_approval
        )
        if not (allowed or approval):
            raise ValueError("MATRIX_SYNC_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:matrix-sync",
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
        claim_handle: Callable[
            [_ImmediateMatrixSyncHandle], _ImmediateMatrixSyncHandle
        ],
    ) -> _ImmediateMatrixSyncHandle:
        reasons, validated_at = validate_commit_fence()
        if reasons:
            raise RuntimeError("MATRIX_SYNC_COMMIT_FENCE_DENIED")
        command = self._metadata(request).command
        handle = _ImmediateMatrixSyncHandle(
            command=command,
            execution_ref=authority_dispatch_execution_ref(request),
            commit_validated_at=validated_at,
        )
        claimed_handle = claim_handle(handle)
        result = self._executor(command)
        claimed_handle.bind_result(result)
        return claimed_handle

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        del request
        raise RuntimeError("MATRIX_SYNC_ATOMIC_START_REQUIRED")

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
