#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.execution import DurableRunRecord, DurableRunState  # noqa: E402
from ultimate_ai_agent.core.task_decomposition.runtime import (  # noqa: E402
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionService,
)


def _service(root: Path) -> TaskDecompositionService:
    service = TaskDecompositionService(
        registry_store=CapabilityRegistryStore(
            CapabilityRegistryStoreConfig(
                registry_path=str(root / "task-registry.json")
            )
        )
    )
    service.ensure_examples()
    return service


def _append_run_state(
    service: TaskDecompositionService,
    *,
    run_ref: str,
    state: DurableRunState,
    suffix: str,
) -> None:
    failure_refs = []
    if state in {DurableRunState.blocked, DurableRunState.dead_lettered}:
        failure_refs = [f"failure-ref:durable-orchestration:{suffix}"]
    restart_refs = []
    if state in {DurableRunState.restart_recovery, DurableRunState.dead_lettered}:
        restart_refs = [f"restart-ref:durable-orchestration:{suffix}"]
    service.durable_run_storage.append_run_record(
        DurableRunRecord(
            run_id=run_ref,
            source_ref=f"source-ref:durable-orchestration:{suffix}",
            state=state,
            safe_summary=f"State-only durable orchestration {suffix} summary.",
            evidence_refs=[f"evidence-ref:durable-orchestration:{suffix}"],
            failure_refs=failure_refs,
            restart_refs=restart_refs,
        ),
        idempotency_key=f"idempotency-ref:durable-orchestration:{suffix}",
        audit_ref=f"audit-ref:durable-orchestration:{suffix}",
        receipt_ref=f"receipt-ref:durable-orchestration:{suffix}",
        rollback_ref=f"rollback-ref:durable-orchestration:{suffix}",
        safe_summary=f"State-only durable orchestration {suffix} checkpoint.",
        evidence_refs=[f"evidence-ref:durable-orchestration:{suffix}"],
    )


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="uaa-durable-orchestration-") as temp:
        service = _service(Path(temp))
        run_ref = "task-decomposition-run:durable-orchestration-verifier"
        _append_run_state(
            service,
            run_ref=run_ref,
            state=DurableRunState.created,
            suffix="created",
        )
        _append_run_state(
            service,
            run_ref=run_ref,
            state=DurableRunState.restart_recovery,
            suffix="restart-recovery",
        )
        _append_run_state(
            service,
            run_ref=run_ref,
            state=DurableRunState.dead_lettered,
            suffix="dead-letter",
        )
        observability = service.run_observability(run_ref)

    required_fields = [
        "current_phase_ref",
        "current_phase_status",
        "current_step_ref",
        "current_step_status",
        "checkpoint_summaries",
        "retry_recovery_posture",
        "approval_wait_state",
        "cancellation_dead_letter_state",
        "redacted_error_summaries",
    ]
    for field in required_fields:
        if field not in observability:
            failures.append(f"Run Observability missing {field}")

    if not observability.get("checkpoint_summaries"):
        failures.append("Run Observability checkpoint summaries are empty")
    retry = observability.get("retry_recovery_posture") or {}
    if retry.get("retry_execution_enabled") is not False:
        failures.append("Retry execution must remain disabled")
    if retry.get("recovery_execution_enabled") is not False:
        failures.append("Recovery execution must remain disabled")
    wait = observability.get("approval_wait_state") or {}
    if wait.get("approval_refs_are_identifiers_only") is not True:
        failures.append("Approval refs must remain identifiers only")
    if wait.get("approval_ref_grants_authority") is not False:
        failures.append("Approval refs must not grant authority")
    cancel = observability.get("cancellation_dead_letter_state") or {}
    if cancel.get("cancel_execution_enabled") is not False:
        failures.append("Cancel execution must remain disabled")
    if cancel.get("dead_letter_execution_enabled") is not False:
        failures.append("Dead-letter execution must remain disabled")
    errors = observability.get("redacted_error_summaries") or []
    if not errors:
        failures.append("Redacted error summaries are empty")
    for error in errors:
        if error.get("raw_error_omitted") is not True:
            failures.append("Raw error content must be omitted")

    for denied_flag in [
        "ui_mutation_controls_enabled",
        "cancel_resume_controls_enabled",
        "live_streaming_runtime_enabled",
        "provider_model_calls_enabled",
        "tool_execution_enabled",
        "connector_writes_enabled",
        "connector_sends_enabled",
        "background_worker_enabled",
        "scheduler_enabled",
        "autonomous_execution_enabled",
        "production_authority_enabled",
    ]:
        if observability.get(denied_flag) is not False:
            failures.append(f"Run Observability broadened authority: {denied_flag}")

    manifest = build_api_manifest(app)
    route_index = {(route.method, route.path): route for route in manifest.routes}
    route = route_index.get(("GET", "/control-center/runs/observability"))
    if route is None:
        failures.append("GET /control-center/runs/observability missing from manifest")
    else:
        if route.side_effect_class != "validation_only":
            failures.append("Run Observability route side-effect class drifted")
        if route.route_classification != "local_readonly":
            failures.append("Run Observability route classification drifted")

    docs = [
        ROOT / "docs/control_center/UAA_GOATCITADEL_CATCHUP_DURABLE_ORCHESTRATION.md",
        ROOT / "docs/control_center/UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md",
    ]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        if "GET /control-center/runs/observability" not in text:
            failures.append(f"Run Observability route ref missing from {doc}")
        if "retry/recovery" not in text.lower():
            failures.append(f"retry/recovery posture missing from {doc}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA GoatCitadel catch-up durable orchestration verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
