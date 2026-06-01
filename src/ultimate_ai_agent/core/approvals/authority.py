import uuid
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationDecision, ApprovalValidationRequest
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalDecisionStatus,
    ApprovalMode,
    ApprovalRiskLevel,
    ApprovalStatus,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.grants import ApprovalGrant
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.approvals.validation import refs_subset, risk_value
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.time import utc_now


class LocalApprovalAuthority:
    def __init__(self, mode: ApprovalMode = ApprovalMode.local_dev):
        self.mode = mode
        self._requests: dict[str, ApprovalRequest] = {}
        self._grants: dict[str, ApprovalGrant] = {}

    def create_request(self, request: ApprovalRequest) -> ApprovalRequest:
        self._requests[request.approval_request_id] = request
        return request

    def grant(
        self,
        request_id: str,
        approved_by_actor_id: str,
        expires_at: Optional[datetime] = None,
        approved_actions: Optional[list[str]] = None,
        approved_resource_refs: Optional[list[str]] = None,
        approval_ref: Optional[str] = None,
    ) -> ApprovalGrant:
        request = self._requests[request_id]
        requested_actions = [request.requested_action]
        requested_refs = request.resource_refs
        actions = [action for action in (approved_actions or requested_actions) if action in requested_actions]
        refs = [ref for ref in (approved_resource_refs or requested_refs) if ref in requested_refs]
        grant = ApprovalGrant(
            approval_ref=approval_ref or f"appr_{uuid.uuid4().hex[:16]}",
            approval_request_id=request.approval_request_id,
            run_id=request.run_id,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            granted_to_actor_id=request.actor_context.actor_id,
            approved_by_actor_id=approved_by_actor_id,
            approved_actions=actions or requested_actions,
            approved_resource_refs=refs,
            risk_level=request.risk_level,
            data_classification=request.data_classification,
            purpose=request.purpose,
            status=ApprovalStatus.granted,
            created_at=utc_now(),
            expires_at=expires_at or request.expires_at or (utc_now() + timedelta(hours=1)),
            event_ref=request.event_ref,
            trace_id=request.trace_id,
            metadata={"approval_mode": self.mode.value},
        )
        self._grants[grant.approval_ref] = grant
        return grant

    def create_test_grant(self, request_id: str, approval_ref: str = "approval_test_local_dev") -> ApprovalGrant:
        return self.grant(request_id, approved_by_actor_id="local_test_fixture", approval_ref=approval_ref)

    def deny(self, request_id: str, denied_by_actor_id: str, reason: str) -> ApprovalValidationDecision:
        request = self._requests[request_id]
        return ApprovalValidationDecision(
            approval_ref=None,
            allowed=False,
            status=ApprovalDecisionStatus.denied,
            reason_codes=["APPROVAL_DENIED"],
            safe_message=f"Approval denied by {denied_by_actor_id}: {reason}",
            event_ref=request.event_ref,
        )

    def revoke(self, approval_ref: str, reason: str) -> ApprovalGrant:
        grant = self._grants[approval_ref]
        revoked = grant.model_copy(
            update={
                "status": ApprovalStatus.revoked,
                "revoked_at": utc_now(),
                "metadata": {**grant.metadata, "revocation_reason": reason},
            }
        )
        self._grants[approval_ref] = revoked
        return revoked

    def validate_for_request(self, request: ApprovalRequest, approval_ref: str) -> ApprovalValidationDecision:
        return self.validate(request.to_validation_request(approval_ref))

    def validate(self, validation_request: ApprovalValidationRequest) -> ApprovalValidationDecision:
        ref = validation_request.approval_ref
        grant = self._grants.get(ref)
        if grant is None:
            return self._decision(validation_request, ApprovalDecisionStatus.invalid, ["APPROVAL_REF_UNKNOWN"], "Approval ref is unknown to the local approval authority.")
        now = validation_request.current_time or utc_now()
        if grant.status == ApprovalStatus.revoked:
            return self._decision(validation_request, ApprovalDecisionStatus.revoked, ["APPROVAL_REVOKED"], "Approval grant has been revoked.", grant)
        if grant.status == ApprovalStatus.expired or (grant.expires_at is not None and grant.expires_at <= now):
            return self._decision(validation_request, ApprovalDecisionStatus.expired, ["APPROVAL_EXPIRED"], "Approval grant has expired.", grant)
        if grant.status != ApprovalStatus.granted:
            return self._decision(validation_request, ApprovalDecisionStatus.denied, ["APPROVAL_NOT_GRANTED"], "Approval grant is not granted.", grant)
        scope_failures = self._scope_failures(validation_request, grant)
        if scope_failures:
            return self._decision(validation_request, ApprovalDecisionStatus.out_of_scope, scope_failures, "Approval grant does not cover the requested action.", grant)
        return self._decision(validation_request, ApprovalDecisionStatus.approved, ["APPROVAL_VALIDATED"], "Approval grant validated for the requested scope.", grant, allowed=True)

    def get_grant(self, approval_ref: str) -> Optional[ApprovalGrant]:
        return self._grants.get(approval_ref)

    def list_grants(self, run_id: str | None = None) -> List[ApprovalGrant]:
        grants = list(self._grants.values())
        if run_id is not None:
            grants = [grant for grant in grants if grant.run_id == run_id]
        return grants

    def _scope_failures(self, request: ApprovalValidationRequest, grant: ApprovalGrant) -> list[str]:
        failures: list[str] = []
        if grant.run_id != request.run_id:
            failures.append("APPROVAL_RUN_MISMATCH")
        if str(grant.subject_type) != str(request.subject_type) or grant.subject_id != request.subject_id:
            failures.append("APPROVAL_SUBJECT_MISMATCH")
        if grant.granted_to_actor_id != request.actor_context.actor_id:
            failures.append("APPROVAL_ACTOR_MISMATCH")
        if request.requested_action not in grant.approved_actions:
            failures.append("APPROVAL_ACTION_NOT_GRANTED")
        if not refs_subset(request.resource_refs, grant.approved_resource_refs):
            failures.append("APPROVAL_RESOURCE_NOT_GRANTED")
        if risk_value(request.risk_level) > risk_value(grant.risk_level) or risk_value(request.risk_level) < risk_value(grant.risk_level):
            failures.append("APPROVAL_RISK_MISMATCH")
        if str(request.data_classification.classification) != str(grant.data_classification.classification):
            failures.append("APPROVAL_DATA_CLASSIFICATION_MISMATCH")
        return failures

    def _decision(
        self,
        request: ApprovalValidationRequest,
        status: ApprovalDecisionStatus,
        reason_codes: list[str],
        safe_message: str,
        grant: ApprovalGrant | None = None,
        *,
        allowed: bool = False,
    ) -> ApprovalValidationDecision:
        return ApprovalValidationDecision(
            approval_ref=request.approval_ref,
            allowed=allowed,
            status=status,
            reason_codes=reason_codes,
            safe_message=safe_message,
            matched_grant_ref=grant.approval_ref if grant and allowed else None,
            required_next_action=None if allowed else "request_valid_local_dev_approval",
            event_ref=request.event_ref,
        )

    @staticmethod
    def request_for_model_route(
        route_request,
        *,
        subject_type: ApprovalSubjectType = ApprovalSubjectType.model_route,
        subject_id: str | None = None,
        requested_action: str = "route_cloud_model",
        resource_refs: list[str] | None = None,
        risk_level: ApprovalRiskLevel = ApprovalRiskLevel.high,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            approval_request_id=f"areq_{route_request.request_id}",
            run_id=route_request.run_id,
            subject_type=subject_type,
            subject_id=subject_id or route_request.request_id,
            actor_context=route_request.actor_context,
            requested_action=requested_action,
            purpose=f"Approve model route for {route_request.task_class}.",
            risk_level=risk_level,
            data_classification=route_request.data_classification,
            resource_refs=resource_refs or [],
            consent_refs=route_request.consent_refs,
            event_ref=route_request.event_ref,
            trace_id=route_request.request_id,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    @staticmethod
    def request_for_tool_request(
        tool_request,
        *,
        subject_type: ApprovalSubjectType = ApprovalSubjectType.tool_request,
        subject_id: str | None = None,
        resource_refs: list[str] | None = None,
        risk_level: ApprovalRiskLevel = ApprovalRiskLevel.high,
    ) -> ApprovalRequest:
        classification = DataClassification(
            classification=ClassificationValue(getattr(tool_request.data_classification, "value", str(tool_request.data_classification))),
            source="tool_request",
            requires_consent=True,
        )
        return ApprovalRequest(
            approval_request_id=f"areq_{tool_request.request_id}",
            run_id=tool_request.run_id,
            subject_type=subject_type,
            subject_id=subject_id or tool_request.request_id,
            actor_context=tool_request.actor_context,
            requested_action=tool_request.requested_action,
            purpose=tool_request.purpose,
            risk_level=risk_level,
            data_classification=classification,
            resource_refs=resource_refs or [tool_request.tool_id],
            tool_id=tool_request.tool_id,
            consent_refs=tool_request.consent_refs,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
