from pathlib import Path

from ultimate_ai_agent.core.recall import GroundedRecallDecision


def test_grounded_recall_decision_records_no_memory_write():
    decision = GroundedRecallDecision(
        decision_id="recall:decision:no-write",
        request_id="recall:req:no-write",
        selected=[],
        excluded=[],
        reason_codes=["NO_ELIGIBLE_RECALL_CANDIDATES"],
        safe_message="No eligible recall candidates were selected.",
    )

    assert decision.no_memory_write_performed is True


def test_recall_module_does_not_import_memory_store_or_write_requests():
    recall_root = Path("src/ultimate_ai_agent/core/recall")
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in recall_root.glob("*.py"))

    assert "localmemorystore" not in source
    assert "memorywriterequest" not in source
    assert "put_record(" not in source
    assert "write_memory(" not in source
