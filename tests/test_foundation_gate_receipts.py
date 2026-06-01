from ultimate_ai_agent.core.gate import run_m5_shadow_replay


def test_shadow_replay_exposes_receipt_and_event_refs(tmp_path):
    result = run_m5_shadow_replay(workspace_root=tmp_path)

    assert result.passed is True
    assert result.receipt_ref.startswith("rcpt_")
    assert len(result.event_ids) >= 7
    assert all(event_id.startswith("evt_") for event_id in result.event_ids)
    assert result.failures == []
