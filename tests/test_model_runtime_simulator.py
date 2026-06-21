from tests.m8_helpers import runtime_request, simulated_manifest
from ultimate_ai_agent.core.model_runtime import (
    ModelRuntimeOutputFormat,
    ModelRuntimeResponseStatus,
    SimulatedModelRuntimeAdapter,
)


def test_simulated_response_is_deterministic_and_marked_simulated() -> None:
    adapter = SimulatedModelRuntimeAdapter()
    request = runtime_request(output_format=ModelRuntimeOutputFormat.text)
    manifest = simulated_manifest()

    first = adapter.simulate_response(request, manifest)
    second = adapter.simulate_response(request, manifest)

    assert first == second
    assert first.status == ModelRuntimeResponseStatus.simulated_success
    assert "Simulated response" in first.output_summary
    assert "no model was called" in first.output_summary


def test_simulated_json_and_structured_outputs_are_safe() -> None:
    adapter = SimulatedModelRuntimeAdapter()

    json_response = adapter.simulate_response(runtime_request(output_format=ModelRuntimeOutputFormat.json), simulated_manifest())
    structured_response = adapter.simulate_response(runtime_request(output_format=ModelRuntimeOutputFormat.structured), simulated_manifest())

    assert json_response.structured_output["simulated"] is True
    assert structured_response.structured_output["runtime_request_id"] == "mrt_req_1"
    assert "prompt" not in str(json_response.model_dump()).lower()


def test_simulated_refusal_uses_refusal_status() -> None:
    response = SimulatedModelRuntimeAdapter().simulate_response(
        runtime_request(output_format=ModelRuntimeOutputFormat.refusal),
        simulated_manifest(),
    )

    assert response.status == ModelRuntimeResponseStatus.simulated_refusal
    assert response.refusal_reason == "SIMULATED_REFUSAL_REQUESTED"


def test_preview_does_not_call_model_and_returns_safe_plan() -> None:
    preview = SimulatedModelRuntimeAdapter().preview(runtime_request(), simulated_manifest())

    assert preview.success is True
    assert preview.data["simulated"] is True
    assert preview.data["would_call_model"] is False
    assert preview.data["would_call_network"] is False
