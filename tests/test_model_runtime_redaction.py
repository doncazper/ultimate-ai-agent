import pytest
from pydantic import ValidationError

from tests.m8_helpers import runtime_request
from ultimate_ai_agent.core.model_runtime import (
    ModelRuntimeOutputFormat,
    ModelRuntimeResponse,
    ModelRuntimeResponseStatus,
    response_is_truth_authority,
)


def test_response_rejects_secret_like_output_and_metadata():
    payload = {
        "runtime_response_id": "mrt_resp_secret",
        "runtime_request_id": "mrt_req_1",
        "run_id": "run_m8",
        "status": ModelRuntimeResponseStatus.simulated_success,
        "output_format": ModelRuntimeOutputFormat.text,
        "output_summary": "password='ABCDEFGHIJKLMNOP'",
        "model_profile_id": "local_coder",
        "adapter_id": "sim_adapter",
    }

    with pytest.raises(ValidationError):
        ModelRuntimeResponse(**payload)

    payload["output_summary"] = "Simulated response for request mrt_req_1; no model was called."
    payload["metadata"] = {"debug": "client_secret='ABCDEFGHIJKLMNOP'"}
    with pytest.raises(ValidationError):
        ModelRuntimeResponse(**payload)


def test_runtime_response_is_not_truth_authority():
    response = ModelRuntimeResponse(
        runtime_response_id="mrt_resp_1",
        runtime_request_id="mrt_req_1",
        run_id="run_m8",
        status=ModelRuntimeResponseStatus.simulated_success,
        output_format=ModelRuntimeOutputFormat.text,
        output_summary="Simulated response for request mrt_req_1; no model was called.",
        model_profile_id="local_coder",
        adapter_id="sim_adapter",
        metadata={"truth_authority": False},
    )

    assert response_is_truth_authority(response) is False


def test_request_secret_like_metadata_rejected():
    with pytest.raises(ValueError, match="secret-like"):
        runtime_request(metadata={"note": "auth_token='ABCDEFGHIJKLMNOP'"})
