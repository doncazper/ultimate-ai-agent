import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities import (
    DETERMINISTIC_WORKFLOW_CAPABILITY_ID,
    EXTERNAL_ACTION_GATE_CAPABILITY_ID,
    LOCAL_FILE_METADATA_CAPABILITY_ID,
    LOCAL_FILE_WRITE_CAPABILITY_ID,
    M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID,
    Coordinator,
    PolicyDeniedError,
    build_live_local_testing_runtime,
)
from ultimate_ai_agent.core.model_runtime import (
    FakeLocalModelCallTransport,
    LocalModelCallRequest,
    LocalModelRuntimeKind,
    build_m23_fixed_prompt,
    local_model_call_approval_request,
)


def test_live_local_registry_reads_actual_file_metadata(tmp_path) -> None:
    target = tmp_path / "notes.txt"
    target.write_text("hello from live local metadata\n", encoding="utf-8")
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)

    artifact = coordinator.run(
        "read local file metadata",
        {
            "capability_ids": [LOCAL_FILE_METADATA_CAPABILITY_ID],
            "path": "notes.txt",
            "include_preview": True,
            "max_preview_bytes": 64,
        },
    )

    result = artifact.content[0]
    assert result["producer_capability_id"] == LOCAL_FILE_METADATA_CAPABILITY_ID
    assert result["content"]["file_ref"]["path"] == "notes.txt"
    assert result["content"]["file_ref"]["size_bytes"] == target.stat().st_size
    assert result["content"]["preview"]["text_preview"] == "hello from live local metadata\n"
    assert result["side_effects_performed"] == ["file_metadata_read"]


def test_live_local_single_writer_applies_actual_file_write(tmp_path) -> None:
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)

    artifact = coordinator.run(
        "write one local file",
        {
            "capability_ids": [LOCAL_FILE_WRITE_CAPABILITY_ID],
            "target_path": "out/live.txt",
            "new_content": "live write complete\n",
            "idempotency_key": "write-live-1",
            "approval_ref": "approval_live_local_write",
            "apply_write": True,
        },
    )

    assert (tmp_path / "out" / "live.txt").read_text(encoding="utf-8") == "live write complete\n"
    result = artifact.content[0]
    assert result["kind"] == "live_local.file_change"
    assert result["content"]["decision"]["allowed"] is True
    assert result["content"]["change"]["target_path"] == "out/live.txt"
    assert artifact.side_effects_performed == ["file_write"]


def test_live_local_writer_requires_approval_before_execution(tmp_path) -> None:
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)

    with pytest.raises(PolicyDeniedError) as exc_info:
        coordinator.run(
            "write one local file",
            {
                "capability_ids": [LOCAL_FILE_WRITE_CAPABILITY_ID],
                "target_path": "blocked.txt",
                "new_content": "blocked\n",
                "idempotency_key": "write-blocked-1",
                "apply_write": True,
            },
        )

    assert "CAPABILITY_APPROVAL_REQUIRED" in exc_info.value.reason_codes
    assert not (tmp_path / "blocked.txt").exists()


def test_live_local_read_fanout_runs_metadata_and_workflow(tmp_path) -> None:
    (tmp_path / "readme.txt").write_text("fanout\n", encoding="utf-8")
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)

    artifact = coordinator.run(
        "read and compose",
        {
            "capability_ids": [LOCAL_FILE_METADATA_CAPABILITY_ID, DETERMINISTIC_WORKFLOW_CAPABILITY_ID],
            "parallel_read_fanout": True,
            "path": "readme.txt",
            "workflow_inputs": {"step": 3, "label": "compose"},
        },
    )

    assert artifact.metadata["artifact_count"] == 2
    assert {item["producer_capability_id"] for item in artifact.content} == {
        LOCAL_FILE_METADATA_CAPABILITY_ID,
        DETERMINISTIC_WORKFLOW_CAPABILITY_ID,
    }
    workflow = next(item for item in artifact.content if item["producer_capability_id"] == DETERMINISTIC_WORKFLOW_CAPABILITY_ID)
    assert workflow["content"]["input_keys"] == ["label", "step"]
    assert workflow["content"]["deterministic_digest"]


def test_live_local_parallel_or_multiple_writers_are_denied(tmp_path) -> None:
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)
    plan = coordinator.plan(
        "write twice",
        {
            "capability_ids": [LOCAL_FILE_WRITE_CAPABILITY_ID, LOCAL_FILE_WRITE_CAPABILITY_ID],
            "target_path": "multi.txt",
            "new_content": "multi\n",
            "idempotency_key": "write-multi-1",
            "approval_ref": "approval_live_local_write",
            "apply_write": True,
        },
    )

    with pytest.raises(PolicyDeniedError) as exc_info:
        coordinator.execute(plan, {"approval_ref": "approval_live_local_write"})

    assert "MULTIPLE_WRITER_NODES_DENIED" in exc_info.value.reason_codes
    assert not (tmp_path / "multi.txt").exists()


def test_live_local_m23_model_loopback_uses_existing_approval_policy(tmp_path) -> None:
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)
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

    artifact = coordinator.run(
        "run fixed local model smoke",
        {
            "capability_ids": [M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID],
            "approval_ref": grant.approval_ref,
            "local_model_request": request,
            "local_model_approval_decision": decision,
            "local_model_transport": transport,
        },
    )

    result = artifact.content[0]
    assert transport.calls == 1
    assert result["content"]["decision"]["allowed"] is True
    assert result["content"]["receipt"]["model_output_non_authoritative"] is True
    assert result["side_effects_performed"] == ["loopback_local_model_call"]


def test_live_local_external_action_gate_returns_structured_denial(tmp_path) -> None:
    runtime = build_live_local_testing_runtime(tmp_path)
    coordinator = Coordinator(runtime.registry)

    artifact = coordinator.run(
        "send an external request",
        {
            "capability_ids": [EXTERNAL_ACTION_GATE_CAPABILITY_ID],
            "requested_external_action": "provider_call",
        },
    )

    result = artifact.content[0]
    assert result["content"]["allowed"] is False
    assert result["content"]["reason_codes"] == ["EXTERNAL_AUTHORITY_NOT_GRANTED", "REVIEWED_ADAPTER_REQUIRED"]
    assert artifact.side_effects_performed == []


def _m23_request(**overrides) -> LocalModelCallRequest:
    prompt = build_m23_fixed_prompt()
    payload = {
        "request_id": "m23_live_req_1",
        "run_id": "run_m23_live",
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
