import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.runtime_readiness import (
    ManualSmokeReport,
    SmokeReportStatus,
    validate_manual_smoke_report,
)


def safe_report_payload(**overrides):
    payload = {
        "report_id": "manual_smoke_report_001",
        "run_id": "run_001",
        "smoke_request_id": "smoke_req_001",
        "endpoint_summary": "loopback host localhost; no query; no credentials",
        "model_id_summary": "local-smoke-model",
        "response_origin": "fake_manual_loopback_smoke",
        "fixed_prompt_hash": "sha256:0123456789abcdef0123456789abcdef",
        "response_marker_found": True,
        "response_preview": "UAA_LOCAL_SMOKE_OK",
        "response_body_sha256": "sha256:abcdef0123456789abcdef0123456789",
        "elapsed_ms": 3,
        "model_output_authoritative": False,
        "metadata": {
            "manual_only": True,
            "no_model_truth_authority": True,
            "no_provider_call": True,
        },
    }
    payload.update(overrides)
    return payload


def test_safe_manual_smoke_report_is_accepted():
    validation = validate_manual_smoke_report(safe_report_payload())

    assert validation.allowed is True
    assert validation.status == SmokeReportStatus.valid
    assert validation.reason_codes == ["MANUAL_SMOKE_REPORT_SAFE"]


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"fixed_prompt_hash": ""}, "FIXED_PROMPT_HASH_REQUIRED"),
        ({"response_preview": "api_key='abcdefghijklmnop'"}, "SECRET_LIKE_VALUE_REJECTED"),
        ({"endpoint_summary": "https://api.example.com/v1/chat"}, "REMOTE_ENDPOINT_SUMMARY_REJECTED"),
        ({"endpoint_summary": "http://localhost:11434?api_key=secret"}, "ENDPOINT_QUERY_SECRET_REJECTED"),
        ({"metadata": {"claim": "cloud provider model call executed"}}, "CLOUD_PROVIDER_EXECUTION_CLAIM_REJECTED"),
        ({"metadata": {"claim": "remote execution completed"}}, "REMOTE_EXECUTION_CLAIM_REJECTED"),
        ({"metadata": {"claim": "live tailnet headscale wireguard connected"}}, "LIVE_MESH_CLAIM_REJECTED"),
        ({"metadata": {"claim": "mobile camera sensor enabled"}}, "MOBILE_SENSOR_CLAIM_REJECTED"),
        ({"metadata": {"claim": "xcode build plugin enabled"}}, "PLUGIN_OR_BUILD_TOOL_CLAIM_REJECTED"),
        ({"model_output_authoritative": True}, "MODEL_OUTPUT_AUTHORITY_REJECTED"),
    ],
)
def test_manual_smoke_report_rejects_unsafe_claims(overrides, reason):
    validation = validate_manual_smoke_report(safe_report_payload(**overrides))

    assert validation.allowed is False
    assert reason in validation.reason_codes
    assert "abcdefghijklmnop" not in validation.safe_message


def test_manual_smoke_report_forbids_raw_prompt_and_full_body_fields():
    with pytest.raises(ValidationError):
        ManualSmokeReport(**safe_report_payload(raw_prompt="summarize my private file"))

    validation = validate_manual_smoke_report(
        safe_report_payload(response_body="full model response should not be accepted")
    )
    assert validation.allowed is False
    assert "REPORT_SCHEMA_INVALID" in validation.reason_codes
