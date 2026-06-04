from __future__ import annotations

from enum import Enum
import re
import stat
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import (
    FilesystemSafeRoot,
    normalize_relative_metadata_path,
)
from ultimate_ai_agent.core.tools.runtime.validation import validate_safe_tool_runtime_text, validate_tool_runtime_ref


FilePreviewSafeRoot = FilesystemSafeRoot

DEFAULT_MAX_PREVIEW_BYTES = 4096
DEFAULT_MAX_FILE_SIZE_BYTES = 65536

_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)\b(api[_-]?key|authorization|cookie|password|secret|token|client[_-]?secret)\b\s*[:=]\s*[^\s]+"
)
_BEARER_TOKEN_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}")
_PRIVATE_KEY_MARKER_RE = re.compile(r"-----" + r"BEGIN [A-Z ]*PRIVATE KEY" + r"-----")
_HIGH_ENTROPY_RE = re.compile(r"\b[A-Za-z0-9_/-]{32,}\b")
_UNSAFE_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class RedactedFilePreviewStatus(str, Enum):
    preview_generated = "preview_generated"
    denied = "denied"
    missing = "missing"
    blocked = "blocked"


class FilePreviewRedactionSummary(BaseModel):
    redaction_count: int = 0
    categories: List[str] = Field(default_factory=list)
    sensitive_values_returned: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_summary(self):
        allowed_categories = {"secret_assignment", "bearer_token", "private_key_marker", "high_entropy_token"}
        if self.redaction_count < 0:
            raise ValueError("REDACTION_COUNT_INVALID")
        if any(category not in allowed_categories for category in self.categories):
            raise ValueError("REDACTION_CATEGORY_INVALID")
        if self.sensitive_values_returned:
            raise ValueError("REDACTION_SUMMARY_MUST_NOT_RETURN_SENSITIVE_VALUES")
        return self


class RedactedFilePreviewPolicy(BaseModel):
    redacted_preview_enabled: bool = True
    raw_content_enabled: bool = False
    full_file_read_enabled: bool = False
    content_hash_enabled: bool = False
    directory_listing_enabled: bool = False
    recursive_traversal_enabled: bool = False
    symlink_following_enabled: bool = False
    caller_selected_root_enabled: bool = False
    file_write_enabled: bool = False
    file_delete_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    context_injection_enabled: bool = False
    max_preview_bytes: int = DEFAULT_MAX_PREVIEW_BYTES
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self):
        if not self.redacted_preview_enabled:
            raise ValueError("REDACTED_PREVIEW_TOOL_DISABLED")
        blocked_fields = [
            "raw_content_enabled",
            "full_file_read_enabled",
            "content_hash_enabled",
            "directory_listing_enabled",
            "recursive_traversal_enabled",
            "symlink_following_enabled",
            "caller_selected_root_enabled",
            "file_write_enabled",
            "file_delete_enabled",
            "filesystem_mutation_enabled",
            "context_injection_enabled",
        ]
        for field_name in blocked_fields:
            if self.__dict__[field_name]:
                raise ValueError(f"{field_name} must be False in M33")
        if not 1 <= self.max_preview_bytes <= DEFAULT_MAX_PREVIEW_BYTES:
            raise ValueError("PREVIEW_BYTE_LIMIT_INVALID")
        if not self.max_preview_bytes <= self.max_file_size_bytes <= DEFAULT_MAX_FILE_SIZE_BYTES:
            raise ValueError("FILE_SIZE_LIMIT_INVALID")
        return self


class RedactedFilePreviewRequest(BaseModel):
    request_ref: str = "file-preview-request:m33"
    root_ref: str
    relative_path: str
    caller_selected_root_path: Optional[str] = None
    raw_content_enabled: bool = False
    include_raw_content: bool = False
    full_file_read_enabled: bool = False
    include_full_file: bool = False
    content_hash_enabled: bool = False
    include_content_hash: bool = False
    directory_listing_enabled: bool = False
    include_directory_listing: bool = False
    recursive_traversal_enabled: bool = False
    recursive_traversal_requested: bool = False
    symlink_following_enabled: bool = False
    follow_symlinks_requested: bool = False
    caller_selected_root_enabled: bool = False
    file_write_enabled: bool = False
    file_delete_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    mutation_requested: bool = False
    context_injection_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self):
        validate_tool_runtime_ref(self.request_ref, "request_ref")
        validate_tool_runtime_ref(self.root_ref, "root_ref")
        return self


class RedactedFilePreviewOutput(BaseModel):
    output_ref: str
    safe_message: str = "REDACTED_FILE_PREVIEW_RETURNED"
    status: RedactedFilePreviewStatus
    root_ref: str
    safe_path_ref: str
    redacted_preview: str
    redaction_summary: FilePreviewRedactionSummary
    preview_truncated: bool = False
    preview_limit_bytes: int = DEFAULT_MAX_PREVIEW_BYTES
    file_size_bytes: int
    raw_content_returned: bool = False
    raw_content_stored: bool = False
    redacted_preview_returned: bool = True
    full_file_returned: bool = False
    content_hash_returned: bool = False
    directory_listing_returned: bool = False
    absolute_path_returned: bool = False
    symlink_followed: bool = False
    mutation_performed: bool = False
    context_injection_performed: bool = False
    side_effects_performed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_output(self):
        for ref in [self.output_ref, self.root_ref, self.safe_path_ref]:
            validate_tool_runtime_ref(ref, "preview_ref")
        validate_safe_tool_runtime_text(self.safe_message, "safe_message")
        if _contains_unredacted_sensitive_preview(self.redacted_preview):
            raise ValueError("REDACTED_FILE_PREVIEW_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT")
        if not self.redacted_preview_returned or self.status != RedactedFilePreviewStatus.preview_generated:
            raise ValueError("REDACTED_FILE_PREVIEW_OUTPUT_INVALID")
        if self.preview_limit_bytes > DEFAULT_MAX_PREVIEW_BYTES:
            raise ValueError("PREVIEW_BYTE_LIMIT_INVALID")
        if self.file_size_bytes > DEFAULT_MAX_FILE_SIZE_BYTES:
            raise ValueError("FILE_TOO_LARGE_DENIED")
        unsafe_flags = [
            self.raw_content_returned,
            self.raw_content_stored,
            self.full_file_returned,
            self.content_hash_returned,
            self.directory_listing_returned,
            self.absolute_path_returned,
            self.symlink_followed,
            self.mutation_performed,
            self.context_injection_performed,
            self.side_effects_performed,
        ]
        if any(unsafe_flags):
            raise ValueError("REDACTED_FILE_PREVIEW_OUTPUT_MUST_BE_REDACTED_ONLY")
        return self


def _contains_unredacted_sensitive_preview(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in [
            _SECRET_ASSIGNMENT_RE,
            _BEARER_TOKEN_RE,
            _PRIVATE_KEY_MARKER_RE,
            _HIGH_ENTROPY_RE,
        ]
    )


def _payload_flag(payload: Dict[str, object], *names: str) -> bool:
    return any(bool(payload.get(name, False)) for name in names)


def redacted_file_preview_request_from_payload(payload: Dict[str, object]) -> RedactedFilePreviewRequest:
    return RedactedFilePreviewRequest.model_validate(
        {
            "request_ref": payload.get("request_ref", "file-preview-request:m33"),
            "root_ref": payload.get("root_ref"),
            "relative_path": payload.get("relative_path"),
            "caller_selected_root_path": payload.get("caller_selected_root_path") or payload.get("root_path"),
            "raw_content_enabled": _payload_flag(payload, "raw_content_enabled"),
            "include_raw_content": _payload_flag(payload, "include_raw_content"),
            "full_file_read_enabled": _payload_flag(payload, "full_file_read_enabled"),
            "include_full_file": _payload_flag(payload, "include_full_file"),
            "content_hash_enabled": _payload_flag(payload, "content_hash_enabled", "file_hash_enabled"),
            "include_content_hash": _payload_flag(payload, "include_content_hash"),
            "directory_listing_enabled": _payload_flag(payload, "directory_listing_enabled"),
            "include_directory_listing": _payload_flag(payload, "include_directory_listing"),
            "recursive_traversal_enabled": _payload_flag(payload, "recursive_traversal_enabled"),
            "recursive_traversal_requested": _payload_flag(payload, "recursive_traversal_requested"),
            "symlink_following_enabled": _payload_flag(payload, "symlink_following_enabled"),
            "follow_symlinks_requested": _payload_flag(payload, "follow_symlinks_requested"),
            "caller_selected_root_enabled": _payload_flag(payload, "caller_selected_root_enabled"),
            "file_write_enabled": _payload_flag(payload, "file_write_enabled"),
            "file_delete_enabled": _payload_flag(payload, "file_delete_enabled"),
            "filesystem_mutation_enabled": _payload_flag(payload, "filesystem_mutation_enabled"),
            "mutation_requested": _payload_flag(payload, "mutation_requested"),
            "context_injection_enabled": _payload_flag(payload, "context_injection_enabled"),
        }
    )


def redacted_file_preview_boundary_reason_codes(request: RedactedFilePreviewRequest) -> list[str]:
    reasons: list[str] = []
    if request.caller_selected_root_path is not None or request.caller_selected_root_enabled:
        reasons.append("CALLER_SELECTED_ROOT_DENIED")
    if request.raw_content_enabled or request.include_raw_content:
        reasons.append("RAW_FILE_CONTENT_DENIED")
    if request.full_file_read_enabled or request.include_full_file:
        reasons.append("FULL_FILE_READ_DENIED")
    if request.content_hash_enabled or request.include_content_hash:
        reasons.append("CONTENT_HASH_DENIED")
    if request.directory_listing_enabled or request.include_directory_listing:
        reasons.append("DIRECTORY_LISTING_DENIED")
    if request.recursive_traversal_enabled or request.recursive_traversal_requested:
        reasons.append("RECURSIVE_TRAVERSAL_DENIED")
    if request.symlink_following_enabled or request.follow_symlinks_requested:
        reasons.append("SYMLINK_FOLLOWING_DENIED")
    if request.file_write_enabled or request.file_delete_enabled or request.filesystem_mutation_enabled or request.mutation_requested:
        reasons.append("FILESYSTEM_MUTATION_DENIED")
    if request.context_injection_enabled:
        reasons.append("CONTEXT_INJECTION_DENIED")
    return reasons


def redacted_file_preview_policy_reason_codes(
    payload: Dict[str, object],
    safe_roots: list[FilePreviewSafeRoot] | None,
) -> tuple[RedactedFilePreviewRequest | None, FilePreviewSafeRoot | None, str | None, list[str]]:
    try:
        request = redacted_file_preview_request_from_payload(payload)
    except ValueError:
        return None, None, None, ["REDACTED_FILE_PREVIEW_REQUEST_INVALID"]
    reasons = redacted_file_preview_boundary_reason_codes(request)
    normalized_path, path_reasons = normalize_relative_metadata_path(request.relative_path)
    reasons.extend(path_reasons)
    roots = {root.root_ref: root for root in safe_roots or []}
    safe_root = roots.get(request.root_ref)
    if safe_root is None:
        reasons.append("UNKNOWN_SAFE_ROOT_DENIED")
    return request, safe_root, normalized_path, list(dict.fromkeys(reasons))


def _safe_path_ref(root_ref: str, normalized_path: str) -> str:
    root_label = "".join("_" if char == ":" else char for char in root_ref)
    return f"filesystem-preview-path:{root_label}/{normalized_path}"


def _redact(text: str) -> tuple[str, FilePreviewRedactionSummary]:
    categories: list[str] = []

    def replace(pattern: re.Pattern[str], category: str, replacement: str, value: str) -> str:
        nonlocal categories
        if pattern.search(value):
            categories.append(category)
        return pattern.sub(replacement, value)

    redacted = text
    redacted = replace(_PRIVATE_KEY_MARKER_RE, "private_key_marker", "[REDACTED:PRIVATE_KEY_MARKER]", redacted)
    redacted = replace(_SECRET_ASSIGNMENT_RE, "secret_assignment", "[REDACTED:SECRET_ASSIGNMENT]", redacted)
    redacted = replace(_BEARER_TOKEN_RE, "bearer_token", "[REDACTED:BEARER_TOKEN]", redacted)
    redacted = replace(_HIGH_ENTROPY_RE, "high_entropy_token", "[REDACTED:HIGH_ENTROPY_TOKEN]", redacted)
    unique_categories = list(dict.fromkeys(categories))
    return redacted, FilePreviewRedactionSummary(
        redaction_count=len(categories),
        categories=unique_categories,
    )


def build_redacted_file_preview_output(
    *,
    invocation_id: str,
    root_ref: str,
    normalized_path: str,
    target_path: Path,
    policy: RedactedFilePreviewPolicy | None = None,
) -> RedactedFilePreviewOutput:
    active_policy = policy or RedactedFilePreviewPolicy()
    try:
        stat_result = target_path.lstat()
    except FileNotFoundError as exc:
        raise ValueError("FILE_MISSING_DENIED") from exc
    mode = stat_result.st_mode
    if stat.S_ISLNK(mode):
        raise ValueError("SYMLINK_DENIED")
    if stat.S_ISDIR(mode):
        raise ValueError("DIRECTORY_PATH_DENIED")
    if not stat.S_ISREG(mode):
        raise ValueError("UNSUPPORTED_FILE_TYPE_DENIED")
    if stat_result.st_size > active_policy.max_file_size_bytes:
        raise ValueError("FILE_TOO_LARGE_DENIED")

    with target_path.open("rb") as handle:
        preview_bytes = handle.read(active_policy.max_preview_bytes + 1)
    preview_truncated = len(preview_bytes) > active_policy.max_preview_bytes
    preview_bytes = preview_bytes[: active_policy.max_preview_bytes]
    if b"\x00" in preview_bytes:
        raise ValueError("BINARY_FILE_DENIED")
    try:
        preview_text = preview_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("UNSUPPORTED_ENCODING_DENIED") from exc
    if _UNSAFE_CONTROL_CHAR_RE.search(preview_text):
        raise ValueError("BINARY_FILE_DENIED")
    redacted_preview, redaction_summary = _redact(preview_text)
    suffix = invocation_id.split(":", 1)[-1]
    return RedactedFilePreviewOutput(
        output_ref=f"redacted-file-preview-output:{suffix}",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref=root_ref,
        safe_path_ref=_safe_path_ref(root_ref, normalized_path),
        redacted_preview=redacted_preview,
        redaction_summary=redaction_summary,
        preview_truncated=preview_truncated,
        preview_limit_bytes=active_policy.max_preview_bytes,
        file_size_bytes=stat_result.st_size,
    )
