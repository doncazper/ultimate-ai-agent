from __future__ import annotations

import hashlib
import re
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


SENSITIVE_CONTEXT_GUARD_REF = "sensitive-context-guard:runtime-context-refs:v1"
SENSITIVE_CONTEXT_CLASSIFIER_REF = "classifier-ref:sensitive-context-refs:v1"

SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:sensitive-context-no-bypass-without-approval",
    "blocked-authority:sensitive-context-no-raw-path-persistence",
    "blocked-authority:sensitive-context-no-protected-context-preview",
    "blocked-authority:sensitive-context-no-automatic-context-injection",
    "blocked-authority:sensitive-context-no-provider-model-call",
    "blocked-authority:sensitive-context-no-connector-write",
    "blocked-authority:sensitive-context-no-shell-execution",
    "blocked-authority:sensitive-context-no-browser-automation",
    "blocked-authority:sensitive-context-no-production-authority",
]

SENSITIVE_CONTEXT_REDACTIONS = [
    "redaction-ref:sensitive-context-raw-candidate-omitted",
    "redaction-ref:sensitive-context-raw-path-material-omitted",
    "redaction-ref:sensitive-context-protected-context-material-omitted",
    "redaction-ref:sensitive-context-credential-like-material-omitted",
]

_ABSOLUTE_LOCAL_PATH_RE = re.compile(
    r"(?i)(^|[\s:=])(/users/|/home/|/etc/|/var/|/private/|[a-z]:[\\/])"
)
_TRAVERSAL_RE = re.compile(r"(^|/|\\)\.\.($|/|\\)")
_HOME_PATH_RE = re.compile(r"(^|[\s:=])~($|/|\\)")
_HIDDEN_SEGMENT_RE = re.compile(r"(^|/|\\)\.[a-z0-9_.-]+($|/|\\)")
_PROTECTED_MARKERS = (
    ".env",
    ".npmrc",
    ".pypirc",
    ".netrc",
    ".ssh",
    "authorized_keys",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "private-key",
    "private_key",
    "protected-config",
    "credentials",
    "credential",
    "client_secret",
    "api_key",
    "apikey",
    "auth_token",
    "access_token",
    "refresh_token",
    "password",
    "passwd",
    "cookie",
)
_PROTECTED_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


class SensitiveContextClassification(BaseModel):
    schema_version: str = "sensitive_context_classification.v1"
    guard_ref: str = SENSITIVE_CONTEXT_GUARD_REF
    classifier_ref: str = SENSITIVE_CONTEXT_CLASSIFIER_REF
    candidate_ref: str
    candidate_kind: str = "context-candidate"
    sensitive: bool
    preview_allowed: bool
    bypass_approval_required: bool
    bypass_approval_enabled: bool = False
    reason_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(SENSITIVE_CONTEXT_REDACTIONS)
    )
    raw_candidate_persisted: bool = False
    raw_path_persisted: bool = False
    protected_context_preview_persisted: bool = False
    provider_model_call_performed: bool = False
    connector_write_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    production_authority_performed: bool = False
    safe_summary: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_classification(self) -> "SensitiveContextClassification":
        for value, field_name in [
            (self.guard_ref, "guard_ref"),
            (self.classifier_ref, "classifier_ref"),
            (self.candidate_ref, "candidate_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "reason_refs",
            "blocked_authority_refs",
            "redactions_applied",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.candidate_kind, "candidate_kind"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "bypass_approval_enabled": self.bypass_approval_enabled,
            "raw_candidate_persisted": self.raw_candidate_persisted,
            "raw_path_persisted": self.raw_path_persisted,
            "protected_context_preview_persisted": (
                self.protected_context_preview_persisted
            ),
            "provider_model_call_performed": self.provider_model_call_performed,
            "connector_write_performed": self.connector_write_performed,
            "shell_execution_performed": self.shell_execution_performed,
            "browser_automation_performed": self.browser_automation_performed,
            "production_authority_performed": self.production_authority_performed,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "SENSITIVE_CONTEXT_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if self.sensitive:
            if self.preview_allowed:
                raise ValueError("SENSITIVE_CONTEXT_PREVIEW_DENIED")
            if not self.reason_refs:
                raise ValueError("SENSITIVE_CONTEXT_REASON_REQUIRED")
            if not self.blocked_authority_refs:
                raise ValueError("SENSITIVE_CONTEXT_BLOCKER_REQUIRED")
        return self


def _candidate_ref(candidate: str, candidate_kind: str) -> str:
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:24]
    return f"sensitive-context-candidate-ref:{candidate_kind}:{digest}"


def _reason_refs(candidate: str) -> list[str]:
    normalized = candidate.strip()
    decoded = unquote(normalized)
    lowered = decoded.lower()
    reasons: list[str] = []
    if contains_obvious_secret({"context_candidate": candidate}):
        reasons.append("sensitive-context-reason:credential-bearing")
    if _ABSOLUTE_LOCAL_PATH_RE.search(lowered):
        reasons.append("sensitive-context-reason:absolute-local-path")
    if _HOME_PATH_RE.search(lowered):
        reasons.append("sensitive-context-reason:home-relative-path")
    if _TRAVERSAL_RE.search(lowered) or _TRAVERSAL_RE.search(
        lowered.replace("%2e", ".")
    ):
        reasons.append("sensitive-context-reason:path-traversal")
    if decoded != normalized and (
        _ABSOLUTE_LOCAL_PATH_RE.search(decoded.lower())
        or _HOME_PATH_RE.search(decoded.lower())
        or _TRAVERSAL_RE.search(decoded.lower())
    ):
        reasons.append("sensitive-context-reason:encoded-unsafe-path")
    if _HIDDEN_SEGMENT_RE.search(lowered):
        reasons.append("sensitive-context-reason:hidden-segment")
    if any(marker in lowered for marker in _PROTECTED_MARKERS):
        reasons.append("sensitive-context-reason:protected-context-marker")
    if lowered.endswith(_PROTECTED_SUFFIXES):
        reasons.append("sensitive-context-reason:protected-file-suffix")
    return list(dict.fromkeys(reasons))


def classify_sensitive_context_candidate(
    candidate: str,
    *,
    candidate_kind: str = "context-candidate",
) -> SensitiveContextClassification:
    if not candidate or not str(candidate).strip():
        raise ValueError("SENSITIVE_CONTEXT_CANDIDATE_REQUIRED")
    reasons = _reason_refs(str(candidate))
    sensitive = bool(reasons)
    return SensitiveContextClassification(
        candidate_ref=_candidate_ref(str(candidate), candidate_kind),
        candidate_kind=candidate_kind,
        sensitive=sensitive,
        preview_allowed=not sensitive,
        bypass_approval_required=sensitive,
        reason_refs=reasons,
        blocked_authority_refs=(
            list(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS) if sensitive else []
        ),
        safe_summary=(
            "Candidate is blocked by sensitive context guards."
            if sensitive
            else "Candidate passed sensitive context guard classification."
        ),
    )


def validate_sensitive_context_candidate_allowed(
    candidate: str,
    *,
    candidate_kind: str,
    status: str = "included",
    preview_available: bool = True,
    blocked_authority_refs: list[str] | None = None,
) -> SensitiveContextClassification:
    classification = classify_sensitive_context_candidate(
        candidate,
        candidate_kind=candidate_kind,
    )
    if not classification.sensitive:
        return classification
    blockers = set(blocked_authority_refs or [])
    required = set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS)
    if status == "blocked" and not preview_available and required.issubset(blockers):
        return classification
    raise ValueError(
        "SENSITIVE_CONTEXT_REF_BLOCKED: " + ",".join(classification.reason_refs)
    )
