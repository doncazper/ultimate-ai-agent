from __future__ import annotations

from scripts import verify_msg_mx_012_messenger_acceptance as verifier


def test_msg_mx_012_canonical_verifier_passes() -> None:
    assert verifier.verify() == []


def test_msg_mx_012_packet_rejects_missing_and_duplicate_matrix_rows() -> None:
    text = verifier.PACKET.read_text(encoding="utf-8")
    missing = text.replace("| `MSG-MX-006` |", "| `MSG-MX-X06` |", 1)
    assert "MSG-MX-012 milestone matrix is incomplete or duplicated" in (
        verifier.verify_packet_text(missing)
    )

    surface_row = next(
        line for line in text.splitlines() if line.startswith("| `COMMS-MX-15` |")
    )
    duplicated = f"{text}\n{surface_row}\n"
    assert "MSG-MX-012 desktop surface matrix is incomplete or duplicated" in (
        verifier.verify_packet_text(duplicated)
    )


def test_msg_mx_012_packet_rejects_missing_state_and_durable_path() -> None:
    text = verifier.PACKET.read_text(encoding="utf-8")
    missing_state = text.replace("`unsupported`", "not-supported")
    assert "MSG-MX-012 state vocabulary missing: unsupported" in (
        verifier.verify_packet_text(missing_state)
    )
    with_path = f"{text}\n/private marker: /Users/example/private\n"
    assert any(
        "packet contains forbidden durable data" in failure
        for failure in verifier.verify_packet_text(with_path)
    )
