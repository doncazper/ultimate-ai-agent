from __future__ import annotations

import os
import platform
import shutil
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _RAW_LOCAL_PATH_RE,
    _SECRET_LIKE_RE,
    _URL_RE,
    _validate_m61_ref,
    _validate_safe_payload,
)


BYTES_PER_GIB = 1024**3


class _M161Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class M161LocalSystemProbePolicy(_M161Model):
    policy_ref: str = "local-system-probe-policy:m161"
    local_read_only: bool = True
    stdlib_only: bool = True
    redacted_buckets_only: bool = True
    hardware_fit_metadata_only: bool = True
    broad_scan_allowed: bool = False
    hostname_allowed: bool = False
    serial_allowed: bool = False
    username_allowed: bool = False
    raw_path_allowed: bool = False
    env_dump_allowed: bool = False
    subprocess_allowed: bool = False
    network_allowed: bool = False
    download_allowed: bool = False
    model_call_allowed: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class M161LocalSystemProbeRequest(_M161Model):
    request_ref: str
    policy_ref: str = "local-system-probe-policy:m161"
    audit_ref: str = "audit:m161-local-system-probe"
    replay_ref: str = "replay:m161-local-system-probe"
    receipt_plan_ref: str = "receipt-plan:m161-local-system-probe"
    disk_budget_scope_ref: str = "disk-budget-scope:default-volume"
    metadata: dict[str, Any] = Field(default_factory=dict)
    broad_scan_requested: bool = False
    hostname_requested: bool = False
    serial_requested: bool = False
    username_requested: bool = False
    raw_path_requested: bool = False
    env_dump_requested: bool = False
    subprocess_requested: bool = False
    network_requested: bool = False
    download_requested: bool = False
    model_call_requested: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.policy_ref, "policy_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.disk_budget_scope_ref, "disk_budget_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.metadata)
        return self


class M161SystemProbeSample(_M161Model):
    os_name: str
    machine_arch: str
    cpu_count: int | None = Field(default=None, ge=1)
    ram_bytes: int | None = Field(default=None, ge=0)
    vram_bytes: int | None = Field(default=None, ge=0)
    disk_free_bytes: int | None = Field(default=None, ge=0)
    power_source_hint: str = "unknown"
    thermal_state_hint: str = "unknown"

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_safe_component_text(self.os_name, "os_name")
        _validate_safe_component_text(self.machine_arch, "machine_arch")
        _validate_safe_component_text(self.power_source_hint, "power_source_hint")
        _validate_safe_component_text(self.thermal_state_hint, "thermal_state_hint")
        return self


class M161LocalSystemCapabilityResult(_M161Model):
    result_ref: str
    request_ref: str
    hardware_summary_ref: str = "hardware-summary:m161-local-system-probe"
    os_arch_bucket: str
    cpu_core_bucket: str
    ram_bucket: str
    vram_bucket: str
    backend_device_family_bucket: str
    disk_budget_bucket: str
    power_thermal_hint: str
    safe_summary: str = "Redacted local system capability buckets produced."
    local_system_probe_performed: bool = True
    local_only: bool = True
    stdlib_only: bool = True
    redacted: bool = True
    bucketed_only: bool = True
    raw_hostname_included: bool = False
    raw_serial_included: bool = False
    raw_username_included: bool = False
    raw_path_included: bool = False
    env_dump_included: bool = False
    broad_scan_performed: bool = False
    subprocess_execution_performed: bool = False
    network_access_performed: bool = False
    download_performed: bool = False
    model_file_read_performed: bool = False
    model_call_performed: bool = False
    backend_route_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.result_ref, "result_ref"),
            (self.request_ref, "request_ref"),
            (self.hardware_summary_ref, "hardware_summary_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for value, field_name in [
            (self.os_arch_bucket, "os_arch_bucket"),
            (self.cpu_core_bucket, "cpu_core_bucket"),
            (self.ram_bucket, "ram_bucket"),
            (self.vram_bucket, "vram_bucket"),
            (self.backend_device_family_bucket, "backend_device_family_bucket"),
            (self.disk_budget_bucket, "disk_budget_bucket"),
            (self.power_thermal_hint, "power_thermal_hint"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_component_text(value, field_name)
        return self


def probe_local_system_capabilities(
    probe_request: M161LocalSystemProbeRequest,
    *,
    sample: M161SystemProbeSample | None = None,
) -> M161LocalSystemCapabilityResult:
    validated_request = validate_m161_local_system_probe_request(probe_request)
    active_sample = sample or collect_m161_stdlib_system_probe_sample()
    return validate_m161_local_system_capability_result(
        M161LocalSystemCapabilityResult(
            result_ref=f"local-system-probe-result:m161-{_safe_ref_suffix(validated_request.request_ref)}",
            request_ref=validated_request.request_ref,
            os_arch_bucket=_os_arch_bucket(active_sample.os_name, active_sample.machine_arch),
            cpu_core_bucket=_cpu_core_bucket(active_sample.cpu_count),
            ram_bucket=_memory_bucket(active_sample.ram_bytes, "ram"),
            vram_bucket=_memory_bucket(active_sample.vram_bytes, "vram"),
            backend_device_family_bucket=_backend_device_family_bucket(active_sample),
            disk_budget_bucket=_disk_budget_bucket(active_sample.disk_free_bytes),
            power_thermal_hint=_power_thermal_hint(active_sample),
        )
    )


def collect_m161_stdlib_system_probe_sample() -> M161SystemProbeSample:
    return M161SystemProbeSample(
        os_name=platform.system() or "unknown",
        machine_arch=platform.machine() or "unknown",
        cpu_count=os.cpu_count(),
        ram_bytes=_stdlib_ram_bytes(),
        vram_bytes=None,
        disk_free_bytes=_stdlib_disk_free_bytes(),
        power_source_hint="unknown",
        thermal_state_hint="unknown",
    )


def validate_m161_local_system_probe_policy(
    policy: M161LocalSystemProbePolicy,
) -> M161LocalSystemProbePolicy:
    validated = M161LocalSystemProbePolicy.model_validate(policy.model_dump())
    for field_name, reason in [
        ("local_read_only", "M161_LOCAL_READ_ONLY_REQUIRED"),
        ("stdlib_only", "M161_STDLIB_ONLY_REQUIRED"),
        ("redacted_buckets_only", "M161_REDACTED_BUCKETS_REQUIRED"),
        ("hardware_fit_metadata_only", "M161_METADATA_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("broad_scan_allowed", "M161_BROAD_SCAN_DENIED"),
        ("hostname_allowed", "M161_HOSTNAME_DENIED"),
        ("serial_allowed", "M161_SERIAL_DENIED"),
        ("username_allowed", "M161_USERNAME_DENIED"),
        ("raw_path_allowed", "M161_RAW_PATH_DENIED"),
        ("env_dump_allowed", "M161_ENV_DUMP_DENIED"),
        ("subprocess_allowed", "M161_PROCESS_DENIED"),
        ("network_allowed", "M161_NETWORK_DENIED"),
        ("download_allowed", "M161_DOWNLOAD_DENIED"),
        ("model_call_allowed", "M161_MODEL_CALL_DENIED"),
        ("dependency_added", "M161_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M161_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m161_local_system_probe_request(
    probe_request: M161LocalSystemProbeRequest,
) -> M161LocalSystemProbeRequest:
    validated = M161LocalSystemProbeRequest.model_validate(probe_request.model_dump())
    for field_name, reason in [
        ("broad_scan_requested", "M161_BROAD_SCAN_DENIED"),
        ("hostname_requested", "M161_HOSTNAME_DENIED"),
        ("serial_requested", "M161_SERIAL_DENIED"),
        ("username_requested", "M161_USERNAME_DENIED"),
        ("raw_path_requested", "M161_RAW_PATH_DENIED"),
        ("env_dump_requested", "M161_ENV_DUMP_DENIED"),
        ("subprocess_requested", "M161_PROCESS_DENIED"),
        ("network_requested", "M161_NETWORK_DENIED"),
        ("download_requested", "M161_DOWNLOAD_DENIED"),
        ("model_call_requested", "M161_MODEL_CALL_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m161_local_system_capability_result(
    result: M161LocalSystemCapabilityResult,
) -> M161LocalSystemCapabilityResult:
    validated = M161LocalSystemCapabilityResult.model_validate(result.model_dump())
    for field_name, reason in [
        ("local_system_probe_performed", "M161_LOCAL_SYSTEM_PROBE_REQUIRED"),
        ("local_only", "M161_LOCAL_ONLY_REQUIRED"),
        ("stdlib_only", "M161_STDLIB_ONLY_REQUIRED"),
        ("redacted", "M161_REDACTION_REQUIRED"),
        ("bucketed_only", "M161_BUCKETS_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("raw_hostname_included", "M161_HOSTNAME_DENIED"),
        ("raw_serial_included", "M161_SERIAL_DENIED"),
        ("raw_username_included", "M161_USERNAME_DENIED"),
        ("raw_path_included", "M161_RAW_PATH_DENIED"),
        ("env_dump_included", "M161_ENV_DUMP_DENIED"),
        ("broad_scan_performed", "M161_BROAD_SCAN_DENIED"),
        ("subprocess_execution_performed", "M161_PROCESS_DENIED"),
        ("network_access_performed", "M161_NETWORK_DENIED"),
        ("download_performed", "M161_DOWNLOAD_DENIED"),
        ("model_file_read_performed", "M161_MODEL_FILE_READ_DENIED"),
        ("model_call_performed", "M161_MODEL_CALL_DENIED"),
        ("backend_route_added", "M161_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M161_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M161_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def _stdlib_ram_bytes() -> int | None:
    if not hasattr(os, "sysconf"):
        return None
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
    except (OSError, ValueError):
        return None
    if not isinstance(page_size, int) or not isinstance(page_count, int):
        return None
    if page_size <= 0 or page_count <= 0:
        return None
    return page_size * page_count


def _stdlib_disk_free_bytes() -> int | None:
    try:
        return int(shutil.disk_usage(os.sep).free)
    except OSError:
        return None


def _os_arch_bucket(os_name: str, machine_arch: str) -> str:
    return f"os-arch:{_normalize_os(os_name)}-{_normalize_arch(machine_arch)}"


def _cpu_core_bucket(cpu_count: int | None) -> str:
    if cpu_count is None or cpu_count <= 0:
        return "cpu-cores:unknown"
    if cpu_count <= 2:
        return "cpu-cores:1-2"
    if cpu_count <= 4:
        return "cpu-cores:3-4"
    if cpu_count <= 8:
        return "cpu-cores:5-8"
    if cpu_count <= 16:
        return "cpu-cores:9-16"
    if cpu_count <= 32:
        return "cpu-cores:17-32"
    return "cpu-cores:33-plus"


def _memory_bucket(byte_count: int | None, label: str) -> str:
    safe_label = _safe_component(label)
    if byte_count is None:
        return f"{safe_label}:unknown"
    gib = byte_count / BYTES_PER_GIB
    if gib < 4:
        return f"{safe_label}:lt4gb"
    if gib < 8:
        return f"{safe_label}:4-7gb"
    if gib < 16:
        return f"{safe_label}:8-15gb"
    if gib < 32:
        return f"{safe_label}:16-31gb"
    if gib < 64:
        return f"{safe_label}:32-63gb"
    if gib < 128:
        return f"{safe_label}:64-127gb"
    return f"{safe_label}:128gb-plus"


def _disk_budget_bucket(byte_count: int | None) -> str:
    if byte_count is None:
        return "disk-free:unknown"
    gib = byte_count / BYTES_PER_GIB
    if gib < 25:
        return "disk-free:lt25gb"
    if gib < 50:
        return "disk-free:25-49gb"
    if gib < 100:
        return "disk-free:50-99gb"
    if gib < 250:
        return "disk-free:100-249gb"
    if gib < 500:
        return "disk-free:250-499gb"
    if gib < 1000:
        return "disk-free:500-999gb"
    return "disk-free:1tb-plus"


def _backend_device_family_bucket(sample: M161SystemProbeSample) -> str:
    os_bucket = _normalize_os(sample.os_name)
    arch_bucket = _normalize_arch(sample.machine_arch)
    if sample.vram_bytes is not None and sample.vram_bytes >= 4 * BYTES_PER_GIB:
        return "backend-device:discrete-gpu-family"
    if os_bucket == "macos" and arch_bucket in {"arm64", "aarch64"}:
        return "backend-device:apple-silicon-metal-family"
    if arch_bucket in {"arm64", "aarch64"}:
        return f"backend-device:{os_bucket}-arm-cpu-family"
    if arch_bucket in {"x86-64", "amd64"}:
        return f"backend-device:{os_bucket}-x86-cpu-family"
    return f"backend-device:{os_bucket}-cpu-family"


def _power_thermal_hint(sample: M161SystemProbeSample) -> str:
    return (
        "power-thermal:"
        f"{_safe_component(sample.power_source_hint)}-{_safe_component(sample.thermal_state_hint)}"
    )


def _normalize_os(value: str) -> str:
    normalized = _safe_component(value)
    mapping = {
        "darwin": "macos",
        "mac": "macos",
        "macos": "macos",
        "linux": "linux",
        "windows": "windows",
        "win32": "windows",
    }
    return mapping.get(normalized, normalized or "unknown")


def _normalize_arch(value: str) -> str:
    normalized = _safe_component(value)
    mapping = {
        "x86_64": "x86-64",
        "x86-64": "x86-64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "aarch64",
    }
    return mapping.get(normalized, normalized or "unknown")


def _safe_component(value: str) -> str:
    lowered = value.strip().lower().replace("_", "-").replace(" ", "-")
    kept = "".join(char for char in lowered if char.isalnum() or char in {".", "-"})
    return kept[:64] or "unknown"


def _safe_ref_suffix(ref: str) -> str:
    suffix = ref.split(":", 1)[-1]
    return _safe_component(suffix.replace("/", "-"))


def _validate_safe_component_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if len(value) > 160:
        raise ValueError(f"{field_name} is too long")
    if _URL_RE.search(value) or _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    if _RAW_LOCAL_PATH_RE.search(value) or "\\Users\\" in value:
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)
