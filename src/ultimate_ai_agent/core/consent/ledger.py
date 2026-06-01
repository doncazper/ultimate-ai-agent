import uuid
from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional
from ultimate_ai_agent.core.consent.enums import ConsentStatus, PermissionRisk, ApprovalRequirement, DataBoundary, PermissionAction
from ultimate_ai_agent.core.consent.grants import ConsentGrant, RevocationRecord
from ultimate_ai_agent.core.consent.decisions import ConsentQuery, ConsentDecision
from ultimate_ai_agent.core.consent.validation import validate_consent_grant

class ConsentLedger:
    def __init__(self):
        self._grants: List[ConsentGrant] = []
        self._revocations: List[RevocationRecord] = []

    def add_grant(self, grant: ConsentGrant) -> None:
        validate_consent_grant(grant)
        self._grants.append(grant)

    def revoke_grant(self, consent_id: str, reason: str, revoked_by: str = "system") -> None:
        for grant in self._grants:
            if grant.consent_id == consent_id:
                grant.status = ConsentStatus.revoked
                grant.revoked_at = utc_now()
                record = RevocationRecord(
                    consent_id=consent_id,
                    reason=reason,
                    revoked_by=revoked_by
                )
                self._revocations.append(record)
                return
        raise ValueError(f"Consent grant with id '{consent_id}' not found.")

    def list_grants(self, status: Optional[ConsentStatus] = None) -> List[ConsentGrant]:
        if status:
            return [g for g in self._grants if g.status == status]
        return list(self._grants)

    def check_expiration(self, now: datetime) -> None:
        for grant in self._grants:
            if grant.status == ConsentStatus.active and grant.expires_at and grant.expires_at <= now:
                grant.status = ConsentStatus.expired

    def evaluate(self, query: ConsentQuery) -> ConsentDecision:
        return self._evaluate_query(query)

    def explain_decision(self, query: ConsentQuery) -> ConsentDecision:
        return self._evaluate_query(query)

    def _evaluate_query(self, query: ConsentQuery) -> ConsentDecision:
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"
        now = utc_now()
        self.check_expiration(now)

        matched_grants: List[str] = []
        reason_codes: List[str] = []
        
        # Rule: Forbidden risk level is instantly blocked
        if query.risk_level == PermissionRisk.forbidden:
            return ConsentDecision(
                decision_id=decision_id,
                allowed=False,
                required_approval=ApprovalRequirement.forbidden,
                reason_codes=["RISK_FORBIDDEN"],
                safe_message="Action is forbidden due to critical risk policy"
            )

        # Deny Overrides Allow check
        for grant in self._grants:
            if grant.status != ConsentStatus.active:
                continue
            
            # Match actor
            if grant.granted_to_actor != query.actor_id and grant.granted_to_actor != "*":
                continue
                
            # If the grant explicitly denies this action or all actions.
            if query.action in grant.denied_actions or PermissionAction.any in grant.denied_actions:
                reason_codes.append("EXPLICIT_DENY_ACTION")
                return ConsentDecision(
                    decision_id=decision_id,
                    allowed=False,
                    matched_grants=[grant.consent_id],
                    required_approval=ApprovalRequirement.forbidden,
                    reason_codes=reason_codes,
                    safe_message=f"Action '{query.action}' is explicitly denied by consent grant '{grant.consent_id}'"
                )
            if query.resource in grant.denied_resources:
                reason_codes.append("EXPLICIT_DENY_RESOURCE")
                return ConsentDecision(
                    decision_id=decision_id,
                    allowed=False,
                    matched_grants=[grant.consent_id],
                    required_approval=ApprovalRequirement.forbidden,
                    reason_codes=reason_codes,
                    safe_message=f"Resource '{query.resource}' is explicitly denied by consent grant '{grant.consent_id}'"
                )
            # If data classification matches denied boundaries
            if query.data_classification and query.data_classification in grant.denied_data_boundaries:
                reason_codes.append("EXPLICIT_DENY_DATA_BOUNDARY")
                return ConsentDecision(
                    decision_id=decision_id,
                    allowed=False,
                    matched_grants=[grant.consent_id],
                    required_approval=ApprovalRequirement.forbidden,
                    reason_codes=reason_codes,
                    safe_message=f"Data boundary '{query.data_classification}' is explicitly denied by consent grant '{grant.consent_id}'"
                )

        # Check allows
        allowed_by_any = False
        for grant in self._grants:
            if grant.status != ConsentStatus.active:
                continue
            
            if grant.granted_to_actor != query.actor_id and grant.granted_to_actor != "*":
                continue

            # Must match allowed action
            action_allowed = (query.action in grant.allowed_actions) or (PermissionAction.any in grant.allowed_actions)
            if not action_allowed:
                continue

            # Must match resource boundary
            resource_allowed = False
            if not grant.allowed_resources or ("*" in grant.allowed_resources):
                resource_allowed = True
            else:
                for res_pattern in grant.allowed_resources:
                    if res_pattern == query.resource or (res_pattern.endswith("*") and query.resource.startswith(res_pattern[:-1])):
                        resource_allowed = True
                        break
            if not resource_allowed:
                continue

            # Check sensitive data boundary if sensitive
            if query.data_classification in [DataBoundary.credential_secret, DataBoundary.sensitive_personal, DataBoundary.tcb_protected]:
                # Requires explicit allowed data boundary
                if query.data_classification not in grant.allowed_data_boundaries:
                    continue

            # Check purpose matching
            purpose_matched = True
            if grant.allowed_purposes:
                if query.purpose not in grant.allowed_purposes and "*" not in grant.allowed_purposes:
                    purpose_matched = False
            if not purpose_matched:
                continue

            allowed_by_any = True
            matched_grants.append(grant.consent_id)

        if not allowed_by_any:
            return ConsentDecision(
                decision_id=decision_id,
                allowed=False,
                missing_permissions=[str(query.action)],
                required_approval=ApprovalRequirement.human_required,
                reason_codes=["NO_MATCHING_GRANT"],
                safe_message="No active matching consent grants found for the requested action"
            )

        # Approval Requirement calculations based on risk
        req_approval = ApprovalRequirement.none
        if query.risk_level == PermissionRisk.low:
            req_approval = ApprovalRequirement.standing
        elif query.risk_level == PermissionRisk.medium:
            req_approval = ApprovalRequirement.session
        elif query.risk_level in [PermissionRisk.high, PermissionRisk.critical]:
            req_approval = ApprovalRequirement.human_required

        return ConsentDecision(
            decision_id=decision_id,
            allowed=True,
            matched_grants=matched_grants,
            required_approval=req_approval,
            reason_codes=["CONSENT_GRANTED"],
            safe_message="Consent successfully authorized by active matching grants"
        )
