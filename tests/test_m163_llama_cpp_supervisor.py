from typing import Any
import pytest

from ultimate_ai_agent.core.local_model_management import (
    FakeM163ProcessFactory,
    M163LlamaCppServerPreset,
    M163LlamaCppSupervisor,
    build_m163_llama_server_argv,
    validate_m163_llama_cpp_server_preset,
    validate_m163_llama_cpp_supervisor_result,
)


def _preset(**overrides: Any) -> Any:
    data = {
        "preset_ref": "llama-cpp-preset:m163-test",
        "llama_server_path": "/opt/uaa/bin/llama-server",
        "model_path": "/tmp/uaa-model-cache/model.gguf",
        "port": 18080,
    }
    data.update(overrides)
    return M163LlamaCppServerPreset(**data)


def test_m163_builds_structured_loopback_argv_without_shell_string() -> None:
    argv, api_key_handle, api_key_secret = build_m163_llama_server_argv(_preset())

    assert argv[0].endswith("llama-server")
    assert "--host" in argv
    assert "127.0.0.1" in argv
    assert "--model" in argv
    assert "/tmp/uaa-model-cache/model.gguf" in argv
    assert api_key_handle == "local-api-key-handle:m163-llama-cpp-preset-m163-test"
    assert api_key_secret
    assert all("\n" not in item for item in argv)


def test_m163_supervisor_uses_process_factory_and_redacts_result() -> None:
    factory = FakeM163ProcessFactory()
    supervisor = M163LlamaCppSupervisor(process_factory=factory)

    result = supervisor.start(_preset())
    payload = result.model_dump_json()

    assert factory.argv is not None
    assert factory.env is not None
    assert factory.env["HF_HUB_OFFLINE"] == "1"
    assert "UAA_LLAMA_CPP_API_KEY" in factory.env
    assert result.process_started is True
    assert result.server_started is True
    assert result.subprocess_execution_performed is True
    assert result.shell_string_used is False
    assert result.loopback_only is True
    assert result.raw_log_stored is False
    assert result.raw_path_returned is False
    assert "model.gguf" not in payload
    assert factory.env["UAA_LLAMA_CPP_API_KEY"] not in payload


def test_m163_supervisor_stop_terminates_managed_process() -> None:
    factory = FakeM163ProcessFactory()
    supervisor = M163LlamaCppSupervisor(process_factory=factory)
    supervisor.start(_preset())

    supervisor.stop()

    assert factory.process.terminated is True


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"host": "0.0.0.0"}, "M163_LOOPBACK_ONLY_REQUIRED"),
        ({"shell_string_allowed": True}, "M163_SHELL_STRING_DENIED"),
        ({"model_path": "/tmp/model.bin"}, "M163_GGUF_MODEL_REQUIRED"),
    ],
)
def test_m163_preset_rejects_unsafe_shape(update: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_m163_llama_cpp_server_preset(_preset(**update))


def test_m163_result_validation_rejects_unsafe_mutation() -> None:
    result = M163LlamaCppSupervisor(process_factory=FakeM163ProcessFactory()).start(_preset())

    with pytest.raises(ValueError, match="M163_RAW_LOG_STORAGE_DENIED"):
        validate_m163_llama_cpp_supervisor_result(result.model_copy(update={"raw_log_stored": True}))
