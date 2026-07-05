import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.local_model_management import (
    FakeM163ProcessFactory,
    FakeM164GatewayTransport,
    LocalModelE2ESmokePrerequisites,
    LocalModelE2ESmokeStatus,
    LocalModelE2ESmokeStep,
    run_local_model_e2e_smoke_harness,
)
from ultimate_ai_agent.core.openwebui_bridge import (
    DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY,
    UAA_OPENWEBUI_TEST_GATEWAY_ENV,
    UAA_OPENWEBUI_TEST_MODEL_ID,
)


client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY}",
        "X-UAA-Idempotency-Key": "idempotency:m151-openwebui",
    }


def test_m151_models_endpoint_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, raising=False)

    response = client.get("/v1/models", headers=_auth_headers())

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_m151_models_endpoint_requires_local_bearer_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_m151_models_endpoint_returns_safe_openai_compatible_model_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")

    response = client.get("/v1/models", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "list"
    assert body["data"][0]["id"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert body["uaa_safety"]["provider_call_enabled"] is False
    assert body["uaa_safety"]["tool_execution_enabled"] is False


def test_m151_chat_completion_returns_deterministic_safe_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")
    secret_like_prompt = "token=should-not-appear"

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": secret_like_prompt}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert "should-not-appear" not in response.text
    assert body["uaa_safety"]["raw_prompt_logged"] is False
    assert body["uaa_safety"]["provider_called"] is False
    assert body["uaa_safety"]["tool_executed"] is False
    assert body["uaa_safety"]["memory_written"] is False
    assert body["uaa_safety"]["context_injected"] is False
    assert body["uaa_safety"]["external_network_called"] is False
    binding = body["uaa_safety"]["turn_harness_binding"]
    assert binding["raw_prompt_persisted"] is False
    assert binding["raw_response_persisted"] is False
    assert binding["no_effect_scope"] == "turn_harness_binding_compilation_only"
    assert binding["no_tool_execution_performed"] is True
    assert binding["no_action_execution_performed"] is True


def test_m151_chat_completion_rejects_streaming_and_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")
    secret_like_prompt = "token=should-not-appear"

    streaming_response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "stream": True,
            "messages": [{"role": "user", "content": secret_like_prompt}],
        },
    )
    tool_response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": "hello"}],
            "tools": [{"type": "function", "function": {"name": "unsafe"}}],
        },
    )

    assert streaming_response.status_code == 422
    assert tool_response.status_code == 422
    assert "should-not-appear" not in streaming_response.text
    assert secret_like_prompt not in streaming_response.text


def test_p0_005_local_model_e2e_smoke_harness_passes_with_reviewed_prereqs() -> None:
    process_factory = FakeM163ProcessFactory()

    report = run_local_model_e2e_smoke_harness(
        LocalModelE2ESmokePrerequisites(
            approved_gguf_ref="gguf-artifact:p0-005-approved",
            reviewer_ref="review-ref:p0-005-local",
            llama_cpp_lifecycle_allowed=True,
            llama_server_path_hint="llama-server",
            model_path_hint="model.gguf",
        ),
        process_factory=process_factory,
        gateway_transport=FakeM164GatewayTransport("smoke harness response"),
    )

    assert report.status == LocalModelE2ESmokeStatus.passed
    assert {step.step for step in report.step_results} == set(LocalModelE2ESmokeStep)
    assert all(step.status == LocalModelE2ESmokeStatus.passed for step in report.step_results)
    assert process_factory.process.terminated is True
    assert report.authority_gate_ref == "checkpoint:m166"
    assert report.source_checkpoint_ref == "checkpoint:m167"
    assert report.redacted_summary_only is True
    assert report.safe_refs_only is True
    assert report.local_dev_only is True
    assert report.loopback_only is True
    assert report.openwebui_shell_only is True
    assert report.m166_exact_scope_bound is True
    assert report.tools_enabled is False
    assert report.functions_enabled is False
    assert report.streaming_enabled is False
    assert report.new_production_authority_granted is False
    assert report.public_distribution_claimed is False
    assert report.raw_prompt_exported is False
    assert report.raw_response_exported is False
    assert report.raw_provider_payload_exported is False
    assert report.raw_log_exported is False
    assert report.raw_path_exported is False
    assert report.credential_material_exported is False
    assert report.side_effect_refs == [
        "side-effect-ref:p0-005:llama-cpp-lifecycle-started",
        "side-effect-ref:p0-005:llama-cpp-lifecycle-stopped",
    ]
    assert "local smoke request sample" not in report.model_dump_json()
    assert "smoke harness response" not in report.model_dump_json()


def test_p0_005_local_model_e2e_smoke_harness_skips_missing_prereqs_safely() -> None:
    report = run_local_model_e2e_smoke_harness()
    statuses_by_step = {step.step: step.status for step in report.step_results}

    assert report.status == LocalModelE2ESmokeStatus.skipped
    assert statuses_by_step[LocalModelE2ESmokeStep.approved_gguf_readiness] == (
        LocalModelE2ESmokeStatus.skipped
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.llama_cpp_supervisor] == (
        LocalModelE2ESmokeStatus.skipped
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.v1_models] == (
        LocalModelE2ESmokeStatus.skipped
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.v1_chat_completions] == (
        LocalModelE2ESmokeStatus.skipped
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.openwebui_shell_compatibility] == (
        LocalModelE2ESmokeStatus.passed
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.auth_failure] == (
        LocalModelE2ESmokeStatus.passed
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.safe_failure] == (
        LocalModelE2ESmokeStatus.passed
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.tools_functions_streaming_denial] == (
        LocalModelE2ESmokeStatus.passed
    )
    assert report.skipped_refs
    assert report.blocker_refs == []
    assert report.side_effect_refs == []
    assert report.new_production_authority_granted is False


def test_p0_005_local_model_e2e_smoke_harness_blocks_incomplete_lifecycle() -> None:
    report = run_local_model_e2e_smoke_harness(
        LocalModelE2ESmokePrerequisites(
            approved_gguf_ref="gguf-artifact:p0-005-approved",
            llama_cpp_lifecycle_allowed=True,
        )
    )
    statuses_by_step = {step.step: step.status for step in report.step_results}

    assert report.status == LocalModelE2ESmokeStatus.blocked
    assert statuses_by_step[LocalModelE2ESmokeStep.approved_gguf_readiness] == (
        LocalModelE2ESmokeStatus.passed
    )
    assert statuses_by_step[LocalModelE2ESmokeStep.llama_cpp_supervisor] == (
        LocalModelE2ESmokeStatus.blocked
    )
    assert "blocker-ref:p0-005:llama-cpp-runtime-hints-missing" in report.blocker_refs
    assert report.rollback_plan_ref == "rollback-ref:p0-005:known-good-local-model"
    assert report.side_effect_refs == []
