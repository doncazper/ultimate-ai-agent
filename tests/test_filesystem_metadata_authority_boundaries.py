from typing import Any
from pathlib import Path
import pytest

from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolInvocationStatus,
    evaluate_tool_invocation,
)


def _safe_root(tmp_path: Path) -> Any:
    root = tmp_path / "safe-root"
    root.mkdir()
    return FilesystemSafeRoot(root_ref="safe-root:test", root_path=root, safe_label="Test safe root")


def _request(**overrides: Any) -> Any:
    data = {
        "invocation_id": "tool-runtime-invocation:m32-authority",
        "tool_ref": FILESYSTEM_METADATA_TOOL_REF,
        "tool_name": FILESYSTEM_METADATA_TOOL_NAME,
        "invocation_kind": ToolInvocationKind.filesystem_metadata,
        "replay_key": "tool-runtime-replay:m32-authority",
        "safe_summary": "Inspect safe filesystem metadata.",
        "metadata": {"root_ref": "safe-root:test", "relative_path": "notes/report.md"},
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


@pytest.mark.parametrize(
    "authority_ref",
    [
        "model:m32",
        "runtime:m32",
        "openwebui:m32",
        "memory:m32",
        "context-pack:m32",
        "tool-intent:m32",
        "approval:m32",
        "task-plan:m32",
        "control-center:m32",
    ],
)
def test_authority_refs_cannot_authorize_filesystem_metadata(tmp_path: Path, authority_ref: Any) -> None:
    safe_root = _safe_root(tmp_path)
    (safe_root.root_path / "notes").mkdir()
    (safe_root.root_path / "notes" / "report.md").write_text("metadata only", encoding="utf-8")

    decision = evaluate_tool_invocation(_request(authority_refs=[authority_ref]), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY" in decision.reason_codes


def test_approval_ref_alone_cannot_authorize_filesystem_metadata(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)

    decision = evaluate_tool_invocation(_request(approval_ref="approval:m32"), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "APPROVAL_REF_NOT_AUTHORITY" in decision.reason_codes


def test_approval_test_ref_is_denied_for_filesystem_metadata(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)

    decision = evaluate_tool_invocation(_request(approval_ref="approval_test_m32"), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "APPROVAL_TEST_REF_DENIED" in decision.reason_codes
