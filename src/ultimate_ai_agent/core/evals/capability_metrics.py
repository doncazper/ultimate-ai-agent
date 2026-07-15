from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CAPABILITY_EVALUATION_SCHEMA_VERSION = "uaa-agent-capability-evaluation.v1"
CAPABILITY_EVALUATION_CONTRACT_REF = "contract-ref:agent-capability-evaluation:v1"
CAPABILITY_COMPONENT_IDS = (
    "reasoning_task_understanding",
    "planning_orchestration",
    "learning_adaptation",
    "memory_context_management",
    "communication_interaction",
    "action_tool_calling",
    "autonomy_authority",
    "code_implementation_assistance",
    "research_web_external",
    "model_provider_management",
    "evidence_audit_observability",
    "safety_security_failure",
    "ux_ai_cockpit",
    "cli_api_parity",
    "extensibility_ecosystem",
    "productized_agent_loop",
)


class CapabilityEvaluationStatus(str, Enum):
    passed = "passed"
    blocked = "blocked"
    failed = "failed"


class _FrozenEvalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} contains duplicate refs")
    for value in values:
        _validate_ref(value, field_name)


class CapabilityScenarioObservation(_FrozenEvalModel):
    schema_version: Literal["uaa-agent-capability-evaluation.v1"] = (
        CAPABILITY_EVALUATION_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:agent-capability-evaluation:v1"] = (
        CAPABILITY_EVALUATION_CONTRACT_REF
    )
    scenario_ref: str
    component_id: str
    expected_status: CapabilityEvaluationStatus
    observed_status: CapabilityEvaluationStatus
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    verifier_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    execution_fingerprint_ref: str
    duration_ms: int = Field(..., ge=0, le=900_000)
    failure_code: Literal[
        "none",
        "assertion_failed",
        "timeout",
        "spawn_failed",
        "output_limit_exceeded",
    ] = "none"
    evidence_complete: bool | None = None
    task_completed: bool | None = None
    completion_claimed: bool | None = None
    operator_interventions: int | None = Field(default=None, ge=0, le=100)
    unsupported_claim_count: int | None = Field(default=None, ge=0, le=100)
    policy_violation_refs: tuple[str, ...] | None = Field(default=None, max_length=16)
    recovery_expected: bool = False
    recovery_succeeded: bool | None = None
    replay_expected: bool = False
    replay_succeeded: bool | None = None
    content_free: bool = True
    raw_content_persisted: bool = False
    authority_granted: bool = False

    @model_validator(mode="after")
    def validate_observation(self) -> "CapabilityScenarioObservation":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref(self.scenario_ref, "scenario_ref")
        _validate_ref(self.execution_fingerprint_ref, "execution_fingerprint_ref")
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown capability evaluation component")
        _validate_refs(self.evidence_refs, "evidence_refs")
        _validate_refs(self.verifier_refs, "verifier_refs")
        if self.policy_violation_refs is not None:
            _validate_refs(self.policy_violation_refs, "policy_violation_refs")
        if not self.content_free or self.raw_content_persisted:
            raise ValueError(
                "capability evaluation observations must remain content-free"
            )
        if self.authority_granted:
            raise ValueError("capability evaluation cannot grant authority")
        if (
            self.observed_status == CapabilityEvaluationStatus.blocked
            and self.task_completed is True
        ):
            raise ValueError("a truthfully blocked scenario cannot be task-complete")
        if self.completion_claimed is not None and self.task_completed is None:
            raise ValueError(
                "completion claims require independently recorded task truth"
            )
        if not self.recovery_expected and self.recovery_succeeded is not None:
            raise ValueError("recovery result requires recovery applicability")
        if not self.replay_expected and self.replay_succeeded is not None:
            raise ValueError("replay result requires replay applicability")
        if (
            self.observed_status == CapabilityEvaluationStatus.failed
            and self.failure_code == "none"
        ):
            raise ValueError("failed observation requires a failure code")
        if (
            self.observed_status != CapabilityEvaluationStatus.failed
            and self.failure_code != "none"
        ):
            raise ValueError("successful safe posture cannot carry a failure code")
        return self

    @property
    def safe_outcome_adhered(self) -> bool:
        return self.observed_status == self.expected_status

    @property
    def passed_unblocked_verifier(self) -> bool:
        return (
            self.expected_status == CapabilityEvaluationStatus.passed
            and self.observed_status == CapabilityEvaluationStatus.passed
        )


class AgentCapabilityEvaluationReport(_FrozenEvalModel):
    schema_version: Literal["uaa-agent-capability-evaluation.v1"] = (
        CAPABILITY_EVALUATION_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:agent-capability-evaluation:v1"] = (
        CAPABILITY_EVALUATION_CONTRACT_REF
    )
    report_ref: str
    benchmark_ref: str
    registry_fingerprint_ref: str
    status: CapabilityEvaluationStatus
    scenario_count: int = Field(..., ge=16, le=32)
    component_count: Literal[16] = 16
    component_ids: tuple[str, ...]
    observations: tuple[CapabilityScenarioObservation, ...]
    safe_outcome_adherence_rate: float = Field(..., ge=0.0, le=1.0)
    verification_pass_rate: float = Field(..., ge=0.0, le=1.0)
    passed_unblocked_verifier_rate: float = Field(..., ge=0.0, le=1.0)
    passed_unblocked_verifier_count: int = Field(..., ge=0)
    task_completion_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    task_completion_count: int | None = Field(default=None, ge=0)
    task_completion_posture: Literal["measured", "not_measured"] = "not_measured"
    blocked_safe_outcome_count: int = Field(..., ge=0)
    correctness_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    recovery_success_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_completeness_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    replay_correctness_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    operator_intervention_count: int | None = Field(default=None, ge=0)
    false_completion_count: int | None = Field(default=None, ge=0)
    unsupported_claim_count: int | None = Field(default=None, ge=0)
    authority_policy_violation_count: int | None = Field(default=None, ge=0)
    correctness_posture: Literal["measured", "not_measured"] = "not_measured"
    recovery_posture: Literal["measured", "not_measured", "not_applicable"] = (
        "not_measured"
    )
    evidence_completeness_posture: Literal["measured", "not_measured"] = "not_measured"
    replay_correctness_posture: Literal[
        "measured", "not_measured", "not_applicable"
    ] = "not_measured"
    operator_intervention_posture: Literal["measured", "not_measured"] = "not_measured"
    false_completion_posture: Literal["measured", "not_measured"] = "not_measured"
    unsupported_claim_posture: Literal["measured", "not_measured"] = "not_measured"
    authority_policy_violation_posture: Literal["measured", "not_measured"] = (
        "not_measured"
    )
    empirical_comparison_posture: Literal["cross_repo_not_measured"] = (
        "cross_repo_not_measured"
    )
    observed_product_experience_posture: Literal["not_measured"] = "not_measured"
    content_free: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    authority_granted: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_report(self) -> "AgentCapabilityEvaluationReport":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref(self.report_ref, "report_ref")
        _validate_ref(self.benchmark_ref, "benchmark_ref")
        _validate_ref(self.registry_fingerprint_ref, "registry_fingerprint_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.scenario_count != len(self.observations):
            raise ValueError("capability evaluation scenario count mismatch")
        expected_components = tuple(CAPABILITY_COMPONENT_IDS)
        if self.component_ids != expected_components:
            raise ValueError(
                "capability evaluation must cover the exact component taxonomy"
            )
        scenario_refs = [item.scenario_ref for item in self.observations]
        if len(scenario_refs) != len(set(scenario_refs)):
            raise ValueError("capability evaluation scenario refs must be unique")
        if {item.component_id for item in self.observations} != set(
            expected_components
        ):
            raise ValueError("capability evaluation must observe every component")
        return self


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def build_agent_capability_evaluation_report(
    *,
    report_ref: str,
    benchmark_ref: str,
    registry_fingerprint_ref: str,
    observations: tuple[CapabilityScenarioObservation, ...],
) -> AgentCapabilityEvaluationReport:
    if not 16 <= len(observations) <= 32:
        raise ValueError("capability evaluation requires 16-32 bounded observations")
    safe_outcome_count = sum(item.safe_outcome_adhered for item in observations)
    verification_pass_count = safe_outcome_count
    passed_unblocked_count = sum(
        item.passed_unblocked_verifier for item in observations
    )
    blocked_count = sum(
        item.observed_status == CapabilityEvaluationStatus.blocked
        for item in observations
    )
    interventions_measured = all(
        item.operator_interventions is not None for item in observations
    )
    task_completion_measured = all(
        item.task_completed is not None for item in observations
    )
    claims_measured = all(
        item.completion_claimed is not None and item.task_completed is not None
        for item in observations
    )
    unsupported_measured = all(
        item.unsupported_claim_count is not None for item in observations
    )
    policy_measured = all(
        item.policy_violation_refs is not None for item in observations
    )
    evidence_measured = all(item.evidence_complete is not None for item in observations)
    recovery_items = [item for item in observations if item.recovery_expected]
    replay_items = [item for item in observations if item.replay_expected]
    recovery_measured = bool(recovery_items) and all(
        item.recovery_succeeded is not None for item in recovery_items
    )
    replay_measured = bool(replay_items) and all(
        item.replay_succeeded is not None for item in replay_items
    )
    false_completion_count = (
        sum(
            item.completion_claimed is True and item.task_completed is False
            for item in observations
        )
        if claims_measured
        else None
    )
    unsupported_claim_count = (
        sum(item.unsupported_claim_count or 0 for item in observations)
        if unsupported_measured
        else None
    )
    policy_violation_count = (
        sum(len(item.policy_violation_refs or ()) for item in observations)
        if policy_measured
        else None
    )
    correctness_measured = unsupported_measured and policy_measured
    correctness_rate = (
        _rate(
            sum(
                item.safe_outcome_adhered
                and (item.unsupported_claim_count or 0) == 0
                and not (item.policy_violation_refs or ())
                for item in observations
            ),
            len(observations),
        )
        if correctness_measured
        else None
    )
    measured_failure = (
        correctness_rate not in {None, 1.0}
        or (
            recovery_measured
            and any(item.recovery_succeeded is not True for item in recovery_items)
        )
        or (
            evidence_measured
            and any(item.evidence_complete is not True for item in observations)
        )
        or (
            replay_measured
            and any(item.replay_succeeded is not True for item in replay_items)
        )
        or false_completion_count not in {None, 0}
        or unsupported_claim_count not in {None, 0}
        or policy_violation_count not in {None, 0}
    )
    passed = safe_outcome_count == len(observations) and not measured_failure
    any_structured_metrics = any(
        (
            correctness_measured,
            recovery_measured,
            evidence_measured,
            replay_measured,
            interventions_measured,
            task_completion_measured,
            claims_measured,
            unsupported_measured,
            policy_measured,
        )
    )
    return AgentCapabilityEvaluationReport(
        report_ref=report_ref,
        benchmark_ref=benchmark_ref,
        registry_fingerprint_ref=registry_fingerprint_ref,
        status=(
            CapabilityEvaluationStatus.passed
            if passed
            else CapabilityEvaluationStatus.failed
        ),
        scenario_count=len(observations),
        component_ids=tuple(CAPABILITY_COMPONENT_IDS),
        observations=observations,
        safe_outcome_adherence_rate=_rate(safe_outcome_count, len(observations)),
        verification_pass_rate=_rate(verification_pass_count, len(observations)),
        passed_unblocked_verifier_rate=_rate(passed_unblocked_count, len(observations)),
        passed_unblocked_verifier_count=passed_unblocked_count,
        task_completion_rate=(
            _rate(
                sum(item.task_completed is True for item in observations),
                len(observations),
            )
            if task_completion_measured
            else None
        ),
        task_completion_count=(
            sum(item.task_completed is True for item in observations)
            if task_completion_measured
            else None
        ),
        task_completion_posture=(
            "measured" if task_completion_measured else "not_measured"
        ),
        blocked_safe_outcome_count=blocked_count,
        correctness_rate=correctness_rate,
        recovery_success_rate=(
            _rate(
                sum(item.recovery_succeeded is True for item in recovery_items),
                len(recovery_items),
            )
            if recovery_measured
            else None
        ),
        evidence_completeness_rate=(
            _rate(
                sum(item.evidence_complete is True for item in observations),
                len(observations),
            )
            if evidence_measured
            else None
        ),
        replay_correctness_rate=(
            _rate(
                sum(item.replay_succeeded is True for item in replay_items),
                len(replay_items),
            )
            if replay_measured
            else None
        ),
        operator_intervention_count=(
            sum(item.operator_interventions or 0 for item in observations)
            if interventions_measured
            else None
        ),
        false_completion_count=false_completion_count,
        unsupported_claim_count=unsupported_claim_count,
        authority_policy_violation_count=policy_violation_count,
        correctness_posture="measured" if correctness_measured else "not_measured",
        recovery_posture=(
            "measured"
            if recovery_measured
            else "not_measured"
            if recovery_items
            else "not_applicable"
        ),
        evidence_completeness_posture="measured"
        if evidence_measured
        else "not_measured",
        replay_correctness_posture=(
            "measured"
            if replay_measured
            else "not_measured"
            if replay_items
            else "not_applicable"
        ),
        operator_intervention_posture="measured"
        if interventions_measured
        else "not_measured",
        false_completion_posture="measured" if claims_measured else "not_measured",
        unsupported_claim_posture="measured"
        if unsupported_measured
        else "not_measured",
        authority_policy_violation_posture="measured"
        if policy_measured
        else "not_measured",
        safe_summary=(
            "All bounded UAA capability verifiers matched expected safe postures and all supplied structured metrics passed."
            if passed and any_structured_metrics
            else "All bounded UAA capability verifiers matched expected safe postures; quality and incident metrics remain not measured."
            if passed
            else "One or more bounded UAA capability verifiers did not match the expected safe posture."
        ),
    )


__all__ = [
    "CAPABILITY_COMPONENT_IDS",
    "CAPABILITY_EVALUATION_CONTRACT_REF",
    "CAPABILITY_EVALUATION_SCHEMA_VERSION",
    "AgentCapabilityEvaluationReport",
    "CapabilityEvaluationStatus",
    "CapabilityScenarioObservation",
    "build_agent_capability_evaluation_report",
]
