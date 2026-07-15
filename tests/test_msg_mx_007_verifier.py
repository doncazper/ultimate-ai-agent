from scripts.verify_msg_mx_007_matrix_crypto import ROOT, verify


def test_msg_mx_007_verifier_passes() -> None:
    assert verify(ROOT) == []
