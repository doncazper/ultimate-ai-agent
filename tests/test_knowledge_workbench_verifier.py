from scripts.verify_queue_v2_q18_knowledge_workbench import verify


def test_q18_knowledge_workbench_verifier() -> None:
    assert verify() == []
