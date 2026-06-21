from typing import Any
from pathlib import Path
import pytest

from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    REDACTED_FILE_PREVIEW_TOOL_NAME,
    REDACTED_FILE_PREVIEW_TOOL_REF,
    FilePreviewSafeRoot,
    FilePreviewRedactionSummary,
    RedactedFilePreviewOutput,
    RedactedFilePreviewPolicy,
    RedactedFilePreviewStatus,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolInvocationStatus,
    build_tool_runtime_manifest,
    evaluate_tool_invocation,
)


def _safe_root(tmp_path: Path) -> Any:
    root = tmp_path / "safe-root"
    root.mkdir()
    return FilePreviewSafeRoot(root_ref="safe-root:test", root_path=root, safe_label="Test safe root")


def _preview_request(**overrides: Any) -> Any:
    data = {
        "invocation_id": "tool-runtime-invocation:m33-preview",
        "tool_ref": REDACTED_FILE_PREVIEW_TOOL_REF,
        "tool_name": REDACTED_FILE_PREVIEW_TOOL_NAME,
        "invocation_kind": ToolInvocationKind.redacted_file_preview,
        "replay_key": "tool-runtime-replay:m33-preview",
        "safe_summary": "Generate a redacted file preview proposal.",
        "input_refs": ["canonical:m33"],
        "metadata": {"root_ref": "safe-root:test", "relative_path": "notes/report.md"},
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


def test_default_file_preview_policy_is_redacted_preview_only() -> None:
    policy = RedactedFilePreviewPolicy()

    assert policy.redacted_preview_enabled is True
    assert policy.raw_content_enabled is False
    assert policy.full_file_read_enabled is False
    assert policy.content_hash_enabled is False
    assert policy.directory_listing_enabled is False
    assert policy.recursive_traversal_enabled is False
    assert policy.symlink_following_enabled is False
    assert policy.file_write_enabled is False
    assert policy.file_delete_enabled is False
    assert policy.filesystem_mutation_enabled is False
    assert policy.caller_selected_root_enabled is False
    assert policy.context_injection_enabled is False


def test_manifest_allowlists_noop_metadata_and_redacted_preview_only() -> None:
    manifest = build_tool_runtime_manifest(baseline_version="0.37.0")

    assert manifest.baseline_version == "0.37.0"
    assert manifest.allowlisted_tool_refs == [
        "tool:no_op.v1",
        FILESYSTEM_METADATA_TOOL_REF,
        REDACTED_FILE_PREVIEW_TOOL_REF,
        "tool:http_fetch.read_only_allowlisted.v1",
    ]
    assert manifest.policy.redacted_file_preview_tool_enabled is True
    assert manifest.policy.read_only_http_fetch_tool_enabled is True
    assert manifest.policy.file_content_read_enabled is False
    assert manifest.policy.file_preview_enabled is False
    assert manifest.policy.file_write_enabled is False
    assert manifest.policy.file_delete_enabled is False


def test_safe_text_fixture_preview_returns_redacted_preview_only(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "report.md"
    target.parent.mkdir()
    target.write_text("Title\nAPI_KEY=super-secret-value\nPublic summary.\n", encoding="utf-8")

    decision = evaluate_tool_invocation(_preview_request(), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.preview_completed
    assert decision.invocation_allowed is True
    assert decision.execution_performed is True
    assert decision.side_effects_performed == []
    assert decision.result is not None
    output = decision.result.output
    assert output.status == RedactedFilePreviewStatus.preview_generated
    assert output.redacted_preview_returned is True
    assert "Title" in output.redacted_preview
    assert "Public summary" in output.redacted_preview
    assert "super-secret-value" not in output.redacted_preview
    assert "[REDACTED:SECRET_ASSIGNMENT]" in output.redacted_preview
    assert output.raw_content_returned is False
    assert output.raw_content_stored is False
    assert output.full_file_returned is False
    assert output.absolute_path_returned is False
    assert output.content_hash_returned is False
    assert output.directory_listing_returned is False
    assert output.redaction_summary.redaction_count >= 1
    assert "super-secret-value" not in str(output.redaction_summary.model_dump())
    dumped = str(decision.model_dump())
    assert "super-secret-value" not in dumped
    assert str(safe_root.root_path) not in dumped


@pytest.mark.parametrize(
    "unsafe_preview",
    [
        "API_KEY=super-secret-value",
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",
        "password=super-secret-value",
        "-----BEGIN PRIVATE KEY-----",
        "abcdefghijklmnopqrstuvwxyz1234567890ABCDEF",
    ],
)
def test_redacted_preview_output_rejects_secret_like_preview_content(unsafe_preview: Any) -> None:
    with pytest.raises(ValueError, match="REDACTED_FILE_PREVIEW_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT"):
        RedactedFilePreviewOutput(
            output_ref="redacted-file-preview-output:unsafe",
            status=RedactedFilePreviewStatus.preview_generated,
            root_ref="safe-root:test",
            safe_path_ref="filesystem-preview-path:safe-root_test/notes/report.md",
            redacted_preview=unsafe_preview,
            redaction_summary=FilePreviewRedactionSummary(),
            file_size_bytes=len(unsafe_preview),
        )


def test_long_file_preview_is_bounded_and_truncated(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "long.md"
    target.parent.mkdir()
    target.write_text("a" * 6000, encoding="utf-8")

    decision = evaluate_tool_invocation(
        _preview_request(metadata={"root_ref": "safe-root:test", "relative_path": "notes/long.md"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.preview_completed
    assert decision.result is not None
    output = decision.result.output
    assert output.preview_truncated is True
    assert len(output.redacted_preview.encode("utf-8")) <= output.preview_limit_bytes
    assert output.raw_content_returned is False


def test_oversized_file_is_denied_before_preview(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "large.md"
    target.parent.mkdir()
    with target.open("wb") as handle:
        handle.write(b"a" * 70000)

    decision = evaluate_tool_invocation(
        _preview_request(metadata={"root_ref": "safe-root:test", "relative_path": "notes/large.md"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "FILE_TOO_LARGE_DENIED" in decision.reason_codes
    assert decision.result is None


def test_binary_file_is_denied(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "binary.txt"
    target.parent.mkdir()
    target.write_bytes(b"hello\x00world")

    decision = evaluate_tool_invocation(
        _preview_request(metadata={"root_ref": "safe-root:test", "relative_path": "notes/binary.txt"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "BINARY_FILE_DENIED" in decision.reason_codes


def test_unsupported_encoding_is_denied(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "latin1.txt"
    target.parent.mkdir()
    target.write_bytes("caf\xe9".encode("latin-1"))

    decision = evaluate_tool_invocation(
        _preview_request(metadata={"root_ref": "safe-root:test", "relative_path": "notes/latin1.txt"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "UNSUPPORTED_ENCODING_DENIED" in decision.reason_codes


def test_noop_and_metadata_tools_still_work(tmp_path: Path) -> None:
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "report.md"
    target.parent.mkdir()
    target.write_text("metadata still works", encoding="utf-8")

    noop = evaluate_tool_invocation(
        ToolInvocationRequest(
            invocation_id="tool-runtime-invocation:m33-noop",
            tool_ref="tool:no_op.v1",
            tool_name="noop",
            invocation_kind=ToolInvocationKind.noop,
            replay_key="tool-runtime-replay:m33-noop",
            safe_summary="No-op still works.",
        )
    )
    metadata = evaluate_tool_invocation(
        ToolInvocationRequest(
            invocation_id="tool-runtime-invocation:m33-metadata",
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            tool_name=FILESYSTEM_METADATA_TOOL_NAME,
            invocation_kind=ToolInvocationKind.filesystem_metadata,
            replay_key="tool-runtime-replay:m33-metadata",
            safe_summary="Metadata still works.",
            metadata={"root_ref": "safe-root:test", "relative_path": "notes/report.md"},
        ),
        safe_roots=[safe_root],
    )

    assert noop.status == ToolInvocationStatus.noop_completed
    assert metadata.status == ToolInvocationStatus.metadata_completed
    assert "metadata still works" not in str(metadata.model_dump())


def test_unknown_raw_file_read_tool_is_denied(tmp_path: Path) -> None:
    decision = evaluate_tool_invocation(
        _preview_request(
            tool_ref="tool:file_raw_read.v1",
            tool_name="file_raw_read",
            invocation_kind=ToolInvocationKind.blocked_file,
        ),
        safe_roots=[_safe_root(tmp_path)],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "TOOL_NOT_ALLOWLISTED_DENIED" in decision.reason_codes
    assert "EFFECTFUL_TOOL_BLOCKED" in decision.reason_codes
