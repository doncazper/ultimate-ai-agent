from ultimate_ai_agent.core.gate import run_m5_shadow_replay


def test_shadow_replay_verifies_rollback_restores_previous_content(tmp_path):
    target = tmp_path / "notes/m5.md"

    result = run_m5_shadow_replay(workspace_root=tmp_path)

    assert result.rollback_verified is True
    assert target.read_text(encoding="utf-8") == "before\n"
    assert result.final_status == "completed"
