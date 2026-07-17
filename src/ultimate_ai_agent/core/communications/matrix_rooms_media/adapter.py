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
from ultimate_ai_agent.core.authority.dispatcher import authority_dispatch_execution_ref
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
    DESTRUCTIVE_OPERATIONS,
    EXTERNAL_MUTATION_OPERATIONS,
    NETWORK_OPERATIONS,
    MatrixRoomsMediaOperation,
    matrix_rooms_media_lane,
    matrix_rooms_media_rollback_ref,
)
from .contracts import (
    MatrixRoomsMediaCommand,
    MatrixRoomsMediaDispatchMetadata,
    MatrixRoomsMediaReadiness,
    matrix_rooms_media_exact_resource_refs,
    stable_matrix_rooms_media_ref,
)


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_matrix_rooms_media_capability_manifest(
    operation: MatrixRoomsMediaOperation,
) -> CapabilityManifest:
    lane = matrix_rooms_media_lane(operation)
    destructive = operation in DESTRUCTIVE_OPERATIONS
    network = operation in NETWORK_OPERATIONS
    return CapabilityManifest(
        id=lane.capability_ref,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=f"Exact Matrix room/search/media {operation.value}",
        description="Execute one exact approved Matrix room, encrypted local-search, or bounded media operation.",
        examples=["Execute one exact operator-reviewed room, search, or media scope."],
        anti_examples=[
            "Standing room authority.",
            "Unbounded transfer or cross-room search.",
        ],
        input_schema={"type": "object", "required": ["request_fingerprint_ref"]},
        output_schema={"type": "object", "required": ["receipt_ref"]},
        input_modes=["safe_refs_plus_transient_private_material"],
        output_modes=["content_free_refs_and_status"],
        side_effects=(
            SideEffectLevel.destructive
            if destructive
            else SideEffectLevel.external
            if network
            else SideEffectLevel.write
        ),
        risk_level=RiskLevel.high,
        authority_level=(
            CapabilityAuthorityLevel.destructive
            if destructive
            else CapabilityAuthorityLevel.external
            if network
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
        provider_runtime_allowed=network,
        browser_runtime_allowed=False,
        connector_write_allowed=operation in EXTERNAL_MUTATION_OPERATIONS,
        sandbox_profile="matrix-exact-rooms-media-local-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref", "request_fingerprint_ref"],
            max_context_refs=96,
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
                if network
                else SideEffectLevel.write
            ),
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:msg-mx-009-rooms-search-media-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "lane_ref": lane.lane_ref,
            "adapter_ref": lane.adapter_ref,
            "provider_ref": "provider-ref:communications:matrix",
            "human_commanded": True,
            "request_scoped": True,
        },
    )


class MatrixRoomsMediaOperationResult:
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


class _ImmediateHandle:
    def __init__(self, *, execution_ref: str, commit_validated_at: datetime) -> None:
        self._execution_ref = execution_ref
        self.commit_validated_at = commit_validated_at
        self._result: MatrixRoomsMediaOperationResult | None = None
        self._collected = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    def bind_result(self, result: MatrixRoomsMediaOperationResult) -> None:
        if self._result is not None or self._settled:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_HANDLE_RESULT_ALREADY_BOUND")
        self._result = result

    def abort(self) -> None:
        self._settled = True

    def finalize(self) -> None:
        if self._settled or self._finalized or not self._collected:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_HANDLE_FINALIZATION_INVALID")
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_HANDLE_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_HANDLE_SETTLEMENT_INVALID")
        self._settled = True

    def collect(self) -> AuthorityDispatchAdapterResult:
        if self._collected or self._result is None:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_HANDLE_COLLECT_INVALID")
        self._collected = True
        return AuthorityDispatchAdapterResult(
            execution_ref=self._execution_ref,
            succeeded=self._result.succeeded,
            failure_category=None
            if self._result.succeeded
            else AuthorityDispatchFailureCategory.permanent_adapter_error,
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref=stable_matrix_rooms_media_ref(
                "actual-cost-ref:matrix-rooms-media",
                {"execution_ref": self._execution_ref},
            ),
            evidence_refs=list(self._result.evidence_refs),
            safe_output=self._result.safe_output,
            safe_summary=self._result.safe_summary,
        )


class MatrixRoomsMediaAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        operation: MatrixRoomsMediaOperation,
        executor: Callable[
            [MatrixRoomsMediaCommand, str], MatrixRoomsMediaOperationResult
        ],
        executor_binding_ref: str,
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
        readiness_provider: Callable[
            [MatrixRoomsMediaCommand], MatrixRoomsMediaReadiness
        ],
    ) -> None:
        self.operation = MatrixRoomsMediaOperation(operation)
        self.lane = matrix_rooms_media_lane(operation)
        self._executor = executor
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._manifest = build_matrix_rooms_media_capability_manifest(operation)
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
            rollback_ref=matrix_rooms_media_rollback_ref(operation),
            safe_disable_ref="safe-disable-ref:matrix-messenger:enabled",
            safe_summary=f"Execute one exact Matrix {operation.value} operation.",
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:matrix-rooms-media",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "executor_binding_ref": executor_binding_ref,
            },
        )

    def _metadata(
        self, request: AuthorityDispatchRequest
    ) -> MatrixRoomsMediaDispatchMetadata:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        return MatrixRoomsMediaDispatchMetadata.model_validate(tool_request.metadata)

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
            command = MatrixRoomsMediaDispatchMetadata.model_validate(
                tool_request.metadata
            ).command
        except ValueError:
            return ["reason-ref:matrix-rooms-media:dispatch-metadata-invalid"]
        if command.operation != self.operation:
            reasons.append("reason-ref:matrix-rooms-media:operation-mismatch")
        if (
            tool_request.tool_ref != self.lane.tool_ref
            or tool_request.tool_name != self.lane.tool_name
        ):
            reasons.append("reason-ref:matrix-rooms-media:tool-binding-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.matrix_rooms_media:
            reasons.append("reason-ref:matrix-rooms-media:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:matrix-rooms-media:embedded-authority-forbidden")
        expected_resources = set(matrix_rooms_media_exact_resource_refs(command))
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append("reason-ref:matrix-rooms-media:resource-binding-mismatch")
        if not self._has_exact_session_lease(request, expected_resources):
            reasons.append("reason-ref:matrix-rooms-media:exact-session-lease-required")
        try:
            policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:matrix-rooms-media:policy-denied")
        else:
            if (
                request.action_request.constraints.get("policy_decision_ref")
                != policy_ref
            ):
                reasons.append("reason-ref:matrix-rooms-media:policy-binding-mismatch")
        return list(dict.fromkeys(reasons))

    def runtime_prestart_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons = self.validate_request(request)
        command = self._metadata(request).command
        try:
            observation = MatrixRoomsMediaReadiness.model_validate(
                self._readiness_provider(command)
            )
        except (TypeError, ValueError):
            return [*reasons, "reason-ref:matrix-rooms-media:readiness-invalid"]
        if (
            observation.request_fingerprint_ref != command.request_fingerprint_ref
            or observation.readiness_ref != command.readiness_ref
        ):
            reasons.append("reason-ref:matrix-rooms-media:readiness-binding-mismatch")
        if observation.adapter_ref != self.lane.adapter_ref:
            reasons.append("reason-ref:matrix-rooms-media:readiness-adapter-mismatch")
        now = utc_now()
        if (
            observation.observed_at < command.request_created_at
            or observation.observed_at > now + timedelta(seconds=5)
            or observation.expires_at > command.start_deadline
        ):
            reasons.append("reason-ref:matrix-rooms-media:readiness-window-mismatch")
        if observation.status != "ready" or now >= observation.expires_at:
            reasons.append("reason-ref:matrix-rooms-media:readiness-fail-closed")
        if observation.kill_switch_engaged or observation.safe_disable_active:
            reasons.append("reason-ref:matrix-rooms-media:runtime-disabled")
        if (
            not observation.broker_integrity_verified
            or not observation.filesystem_root_verified
            or not observation.encrypted_index_available
        ):
            reasons.append("reason-ref:matrix-rooms-media:runtime-posture-incomplete")
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        command = self._metadata(request).command
        task = TaskEnvelope(
            task_id=command.task_ref,
            user_request="Execute one exact human-commanded Matrix room, search, or media operation.",
            objective="Produce content-free evidence for one exact bounded scope.",
            scope=[self.lane.capability_ref],
            out_of_scope=[
                "standing authority",
                "cross-room leakage",
                "unbounded transfer",
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
                "connector_write_allowed": (
                    self.operation in EXTERNAL_MUTATION_OPERATIONS
                ),
            },
        )
        if (
            decision.status != PolicyDecisionStatus.approval_required
            or not decision.requires_approval
        ):
            raise ValueError("MATRIX_ROOMS_MEDIA_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:matrix-rooms-media",
            {
                "decision": decision.model_dump(mode="json"),
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
        claim_handle: Callable[[_ImmediateHandle], _ImmediateHandle],
    ) -> _ImmediateHandle:
        reasons, validated_at = validate_commit_fence()
        if reasons:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_COMMIT_FENCE_DENIED")
        if request.approval_validation_request is None:
            raise RuntimeError("MATRIX_ROOMS_MEDIA_APPROVAL_REQUIRED")
        command = self._metadata(request).command
        handle = claim_handle(
            _ImmediateHandle(
                execution_ref=authority_dispatch_execution_ref(request),
                commit_validated_at=validated_at,
            )
        )
        try:
            result = self._executor(
                command, request.approval_validation_request.approval_ref
            )
        except Exception as exc:
            outcome_uncertain = (
                self.operation in NETWORK_OPERATIONS and not isinstance(exc, ValueError)
            )
            result = MatrixRoomsMediaOperationResult(
                succeeded=False,
                safe_output={
                    "runtime_status": (
                        "outcome_uncertain" if outcome_uncertain else "blocked"
                    ),
                    "operation": command.operation.value,
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "external_write_performed": False,
                    "raw_content_included": False,
                    "raw_identifiers_included": False,
                    "automatic_retry_permitted": False,
                    "manual_retry_requires_same_idempotency_ref": True,
                    "outcome_uncertain": outcome_uncertain,
                },
                evidence_refs=(
                    "evidence-ref:matrix-rooms-media:executor-outcome-uncertain"
                    if outcome_uncertain
                    else "evidence-ref:matrix-rooms-media:executor-failed-safely",
                ),
                safe_summary=(
                    "The exact Matrix room, local-search, or media executor "
                    "failed without exposing exception data."
                ),
            )
        handle.bind_result(result)
        return handle

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        del request
        raise RuntimeError("MATRIX_ROOMS_MEDIA_ATOMIC_START_REQUIRED")

    def _has_exact_session_lease(
        self, request: AuthorityDispatchRequest, expected_resources: set[str]
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
        expected_domains = {
            domain.value: [capability.value for capability in capabilities]
            for domain, capabilities in self.lane.requested_domains.items()
        }
        return lease.domains == expected_domains and any(
            AuthorityConstraintKind(constraint.kind)
            == AuthorityConstraintKind.resource_refs
            and set(constraint.allowed_refs) == expected_resources
            for constraint in lease.authority_constraints
        )


__all__ = [
    "MatrixRoomsMediaAuthorityDispatchAdapter",
    "MatrixRoomsMediaOperationResult",
    "build_matrix_rooms_media_capability_manifest",
]
