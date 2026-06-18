from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.capabilities import (  # noqa: E402
    DETERMINISTIC_WORKFLOW_CAPABILITY_ID,
    EXTERNAL_ACTION_GATE_CAPABILITY_ID,
    LOCAL_FILE_METADATA_CAPABILITY_ID,
    LOCAL_FILE_WRITE_CAPABILITY_ID,
    M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID,
    Coordinator,
    build_live_local_testing_runtime,
)
from ultimate_ai_agent.core.model_runtime import (  # noqa: E402
    FakeLocalModelCallTransport,
    LocalModelCallRequest,
    LocalModelRuntimeKind,
    build_m23_fixed_prompt,
    local_model_call_approval_request,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="uaa-live-capability-") as workspace:
        workspace_path = Path(workspace)
        (workspace_path / "input.txt").write_text("live local smoke\n", encoding="utf-8")

        runtime = build_live_local_testing_runtime(workspace_path)
        coordinator = Coordinator(runtime.registry)

        metadata = coordinator.run(
            "Read live-local metadata",
            {
                "capability_ids": [LOCAL_FILE_METADATA_CAPABILITY_ID],
                "path": "input.txt",
                "include_preview": True,
            },
        )
        fanout = coordinator.run(
            "Read and compose live-local state",
            {
                "capability_ids": [LOCAL_FILE_METADATA_CAPABILITY_ID, DETERMINISTIC_WORKFLOW_CAPABILITY_ID],
                "parallel_read_fanout": True,
                "path": "input.txt",
                "workflow_inputs": {"smoke": True, "step": 3},
            },
        )
        coordinator.run(
            "Write one approved live-local file",
            {
                "capability_ids": [LOCAL_FILE_WRITE_CAPABILITY_ID],
                "target_path": "out/result.txt",
                "new_content": "live local write complete\n",
                "idempotency_key": "live-local-smoke-write-1",
                "approval_ref": "approval_live_local_smoke",
                "apply_write": True,
            },
        )
        model = _run_fake_m23_smoke(coordinator)
        external_gate = coordinator.run(
            "Gate an external action",
            {
                "capability_ids": [EXTERNAL_ACTION_GATE_CAPABILITY_ID],
                "requested_external_action": "provider_call",
            },
        )

        payload = {
            "ok": True,
            "workspace_removed_on_exit": True,
            "metadata_capability": metadata.content[0]["producer_capability_id"],
            "fanout_artifact_count": fanout.metadata["artifact_count"],
            "write_applied": (workspace_path / "out" / "result.txt").read_text(encoding="utf-8"),
            "model_call_performed": model.content[0]["content"]["transport_result"]["call_performed"],
            "model_output_non_authoritative": model.content[0]["content"]["receipt"]["model_output_non_authoritative"],
            "external_gate_allowed": external_gate.content[0]["content"]["allowed"],
            "external_gate_reasons": external_gate.content[0]["content"]["reason_codes"],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _run_fake_m23_smoke(coordinator: Coordinator):
    request = _m23_request(dry_run=False, execute_local_call=True, approval_ref="approval_m23")
    approval_request = local_model_call_approval_request(request)
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    request = request.model_copy(update={"approval_ref": grant.approval_ref})
    decision = authority.validate_for_request(
        approval_request.model_copy(update={"resource_refs": [request.endpoint_url, request.model_ref]}),
        grant.approval_ref,
    )
    transport = FakeLocalModelCallTransport(response_text="UAA_M23_LOCAL_MODEL_CALL_OK")
    return coordinator.run(
        "Run fixed local model smoke",
        {
            "capability_ids": [M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID],
            "approval_ref": grant.approval_ref,
            "local_model_request": request,
            "local_model_approval_decision": decision,
            "local_model_transport": transport,
        },
    )


def _m23_request(**overrides) -> LocalModelCallRequest:
    prompt = build_m23_fixed_prompt()
    payload = {
        "request_id": "m23_live_smoke_req_1",
        "run_id": "run_m23_live_smoke",
        "runtime_kind": LocalModelRuntimeKind.ollama_planned,
        "endpoint_url": "http://127.0.0.1:11434/api/generate",
        "safe_endpoint_label": "loopback ollama local endpoint",
        "model_ref": "local-model-ref",
        "fixed_prompt_id": prompt.prompt_id,
        "prompt_text": prompt.prompt_text,
        "approval_ref": None,
    }
    payload.update(overrides)
    return LocalModelCallRequest(**payload)


if __name__ == "__main__":
    raise SystemExit(main())
