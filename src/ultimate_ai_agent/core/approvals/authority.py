import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from threading import RLock
from typing import Any, Iterator, List, Optional

from ultimate_ai_agent.core._compat import UTC
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
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityLease,
    AuthorityLeaseStatus,
    AuthorityPolicyDecision,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


def build_approval_revocation_reason_ref(reason: str) -> str:
    return f"approval-revocation-reason-ref:sha256:{hash_text(reason)[:24]}"


class LocalApprovalAuthority:
    def __init__(self, mode: ApprovalMode = ApprovalMode.local_dev) -> None:
        self.mode = mode
        self._requests: dict[str, ApprovalRequest] = {}
        self._grants: dict[str, ApprovalGrant] = {}
        self._authority_leases: dict[str, AuthorityLease] = {}
        self._validation_lock = RLock()

    @contextmanager
    def hold_validation_lock(self) -> Iterator[None]:
        """Serialize a validation decision with an external durable start claim."""

        with self._validation_lock:
            yield

    def create_request(self, request: ApprovalRequest) -> ApprovalRequest:
        stored = ApprovalRequest.model_validate(request.model_dump(mode="python"))
        with self._validation_lock:
            self._requests[stored.approval_request_id] = stored
        return stored.model_copy(deep=True)

    def grant(
        self,
        request_id: str,
        approved_by_actor_id: str,
        expires_at: Optional[datetime] = None,
        approved_actions: Optional[list[str]] = None,
        approved_resource_refs: Optional[list[str]] = None,
        approval_ref: Optional[str] = None,
    ) -> ApprovalGrant:
        with self._validation_lock:
            request = self._requests[request_id].model_copy(deep=True)
        requested_actions = [request.requested_action]
        requested_refs = list(request.resource_refs)
        if approved_actions is None:
            actions = requested_actions
        else:
            if not approved_actions or not set(approved_actions).issubset(requested_actions):
                raise ValueError("APPROVAL_ACTION_SCOPE_INVALID")
            actions = list(approved_actions)
        if approved_resource_refs is None:
            refs = requested_refs
        else:
            if not set(approved_resource_refs).issubset(requested_refs):
                raise ValueError("APPROVAL_RESOURCE_SCOPE_INVALID")
            refs = list(approved_resource_refs)
        grant = ApprovalGrant(
            approval_ref=approval_ref or f"appr_{uuid.uuid4().hex[:16]}",
            approval_request_id=request.approval_request_id,
            run_id=request.run_id,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            granted_to_actor_id=request.actor_context.actor_id,
            approved_by_actor_id=approved_by_actor_id,
            approved_actions=actions,
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
        with self._validation_lock:
            self._grants[grant.approval_ref] = grant.model_copy(deep=True)
        return grant.model_copy(deep=True)

    def create_test_grant(self, request_id: str, approval_ref: str = "approval_test_local_dev") -> ApprovalGrant:
        return self.grant(request_id, approved_by_actor_id="local_test_fixture", approval_ref=approval_ref)

    def deny(self, request_id: str, denied_by_actor_id: str, reason: str) -> ApprovalValidationDecision:
        with self._validation_lock:
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
        with self._validation_lock:
            grant = self._grants[approval_ref]
            reason_ref = build_approval_revocation_reason_ref(reason)
            payload = grant.model_dump(mode="python")
            payload.update(
                {
                    "status": ApprovalStatus.revoked,
                    "revoked_at": utc_now(),
                    "metadata": {
                        **grant.metadata,
                        "revocation_reason_ref": reason_ref,
                    },
                }
            )
            revoked = ApprovalGrant.model_validate(payload)
            self._grants[approval_ref] = revoked
            return revoked.model_copy(deep=True)

    def apply_revocation_tombstone(
        self,
        approval_ref: str,
        *,
        reason_ref: str,
        revoked_at: datetime,
    ) -> ApprovalGrant:
        validate_task_ref(reason_ref, "approval_revocation_reason_ref")
        with self._validation_lock:
            grant = self._grants[approval_ref]
            payload = grant.model_dump(mode="python")
            payload.update(
                {
                    "status": ApprovalStatus.revoked,
                    "revoked_at": revoked_at,
                    "metadata": {
                        **grant.metadata,
                        "revocation_reason_ref": reason_ref,
                    },
                }
            )
            revoked = ApprovalGrant.model_validate(payload)
            self._grants[approval_ref] = revoked
            return revoked.model_copy(deep=True)

    def validate_for_request(self, request: ApprovalRequest, approval_ref: str) -> ApprovalValidationDecision:
        return self.validate(request.to_validation_request(approval_ref))

    def validate(self, validation_request: ApprovalValidationRequest) -> ApprovalValidationDecision:
        with self._validation_lock:
            return self._validate_locked(validation_request)

    def _validate_locked(
        self, validation_request: ApprovalValidationRequest
    ) -> ApprovalValidationDecision:
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

    def validate_at_trusted_time(
        self,
        validation_request: ApprovalValidationRequest,
        *,
        current_time: datetime,
    ) -> ApprovalValidationDecision:
        """Revalidate with a core-supplied clock value under the mutation lock."""

        with self._validation_lock:
            return self._validate_locked(
                validation_request.model_copy(update={"current_time": current_time})
            )

    def get_grant(self, approval_ref: str) -> Optional[ApprovalGrant]:
        with self._validation_lock:
            grant = self._grants.get(approval_ref)
            return grant.model_copy(deep=True) if grant is not None else None

    def find_request_for_validation(
        self,
        validation_request: ApprovalValidationRequest,
    ) -> Optional[ApprovalRequest]:
        """Return an exact registered request; this lookup grants no authority."""

        expected = validation_request.model_dump(
            mode="json",
            exclude={"current_time"},
        )
        with self._validation_lock:
            for request in self._requests.values():
                candidate = request.to_validation_request(
                    validation_request.approval_ref
                ).model_dump(mode="json", exclude={"current_time"})
                if candidate == expected:
                    return request.model_copy(deep=True)
        return None

    def load_grant_for_validation(self, grant: ApprovalGrant) -> None:
        stored = ApprovalGrant.model_validate(grant.model_dump(mode="python"))
        with self._validation_lock:
            self._grants[stored.approval_ref] = stored

    def remove_request_for_rollback(self, approval_request_id: str) -> None:
        with self._validation_lock:
            self._requests.pop(approval_request_id, None)

    def remove_grant_for_rollback(self, approval_ref: str) -> None:
        with self._validation_lock:
            self._grants.pop(approval_ref, None)

    def list_grants(self, run_id: str | None = None) -> List[ApprovalGrant]:
        with self._validation_lock:
            grants = [grant.model_copy(deep=True) for grant in self._grants.values()]
        if run_id is not None:
            grants = [grant for grant in grants if grant.run_id == run_id]
        return grants

    def issue_authority_lease(self, lease: AuthorityLease) -> AuthorityLease:
        stored = AuthorityLease.model_validate(lease.model_dump(mode="python"))
        with self._validation_lock:
            self._authority_leases[stored.lease_ref] = stored
        return stored.model_copy(deep=True)

    def revoke_authority_lease(self, lease_ref: str, reason_ref: str) -> AuthorityLease:
        validate_task_ref(reason_ref, "authority_lease_revocation_reason_ref")
        with self._validation_lock:
            lease = self._authority_leases[lease_ref]
            payload = lease.model_dump(mode="python")
            payload.update(
                {
                    "status": AuthorityLeaseStatus.revoked,
                    "constraints": {
                        **lease.constraints,
                        "revocation_reason_ref": reason_ref,
                    },
                }
            )
            revoked = AuthorityLease.model_validate(payload)
            self._authority_leases[lease_ref] = revoked
            return revoked.model_copy(deep=True)

    def list_authority_leases(self, *, active_only: bool = False) -> list[AuthorityLease]:
        with self._validation_lock:
            leases = [
                lease.model_copy(deep=True)
                for lease in self._authority_leases.values()
            ]
        if active_only:
            leases = [lease for lease in leases if lease.is_active()]
        return leases

    def load_authority_lease_for_validation(self, lease: AuthorityLease) -> None:
        stored = AuthorityLease.model_validate(lease.model_dump(mode="python"))
        with self._validation_lock:
            self._authority_leases[stored.lease_ref] = stored

    def evaluate_authority_scope(
        self,
        request: AuthorityActionRequest,
        *,
        include_default_read_only: bool = False,
    ) -> AuthorityPolicyDecision:
        leases = self.list_authority_leases(active_only=True)
        if include_default_read_only and not leases:
            leases = build_default_authority_leases()
        return evaluate_authority_request(request, leases)

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
        route_request: Any,
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
        tool_request: Any,
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
