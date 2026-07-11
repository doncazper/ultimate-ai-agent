from __future__ import annotations

from enum import Enum
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MissionControlEvent,
    MissionControlReceipt,
    MissionControlRequest,
    MissionControlStore,
)
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_approval_scope_fingerprint,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text


MISSION_FAILURE_MANAGEMENT_REDACTIONS = [
    "safe_refs_only",
    "raw_task_inputs_omitted",
    "raw_paths_omitted",
    "raw_logs_omitted",
    "raw_provider_payloads_omitted",
    "credentials_omitted",
]


class MissionFailureManagementResult(BaseModel):
    event: MissionControlEvent
    status: Literal["recorded"] = "recorded"
    control_receipt_ref: str
    control_entry_hash_ref: str
    request_fingerprint_ref: str
    execution_authority_granted: Literal[False] = False
    execution_performed: Literal[False] = False
    adapter_invocation_performed: Literal[False] = False
    original_dead_letter_reopened: Literal[False] = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(MISSION_FAILURE_MANAGEMENT_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class MissionApprovalDecision(str, Enum):
    approve = "approve"
    deny = "deny"


class MissionApprovalDecisionRequest(BaseModel):
    step_ref: str
    approval_request_ref: str
    approval_ref: str
    approval_scope_fingerprint_ref: str
    approval_validation_request: ApprovalValidationRequest
    decision: MissionApprovalDecision
    operator_ref: str
    idempotency_ref: str
    reason_ref: str
    safe_summary: str

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    def model_post_init(self, _context: object) -> None:
        for value, field_name in [
            (self.step_ref, "mission_approval_step_ref"),
            (self.approval_request_ref, "mission_approval_request_ref"),
            (self.approval_ref, "mission_approval_ref"),
            (
                self.approval_scope_fingerprint_ref,
                "mission_approval_scope_fingerprint_ref",
            ),
            (self.operator_ref, "mission_approval_operator_ref"),
            (self.idempotency_ref, "mission_approval_idempotency_ref"),
            (self.reason_ref, "mission_approval_reason_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "mission_approval_safe_summary")
        if self.approval_validation_request.current_time is not None:
            raise ValueError("MISSION_APPROVAL_CALLER_TIME_FORBIDDEN")
        if self.approval_validation_request.approval_ref != self.approval_ref:
            raise ValueError("MISSION_APPROVAL_VALIDATION_REF_MISMATCH")

    @property
    def fingerprint_ref(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        return (
            "approval-validation-ref:mission-decision:sha256:"
            f"{hash_text(payload)[:24]}"
        )


class MissionApprovalDecisionResult(BaseModel):
    status: Literal["recorded"] = "recorded"
    decision: MissionApprovalDecision
    step_ref: str
    control_receipt_ref: str
    control_entry_hash_ref: str
    decision_fingerprint_ref: str
    execution_authority_granted: Literal[False] = False
    execution_performed: Literal[False] = False
    adapter_invocation_performed: Literal[False] = False
    fresh_dispatch_evaluation_required: Literal[True] = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(MISSION_FAILURE_MANAGEMENT_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")


class AuthorityMissionFailureManagementService:
    """Shared API/CLI service for exact authority-reducing mission controls."""

    def __init__(
        self,
        state_dir: Path | None = None,
    ) -> None:
        self.state_dir = state_dir or authority_state_dir()
        dispatcher = AuthorityDispatcher(self.state_dir, adapters=[])
        step_store = MissionStepStore(self.state_dir)
        self.orchestrator = SynchronousAuthorityMissionOrchestrator(
            runner=AuthorityMissionRunner(
                dispatcher=dispatcher,
                step_store=step_store,
            ),
            plan_store=DurableMissionPlanStore(self.state_dir),
            control_store=MissionControlStore(self.state_dir),
        )
        self.control_store = self.orchestrator.control_store

    def cancel(
        self,
        request: MissionControlRequest,
    ) -> MissionFailureManagementResult:
        if request.event != MissionControlEvent.cancellation_requested.value:
            raise ValueError("MISSION_FAILURE_MANAGEMENT_CANCELLATION_REQUIRED")
        return self._result(self.control_store.append(request))

    def request_dead_letter_recovery(
        self,
        request: MissionControlRequest,
    ) -> MissionFailureManagementResult:
        if request.event != MissionControlEvent.dead_letter_recovery_requested.value:
            raise ValueError("MISSION_FAILURE_MANAGEMENT_DEAD_LETTER_REQUIRED")
        return self._result(self.control_store.append(request))

    def resolve_approval(
        self,
        request: MissionApprovalDecisionRequest,
    ) -> MissionApprovalDecisionResult:
        validated = MissionApprovalDecisionRequest.model_validate(
            request.model_dump(mode="python")
        )
        receipts = self.orchestrator.step_store.receipts()
        waiting = next(
            (
                receipt
                for receipt in reversed(receipts)
                if receipt.definition.step_ref == validated.step_ref
            ),
            None,
        )
        if waiting is None or waiting.status != MissionStepStatus.approval_wait.value:
            raise MissionStepConflictError("MISSION_APPROVAL_WAIT_REQUIRED")
        if (
            waiting.approval_request_ref != validated.approval_request_ref
            or waiting.approval_ref != validated.approval_ref
            or waiting.approval_scope_fingerprint_ref
            != validated.approval_scope_fingerprint_ref
            or mission_step_approval_scope_fingerprint(
                validated.approval_validation_request
            )
            != validated.approval_scope_fingerprint_ref
        ):
            raise MissionStepConflictError("MISSION_APPROVAL_SCOPE_MISMATCH")
        plan_ref = waiting.definition.orchestration_plan_ref
        if plan_ref is None:
            raise MissionStepConflictError("MISSION_APPROVAL_PLAN_BINDING_REQUIRED")
        plan_receipts = [
            receipt
            for receipt in self.orchestrator.plan_store.list_receipts()
            if receipt.plan.plan_ref == plan_ref
        ]
        if len(plan_receipts) != 1:
            raise MissionStepConflictError("MISSION_APPROVAL_PLAN_BINDING_REQUIRED")
        plan_receipt = plan_receipts[0]
        control = MissionControlRequest(
            control_ref=(
                "mission-control-ref:approval-decision:"
                f"{hash_text(validated.step_ref)[:24]}"
            ),
            event=MissionControlEvent.approval_decision_recorded,
            plan_ref=plan_ref,
            plan_fingerprint_ref=plan_receipt.plan_fingerprint_ref,
            mission_ref=waiting.definition.mission_ref,
            run_ref=waiting.definition.run_ref,
            lease_ref=waiting.definition.lease_ref,
            idempotency_ref=validated.idempotency_ref,
            reason_ref=validated.reason_ref,
            approval_step_ref=validated.step_ref,
            approval_request_ref=validated.approval_request_ref,
            approval_ref=validated.approval_ref,
            approval_scope_fingerprint_ref=(
                validated.approval_scope_fingerprint_ref
            ),
            approval_decision=validated.decision,
            approval_decision_fingerprint_ref=validated.fingerprint_ref,
            operator_ref=validated.operator_ref,
            safe_summary=validated.safe_summary,
        )
        receipt = self.control_store.append(control)
        return MissionApprovalDecisionResult(
            decision=validated.decision,
            step_ref=validated.step_ref,
            control_receipt_ref=receipt.receipt_ref,
            control_entry_hash_ref=receipt.entry_hash_ref,
            decision_fingerprint_ref=validated.fingerprint_ref,
        )

    @staticmethod
    def _result(receipt: MissionControlReceipt) -> MissionFailureManagementResult:
        return MissionFailureManagementResult(
            event=receipt.request.event,
            control_receipt_ref=receipt.receipt_ref,
            control_entry_hash_ref=receipt.entry_hash_ref,
            request_fingerprint_ref=receipt.request_fingerprint_ref,
        )
