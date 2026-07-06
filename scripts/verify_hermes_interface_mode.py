#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    HermesChatRequest,
    HermesCliAdapter,
    HERMES_INTERFACE_MODE_ENABLED_ENV,
    HermesProcessResult,
    RuntimeInterfaceMode,
    build_hermes_context_pack_read_model,
    build_runtime_interface_mode_read_model,
    verify_hermes_interface_mode_contract,
)


def _runner(
    *,
    argv: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    output_byte_limit: int,
) -> HermesProcessResult:
    del argv, cwd, env, timeout_seconds, output_byte_limit
    return HermesProcessResult(
        exit_code=0,
        timed_out=False,
        duration_ms=1,
        output_bytes=b"hermes safe status",
    )


def main() -> int:
    failures: list[str] = []
    previous_enabled = os.environ.get(HERMES_INTERFACE_MODE_ENABLED_ENV)
    try:
        os.environ.pop(HERMES_INTERFACE_MODE_ENABLED_ENV, None)
        disabled_interface = build_runtime_interface_mode_read_model(
            adapter=HermesCliAdapter(runner=_runner)
        )
        disabled_context_pack = build_hermes_context_pack_read_model()
        if disabled_interface.interface_enabled or disabled_interface.active_mode != "disabled":
            failures.append("Hermes interface mode must default to disabled.")
        if disabled_interface.hermes_cli_posture.readiness_checked:
            failures.append("Disabled Hermes interface mode must not run readiness.")
        if disabled_context_pack.projection_enabled or disabled_context_pack.section_count:
            failures.append("Disabled Hermes interface mode must not project context.")

        os.environ[HERMES_INTERFACE_MODE_ENABLED_ENV] = "1"
        adapter = HermesCliAdapter(runner=_runner)
        interface = build_runtime_interface_mode_read_model(adapter=adapter)
        context_pack = build_hermes_context_pack_read_model()
        verification = verify_hermes_interface_mode_contract()

        if not verification["default_disabled"]:
            failures.append("Core verifier did not prove default disabled posture.")
        if interface.uaa_native_agent_enabled or interface.uaa_execution_enabled:
            failures.append("UAA-native agent execution must stay off in interface mode.")
        if interface.control_center_mints_authority:
            failures.append("Control Center must not mint interface-mode authority.")
        if context_pack.raw_memory_records_exposed or context_pack.raw_crm_records_exposed:
            failures.append("Hermes context pack exposed raw Memory or CRM records.")
        if context_pack.raw_chat_transcripts_exposed or context_pack.raw_local_paths_exposed:
            failures.append("Hermes context pack exposed raw chat transcripts or local paths.")
        if context_pack.direct_memory_write_enabled:
            failures.append("Hermes memory updates must remain candidate-only.")
        if not verification["pass_through_external_only"]:
            failures.append("Pure Hermes pass-through must be external handoff only.")

        blocked = adapter.chat(
            HermesChatRequest(
                mode=RuntimeInterfaceMode.pure_hermes_pass_through,
                query="external only",
                operator_submission_acknowledged=True,
            ),
            idempotency_ref="idempotency-ref:hermes-interface-mode-verifier",
        )
        if blocked.execution_performed or not blocked.external_handoff_only:
            failures.append("Pure Hermes pass-through performed execution.")

        safe_chat = adapter.chat(
            HermesChatRequest(
                mode=RuntimeInterfaceMode.shell_guarded,
                query="Summarize the current UAA safe refs.",
                operator_submission_acknowledged=True,
            ),
            idempotency_ref="idempotency-ref:hermes-interface-mode-safe-chat",
        )
        if safe_chat.raw_prompt_persisted or safe_chat.raw_output_persisted:
            failures.append("Hermes chat receipt persisted raw prompt or raw output.")
        if safe_chat.query_ref.startswith("Summarize"):
            failures.append("Hermes chat receipt exposed raw query text.")
    finally:
        if previous_enabled is None:
            os.environ.pop(HERMES_INTERFACE_MODE_ENABLED_ENV, None)
        else:
            os.environ[HERMES_INTERFACE_MODE_ENABLED_ENV] = previous_enabled

    payload = {
        "schema_version": "hermes_interface_mode_verifier_report.v1",
        "ok": not failures,
        "failures": failures,
        "disabled_interface_mode": disabled_interface.model_dump(mode="json"),
        "disabled_context_projection_enabled": disabled_context_pack.projection_enabled,
        "interface_mode": interface.model_dump(mode="json"),
        "context_pack_ref": context_pack.context_pack_ref,
        "context_section_count": context_pack.section_count,
        "pass_through_receipt": blocked.model_dump(mode="json"),
        "safe_chat_receipt": safe_chat.model_dump(mode="json"),
        "raw_memory_exposed": context_pack.raw_memory_records_exposed,
        "raw_crm_exposed": context_pack.raw_crm_records_exposed,
        "raw_chat_exposed": context_pack.raw_chat_transcripts_exposed,
        "direct_memory_write_enabled": context_pack.direct_memory_write_enabled,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
