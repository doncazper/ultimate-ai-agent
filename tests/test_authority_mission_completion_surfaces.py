import argparse
import json
from pathlib import Path

from scripts.dev.uaa_runtime_mission_completion import inspect
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
    assert cli_status == 0
    assert "Authority mission completions" in cli_output
    assert result.completion.completion_ref in cli_output
    assert "Inspection grants execution authority: false" in cli_output
    assert "Request-scoped authority still required: true" in cli_output

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
