import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_router.enums import ModelRouteStatus
from ultimate_ai_agent.core.approvals import ApprovalValidationRequest
from ultimate_ai_agent.core.time import utc_now


def build_approval_validation_decision_ref(
    validation_request: ApprovalValidationRequest,
    decision: BaseModel,
) -> str:
    payload = {
        "validation_request": validation_request.model_dump(
            mode="json",
            exclude={"current_time"},
        ),
        "decision": decision.model_dump(
            mode="json",
            exclude={"decision_id", "created_at"},
        ),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"approval-validation-decision-ref:sha256:{digest}"


class ModelRouteDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"mroute_{uuid.uuid4().hex[:12]}")
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    status: ModelRouteStatus
    selected_profile_id: Optional[str] = None
    selected_model_id: Optional[str] = None
    candidate_profile_ids: List[str] = Field(default_factory=list)
    rejected_profile_ids: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    estimated_cost: Optional[float] = Field(None, ge=0)
    estimated_latency_ms: Optional[float] = Field(None, ge=0)
    cost_mode: Optional[str] = None
    fallback_plan_ref: Optional[str] = None
    fallback_used: bool = False
    verification_required: bool = False
    verification_route_id: Optional[str] = None
    eval_result_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    privacy_notes: List[str] = Field(default_factory=list)
    required_approval: bool = False
    approval_validation_decision_ref: Optional[str] = None
    consent_refs: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_approval_evidence(self) -> "ModelRouteDecision":
        approval_validated = "APPROVAL_VALIDATED" in self.reason_codes
        if approval_validated != (self.approval_validation_decision_ref is not None):
            raise ValueError("MODEL_ROUTE_APPROVAL_EVIDENCE_DRIFT")
        if (
            self.approval_validation_decision_ref is not None
            and re.fullmatch(
                r"approval-validation-decision-ref:sha256:[a-f0-9]{64}",
                self.approval_validation_decision_ref,
            )
            is None
        ):
            raise ValueError("MODEL_ROUTE_APPROVAL_EVIDENCE_REF_INVALID")
        if approval_validated and self.status != ModelRouteStatus.selected.value:
            raise ValueError("MODEL_ROUTE_APPROVAL_EVIDENCE_STATUS_INVALID")
        return self


def build_model_route_decision_ref(decision: ModelRouteDecision) -> str:
    """Bind runtime evidence to the deterministic content of a route decision."""

    payload = decision.model_dump(
        mode="json",
        exclude={"decision_id", "created_at"},
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"model-route-decision-ref:sha256:{digest}"
