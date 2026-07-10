from __future__ import annotations

from scripts.inspect_firecrawl_cloud_credits import (
    inspect_cloud_credit_payload,
    main,
    render_summary,
)
from tests.test_firecrawl_cloud import NOW, _credential, _credit_payload


def test_cli_and_core_share_safe_credit_truth_without_secret_or_raw_payload() -> None:
    credential = _credential()
    payload = inspect_cloud_credit_payload(
        credential=credential,
        transport=lambda _credential: _credit_payload(remaining=9),
        fetched_at=NOW,
    )
    summary = render_summary(payload)

    assert payload["status"] == "simulated"
    assert payload["plan_kind"] == "free"
    assert payload["remaining_credits"] == 9
    assert payload["paid_usage_allowed"] is False
    assert payload["credential_material_returned"] is False
    assert payload["raw_provider_payload_returned"] is False
    assert credential.value.get_secret_value() not in str(payload)
    assert credential.value.get_secret_value() not in summary
    assert "providerPrivateField" not in str(payload)
    assert "exact approval" in summary
    assert "{" not in summary


def test_cli_missing_credential_emits_only_safe_code(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    missing = tmp_path / ".uaa/local-web-services/firecrawl_cloud_api_key"

    assert main(["--secret-file", str(missing)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == (
        "Firecrawl Cloud credit inspection blocked: "
        "FIRECRAWL_CLOUD_INSPECTION_BLOCKED"
    )
    assert str(tmp_path) not in captured.err
    assert ".venv" not in captured.err
