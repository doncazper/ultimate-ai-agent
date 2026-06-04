import stat
from pathlib import Path
from typing import Iterable

from ultimate_ai_agent.core.tools.runtime.contracts import (
    ToolInvocationDecision,
    ToolInvocationRequest,
    ToolInvocationResult,
    ToolRuntimePolicy,
)
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationStatus, ToolRuntimeAuthorityLevel
from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import (
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemSafeRoot,
    build_filesystem_metadata_output,
    build_missing_filesystem_metadata_output,
    filesystem_metadata_policy_reason_codes,
)
from ultimate_ai_agent.core.tools.runtime.file_preview import (
    RedactedFilePreviewPolicy,
    build_redacted_file_preview_output,
    redacted_file_preview_policy_reason_codes,
)
from ultimate_ai_agent.core.tools.runtime.noop import invoke_noop_tool
from ultimate_ai_agent.core.tools.runtime.policy import validate_runtime_policy, validate_tool_invocation_request
from ultimate_ai_agent.core.tools.runtime.receipts import build_tool_invocation_receipt_plan
from ultimate_ai_agent.core.tools.runtime.validation import (
    ALLOWLISTED_TOOL_NAMES,
    NOOP_TOOL_REF,
    REDACTED_FILE_PREVIEW_TOOL_REF,
    validate_tool_runtime_ref,
)


def _safe_invocation_id(value: str) -> str:
    try:
        validate_tool_runtime_ref(value, "invocation_id")
    except ValueError:
        return "tool-runtime-invocation:denied"
    return value


def _denied_decision(request: ToolInvocationRequest, reasons: list[str]) -> ToolInvocationDecision:
    status = ToolInvocationStatus.replay_detected if "TOOL_RUNTIME_REPLAY_DETECTED" in reasons else ToolInvocationStatus.denied
    invocation_id = _safe_invocation_id(request.invocation_id)
    safe_tool_ref = request.tool_ref if request.tool_ref in ALLOWLISTED_TOOL_NAMES else NOOP_TOOL_REF
    return ToolInvocationDecision(
        decision_id=f"tool-runtime-decision:{invocation_id.split(':', 1)[-1]}",
        invocation_id=invocation_id,
        tool_ref=safe_tool_ref,
        status=status,
        invocation_allowed=False,
        execution_performed=False,
        reason_codes=list(dict.fromkeys(reasons)),
        safe_message="Tool runtime invocation denied by governed tool runtime policy.",
    )


def _symlink_reason_codes(root: Path, normalized_path: str) -> list[str]:
    reasons: list[str] = []
    try:
        root_mode = root.lstat().st_mode
    except FileNotFoundError:
        return reasons
    if stat.S_ISLNK(root_mode):
        return ["SAFE_ROOT_SYMLINK_DENIED"]
    current = root
    for part in normalized_path.split("/"):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            break
        if stat.S_ISLNK(mode):
            reasons.append("SYMLINK_DENIED")
            break
    return reasons


def evaluate_tool_invocation(
    request: ToolInvocationRequest,
    policy: ToolRuntimePolicy | None = None,
    replay_keys_seen: Iterable[str] | None = None,
    safe_roots: list[FilesystemSafeRoot] | None = None,
) -> ToolInvocationDecision:
    active_policy = policy or ToolRuntimePolicy()
    reasons = validate_runtime_policy(active_policy)
    reasons.extend(validate_tool_invocation_request(request, safe_roots=safe_roots))
    fs_request = None
    fs_root = None
    fs_normalized_path = None
    preview_request = None
    preview_root = None
    preview_normalized_path = None
    if request.tool_ref == FILESYSTEM_METADATA_TOOL_REF:
        fs_request, fs_root, fs_normalized_path, fs_reasons = filesystem_metadata_policy_reason_codes(
            request.metadata, safe_roots=safe_roots
        )
        reasons.extend(fs_reasons)
        if fs_root is not None and fs_normalized_path is not None:
            reasons.extend(_symlink_reason_codes(fs_root.root_path, fs_normalized_path))
    if request.tool_ref == REDACTED_FILE_PREVIEW_TOOL_REF:
        preview_request, preview_root, preview_normalized_path, preview_reasons = redacted_file_preview_policy_reason_codes(
            request.metadata, safe_roots=safe_roots
        )
        reasons.extend(preview_reasons)
        if preview_root is not None and preview_normalized_path is not None:
            reasons.extend(_symlink_reason_codes(preview_root.root_path, preview_normalized_path))
    if active_policy.replay_protection_required and request.replay_key in set(replay_keys_seen or []):
        reasons.append("TOOL_RUNTIME_REPLAY_DETECTED")
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return _denied_decision(request, reasons)

    receipt = build_tool_invocation_receipt_plan(request)
    if request.tool_ref == FILESYSTEM_METADATA_TOOL_REF:
        assert fs_request is not None
        assert fs_root is not None
        assert fs_normalized_path is not None
        target_path = fs_root.root_path / fs_normalized_path
        try:
            output = build_filesystem_metadata_output(
                invocation_id=request.invocation_id,
                root_ref=fs_request.root_ref,
                normalized_path=fs_normalized_path,
                target_path=target_path,
            )
        except FileNotFoundError:
            output = build_missing_filesystem_metadata_output(
                invocation_id=request.invocation_id,
                root_ref=fs_request.root_ref,
                normalized_path=fs_normalized_path,
            )
        result = ToolInvocationResult(
            result_id=f"tool-runtime-result:{request.invocation_id.split(':', 1)[-1]}",
            invocation_id=request.invocation_id,
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            status=ToolInvocationStatus.metadata_completed,
            output=output,
            receipt_plan=receipt,
        )
        return ToolInvocationDecision(
            decision_id=f"tool-runtime-decision:{request.invocation_id.split(':', 1)[-1]}",
            invocation_id=request.invocation_id,
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            status=ToolInvocationStatus.metadata_completed,
            invocation_allowed=True,
            execution_performed=True,
            authority_level=ToolRuntimeAuthorityLevel.metadata_runtime_only,
            reason_codes=["FILESYSTEM_METADATA_RETURNED"],
            safe_message="Filesystem metadata lookup completed without content access or side effects.",
            result=result,
            receipt_plan=receipt,
        )

    if request.tool_ref == REDACTED_FILE_PREVIEW_TOOL_REF:
        assert preview_request is not None
        assert preview_root is not None
        assert preview_normalized_path is not None
        target_path = preview_root.root_path / preview_normalized_path
        try:
            output = build_redacted_file_preview_output(
                invocation_id=request.invocation_id,
                root_ref=preview_request.root_ref,
                normalized_path=preview_normalized_path,
                target_path=target_path,
                policy=RedactedFilePreviewPolicy(),
            )
        except ValueError as exc:
            return _denied_decision(request, [str(exc)])
        result = ToolInvocationResult(
            result_id=f"tool-runtime-result:{request.invocation_id.split(':', 1)[-1]}",
            invocation_id=request.invocation_id,
            tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
            status=ToolInvocationStatus.preview_completed,
            output=output,
            receipt_plan=receipt,
        )
        return ToolInvocationDecision(
            decision_id=f"tool-runtime-decision:{request.invocation_id.split(':', 1)[-1]}",
            invocation_id=request.invocation_id,
            tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
            status=ToolInvocationStatus.preview_completed,
            invocation_allowed=True,
            execution_performed=True,
            authority_level=ToolRuntimeAuthorityLevel.metadata_runtime_only,
            reason_codes=["REDACTED_FILE_PREVIEW_RETURNED"],
            safe_message="Redacted file preview proposal completed without raw content return or side effects.",
            result=result,
            receipt_plan=receipt,
        )

    output = invoke_noop_tool(request)
    result = ToolInvocationResult(
        result_id=f"tool-runtime-result:{request.invocation_id.split(':', 1)[-1]}",
        invocation_id=request.invocation_id,
        output=output,
        receipt_plan=receipt,
    )
    return ToolInvocationDecision(
        decision_id=f"tool-runtime-decision:{request.invocation_id.split(':', 1)[-1]}",
        invocation_id=request.invocation_id,
        tool_ref=NOOP_TOOL_REF,
        status=ToolInvocationStatus.noop_completed,
        invocation_allowed=True,
        execution_performed=True,
        authority_level=ToolRuntimeAuthorityLevel.noop_runtime_only,
        reason_codes=["NOOP_TOOL_COMPLETED"],
        safe_message="Deterministic no-op tool invocation completed without side effects.",
        result=result,
        receipt_plan=receipt,
    )
