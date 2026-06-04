import os

from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemMetadataRequest,
    FilesystemMetadataStatus,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolInvocationStatus,
    ToolRuntimeAdapter,
    build_tool_runtime_manifest,
    evaluate_tool_invocation,
)


def _safe_root(tmp_path):
    root = tmp_path / "safe-root"
    root.mkdir()
    return FilesystemSafeRoot(root_ref="safe-root:test", root_path=root, safe_label="Test safe root")


def _request(**overrides):
    data = {
        "invocation_id": "tool-runtime-invocation:m32-filesystem-metadata",
        "tool_ref": FILESYSTEM_METADATA_TOOL_REF,
        "tool_name": FILESYSTEM_METADATA_TOOL_NAME,
        "invocation_kind": ToolInvocationKind.filesystem_metadata,
        "replay_key": "tool-runtime-replay:m32-filesystem-metadata",
        "safe_summary": "Inspect safe filesystem metadata.",
        "input_refs": ["canonical:m32"],
        "metadata": {"root_ref": "safe-root:test", "relative_path": "notes/report.md"},
    }
    data.update(overrides)
    return ToolInvocationRequest(**data)


def test_manifest_allowlists_noop_and_filesystem_metadata_only():
    manifest = build_tool_runtime_manifest(baseline_version="0.36.0")

    assert manifest.baseline_version == "0.36.0"
    assert manifest.allowlisted_tool_refs == ["tool:no_op.v1", FILESYSTEM_METADATA_TOOL_REF]
    assert manifest.policy.noop_tool_enabled is True
    assert manifest.policy.filesystem_metadata_tool_enabled is True
    assert manifest.policy.file_tools_enabled is False
    assert manifest.policy.file_content_read_enabled is False
    assert manifest.policy.file_preview_enabled is False
    assert manifest.policy.file_hash_enabled is False
    assert manifest.policy.directory_listing_enabled is False
    assert manifest.policy.recursive_traversal_enabled is False
    assert manifest.policy.symlink_following_enabled is False
    assert manifest.policy.caller_selected_root_enabled is False
    assert manifest.policy.file_write_enabled is False
    assert manifest.policy.file_delete_enabled is False


def test_safe_file_metadata_invocation_returns_metadata_only(tmp_path):
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "report.md"
    target.parent.mkdir()
    target.write_text("do not read this body", encoding="utf-8")

    decision = evaluate_tool_invocation(_request(), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.metadata_completed
    assert decision.invocation_allowed is True
    assert decision.execution_performed is True
    assert decision.side_effects_performed == []
    assert decision.result is not None
    assert decision.result.output.status == FilesystemMetadataStatus.metadata_returned
    assert decision.result.output.path_kind == "file"
    assert decision.result.output.exists is True
    assert decision.result.output.size_bytes == len("do not read this body")
    assert decision.result.output.safe_path_ref == "filesystem-path:safe-root_test/notes/report.md"
    assert decision.result.output.root_ref == "safe-root:test"
    assert decision.result.output.raw_content_returned is False
    assert decision.result.output.text_preview_returned is False
    assert decision.result.output.content_hash_returned is False
    assert decision.result.output.directory_listing_returned is False
    assert decision.result.output.absolute_path_returned is False
    dumped = decision.model_dump()
    assert "do not read this body" not in str(dumped)
    assert str(safe_root.root_path) not in str(dumped)
    assert "absolute_path" not in dumped["result"]["output"]
    assert "text_preview" not in dumped["result"]["output"]
    assert "content_hash" not in dumped["result"]["output"]


def test_safe_directory_metadata_does_not_list_children(tmp_path):
    safe_root = _safe_root(tmp_path)
    directory = safe_root.root_path / "docs"
    directory.mkdir()
    (directory / "child.md").write_text("child content", encoding="utf-8")

    decision = evaluate_tool_invocation(
        _request(metadata={"root_ref": "safe-root:test", "relative_path": "docs"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.metadata_completed
    assert decision.result is not None
    output = decision.result.output
    assert output.path_kind == "directory"
    assert output.directory_listing_returned is False
    assert "child.md" not in str(decision.model_dump())


def test_adapter_invokes_filesystem_metadata_through_same_policy(tmp_path):
    safe_root = _safe_root(tmp_path)
    (safe_root.root_path / "notes").mkdir()
    (safe_root.root_path / "notes" / "report.md").write_text("metadata only", encoding="utf-8")

    decision = ToolRuntimeAdapter().invoke(_request(), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.metadata_completed
    assert decision.result is not None
    assert decision.result.output.safe_message == "FILESYSTEM_METADATA_RETURNED"


def test_filesystem_metadata_contract_rejects_caller_selected_root(tmp_path):
    safe_root = _safe_root(tmp_path)
    request = FilesystemMetadataRequest(
        request_ref="filesystem-metadata-request:m32",
        root_ref=safe_root.root_ref,
        relative_path="notes/report.md",
        caller_selected_root_path=str(tmp_path),
    )

    decision = evaluate_tool_invocation(
        _request(metadata=request.model_dump()),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "CALLER_SELECTED_ROOT_DENIED" in decision.reason_codes


def test_filesystem_metadata_request_revalidation_denies_model_copy_raw_file(tmp_path):
    safe_root = _safe_root(tmp_path)
    request = _request().model_copy(update={"contains_raw_file_content": True})

    decision = evaluate_tool_invocation(request, safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.denied
    assert "RAW_FILE_CONTENT_DENIED" in decision.reason_codes


def test_symlink_path_is_denied(tmp_path):
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "target.md"
    target.write_text("metadata only", encoding="utf-8")
    link = safe_root.root_path / "link.md"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        return

    decision = evaluate_tool_invocation(
        _request(metadata={"root_ref": "safe-root:test", "relative_path": "link.md"}),
        safe_roots=[safe_root],
    )

    assert decision.status == ToolInvocationStatus.denied
    assert "SYMLINK_DENIED" in decision.reason_codes


def test_no_filesystem_mutation_occurs(tmp_path):
    safe_root = _safe_root(tmp_path)
    target = safe_root.root_path / "notes" / "report.md"
    target.parent.mkdir()
    content = "stable"
    target.write_text(content, encoding="utf-8")
    before_size = os.stat(target).st_size
    before = os.stat(target).st_mtime_ns

    decision = evaluate_tool_invocation(_request(), safe_roots=[safe_root])

    assert decision.status == ToolInvocationStatus.metadata_completed
    assert os.stat(target).st_size == before_size == len(content)
    assert os.stat(target).st_mtime_ns == before
