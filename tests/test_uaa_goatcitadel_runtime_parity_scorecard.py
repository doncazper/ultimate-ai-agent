from pathlib import Path

from scripts.verify_uaa_goatcitadel_runtime_parity_scorecard import DEFAULT_REPORT, verify


def test_runtime_parity_scorecard_verifier_passes() -> None:
    assert verify(DEFAULT_REPORT) == []


def test_runtime_parity_scorecard_keeps_blocked_authority_visible() -> None:
    text = Path(DEFAULT_REPORT).read_text(encoding="utf-8")

    for phrase in (
        "provider SDK calls",
        "browser automation",
        "connector writes",
        "unrestricted shell/subprocess execution",
        "production authority",
        "broad autonomy",
    ):
        assert phrase in text

    assert "not copied from GoatCitadel" in text
    assert "does not change Control Center behavior" in text
