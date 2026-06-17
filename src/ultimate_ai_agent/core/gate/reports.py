import re
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.time import utc_now


class FoundationGateResult(BaseModel):
    criterion_id: str = Field(..., min_length=1)
    status: FoundationGateStatus
    safe_message: str = Field(..., min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FoundationGateCommandReceipt(BaseModel):
    command_ref: str = Field(..., min_length=1)
    command_mode: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    satisfied_by: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    return_code: Optional[int] = None
    elapsed_ms: Optional[int] = Field(default=None, ge=0)
    checked_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class FoundationGateReport(BaseModel):
    report_id: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    overall_status: FoundationGateStatus
    results: List[FoundationGateResult]
    passed_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    blocked_count: int = 0
    summary: str
    next_recommended_action: str
    event_ref: Optional[str] = None
    trace_id: Optional[str] = None
    command_mode: Optional[str] = None
    command_receipts: List[FoundationGateCommandReceipt] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def build_foundation_gate_report(
    *,
    version: str,
    results: List[FoundationGateResult],
    event_ref: Optional[str] = None,
    trace_id: Optional[str] = None,
    command_mode: Optional[str] = None,
    command_receipts: Optional[List[FoundationGateCommandReceipt]] = None,
) -> FoundationGateReport:
    ordered_results = sorted(results, key=lambda result: result.criterion_id)
    passed_count = sum(1 for result in ordered_results if result.status == FoundationGateStatus.passed)
    failed_count = sum(1 for result in ordered_results if result.status == FoundationGateStatus.failed)
    warning_count = sum(1 for result in ordered_results if result.status == FoundationGateStatus.warning)
    blocked_count = sum(1 for result in ordered_results if result.status == FoundationGateStatus.blocked)

    if failed_count:
        overall_status = FoundationGateStatus.failed
        next_action = "Fix failed criteria before expansion."
    elif blocked_count:
        overall_status = FoundationGateStatus.blocked
        next_action = "Remove blocked capability before expansion."
    elif warning_count:
        overall_status = FoundationGateStatus.warning
        next_action = "Review warnings before expansion."
    else:
        overall_status = FoundationGateStatus.passed
        next_action = "Foundation can proceed to controlled expansion review."

    return FoundationGateReport(
        report_id=f"fgrep_{uuid.uuid4().hex[:12]}",
        version=version,
        overall_status=overall_status,
        results=ordered_results,
        passed_count=passed_count,
        failed_count=failed_count,
        warning_count=warning_count,
        blocked_count=blocked_count,
        summary=(
            f"{passed_count} passed, {failed_count} failed, "
            f"{warning_count} warnings, {blocked_count} blocked."
        ),
        next_recommended_action=next_action,
        event_ref=event_ref,
        trace_id=trace_id,
        command_mode=command_mode,
        command_receipts=command_receipts or [],
    )


def scan_public_gate_payload_for_secrets(payload) -> List[str]:
    loose_assignment = re.compile(
        r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|auth[_-]?token|password)\s*=\s*[A-Za-z0-9_\-.:/]{12,}"
    )

    def walk(value, path: str) -> List[str]:
        findings: List[str] = []
        if isinstance(value, str):
            if loose_assignment.search(value) or scan_payload_for_secrets(value):
                findings.append(path)
        elif isinstance(value, dict):
            for key, item in value.items():
                findings.extend(walk(item, f"{path}.{key}"))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                findings.extend(walk(item, f"{path}[{index}]"))
        return findings

    return walk(payload, "payload")


def validate_foundation_gate_report(report: FoundationGateReport) -> ResultEnvelope:
    secret_refs = scan_public_gate_payload_for_secrets(report.model_dump(mode="json"))
    if secret_refs:
        return ResultEnvelope(
            success=False,
            operation="validate_foundation_gate_report",
            service="FoundationGateAPI",
            trace_id=report.trace_id or report.report_id,
            error=ErrorEnvelope(
                code="FOUNDATION_GATE_REPORT_SECRET_EXPOSURE",
                category=ErrorCategory.security_blocked,
                safe_message="Foundation Gate report validation failed: secret-like content detected.",
                severity=Severity.critical,
                retryable=False,
                details_redacted=True,
                source="FoundationGateAPI",
            ),
        )

    return ResultEnvelope(
        success=True,
        operation="validate_foundation_gate_report",
        service="FoundationGateAPI",
        trace_id=report.trace_id or report.report_id,
        data={
            "report_id": report.report_id,
            "status": "validated",
            "overall_status": report.overall_status,
        },
    )
