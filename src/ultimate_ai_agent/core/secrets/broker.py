import uuid
from ultimate_ai_agent.core.time import utc_now
from typing import Dict, List, Optional

from ultimate_ai_agent.core.secrets.credentials import CredentialReference, SecretAccessRequest
from ultimate_ai_agent.core.secrets.enums import CredentialStatus
from ultimate_ai_agent.core.secrets.handles import (
    RedactedSecretView,
    SecretAccessDecision,
    SecretHandle,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret, redact_secret_value


class SecretBroker:
    """Local/dev-only in-memory Secret Broker contract.

    This class never writes secret values to disk and never returns raw values.
    The in-memory value store exists only so unit tests can prove redaction and
    handle behavior.
    """

    def __init__(self):
        self._references: Dict[str, CredentialReference] = {}
        self._secret_values: Dict[str, str] = {}

    def register_credential(self, reference: CredentialReference, secret_value: Optional[str] = None) -> None:
        self._references[reference.credential_ref] = reference
        if secret_value is not None:
            self._secret_values[reference.credential_ref] = secret_value

    def get_reference(self, credential_ref: str) -> Optional[CredentialReference]:
        return self._references.get(credential_ref)

    def list_references(self) -> List[CredentialReference]:
        return list(self._references.values())

    def revoke_credential(self, credential_ref: str, reason: str) -> None:
        reference = self._require_reference(credential_ref)
        reference.status = CredentialStatus.revoked
        reference.metadata["revocation_reason"] = reason

    def request_secret(
        self,
        access_request: Optional[SecretAccessRequest] = None,
        *,
        credential_ref: Optional[str] = None,
        requester_actor_id: str = "system",
        purpose: Optional[str] = None,
        provider_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        consent_ref: Optional[str] = None,
        policy_ref: Optional[str] = None,
    ) -> SecretAccessDecision:
        request = access_request or SecretAccessRequest(
            credential_ref=credential_ref or "",
            requester_actor_id=requester_actor_id,
            purpose=purpose or "",
            provider_id=provider_id,
            tool_id=tool_id,
            consent_ref=consent_ref,
            policy_ref=policy_ref,
        )
        reference = self._references.get(request.credential_ref)
        if reference is None:
            return self._deny(request.credential_ref, ["CREDENTIAL_NOT_FOUND"], "Credential reference was not found.")

        inactive_reasons = self._inactive_reasons(reference)
        if inactive_reasons:
            return self._deny(reference.credential_ref, inactive_reasons, "Credential is not active.")

        if not request.consent_ref and not request.policy_ref and not reference.consent_ref:
            return self._deny(reference.credential_ref, ["CONSENT_REQUIRED"], "Secret access requires consent or policy approval.")

        if reference.allowed_purposes and request.purpose not in reference.allowed_purposes:
            return self._deny(reference.credential_ref, ["PURPOSE_NOT_ALLOWED"], "Requested purpose is outside credential policy.")

        if request.provider_id and reference.provider_id and request.provider_id != reference.provider_id:
            return self._deny(reference.credential_ref, ["PROVIDER_SCOPE_MISMATCH"], "Provider scope does not match credential.")

        if request.tool_id and reference.tool_id and request.tool_id != reference.tool_id:
            return self._deny(reference.credential_ref, ["TOOL_SCOPE_MISMATCH"], "Tool scope does not match credential.")

        reference.last_used_at = utc_now()
        handle = SecretHandle(
            handle_id=f"sh_{uuid.uuid4().hex[:12]}",
            credential_ref=reference.credential_ref,
            provider_id=reference.provider_id,
            tool_id=reference.tool_id,
        )
        return SecretAccessDecision(
            decision_id=f"sdec_{uuid.uuid4().hex[:8]}",
            allowed=True,
            credential_ref=reference.credential_ref,
            secret_handle=handle,
            reason_codes=["SECRET_HANDLE_ISSUED"],
            safe_message="Secret access authorized; opaque handle issued.",
            redactions_applied=["secret_value"],
            event_ref=request.event_ref,
        )

    def redact_value(self, value: str) -> str:
        return redact_secret_value(value)

    def redacted_view(self, credential_ref: str) -> RedactedSecretView:
        reference = self._require_reference(credential_ref)
        return RedactedSecretView(
            credential_ref=reference.credential_ref,
            provider_id=reference.provider_id,
            tool_id=reference.tool_id,
        )

    def validate_no_secret_leak(self, payload: object) -> bool:
        return not contains_obvious_secret(payload)

    def _require_reference(self, credential_ref: str) -> CredentialReference:
        reference = self._references.get(credential_ref)
        if reference is None:
            raise ValueError(f"Credential reference not found: {credential_ref}")
        return reference

    def _inactive_reasons(self, reference: CredentialReference) -> List[str]:
        if reference.status != CredentialStatus.active:
            return ["CREDENTIAL_INACTIVE"]
        if reference.expires_at and reference.expires_at <= utc_now():
            reference.status = CredentialStatus.expired
            return ["CREDENTIAL_INACTIVE", "CREDENTIAL_EXPIRED"]
        return []

    def _deny(self, credential_ref: str, reason_codes: List[str], safe_message: str) -> SecretAccessDecision:
        return SecretAccessDecision(
            decision_id=f"sdec_{uuid.uuid4().hex[:8]}",
            allowed=False,
            credential_ref=credential_ref,
            reason_codes=reason_codes,
            safe_message=safe_message,
            redactions_applied=["secret_value"],
        )
