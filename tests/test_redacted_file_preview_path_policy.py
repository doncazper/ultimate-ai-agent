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


def _safe_root(tmp_path):
    root = tmp_path / "safe-root"
    root.mkdir()
    return FilePreviewSafeRoot(root_ref="safe-root:test", root_path=root, safe_label="Test safe root")


def _request(relative_path, **metadata):
    suffix = str(abs(hash(relative_path)))
    payload = {"root_ref": "safe-root:test", "relative_path": relative_path}
    payload.update(metadata)
    return ToolInvocationRequest(
        invocation_id=f"tool-runtime-invocation:m33-path-{suffix}",
        tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
        tool_name=REDACTED_FILE_PREVIEW_TOOL_NAME,
        invocation_kind=ToolInvocationKind.redacted_file_preview,
        replay_key=f"tool-runtime-replay:m33-path-{suffix}",
        safe_summary="Generate a redacted file preview proposal.",
        metadata=payload,
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
def test_unsafe_preview_paths_are_denied(tmp_path, relative_path, reason_code):
    decision = evaluate_tool_invocation(_request(relative_path), safe_roots=[_safe_root(tmp_path)])

    assert decision.status == ToolInvocationStatus.denied
    assert decision.invocation_allowed is False
    assert decision.execution_performed is False
    assert reason_code in decision.reason_codes
    assert decision.side_effects_performed == []


def test_unknown_safe_root_ref_is_denied(tmp_path):
    decision = evaluate_tool_invocation(
        _request("notes/report.md", root_ref="safe-root:missing"),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "UNKNOWN_SAFE_ROOT_DENIED" in decision.reason_codes


def test_arbitrary_root_path_in_metadata_is_denied(tmp_path):
    decision = evaluate_tool_invocation(
        _request("notes/report.md", root_path=str(tmp_path)),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "CALLER_SELECTED_ROOT_DENIED" in decision.reason_codes


def test_directory_path_is_denied_without_listing(tmp_path):
    safe_root = _safe_root(tmp_path)
    notes = safe_root.root_path / "notes"
    notes.mkdir()
    (notes / "child.md").write_text("child content", encoding="utf-8")

    decision = evaluate_tool_invocation(_request("notes"), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "DIRECTORY_PATH_DENIED" in decision.reason_codes
    assert "child.md" not in str(decision.model_dump())


def test_symlink_path_is_denied(tmp_path):
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "target.md"
    target.write_text("safe target", encoding="utf-8")
    link = safe_root.root_path / "link.md"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not supported")

    decision = evaluate_tool_invocation(_request("link.md"), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "SYMLINK_DENIED" in decision.reason_codes


@pytest.mark.parametrize(
    ("flag_name", "reason_code"),
    [
        ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
        ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
        ("content_hash_enabled", "CONTENT_HASH_DENIED"),
        ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
        ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
        ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
        ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
        ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
        ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
        ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ],
)
def test_preview_denies_model_copy_mutated_metadata_alias_flags(tmp_path, flag_name, reason_code):
    safe_root = _safe_root(tmp_path)
    request = _request("notes/report.md").model_copy(
        update={"metadata": {"root_ref": "safe-root:test", "relative_path": "notes/report.md", flag_name: True}}
    )

    decision = evaluate_tool_invocation(request, safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert reason_code in decision.reason_codes

