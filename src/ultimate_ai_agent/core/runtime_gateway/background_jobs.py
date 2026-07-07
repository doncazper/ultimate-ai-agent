from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_BACKGROUND_JOBS_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-background-jobs:v1"
)
RUNTIME_BACKGROUND_JOBS_ROUTE_REF = "GET /api/runtime/background-jobs"
RUNTIME_BACKGROUND_JOBS_CLI_REF = "uaa runtime inspect-background-jobs"
RUNTIME_BACKGROUND_JOBS_SNAPSHOT_REF = "background-jobs-snapshot-ref:runtime:proposals"
RUNTIME_BACKGROUND_JOBS_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-31:background-jobs"
)
RUNTIME_BACKGROUND_JOBS_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-31:background-jobs"
)
RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF = "lane-ref:background-autonomy-scoped"
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:background-jobs-no-autonomous-background-execution",
    "blocked-authority:background-jobs-no-background-worker",
    "blocked-authority:background-jobs-no-scheduler",
    "blocked-authority:background-jobs-no-autonomous-retry",
    "blocked-authority:background-jobs-no-external-delivery",
    "blocked-authority:background-jobs-no-provider-call",
    "blocked-authority:background-jobs-no-shell-execution",
    "blocked-authority:background-jobs-no-connector-write",
    "blocked-authority:background-jobs-no-control-center-authority-mint",
    "blocked-authority:background-jobs-no-raw-job-payload-persistence",
)


class RuntimeBackgroundJobKind(str, Enum):
    runtime_doctor_check = "runtime_doctor_check"
    proof_pack_export = "proof_pack_export"
    context_budget_review = "context_budget_review"
    connector_delivery_followup = "connector_delivery_followup"


class RuntimeBackgroundJobStatus(str, Enum):
    proposal = "proposal"
    paused = "paused"
    approval_required = "approval_required"
    execution_blocked = "execution_blocked"


class RuntimeBackgroundJobSchedulePolicy(str, Enum):
    manual_review_only = "manual_review_only"
    operator_window_required = "operator_window_required"
    blocked_scheduler = "blocked_scheduler"


class RuntimeBackgroundJobProposalReadModel(BaseModel):
    job_ref: str
    display_label: str
    job_kind: RuntimeBackgroundJobKind
    status: RuntimeBackgroundJobStatus
    schedule_policy: RuntimeBackgroundJobSchedulePolicy
    cadence_ref: str
    approval_scope_ref: str
    idempotency_ref: str
    safe_disable_ref: str
    receipt_plan_ref: str
    failure_handling_ref: str
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    pause_enabled: bool = False
    resume_enabled: bool = False
    run_now_enabled: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    autonomous_retry_enabled: bool = False
    external_delivery_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    connector_write_enabled: bool = False
    raw_job_payload_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "RuntimeBackgroundJobProposalReadModel":
        for value, field_name in [
            (self.job_ref, "job_ref"),
            (self.cadence_ref, "cadence_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.failure_handling_ref, "failure_handling_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.job_kind), "job_kind"),
            (str(self.status), "status"),
            (str(self.schedule_policy), "schedule_policy"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "pause_enabled": self.pause_enabled,
            "resume_enabled": self.resume_enabled,
            "run_now_enabled": self.run_now_enabled,
            "scheduler_enabled": self.scheduler_enabled,
            "background_worker_enabled": self.background_worker_enabled,
            "autonomous_retry_enabled": self.autonomous_retry_enabled,
            "external_delivery_enabled": self.external_delivery_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_job_payload_persisted": self.raw_job_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_BACKGROUND_JOB_EXECUTION_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_BACKGROUND_JOB_BLOCKERS_REQUIRED")
        if not self.proof_refs:
            raise ValueError("RUNTIME_BACKGROUND_JOB_PROOF_REQUIRED")
        return self


class RuntimeBackgroundJobsReadModel(BaseModel):
    schema_version: str = "runtime_background_jobs.v1"
    contract_ref: str = RUNTIME_BACKGROUND_JOBS_CONTRACT_REF
    status: str = "durable_job_proposal_posture"
    snapshot_ref: str = RUNTIME_BACKGROUND_JOBS_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-background-jobs:pending"
    route_ref: str = RUNTIME_BACKGROUND_JOBS_ROUTE_REF
    cli_ref: str = RUNTIME_BACKGROUND_JOBS_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str = RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_ROUTE_REF
    authority_state_cli_ref: str = RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_CLI_REF
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Background job posture exposes durable job proposals and blocked "
        "scheduler labels only; no worker or autonomous execution is enabled."
    )
    jobs: list[RuntimeBackgroundJobProposalReadModel] = Field(default_factory=list)
    job_count: int = 0
    proposal_count: int = 0
    paused_count: int = 0
    approval_required_count: int = 0
    execution_blocked_count: int = 0
    reviewable_job_count: int = 0
    durable_job_refs_visible: bool = True
    schedule_policy_visible: bool = True
    approval_scope_visible: bool = True
    idempotency_visible: bool = True
    safe_disable_visible: bool = True
    receipt_plan_visible: bool = True
    failure_handling_visible: bool = True
    pause_enabled: bool = False
    resume_enabled: bool = False
    run_now_enabled: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    autonomous_background_execution_enabled: bool = False
    autonomous_retry_enabled: bool = False
    external_delivery_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_job_payload_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_job_payloads_omitted",
            "raw_schedule_material_omitted",
            "worker_logs_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeBackgroundJobsReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_UNKNOWN")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_BACKGROUND_JOBS_AUTHORITY_OUTCOME_UNKNOWN")
        if self.job_count != len(self.jobs):
            raise ValueError("RUNTIME_BACKGROUND_JOB_COUNT_DRIFT")
        status_counts = {
            RuntimeBackgroundJobStatus.proposal.value: self.proposal_count,
            RuntimeBackgroundJobStatus.paused.value: self.paused_count,
            RuntimeBackgroundJobStatus.approval_required.value: (
                self.approval_required_count
            ),
            RuntimeBackgroundJobStatus.execution_blocked.value: (
                self.execution_blocked_count
            ),
        }
        for status, expected in status_counts.items():
            actual = sum(1 for job in self.jobs if job.status == status)
            if actual != expected:
                raise ValueError("RUNTIME_BACKGROUND_JOB_STATUS_COUNT_DRIFT")
        expected_reviewable = sum(
            1
            for job in self.jobs
            if job.status
            in {
                RuntimeBackgroundJobStatus.proposal.value,
                RuntimeBackgroundJobStatus.paused.value,
                RuntimeBackgroundJobStatus.approval_required.value,
            }
        )
        if self.reviewable_job_count != expected_reviewable:
            raise ValueError("RUNTIME_BACKGROUND_JOB_REVIEWABLE_COUNT_DRIFT")
        visibility_flags = {
            "durable_job_refs_visible": self.durable_job_refs_visible,
            "schedule_policy_visible": self.schedule_policy_visible,
            "approval_scope_visible": self.approval_scope_visible,
            "idempotency_visible": self.idempotency_visible,
            "safe_disable_visible": self.safe_disable_visible,
            "receipt_plan_visible": self.receipt_plan_visible,
            "failure_handling_visible": self.failure_handling_visible,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_BACKGROUND_JOB_VISIBILITY_REQUIRED: " + ", ".join(missing)
            )
        denied_flags = {
            "pause_enabled": self.pause_enabled,
            "resume_enabled": self.resume_enabled,
            "run_now_enabled": self.run_now_enabled,
            "scheduler_enabled": self.scheduler_enabled,
            "background_worker_enabled": self.background_worker_enabled,
            "autonomous_background_execution_enabled": (
                self.autonomous_background_execution_enabled
            ),
            "autonomous_retry_enabled": self.autonomous_retry_enabled,
            "external_delivery_enabled": self.external_delivery_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_job_payload_persisted": self.raw_job_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_BACKGROUND_JOBS_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_BACKGROUND_JOBS_BLOCKER_MISSING")
        if RUNTIME_BACKGROUND_JOBS_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_BACKGROUND_JOBS_PROOF_REF_REQUIRED")
        if RUNTIME_BACKGROUND_JOBS_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_BACKGROUND_JOBS_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-background-jobs:{digest}"


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _job(
    slug: str,
    *,
    display_label: str,
    job_kind: RuntimeBackgroundJobKind,
    status: RuntimeBackgroundJobStatus,
    schedule_policy: RuntimeBackgroundJobSchedulePolicy,
    safe_summary: str,
) -> RuntimeBackgroundJobProposalReadModel:
    return RuntimeBackgroundJobProposalReadModel(
        job_ref=f"background-job-ref:{slug}",
        display_label=display_label,
        job_kind=job_kind,
        status=status,
        schedule_policy=schedule_policy,
        cadence_ref=f"cadence-ref:background-job:{slug}:review-only",
        approval_scope_ref=f"approval-scope-ref:background-job:{slug}",
        idempotency_ref=f"idempotency-ref:background-job:{slug}",
        safe_disable_ref=f"safe-disable-ref:background-job:{slug}",
        receipt_plan_ref=f"receipt-plan-ref:background-job:{slug}",
        failure_handling_ref=f"failure-handling-ref:background-job:{slug}",
        safe_summary=safe_summary,
        proof_refs=[RUNTIME_BACKGROUND_JOBS_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:background-job:{slug}:review"],
    )


def build_runtime_background_jobs_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeBackgroundJobsReadModel:
    return build_runtime_background_jobs_read_model_from_authority_catalog(
        authority_decision_catalog=authority_decision_catalog
        or build_authority_decision_catalog(),
    )


def build_runtime_background_jobs_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeBackgroundJobsReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    jobs = [
        _job(
            "runtime-doctor-check",
            display_label="Runtime doctor check",
            job_kind=RuntimeBackgroundJobKind.runtime_doctor_check,
            status=RuntimeBackgroundJobStatus.approval_required,
            schedule_policy=RuntimeBackgroundJobSchedulePolicy.manual_review_only,
            safe_summary=(
                "Reviewable runtime doctor check proposal; scheduler and worker "
                "execution remain blocked."
            ),
        ),
        _job(
            "proof-pack-export",
            display_label="Proof pack export",
            job_kind=RuntimeBackgroundJobKind.proof_pack_export,
            status=RuntimeBackgroundJobStatus.proposal,
            schedule_policy=RuntimeBackgroundJobSchedulePolicy.operator_window_required,
            safe_summary=(
                "Proof pack export is a durable proposal requiring an operator "
                "window before any future run lane."
            ),
        ),
        _job(
            "context-budget-review",
            display_label="Context budget review",
            job_kind=RuntimeBackgroundJobKind.context_budget_review,
            status=RuntimeBackgroundJobStatus.paused,
            schedule_policy=RuntimeBackgroundJobSchedulePolicy.manual_review_only,
            safe_summary=(
                "Context budget review is paused metadata; resume/run-now "
                "controls are not enabled."
            ),
        ),
        _job(
            "connector-delivery-followup",
            display_label="Connector delivery follow-up",
            job_kind=RuntimeBackgroundJobKind.connector_delivery_followup,
            status=RuntimeBackgroundJobStatus.execution_blocked,
            schedule_policy=RuntimeBackgroundJobSchedulePolicy.blocked_scheduler,
            safe_summary=(
                "Connector delivery follow-up remains blocked because external "
                "delivery and connector writes are not promoted."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "jobs": [job.model_dump(mode="json") for job in jobs],
        "blocked": list(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeBackgroundJobsReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        jobs=jobs,
        job_count=len(jobs),
        proposal_count=sum(
            1 for job in jobs if job.status == RuntimeBackgroundJobStatus.proposal.value
        ),
        paused_count=sum(
            1 for job in jobs if job.status == RuntimeBackgroundJobStatus.paused.value
        ),
        approval_required_count=sum(
            1
            for job in jobs
            if job.status == RuntimeBackgroundJobStatus.approval_required.value
        ),
        execution_blocked_count=sum(
            1
            for job in jobs
            if job.status == RuntimeBackgroundJobStatus.execution_blocked.value
        ),
        reviewable_job_count=sum(
            1
            for job in jobs
            if job.status
            in {
                RuntimeBackgroundJobStatus.proposal.value,
                RuntimeBackgroundJobStatus.paused.value,
                RuntimeBackgroundJobStatus.approval_required.value,
            }
        ),
        blocked_authority_refs=list(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:background-jobs:exact-job-type",
            "promotion-path-ref:background-jobs:schedule-policy",
            "promotion-path-ref:background-jobs:approval-binding",
            "promotion-path-ref:background-jobs:idempotency",
            "promotion-path-ref:background-jobs:safe-disable",
            "promotion-path-ref:background-jobs:receipt",
            "promotion-path-ref:background-jobs:failure-handling",
        ],
        proof_refs=[
            RUNTIME_BACKGROUND_JOBS_PROOF_REF,
            "proof-ref:background-jobs:durable-proposals",
            "proof-ref:background-jobs:blocked-execution-labels",
        ],
        verifier_refs=[RUNTIME_BACKGROUND_JOBS_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:background-jobs:review-job-types",
            "next-safe-action-ref:background-jobs:bind-schedule-policy",
            "next-safe-action-ref:background-jobs:keep-workers-blocked",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    entries = {entry.lane_ref: entry for entry in catalog}
    if RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF not in entries:
        raise ValueError("RUNTIME_BACKGROUND_JOBS_AUTHORITY_CATALOG_MISSING")
    return entries[RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF]
