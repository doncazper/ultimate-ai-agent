from __future__ import annotations

import hashlib
import json
import re
from datetime import timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.time import utc_now


FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF = (
    "contract-ref:founder-loop-local-task-commit:v1"
)
FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF = (
    "POST /control-center/actions/{action_id}/local-task/commit"
)
FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND = "local_task_create"
FOUNDER_LOOP_LOCAL_TASK_COMMIT_STATUS = "local_task_created"
FOUNDER_LOOP_LOCAL_TASK_COMMIT_REQUESTED_ACTION = (
    "commit_founder_loop_local_task"
)
FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS = (
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-external-side-effect",
    "blocked-state:no-production-authority",
)
SAFE_LOCAL_TASK_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")


def _default_actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_operator",
        authority_source=AuthoritySource.explicit_user_request,
    )


class FounderLoopLocalTaskCommitRequest(BaseModel):
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    approval_ref: str = Field(..., min_length=1, max_length=160)
    approval_grants: list[ApprovalGrant] = Field(default_factory=list)
    decision_reason_ref: str = Field(
        default="decision-reason-ref:founder-loop:local-task-commit",
        min_length=1,
        max_length=160,
    )
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_safe_refs(self) -> "FounderLoopLocalTaskCommitRequest":
        _validate_safe_ref(self.approval_ref, "approval_ref")
        _validate_safe_ref(self.decision_reason_ref, "decision_reason_ref")
        for ref_value in self.metadata_refs:
            _validate_safe_ref(ref_value, "metadata_refs")
        _validate_safe_payload(self.model_dump(mode="json"), "local_task_commit_request")
        return self


class FounderLoopLocalTaskCommitReceipt(BaseModel):
    contract_ref: str = FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
    item_ref: str = Field(..., min_length=1)
    action_kind: Literal["local_task_create"] = FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    local_task_ref: str = Field(..., min_length=1)
    status: str = Field(
        default=FOUNDER_LOOP_LOCAL_TASK_COMMIT_STATUS,
        min_length=1,
        max_length=80,
    )
    receipt_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    evidence_timeline_event_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1, max_length=160)
    approval_status: str = Field(..., min_length=1, max_length=80)
    approval_reason_refs: list[str] = Field(default_factory=list)
    local_task_created: bool = True
    connector_write_performed: bool = False
    shell_subprocess_execution_performed: bool = False
    model_provider_authority_used: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    external_side_effect_performed: bool = False
    raw_content_stored: bool = False
    replayed: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=320)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "FounderLoopLocalTaskCommitReceipt":
        for field_name in [
            "contract_ref",
            "item_ref",
            "local_task_ref",
            "receipt_ref",
            "audit_ref",
            "idempotency_key_ref",
            "payload_fingerprint_ref",
            "evidence_timeline_event_ref",
            "approval_ref",
        ]:
            _validate_safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "approval_reason_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        denied_flags = {
            "connector_write_performed": self.connector_write_performed,
            "shell_subprocess_execution_performed": self.shell_subprocess_execution_performed,
            "model_provider_authority_used": self.model_provider_authority_used,
            "memory_write_performed": self.memory_write_performed,
            "context_injection_performed": self.context_injection_performed,
            "external_side_effect_performed": self.external_side_effect_performed,
            "raw_content_stored": self.raw_content_stored,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"local task receipt enabled denied authority: {enabled[0]}")
        if not set(FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS).issubset(
            set(self.blocked_state_refs)
        ):
            raise ValueError("local task receipt must preserve blocked external authority refs")
        _validate_safe_payload(self.model_dump(mode="json"), "local_task_commit_receipt")
        return self


def local_task_ref_for_action(item_ref: str) -> str:
    _validate_safe_ref(item_ref, "item_ref")
    return f"local-task:founder-loop:{_safe_suffix(item_ref)}"


def local_task_commit_receipt_ref(item_ref: str, idempotency_key_ref: str) -> str:
    return (
        "receipt:founder-loop-local-task:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
    )


def local_task_commit_audit_ref(item_ref: str, idempotency_key_ref: str) -> str:
    return (
        "audit:founder-loop-local-task:"
        f"{_safe_suffix(item_ref)}:{_safe_suffix(idempotency_key_ref)}"
    )


def local_task_commit_event_ref(item_ref: str) -> str:
    return f"evidence-timeline:local-task/{_safe_suffix(item_ref)}"


def local_task_commit_payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"payload-fingerprint:founder-loop-local-task:{digest}"


def local_task_commit_payload_for_fingerprint(
    *,
    item_ref: str,
    request: FounderLoopLocalTaskCommitRequest,
) -> dict[str, Any]:
    return {
        "contract_ref": FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
        "item_ref": item_ref,
        "action_kind": FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
        "actor_id": request.actor_context.actor_id,
        "approval_ref": request.approval_ref,
        "decision_reason_ref": request.decision_reason_ref,
        "metadata_refs": sorted(request.metadata_refs),
    }


def local_task_commit_approval_request(
    *,
    item_ref: str,
    actor_context: ActorContext,
    risk_class: str,
    resource_refs: list[str],
) -> ApprovalRequest:
    _validate_safe_ref(item_ref, "item_ref")
    for ref_value in resource_refs:
        _validate_safe_ref(ref_value, "resource_refs")
    risk_values = {item.value for item in ApprovalRiskLevel}
    risk_level = (
        ApprovalRiskLevel(risk_class)
        if risk_class in risk_values
        else ApprovalRiskLevel.medium
    )
    return ApprovalRequest(
        approval_request_id=f"approval-request:local-task:{_safe_suffix(item_ref)}",
        run_id=f"run:founder-loop-local-task:{_safe_suffix(item_ref)}",
        subject_type=ApprovalSubjectType.external_action,
        subject_id=item_ref,
        actor_context=actor_context,
        requested_action=FOUNDER_LOOP_LOCAL_TASK_COMMIT_REQUESTED_ACTION,
        purpose="Commit an exact-scoped Founder Loop local task from an approved Action Inbox item.",
        risk_level=risk_level,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="founder_loop_local_task_commit",
            requires_redaction=True,
        ),
        resource_refs=resource_refs,
        event_ref=f"event-ref:founder-loop-local-task:{_safe_suffix(item_ref)}",
        trace_id=f"trace-ref:founder-loop-local-task:{_safe_suffix(item_ref)}",
        expires_at=utc_now() + timedelta(hours=1),
    )


def _safe_suffix(value: str) -> str:
    suffix = SAFE_LOCAL_TASK_SUFFIX_CHARS.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_safe_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_safe_text(str(key), field_name)
            _validate_safe_payload(item, field_name)
