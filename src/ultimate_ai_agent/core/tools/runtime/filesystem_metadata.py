from __future__ import annotations

from enum import Enum
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.runtime.validation import (
    SECRET_LIKE_RE,
    validate_safe_tool_runtime_text,
    validate_tool_runtime_ref,
)


FILESYSTEM_METADATA_TOOL_REF = "tool:filesystem_metadata.v1"
FILESYSTEM_METADATA_TOOL_NAME = "filesystem_metadata"

HIDDEN_SEGMENT_DENY_REASON = "HIDDEN_PATH_DENIED"
SECRET_SEGMENT_DENY_REASON = "SECRET_LIKE_PATH_DENIED"
PRIVATE_KEY_LIKE_SEGMENTS = {
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "private.key",
    "private_key",
}


class FilesystemMetadataStatus(str, Enum):
    metadata_returned = "metadata_returned"
    denied = "denied"
    missing = "missing"


class FilesystemSafeRoot(BaseModel):
    root_ref: str = Field(..., min_length=1)
    root_path: Path
    safe_label: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_root(self) -> Any:
        validate_tool_runtime_ref(self.root_ref, "root_ref")
        validate_safe_tool_runtime_text(self.safe_label, "safe_label")
        if not self.root_path.is_absolute():
            raise ValueError("SAFE_ROOT_PATH_MUST_BE_ABSOLUTE")
        return self


class FilesystemMetadataRequest(BaseModel):
    request_ref: str = "filesystem-metadata-request:m32"
    root_ref: str
    relative_path: str
    caller_selected_root_path: Optional[str] = None
    include_raw_content: bool = False
    include_text_preview: bool = False
    include_content_hash: bool = False
    include_directory_listing: bool = False
    recursive_traversal_requested: bool = False
    follow_symlinks_requested: bool = False
    mutation_requested: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        validate_tool_runtime_ref(self.request_ref, "request_ref")
        validate_tool_runtime_ref(self.root_ref, "root_ref")
        return self


class FilesystemMetadataOutput(BaseModel):
    output_ref: str
    safe_message: str = "FILESYSTEM_METADATA_RETURNED"
    status: str
    root_ref: str
    safe_path_ref: str
    path_kind: str = "missing"
    exists: bool = False
    size_bytes: Optional[int] = None
    modified_time_ns: Optional[int] = None
    extension: Optional[str] = None
    raw_content_returned: bool = False
    text_preview_returned: bool = False
    content_hash_returned: bool = False
    directory_listing_returned: bool = False
    absolute_path_returned: bool = False
    symlink_followed: bool = False
    mutation_performed: bool = False
    side_effects_performed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_output(self) -> Any:
        for ref in [self.output_ref, self.root_ref, self.safe_path_ref]:
            validate_tool_runtime_ref(ref, "metadata_ref")
        validate_safe_tool_runtime_text(self.safe_message, "safe_message")
        if self.status not in {
            FilesystemMetadataStatus.metadata_returned,
            FilesystemMetadataStatus.denied,
            FilesystemMetadataStatus.missing,
        }:
            raise ValueError("FILESYSTEM_METADATA_STATUS_INVALID")
        if self.path_kind not in {"file", "directory", "other", "missing"}:
            raise ValueError("FILESYSTEM_METADATA_KIND_INVALID")
        unsafe_flags = [
            self.raw_content_returned,
            self.text_preview_returned,
            self.content_hash_returned,
            self.directory_listing_returned,
            self.absolute_path_returned,
            self.symlink_followed,
            self.mutation_performed,
            self.side_effects_performed,
        ]
        if any(unsafe_flags):
            raise ValueError("FILESYSTEM_METADATA_OUTPUT_MUST_BE_METADATA_ONLY")
        return self


def filesystem_metadata_boundary_reason_codes(request: FilesystemMetadataRequest) -> list[str]:
    reasons: list[str] = []
    if request.caller_selected_root_path is not None:
        reasons.append("CALLER_SELECTED_ROOT_DENIED")
    if request.include_raw_content:
        reasons.append("RAW_FILE_CONTENT_DENIED")
    if request.include_text_preview:
        reasons.append("TEXT_PREVIEW_DENIED")
    if request.include_content_hash:
        reasons.append("CONTENT_HASH_DENIED")
    if request.include_directory_listing:
        reasons.append("DIRECTORY_LISTING_DENIED")
    if request.recursive_traversal_requested:
        reasons.append("RECURSIVE_TRAVERSAL_DENIED")
    if request.follow_symlinks_requested:
        reasons.append("SYMLINK_FOLLOWING_DENIED")
    if request.mutation_requested:
        reasons.append("FILESYSTEM_MUTATION_DENIED")
    return reasons


def normalize_relative_metadata_path(relative_path: str) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    if not relative_path or not relative_path.strip():
        return None, ["EMPTY_PATH_DENIED"]
    path_text = relative_path.strip()
    decoded_path_text = unquote(path_text)
    path_texts_to_check = [path_text]
    if decoded_path_text != path_text:
        path_texts_to_check.append(decoded_path_text)
    if "\\" in path_text or "\\" in decoded_path_text:
        reasons.append("UNSAFE_PATH_SEPARATOR_DENIED")
    if "//" in path_text or "//" in decoded_path_text:
        reasons.append("UNSAFE_PATH_SEPARATOR_DENIED")
    if path_text.startswith("~") or decoded_path_text.startswith("~"):
        reasons.append("HOME_PATH_DENIED")
    if path_text.startswith("//") or decoded_path_text.startswith("//"):
        reasons.append("UNC_PATH_DENIED")
    if any(len(text) >= 2 and text[1] == ":" for text in path_texts_to_check):
        reasons.append("WINDOWS_PATH_DENIED")
    if any("*" in text or "?" in text or "[" in text or "]" in text for text in path_texts_to_check):
        reasons.append("GLOB_PATH_DENIED")
    candidate = PurePosixPath(decoded_path_text)
    if candidate.is_absolute():
        reasons.append("ABSOLUTE_PATH_DENIED")
    parts = [part for part in candidate.parts if part not in {"", "."}]
    if not parts:
        reasons.append("EMPTY_PATH_DENIED")
    if any(part == ".." for part in parts):
        reasons.append("PATH_TRAVERSAL_DENIED")
    for part in parts:
        lower_part = part.lower()
        if part.startswith("."):
            reasons.append(HIDDEN_SEGMENT_DENY_REASON)
        if SECRET_LIKE_RE.search(part) or lower_part in PRIVATE_KEY_LIKE_SEGMENTS or lower_part.endswith(".pem"):
            reasons.append(SECRET_SEGMENT_DENY_REASON)
    if reasons:
        return None, list(dict.fromkeys(reasons))
    return "/".join(parts), []


def filesystem_safe_path_ref(root_ref: str, normalized_path: str) -> str:
    root_label = "".join("_" if char == ":" else char for char in root_ref)
    return f"filesystem-path:{root_label}/{normalized_path}"


def filesystem_metadata_target_path(
    root_path: Path,
    normalized_path: str,
) -> Path:
    target_path = root_path / normalized_path
    current = root_path
    candidates = [current]
    for part in PurePosixPath(normalized_path).parts:
        current = current / part
        candidates.append(current)
    for candidate in candidates:
        try:
            mode = candidate.lstat().st_mode
        except (FileNotFoundError, NotADirectoryError):
            break
        if stat.S_ISLNK(mode):
            raise ValueError("SYMLINK_DENIED")
    return target_path


def _payload_flag(payload: Dict[str, object], *names: str) -> bool:
    return any(bool(payload.get(name, False)) for name in names)


def filesystem_metadata_request_from_payload(payload: Dict[str, object]) -> FilesystemMetadataRequest:
    return FilesystemMetadataRequest.model_validate(
        {
            "request_ref": payload.get("request_ref", "filesystem-metadata-request:m32"),
            "root_ref": payload.get("root_ref"),
            "relative_path": payload.get("relative_path"),
            "caller_selected_root_path": payload.get("caller_selected_root_path") or payload.get("root_path"),
            "include_raw_content": _payload_flag(payload, "include_raw_content", "raw_content_enabled"),
            "include_text_preview": _payload_flag(payload, "include_text_preview", "file_preview_enabled"),
            "include_content_hash": _payload_flag(payload, "include_content_hash", "file_hash_enabled"),
            "include_directory_listing": _payload_flag(
                payload, "include_directory_listing", "directory_listing_enabled"
            ),
            "recursive_traversal_requested": _payload_flag(
                payload, "recursive_traversal_requested", "recursive_traversal_enabled"
            ),
            "follow_symlinks_requested": _payload_flag(
                payload, "follow_symlinks_requested", "symlink_following_enabled"
            ),
            "mutation_requested": _payload_flag(
                payload,
                "mutation_requested",
                "file_write_enabled",
                "file_delete_enabled",
                "filesystem_mutation_enabled",
            ),
        }
    )


def filesystem_metadata_policy_reason_codes(
    payload: Dict[str, object],
    safe_roots: list[FilesystemSafeRoot] | None,
) -> tuple[FilesystemMetadataRequest | None, FilesystemSafeRoot | None, str | None, list[str]]:
    try:
        request = filesystem_metadata_request_from_payload(payload)
    except ValueError:
        return None, None, None, ["FILESYSTEM_METADATA_REQUEST_INVALID"]
    reasons = filesystem_metadata_boundary_reason_codes(request)
    if _payload_flag(payload, "caller_selected_root_enabled"):
        reasons.append("CALLER_SELECTED_ROOT_DENIED")
    normalized_path, path_reasons = normalize_relative_metadata_path(request.relative_path)
    reasons.extend(path_reasons)
    roots = {root.root_ref: root for root in safe_roots or []}
    safe_root = roots.get(request.root_ref)
    if safe_root is None:
        reasons.append("UNKNOWN_SAFE_ROOT_DENIED")
    return request, safe_root, normalized_path, list(dict.fromkeys(reasons))


def build_filesystem_metadata_output(
    *,
    invocation_id: str,
    root_ref: str,
    normalized_path: str,
    target_path: Path,
) -> FilesystemMetadataOutput:
    stat_result = target_path.lstat()
    mode = stat_result.st_mode
    if stat.S_ISLNK(mode):
        raise ValueError("SYMLINK_DENIED")
    if stat.S_ISDIR(mode):
        path_kind = "directory"
        size_bytes = None
        extension = None
    elif stat.S_ISREG(mode):
        path_kind = "file"
        size_bytes = stat_result.st_size
        extension = target_path.suffix.lower() or None
    else:
        path_kind = "other"
        size_bytes = stat_result.st_size
        extension = None
    suffix = invocation_id.split(":", 1)[-1]
    return FilesystemMetadataOutput(
        output_ref=f"filesystem-metadata-output:{suffix}",
        status=FilesystemMetadataStatus.metadata_returned,
        root_ref=root_ref,
        safe_path_ref=filesystem_safe_path_ref(root_ref, normalized_path),
        path_kind=path_kind,
        exists=True,
        size_bytes=size_bytes,
        modified_time_ns=stat_result.st_mtime_ns,
        extension=extension,
    )


def build_missing_filesystem_metadata_output(
    *,
    invocation_id: str,
    root_ref: str,
    normalized_path: str,
) -> FilesystemMetadataOutput:
    suffix = invocation_id.split(":", 1)[-1]
    return FilesystemMetadataOutput(
        output_ref=f"filesystem-metadata-output:{suffix}",
        safe_message="FILESYSTEM_METADATA_MISSING",
        status=FilesystemMetadataStatus.missing,
        root_ref=root_ref,
        safe_path_ref=filesystem_safe_path_ref(root_ref, normalized_path),
        path_kind="missing",
        exists=False,
    )
