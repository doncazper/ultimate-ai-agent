from __future__ import annotations

import hashlib
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CONTROL_CENTER_PROOF_CONTRACT_REF = "contract-ref:control-center-proof-spine:v1"
CONTROL_CENTER_PROOF_INDEX_SOURCE = "python_core_control_center_proof_index"
CONTROL_CENTER_PROOF_DETAIL_SOURCE = "python_core_control_center_proof_detail"
CONTROL_CENTER_PROOF_INDEX_ROUTE_REF = "GET /control-center/proof/index"
CONTROL_CENTER_PROOF_DETAIL_ROUTE_REF = "GET /control-center/proof/{proof_ref}"
CONTROL_CENTER_PROOF_CLI_REF = "python scripts/dev/uaa_founder_loop.py inspect-proof"

ProofKind = Literal[
    "daily_loop",
    "action_decision",
    "local_task_commit",
    "memory_decision",
    "evidence_event",
    "web_evidence",
    "source_readiness",
    "approval",
    "setup_package",
]

_DENIED_FLAGS = (
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "browser_execution_enabled",
    "shell_subprocess_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)
_COMMON_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:proof-detail:no-runtime-execution",
    "blocked-state:proof-detail:no-provider-model-call",
    "blocked-state:proof-detail:no-connector-write-or-send",
    "blocked-state:proof-detail:no-browser-execution",
    "blocked-state:proof-detail:no-shell-subprocess-execution",
    "blocked-state:proof-detail:no-background-autonomy",
    "blocked-state:proof-detail:no-production-authority",
)
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_-]+")
_ACTION_PROOF_NEXT_ITEM_GROUP_ORDER = (
    "approved_local_task_lane",
    "ready_for_decision",
    "proposal_only_no_execution_path",
    "blocked_by_authority",
    "expired_stale",
    "receipt_recorded",
)


class ControlCenterProofRunDetail(BaseModel):
    schema_version: str = "control-center-proof-run-detail.v1"
    contract_ref: str = CONTROL_CENTER_PROOF_CONTRACT_REF
    source: str = "python_core_control_center_proof_run_detail"
    run_detail_ref: str = Field(..., min_length=1)
    proof_ref: str = Field(..., min_length=1)
    proof_kind: ProofKind
    run_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    status: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=700)
    authority_posture: str = Field(..., min_length=1, max_length=700)
    full_strength_goal: str = (
        "Every action, approval, evidence event, memory decision, local task "
        "commit, and setup/package event opens coherent Proof and Run Detail."
    )
    repo_safe_scope: str = (
        "Backend-owned safe refs, bounded summaries, route refs, receipts, "
        "rollback/safe-disable refs, and blocked authority refs only."
    )
    blocked_authority_summary: str = (
        "Provider/model calls, connector writes or sends, browser automation, "
        "shell execution, background autonomy, public release claims, and "
        "production authority remain blocked."
    )
    exact_promotion_path_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)
    backend_route_refs: list[str] = Field(default_factory=list)
    cli_ref: str = CONTROL_CENTER_PROOF_CLI_REF
    related_run_refs: list[str] = Field(default_factory=list)
    operator_run_event_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    redaction_state: str = "safe_refs_and_bounded_summaries_only"
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    safe_refs_only: bool = True
    raw_content_included: bool = False
    control_center_presentation_only: bool = True
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_run_detail(self) -> "ControlCenterProofRunDetail":
        if self.schema_version != "control-center-proof-run-detail.v1":
            raise ValueError("Proof run detail schema drift")
        if self.contract_ref != CONTROL_CENTER_PROOF_CONTRACT_REF:
            raise ValueError("Proof run detail contract drift")
        if self.source != "python_core_control_center_proof_run_detail":
            raise ValueError("Proof run detail source drift")
        for field_name in ("run_detail_ref", "proof_ref", "run_ref"):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        if self.run_ref not in self.related_run_refs:
            raise ValueError("Proof run detail must include its run ref")
        for field_name in (
            "proof_kind",
            "status",
            "title",
            "safe_summary",
            "authority_posture",
            "full_strength_goal",
            "repo_safe_scope",
            "blocked_authority_summary",
            "cli_ref",
            "redaction_state",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "exact_promotion_path_refs",
            "related_run_refs",
            "operator_run_event_refs",
            "receipt_refs",
            "evidence_refs",
            "audit_refs",
            "approval_refs",
            "rollback_refs",
            "safe_disable_refs",
            "memory_candidate_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        _validate_text_list(self.backend_route_refs, "backend_route_refs")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Proof run detail must stay safe-ref only")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Proof run detail must not enable {flag}")
        return self


class ControlCenterProofRecord(BaseModel):
    schema_version: str = "control-center-proof-record.v1"
    contract_ref: str = CONTROL_CENTER_PROOF_CONTRACT_REF
    proof_ref: str = Field(..., min_length=1)
    proof_kind: ProofKind
    status: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=700)
    authority_posture: str = Field(..., min_length=1, max_length=700)
    route_refs: list[str] = Field(default_factory=list)
    backend_route_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    redaction_state: str = "safe_refs_and_bounded_summaries_only"
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    detail_route_ref: str = CONTROL_CENTER_PROOF_DETAIL_ROUTE_REF
    safe_refs_only: bool = True
    raw_content_included: bool = False
    control_center_presentation_only: bool = True
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False
    run_detail: ControlCenterProofRunDetail | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "ControlCenterProofRecord":
        if self.schema_version != "control-center-proof-record.v1":
            raise ValueError("Proof record schema drift")
        if self.contract_ref != CONTROL_CENTER_PROOF_CONTRACT_REF:
            raise ValueError("Proof record contract drift")
        validate_execution_ref(self.proof_ref, "proof_ref")
        for field_name in (
            "proof_kind",
            "status",
            "title",
            "safe_summary",
            "authority_posture",
            "redaction_state",
            "next_safe_action",
            "detail_route_ref",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "run_refs",
            "receipt_refs",
            "evidence_refs",
            "audit_refs",
            "approval_refs",
            "rollback_refs",
            "safe_disable_refs",
            "memory_candidate_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        _validate_text_list(self.backend_route_refs, "backend_route_refs")
        if self.run_detail is not None:
            if self.run_detail.proof_ref != self.proof_ref:
                raise ValueError("Proof record run detail proof ref drift")
            if self.run_detail.proof_kind != self.proof_kind:
                raise ValueError("Proof record run detail proof kind drift")
            if not self.run_refs:
                raise ValueError("Proof record run refs required with run detail")
            if self.run_detail.run_ref not in self.run_refs:
                raise ValueError("Proof record run detail run ref drift")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Proof record must stay safe-ref only")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Proof record must not enable {flag}")
        return self


class ControlCenterProofIndex(BaseModel):
    schema_version: str = "control-center-proof-index.v1"
    contract_ref: str = CONTROL_CENTER_PROOF_CONTRACT_REF
    source: str = CONTROL_CENTER_PROOF_INDEX_SOURCE
    status: str = "implemented_backend_owned_universal_proof_index"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    index_route_ref: str = CONTROL_CENTER_PROOF_INDEX_ROUTE_REF
    detail_route_ref: str = CONTROL_CENTER_PROOF_DETAIL_ROUTE_REF
    cli_ref: str = CONTROL_CENTER_PROOF_CLI_REF
    proof_count: int = Field(default=0, ge=0)
    proof_refs: list[str] = Field(default_factory=list)
    records: list[ControlCenterProofRecord] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = "Open one proof record and inspect safe refs only."
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_index(self) -> "ControlCenterProofIndex":
        if self.schema_version != "control-center-proof-index.v1":
            raise ValueError("Proof index schema drift")
        if self.source != CONTROL_CENTER_PROOF_INDEX_SOURCE:
            raise ValueError("Proof index source drift")
        if self.proof_count != len(self.records):
            raise ValueError("Proof index count drift")
        if self.proof_refs != [record.proof_ref for record in self.records]:
            raise ValueError("Proof index refs must match records")
        if any(record.run_detail is None for record in self.records):
            raise ValueError("Proof index records must include run detail")
        for field_name in (
            "status",
            "index_route_ref",
            "detail_route_ref",
            "cli_ref",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for ref in self.proof_refs:
            validate_execution_ref(ref, "proof_ref")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if not self.backend_owned or not self.local_read_model_only:
            raise ValueError("Proof index must remain backend-owned local read model")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Proof index must stay safe-ref only")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Proof index must not enable {flag}")
        return self


class ControlCenterProofDetail(BaseModel):
    schema_version: str = "control-center-proof-detail.v1"
    contract_ref: str = CONTROL_CENTER_PROOF_CONTRACT_REF
    source: str = CONTROL_CENTER_PROOF_DETAIL_SOURCE
    status: str = "implemented_backend_owned_universal_proof_detail"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    requested_proof_ref: str = Field(..., min_length=1)
    record: ControlCenterProofRecord
    next_safe_action: str = "Use this proof detail as inspection evidence only."
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_detail(self) -> "ControlCenterProofDetail":
        if self.source != CONTROL_CENTER_PROOF_DETAIL_SOURCE:
            raise ValueError("Proof detail source drift")
        validate_execution_ref(self.requested_proof_ref, "requested_proof_ref")
        if self.requested_proof_ref != self.record.proof_ref:
            raise ValueError("Proof detail requested ref must match record")
        if self.record.run_detail is None:
            raise ValueError("Proof detail record must include run detail")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if not self.backend_owned or not self.local_read_model_only:
            raise ValueError("Proof detail must remain backend-owned local read model")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Proof detail must stay safe-ref only")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Proof detail must not enable {flag}")
        return self


def build_control_center_proof_index(*, today_summary: dict[str, Any]) -> dict[str, Any]:
    records = _proof_records(today_summary)
    model = ControlCenterProofIndex(
        proof_count=len(records),
        proof_refs=[record.proof_ref for record in records],
        records=records,
        blocked_authority_refs=list(_COMMON_BLOCKED_AUTHORITY_REFS),
    )
    return model.model_dump(mode="json")


def build_control_center_proof_detail(
    *,
    today_summary: dict[str, Any],
    proof_ref: str,
) -> dict[str, Any]:
    validate_execution_ref(proof_ref, "proof_ref")
    records = _proof_records(today_summary)
    record_by_ref = {record.proof_ref: record for record in records}
    record = record_by_ref.get(proof_ref)
    if record is None:
        record = ControlCenterProofRecord(
            proof_ref=proof_ref,
            proof_kind="evidence_event",
            status="missing_proof_ref",
            title="Proof ref not found",
            safe_summary="The requested proof ref was not present in the current backend proof index.",
            authority_posture="Missing proof details grant no authority.",
            route_refs=["route-ref:control-center:proof"],
            backend_route_refs=[CONTROL_CENTER_PROOF_DETAIL_ROUTE_REF],
            run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
            evidence_refs=["evidence-ref:control-center:proof:not-found"],
            next_safe_action="Return to the proof index and select an available proof ref.",
            blocked_authority_refs=[
                *_COMMON_BLOCKED_AUTHORITY_REFS,
                "blocked-state:proof-detail:proof-ref-not-found",
            ],
        )
        record = _with_run_detail(record)
    model = ControlCenterProofDetail(
        requested_proof_ref=proof_ref,
        record=record,
        blocked_authority_refs=list(_COMMON_BLOCKED_AUTHORITY_REFS),
    )
    return model.model_dump(mode="json")


def _proof_records(today_summary: dict[str, Any]) -> list[ControlCenterProofRecord]:
    records: list[ControlCenterProofRecord] = []
    runs = _dict(today_summary.get("founder_loop_runs_integration_read_model"))
    evidence_refs = _refs(today_summary.get("evidence_refs"))
    records.append(_daily_loop_record(runs=runs, evidence_refs=evidence_refs))
    records.extend(_action_records(today_summary))
    records.append(_local_task_commit_record(today_summary))
    records.append(_memory_decision_record(today_summary))
    records.append(_evidence_event_record(today_summary))
    records.append(_web_evidence_record(today_summary))
    records.append(_source_readiness_record(today_summary))
    records.append(_approval_record(today_summary))
    records.append(_setup_package_record(today_summary))
    return _attach_run_details(_dedupe_records(records))


def _daily_loop_record(
    *,
    runs: dict[str, Any],
    evidence_refs: list[str],
) -> ControlCenterProofRecord:
    return ControlCenterProofRecord(
        proof_ref=str(
            runs.get("primary_proof_ref")
            or FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
        ),
        proof_kind="daily_loop",
        status=str(runs.get("status") or "implemented_backend_owned_run_proof_refs"),
        title="Governed Daily Loop",
        safe_summary=(
            "Start Here, Today, Action Inbox, Evidence, and Memory share one "
            "backend-owned local run/proof spine."
        ),
        authority_posture=(
            "Read-only proof inspection only; proof refs explain state and do "
            "not grant action execution or external authority."
        ),
        route_refs=["route-ref:control-center:start", "route-ref:control-center:today"],
        backend_route_refs=[
            "GET /control-center/start-here/summary",
            "GET /control-center/today/summary",
            CONTROL_CENTER_PROOF_INDEX_ROUTE_REF,
        ],
        run_refs=_refs(runs.get("run_refs"))
        or [FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        receipt_refs=_refs(runs.get("receipt_refs")),
        evidence_refs=evidence_refs or _refs(runs.get("evidence_refs")),
        approval_refs=_refs(runs.get("approval_refs")),
        memory_candidate_refs=_refs(runs.get("memory_candidate_refs")),
        blocked_authority_refs=_merge_refs(
            _refs(runs.get("blocked_authority_refs")),
            list(_COMMON_BLOCKED_AUTHORITY_REFS),
        ),
        next_safe_action="Inspect the action, evidence, and memory proof records.",
    )


def _action_records(today_summary: dict[str, Any]) -> list[ControlCenterProofRecord]:
    actions = _list_of_dicts(today_summary.get("actions"))
    records: list[ControlCenterProofRecord] = []
    for action in _actions_for_proof_index(actions):
        source_ref = _first_ref(
            action.get("action_envelope_ref"),
            action.get("item_ref"),
            fallback="action:missing",
        )
        records.append(
            ControlCenterProofRecord(
                proof_ref=_derived_proof_ref("action-decision", source_ref),
                proof_kind="action_decision",
                status=str(action.get("status") or "review_ready"),
                title=_safe_title(str(action.get("title") or "Action decision")),
                safe_summary=str(
                    action.get("action_envelope_safe_summary")
                    or action.get("safe_summary")
                    or "Action decision is represented by safe refs only."
                ),
                authority_posture=str(
                    action.get("action_authority_boundary")
                    or action.get("authority_boundary")
                    or "Decision proof does not execute the action."
                ),
                route_refs=["route-ref:control-center:actions"],
                backend_route_refs=[
                    "GET /control-center/actions/inbox",
                    "GET /control-center/actions/{action_id}/receipt",
                ],
                run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
                receipt_refs=_merge_refs(
                    _refs(action.get("receipt_refs")),
                    _refs(action.get("action_expected_receipt_refs")),
                ),
                evidence_refs=_refs(action.get("evidence_refs")),
                audit_refs=_refs(action.get("audit_refs")),
                approval_refs=_refs(
                    [
                        action.get("approval_envelope_ref"),
                        action.get("action_approval_requirement_ref"),
                    ]
                ),
                rollback_refs=_refs(
                    [action.get("rollback_ref"), action.get("action_rollback_ref")]
                ),
                safe_disable_refs=_refs(
                    [
                        action.get("safe_disable_ref"),
                        action.get("action_safe_disable_ref"),
                    ]
                ),
                blocked_authority_refs=_merge_refs(
                    _refs(action.get("action_blocked_state_refs")),
                    list(_COMMON_BLOCKED_AUTHORITY_REFS),
                ),
                next_safe_action=str(
                    action.get("next_safe_action")
                    or "Inspect the action receipt refs; do not execute from proof."
                ),
            )
        )
    return records


def _local_task_commit_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    actions = _list_of_dicts(today_summary.get("actions"))
    local_task = next(
        (
            action
            for action in actions
            if str(action.get("action_kind")) == "local_task_create"
            or "local-task" in str(action.get("item_ref"))
        ),
        None,
    )
    if local_task is None:
        return ControlCenterProofRecord(
            proof_ref="proof-ref:local-task-commit:not-yet-recorded",
            proof_kind="local_task_commit",
            status="blocked_no_local_task_commit_record",
            title="Local Task Commit",
            safe_summary="No local task commit receipt is present in the current proof index.",
            authority_posture="Local task commit remains unavailable until exact backend approval and receipt evidence exist.",
            route_refs=["route-ref:control-center:actions"],
            backend_route_refs=["POST /control-center/actions/{action_id}/local-task/commit"],
            run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
            evidence_refs=["evidence-ref:proof:local-task-commit:not-yet-recorded"],
            blocked_authority_refs=[
                *_COMMON_BLOCKED_AUTHORITY_REFS,
                "blocked-state:proof-detail:local-task-commit-not-recorded",
            ],
            next_safe_action="Approve and commit only through the Action Inbox exact local task route when eligible.",
        )
    source_ref = _first_ref(local_task.get("item_ref"), fallback="local-task:missing")
    receipt_refs = _refs(local_task.get("receipt_refs"))
    local_task_commit_receipt_refs = [
        ref for ref in receipt_refs if ref.startswith("receipt:founder-loop-local-task:")
    ]
    local_task_commit_receipt_ref = local_task.get("local_task_commit_receipt_ref")
    if (
        isinstance(local_task_commit_receipt_ref, str)
        and local_task_commit_receipt_ref.startswith(
            "receipt:founder-loop-local-task:"
        )
    ):
        local_task_commit_receipt_refs.append(local_task_commit_receipt_ref)
    if not local_task_commit_receipt_refs:
        return ControlCenterProofRecord(
            proof_ref=_derived_proof_ref("local-task-commit", source_ref),
            proof_kind="local_task_commit",
            status="blocked_no_local_task_commit_receipt",
            title="Local Task Commit",
            safe_summary=(
                "A local-task action is visible, but no local-task commit "
                "receipt ref exists yet."
            ),
            authority_posture=(
                "Action visibility and approval posture do not prove local "
                "task mutation until the exact local-task commit receipt exists."
            ),
            route_refs=["route-ref:control-center:actions"],
            backend_route_refs=[
                "POST /control-center/actions/{action_id}/local-task/commit"
            ],
            run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
            receipt_refs=receipt_refs,
            evidence_refs=_refs(local_task.get("evidence_refs")),
            approval_refs=_refs([local_task.get("approval_envelope_ref")]),
            rollback_refs=_refs([local_task.get("rollback_ref")]),
            safe_disable_refs=_refs([local_task.get("safe_disable_ref")]),
            blocked_authority_refs=[
                *_COMMON_BLOCKED_AUTHORITY_REFS,
                "blocked-state:proof-detail:local-task-commit-receipt-missing",
            ],
            next_safe_action=(
                "Commit only through the Action Inbox exact local task route "
                "when eligible, then inspect the receipt ref."
            ),
        )
    return ControlCenterProofRecord(
        proof_ref=_derived_proof_ref("local-task-commit", source_ref),
        proof_kind="local_task_commit",
        status=str(local_task.get("status") or "receipt_available"),
        title="Local Task Commit",
        safe_summary=str(
            local_task.get("safe_summary")
            or "Local task commit proof is represented by receipt refs."
        ),
        authority_posture="Local task proof is local-only and does not grant generic action execution.",
        route_refs=["route-ref:control-center:actions"],
        backend_route_refs=["POST /control-center/actions/{action_id}/local-task/commit"],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        receipt_refs=receipt_refs,
        evidence_refs=_refs(local_task.get("evidence_refs")),
        approval_refs=_refs([local_task.get("approval_envelope_ref")]),
        rollback_refs=_refs([local_task.get("rollback_ref")]),
        safe_disable_refs=_refs([local_task.get("safe_disable_ref")]),
        blocked_authority_refs=list(_COMMON_BLOCKED_AUTHORITY_REFS),
        next_safe_action="Inspect receipt and evidence refs before claiming the local task outcome.",
    )


def _memory_decision_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    memory = _dict(today_summary.get("memory_review"))
    candidates = _list_of_dicts(
        today_summary.get("memory_review_queue")
        or memory.get("items")
        or memory.get("candidates")
    )
    candidate = candidates[0] if candidates else {}
    source_ref = _first_ref(
        candidate.get("business_memory_candidate_ref"),
        candidate.get("candidate_ref"),
        candidate.get("memory_candidate_ref"),
        candidate.get("review_ref"),
        fallback="memory-candidate:not-selected",
    )
    return ControlCenterProofRecord(
        proof_ref=_derived_proof_ref("memory-decision", source_ref),
        proof_kind="memory_decision",
        status=str(candidate.get("status") or "review_available_or_explicit_none"),
        title="Memory Decision",
        safe_summary=str(
            candidate.get("safe_summary")
            or "Memory proof links reviewed candidates by safe refs only."
        ),
        authority_posture=(
            "Memory decision proof does not make memory recall truth and does "
            "not inject context into a model."
        ),
        route_refs=["route-ref:control-center:memory"],
        backend_route_refs=[
            "GET /control-center/memory/review",
            "GET /control-center/memory/review/{candidate_ref}/receipt",
        ],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        receipt_refs=_merge_refs(
            _refs(candidate.get("receipt_refs")),
            _refs(candidate.get("decision_receipt_refs")),
            _refs(today_summary.get("memory_review_decision_receipt_refs")),
        ),
        evidence_refs=_refs(candidate.get("evidence_refs"))
        or ["evidence-ref:proof:memory-decision"],
        approval_refs=_refs(candidate.get("approval_refs")),
        memory_candidate_refs=_refs([source_ref]),
        blocked_authority_refs=[
            *_COMMON_BLOCKED_AUTHORITY_REFS,
            "blocked-state:proof-detail:no-automatic-memory-write",
            "blocked-state:proof-detail:no-context-injection",
        ],
        next_safe_action="Review memory receipts and citations before relying on recall.",
    )


def _evidence_event_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    binding = _dict(today_summary.get("evidence_memory_loop_binding_read_model"))
    events = _list_of_dicts(binding.get("evidence_bindings"))
    timeline = _list_of_dicts(today_summary.get("evidence_timeline"))
    event = events[0] if events else (timeline[0] if timeline else {})
    source_ref = _first_ref(
        event.get("event_ref"),
        event.get("timeline_item_ref"),
        event.get("evidence_ref"),
        fallback="evidence-event:daily-loop",
    )
    return ControlCenterProofRecord(
        proof_ref=_derived_proof_ref("evidence-event", source_ref),
        proof_kind="evidence_event",
        status=str(event.get("status") or "evidence_refs_available"),
        title="Evidence Event",
        safe_summary=str(
            event.get("safe_summary")
            or "Evidence proof records local timeline refs without raw payloads."
        ),
        authority_posture="Evidence proof is read-only and does not execute or mutate sources.",
        route_refs=["route-ref:control-center:evidence"],
        backend_route_refs=["GET /control-center/evidence/timeline"],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        receipt_refs=_refs(event.get("receipt_refs")),
        evidence_refs=_merge_refs(
            _refs(event.get("evidence_refs")),
            _refs([source_ref, *_refs(today_summary.get("evidence_refs"))]),
        ),
        approval_refs=_refs(event.get("approval_refs")),
        audit_refs=_refs(event.get("audit_refs")),
        blocked_authority_refs=list(_COMMON_BLOCKED_AUTHORITY_REFS),
        next_safe_action="Inspect linked receipts and blocked authority refs.",
    )


def _web_evidence_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    attachment_refs = _refs(today_summary.get("web_evidence_attachment_refs"))
    receipt_refs = _refs(today_summary.get("web_evidence_receipt_refs"))
    evidence_refs = _refs(today_summary.get("web_evidence_evidence_refs"))
    audit_refs = _refs(today_summary.get("web_evidence_audit_refs"))
    preview_refs = _refs(today_summary.get("web_evidence_preview_refs"))
    host_refs = _refs(today_summary.get("web_evidence_host_refs"))
    web_access_request_refs = _refs(
        today_summary.get("web_evidence_web_access_request_refs")
    )
    status = str(
        today_summary.get("web_evidence_product_slice_status")
        or "implemented_route_ready_no_web_evidence_attached"
    )
    if receipt_refs:
        safe_summary = (
            "Web evidence proof shows allowlisted WebAccessGateway preview "
            "receipts as safe refs only; page text is omitted from proof."
        )
        next_safe_action = (
            "Inspect the receipt, preview, audit, and evidence refs before "
            "relying on the fetched source."
        )
    else:
        safe_summary = (
            "The web evidence product slice route is ready, but no local web "
            "evidence receipt has been attached yet."
        )
        next_safe_action = (
            "Attach one allowlisted HTTPS GET preview through the Evidence or "
            "Proof surface."
        )
    proof_evidence_refs = _merge_refs(
        evidence_refs,
        attachment_refs,
        preview_refs,
        host_refs,
        web_access_request_refs,
        ["evidence-ref:web-evidence-product-slice:route-ready"],
    )
    return ControlCenterProofRecord(
        proof_ref=WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
        proof_kind="web_evidence",
        status=status,
        title="Web Evidence",
        safe_summary=safe_summary,
        authority_posture=(
            "Tier 1 read-only web evidence preview through WebAccessGateway. "
            "No browser action, session state, download, upload, mutation "
            "method, context injection, memory write, provider call, connector "
            "write, or production authority is granted."
        ),
        route_refs=[
            "route-ref:control-center:evidence",
            "route-ref:control-center:proof",
        ],
        backend_route_refs=[
            WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
            "GET /control-center/evidence/timeline",
            CONTROL_CENTER_PROOF_INDEX_ROUTE_REF,
            CONTROL_CENTER_PROOF_DETAIL_ROUTE_REF,
        ],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        receipt_refs=receipt_refs,
        evidence_refs=proof_evidence_refs,
        audit_refs=audit_refs,
        approval_refs=["approval-status:web-evidence-tier-1-no-action-approval-required"],
        rollback_refs=["rollback:web-evidence-product-slice:suppress-local-receipt"],
        safe_disable_refs=["safe-disable:web-evidence-product-slice:env-and-route-off"],
        memory_candidate_refs=[],
        blocked_authority_refs=_merge_refs(
            list(_COMMON_BLOCKED_AUTHORITY_REFS),
            list(WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS),
        ),
        next_safe_action=next_safe_action,
    )


def _source_readiness_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    return ControlCenterProofRecord(
        proof_ref="proof-ref:source-readiness:read-model",
        proof_kind="source_readiness",
        status="read_only_source_posture",
        title="Source Readiness",
        safe_summary="Source readiness proof explains connector/source posture as refs and labels only.",
        authority_posture="Source readiness proof does not sync accounts or read connector content.",
        route_refs=["route-ref:control-center:inbox"],
        backend_route_refs=["GET /control-center/sources/readiness"],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        evidence_refs=_refs(today_summary.get("evidence_refs"))
        or ["evidence-ref:proof:source-readiness"],
        blocked_authority_refs=[
            *_COMMON_BLOCKED_AUTHORITY_REFS,
            "blocked-state:proof-detail:no-account-sync",
            "blocked-state:proof-detail:no-connector-read-runtime",
        ],
        next_safe_action="Use source readiness as planning context only.",
    )


def _approval_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    actions = _list_of_dicts(today_summary.get("actions"))
    approval_refs = _merge_refs(
        *(
            _refs([action.get("approval_envelope_ref")])
            for action in _actions_for_proof_index(actions)
        )
    )
    return ControlCenterProofRecord(
        proof_ref="proof-ref:approval-review:queue",
        proof_kind="approval",
        status="approval_refs_are_identifiers_only",
        title="Approval Review",
        safe_summary="Approval proof collects approval refs for review without granting authority.",
        authority_posture="Approval refs are identifiers until exact LocalApprovalAuthority scope validates.",
        route_refs=["route-ref:control-center:approvals"],
        backend_route_refs=["GET /control-center/approvals/queue"],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        approval_refs=approval_refs or ["approval-ref:proof:no-pending-approval"],
        evidence_refs=["evidence-ref:proof:approval-review"],
        blocked_authority_refs=[
            *_COMMON_BLOCKED_AUTHORITY_REFS,
            "blocked-state:proof-detail:approval-ref-not-authority",
        ],
        next_safe_action="Inspect approval scope and receipt refs in Action Inbox before mutation.",
    )


def _setup_package_record(today_summary: dict[str, Any]) -> ControlCenterProofRecord:
    return ControlCenterProofRecord(
        proof_ref="proof-ref:setup-package:local-only",
        proof_kind="setup_package",
        status="local_setup_package_proof_review_only",
        title="Setup And Package Proof",
        safe_summary="Setup/package proof is local-only review posture and does not claim distribution readiness.",
        authority_posture="No signed installer, notarization, LaunchAgent, daemon, auto-update, public release, or production authority is granted.",
        route_refs=["route-ref:control-center:setup"],
        backend_route_refs=["GET /control-center/setup-assistant/summary"],
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        evidence_refs=_refs(today_summary.get("evidence_refs"))
        or ["evidence-ref:proof:setup-package"],
        rollback_refs=["rollback-plan:setup-package:local-only"],
        safe_disable_refs=["safe-disable:setup-package:local-only"],
        blocked_authority_refs=[
            *_COMMON_BLOCKED_AUTHORITY_REFS,
            "blocked-state:proof-detail:no-signed-installer",
            "blocked-state:proof-detail:no-public-distribution",
        ],
        next_safe_action="Inspect local setup posture without launching installer or package work.",
    )


def _dedupe_records(
    records: list[ControlCenterProofRecord],
) -> list[ControlCenterProofRecord]:
    result: list[ControlCenterProofRecord] = []
    seen: set[str] = set()
    for record in records:
        if record.proof_ref in seen:
            continue
        seen.add(record.proof_ref)
        result.append(record)
    return result


def _attach_run_details(
    records: list[ControlCenterProofRecord],
) -> list[ControlCenterProofRecord]:
    return [_with_run_detail(record) for record in records]


def _with_run_detail(record: ControlCenterProofRecord) -> ControlCenterProofRecord:
    run_ref = (
        record.run_refs[0]
        if record.run_refs
        else FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    )
    run_refs = _merge_refs(record.run_refs, [run_ref])
    run_detail = ControlCenterProofRunDetail(
        run_detail_ref=_run_detail_ref(record.proof_ref),
        proof_ref=record.proof_ref,
        proof_kind=record.proof_kind,
        run_ref=run_ref,
        status=record.status,
        title=record.title,
        safe_summary=(
            f"Run Detail for {record.title} ties proof, run, receipt, "
            "evidence, approval, rollback, safe-disable, memory, and blocked "
            "authority refs without raw payloads."
        ),
        authority_posture=record.authority_posture,
        exact_promotion_path_refs=_promotion_path_refs_for_kind(record.proof_kind),
        route_refs=record.route_refs,
        backend_route_refs=_merge_text_refs(
            record.backend_route_refs,
            [record.detail_route_ref],
        ),
        related_run_refs=_merge_refs(record.run_refs, [run_ref]),
        operator_run_event_refs=[
            _operator_run_event_ref(record.proof_ref, record.proof_kind)
        ],
        receipt_refs=record.receipt_refs,
        evidence_refs=record.evidence_refs,
        audit_refs=record.audit_refs,
        approval_refs=record.approval_refs,
        rollback_refs=record.rollback_refs,
        safe_disable_refs=record.safe_disable_refs,
        memory_candidate_refs=record.memory_candidate_refs,
        blocked_authority_refs=record.blocked_authority_refs,
        next_safe_action=record.next_safe_action,
    )
    data = record.model_dump()
    data["run_refs"] = run_refs
    data["run_detail"] = run_detail
    return ControlCenterProofRecord.model_validate(data)


def _run_detail_ref(proof_ref: str) -> str:
    suffix = _safe_hashed_suffix(proof_ref, limit=72)
    ref = f"run-detail-ref:control-center-proof:{suffix}"
    validate_execution_ref(ref, "run_detail_ref")
    return ref


def _operator_run_event_ref(proof_ref: str, proof_kind: ProofKind) -> str:
    suffix = _safe_hashed_suffix(proof_ref, limit=56)
    kind = str(proof_kind).replace("_", "-")
    ref = f"operator-run-event-ref:proof:{kind}:{suffix}"
    validate_execution_ref(ref, "operator_run_event_ref")
    return ref


def _safe_hashed_suffix(value: str, *, limit: int) -> str:
    safe = _SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-")[:limit].strip("-")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{safe or 'missing'}-sha256-{digest}"


def _promotion_path_refs_for_kind(proof_kind: ProofKind) -> list[str]:
    kind = str(proof_kind).replace("_", "-")
    return [
        "promotion-path-ref:proof-run-spine:detail-route-parity",
        "promotion-path-ref:proof-run-spine:receipt-evidence-binding",
        "promotion-path-ref:proof-run-spine:rollback-safe-disable-binding",
        "promotion-path-ref:proof-run-spine:cli-inspection-parity",
        f"promotion-path-ref:proof-run-spine:{kind}",
    ]


def _actions_for_proof_index(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = list(actions[:6])
    next_action = _next_action_for_proof(actions)
    if next_action is not None and all(
        _action_identity(action) != _action_identity(next_action)
        for action in selected
    ):
        selected.append(next_action)
    return selected


def _next_action_for_proof(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for group_id in _ACTION_PROOF_NEXT_ITEM_GROUP_ORDER:
        for action in actions:
            if str(action.get("action_group_id") or "") == group_id:
                return action
    return actions[0] if actions else None


def _action_identity(action: dict[str, Any]) -> str:
    return str(
        action.get("action_envelope_ref")
        or action.get("item_ref")
        or action.get("title")
        or id(action)
    )


def _derived_proof_ref(kind: str, source_ref: str) -> str:
    slug = _SAFE_SUFFIX_RE.sub("-", source_ref.lower()).strip("-")[:80]
    candidate = f"proof-ref:{kind}:{slug or 'missing'}"
    try:
        validate_execution_ref(candidate, "proof_ref")
        return candidate
    except ValueError:
        digest = hashlib.sha256(source_ref.encode("utf-8")).hexdigest()[:24]
        ref = f"proof-ref:{kind}:sha256:{digest}"
        validate_execution_ref(ref, "proof_ref")
        return ref


def _first_ref(*values: Any, fallback: str) -> str:
    for value in values:
        if isinstance(value, str) and value:
            try:
                validate_execution_ref(value, "ref")
                return value
            except ValueError:
                digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
                ref = f"external-ref:sha256:{digest}"
                validate_execution_ref(ref, "ref")
                return ref
    validate_execution_ref(fallback, "ref")
    return fallback


def _refs(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    refs: list[str] = []
    for item in values:
        if not isinstance(item, str) or not item:
            continue
        validate_execution_ref(item, "ref")
        refs.append(item)
    return _unique_refs(refs)


def _merge_refs(*groups: Any) -> list[str]:
    refs: list[str] = []
    for group in groups:
        refs.extend(_refs(group))
    return _unique_refs(refs)


def _merge_text_refs(*groups: list[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            if value in seen:
                continue
            validate_safe_execution_text(value, "text_ref")
            seen.add(value)
            values.append(value)
    return values


def _unique_refs(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        validate_execution_ref(value, "ref")
        seen.add(value)
        result.append(value)
    return result


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)


def _validate_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_safe_execution_text(value, field_name)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_title(value: str) -> str:
    validate_safe_execution_text(value, "title")
    return value[:160] or "Proof Record"
