from typing import Any
from pathlib import Path
import pytest

from ultimate_ai_agent.core.tools.runtime import (
    REDACTED_FILE_PREVIEW_TOOL_NAME,
    REDACTED_FILE_PREVIEW_TOOL_REF,
    FilePreviewSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolInvocationStatus,
    evaluate_tool_invocation,
)


def _safe_root(tmp_path: Path) -> Any:
    root = tmp_path / "safe-root"
    root.mkdir()
    return FilePreviewSafeRoot(root_ref="safe-root:test", root_path=root, safe_label="Test safe root")


def _request(**overrides: Any) -> Any:
    data = {
        "invocation_id": "tool-runtime-invocation:m33-authority",
        "tool_ref": REDACTED_FILE_PREVIEW_TOOL_REF,
        "tool_name": REDACTED_FILE_PREVIEW_TOOL_NAME,
        "invocation_kind": ToolInvocationKind.redacted_file_preview,
        "replay_key": "tool-runtime-replay:m33-authority",
        "safe_summary": "Generate a redacted file preview proposal.",
        "metadata": {"root_ref": "safe-root:test", "relative_path": "notes/report.md"},
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


@pytest.mark.parametrize(
    "authority_ref",
    [
        "model:m33",
        "runtime:m33",
        "openwebui:m33",
        "memory:m33",
        "context-pack:m33",
        "tool-intent:m33",
        "approval:m33",
        "task-plan:m33",
        "control-center:m33",
    ],
)
def test_authority_refs_cannot_authorize_redacted_preview(tmp_path: Path, authority_ref: Any) -> None:
    safe_root = _safe_root(tmp_path)
    (safe_root.root_path / "notes").mkdir()
    (safe_root.root_path / "notes" / "report.md").write_text("safe body", encoding="utf-8")

    decision = evaluate_tool_invocation(_request(authority_refs=[authority_ref]), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY" in decision.reason_codes


def test_approval_ref_alone_cannot_authorize_redacted_preview(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(_request(approval_ref="approval:m33"), safe_roots=[_safe_root(tmp_path)])

    assert decision.status == ToolInvocationStatus.denied
    assert "APPROVAL_REF_NOT_AUTHORITY" in decision.reason_codes


def test_approval_test_ref_is_denied_for_redacted_preview(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(_request(approval_ref="approval_test_m33"), safe_roots=[_safe_root(tmp_path)])

    assert decision.status == ToolInvocationStatus.denied
    assert "APPROVAL_TEST_REF_DENIED" in decision.reason_codes


def test_model_copy_mutated_raw_file_flag_is_denied(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(
        _request().model_copy(update={"contains_raw_file_content": True}),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "RAW_FILE_CONTENT_DENIED" in decision.reason_codes


def test_model_copy_mutated_tool_ref_to_raw_read_is_denied(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(
        _request().model_copy(update={"tool_ref": "tool:filesystem.raw_read.v1", "tool_name": "redacted_file_preview"}),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "TOOL_NOT_ALLOWLISTED_DENIED" in decision.reason_codes
    assert "EFFECTFUL_TOOL_BLOCKED" in decision.reason_codes

