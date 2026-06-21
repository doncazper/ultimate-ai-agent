from pathlib import Path

from ultimate_ai_agent.core.gate import (
    default_m5_shadow_replay_scenario,
    run_m5_shadow_replay,
)


def test_shadow_replay_m5_happy_path_captures_events_receipt_and_rollback(tmp_path: Path) -> None:
    result = run_m5_shadow_replay(workspace_root=tmp_path)

    assert result.passed is True
    assert result.final_status == "completed"
    assert result.receipt_ref
    assert result.rollback_verified is True
    assert result.event_ids
    assert result.event_names[:4] == [
        "run.created",
        "execution_contract.created",
        "context_pack.created",
        "tool.call.requested",
    ]
    assert "file.change.applied" in result.event_names
    assert "memory.write.proposed" in result.event_names
    assert (tmp_path / "notes/m5.md").read_text(encoding="utf-8") == "before\n"


def test_shadow_replay_denial_path_does_not_write_file(tmp_path: Path) -> None:
    result = run_m5_shadow_replay(workspace_root=tmp_path, denial_path=True)

    assert result.passed is True
    assert result.final_status == "denied"
    assert result.rollback_verified is False
    assert not (tmp_path / "notes/m5.md").exists()
    assert "tool.call.requested" in result.event_names


def test_shadow_replay_scenario_has_gate_contract_defaults() -> None:
    scenario = default_m5_shadow_replay_scenario()

    assert scenario.scenario_id == "m5_minimum_lovable_kernel_replay"
    assert scenario.requires_rollback is True
    assert scenario.requires_receipt is True
    assert scenario.expected_final_status == "completed"
    assert "file.change.applied" in scenario.expected_event_names
