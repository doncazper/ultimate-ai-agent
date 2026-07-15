from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.evals.capability_metrics import (
    CAPABILITY_COMPONENT_IDS,
    AgentCapabilityEvaluationReport,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CAPABILITY_MATURITY_SCHEMA_VERSION = "uaa-capability-maturity.v1"
CAPABILITY_MATURITY_CONTRACT_REF = "contract-ref:capability-maturity:v1"
CAPABILITY_MATURITY_BASELINE_SOURCE_REF = (
    "repo-ref:uaa:docs/benchmarks/runtime_capability_foundation/"
    "goat_comparison_20260712.json:initial_scores.uaa.components"
)
CAPABILITY_MATURITY_BASELINE_SCORES = {
    "reasoning_task_understanding": 8,
    "planning_orchestration": 10,
    "learning_adaptation": 8,
    "memory_context_management": 9,
    "communication_interaction": 8,
    "action_tool_calling": 9,
    "autonomy_authority": 10,
    "code_implementation_assistance": 8,
    "research_web_external": 10,
    "model_provider_management": 8,
    "evidence_audit_observability": 9,
    "safety_security_failure": 10,
    "ux_ai_cockpit": 8,
    "cli_api_parity": 9,
    "extensibility_ecosystem": 7,
    "productized_agent_loop": 8,
}


def _baseline_fingerprint(scores: dict[str, int]) -> str:
    encoded = json.dumps(scores, sort_keys=True, separators=(",", ":")).encode()
    return (
        "fingerprint-ref:capability-maturity-baseline:sha256:"
        f"{hashlib.sha256(encoded).hexdigest()}"
    )


CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF = _baseline_fingerprint(
    CAPABILITY_MATURITY_BASELINE_SCORES
)


class CapabilityMaturityEvidenceStatus(str, Enum):
    baseline_only = "baseline_only"
    automated_evidence_ready = "automated_evidence_ready"
    manual_validation_required = "manual_validation_required"
    external_dependency_required = "external_dependency_required"
    target_proven = "target_proven"
    ceiling_defended = "ceiling_defended"
    evidence_failed = "evidence_failed"


class CapabilityMaturityGateKind(str, Enum):
    implementation = "implementation"
    automated_tests = "automated_tests"
    runtime_scenario = "runtime_scenario"
    operator_surface = "operator_surface"
    recovery_and_failure = "recovery_and_failure"
    independent_acceptance = "independent_acceptance"


class CapabilityMaturityGateStatus(str, Enum):
    satisfied = "satisfied"
    pending = "pending"
    blocked = "blocked"


class CapabilityMaturityDecisionStatus(str, Enum):
    accepted = "accepted"
    held = "held"
    rejected = "rejected"


def capability_maturity_decision_ref(
    *,
    component_id: str,
    status: CapabilityMaturityDecisionStatus | str,
    evaluation_report_digest_ref: str,
    reviewer_ref: str,
    acceptance_ref: str,
    evidence_refs: tuple[str, ...],
    safe_summary: str,
) -> str:
    payload = json.dumps(
        {
            "contract_ref": CAPABILITY_MATURITY_CONTRACT_REF,
            "component_id": component_id,
            "status": (
                status.value
                if isinstance(status, CapabilityMaturityDecisionStatus)
                else status
            ),
            "evaluation_report_digest_ref": evaluation_report_digest_ref,
            "reviewer_ref": reviewer_ref,
            "acceptance_ref": acceptance_ref,
            "evidence_refs": evidence_refs,
            "safe_summary": safe_summary,
            "content_free": True,
            "authority_granted": False,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return (
        f"decision-ref:capability-maturity:sha256:{hashlib.sha256(payload).hexdigest()}"
    )


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
    acceptance_ref: str
    acceptance_summary: str = Field(..., min_length=1, max_length=320)
    external_dependency_code: str | None = None

    @model_validator(mode="after")
    def validate_definition(self) -> "CapabilityMaturityDefinition":
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown capability maturity component")
        expected_target = min(10, self.baseline_score + 1)
        if self.target_score != expected_target:
            raise ValueError(
                "capability maturity target must be exactly one point higher or capped at 10"
            )
        validate_safe_execution_text(self.label, "label")
        validate_safe_execution_text(self.acceptance_summary, "acceptance_summary")
        for name, value in (
            ("implementation_ref", self.implementation_ref),
            ("test_ref", self.test_ref),
            ("operator_surface_ref", self.operator_surface_ref),
            ("acceptance_ref", self.acceptance_ref),
        ):
            validate_execution_ref(value, name)
        if self.external_dependency_code is not None:
            validate_safe_execution_text(
                self.external_dependency_code, "external_dependency_code"
            )
        return self


class CapabilityMaturityEvidenceGate(_FrozenMaturityModel):
    gate_kind: CapabilityMaturityGateKind
    status: CapabilityMaturityGateStatus
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_gate(self) -> "CapabilityMaturityEvidenceGate":
        if (
            self.status == CapabilityMaturityGateStatus.satisfied
            and not self.evidence_refs
        ):
            raise ValueError("satisfied maturity gate requires evidence refs")
        if (
            self.status != CapabilityMaturityGateStatus.satisfied
            and not self.blocker_codes
        ):
            raise ValueError("unmet maturity gate requires blocker codes")
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        for code in self.blocker_codes:
            validate_safe_execution_text(code, "blocker_code")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        return self


class CapabilityMaturityGraduationDecision(_FrozenMaturityModel):
    decision_ref: str
    component_id: str
    status: CapabilityMaturityDecisionStatus
    evaluation_report_digest_ref: str
    reviewer_ref: str
    acceptance_ref: str
    evidence_refs: tuple[str, ...] = Field(..., min_length=2, max_length=16)
    safe_summary: str = Field(..., min_length=1, max_length=320)
    content_free: Literal[True] = True
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_decision(self) -> "CapabilityMaturityGraduationDecision":
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown maturity decision component")
        for name, value in (
            ("decision_ref", self.decision_ref),
            ("evaluation_report_digest_ref", self.evaluation_report_digest_ref),
            ("reviewer_ref", self.reviewer_ref),
            ("acceptance_ref", self.acceptance_ref),
        ):
            validate_execution_ref(value, name)
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "decision_evidence_ref")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("maturity decision evidence refs must be unique")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        expected_ref = capability_maturity_decision_ref(
            component_id=self.component_id,
            status=self.status,
            evaluation_report_digest_ref=self.evaluation_report_digest_ref,
            reviewer_ref=self.reviewer_ref,
            acceptance_ref=self.acceptance_ref,
            evidence_refs=self.evidence_refs,
            safe_summary=self.safe_summary,
        )
        if self.decision_ref != expected_ref:
            raise ValueError("maturity decision fingerprint drift")
        return self


class CapabilityMaturityComponent(_FrozenMaturityModel):
    component_id: str
    label: str
    weight: int
    baseline_score: int
    target_score: int
    verified_score: int
    evidence_status: CapabilityMaturityEvidenceStatus
    scenario_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    evidence_refs: tuple[str, ...] = Field(..., min_length=3, max_length=24)
    gates: tuple[CapabilityMaturityEvidenceGate, ...] = Field(
        ..., min_length=6, max_length=6
    )
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    next_acceptance_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_component(self) -> "CapabilityMaturityComponent":
        if self.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("unknown capability maturity component")
        if self.verified_score not in {self.baseline_score, self.target_score}:
            raise ValueError(
                "verified score must remain at baseline or reach the exact target"
            )
        gate_kinds = tuple(gate.gate_kind for gate in self.gates)
        if gate_kinds != tuple(CapabilityMaturityGateKind):
            raise ValueError(
                "maturity gates must be complete and preserve canonical order"
            )
        proven = self.evidence_status in {
            CapabilityMaturityEvidenceStatus.target_proven,
            CapabilityMaturityEvidenceStatus.ceiling_defended,
        }
        if proven and self.verified_score != self.target_score:
            raise ValueError("proven component must use target score")
        if not proven and self.verified_score != self.baseline_score:
            raise ValueError("unproven component must remain at baseline")
        if (
            self.evidence_status == CapabilityMaturityEvidenceStatus.target_proven
            and any(
                gate.status != CapabilityMaturityGateStatus.satisfied
                for gate in self.gates
            )
        ):
            raise ValueError("target proof requires every independent evidence gate")
        for ref in (*self.scenario_refs, *self.evidence_refs):
            validate_execution_ref(ref, "component_ref")
        validate_execution_ref(self.next_acceptance_ref, "next_acceptance_ref")
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
    baseline_source_ref: str = CAPABILITY_MATURITY_BASELINE_SOURCE_REF
    baseline_source_fingerprint_ref: str = CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF
    evidence_report_ref: str | None = None
    evidence_report_digest_ref: str | None = None
    verification_posture: Literal[
        "evaluation_required",
        "automated_evidence_ready",
        "partially_graduated",
        "targets_proven",
        "evaluation_failed",
    ]
    baseline_weighted_score: float = Field(..., ge=0, le=100)
    target_weighted_score: float = Field(..., ge=0, le=100)
    verified_weighted_score: float = Field(..., ge=0, le=100)
    component_count: Literal[16] = 16
    uplift_target_count: int = Field(..., ge=0, le=16)
    uplift_proven_count: int = Field(..., ge=0, le=16)
    automated_evidence_ready_count: int = Field(..., ge=0, le=16)
    manual_validation_required_count: int = Field(..., ge=0, le=16)
    external_dependency_required_count: int = Field(..., ge=0, le=16)
    ceiling_defended_count: int = Field(..., ge=0, le=16)
    components: tuple[CapabilityMaturityComponent, ...]
    backend_owned: Literal[True] = True
    read_only: Literal[True] = True
    content_free: Literal[True] = True
    authority_granted: Literal[False] = False
    score_increase_requires_runtime_evidence: Literal[True] = True
    score_increase_requires_independent_acceptance: Literal[True] = True
    trusted_acceptance_verification_implemented: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=400)

    @model_validator(mode="after")
    def validate_read_model(self) -> "CapabilityMaturityReadModel":
        validate_execution_ref(self.contract_ref, "contract_ref")
        validate_execution_ref(self.read_model_ref, "read_model_ref")
        validate_execution_ref(self.baseline_source_ref, "baseline_source_ref")
        validate_execution_ref(
            self.baseline_source_fingerprint_ref,
            "baseline_source_fingerprint_ref",
        )
        if self.baseline_source_ref != CAPABILITY_MATURITY_BASELINE_SOURCE_REF:
            raise ValueError("capability maturity baseline source drift")
        if (
            self.baseline_source_fingerprint_ref
            != CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF
        ):
            raise ValueError("capability maturity baseline fingerprint drift")
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
            raise ValueError(
                "capability maturity read model must preserve taxonomy order"
            )
        if (self.evidence_report_ref is None) != (
            self.evidence_report_digest_ref is None
        ):
            raise ValueError("maturity evidence report ref and digest must be paired")

        for component, definition in zip(
            self.components, CAPABILITY_MATURITY_DEFINITIONS, strict=True
        ):
            if (
                component.label != definition.label
                or component.weight != definition.weight
                or component.baseline_score != definition.baseline_score
                or component.target_score != definition.target_score
                or component.next_acceptance_ref != definition.acceptance_ref
                or component.evidence_refs
                != (
                    definition.implementation_ref,
                    definition.test_ref,
                    definition.operator_surface_ref,
                )
            ):
                raise ValueError("capability maturity component definition drift")

        baseline_scores = {
            item.component_id: item.baseline_score for item in self.components
        }
        target_scores = {
            item.component_id: item.target_score for item in self.components
        }
        verified_scores = {
            item.component_id: item.verified_score for item in self.components
        }
        if self.baseline_weighted_score != _weighted_score(baseline_scores):
            raise ValueError("capability maturity baseline weighted score drift")
        if baseline_scores != CAPABILITY_MATURITY_BASELINE_SCORES:
            raise ValueError("capability maturity canonical baseline drift")
        if self.target_weighted_score != _weighted_score(target_scores):
            raise ValueError("capability maturity target weighted score drift")
        if self.verified_weighted_score != _weighted_score(verified_scores):
            raise ValueError("capability maturity verified weighted score drift")
        if any(
            item.verified_score != item.baseline_score
            or item.evidence_status
            in {
                CapabilityMaturityEvidenceStatus.target_proven,
                CapabilityMaturityEvidenceStatus.ceiling_defended,
            }
            for item in self.components
        ):
            raise ValueError(
                "trusted acceptance verification is not implemented; scores must remain held"
            )

        uplift_proven = sum(
            item.evidence_status == CapabilityMaturityEvidenceStatus.target_proven
            for item in self.components
        )
        automated_ready = sum(
            item.evidence_status
            in {
                CapabilityMaturityEvidenceStatus.automated_evidence_ready,
                CapabilityMaturityEvidenceStatus.manual_validation_required,
                CapabilityMaturityEvidenceStatus.external_dependency_required,
                CapabilityMaturityEvidenceStatus.target_proven,
            }
            for item in self.components
        )
        manual_required = sum(
            item.evidence_status
            == CapabilityMaturityEvidenceStatus.manual_validation_required
            for item in self.components
        )
        external_required = sum(
            item.evidence_status
            == CapabilityMaturityEvidenceStatus.external_dependency_required
            for item in self.components
        )
        ceiling_defended = sum(
            item.evidence_status == CapabilityMaturityEvidenceStatus.ceiling_defended
            for item in self.components
        )
        expected_counts = (
            sum(item.baseline_score < 10 for item in self.components),
            uplift_proven,
            automated_ready,
            manual_required,
            external_required,
            ceiling_defended,
        )
        observed_counts = (
            self.uplift_target_count,
            self.uplift_proven_count,
            self.automated_evidence_ready_count,
            self.manual_validation_required_count,
            self.external_dependency_required_count,
            self.ceiling_defended_count,
        )
        if observed_counts != expected_counts:
            raise ValueError("capability maturity aggregate count drift")

        all_targets_proven = uplift_proven == expected_counts[0]
        any_failed = any(
            item.evidence_status == CapabilityMaturityEvidenceStatus.evidence_failed
            for item in self.components
        )
        expected_posture = (
            "targets_proven"
            if all_targets_proven
            else "evaluation_failed"
            if any_failed
            else "partially_graduated"
            if uplift_proven
            else "automated_evidence_ready"
            if automated_ready
            else "evaluation_required"
        )
        if self.verification_posture != expected_posture:
            raise ValueError("capability maturity verification posture drift")
        return self


_DEFINITION_ROWS = (
    (
        "reasoning_task_understanding",
        "Reasoning and task understanding",
        8,
        8,
        "intent/reasoning_truth.py",
        "test_phase01_reasoning_truth.py",
        "Run an ambiguity and contradiction trial from operator input and verify the explanation separates facts, assumptions, unknowns, and questions.",
    ),
    (
        "planning_orchestration",
        "Planning and orchestration",
        8,
        10,
        "execution/mission_orchestrator.py",
        "test_authority_mission_orchestrator_hardening.py",
        "Repeat the bounded DAG crash, replay, cancellation, and settlement drills on the release candidate.",
    ),
    (
        "learning_adaptation",
        "Learning and adaptation",
        8,
        8,
        "memory/review_runtime.py",
        "test_governed_memory_context_phase03.py",
        "Complete an operator-reviewed correction, supersession, rejection, and idempotent feedback replay trial.",
    ),
    (
        "memory_context_management",
        "Memory and context management",
        9,
        9,
        "memory/governed_context.py",
        "test_governed_memory_context_phase03.py",
        "Verify excluded, deleted, stale, and conflicting sources cannot enter a bounded context manifest.",
    ),
    (
        "communication_interaction",
        "Communication and interaction quality",
        7,
        8,
        "control_center/chat_to_loop_handoff.py",
        "test_chat_to_loop_handoff_v1.py",
        "Browser-test readable success, ambiguity, blocked, and failure handoffs with an operator.",
    ),
    (
        "action_tool_calling",
        "Action and tool calling",
        9,
        9,
        "authority/dispatcher.py",
        "test_authority_dispatcher_approval_and_start.py",
        "Run independent concurrent replay, pre-start revocation, and rollback-readiness drills for exact adapters.",
    ),
    (
        "autonomy_authority",
        "Autonomy and authority management",
        10,
        10,
        "authority/dispatcher.py",
        "test_authority_mission_approval_wait.py",
        "Repeat approval expiry, lease revocation, budget denial, and kill-switch adversarial drills on the release candidate.",
    ),
    (
        "code_implementation_assistance",
        "Code and implementation assistance",
        6,
        8,
        "files/manager.py",
        "test_file_atomic_writes.py",
        "Complete an operator-reviewed proposal, patch-hash, validation, exact apply, rollback, and receipt trial without generic shell authority.",
    ),
    (
        "research_web_external",
        "Research, web, and external information",
        5,
        10,
        "web_access/research_aggregation.py",
        "test_web_research_aggregation.py",
        "Repeat bounded citation, fallback, cost reconciliation, injection-isolation, and no-mutation drills.",
    ),
    (
        "model_provider_management",
        "Model and provider management",
        6,
        8,
        "providers/router_dry_run.py",
        "test_provider_router_dry_run.py",
        "Land the provider-intelligence slice, then validate routing explanation, readiness, latency, cost, and unknown-budget denial against a configured local provider.",
    ),
    (
        "evidence_audit_observability",
        "Evidence, audit, and observability",
        9,
        9,
        "execution/portable_mission_evidence.py",
        "test_portable_mission_evidence.py",
        "Independently verify tamper, truncation, reorder, replay, and cross-run substitution detection over an exported content-free receipt chain.",
    ),
    (
        "safety_security_failure",
        "Safety, security, and failure handling",
        10,
        10,
        "execution/durable_mission_controls.py",
        "test_authority_mission_controls.py",
        "Repeat redaction, corruption, stale state, cancellation, and recovery-required drills on the release candidate.",
    ),
    (
        "ux_ai_cockpit",
        "UX as an AI cockpit",
        7,
        8,
        "control_center/capability_surface.py",
        "App.test.tsx",
        "Browser-test desktop Today, Actions, Evidence, and Capabilities at supported viewport sizes and complete operator usability acceptance.",
    ),
    (
        "cli_api_parity",
        "CLI and API parity",
        6,
        9,
        "control_center/capability_surface.py",
        "test_control_center_api_routes.py",
        "Run one exact-SHA API, CLI, and desktop parity drill over success, blocked, stale, and failure states.",
    ),
    (
        "extensibility_ecosystem",
        "Extensibility and ecosystem",
        6,
        7,
        "extension_catalog/exact_adapter.py",
        "test_exact_extension_adapter.py",
        "Merge the exact extension lane, prove a second isolated adapter, then complete compatibility, safe-disable, rollback, replay, and developer-tooling acceptance.",
    ),
    (
        "productized_agent_loop",
        "Productized agent loop",
        10,
        8,
        "control_center/founder_loop_mission.py",
        "test_founder_loop_filesystem_mission.py",
        "Complete the desktop Today-to-proposal-to-approval-to-lease-to-execution-to-receipt-to-refreshed-Today operator trial.",
    ),
)

if tuple(CAPABILITY_MATURITY_BASELINE_SCORES) != tuple(CAPABILITY_COMPONENT_IDS):
    raise RuntimeError("capability maturity baseline taxonomy drift")
if {
    component_id: baseline for component_id, _, _, baseline, _, _, _ in _DEFINITION_ROWS
} != CAPABILITY_MATURITY_BASELINE_SCORES:
    raise RuntimeError("capability maturity definitions drift from canonical baseline")


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
        acceptance_ref=f"acceptance-ref:capability-maturity:{component_id}:v1",
        acceptance_summary=acceptance_summary,
        external_dependency_code=(
            "PROVIDER_INTELLIGENCE_INTEGRATION_REQUIRED"
            if component_id == "model_provider_management"
            else None
        ),
    )
    for (
        component_id,
        label,
        weight,
        baseline,
        implementation_path,
        test_path,
        acceptance_summary,
    ) in _DEFINITION_ROWS
)


def _weighted_score(scores: dict[str, int]) -> float:
    total_weight = sum(item.weight for item in CAPABILITY_MATURITY_DEFINITIONS)
    weighted = sum(
        scores[item.component_id] * item.weight
        for item in CAPABILITY_MATURITY_DEFINITIONS
    )
    return round(weighted / (10 * total_weight) * 100, 1)


def capability_maturity_report_digest(report: AgentCapabilityEvaluationReport) -> str:
    payload = report.model_dump(
        mode="json", exclude={"observations": {"__all__": {"duration_ms"}}}
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return (
        f"digest-ref:capability-maturity:sha256:{hashlib.sha256(encoded).hexdigest()}"
    )


@dataclass(frozen=True)
class _ComponentEvidencePosture:
    automated_tests: bool
    runtime_scenario: bool
    recovery_and_failure: bool
    scenario_refs: tuple[str, ...]


def _component_evidence_posture(
    report: AgentCapabilityEvaluationReport,
    component_id: str,
) -> _ComponentEvidencePosture:
    observations = tuple(
        item for item in report.observations if item.component_id == component_id
    )
    if not observations:
        return _ComponentEvidencePosture(False, False, False, ())
    automated_tests = all(item.safe_outcome_adhered for item in observations)
    runtime_scenario = all(
        item.task_completed is True
        and item.completion_claimed is True
        and item.evidence_complete is True
        for item in observations
    ) and any(item.passed_unblocked_verifier for item in observations)
    recovery_items = tuple(
        item for item in observations if item.recovery_expected or item.replay_expected
    )
    recovery_and_failure = bool(recovery_items) and all(
        (not item.recovery_expected or item.recovery_succeeded is True)
        and (not item.replay_expected or item.replay_succeeded is True)
        for item in recovery_items
    )
    return _ComponentEvidencePosture(
        automated_tests=automated_tests,
        runtime_scenario=runtime_scenario,
        recovery_and_failure=recovery_and_failure,
        scenario_refs=tuple(item.scenario_ref for item in observations),
    )


def _decision_for_component(
    decisions: tuple[CapabilityMaturityGraduationDecision, ...],
    definition: CapabilityMaturityDefinition,
    report_digest_ref: str | None,
) -> CapabilityMaturityGraduationDecision | None:
    matches = tuple(
        item for item in decisions if item.component_id == definition.component_id
    )
    if len(matches) > 1:
        raise ValueError("duplicate maturity graduation decision")
    if not matches:
        return None
    decision = matches[0]
    if decision.acceptance_ref != definition.acceptance_ref:
        raise ValueError("maturity decision acceptance binding drift")
    if (
        report_digest_ref is None
        or decision.evaluation_report_digest_ref != report_digest_ref
    ):
        raise ValueError("maturity decision evaluation binding drift")
    return decision


def _evidence_gates(
    definition: CapabilityMaturityDefinition,
    *,
    report_ref: str | None,
    evidence: _ComponentEvidencePosture,
    decision: CapabilityMaturityGraduationDecision | None,
) -> tuple[CapabilityMaturityEvidenceGate, ...]:
    automated_ref = report_ref or "evidence-ref:capability-maturity:evaluation-required"
    # A caller-created, self-consistent decision proves only its own fingerprint.
    # No trusted resolver or attestation lifecycle exists in this slice, so a
    # supplied acceptance assertion cannot advance a score.
    accepted = False
    external_blocked = definition.external_dependency_code is not None
    return (
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.implementation,
            status=CapabilityMaturityGateStatus.satisfied,
            evidence_refs=(definition.implementation_ref,),
            safe_summary="A concrete repository implementation surface exists.",
        ),
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.automated_tests,
            status=(
                CapabilityMaturityGateStatus.satisfied
                if evidence.automated_tests
                else CapabilityMaturityGateStatus.pending
            ),
            evidence_refs=(
                (definition.test_ref, automated_ref) if evidence.automated_tests else ()
            ),
            blocker_codes=(
                () if evidence.automated_tests else ("AUTOMATED_EVALUATION_REQUIRED",)
            ),
            safe_summary=(
                "Focused tests and the bounded evaluator passed."
                if evidence.automated_tests
                else "The bounded evaluator has not supplied complete automated evidence."
            ),
        ),
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.runtime_scenario,
            status=(
                CapabilityMaturityGateStatus.satisfied
                if evidence.runtime_scenario
                else CapabilityMaturityGateStatus.pending
            ),
            evidence_refs=((automated_ref,) if evidence.runtime_scenario else ()),
            blocker_codes=(
                () if evidence.runtime_scenario else ("RUNTIME_SCENARIO_REQUIRED",)
            ),
            safe_summary=(
                "Bounded runtime scenarios produced the expected safe outcome."
                if evidence.runtime_scenario
                else "A bounded runtime scenario must still produce the expected safe outcome."
            ),
        ),
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.operator_surface,
            status=CapabilityMaturityGateStatus.pending,
            blocker_codes=("OPERATOR_SURFACE_ACCEPTANCE_REQUIRED",),
            safe_summary=(
                "An operator surface is declared, but observed usability and parity "
                "acceptance remain unmeasured."
            ),
        ),
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.recovery_and_failure,
            status=(
                CapabilityMaturityGateStatus.satisfied
                if evidence.recovery_and_failure
                else CapabilityMaturityGateStatus.pending
            ),
            evidence_refs=(
                (definition.test_ref, automated_ref)
                if evidence.recovery_and_failure
                else ()
            ),
            blocker_codes=(
                ()
                if evidence.recovery_and_failure
                else ("FAILURE_AND_RECOVERY_PROOF_REQUIRED",)
            ),
            safe_summary=(
                "The bounded evidence includes safe failure, replay, or recovery posture where applicable."
                if evidence.recovery_and_failure
                else "Failure, replay, and recovery posture still require bounded evidence."
            ),
        ),
        CapabilityMaturityEvidenceGate(
            gate_kind=CapabilityMaturityGateKind.independent_acceptance,
            status=(
                CapabilityMaturityGateStatus.satisfied
                if accepted
                else CapabilityMaturityGateStatus.blocked
                if external_blocked
                else CapabilityMaturityGateStatus.pending
            ),
            evidence_refs=(
                decision.evidence_refs if accepted and decision is not None else ()
            ),
            blocker_codes=(
                ()
                if accepted
                else (
                    (definition.external_dependency_code,)
                    if external_blocked
                    else (
                        "TRUSTED_ACCEPTANCE_VERIFICATION_REQUIRED"
                        if decision is not None
                        and decision.status == CapabilityMaturityDecisionStatus.accepted
                        else "INDEPENDENT_ACCEPTANCE_REQUIRED",
                    )
                )
            ),
            safe_summary=(
                definition.acceptance_summary
                if decision is None
                else "A supplied decision is content-bound but cannot be trusted without a separately implemented acceptance verifier."
            ),
        ),
    )


def build_capability_maturity_read_model(
    report: AgentCapabilityEvaluationReport | None = None,
    *,
    graduation_decisions: tuple[CapabilityMaturityGraduationDecision, ...] = (),
) -> CapabilityMaturityReadModel:
    report_digest_ref = (
        capability_maturity_report_digest(report) if report is not None else None
    )
    components: list[CapabilityMaturityComponent] = []
    for definition in CAPABILITY_MATURITY_DEFINITIONS:
        evidence = (
            _component_evidence_posture(report, definition.component_id)
            if report is not None
            else _ComponentEvidencePosture(False, False, False, ())
        )
        decision = _decision_for_component(
            graduation_decisions, definition, report_digest_ref
        )
        gates = _evidence_gates(
            definition,
            report_ref=report.report_ref if report is not None else None,
            evidence=evidence,
            decision=decision,
        )
        unsatisfied_blockers = tuple(
            code
            for gate in gates
            if gate.status != CapabilityMaturityGateStatus.satisfied
            for code in gate.blocker_codes
        )
        if report is not None and not evidence.automated_tests:
            status = CapabilityMaturityEvidenceStatus.evidence_failed
            verified_score = definition.baseline_score
            blockers = ("CAPABILITY_MATURITY_AUTOMATED_EVIDENCE_FAILED",)
            summary = "The baseline is retained because bounded automated evidence is incomplete or failed."
        elif (
            evidence.automated_tests and definition.external_dependency_code is not None
        ):
            status = CapabilityMaturityEvidenceStatus.external_dependency_required
            verified_score = definition.baseline_score
            blockers = unsatisfied_blockers
            summary = "Automated checks passed, but external integration and the remaining evidence gates are unresolved."
        elif evidence.automated_tests:
            status = CapabilityMaturityEvidenceStatus.automated_evidence_ready
            verified_score = definition.baseline_score
            blockers = unsatisfied_blockers
            summary = "Automated checks passed; runtime, recovery, operator, and trusted acceptance truth remain independently gated."
        else:
            status = CapabilityMaturityEvidenceStatus.baseline_only
            verified_score = definition.baseline_score
            blockers = ("CAPABILITY_MATURITY_EVALUATION_REQUIRED",)
            summary = "The baseline is retained until automated evidence and independent acceptance both pass."
        components.append(
            CapabilityMaturityComponent(
                component_id=definition.component_id,
                label=definition.label,
                weight=definition.weight,
                baseline_score=definition.baseline_score,
                target_score=definition.target_score,
                verified_score=verified_score,
                evidence_status=status,
                scenario_refs=evidence.scenario_refs,
                evidence_refs=(
                    definition.implementation_ref,
                    definition.test_ref,
                    definition.operator_surface_ref,
                ),
                gates=gates,
                blocker_codes=blockers,
                next_acceptance_ref=definition.acceptance_ref,
                safe_summary=summary,
            )
        )
    scores = {item.component_id: item.verified_score for item in components}
    baseline_scores = {
        item.component_id: item.baseline_score
        for item in CAPABILITY_MATURITY_DEFINITIONS
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
    automated_ready = sum(
        item.evidence_status
        in {
            CapabilityMaturityEvidenceStatus.automated_evidence_ready,
            CapabilityMaturityEvidenceStatus.manual_validation_required,
            CapabilityMaturityEvidenceStatus.external_dependency_required,
            CapabilityMaturityEvidenceStatus.target_proven,
        }
        for item in components
    )
    manual_required = sum(
        item.evidence_status
        == CapabilityMaturityEvidenceStatus.manual_validation_required
        for item in components
    )
    external_required = sum(
        item.evidence_status
        == CapabilityMaturityEvidenceStatus.external_dependency_required
        for item in components
    )
    all_targets_proven = uplift_proven == sum(
        item.baseline_score < 10 for item in CAPABILITY_MATURITY_DEFINITIONS
    )
    any_failed = any(
        item.evidence_status == CapabilityMaturityEvidenceStatus.evidence_failed
        for item in components
    )
    return CapabilityMaturityReadModel(
        read_model_ref="read-model-ref:capability-maturity:v1",
        evidence_report_ref=report.report_ref if report is not None else None,
        evidence_report_digest_ref=report_digest_ref,
        verification_posture=(
            "targets_proven"
            if all_targets_proven
            else "evaluation_failed"
            if any_failed
            else "partially_graduated"
            if uplift_proven
            else "automated_evidence_ready"
            if automated_ready
            else "evaluation_required"
        ),
        baseline_weighted_score=_weighted_score(baseline_scores),
        target_weighted_score=_weighted_score(target_scores),
        verified_weighted_score=_weighted_score(scores),
        uplift_target_count=sum(
            item.baseline_score < 10 for item in CAPABILITY_MATURITY_DEFINITIONS
        ),
        uplift_proven_count=uplift_proven,
        automated_evidence_ready_count=automated_ready,
        manual_validation_required_count=manual_required,
        external_dependency_required_count=external_required,
        ceiling_defended_count=ceiling_defended,
        components=tuple(components),
        safe_summary=(
            "All one-point targets have runtime evidence and trusted independent acceptance; score visibility grants no authority."
            if all_targets_proven
            else "Passing tests advance only their own evidence gate. Every score stays at baseline until runtime, recovery, operator, external, and trusted acceptance evidence is independently verified."
        ),
    )


__all__ = [
    "CAPABILITY_MATURITY_CONTRACT_REF",
    "CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF",
    "CAPABILITY_MATURITY_BASELINE_SCORES",
    "CAPABILITY_MATURITY_BASELINE_SOURCE_REF",
    "CAPABILITY_MATURITY_DEFINITIONS",
    "CAPABILITY_MATURITY_SCHEMA_VERSION",
    "CapabilityMaturityComponent",
    "CapabilityMaturityDecisionStatus",
    "CapabilityMaturityDefinition",
    "CapabilityMaturityEvidenceGate",
    "CapabilityMaturityEvidenceStatus",
    "CapabilityMaturityGateKind",
    "CapabilityMaturityGateStatus",
    "CapabilityMaturityGraduationDecision",
    "CapabilityMaturityReadModel",
    "build_capability_maturity_read_model",
    "capability_maturity_decision_ref",
    "capability_maturity_report_digest",
]
