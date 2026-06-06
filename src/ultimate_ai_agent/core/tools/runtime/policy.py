from pydantic import ValidationError

from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest, ToolRuntimePolicy
from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import (
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemSafeRoot,
    filesystem_metadata_policy_reason_codes,
)
from ultimate_ai_agent.core.tools.runtime.file_preview import (
    redacted_file_preview_policy_reason_codes,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (
    READ_ONLY_HTTP_FETCH_TOOL_REF,
    http_fetch_policy_reason_codes,
)
from ultimate_ai_agent.core.tools.runtime.validation import (
    REDACTED_FILE_PREVIEW_TOOL_REF,
    authority_reason_codes,
    raw_input_reason_codes,
    runtime_request_boundary_reason_codes,
    safe_validation_reasons,
    tool_allowlist_reason_codes,
    validate_safe_tool_runtime_payload,
)


def validate_tool_invocation_request(
    request: ToolInvocationRequest, safe_roots: list[FilesystemSafeRoot] | None = None
) -> list[str]:
    reasons: list[str] = []
    try:
        if request.tool_ref not in {
            FILESYSTEM_METADATA_TOOL_REF,
            REDACTED_FILE_PREVIEW_TOOL_REF,
            READ_ONLY_HTTP_FETCH_TOOL_REF,
        }:
            validate_safe_tool_runtime_payload(request.metadata, "metadata")
        ToolInvocationRequest.model_validate(request.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(safe_validation_reasons(exc, fallback="TOOL_RUNTIME_REQUEST_REVALIDATION_FAILED"))
    reasons.extend(runtime_request_boundary_reason_codes(request, set(ToolInvocationRequest.model_fields)))
    reasons.extend(raw_input_reason_codes(request))
    reasons.extend(tool_allowlist_reason_codes(request.tool_ref, request.tool_name))
    reasons.extend(authority_reason_codes(request.approval_ref, request.authority_refs))
    if request.tool_ref == FILESYSTEM_METADATA_TOOL_REF:
        metadata_request, _safe_root, _normalized_path, fs_reasons = filesystem_metadata_policy_reason_codes(
            request.metadata, safe_roots=safe_roots
        )
        reasons.extend(fs_reasons)
        if metadata_request is None:
            reasons.append("FILESYSTEM_METADATA_REQUEST_INVALID")
    if request.tool_ref == REDACTED_FILE_PREVIEW_TOOL_REF:
        preview_request, _safe_root, _normalized_path, preview_reasons = redacted_file_preview_policy_reason_codes(
            request.metadata, safe_roots=safe_roots
        )
        reasons.extend(preview_reasons)
        if preview_request is None:
            reasons.append("REDACTED_FILE_PREVIEW_REQUEST_INVALID")
    if request.tool_ref == READ_ONLY_HTTP_FETCH_TOOL_REF:
        http_request, _http_target, http_reasons = http_fetch_policy_reason_codes(request.metadata)
        reasons.extend(http_reasons)
        if http_request is None:
            reasons.append("HTTP_FETCH_REQUEST_INVALID")
    if request.tool_ref == FILESYSTEM_METADATA_TOOL_REF and request.invocation_kind.value != "filesystem_metadata":
        reasons.append("TOOL_INVOCATION_KIND_MISMATCH_DENIED")
    elif request.tool_ref == REDACTED_FILE_PREVIEW_TOOL_REF and request.invocation_kind.value != "redacted_file_preview":
        reasons.append("TOOL_INVOCATION_KIND_MISMATCH_DENIED")
    elif request.tool_ref == READ_ONLY_HTTP_FETCH_TOOL_REF and request.invocation_kind.value != "read_only_http_fetch":
        reasons.append("TOOL_INVOCATION_KIND_MISMATCH_DENIED")
    elif request.tool_ref != FILESYSTEM_METADATA_TOOL_REF and request.invocation_kind.value != "noop":
        if request.tool_ref not in {REDACTED_FILE_PREVIEW_TOOL_REF, READ_ONLY_HTTP_FETCH_TOOL_REF}:
            reasons.append("EFFECTFUL_TOOL_BLOCKED")
    return list(dict.fromkeys(reasons))


def validate_runtime_policy(policy: ToolRuntimePolicy) -> list[str]:
    try:
        ToolRuntimePolicy.model_validate(policy.model_dump())
    except (ValidationError, ValueError) as exc:
        return safe_validation_reasons(exc, fallback="TOOL_RUNTIME_POLICY_INVALID")
    return []
