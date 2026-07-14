from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.evals.capability_metrics import (
    CAPABILITY_COMPONENT_IDS,
    AgentCapabilityEvaluationReport,
    CapabilityEvaluationStatus,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CAPABILITY_MATURITY_SCHEMA_VERSION = "uaa-capability-maturity.v1"
CAPABILITY_MATURITY_CONTRACT_REF = "contract-ref:capability-maturity:v1"


class CapabilityMaturityEvidenceStatus(str, Enum):
    baseline_only = "baseline_only"
    target_proven = "target_proven"
    ceiling_defended = "ceiling_defended"
    evidence_failed = "evidence_failed"


class _FrozenMaturityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CapabilityMaturityDefinition(_FrozenMaturityModel):
    component_id: str
    label: str
    weight: int = Field(..., ge=1, le=10)
    baseline_score: int = Field(..., ge=0, le=10)
    target_score: int = Field(..., ge=0, le=10)
    implementation_ref: str
    test_ref: str
    operator_surface_ref: str

    @model_validator(mode="after")
    def validate_definition(self) -> "CapabilityMaturityDefinition":
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown capability maturity component")
        expected_target = min(10, self.baseline_score + 1)
        if self.target_score != expected_target:
            raise ValueError("capability maturity target must be exactly one point higher or capped at 10")
        validate_safe_execution_text(self.label, "label")
        for name, value in (
            ("implementation_ref", self.implementation_ref),
            ("test_ref", self.test_ref),
            ("operator_surface_ref", self.operator_surface_ref),
        ):
            validate_execution_ref(value, name)
        return self


class CapabilityMaturityComponent(_FrozenMaturityModel):
    component_id: str
    label: str
    weight: int
    baseline_score: int
    target_score: int
    verified_score: int
    evidence_status: CapabilityMaturityEvidenceStatus
    scenario_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    evidence_refs: tuple[str, ...] = Field(..., min_length=3, max_length=24)
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_component(self) -> "CapabilityMaturityComponent":
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown capability maturity component")
        if self.verified_score not in {self.baseline_score, self.target_score}:
            raise ValueError("verified score must remain at baseline or reach the exact target")
        if self.evidence_status in {
            CapabilityMaturityEvidenceStatus.target_proven,
            CapabilityMaturityEvidenceStatus.ceiling_defended,
        } and self.verified_score != self.target_score:
            raise ValueError("proven component must use target score")
        if self.evidence_status in {
            CapabilityMaturityEvidenceStatus.baseline_only,
            CapabilityMaturityEvidenceStatus.evidence_failed,
        } and self.verified_score != self.baseline_score:
            raise ValueError("unproven component must remain at baseline")
        for ref in (*self.scenario_refs, *self.evidence_refs):
            validate_execution_ref(ref, "component_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        return self


class CapabilityMaturityReadModel(_FrozenMaturityModel):
    schema_version: Literal["uaa-capability-maturity.v1"] = (
        CAPABILITY_MATURITY_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:capability-maturity:v1"] = (
        CAPABILITY_MATURITY_CONTRACT_REF
    )
    read_model_ref: str
    evidence_report_ref: str | None = None
    evidence_report_digest_ref: str | None = None
    verification_posture: Literal[
        "evaluation_required", "targets_proven", "evaluation_failed"
    ]
    baseline_weighted_score: float = Field(..., ge=0, le=100)
    target_weighted_score: float = Field(..., ge=0, le=100)
    verified_weighted_score: float = Field(..., ge=0, le=100)
    component_count: Literal[16] = 16
    uplift_target_count: int = Field(..., ge=0, le=16)
    uplift_proven_count: int = Field(..., ge=0, le=16)
    ceiling_defended_count: int = Field(..., ge=0, le=16)
    components: tuple[CapabilityMaturityComponent, ...]
    backend_owned: Literal[True] = True
    read_only: Literal[True] = True
    content_free: Literal[True] = True
    authority_granted: Literal[False] = False
    score_increase_requires_runtime_evidence: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=400)

    @model_validator(mode="after")
    def validate_read_model(self) -> "CapabilityMaturityReadModel":
        validate_execution_ref(self.contract_ref, "contract_ref")
        validate_execution_ref(self.read_model_ref, "read_model_ref")
        if self.evidence_report_ref is not None:
            validate_execution_ref(self.evidence_report_ref, "evidence_report_ref")
        if self.evidence_report_digest_ref is not None:
            validate_execution_ref(
                self.evidence_report_digest_ref, "evidence_report_digest_ref"
            )
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if tuple(item.component_id for item in self.components) != tuple(
            CAPABILITY_COMPONENT_IDS
        ):
            raise ValueError("capability maturity read model must preserve taxonomy order")
        return self


_DEFINITION_ROWS = (
    ("reasoning_task_understanding", "Reasoning and task understanding", 8, 8, "intent/reasoning_truth.py", "test_phase01_reasoning_truth.py"),
    ("planning_orchestration", "Planning and orchestration", 8, 10, "execution/mission_orchestrator.py", "test_authority_mission_orchestrator_hardening.py"),
    ("learning_adaptation", "Learning and adaptation", 8, 8, "memory/review_runtime.py", "test_governed_memory_context_phase03.py"),
    ("memory_context_management", "Memory and context management", 9, 9, "memory/governed_context.py", "test_governed_memory_context_phase03.py"),
    ("communication_interaction", "Communication and interaction quality", 7, 8, "control_center/chat_to_loop_handoff.py", "test_chat_to_loop_handoff_v1.py"),
    ("action_tool_calling", "Action and tool calling", 9, 9, "authority/dispatcher.py", "test_authority_dispatcher_approval_and_start.py"),
    ("autonomy_authority", "Autonomy and authority management", 10, 10, "authority/dispatcher.py", "test_authority_mission_approval_wait.py"),
    ("code_implementation_assistance", "Code and implementation assistance", 6, 8, "files/manager.py", "test_file_atomic_writes.py"),
    ("research_web_external", "Research, web, and external information", 5, 10, "web_access/research_aggregation.py", "test_web_research_aggregation.py"),
    ("model_provider_management", "Model and provider management", 6, 8, "providers/router_dry_run.py", "test_provider_router_dry_run.py"),
    ("evidence_audit_observability", "Evidence, audit, and observability", 9, 9, "execution/portable_mission_evidence.py", "test_portable_mission_evidence.py"),
    ("safety_security_failure", "Safety, security, and failure handling", 10, 10, "execution/durable_mission_controls.py", "test_authority_mission_controls.py"),
    ("ux_ai_cockpit", "UX as an AI cockpit", 7, 8, "control_center/capability_surface.py", "App.test.tsx"),
    ("cli_api_parity", "CLI and API parity", 6, 9, "control_center/capability_surface.py", "test_control_center_api_routes.py"),
    ("extensibility_ecosystem", "Extensibility and ecosystem", 6, 9, "extension_catalog/exact_adapter.py", "test_exact_extension_adapter.py"),
    ("productized_agent_loop", "Productized agent loop", 10, 8, "control_center/founder_loop_mission.py", "test_founder_loop_filesystem_mission.py"),
)


CAPABILITY_MATURITY_DEFINITIONS = tuple(
    CapabilityMaturityDefinition(
        component_id=component_id,
        label=label,
        weight=weight,
        baseline_score=baseline,
        target_score=min(10, baseline + 1),
        implementation_ref=f"repo-ref:uaa:src/ultimate_ai_agent/core/{implementation_path}",
        test_ref=(
            f"repo-ref:uaa:apps/control-center/src/{test_path}"
            if test_path.endswith(".tsx")
            else f"repo-ref:uaa:tests/{test_path}"
        ),
        operator_surface_ref="repo-ref:uaa:apps/control-center/src/components/CapabilitySurfacePanel.tsx",
    )
    for component_id, label, weight, baseline, implementation_path, test_path in _DEFINITION_ROWS
)


def _weighted_score(scores: dict[str, int]) -> float:
    total_weight = sum(item.weight for item in CAPABILITY_MATURITY_DEFINITIONS)
    weighted = sum(
        scores[item.component_id] * item.weight
        for item in CAPABILITY_MATURITY_DEFINITIONS
    )
    return round(weighted / (10 * total_weight) * 100, 1)


def _report_digest(report: AgentCapabilityEvaluationReport) -> str:
    payload = report.model_dump(mode="json", exclude={"observations": {"__all__": {"duration_ms"}}})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"digest-ref:capability-maturity:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _component_is_proven(
    report: AgentCapabilityEvaluationReport,
    component_id: str,
) -> tuple[bool, tuple[str, ...]]:
    observations = tuple(
        item for item in report.observations if item.component_id == component_id
    )
    if not observations:
        return False, ()
    metrics_complete = all(
        item.task_completed is True
        and item.completion_claimed is True
        and item.evidence_complete is True
        and item.operator_interventions is not None
        and item.unsupported_claim_count == 0
        and item.policy_violation_refs == ()
        and (not item.recovery_expected or item.recovery_succeeded is True)
        and (not item.replay_expected or item.replay_succeeded is True)
        for item in observations
    )
    has_implemented_success = any(
        item.expected_status == CapabilityEvaluationStatus.passed
        and item.observed_status == CapabilityEvaluationStatus.passed
        for item in observations
    )
    return (
        report.status == CapabilityEvaluationStatus.passed
        and all(item.safe_outcome_adhered for item in observations)
        and metrics_complete
        and has_implemented_success,
        tuple(item.scenario_ref for item in observations),
    )


def build_capability_maturity_read_model(
    report: AgentCapabilityEvaluationReport | None = None,
) -> CapabilityMaturityReadModel:
    components: list[CapabilityMaturityComponent] = []
    for definition in CAPABILITY_MATURITY_DEFINITIONS:
        proven, scenario_refs = (
            _component_is_proven(report, definition.component_id)
            if report is not None
            else (False, ())
        )
        if proven:
            status = (
                CapabilityMaturityEvidenceStatus.ceiling_defended
                if definition.baseline_score == 10
                else CapabilityMaturityEvidenceStatus.target_proven
            )
            verified_score = definition.target_score
            blockers: tuple[str, ...] = ()
            summary = (
                "The existing score ceiling is defended by passing runtime, test, and operator-surface evidence."
                if status == CapabilityMaturityEvidenceStatus.ceiling_defended
                else "The one-point uplift target is proven by passing runtime, test, and operator-surface evidence."
            )
        else:
            status = (
                CapabilityMaturityEvidenceStatus.evidence_failed
                if report is not None
                else CapabilityMaturityEvidenceStatus.baseline_only
            )
            verified_score = definition.baseline_score
            blockers = ("CAPABILITY_MATURITY_EVALUATION_REQUIRED",) if report is None else ("CAPABILITY_MATURITY_EVIDENCE_FAILED",)
            summary = "The baseline is retained until the bounded empirical evaluation proves the target."
        components.append(
            CapabilityMaturityComponent(
                component_id=definition.component_id,
                label=definition.label,
                weight=definition.weight,
                baseline_score=definition.baseline_score,
                target_score=definition.target_score,
                verified_score=verified_score,
                evidence_status=status,
                scenario_refs=scenario_refs,
                evidence_refs=(
                    definition.implementation_ref,
                    definition.test_ref,
                    definition.operator_surface_ref,
                ),
                blocker_codes=blockers,
                safe_summary=summary,
            )
        )
    scores = {item.component_id: item.verified_score for item in components}
    baseline_scores = {
        item.component_id: item.baseline_score for item in CAPABILITY_MATURITY_DEFINITIONS
    }
    target_scores = {
        item.component_id: item.target_score for item in CAPABILITY_MATURITY_DEFINITIONS
    }
    uplift_proven = sum(
        item.evidence_status == CapabilityMaturityEvidenceStatus.target_proven
        for item in components
    )
    ceiling_defended = sum(
        item.evidence_status == CapabilityMaturityEvidenceStatus.ceiling_defended
        for item in components
    )
    all_proven = uplift_proven + ceiling_defended == len(components)
    return CapabilityMaturityReadModel(
        read_model_ref="read-model-ref:capability-maturity:v1",
        evidence_report_ref=report.report_ref if report is not None else None,
        evidence_report_digest_ref=_report_digest(report) if report is not None else None,
        verification_posture=(
            "targets_proven"
            if all_proven
            else "evaluation_failed"
            if report is not None
            else "evaluation_required"
        ),
        baseline_weighted_score=_weighted_score(baseline_scores),
        target_weighted_score=_weighted_score(target_scores),
        verified_weighted_score=_weighted_score(scores),
        uplift_target_count=sum(item.baseline_score < 10 for item in CAPABILITY_MATURITY_DEFINITIONS),
        uplift_proven_count=uplift_proven,
        ceiling_defended_count=ceiling_defended,
        components=tuple(components),
        safe_summary=(
            "All bounded one-point maturity targets are empirically proven and existing score ceilings remain defended; this evidence grants no runtime authority."
            if all_proven
            else "This backend-owned plan retains every baseline until bounded runtime, test, and operator-surface evidence proves each target; score visibility grants no authority."
        ),
    )


__all__ = [
    "CAPABILITY_MATURITY_CONTRACT_REF",
    "CAPABILITY_MATURITY_DEFINITIONS",
    "CAPABILITY_MATURITY_SCHEMA_VERSION",
    "CapabilityMaturityComponent",
    "CapabilityMaturityDefinition",
    "CapabilityMaturityEvidenceStatus",
    "CapabilityMaturityReadModel",
    "build_capability_maturity_read_model",
]
