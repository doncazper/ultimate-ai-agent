"""Regression tests for consistent content hashing across read and write paths.

build_file_ref/read_preview previously hashed the raw on-disk bytes while
propose_write computed the existing-file hash from the decoded text
(read_text applies universal-newline translation). For any file containing
CRLF line endings the two hashes disagreed, so an optimistic-concurrency
write whose ``expected_existing_hash`` came from build_file_ref/read_preview
was spuriously rejected with EXPECTED_HASH_MISMATCH even though nothing had
changed. These tests pin a single, consistent hash across both paths.
"""

from pathlib import Path

from ultimate_ai_agent.core.files import (
    FileKind,
    FileSensitivity,
    FileReadRequest,
    FileWriteProposal,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def test_read_path_hash_matches_write_path_for_crlf_file(tmp_path: Path):
    target = tmp_path / "crlf.txt"
    # Write explicit CRLF bytes regardless of host platform.
    target.write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")
    manager = LocalFileManager(workspace_root=tmp_path)

    ref_hash = manager.build_file_ref("crlf.txt").content_hash
    preview_hash = manager.read_preview(
        FileReadRequest(
            request_id="frr_crlf",
            run_id="run_123",
            actor_context=_actor(),
            path="crlf.txt",
            purpose="hash check",
            max_bytes=4096,
        )
    ).content_hash

    # Read paths agree with one another...
    assert ref_hash == preview_hash

    # ...and an optimistic-lock write using that hash is NOT rejected as a
    # mismatch (it would be under the old raw-byte read-path hash).
    proposal = FileWriteProposal(
        proposal_id="fwp_crlf",
        run_id="run_123",
        actor_context=_actor(),
        target_path="crlf.txt",
        purpose="optimistic update",
        new_content="alpha\nbeta\ngamma\nrevised\n",
        expected_existing_hash=ref_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_crlf",
    )
    decision = manager.propose_write(proposal)

    assert "EXPECTED_HASH_MISMATCH" not in decision.reason_codes
    assert decision.allowed is True


def test_stale_expected_hash_still_detected(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_bytes(b"current contents\n")
    manager = LocalFileManager(workspace_root=tmp_path)

    proposal = FileWriteProposal(
        proposal_id="fwp_stale",
        run_id="run_123",
        actor_context=_actor(),
        target_path="note.txt",
        purpose="optimistic update",
        new_content="new contents\n",
        expected_existing_hash="0" * 64,  # deliberately wrong
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_stale",
    )
    decision = manager.propose_write(proposal)

    assert decision.allowed is False
    assert "EXPECTED_HASH_MISMATCH" in decision.reason_codes
