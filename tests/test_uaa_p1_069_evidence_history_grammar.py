from scripts.verify_uaa_p1_069_evidence_history_grammar import main


def test_uaa_p1_069_evidence_history_grammar_verifier_passes() -> None:
    assert main() == 0
