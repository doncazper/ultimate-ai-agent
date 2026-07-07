import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.runtime_gateway import (
    HERMES_CLI_ENV,
    HERMES_INTERFACE_MODE_ENABLED_ENV,
    HermesChatRequest,
    HermesCliAdapter,
    HermesProcessResult,
    RuntimeInterfaceMode,
    build_hermes_context_pack_read_model,
    build_runtime_interface_mode_read_model,
)
from tests.authority_helpers import (
    issue_workspace_execute_authority_lease,
    workspace_execute_authority_lease,
)


client = TestClient(app)
IDEMPOTENCY_HEADERS = {"x-uaa-idempotency-key": "idempotency-ref:hermes-api-test"}


def _fake_hermes(tmp_path: Path) -> Path:
    fake = tmp_path / "hermes"
    fake.write_text("#!/bin/sh\necho hermes safe fixture\n", encoding="utf-8")
    fake.chmod(0o700)
    return fake


def test_runtime_interface_mode_defaults_to_uaa_native_disabled_without_probe(
    tmp_path,
    monkeypatch,
) -> None:
    fake = _fake_hermes(tmp_path)
    monkeypatch.setenv(HERMES_CLI_ENV, str(fake))
    monkeypatch.delenv(HERMES_INTERFACE_MODE_ENABLED_ENV, raising=False)

    def runner(**kwargs) -> HermesProcessResult:
        raise AssertionError("Hermes runner must not be called while disabled")

    read_model = build_runtime_interface_mode_read_model(
        adapter=HermesCliAdapter(runner=runner)
    )
    context_pack = build_hermes_context_pack_read_model()
    receipt = HermesCliAdapter(runner=runner).chat(
        HermesChatRequest(
            mode=RuntimeInterfaceMode.shell_guarded,
            query="Summarize operator-safe refs.",
            operator_submission_acknowledged=True,
        ),
        idempotency_ref="idempotency-ref:hermes-disabled-test",
    )

    assert read_model.active_mode == "disabled"
    assert read_model.interface_enabled is False
    assert read_model.hermes_cli_posture.readiness_checked is False
    assert read_model.hermes_cli_posture.discovery_source == "disabled"
    assert read_model.uaa_execution_enabled is False
    assert context_pack.projection_enabled is False
    assert context_pack.section_count == 0
    assert receipt.execution_performed is False
    assert receipt.status == "blocked"
    assert "blocked-authority:hermes-interface-mode-disabled" in receipt.blocked_reason_refs


def test_runtime_interface_mode_enabled_keeps_uaa_native_agent_off(
    tmp_path,
    monkeypatch,
) -> None:
    fake = _fake_hermes(tmp_path)
    monkeypatch.setenv(HERMES_CLI_ENV, str(fake))
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")

    def runner(**kwargs) -> HermesProcessResult:
        assert kwargs["argv"] == (str(fake), "status", "--all")
        return HermesProcessResult(
            exit_code=0,
            timed_out=False,
            duration_ms=2,
            output_bytes=b"ready",
        )

    read_model = build_runtime_interface_mode_read_model(
        adapter=HermesCliAdapter(runner=runner)
    )

    assert read_model.schema_version == "runtime_interface_mode.v1"
    assert read_model.active_mode == "shell_guarded"
    assert read_model.interface_enabled is True
    assert read_model.uaa_native_agent_enabled is False
    assert read_model.uaa_planning_enabled is False
    assert read_model.uaa_execution_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.hermes_cli_posture.status == "ready"
    assert read_model.hermes_cli_posture.cli_path_persisted is False
    assert str(tmp_path) not in json.dumps(read_model.model_dump(mode="json"))


def test_hermes_chat_uses_exact_guarded_argv_and_redacted_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    fake = _fake_hermes(tmp_path)
    monkeypatch.setenv(HERMES_CLI_ENV, str(fake))
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    observed: list[tuple[str, ...]] = []

    def runner(**kwargs) -> HermesProcessResult:
        observed.append(kwargs["argv"])
        return HermesProcessResult(
            exit_code=0,
            timed_out=False,
            duration_ms=3,
            output_bytes=b"safe proposal text",
        )

    request = HermesChatRequest(
        mode=RuntimeInterfaceMode.shell_guarded,
        query="Explain the current operator-safe context.",
        operator_submission_acknowledged=True,
    )
    receipt = HermesCliAdapter(runner=runner).chat(
        request,
        idempotency_ref="idempotency-ref:hermes-chat-test",
        active_authority_leases=[workspace_execute_authority_lease()],
    )

    assert observed == [
        (
            str(fake),
            "chat",
            "--query",
            "Explain the current operator-safe context.",
            "--quiet",
            "--source",
            "uaa-control-center",
        )
    ]
    assert receipt.status == "receipt_recorded"
    assert receipt.execution_performed is True
    assert receipt.query_ref.startswith("hermes-query-ref:")
    assert receipt.raw_prompt_persisted is False
    assert receipt.raw_output_persisted is False
    dumped = json.dumps(receipt.model_dump(mode="json"))
    assert "Explain the current operator-safe context." not in dumped
    assert "safe proposal text" not in dumped
    assert str(tmp_path) not in dumped


def test_hermes_chat_rejects_unsafe_flags() -> None:
    with pytest.raises(ValueError, match="HERMES_QUERY_UNSAFE_FRAGMENT_DENIED"):
        HermesChatRequest(
            mode=RuntimeInterfaceMode.shell_guarded,
            query="please run --yolo",
            operator_submission_acknowledged=True,
        )


def test_hermes_context_pack_is_curated_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    context_pack = build_hermes_context_pack_read_model()

    assert context_pack.section_count == 9
    assert context_pack.projection_enabled is True
    assert context_pack.raw_memory_records_exposed is False
    assert context_pack.raw_crm_records_exposed is False
    assert context_pack.raw_chat_transcripts_exposed is False
    assert context_pack.raw_local_paths_exposed is False
    assert context_pack.direct_memory_write_enabled is False
    assert context_pack.memory_update_policy == "candidate_only_review_required"
    assert {section.source_surface for section in context_pack.sections} >= {
        "Memory Review and reviewed context",
        "CRM local command center",
        "Evidence",
        "Proof",
    }


def test_runtime_hermes_api_routes_return_backend_read_models(
    tmp_path,
    monkeypatch,
) -> None:
    fake = _fake_hermes(tmp_path)
    authority_dir = tmp_path / "authority"
    issue_workspace_execute_authority_lease(authority_dir)
    monkeypatch.setenv(HERMES_CLI_ENV, str(fake))
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    monkeypatch.setenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, "1")
    reset_api_rate_limit_state()

    interface = client.get("/api/runtime/interface-mode")
    context_pack = client.get("/api/runtime/hermes/context-pack")
    chat = client.post(
        "/api/runtime/hermes/chat",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "mode": "shell_guarded",
            "query": "Summarize operator-safe refs.",
            "operator_submission_acknowledged": True,
        },
    )

    assert interface.status_code == 200
    assert interface.json()["data"]["schema_version"] == "runtime_interface_mode.v1"
    assert context_pack.status_code == 200
    assert context_pack.json()["data"]["schema_version"] == "hermes_context_pack.v1"
    assert chat.status_code == 200
    receipt = chat.json()["data"]["receipt"]
    assert receipt["status"] == "receipt_recorded"
    assert receipt["execution_performed"] is True
    assert receipt["authority_decision_outcome"] == "allow"
    assert receipt["authority_lease_ref"]
    assert receipt["query_ref"].startswith("hermes-query-ref:")
    assert receipt["raw_prompt_persisted"] is False
    assert receipt["raw_output_persisted"] is False
    assert "Summarize operator-safe refs." not in json.dumps(chat.json())


def test_runtime_hermes_chat_route_requires_idempotency(
    monkeypatch,
) -> None:
    monkeypatch.setenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, "1")
    reset_api_rate_limit_state()

    response = client.post(
        "/api/runtime/hermes/chat",
        json={
            "mode": "shell_guarded",
            "query": "Summarize operator-safe refs.",
            "operator_submission_acknowledged": True,
        },
    )

    assert response.status_code == 428
    assert response.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


def test_runtime_cli_interface_mode_and_hermes_context_pack(
    tmp_path,
    monkeypatch,
) -> None:
    fake = _fake_hermes(tmp_path)
    authority_dir = tmp_path / "authority"
    issue_workspace_execute_authority_lease(authority_dir)
    env = os.environ.copy()
    env[HERMES_CLI_ENV] = str(fake)
    env[HERMES_INTERFACE_MODE_ENABLED_ENV] = "1"
    env[AUTHORITY_STATE_DIR_ENV] = str(authority_dir)

    interface = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-interface-mode",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    context_pack = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-hermes-context-pack",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    chat = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "hermes-chat",
            "--mode",
            "shell_guarded",
            "--query",
            "Summarize operator-safe refs.",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    interface_payload = json.loads(interface.stdout)
    context_payload = json.loads(context_pack.stdout)
    chat_payload = json.loads(chat.stdout)

    assert interface_payload["runtime_interface_mode"]["schema_version"] == (
        "runtime_interface_mode.v1"
    )
    assert context_payload["hermes_context_pack"]["schema_version"] == (
        "hermes_context_pack.v1"
    )
    assert chat_payload["hermes_chat_receipt"]["query_ref"].startswith(
        "hermes-query-ref:"
    )
    assert chat_payload["raw_query_omitted"] is True
    assert "Summarize operator-safe refs." not in chat.stdout


def test_runtime_cli_hermes_chat_denies_unsafe_query_without_traceback() -> None:
    denied = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "hermes-chat",
            "--mode",
            "shell_guarded",
            "--query",
            "please run --yolo",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert denied.returncode == 2
    assert denied.stderr == ""
    assert "Traceback" not in denied.stdout
    assert "--yolo" not in denied.stdout
    payload = json.loads(denied.stdout)
    receipt = payload["hermes_chat_receipt"]
    assert receipt["status"] == "blocked_unsafe_input"
    assert receipt["execution_performed"] is False
    assert receipt["unsafe_arg_blocked"] is True
    assert receipt["raw_prompt_persisted"] is False
    assert receipt["raw_output_persisted"] is False
