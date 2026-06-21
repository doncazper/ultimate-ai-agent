from tests.m8_helpers import runtime_request, simulated_manifest
from ultimate_ai_agent.core.model_runtime import SimulatedModelRuntimeAdapter, runtime_event_metadata


def test_runtime_event_metadata_is_receipt_safe_and_secret_free() -> None:
    response = SimulatedModelRuntimeAdapter().simulate_response(runtime_request(), simulated_manifest())
    metadata = runtime_event_metadata(runtime_request(), response)

    assert metadata["event_name"] == "model.runtime.simulated"
    assert metadata["runtime_request_id"] == "mrt_req_1"
    assert metadata["runtime_response_id"] == response.runtime_response_id
    assert metadata["simulated"] is True
    assert "prompt_summary" not in metadata
    assert "secret" not in str(metadata).lower()
