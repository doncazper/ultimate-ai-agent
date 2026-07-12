import argparse
import json
import os
from pathlib import Path

import pytest

from scripts.dev.uaa_runtime_mission_completion import (
    export_portable,
    inspect,
    read_bounded_regular_file,
    verify_portable,
)
from tests.test_founder_loop_filesystem_mission import _service_fixture
from ultimate_ai_agent.api.routes import runtime_pilot_service


def _complete_one(tmp_path: Path):
    service, approval_authority, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="completion-surfaces",
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:completion-surfaces",
    )
    result = service.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:completion-surfaces",
    )
    return service, result


def test_completion_api_and_cli_expose_the_same_backend_owned_truth(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    service, result = _complete_one(tmp_path)
    state_dir = service.orchestrator.step_store.state_dir
    monkeypatch.setattr(runtime_pilot_service, "authority_state_dir", lambda: state_dir)

    envelope = runtime_pilot_service.get_api_runtime_authority_missions_completions()
    cli_status = inspect(argparse.Namespace(state_dir=str(state_dir), json=False))
    cli_output = capsys.readouterr().out

    assert envelope.success is True
    assert envelope.operation == "api_runtime_authority_missions_completions"
    assert envelope.data is not None
    assert envelope.data["completion_count"] == 1
    assert (
        envelope.data["latest_manifests"][0]["completion_ref"]
        == result.completion.completion_ref
    )
    assert envelope.data["execution_available_from_read_model"] is False
    assert envelope.data["approval_or_lease_minted"] is False
    integrity = envelope.data["integrity_summary"]
    assert integrity["hash_chain_verified"] is True
    assert integrity["signature_present"] is False
    assert integrity["source_ledgers_verified"] is False
    assert integrity["cryptographic_authenticity_verified"] is False
    assert integrity["external_anchor_verified"] is False
    portable = envelope.data["portable_evidence_summary"]
    assert portable["status"] == "verified_local_hash_chain"
    assert portable["source_receipts_bound"] is True
    assert portable["source_ledgers_verified"] is False
    assert portable["caller_expected_binding_matched"] is False
    assert portable["external_anchor_verified"] is False
    assert cli_status == 0
    assert "Authority mission completions" in cli_output
    assert result.completion.completion_ref in cli_output
    assert "Inspection grants execution authority: false" in cli_output
    assert "Request-scoped authority still required: true" in cli_output
    assert "Completion integrity: local SHA-256 hash chain verified" in cli_output
    assert "Portable evidence: verified_local_hash_chain" in cli_output
    assert "Portable source records bound: true" in cli_output
    assert "Cryptographic signing: blocked" in cli_output
    assert "Authenticity or external anchoring verified: false" in cli_output

    json_status = inspect(argparse.Namespace(state_dir=str(state_dir), json=True))
    json_output = json.loads(capsys.readouterr().out)
    assert json_status == 0
    assert json_output["authority_mission_completions"] == envelope.data
    manifest = json_output["authority_mission_completions"]["latest_manifests"][0]
    assert manifest["dispatch_bindings"] == envelope.data["latest_manifests"][0][
        "dispatch_bindings"
    ]
    assert manifest["approval_validation_refs"]


def test_completion_api_fails_closed_on_corrupt_local_ledger(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "corrupt-completion"
    state_dir.mkdir()
    (state_dir / "mission_completion_receipts.jsonl").write_text(
        "not-json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_pilot_service, "authority_state_dir", lambda: state_dir)

    envelope = runtime_pilot_service.get_api_runtime_authority_missions_completions()

    assert envelope.success is False
    assert envelope.error is not None
    assert envelope.error.code == "MISSION_COMPLETION_INSPECTION_UNAVAILABLE"
    assert envelope.error.details_redacted is True


def test_portable_evidence_cli_export_and_offline_verify(
    tmp_path: Path,
    capsys,
) -> None:
    service, _result = _complete_one(tmp_path)
    state_dir = service.orchestrator.step_store.state_dir

    assert export_portable(argparse.Namespace(state_dir=str(state_dir))) == 0
    exported = capsys.readouterr().out
    payload = json.loads(exported)
    assert payload["signature_present"] is False
    assert payload["source_ledgers_verified"] is False
    assert payload["execution_evidence_grants_authority"] is False

    bundle_path = tmp_path / "portable-evidence.json"
    bundle_path.write_text(exported, encoding="utf-8")
    status = verify_portable(
        argparse.Namespace(
            input=str(bundle_path),
            expected_bundle_ref=payload["bundle_ref"],
            expected_envelope_count=payload["envelope_count"],
            json=False,
        )
    )
    output = capsys.readouterr().out
    assert status == 0
    assert "Valid local hash chain: true" in output
    assert "Caller-supplied expected binding matched: true" in output
    assert "External anchor verified: false" in output
    assert "Cryptographic signature verified: false" in output
    assert "Evidence grants execution authority: false" in output


def test_portable_evidence_reader_rejects_unsafe_files(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}", encoding="utf-8")

    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(source)
    with pytest.raises(OSError):
        read_bounded_regular_file(symlink)

    hardlink = tmp_path / "hardlink.json"
    os.link(source, hardlink)
    with pytest.raises(ValueError, match="PORTABLE_EVIDENCE_INPUT_UNSAFE"):
        read_bounded_regular_file(source)

    fifo = tmp_path / "fifo.json"
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match="PORTABLE_EVIDENCE_INPUT_UNSAFE"):
        read_bounded_regular_file(fifo)

    oversized = tmp_path / "oversized.json"
    with oversized.open("wb") as stream:
        stream.truncate((4 * 1024 * 1024) + 1)
    with pytest.raises(ValueError, match="PORTABLE_EVIDENCE_INPUT_UNSAFE"):
        read_bounded_regular_file(oversized)
