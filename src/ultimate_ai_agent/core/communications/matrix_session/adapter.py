from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
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

from .backend import MatrixSessionBackend, MatrixSessionExecutionHandle
from .constants import MatrixSessionLane, MatrixSessionOperation, matrix_session_lane
from .contracts import (
    MatrixSessionCommand,
    MatrixSessionDispatchMetadata,
    matrix_session_exact_resource_refs,
    matrix_session_rollback_ref,
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


def build_matrix_session_capability_manifest(
    operation: MatrixSessionOperation,
) -> CapabilityManifest:
    lane = matrix_session_lane(operation)
    mutation = lane.approval_required
    implemented_read = operation in {
        MatrixSessionOperation.discovery_read,
        MatrixSessionOperation.auth_methods_read,
    }
    browser = operation == MatrixSessionOperation.sso_launch
    connector_write = operation in {
        MatrixSessionOperation.credential_auth_create,
        MatrixSessionOperation.sso_callback_consume,
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.logout,
        MatrixSessionOperation.revoke_all,
    }
    destructive = operation in {
        MatrixSessionOperation.revoke_all,
        MatrixSessionOperation.credential_delete,
    }
    return CapabilityManifest(
        id=lane.capability_ref,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=f"Governed Matrix session {operation.value}",
        description="Execute one exact bounded Matrix discovery or session operation.",
        examples=["Inspect or update one exact account session through the approved adapter."],
        anti_examples=[
            "Synchronize rooms, read messages, send messages, transfer media, or initialize crypto."
        ],
        input_schema={"type": "object", "required": ["request_fingerprint_ref"]},
        output_schema={"type": "object", "required": ["result_ref"]},
        input_modes=["safe_refs_plus_transient_native_material"],
        output_modes=["content_free_refs_and_status"],
        side_effects=(
            SideEffectLevel.destructive
            if destructive
            else SideEffectLevel.external
            if connector_write or browser
            else SideEffectLevel.write
            if mutation
            else SideEffectLevel.read
        ),
        risk_level=RiskLevel.high if mutation else RiskLevel.low,
        authority_level=(
            CapabilityAuthorityLevel.destructive
            if destructive
            else CapabilityAuthorityLevel.external
            if connector_write or browser
            else CapabilityAuthorityLevel.mutating
            if mutation
            else CapabilityAuthorityLevel.read_only
        ),
        approval_required=lane.approval_required,
        deterministic=False,
        rollback_supported=False,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=implemented_read,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        sandbox_profile="matrix-session-macos-native-boundary-v1",
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
                else SideEffectLevel.external
                if connector_write or browser
                else SideEffectLevel.write
                if mutation
                else SideEffectLevel.read
            ),
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:msg-mx-005-matrix-session-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "lane_ref": lane.lane_ref,
            "adapter_ref": lane.adapter_ref,
            "provider_ref": "provider-ref:communications:matrix",
            "sync_enabled": False,
            "message_read_enabled": False,
            "message_write_enabled": False,
            "crypto_initialized": False,
        },
    )


class _MatrixSessionDispatchHandle:
    def __init__(self, handle: MatrixSessionExecutionHandle) -> None:
        self._handle = handle
        self.commit_validated_at = handle.commit_validated_at

    def collect(self) -> AuthorityDispatchAdapterResult:
        result = self._handle.collect()
        return AuthorityDispatchAdapterResult(
            execution_ref=result.execution_ref,
            succeeded=result.succeeded,
            failure_category=(
                None
                if result.succeeded
                else AuthorityDispatchFailureCategory.permanent_adapter_error
            ),
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref=_canonical_ref(
                "actual-cost-ref:matrix-session",
                {"execution_ref": result.execution_ref, "cost_microusd": 0},
            ),
            evidence_refs=list(result.evidence_refs),
            safe_output=result.safe_output,
            safe_summary=result.safe_summary,
        )


class MatrixSessionAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        operation: MatrixSessionOperation,
        backend: MatrixSessionBackend,
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
        readiness_provider: Callable[[MatrixSessionCommand], list[str]] | None = None,
    ) -> None:
        self.operation = MatrixSessionOperation(operation)
        self.lane: MatrixSessionLane = matrix_session_lane(operation)
        self._backend = backend
        self._authority_leases_provider = authority_leases_provider
        self._readiness_provider = readiness_provider
        self._manifest = build_matrix_session_capability_manifest(operation)
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
            idempotent_replay_supported=self.operation
            in {
                MatrixSessionOperation.discovery_read,
                MatrixSessionOperation.auth_methods_read,
            },
            rollback_ref=matrix_session_rollback_ref(operation),
            safe_disable_ref="safe-disable-ref:communications:matrix-session",
            safe_summary=f"Execute one exact Matrix session {operation.value} operation.",
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:matrix-session",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "backend_binding_ref": backend.binding_ref,
                "manifest": self._manifest.model_dump(mode="json"),
            },
        )

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
            metadata = MatrixSessionDispatchMetadata.model_validate(
                tool_request.metadata
            )
            command = metadata.command
        except ValueError:
            return ["reason-ref:matrix-session:dispatch-metadata-invalid"]
        if command.operation != self.operation:
            reasons.append("reason-ref:matrix-session:operation-mismatch")
        if tool_request.tool_ref != self.lane.tool_ref:
            reasons.append("reason-ref:matrix-session:tool-ref-mismatch")
        if tool_request.tool_name != self.lane.tool_name:
            reasons.append("reason-ref:matrix-session:tool-name-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.matrix_session:
            reasons.append("reason-ref:matrix-session:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:matrix-session:embedded-authority-forbidden")
        expected_resources = set(matrix_session_exact_resource_refs(command))
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append("reason-ref:matrix-session:resource-binding-mismatch")
        if not self._has_exact_session_lease(request, expected_resources):
            reasons.append("reason-ref:matrix-session:exact-session-lease-required")
        try:
            policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:matrix-session:policy-denied")
        else:
            if request.action_request.constraints.get("policy_decision_ref") != policy_ref:
                reasons.append("reason-ref:matrix-session:policy-binding-mismatch")
        return list(dict.fromkeys(reasons))

    def runtime_prestart_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons = self.validate_request(request)
        metadata = MatrixSessionDispatchMetadata.model_validate(
            ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            ).metadata
        )
        reasons.extend(self._backend.readiness_reason_refs(self.operation))
        try:
            self._backend.validate_transient_target(metadata.command)
        except (ValueError, RuntimeError):
            reasons.append("reason-ref:matrix-session:transient-target-invalid")
        if self._readiness_provider is not None:
            reasons.extend(self._readiness_provider(metadata.command))
        if metadata.command.discovery_freshness_ref.endswith(":stale"):
            reasons.append("reason-ref:matrix-session:discovery-stale")
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        metadata = MatrixSessionDispatchMetadata.model_validate(
            ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            ).metadata
        )
        command = metadata.command
        task = TaskEnvelope(
            task_id=command.task_ref,
            user_request="Execute one exact governed Matrix session operation.",
            objective="Return content-free session evidence for one exact target.",
            scope=[self.lane.capability_ref],
            out_of_scope=[
                "message synchronization",
                "room reads",
                "message sends",
                "media transfer",
                "crypto initialization",
            ],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[self.lane.tool_ref],
            acceptance_criteria=["Return only safe refs, status, and reason codes."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={
                "target_ref": metadata.target_ref,
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
            raise ValueError("MATRIX_SESSION_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:matrix-session",
            {
                "decision": decision.model_dump(mode="json"),
                "operation": self.operation.value,
                "dispatch_ref": request.dispatch_ref,
                "lease_ref": request.lease_ref,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        )

    def claim_request_state(self, dispatch_ref: str) -> None:
        self._backend.claim_request_state(dispatch_ref)

    def release_request_state(self, dispatch_ref: str) -> None:
        self._backend.release_request_state(dispatch_ref)

    def request_state_active(self, dispatch_ref: str) -> bool:
        return self._backend.request_state_active(dispatch_ref)

    def start(
        self,
        request: AuthorityDispatchRequest,
        *,
        validate_commit_fence: Callable[[], tuple[list[str], datetime]],
    ) -> _MatrixSessionDispatchHandle:
        metadata = MatrixSessionDispatchMetadata.model_validate(
            ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            ).metadata
        )
        command = metadata.command
        safe_request = command.model_dump(mode="json")
        handle = self._backend.start_operation(
            operation=self.operation,
            dispatch_ref=request.dispatch_ref,
            execution_ref=authority_dispatch_execution_ref(request),
            safe_request=safe_request,
            validate_commit_fence=validate_commit_fence,
        )
        return _MatrixSessionDispatchHandle(handle)

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        raise RuntimeError("MATRIX_SESSION_ATOMIC_START_REQUIRED")

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
