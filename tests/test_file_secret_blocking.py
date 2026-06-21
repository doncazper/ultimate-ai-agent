from typing import Any
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.files import (
    FileKind,
    FileOperationStatus,
    FilePatchProposal,
    FileReadRequest,
    FileSensitivity,
    FileWriteProposal,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.secrets import SecretBroker


def _actor() -> Any:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _synthetic_secret_value(prefix: str = "synthetic") -> str:
    return prefix + "_" + "".join(["A"] * 18)


def _synthetic_access_key() -> str:
    return "".join(["A", "K", "I", "A"]) + "".join(["Z"] * 16)


def _private_key_header() -> str:
    return "-----BEGIN " + "OPENSSH " + "PRIVATE KEY-----"


def _write_proposal(path: str, content: str, **kwargs: Any) -> FileWriteProposal:
    return FileWriteProposal(
        proposal_id=kwargs.pop("proposal_id", "fwp_secret_blocking"),
        run_id="run_123",
        actor_context=_actor(),
        target_path=path,
        purpose="secret blocking",
        new_content=content,
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_secret_blocking"),
        **kwargs,
    )


def _patch_proposal(manager: LocalFileManager, path: str, content: str, **kwargs: Any) -> FilePatchProposal:
    return FilePatchProposal(
        proposal_id=kwargs.pop("proposal_id", "file-patch-proposal:secret-blocking"),
        run_id="run_123",
        actor_context=_actor(),
        file_ref=kwargs.pop("file_ref", manager.build_file_ref(path).file_ref),
        target_path=path,
        purpose="secret blocking patch",
        new_content=content,
        expected_existing_hash=kwargs.pop("expected_existing_hash", manager.build_file_ref(path).content_hash),
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_patch_secret_blocking"),
        audit_ref=kwargs.pop("audit_ref", "file-patch-audit:secret-blocking"),
        **kwargs,
    )


def _read_request(path: str) -> FileReadRequest:
    return FileReadRequest(
        request_id="file-read-secret-preview",
        run_id="run_123",
        actor_context=_actor(),
        path=path,
        purpose="redacted preview",
        max_bytes=4096,
    )


def test_private_key_write_is_blocked(tmp_path: Path) -> None:
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = _write_proposal(
        "id_rsa",
        _private_key_header(),
        proposal_id="fwp_private_key",
        sensitivity=FileSensitivity.credential_secret,
        idempotency_key="idem_key",
    )

    decision = manager.propose_write(proposal)

    assert decision.allowed is False
    assert "FILE_PATH_BLOCKED" in decision.reason_codes or "SECRET_CONTENT_BLOCKED" in decision.reason_codes


@pytest.mark.parametrize(
    "content",
    [
        lambda: "api_key: '" + _synthetic_secret_value("api") + "'",
        lambda: "Authorization: Bearer " + _synthetic_secret_value("bearer"),
        lambda: "cloud_access_key=" + _synthetic_access_key(),
        lambda: _private_key_header(),
    ],
)
def test_patch_proposal_blocks_common_secret_like_patterns(tmp_path: Path, content: str) -> None:
    secret_like_content = content()
    target = tmp_path / "note.txt"
    target.write_text("safe text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_patch(_patch_proposal(manager, "note.txt", secret_like_content))

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "PATCH_DIFF_CONTENT_BLOCKED" in decision.reason_codes
    assert "secret_value" in decision.redactions_applied
    assert decision.preview_ref is None
    assert decision.preview_summary is not None
    assert "raw_diff_omitted=True" in decision.preview_summary
    assert secret_like_content not in decision.model_dump_json()
    assert SecretBroker().validate_no_secret_leak(decision.model_dump()) is True


def test_redacted_preview_masks_secret_like_content(tmp_path: Path) -> None:
    secret_value = _synthetic_secret_value("preview")
    target = tmp_path / "note.txt"
    target.write_text("auth_token: '" + secret_value + "'\npublic summary\n", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.read_preview(_read_request("note.txt"))

    assert "secret_value" in preview.redactions_applied
    assert "[REDACTED_SECRET]" in preview.text_preview
    assert secret_value not in preview.model_dump_json()


def test_secret_like_patch_cannot_be_submitted_for_approval_or_applied(tmp_path: Path) -> None:
    secret_value = _synthetic_secret_value("blocked")
    target = tmp_path / "note.txt"
    target.write_text("safe text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = _patch_proposal(manager, "note.txt", "token: '" + secret_value + "'")

    with pytest.raises(ValueError, match="blocked"):
        manager.approval_request_for_patch(patch)

    blocked_apply = manager.apply_patch_proposal(
        patch.model_copy(update={"approval_ref": "approval:file-patch-secret-denied"}),
        approval_authority=LocalApprovalAuthority(),
    )

    assert blocked_apply.allowed is False
    assert blocked_apply.status == FileOperationStatus.blocked
    assert "PATCH_DIFF_CONTENT_BLOCKED" in blocked_apply.reason_codes
    assert target.read_text(encoding="utf-8") == "safe text"
    assert secret_value not in blocked_apply.model_dump_json()


def test_safe_placeholder_and_planning_text_do_not_trigger_secret_block(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("safe text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    content = "token budget remains bounded\napi_key: example-placeholder-value\n"

    decision = manager.propose_patch(_patch_proposal(manager, "note.txt", content))

    assert decision.allowed is True
    assert decision.status == FileOperationStatus.proposed
    assert decision.preview_ref is not None
    assert decision.preview_summary is not None
    assert content not in decision.model_dump_json()


def test_existing_secret_like_diff_is_blocked_without_echoing_value(tmp_path: Path) -> None:
    secret_value = _synthetic_secret_value("existing")
    target = tmp_path / "note.txt"
    target.write_text("password: '" + secret_value + "'\n", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_patch(_patch_proposal(manager, "note.txt", "safe replacement"))

    assert decision.allowed is False
    assert "PATCH_DIFF_CONTENT_BLOCKED" in decision.reason_codes
    assert decision.preview_summary is not None
    assert secret_value not in decision.model_dump_json()
