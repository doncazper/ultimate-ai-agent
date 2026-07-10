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


def _request(relative_path: Any) -> Any:
    suffix = str(abs(hash(relative_path)))
    return ToolInvocationRequest(
        invocation_id=f"tool-runtime-invocation:m32-path-{suffix}",
        tool_ref=FILESYSTEM_METADATA_TOOL_REF,
        tool_name=FILESYSTEM_METADATA_TOOL_NAME,
        invocation_kind=ToolInvocationKind.filesystem_metadata,
        replay_key=f"tool-runtime-replay:m32-path-{suffix}",
        safe_summary="Inspect safe filesystem metadata.",
        metadata={"root_ref": "safe-root:test", "relative_path": relative_path},
    )


@pytest.mark.parametrize(
    ("relative_path", "reason_code"),
    [
        ("/etc/passwd", "ABSOLUTE_PATH_DENIED"),
        ("../outside.txt", "PATH_TRAVERSAL_DENIED"),
        ("notes/../../outside.txt", "PATH_TRAVERSAL_DENIED"),
        ("notes/%2e%2e/outside.txt", "PATH_TRAVERSAL_DENIED"),
        ("~/notes/report.md", "HOME_PATH_DENIED"),
        ("C:/Users/report.md", "WINDOWS_PATH_DENIED"),
        ("notes//report.md", "UNSAFE_PATH_SEPARATOR_DENIED"),
        ("", "EMPTY_PATH_DENIED"),
        (".env", "HIDDEN_PATH_DENIED"),
        (".git/config", "HIDDEN_PATH_DENIED"),
        ("notes/.private/report.md", "HIDDEN_PATH_DENIED"),
        ("secrets/report.md", "SECRET_LIKE_PATH_DENIED"),
        ("notes/api_key.txt", "SECRET_LIKE_PATH_DENIED"),
        ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
        ("keys/private.key", "SECRET_LIKE_PATH_DENIED"),
        ("notes/*.md", "GLOB_PATH_DENIED"),
        ("notes/%2A.md", "GLOB_PATH_DENIED"),
    ],
)
def test_unsafe_metadata_paths_are_denied(tmp_path: Path, relative_path: Any, reason_code: Any) -> None:
    decision = evaluate_tool_invocation(_request(relative_path), safe_roots=[_safe_root(tmp_path)])

    assert decision.status == ToolInvocationStatus.denied
    assert decision.invocation_allowed is False
    assert decision.execution_performed is False
    assert reason_code in decision.reason_codes
    assert decision.side_effects_performed == []


def test_unknown_safe_root_ref_is_denied(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(
        _request("notes/report.md").model_copy(update={"metadata": {"root_ref": "safe-root:missing", "relative_path": "notes/report.md"}}),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "UNKNOWN_SAFE_ROOT_DENIED" in decision.reason_codes


def test_arbitrary_root_path_in_metadata_is_denied(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(
        _request("notes/report.md").model_copy(
            update={
                "metadata": {
                    "root_ref": "safe-root:test",
                    "relative_path": "notes/report.md",
                    "root_path": str(tmp_path),
                }
            }
        ),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "CALLER_SELECTED_ROOT_DENIED" in decision.reason_codes


def test_intermediate_symlink_cannot_escape_safe_root(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "report.md").write_text("outside", encoding="utf-8")
    (safe_root.root_path / "notes").symlink_to(outside, target_is_directory=True)

    decision = evaluate_tool_invocation(
        _request("notes/report.md"),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert decision.invocation_allowed is False
    assert decision.execution_performed is False
    assert "SYMLINK_DENIED" in decision.reason_codes
