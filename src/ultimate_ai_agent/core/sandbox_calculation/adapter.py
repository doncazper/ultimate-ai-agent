from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
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
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .backend import (
    DockerSealedCalculationBackend,
    SealedCalculationCleanupUnconfirmedError,
    SealedCalculationExecutionTruthUnknownError,
    SealedCalculationExecutionHandle,
    TransientCalculationInputStore,
)
from .contracts import (
    SEALED_CALCULATION_ADAPTER_REF,
    SEALED_CALCULATION_CAPABILITY_REF,
    SEALED_CALCULATION_LANE_REF,
    SEALED_CALCULATION_ROLLBACK_REF,
    SEALED_CALCULATION_SAFE_DISABLE_REF,
    SEALED_CALCULATION_TARGET_REF,
    SEALED_CALCULATION_TOOL_NAME,
    SEALED_CALCULATION_TOOL_REF,
    SealedCalculationStatus,
    SealedCalculationResult,
)


SEALED_CALCULATION_POLICY_REF = "policy-ref:sealed-calculation-no-approval-v1"
SEALED_CALCULATION_GRAMMAR_POLICY_REF = "grammar-policy-ref:sealed-arithmetic-v1"


class SealedCalculationDispatchMetadata(BaseModel):
    input_ref: str
    expression_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    expression_bytes: int = Field(..., ge=1, le=512)
    target_ref: str
    grammar_policy_ref: str
    limits_ref: str
    attestation_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_metadata(self) -> "SealedCalculationDispatchMetadata":
        for ref in (
            self.input_ref,
            self.target_ref,
            self.grammar_policy_ref,
            self.limits_ref,
            self.attestation_ref,
        ):
            validate_execution_ref(ref, "sealed_calculation_dispatch_ref")
        return self


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_sealed_calculation_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=SEALED_CALCULATION_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="Sealed deterministic calculation",
        description=(
            "Evaluate one bounded arithmetic expression inside an attested local container."
        ),
        examples=[
            "Calculate one bounded numeric expression under an exact mission lease."
        ],
        anti_examples=[
            "Run Python, shell commands, imports, files, network, or packages."
        ],
        input_schema={
            "type": "object",
            "required": ["input_ref", "expression_sha256", "target_ref"],
        },
        output_schema={
            "type": "object",
            "required": ["output_sha256", "result_preview", "evidence_refs"],
        },
        input_modes=["transient_bounded_arithmetic"],
        output_modes=["safe_numeric_preview_and_refs"],
        side_effects=SideEffectLevel.none,
        risk_level=RiskLevel.low,
        authority_level=CapabilityAuthorityLevel.read_only,
        approval_required=False,
        deterministic=True,
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
        sandbox_profile="docker-desktop-sealed-arithmetic-v1",
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref", "expression_sha256"],
            max_context_refs=4,
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=5,
            max_retries=0,
            max_concurrency=1,
            deterministic=True,
            estimated_cost_usd=0,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=False,
            approval_required=False,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            deny_if_deprecated=True,
            max_risk_level=RiskLevel.low,
            max_side_effect_level=SideEffectLevel.none,
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:sealed-calculation-adversarial"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "adapter_ref": SEALED_CALCULATION_ADAPTER_REF,
            "lane_ref": SEALED_CALCULATION_LANE_REF,
            "policy_ref": SEALED_CALCULATION_POLICY_REF,
            "safe_disable_ref": SEALED_CALCULATION_SAFE_DISABLE_REF,
            "broad_code_execution": False,
            "broad_shell_execution": False,
        },
    )


class _SealedCalculationDispatchHandle:
    def __init__(
        self,
        handle: SealedCalculationExecutionHandle,
        *,
        operation_count: int,
        result_sink: Callable[[SealedCalculationResult], None],
        result_discard: Callable[[str], None],
    ) -> None:
        self._handle = handle
        self._operation_count = operation_count
        self._result_sink = result_sink
        self._result_discard = result_discard
        self._pending_result: SealedCalculationResult | None = None

    @property
    def commit_validated_at(self) -> datetime:
        return self._handle.commit_validated_at

    @property
    def settled(self) -> bool:
        return self._handle.settled

    def abort(self) -> None:
        try:
            self._handle.abort()
        except BaseException as exc:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "AUTHORITY_DISPATCH_ATOMIC_CONFIRMATION_ABORT_RECOVERY_REQUIRED"
            ) from exc
        finally:
            self._result_discard(self._handle.execution_ref)

    def finalize(self) -> None:
        if self._pending_result is None:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "AUTHORITY_DISPATCH_ATOMIC_RESULT_FINALIZATION_REQUIRED"
            )
        self._result_sink(self._pending_result)
        try:
            self._handle.finalize()
        except BaseException:
            self._result_discard(self._pending_result.execution_ref)
            raise

    def commit(self) -> None:
        self._handle.commit()

    def settle(self) -> None:
        self._handle.settle()

    def collect(self) -> AuthorityDispatchAdapterResult:
        result = self._handle.collect()
        self._pending_result = result
        if result.status == SealedCalculationStatus.recovery_required:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "AUTHORITY_DISPATCH_ATOMIC_COLLECTION_RECOVERY_REQUIRED"
            )
        succeeded = result.status == SealedCalculationStatus.succeeded
        output_refs = (
            [f"output-hash-ref:sha256:{result.output_sha256}"]
            if result.output_sha256 is not None
            else []
        )
        safe_output: dict[str, Any] = {
            "status": str(result.status),
            "expression_sha256": result.expression_sha256,
            "output_sha256": result.output_sha256,
            "result_preview": result.result_preview,
            "reason_codes": result.reason_codes,
            "redaction_status": result.redaction_status,
            "code_output_is_evidence_not_authority": True,
        }
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
                "actual-cost-ref:sealed-calculation",
                {"execution_ref": result.execution_ref, "cost_microusd": 0},
            ),
            evidence_refs=result.evidence_refs,
            output_refs=output_refs,
            safe_output=safe_output,
            safe_summary=result.safe_summary,
        )


class SealedCalculationAuthorityDispatchAdapter:
    def __init__(
        self,
        *,
        backend: DockerSealedCalculationBackend,
        input_store: TransientCalculationInputStore,
    ) -> None:
        self._backend = backend
        self._input_store = input_store
        self._manifest = build_sealed_calculation_capability_manifest()
        self._policy = PolicyEngine(default_max_risk=RiskLevel.low)
        self._results: dict[str, SealedCalculationResult] = {}
        self._results_lock = threading.RLock()
        self.descriptor = AuthorityDispatchAdapterDescriptor(
            adapter_ref=SEALED_CALCULATION_ADAPTER_REF,
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            capability_ref=SEALED_CALCULATION_CAPABILITY_REF,
            tool_ref=SEALED_CALCULATION_TOOL_REF,
            approval_required=False,
            atomic_start_required=True,
            operation_count=1,
            estimated_cost_microusd=0,
            failure_cost_microusd=0,
            idempotent_replay_supported=True,
            rollback_ref=SEALED_CALCULATION_ROLLBACK_REF,
            safe_disable_ref=SEALED_CALCULATION_SAFE_DISABLE_REF,
            safe_summary=(
                "Run one bounded arithmetic expression in the attested sealed backend."
            ),
        )
        self.binding_ref = _canonical_ref(
            "adapter-binding-ref:sealed-calculation",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "attestation": backend.attestation.model_dump(mode="json"),
                "policy_ref": SEALED_CALCULATION_POLICY_REF,
                "grammar_policy_ref": SEALED_CALCULATION_GRAMMAR_POLICY_REF,
            },
        )

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
            metadata = SealedCalculationDispatchMetadata.model_validate(
                tool_request.metadata
            )
        except ValueError:
            return ["reason-ref:sealed-calculation:dispatch-metadata-invalid"]
        if tool_request.tool_ref != SEALED_CALCULATION_TOOL_REF:
            reasons.append("reason-ref:sealed-calculation:tool-ref-mismatch")
        if tool_request.tool_name != SEALED_CALCULATION_TOOL_NAME:
            reasons.append("reason-ref:sealed-calculation:tool-name-mismatch")
        if tool_request.invocation_kind != ToolInvocationKind.sealed_arithmetic:
            reasons.append("reason-ref:sealed-calculation:invocation-kind-mismatch")
        if tool_request.approval_ref is not None or tool_request.authority_refs:
            reasons.append("reason-ref:sealed-calculation:embedded-authority-forbidden")
        transient = self._input_store.get(metadata.input_ref)
        if transient is None:
            reasons.append("reason-ref:sealed-calculation:transient-input-required")
        else:
            if (
                transient.expression_sha256 != metadata.expression_sha256
                or len(transient.expression.encode("utf-8"))
                != metadata.expression_bytes
                or transient.target_ref != metadata.target_ref
                or transient.limits != self._backend.config.limits
            ):
                reasons.append(
                    "reason-ref:sealed-calculation:transient-input-binding-mismatch"
                )
        if metadata.target_ref != SEALED_CALCULATION_TARGET_REF:
            reasons.append("reason-ref:sealed-calculation:target-mismatch")
        if metadata.grammar_policy_ref != SEALED_CALCULATION_GRAMMAR_POLICY_REF:
            reasons.append("reason-ref:sealed-calculation:grammar-policy-mismatch")
        if metadata.limits_ref != self._backend.attestation.limits_ref:
            reasons.append("reason-ref:sealed-calculation:limits-mismatch")
        if metadata.attestation_ref != self._backend.attestation.attestation_ref:
            reasons.append("reason-ref:sealed-calculation:attestation-mismatch")
        expected_resources = {
            SEALED_CALCULATION_CAPABILITY_REF,
            SEALED_CALCULATION_ADAPTER_REF,
            SEALED_CALCULATION_TARGET_REF,
            metadata.input_ref,
            f"expression-hash-ref:sha256:{metadata.expression_sha256}",
        }
        if not expected_resources.issubset(request.action_request.resource_refs):
            reasons.append("reason-ref:sealed-calculation:resource-binding-mismatch")
        try:
            expected_policy_ref = self.policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:sealed-calculation:policy-denied")
        else:
            if (
                request.action_request.constraints.get("policy_decision_ref")
                != expected_policy_ref
            ):
                reasons.append("reason-ref:sealed-calculation:policy-binding-mismatch")
        reasons.extend(
            f"reason-ref:sealed-calculation:{code.lower().replace('_', '-')}"
            for code in self._backend.readiness_reason_codes()
        )
        return list(dict.fromkeys(reasons))

    def policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        metadata = SealedCalculationDispatchMetadata.model_validate(
            tool_request.metadata
        )
        task = TaskEnvelope(
            task_id=request.run_ref,
            user_request="Evaluate one bounded arithmetic expression.",
            objective="Return one numeric evidence preview and content-free receipt refs.",
            scope=[SEALED_CALCULATION_CAPABILITY_REF],
            out_of_scope=["python", "shell", "filesystem", "network", "packages"],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[SEALED_CALCULATION_TOOL_REF],
            acceptance_criteria=["Return an exact bounded numeric result."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={
                "target_ref": metadata.target_ref,
                "expression_sha256": metadata.expression_sha256,
            },
        )
        decision = self._policy.can_execute(
            self._manifest,
            task,
            {
                "allowed_capability_ids": [self._manifest.id],
                "max_risk_level": RiskLevel.low.value,
                "capability_health": {self._manifest.id: "healthy"},
                "coordination_mode": CoordinationMode.workflow_node.value,
            },
        )
        if decision.status != PolicyDecisionStatus.allowed or not decision.allowed:
            raise ValueError("SEALED_CALCULATION_POLICY_DENIED")
        return _canonical_ref(
            "policy-decision-ref:sealed-calculation",
            {
                "decision": decision.model_dump(mode="json"),
                "dispatch_ref": request.dispatch_ref,
                "run_ref": request.run_ref,
                "lease_ref": request.lease_ref,
                "input_ref": metadata.input_ref,
                "expression_sha256": metadata.expression_sha256,
                "target_ref": metadata.target_ref,
            },
        )

    def start(
        self,
        request: AuthorityDispatchRequest,
        *,
        validate_commit_fence: Callable[[], tuple[list[str], datetime]],
        claim_handle: Callable[
            [_SealedCalculationDispatchHandle],
            _SealedCalculationDispatchHandle,
        ],
    ) -> _SealedCalculationDispatchHandle:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        metadata = SealedCalculationDispatchMetadata.model_validate(
            tool_request.metadata
        )
        transient = self._input_store.get(metadata.input_ref)
        if transient is None:
            raise ValueError("SEALED_CALCULATION_TRANSIENT_INPUT_REQUIRED")
        try:
            try:
                return self._backend.start(
                    execution_ref=authority_dispatch_execution_ref(request),
                    request=transient,
                    validate_commit_fence=validate_commit_fence,
                    claim_handle=lambda backend_handle: claim_handle(
                        _SealedCalculationDispatchHandle(
                            backend_handle,
                            operation_count=self.descriptor.operation_count,
                            result_sink=self._record_result,
                            result_discard=self._discard_result,
                        )
                    ),
                )
            except (
                SealedCalculationCleanupUnconfirmedError,
                SealedCalculationExecutionTruthUnknownError,
            ) as exc:
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "AUTHORITY_DISPATCH_ATOMIC_START_CONTAINMENT_UNCONFIRMED"
                ) from exc
        finally:
            self._input_store.discard(metadata.input_ref)

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        raise RuntimeError("SEALED_CALCULATION_ATOMIC_START_REQUIRED")

    def take_result(self, execution_ref: str) -> SealedCalculationResult | None:
        with self._results_lock:
            result = self._results.pop(execution_ref, None)
            return result.model_copy(deep=True) if result is not None else None

    def _record_result(self, result: SealedCalculationResult) -> None:
        with self._results_lock:
            self._results[result.execution_ref] = result.model_copy(deep=True)

    def _discard_result(self, execution_ref: str) -> None:
        with self._results_lock:
            self._results.pop(execution_ref, None)
