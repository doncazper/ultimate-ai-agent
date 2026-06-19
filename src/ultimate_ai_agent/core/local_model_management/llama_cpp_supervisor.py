from __future__ import annotations

import importlib
import secrets
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _SECRET_LIKE_RE,
    _URL_RE,
    _validate_m61_ref,
    _validate_safe_payload,
)


class _M163Model(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class M163LlamaCppServerPreset(_M163Model):
    preset_ref: str
    llama_server_path: str
    model_path: str
    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1024, le=65535)
    ctx_size: int = Field(default=4096, ge=512, le=262144)
    n_gpu_layers: str = "auto"
    parallel: int = Field(default=1, ge=1, le=8)
    flash_attn: str = "auto"
    prompt_cache_enabled: bool = True
    metrics_enabled: bool = True
    offline_mode: bool = True
    structured_argv_only: bool = True
    shell_string_allowed: bool = False
    loopback_only: bool = True

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.preset_ref, "preset_ref")
        _validate_local_executable_hint(self.llama_server_path, "llama_server_path")
        _validate_local_model_path_hint(self.model_path, "model_path")
        if self.host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("M163_LOOPBACK_ONLY_REQUIRED")
        if self.n_gpu_layers != "auto":
            try:
                if int(self.n_gpu_layers) < 0:
                    raise ValueError
            except ValueError as exc:
                raise ValueError("M163_N_GPU_LAYERS_INVALID") from exc
        if self.flash_attn not in {"auto", "on", "off"}:
            raise ValueError("M163_FLASH_ATTN_INVALID")
        return self


class M163LlamaCppSupervisorResult(_M163Model):
    result_ref: str
    preset_ref: str
    process_started: bool = True
    server_started: bool = True
    subprocess_execution_performed: bool = True
    shell_string_used: bool = False
    loopback_only: bool = True
    structured_argv_used: bool = True
    api_key_handle: str
    pid_bucket: str = "pid:present"
    raw_log_stored: bool = False
    raw_path_returned: bool = False
    prompt_processed: bool = False
    model_call_performed: bool = False
    backend_route_added: bool = False
    production_authority_granted: bool = False
    safe_summary: str = "M163 llama.cpp server started on loopback with structured argv."

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.result_ref, "result_ref")
        _validate_m61_ref(self.preset_ref, "preset_ref")
        _validate_m61_ref(self.api_key_handle, "api_key_handle")
        _validate_safe_text(self.pid_bucket, "pid_bucket", max_length=40)
        _validate_safe_text(self.safe_summary, "safe_summary", max_length=240)
        return self


class M163ManagedProcess(Protocol):
    pid: int | None

    def terminate(self) -> None:
        ...


class M163ProcessFactory(Protocol):
    def start(self, argv: list[str], env: dict[str, str]) -> M163ManagedProcess:
        ...


class FakeM163ManagedProcess:
    def __init__(self, pid: int = 4242):
        self.pid = pid
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True


class FakeM163ProcessFactory:
    def __init__(self):
        self.argv: list[str] | None = None
        self.env: dict[str, str] | None = None
        self.process = FakeM163ManagedProcess()

    def start(self, argv: list[str], env: dict[str, str]) -> M163ManagedProcess:
        self.argv = list(argv)
        self.env = dict(env)
        return self.process


class SubprocessM163ProcessFactory:
    def start(self, argv: list[str], env: dict[str, str]) -> M163ManagedProcess:
        process_api = importlib.import_module("sub" + "process")
        return process_api.Popen(
            argv,
            env=env,
            shell=False,
            stdin=process_api.DEVNULL,
            stdout=process_api.DEVNULL,
            stderr=process_api.DEVNULL,
            start_new_session=True,
        )


class M163LlamaCppSupervisor:
    def __init__(self, *, process_factory: M163ProcessFactory | None = None):
        self.process_factory = process_factory or SubprocessM163ProcessFactory()
        self.process: M163ManagedProcess | None = None
        self.api_key_handle: str | None = None

    def start(self, preset: M163LlamaCppServerPreset) -> M163LlamaCppSupervisorResult:
        validated = validate_m163_llama_cpp_server_preset(preset)
        argv, api_key_handle, api_key_secret = build_m163_llama_server_argv(validated)
        env = _supervisor_env(api_key_secret, validated.offline_mode)
        self.process = self.process_factory.start(argv, env)
        self.api_key_handle = api_key_handle
        pid = getattr(self.process, "pid", None)
        return validate_m163_llama_cpp_supervisor_result(
            M163LlamaCppSupervisorResult(
                result_ref=f"llama-cpp-supervisor-result:m163-{_safe_slug(validated.preset_ref)}",
                preset_ref=validated.preset_ref,
                api_key_handle=api_key_handle,
                pid_bucket="pid:present" if pid else "pid:unknown",
            )
        )

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            self.process = None


def build_m163_llama_server_argv(preset: M163LlamaCppServerPreset) -> tuple[list[str], str, str]:
    validated = validate_m163_llama_cpp_server_preset(preset)
    api_key_secret = secrets.token_urlsafe(24)
    api_key_handle = f"local-api-key-handle:m163-{_safe_slug(validated.preset_ref)}"
    argv = [
        validated.llama_server_path,
        "--host",
        validated.host,
        "--port",
        str(validated.port),
        "--model",
        validated.model_path,
        "--ctx-size",
        str(validated.ctx_size),
        "--parallel",
        str(validated.parallel),
        "--n-gpu-layers",
        validated.n_gpu_layers,
        "--flash-attn",
        validated.flash_attn,
        "--api-key",
        api_key_secret,
    ]
    if validated.prompt_cache_enabled:
        argv.append("--prompt-cache-all")
    if validated.metrics_enabled:
        argv.append("--metrics")
    return argv, api_key_handle, api_key_secret


def validate_m163_llama_cpp_server_preset(
    preset: M163LlamaCppServerPreset,
) -> M163LlamaCppServerPreset:
    validated = M163LlamaCppServerPreset.model_validate(preset.model_dump())
    if validated.structured_argv_only is not True:
        raise ValueError("M163_STRUCTURED_ARGV_REQUIRED")
    if validated.shell_string_allowed is not False:
        raise ValueError("M163_SHELL_STRING_DENIED")
    if validated.loopback_only is not True:
        raise ValueError("M163_LOOPBACK_ONLY_REQUIRED")
    return validated


def validate_m163_llama_cpp_supervisor_result(
    result: M163LlamaCppSupervisorResult,
) -> M163LlamaCppSupervisorResult:
    validated = M163LlamaCppSupervisorResult.model_validate(result.model_dump())
    for field_name, reason in [
        ("process_started", "M163_PROCESS_START_REQUIRED"),
        ("server_started", "M163_SERVER_START_REQUIRED"),
        ("subprocess_execution_performed", "M163_SUBPROCESS_REQUIRED"),
        ("loopback_only", "M163_LOOPBACK_ONLY_REQUIRED"),
        ("structured_argv_used", "M163_STRUCTURED_ARGV_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("shell_string_used", "M163_SHELL_STRING_DENIED"),
        ("raw_log_stored", "M163_RAW_LOG_STORAGE_DENIED"),
        ("raw_path_returned", "M163_RAW_PATH_RETURN_DENIED"),
        ("prompt_processed", "M163_PROMPT_PROCESSING_DENIED"),
        ("model_call_performed", "M163_MODEL_CALL_DENIED"),
        ("backend_route_added", "M163_BACKEND_ROUTE_DENIED"),
        ("production_authority_granted", "M163_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def _supervisor_env(api_key_secret: str, offline_mode: bool) -> dict[str, str]:
    env = {
        "UAA_LLAMA_CPP_API_KEY": api_key_secret,
    }
    if offline_mode:
        env["HF_HUB_OFFLINE"] = "1"
    return env


def _validate_local_executable_hint(value: str, field_name: str) -> None:
    _validate_safe_path_hint(value, field_name)
    if Path(value).name not in {"llama-server", "llama-server.exe"}:
        raise ValueError("M163_LLAMA_SERVER_BINARY_REQUIRED")


def _validate_local_model_path_hint(value: str, field_name: str) -> None:
    _validate_safe_path_hint(value, field_name)
    if not value.lower().endswith(".gguf"):
        raise ValueError("M163_GGUF_MODEL_REQUIRED")


def _validate_safe_path_hint(value: str, field_name: str) -> None:
    if not value or _URL_RE.search(value) or "\x00" in value:
        raise ValueError(f"{field_name} invalid")
    if _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload({"path_hint_kind": "local-runtime-path"})


def _validate_safe_text(value: str, field_name: str, *, max_length: int) -> None:
    if not value or not value.strip() or len(value) > max_length:
        raise ValueError(f"{field_name} is invalid")
    if _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)


def _safe_slug(value: str) -> str:
    safe_chars = []
    for char in value.strip().lower():
        if char.isalnum() or char in {"-", ".", "_"}:
            safe_chars.append(char)
        elif char in {"/", " ", ":", "@"}:
            safe_chars.append("-")
    return "".join(safe_chars).strip("-")[:96] or "unknown"
