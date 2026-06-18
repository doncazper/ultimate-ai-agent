import pytest

from ultimate_ai_agent.core.local_model_management import (
    BYTES_PER_GIB,
    M161LocalSystemProbePolicy,
    M161LocalSystemProbeRequest,
    M161SystemProbeSample,
    collect_m161_stdlib_system_probe_sample,
    probe_local_system_capabilities,
    validate_m161_local_system_capability_result,
    validate_m161_local_system_probe_policy,
    validate_m161_local_system_probe_request,
)


def _request(**overrides):
    data = {"request_ref": "local-system-probe-request:m161-test"}
    data.update(overrides)
    return M161LocalSystemProbeRequest(**data)


def _sample(**overrides):
    data = {
        "os_name": "Darwin",
        "machine_arch": "arm64",
        "cpu_count": 12,
        "ram_bytes": 64 * BYTES_PER_GIB,
        "vram_bytes": None,
        "disk_free_bytes": 512 * BYTES_PER_GIB,
        "power_source_hint": "ac",
        "thermal_state_hint": "nominal",
    }
    data.update(overrides)
    return M161SystemProbeSample(**data)


def test_m161_policy_allows_only_redacted_stdlib_local_probe():
    policy = validate_m161_local_system_probe_policy(M161LocalSystemProbePolicy())

    assert policy.local_read_only is True
    assert policy.stdlib_only is True
    assert policy.redacted_buckets_only is True
    assert policy.hardware_fit_metadata_only is True
    assert policy.hostname_allowed is False
    assert policy.serial_allowed is False
    assert policy.username_allowed is False
    assert policy.raw_path_allowed is False
    assert policy.env_dump_allowed is False
    assert policy.subprocess_allowed is False
    assert policy.network_allowed is False
    assert policy.download_allowed is False
    assert policy.model_call_allowed is False
    assert policy.dependency_added is False

    with pytest.raises(ValueError, match="M161_RAW_PATH_DENIED"):
        validate_m161_local_system_probe_policy(M161LocalSystemProbePolicy(raw_path_allowed=True))


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"broad_scan_requested": True}, "M161_BROAD_SCAN_DENIED"),
        ({"hostname_requested": True}, "M161_HOSTNAME_DENIED"),
        ({"serial_requested": True}, "M161_SERIAL_DENIED"),
        ({"username_requested": True}, "M161_USERNAME_DENIED"),
        ({"raw_path_requested": True}, "M161_RAW_PATH_DENIED"),
        ({"env_dump_requested": True}, "M161_ENV_DUMP_DENIED"),
        ({"subprocess_requested": True}, "M161_PROCESS_DENIED"),
        ({"network_requested": True}, "M161_NETWORK_DENIED"),
        ({"download_requested": True}, "M161_DOWNLOAD_DENIED"),
        ({"model_call_requested": True}, "M161_MODEL_CALL_DENIED"),
    ],
)
def test_m161_request_denies_host_inventory_execution_network_and_models(update, reason):
    with pytest.raises(ValueError, match=reason):
        validate_m161_local_system_probe_request(_request(**update))


def test_m161_deterministic_sample_probe_returns_only_buckets():
    result = probe_local_system_capabilities(_request(), sample=_sample())
    payload = result.model_dump_json()

    assert result.local_system_probe_performed is True
    assert result.local_only is True
    assert result.stdlib_only is True
    assert result.redacted is True
    assert result.bucketed_only is True
    assert result.os_arch_bucket == "os-arch:macos-arm64"
    assert result.cpu_core_bucket == "cpu-cores:9-16"
    assert result.ram_bucket == "ram:64-127gb"
    assert result.vram_bucket == "vram:unknown"
    assert result.backend_device_family_bucket == "backend-device:apple-silicon-metal-family"
    assert result.disk_budget_bucket == "disk-free:500-999gb"
    assert result.power_thermal_hint == "power-thermal:ac-nominal"
    assert result.raw_hostname_included is False
    assert result.raw_serial_included is False
    assert result.raw_username_included is False
    assert result.raw_path_included is False
    assert result.env_dump_included is False
    assert result.broad_scan_performed is False
    assert result.subprocess_execution_performed is False
    assert result.network_access_performed is False
    assert result.download_performed is False
    assert result.model_call_performed is False
    assert "/Users/" not in payload
    assert "/home/" not in payload
    assert "USERNAME" not in payload
    assert "PATH=" not in payload


def test_m161_sample_probe_can_bucket_discrete_gpu_family_when_vram_is_injected():
    result = probe_local_system_capabilities(
        _request(request_ref="local-system-probe-request:m161-linux"),
        sample=_sample(
            os_name="Linux",
            machine_arch="x86_64",
            cpu_count=32,
            ram_bytes=128 * BYTES_PER_GIB,
            vram_bytes=24 * BYTES_PER_GIB,
            disk_free_bytes=2_000 * BYTES_PER_GIB,
            power_source_hint="unknown",
            thermal_state_hint="unknown",
        ),
    )

    assert result.os_arch_bucket == "os-arch:linux-x86-64"
    assert result.cpu_core_bucket == "cpu-cores:17-32"
    assert result.ram_bucket == "ram:128gb-plus"
    assert result.vram_bucket == "vram:16-31gb"
    assert result.backend_device_family_bucket == "backend-device:discrete-gpu-family"
    assert result.disk_budget_bucket == "disk-free:1tb-plus"


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"raw_hostname_included": True}, "M161_HOSTNAME_DENIED"),
        ({"raw_serial_included": True}, "M161_SERIAL_DENIED"),
        ({"raw_username_included": True}, "M161_USERNAME_DENIED"),
        ({"raw_path_included": True}, "M161_RAW_PATH_DENIED"),
        ({"env_dump_included": True}, "M161_ENV_DUMP_DENIED"),
        ({"broad_scan_performed": True}, "M161_BROAD_SCAN_DENIED"),
        ({"subprocess_execution_performed": True}, "M161_PROCESS_DENIED"),
        ({"network_access_performed": True}, "M161_NETWORK_DENIED"),
        ({"download_performed": True}, "M161_DOWNLOAD_DENIED"),
        ({"model_call_performed": True}, "M161_MODEL_CALL_DENIED"),
    ],
)
def test_m161_result_validation_rejects_unsafe_mutations(update, reason):
    result = probe_local_system_capabilities(_request(), sample=_sample())

    with pytest.raises(ValueError, match=reason):
        validate_m161_local_system_capability_result(result.model_copy(update=update))


def test_m161_actual_stdlib_probe_shape_is_redacted_and_safe():
    sample = collect_m161_stdlib_system_probe_sample()
    result = probe_local_system_capabilities(
        _request(request_ref="local-system-probe-request:m161-actual"),
        sample=sample,
    )
    payload = result.model_dump_json()

    assert result.local_system_probe_performed is True
    assert result.os_arch_bucket.startswith("os-arch:")
    assert result.cpu_core_bucket.startswith("cpu-cores:")
    assert result.ram_bucket.startswith("ram:")
    assert result.vram_bucket.startswith("vram:")
    assert result.disk_budget_bucket.startswith("disk-free:")
    assert result.backend_device_family_bucket.startswith("backend-device:")
    assert result.raw_hostname_included is False
    assert result.raw_serial_included is False
    assert result.raw_username_included is False
    assert result.raw_path_included is False
    assert result.env_dump_included is False
    assert "/Users/" not in payload
    assert "/home/" not in payload
