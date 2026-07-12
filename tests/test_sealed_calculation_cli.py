from __future__ import annotations

import io
import json

from scripts.dev import uaa_runtime, uaa_runtime_sealed_calculation
from ultimate_ai_agent.core.sandbox_calculation.backend import (
    SealedCalculationBackendError,
)

from .test_sealed_calculation_mission import EXPRESSION, _service_with_exact_lease


def test_cli_inspect_is_human_readable_and_never_grants_authority(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    service, _request, _state_dir = _service_with_exact_lease(tmp_path)
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation,
        "_discover",
        lambda _state_dir=None: service.adapter._backend,  # noqa: SLF001
    )

    assert uaa_runtime.main(["sealed-calculation", "inspect"]) == 0
    output = capsys.readouterr().out

    assert "Sealed deterministic calculation" in output
    assert "ready_for_exact_lease_evaluation" in output
    assert "Code output is evidence, not authority." in output
    assert not output.lstrip().startswith("{")


def test_cli_inspect_normalizes_backend_failures_without_path_leak(
    monkeypatch,
    capsys,
) -> None:
    def unavailable(_state_dir=None):
        raise SealedCalculationBackendError("backend failure at /unsafe/local/path")

    monkeypatch.setattr(uaa_runtime_sealed_calculation, "_discover", unavailable)

    assert uaa_runtime.main(["sealed-calculation", "inspect", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "configuration_required"
    assert payload["reason_code"] == "SEALED_CALCULATION_BACKEND_UNAVAILABLE"
    assert payload["execution_performed"] is False
    assert "/unsafe/" not in json.dumps(payload)


def test_cli_inspect_normalizes_configuration_value_errors(
    monkeypatch,
    capsys,
) -> None:
    def unavailable(_state_dir=None):
        raise ValueError("configuration failed at /unsafe/local/path")

    monkeypatch.setattr(uaa_runtime_sealed_calculation, "_discover", unavailable)

    assert uaa_runtime.main(["sealed-calculation", "inspect", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "configuration_required"
    assert payload["reason_code"] == "SEALED_CALCULATION_BACKEND_UNAVAILABLE"
    assert "/unsafe/" not in json.dumps(payload)


def test_cli_run_uses_exact_mission_service_and_returns_safe_evidence(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    service, request, state_dir = _service_with_exact_lease(tmp_path)
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation,
        "_discover",
        lambda _state_dir=None: service.adapter._backend,  # noqa: SLF001
    )
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation.sys,
        "stdin",
        io.StringIO(EXPRESSION + "\n"),
    )

    exit_code = uaa_runtime.main(
        [
            "--state-dir",
            str(state_dir),
            "sealed-calculation",
            "run",
            "--request-ref",
            request.request_ref,
            "--input-ref",
            request.input_ref,
            "--plan-ref",
            request.plan_ref,
            "--mission-ref",
            request.mission_ref,
            "--run-ref",
            request.run_ref,
            "--step-ref",
            request.step_ref,
            "--lease-ref",
            request.lease_ref,
            "--owner-ref",
            "worker-ref:sealed-calculation:cli-test",
            "--start-deadline",
            request.start_deadline.isoformat(),
            "--request-created-at",
            request.request_created_at.isoformat(),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "succeeded"
    assert payload["result_preview"] == "853973398759475"
    assert payload["result_is_evidence_not_authority"] is True
    assert payload["raw_expression_persisted"] is False
    assert payload["global_authority_granted"] is False
    assert EXPRESSION not in json.dumps(payload)


def test_cli_prepare_emits_exact_lease_refs_without_execution(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation,
        "_discover",
        lambda _state_dir=None: service.adapter._backend,  # noqa: SLF001
    )
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation.sys,
        "stdin",
        io.StringIO(EXPRESSION + "\n"),
    )

    assert (
        uaa_runtime.main(
            [
                "sealed-calculation",
                "prepare",
                "--input-ref",
                request.input_ref,
                "--mission-ref",
                request.mission_ref,
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "exact_lease_resources_prepared"
    assert payload["execution_performed"] is False
    assert payload["raw_expression_persisted"] is False
    assert payload["required_domain"] == "workspace"
    assert payload["required_capability"] == "execute"
    assert payload["request_created_at"]
    assert request.mission_ref in payload["resource_refs"]
    assert request.input_ref in payload["resource_refs"]
    assert EXPRESSION not in json.dumps(payload)


def test_cli_discovery_wires_current_global_kill_and_safe_disable(
    monkeypatch,
    tmp_path,
) -> None:
    captured = {}

    class FakeRuntimeStore:
        def __init__(self, state_dir):
            captured["state_dir"] = state_dir

        @staticmethod
        def operator_safe_disable_active() -> bool:
            return True

    def fake_discover(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        uaa_runtime_sealed_calculation,
        "RuntimeInvocationStore",
        FakeRuntimeStore,
    )
    monkeypatch.setattr(
        uaa_runtime_sealed_calculation,
        "discover_local_docker_backend",
        fake_discover,
    )
    monkeypatch.setenv("UAA_AUTHORITY_LEASE_KILL_SWITCH", "engaged")

    uaa_runtime_sealed_calculation._discover(tmp_path)

    assert captured["state_dir"] == tmp_path
    assert captured["kill_switch"]() is True
    assert captured["safe_disabled"]() is True
