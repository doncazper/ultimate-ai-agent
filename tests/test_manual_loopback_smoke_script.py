import pytest
import json

from tests.m10_helpers import approval_for_smoke, smoke_request
from ultimate_ai_agent.core.model_runtime import FakeManualLoopbackSmokeTransport
from scripts import local_loopback_smoke


def test_script_requires_explicit_enable_flag(capsys: pytest.CaptureFixture[str]) -> None:
    code = local_loopback_smoke.main(
        [
            "--endpoint",
            "http://127.0.0.1:11434/api/generate",
            "--model",
            "local-smoke-model",
            "--approval-ref",
            "approval_m10",
        ],
        transport=FakeManualLoopbackSmokeTransport(),
    )

    output = capsys.readouterr().out
    assert code != 0
    assert "ENABLE_MANUAL_LOCAL_SMOKE_REQUIRED" in output


def test_script_rejects_remote_endpoint(capsys: pytest.CaptureFixture[str]) -> None:
    code = local_loopback_smoke.main(
        [
            "--endpoint",
            "http://example.com/api/generate",
            "--model",
            "local-smoke-model",
            "--approval-ref",
            "approval_m10",
            "--enable-manual-local-smoke",
        ],
        transport=FakeManualLoopbackSmokeTransport(),
    )

    output = capsys.readouterr().out
    assert code != 0
    assert "MODEL_RUNTIME_VALIDATION_FAILED" in output or "NON_LOOPBACK_HOST_DENIED" in output


def test_script_uses_fixed_prompt_and_fake_transport_with_valid_grant(capsys: pytest.CaptureFixture[str]) -> None:
    request = smoke_request()
    _, _, grant, _ = approval_for_smoke(request)
    code = local_loopback_smoke.main(
        [
            "--endpoint",
            request.endpoint.base_url,
            "--model",
            request.model_id,
            "--approval-ref",
            grant.approval_ref,
            "--enable-manual-local-smoke",
            "--approval-grant-json",
            grant.model_dump_json(),
        ],
        transport=FakeManualLoopbackSmokeTransport(),
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 0
    assert payload["success"] is True
    assert payload["response_preview"] == "UAA_LOCAL_SMOKE_OK"
    assert "fixed_prompt" not in payload
