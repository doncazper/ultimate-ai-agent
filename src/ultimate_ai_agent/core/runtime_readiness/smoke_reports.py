from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.runtime_readiness.enums import SmokeReportStatus
from ultimate_ai_agent.core.time import utc_now

ALLOWED_RESPONSE_ORIGINS = {
    "local_loopback_smoke",
    "fake_transport",
    "fake_manual_loopback_smoke",
    "simulated_fallback",
}

SECRET_QUERY_MARKERS = ("api_key=", "token=", "secret=", "password=", "auth=", "credential=")
REMOTE_ENDPOINT_MARKERS = ("https://", "api.openai.com", "anthropic.com", "generativelanguage", "://")
CLOUD_PROVIDER_MARKERS = ("cloud provider", "provider model call", "openai", "anthropic", "gemini", "api call executed")
REMOTE_EXECUTION_MARKERS = ("remote execution", "remote dispatch", "worker executed", "subagent launched")
LIVE_MESH_MARKERS = ("live tailnet", "live mesh", "headscale", "tailscale", "wireguard connected", "node key")
MOBILE_SENSOR_MARKERS = ("mobile camera", "microphone", "gps", "location sensor", "photos access", "contacts access")
PLUGIN_BUILD_MARKERS = ("plugin enabled", "build plugin enabled", "xcode build", "simulator run", "computer use enabled")
PRODUCTION_RUNTIME_MARKERS = (
    "production runtime",
    "production readiness",
    "production evidence",
    "real runtime origin",
    "real model output",
)


class ManualSmokeReport(BaseModel):
    report_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    smoke_request_id: str = Field(..., min_length=1)
    endpoint_summary: str = Field(..., min_length=1, max_length=256)
    model_id_summary: str = Field(..., min_length=1, max_length=128)
    response_origin: str = Field(..., min_length=1)
    fixed_prompt_hash: str = Field(..., min_length=8, max_length=128)
    response_marker_found: bool = False
    response_preview: str | None = Field(None, max_length=512)
    response_body_sha256: str | None = Field(None, min_length=8, max_length=128)
    elapsed_ms: int | None = Field(None, ge=0, le=120_000)
    model_output_authoritative: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())

    model_config = ConfigDict(extra="forbid")

    @field_validator("response_origin")
    @classmethod
    def response_origin_allowed(cls, value: str) -> str:
        if value not in ALLOWED_RESPONSE_ORIGINS:
            raise ValueError("SMOKE_RESPONSE_ORIGIN_NOT_ALLOWED")
        return value

    @model_validator(mode="after")
    def report_values_must_be_safe(self) -> Any:
        if self.model_output_authoritative:
            raise ValueError("MODEL_OUTPUT_AUTHORITY_REJECTED")
        return self


class ManualSmokeReportValidation(BaseModel):
    validation_id: str = Field(default_factory=lambda: f"manual_smoke_report_validation_{utc_now().timestamp():.0f}")
    report_id: str | None = None
    allowed: bool
    status: SmokeReportStatus
    reason_codes: list[str]
    safe_message: str
    redactions_applied: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def validate_manual_smoke_report(report: ManualSmokeReport | Mapping[str, Any]) -> ManualSmokeReportValidation:
    raw_report: dict[str, Any] | None = None
    try:
        raw_report = report.model_dump(mode="json") if isinstance(report, ManualSmokeReport) else dict(report)
        parsed = report if isinstance(report, ManualSmokeReport) else ManualSmokeReport(**raw_report)
    except ValidationError as exc:
        reasons = ["REPORT_SCHEMA_INVALID"]
        if raw_report is not None and not raw_report.get("fixed_prompt_hash"):
            reasons.append("FIXED_PROMPT_HASH_REQUIRED")
        if "MODEL_OUTPUT_AUTHORITY_REJECTED" in str(exc):
            reasons.append("MODEL_OUTPUT_AUTHORITY_REJECTED")
        if "SMOKE_RESPONSE_ORIGIN_NOT_ALLOWED" in str(exc):
            reasons.append("SMOKE_RESPONSE_ORIGIN_NOT_ALLOWED")
        return _validation(None, False, reasons, ["schema"])

    reasons: list[str] = []
    redactions: list[str] = []
    payload = parsed.model_dump(mode="json")

    if not parsed.fixed_prompt_hash:
        reasons.append("FIXED_PROMPT_HASH_REQUIRED")
    if parsed.model_output_authoritative:
        reasons.append("MODEL_OUTPUT_AUTHORITY_REJECTED")
    if contains_secret_like(payload):
        reasons.append("SECRET_LIKE_VALUE_REJECTED")
        redactions.append("unsafe_values")
    if contains_secret_like(parsed.response_preview):
        reasons.append("SECRET_LIKE_VALUE_REJECTED")
        redactions.append("response_preview")

    endpoint = parsed.endpoint_summary.lower()
    if "@" in endpoint:
        reasons.append("ENDPOINT_CREDENTIALS_REJECTED")
    if any(marker in endpoint for marker in SECRET_QUERY_MARKERS):
        reasons.append("ENDPOINT_QUERY_SECRET_REJECTED")
    if _remote_endpoint_summary(endpoint):
        reasons.append("REMOTE_ENDPOINT_SUMMARY_REJECTED")

    combined_text = _flatten_text(payload)
    reasons.extend(_claim_reasons(combined_text))

    deduped = _dedupe(reasons)
    if deduped:
        return _validation(parsed.report_id, False, deduped, redactions)
    return ManualSmokeReportValidation(
        report_id=parsed.report_id,
        allowed=True,
        status=SmokeReportStatus.valid,
        reason_codes=["MANUAL_SMOKE_REPORT_SAFE"],
        safe_message="Manual smoke report is safe to retain as non-authoritative readiness metadata.",
        redactions_applied=[],
    )


def _remote_endpoint_summary(endpoint: str) -> bool:
    if "://" not in endpoint:
        return False
    if "localhost" in endpoint or "127.0.0.1" in endpoint or "[::1]" in endpoint or "::1" in endpoint:
        return False
    return any(marker in endpoint for marker in REMOTE_ENDPOINT_MARKERS)


def _claim_reasons(text: str) -> list[str]:
    lowered = text.lower()
    reasons: list[str] = []
    if any(marker in lowered for marker in CLOUD_PROVIDER_MARKERS):
        reasons.append("CLOUD_PROVIDER_EXECUTION_CLAIM_REJECTED")
    if any(marker in lowered for marker in REMOTE_EXECUTION_MARKERS):
        reasons.append("REMOTE_EXECUTION_CLAIM_REJECTED")
    if any(marker in lowered for marker in LIVE_MESH_MARKERS):
        reasons.append("LIVE_MESH_CLAIM_REJECTED")
    if any(marker in lowered for marker in MOBILE_SENSOR_MARKERS):
        reasons.append("MOBILE_SENSOR_CLAIM_REJECTED")
    if any(marker in lowered for marker in PLUGIN_BUILD_MARKERS):
        reasons.append("PLUGIN_OR_BUILD_TOOL_CLAIM_REJECTED")
    if any(marker in lowered for marker in PRODUCTION_RUNTIME_MARKERS):
        reasons.append("PRODUCTION_RUNTIME_CLAIM_REJECTED")
    return reasons


def _flatten_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _validation(
    report_id: str | None,
    allowed: bool,
    reasons: list[str],
    redactions: list[str],
) -> ManualSmokeReportValidation:
    return ManualSmokeReportValidation(
        report_id=report_id,
        allowed=allowed,
        status=SmokeReportStatus.invalid,
        reason_codes=_dedupe(reasons),
        safe_message="Manual smoke report was rejected by runtime readiness validation.",
        redactions_applied=_dedupe(redactions),
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
