import re
from typing import Any
from ultimate_ai_agent.core.contracts.enums import GroundingMode, ContractStatus, RiskLevel, AgentMode
from ultimate_ai_agent.core.contracts.execution_contract import ExecutionContract
from ultimate_ai_agent.core.contracts.context_pack import ContextPack
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope, ErrorEnvelope, ErrorCategory, Severity

BLOCKED_CAPABILITIES = [
    "reddit_scanner",
    "news_scanner",
    "weather_provider_v1",
    "email_scanner",
    "message_scanner",
    "calendar_scanner",
    "companion_proactivity",
    "skill_factory",
    "self_improving_code",
    "autopilot_workflows",
    "external_high_autonomy_execution",
    "credentialed_provider_integrations",
    "truth_sensitive_scanners",
]

SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]")

def validate_execution_contract(contract: ExecutionContract) -> ResultEnvelope:
    # Rule 7 & 8 & 9: Blocked capabilities, skills, and real executions
    for tool in contract.allowed_tools:
        if any(blocked in tool.lower() for blocked in BLOCKED_CAPABILITIES) or "skill" in tool.lower():
            err = ErrorEnvelope(
                code="BLOCKED_CAPABILITY",
                category=ErrorCategory.security_blocked,
                safe_message=f"Tool '{tool}' is blocked by the Foundation Gate",
                severity=Severity.critical,
                retryable=False,
                details_redacted=False,
                source="ContractValidator"
            )
            return ResultEnvelope(
                success=False,
                operation="validate_contract",
                service="ContractValidator",
                trace_id=contract.run_id,
                error=err
            )

    for flag in contract.capability_flags_required:
        if any(blocked in flag.lower() for blocked in BLOCKED_CAPABILITIES) or "skill" in flag.lower():
            err = ErrorEnvelope(
                code="BLOCKED_CAPABILITY",
                category=ErrorCategory.security_blocked,
                safe_message=f"Capability flag '{flag}' is blocked by the Foundation Gate",
                severity=Severity.critical,
                retryable=False,
                details_redacted=False,
                source="ContractValidator"
            )
            return ResultEnvelope(
                success=False,
                operation="validate_contract",
                service="ContractValidator",
                trace_id=contract.run_id,
                error=err
            )

    # Rule 1: Mutating/external/destructive/high-risk actions require approval policy.
    is_high_risk = contract.risk_level in [RiskLevel.high, RiskLevel.critical]
    is_mutating = contract.mode in [AgentMode.execute, AgentMode.self_improve] or any(
        "write" in t or "update" in t or "exec" in t for t in contract.allowed_tools
    )
    if (is_high_risk or is_mutating) and not contract.approval_policy:
        err = ErrorEnvelope(
            code="MISSING_APPROVAL_POLICY",
            category=ErrorCategory.policy_denied,
            safe_message="Approval policy is required for mutating or high-risk tasks",
            severity=Severity.high,
            retryable=False,
            details_redacted=False,
            source="ContractValidator"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_contract",
            service="ContractValidator",
            trace_id=contract.run_id,
            error=err
        )

    # Rule 3: High-risk actions cannot use standing approvals.
    if is_high_risk and contract.approval_policy:
        if contract.approval_policy.get("standing_approval") is True:
            err = ErrorEnvelope(
                code="STANDING_APPROVAL_NOT_ALLOWED",
                category=ErrorCategory.policy_denied,
                safe_message="Standing approvals are not allowed for high-risk or critical tasks",
                severity=Severity.high,
                retryable=False,
                details_redacted=False,
                source="ContractValidator"
            )
            return ResultEnvelope(
                success=False,
                operation="validate_contract",
                service="ContractValidator",
                trace_id=contract.run_id,
                error=err
            )

    # Rule 4: High-stakes factual tasks require grounding_mode != none
    if is_high_risk and contract.mode in [AgentMode.research, AgentMode.answer]:
        if contract.grounding_mode == GroundingMode.none:
            err = ErrorEnvelope(
                code="GROUNDING_REQUIRED",
                category=ErrorCategory.policy_denied,
                safe_message="Grounding mode cannot be 'none' for high-stakes factual or research tasks",
                severity=Severity.high,
                retryable=False,
                details_redacted=False,
                source="ContractValidator"
            )
            return ResultEnvelope(
                success=False,
                operation="validate_contract",
                service="ContractValidator",
                trace_id=contract.run_id,
                error=err
            )

    # Rule 5: If grounding_mode requires evidence, required_evidence cannot be empty.
    if contract.grounding_mode != GroundingMode.none and not contract.required_evidence:
        err = ErrorEnvelope(
            code="REQUIRED_EVIDENCE_EMPTY",
            category=ErrorCategory.validation_error,
            safe_message="Grounding mode requires evidence, but required_evidence is empty",
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ContractValidator"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_contract",
            service="ContractValidator",
            trace_id=contract.run_id,
            error=err
        )

    # Rule 6: If unknowns block acceptance criteria, contract status should indicate needs_clarification or blocked.
    if contract.unknowns and contract.status not in [ContractStatus.needs_clarification, ContractStatus.blocked, ContractStatus.draft]:
        err = ErrorEnvelope(
            code="CONTRACT_BLOCKED_BY_UNKNOWNS",
            category=ErrorCategory.validation_error,
            safe_message="Contract contains unknowns but status is not draft, needs_clarification or blocked",
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ContractValidator"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_contract",
            service="ContractValidator",
            trace_id=contract.run_id,
            error=err
        )

    # Rule 11: Redaction policy must exist when private/sensitive data classifications are present.
    if contract.data_classification and contract.data_classification.classification in [
        "sensitive_personal",
        "credential_secret",
        "regulated",
        "third_party_confidential"
    ]:
        if not contract.redaction_policy:
            err = ErrorEnvelope(
                code="REDACTION_POLICY_REQUIRED",
                category=ErrorCategory.policy_denied,
                safe_message="Redaction policy is required for sensitive or private data classifications",
                severity=Severity.high,
                retryable=False,
                details_redacted=False,
                source="ContractValidator"
            )
            return ResultEnvelope(
                success=False,
                operation="validate_contract",
                service="ContractValidator",
                trace_id=contract.run_id,
                error=err
            )

    return ResultEnvelope(
        success=True,
        operation="validate_contract",
        service="ContractValidator",
        trace_id=contract.run_id,
        data={"contract_id": contract.contract_id, "status": "validated"}
    )

def validate_context_pack(pack: ContextPack) -> ResultEnvelope:
    # Rule 10: Check Context Pack fields for raw secrets
    def scan_for_secrets(val: Any) -> bool:
        if isinstance(val, str):
            if SECRET_PATTERN.search(val):
                return True
        elif isinstance(val, dict):
            for k, v in val.items():
                if scan_for_secrets(k) or scan_for_secrets(v):
                    return True
        elif isinstance(val, list):
            for item in val:
                if scan_for_secrets(item):
                    return True
        return False

    if scan_for_secrets(pack.model_dump()):
        err = ErrorEnvelope(
            code="SECRET_EXPOSURE_BLOCKED",
            category=ErrorCategory.security_blocked,
            safe_message="Context Pack validation failed: raw secrets/credentials detected in payload",
            severity=Severity.critical,
            retryable=False,
            details_redacted=False,
            source="ContextPackValidator"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_context_pack",
            service="ContextPackValidator",
            trace_id=pack.run_id,
            error=err
        )

    return ResultEnvelope(
        success=True,
        operation="validate_context_pack",
        service="ContextPackValidator",
        trace_id=pack.run_id,
        data={"context_pack_id": pack.context_pack_id, "status": "validated"}
    )
