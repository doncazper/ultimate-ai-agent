from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any

from ultimate_ai_agent.core.authority import (
    AuthorityConstraintKind,
    AuthorityDomain,
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

from .backend import DockerMatrixHarnessBackend, MatrixHarnessExecutionHandle
from .constants import (
    MATRIX_HARNESS_IMAGE_REF,
    MatrixHarnessLane,
    MatrixHarnessOperation,
    matrix_harness_lane,
)
from .contracts import (
    MatrixHarnessBackendResult,
    MatrixHarnessCommand,
    MatrixHarnessDispatchMetadata,
    MatrixHarnessOperationOutcome,
    matrix_harness_exact_resource_refs,
)


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_matrix_harness_capability_manifest(
    operation: MatrixHarnessOperation,
) -> CapabilityManifest:
    lane = matrix_harness_lane(operation)
    mutation = operation in {
        MatrixHarnessOperation.start,
        MatrixHarnessOperation.fixture_seed,
        MatrixHarnessOperation.stop,
        MatrixHarnessOperation.reset,
    }
    return CapabilityManifest(
        id=lane.capability_ref,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=f"Disposable Matrix harness {operation.value}",
        description=(
            "Execute one exact bounded local-only Synapse harness operation."
        ),
        examples=["Operate the digest-pinned disposable loopback test harness."],
        anti_examples=[
            "Operate a public, federated, hosted, production, or account Matrix service."
        ],
        input_schema={"type": "object", "required": ["request_fingerprint_ref"]},
        output_schema={"type": "object", "required": ["evidence_refs"]},
        input_modes=["safe_refs_only"],
        output_modes=["content_free_counts_and_refs"],
        side_effects=(SideEffectLevel.write if mutation else SideEffectLevel.read),
        risk_level=(RiskLevel.high if mutation else RiskLevel.low),
        authority_level=(
            CapabilityAuthorityLevel.mutating
            if mutation
            else CapabilityAuthorityLevel.read_only
        ),
        approval_required=lane.approval_required,
        deterministic=False,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        sandbox_profile="docker-desktop-loopback-synapse-test-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        single_writer_required=mutation,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref", "request_fingerprint_ref"],
            max_context_refs=32,
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=120,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
            estimated_cost_usd=0,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=mutation,
            approval_required=lane.approval_required,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            deny_if_deprecated=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=(
                SideEffectLevel.write if mutation else SideEffectLevel.read
            ),
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:msg-mx-004-matrix-harness-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "lane_ref": lane.lane_ref,
            "adapter_ref": lane.adapter_ref,
            "image_ref": MATRIX_HARNESS_IMAGE_REF,
            "public_binding": False,
            "federation": False,
            "production": False,
        },
    )


class _MatrixHarnessDispatchHandle:
    def __init__(
        self,
        handle: MatrixHarnessExecutionHandle,
        *,
        operation_count: int,
    ) -> None:
        self._handle = handle
        self._operation_count = operation_count
        self.commit_validated_at = handle.commit_validated_at

    def collect(self) -> AuthorityDispatchAdapterResult:
        result = self._handle.collect()
        if result.outcome == MatrixHarnessOperationOutcome.recovery_required:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_HARNESS_COLLECTION_RECOVERY_REQUIRED"
            )
        succeeded = result.outcome == MatrixHarnessOperationOutcome.succeeded
        return AuthorityDispatchAdapterResult(
            execution_ref=result.execution_ref,
            succeeded=succeeded,
            failure_category=(
                None
                if succeeded
                else AuthorityDispatchFailureCategory.permanent_adapter_error
            ),
            actual_operation_count=self._operation_count,
            actual_cost_microusd=0,
            actual_cost_ref=_canonical_ref(
                "actual-cost-ref:matrix-harness",
                {"execution_ref": result.execution_ref, "cost_microusd": 0},
            ),
            evidence_refs=result.evidence_refs,
            safe_output=_safe_backend_output(result),
            safe_summary=result.safe_summary,
        )


class MatrixHarnessAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        operation: MatrixHarnessOperation,
        backend: DockerMatrixHarnessBackend,
        authority_leases_provider: Callable[[], Sequence[AuthorityLease]],
    ) -> None:
        self.operation = MatrixHarnessOperation(operation)
        self.lane: MatrixHarnessLane = matrix_harness_lane(self.operation)
        self._backend = backend
        self._authority_leases_provider = authority_leases_provider
        self._manifest = build_matrix_harness_capability_manifest(self.operation)
        self._policy = PolicyEngine(default_max_risk=RiskLevel.high)
        self.descriptor = AuthorityDispatchAdapterDescriptor(
            adapter_ref=self.lane.adapter_ref,
            domain=AuthorityDomain.messages,
            capability=self.lane.authority_capability,
            capability_ref=self.lane.capability_ref,
            tool_ref=self.lane.tool_ref,
            approval_required=self.lane.approval_required,
            atomic_start_required=True,
            operation_count=1,
            estimated_cost_microusd=0,
            failure_cost_microusd=0,
            idempotent_replay_supported=True,
            rollback_ref=f"rollback-ref:matrix-harness:{self.operation.value}",
            safe_disable_ref="safe-disable-ref:communications:matrix-harness-local",
            safe_summary=(
                f"Execute the exact disposable Matrix harness {self.operation.value} lane."
            ),
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:matrix-harness",
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
            metadata = MatrixHarnessDispatchMetadata.model_validate(
                tool_request.metadata
            )
            command = _command_from_dispatch(request, metadata)
        except ValueError:
            return ["reason-ref:matrix-harness:dispatch-metadata-invalid"]
        if metadata.operation != self.operation:
            reasons.append("reason-ref:matrix-harness:operation-mismatch")
        if tool_request.tool_ref != self.lane.tool_ref:
            reasons.append("reason-ref:matrix-harness:tool-ref-mismatch")
        if tool_request.tool_name != self.lane.tool_name:
            reasons.append("reason-ref:matrix-harness:tool-name-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.matrix_harness:
            reasons.append("reason-ref:matrix-harness:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:matrix-harness:embedded-authority-forbidden")
        expected_resources = set(matrix_harness_exact_resource_refs(command))
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append("reason-ref:matrix-harness:resource-binding-mismatch")
        if not self._has_exact_mission_lease(
            request,
            expected_resources=expected_resources,
            mission_ref=metadata.mission_ref,
        ):
            reasons.append("reason-ref:matrix-harness:exact-mission-lease-required")
        try:
            policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:matrix-harness:policy-denied")
        else:
            if request.action_request.constraints.get("policy_decision_ref") != policy_ref:
                reasons.append("reason-ref:matrix-harness:policy-binding-mismatch")
        return list(dict.fromkeys(reasons))

    def runtime_prestart_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons = self.validate_request(request)
        reasons.extend(self._backend.readiness_reason_refs(self.operation))
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        metadata = MatrixHarnessDispatchMetadata.model_validate(tool_request.metadata)
        task = TaskEnvelope(
            task_id=metadata.task_ref,
            user_request="Execute one exact disposable local Matrix harness operation.",
            objective="Return content-free lifecycle evidence for the loopback harness.",
            scope=[self.lane.capability_ref],
            out_of_scope=[
                "public hosting",
                "federation",
                "production",
                "account authentication",
                "message connector authority",
            ],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[self.lane.tool_ref],
            acceptance_criteria=["Return only safe lifecycle refs and bounded counts."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={
                "target_ref": metadata.target_ref,
                "request_fingerprint_ref": metadata.request_fingerprint_ref,
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
        policy_allows_lane = (
            decision.status == PolicyDecisionStatus.allowed and decision.allowed
        )
        policy_requires_exact_approval = (
            self.lane.approval_required
            and decision.status == PolicyDecisionStatus.approval_required
            and decision.requires_approval
        )
        if not (policy_allows_lane or policy_requires_exact_approval):
            raise ValueError("MATRIX_HARNESS_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:matrix-harness",
            {
                "decision": decision.model_dump(mode="json"),
                "operation": self.operation.value,
                "dispatch_ref": request.dispatch_ref,
                "lease_ref": request.lease_ref,
                "request_fingerprint_ref": metadata.request_fingerprint_ref,
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
    ) -> _MatrixHarnessDispatchHandle:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        metadata = MatrixHarnessDispatchMetadata.model_validate(
            tool_request.metadata
        )
        handle = self._backend.start_operation(
            operation=self.operation,
            execution_ref=authority_dispatch_execution_ref(request),
            lifecycle_generation_ref=metadata.lifecycle_generation_ref,
            expected_state_ref=metadata.expected_state_ref,
            validate_commit_fence=validate_commit_fence,
        )
        return _MatrixHarnessDispatchHandle(
            handle,
            operation_count=self.descriptor.operation_count,
        )

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        raise RuntimeError("MATRIX_HARNESS_ATOMIC_START_REQUIRED")

    def _has_exact_mission_lease(
        self,
        request: AuthorityDispatchRequest,
        *,
        expected_resources: set[str],
        mission_ref: str,
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
            or lease.scope != AuthorityLeaseScope.mission.value
            or lease.mission_ref != mission_ref
        ):
            return False
        for constraint in lease.authority_constraints:
            if (
                AuthorityConstraintKind(constraint.kind)
                == AuthorityConstraintKind.resource_refs
                and set(constraint.allowed_refs) == expected_resources
            ):
                return True
        return False


def _command_from_dispatch(
    request: AuthorityDispatchRequest,
    metadata: MatrixHarnessDispatchMetadata,
) -> MatrixHarnessCommand:
    if request.start_deadline is None:
        raise ValueError("MATRIX_HARNESS_START_DEADLINE_REQUIRED")
    return MatrixHarnessCommand(
        operation=metadata.operation,
        request_ref=metadata.request_ref,
        task_ref=metadata.task_ref,
        mission_ref=metadata.mission_ref,
        run_ref=metadata.run_ref,
        dispatch_ref=request.dispatch_ref,
        idempotency_ref=request.idempotency_ref,
        lease_ref=request.lease_ref,
        lifecycle_generation_ref=metadata.lifecycle_generation_ref,
        expected_state_ref=metadata.expected_state_ref,
        start_deadline=request.start_deadline,
        request_fingerprint_ref=metadata.request_fingerprint_ref,
    )


def _safe_backend_output(result: MatrixHarnessBackendResult) -> dict[str, Any]:
    return {
        "operation": result.operation.value,
        "outcome": result.outcome.value,
        "runtime_status": result.runtime_status.value,
        "reason_codes": list(result.reason_codes),
        "warning_reason_refs": list(result.warning_reason_refs),
        "lifecycle_generation_ref": result.lifecycle_generation_ref,
        "lifecycle_state_ref": result.lifecycle_state_ref,
        "container_count": result.container_count,
        "network_count": result.network_count,
        "volume_count": result.volume_count,
        "fixture_account_count": result.fixture_account_count,
        "fixture_room_count": result.fixture_room_count,
        "fixture_event_count": result.fixture_event_count,
        "residual_resource_count": result.residual_resource_count,
        "encryption_fixture_posture": result.encryption_fixture_posture,
        "raw_output_persisted": False,
        "raw_paths_persisted": False,
        "credentials_persisted_in_receipt": False,
        "fixture_content_persisted_in_receipt": False,
    }
