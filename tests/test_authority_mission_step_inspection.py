from datetime import timedelta
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from scripts.dev import uaa_runtime
from tests.test_authority_mission_runner import _runner_request
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import (
    build_api_manifest,
    route_classification_for_path,
    route_side_effect_class,
)
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.authority.dispatcher import (
    AUTHORITY_DISPATCH_LEDGER_MAX_BYTES,
    AUTHORITY_DISPATCH_LEDGER_MAX_RECEIPTS,
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MISSION_STEP_LEDGER_MAX_BYTES,
    MISSION_STEP_LEDGER_MAX_RECEIPTS,
    MissionStepCorruptionError,
    MissionStepDefinition,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_runner import AuthorityMissionRunner
from ultimate_ai_agent.core.execution.mission_step_inspection import (
    build_mission_step_inspection_read_model,
)
from ultimate_ai_agent.core.time import utc_now


client = TestClient(app)


def _definition(*, deadline=None) -> MissionStepDefinition:
    return MissionStepDefinition(
        mission_ref="mission-ref:identity@marker",
        run_ref="run-ref:scope/segment",
        step_ref="mission-step-ref:test:inspection",
        capability_ref="capability-ref:scope/segment",
        adapter_ref="adapter-ref:identity@marker",
        lease_ref="lease-ref:scope/segment",
        deadline=deadline or utc_now() + timedelta(minutes=5),
        safe_summary="Persisted operator text with identity@marker and path/fragment.",
    )


def _seed_claimed_step(state_dir: Path, *, current) -> MissionStepStore:
    store = MissionStepStore(state_dir, clock=lambda: current[0])
    definition = _definition(deadline=current[0] + timedelta(minutes=5))
    store.create(definition)
    store.claim(
        definition.step_ref,
        owner_ref="mission-owner-ref:identity@marker",
        ttl_seconds=300,
    )
    return store


def _enable_dev_api(monkeypatch: pytest.MonkeyPatch, state_dir: Path) -> None:
    monkeypatch.setenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, "1")
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))


def _without_volatile_authority_times(value):
    if isinstance(value, dict):
        return {
            key: _without_volatile_authority_times(item)
            for key, item in value.items()
            if key not in {"decided_at", "issued_at", "expires_at"}
        }
    if isinstance(value, list):
        return [_without_volatile_authority_times(item) for item in value]
    return value


def test_inspection_validates_orchestrated_blocked_and_halted_plan_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="inspection-terminal-plan-evidence",
        dependency_graph=[[], [0], [1], []],
        operation_limit=1,
        shared_state=True,
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:inspection-terminal-plan-evidence",
    )
    assert [step.status for step in result.steps] == [
        MissionStepStatus.succeeded.value,
        MissionStepStatus.failed.value,
        MissionStepStatus.dependency_blocked.value,
        MissionStepStatus.fail_fast_halted.value,
    ]

    blocked = build_mission_step_inspection_read_model(
        request.steps[2].definition.step_ref,
        state_dir=dispatcher.state_dir,
    )
    halted = build_mission_step_inspection_read_model(
        request.steps[3].definition.step_ref,
        state_dir=dispatcher.state_dir,
    )
    assert blocked.durable_status == MissionStepStatus.dependency_blocked.value
    assert halted.durable_status == MissionStepStatus.fail_fast_halted.value
    assert blocked.request_scoped_authority_required is True
    assert halted.execution_authority_granted is False

    _enable_dev_api(monkeypatch, dispatcher.state_dir)
    response = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": request.steps[3].definition.step_ref},
    )
    assert response.status_code == 200
    api_projection = response.json()["data"]["mission_step_inspection"]
    exit_code = uaa_runtime.main(
        [
            "--state-dir",
            str(dispatcher.state_dir),
            "inspect-authority-mission-step",
            request.steps[3].definition.step_ref,
            "--json",
        ]
    )
    assert exit_code == 0
    cli_projection = json.loads(capsys.readouterr().out)["mission_step_inspection"]
    assert api_projection["durable_status"] == "fail_fast_halted"
    assert cli_projection["durable_status"] == "fail_fast_halted"


def test_api_and_cli_share_redacted_backend_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "private-state"
    current = [utc_now()]
    _seed_claimed_step(state_dir, current=current)
    _enable_dev_api(monkeypatch, state_dir)
    ledger_before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in state_dir.glob("*.jsonl")
    }

    baseline = client.get("/api/runtime/authority-state").json()
    response = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": _definition().step_ref},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    api_projection = body["data"].pop("mission_step_inspection")
    assert "mission_step_inspection" not in baseline["data"]
    assert _without_volatile_authority_times(
        body["data"]
    ) == _without_volatile_authority_times(baseline["data"])
    assert body["operation"] == baseline["operation"]
    assert body["service"] == baseline["service"]

    exit_code = uaa_runtime.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-authority-mission-step",
            _definition().step_ref,
            "--json",
        ]
    )
    assert exit_code == 0
    cli_payload = json.loads(capsys.readouterr().out)
    cli_projection = cli_payload["mission_step_inspection"]
    for projection in [api_projection, cli_projection]:
        projection.pop("observed_at")
    assert cli_projection == api_projection
    assert api_projection["durable_status"] == MissionStepStatus.claimed.value
    assert api_projection["claim_freshness"] == "active"
    assert api_projection["execution_authority_granted"] is False
    assert api_projection["request_scoped_authority_required"] is True
    assert api_projection["adapter_invocation_performed"] is False
    assert api_projection["autonomous_retry_performed"] is False
    combined = response.text + json.dumps(cli_payload)
    assert str(state_dir) not in combined
    assert "identity@marker" not in combined
    assert "scope/segment" not in combined
    assert "path/fragment" not in combined
    assert _definition().safe_summary not in combined
    ledger_after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in state_dir.glob("*.jsonl")
    }
    assert ledger_after == ledger_before


def test_text_cli_is_primary_and_claim_freshness_can_expire(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "state"
    current = [utc_now()]
    definition = _definition(deadline=current[0] + timedelta(minutes=5))
    store = MissionStepStore(state_dir, clock=lambda: current[0])
    store.create(definition)
    store.claim(
        definition.step_ref,
        owner_ref="mission-owner-ref:test:inspection",
        ttl_seconds=1,
    )
    current[0] += timedelta(seconds=2)

    inspection = build_mission_step_inspection_read_model(
        definition.step_ref,
        state_dir=state_dir,
        clock=lambda: current[0],
    )
    assert inspection.durable_status == MissionStepStatus.claimed.value
    assert inspection.claim_freshness == "expired"

    exit_code = uaa_runtime.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-authority-mission-step",
            definition.step_ref,
        ]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Authority mission step inspection" in output
    assert "Inspection grants execution authority: false" in output
    assert "Request-scoped authority still required: true" in output
    assert not output.lstrip().startswith("{")
    assert str(state_dir) not in output
    assert "identity@marker" not in output
    assert "scope/segment" not in output
    assert "path/fragment" not in output
    assert "Durable status: claimed" in output
    assert "Reasons: none" in output
    assert "Evidence: none" in output


def test_success_inspection_requires_validated_dispatch_ledger(tmp_path: Path) -> None:
    _, dispatcher, _, _, definition, request, root = _runner_request(
        tmp_path,
        "inspection-success",
    )
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(dispatcher.state_dir),
    )
    result = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:inspection-success",
    )
    assert result.step.status == MissionStepStatus.succeeded.value

    inspection = build_mission_step_inspection_read_model(
        definition.step_ref,
        state_dir=dispatcher.state_dir,
    )
    assert inspection.durable_status == MissionStepStatus.succeeded.value
    assert inspection.dispatch_receipt_safe_ref is not None
    assert inspection.dispatch_binding_validated is True
    assert inspection.reason_safe_refs
    assert inspection.evidence_safe_refs
    assert str(root) not in inspection.model_dump_json()
    raw_refs = [
        *result.step.reason_refs,
        *result.step.evidence_refs,
        result.step.dispatch_ref,
        result.step.dispatch_receipt_ref,
    ]
    projection_json = inspection.model_dump_json()
    assert all(ref not in projection_json for ref in raw_refs if ref is not None)

    dispatcher.receipts_path.write_text("invalid dispatch ledger", encoding="utf-8")
    with pytest.raises(AuthorityDispatchCorruptionError):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=dispatcher.state_dir,
        )


def test_claimed_dispatch_binding_must_match_durable_dispatch(tmp_path: Path) -> None:
    _, dispatcher, _, _, definition, request, _ = _runner_request(
        tmp_path,
        "inspection-claimed-binding",
    )
    store = MissionStepStore(dispatcher.state_dir)
    store.create(definition)
    store.claim(
        definition.step_ref,
        owner_ref="mission-owner-ref:test:binding",
        ttl_seconds=30,
        dispatch_ref=request.dispatch_ref,
        dispatch_request_fingerprint_ref=(
            "request-fingerprint-ref:mission-step:mismatched"
        ),
    )
    dispatcher.prepare(request)

    with pytest.raises(
        MissionStepCorruptionError,
        match="MISSION_STEP_DISPATCH_BINDING_INVALID",
    ):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=dispatcher.state_dir,
        )


def test_missing_unknown_corrupt_and_oversized_state_are_distinct_and_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "state"
    _enable_dev_api(monkeypatch, state_dir)
    requested_ref = "mission-step-ref:test:missing"

    invalid = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": "malformed ref"},
    ).json()
    assert invalid["error"]["code"] == "MISSION_STEP_REF_INVALID"

    missing = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": requested_ref},
    ).json()
    assert missing["error"]["code"] == "MISSION_STEP_INSPECTION_NOT_INITIALIZED"

    store = MissionStepStore(state_dir)
    store.create(_definition())
    unknown = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": requested_ref},
    ).json()
    assert unknown["error"]["code"] == "MISSION_STEP_NOT_FOUND"

    store.receipts_path.write_text("not-json", encoding="utf-8")
    corrupt = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": requested_ref},
    ).json()
    assert corrupt["error"]["code"] == "MISSION_STEP_INSPECTION_UNAVAILABLE"
    assert str(state_dir) not in json.dumps(corrupt)
    assert "not-json" not in json.dumps(corrupt)

    store.receipts_path.write_bytes(b"x" * (MISSION_STEP_LEDGER_MAX_BYTES + 1))
    exit_code = uaa_runtime.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-authority-mission-step",
            requested_ref,
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "Mission step inspection: local state could not be validated.\n"
    )
    assert str(state_dir) not in captured.err


def test_auth_gate_runs_before_mission_state_distinction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "state"
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, "inspection-local-bearer")
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))

    response = client.get(
        "/api/runtime/authority-state",
        params={"mission_step_ref": "mission-step-ref:test:missing"},
    )
    assert response.status_code == 401
    assert "NOT_INITIALIZED" not in response.text
    assert str(state_dir) not in response.text


def test_dispatch_ledger_bounds_and_mission_symlinks_fail_closed(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "state"
    store = MissionStepStore(state_dir)
    definition = _definition()
    store.create(definition)
    dispatcher = AuthorityDispatcher(state_dir, adapters=[])
    dispatcher.receipts_path.write_bytes(
        b"x" * (AUTHORITY_DISPATCH_LEDGER_MAX_BYTES + 1)
    )

    with pytest.raises(AuthorityDispatchCorruptionError):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=state_dir,
        )

    dispatcher.receipts_path.unlink()
    ledger_payload = store.receipts_path.read_bytes()
    linked_payload = tmp_path / "linked-ledger"
    linked_payload.write_bytes(ledger_payload)
    store.receipts_path.unlink()
    store.receipts_path.symlink_to(linked_payload)
    with pytest.raises(
        MissionStepCorruptionError,
        match="MISSION_STEP_LEDGER_READ_FAILED",
    ):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=state_dir,
        )


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO is POSIX-only")
def test_nonregular_and_dangling_ledger_paths_fail_closed(tmp_path: Path) -> None:
    mission_fifo_state = tmp_path / "mission-fifo"
    mission_fifo_state.mkdir()
    mission_fifo = MissionStepStore(mission_fifo_state).receipts_path
    os.mkfifo(mission_fifo)
    with pytest.raises(MissionStepCorruptionError):
        build_mission_step_inspection_read_model(
            "mission-step-ref:test:fifo",
            state_dir=mission_fifo_state,
        )

    dispatch_fifo_state = tmp_path / "dispatch-fifo"
    store = MissionStepStore(dispatch_fifo_state)
    definition = _definition()
    store.create(definition)
    dispatch_fifo = AuthorityDispatcher(
        dispatch_fifo_state,
        adapters=[],
    ).receipts_path
    os.mkfifo(dispatch_fifo)
    with pytest.raises(AuthorityDispatchCorruptionError):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=dispatch_fifo_state,
        )

    dangling_mission_state = tmp_path / "dangling-mission"
    dangling_mission_state.mkdir()
    dangling_mission = MissionStepStore(dangling_mission_state).receipts_path
    dangling_mission.symlink_to(tmp_path / "absent-mission-ledger")
    with pytest.raises(MissionStepCorruptionError):
        build_mission_step_inspection_read_model(
            "mission-step-ref:test:dangling",
            state_dir=dangling_mission_state,
        )

    dangling_dispatch_state = tmp_path / "dangling-dispatch"
    dangling_store = MissionStepStore(dangling_dispatch_state)
    dangling_definition = _definition()
    dangling_store.create(dangling_definition)
    dangling_dispatch = AuthorityDispatcher(
        dangling_dispatch_state,
        adapters=[],
    ).receipts_path
    dangling_dispatch.symlink_to(tmp_path / "absent-dispatch-ledger")
    with pytest.raises(AuthorityDispatchCorruptionError):
        build_mission_step_inspection_read_model(
            dangling_definition.step_ref,
            state_dir=dangling_dispatch_state,
        )


@pytest.mark.parametrize(
    ("ledger_kind", "payload"),
    [
        ("mission", b"\xff"),
        ("dispatch", b"\xff"),
        ("mission", b"\n" * (MISSION_STEP_LEDGER_MAX_RECEIPTS + 1)),
        ("dispatch", b"\n" * (AUTHORITY_DISPATCH_LEDGER_MAX_RECEIPTS + 1)),
    ],
)
def test_ledger_encoding_and_receipt_count_limits_fail_closed(
    tmp_path: Path,
    ledger_kind: str,
    payload: bytes,
) -> None:
    state_dir = tmp_path / ledger_kind
    store = MissionStepStore(state_dir)
    definition = _definition()
    store.create(definition)
    dispatcher = AuthorityDispatcher(state_dir, adapters=[])
    path = store.receipts_path if ledger_kind == "mission" else dispatcher.receipts_path
    path.write_bytes(payload)
    expected_error = (
        MissionStepCorruptionError
        if ledger_kind == "mission"
        else AuthorityDispatchCorruptionError
    )
    with pytest.raises(expected_error):
        build_mission_step_inspection_read_model(
            definition.step_ref,
            state_dir=state_dir,
        )


def test_manifest_and_openapi_keep_existing_protected_route_contract() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    assert (
        "authority_mission_step_read_only_inspection"
        in manifest["capabilities_declared"]
    )
    assert (
        "authority_mission_step_inspection_as_execution_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "authority_mission_step_inspection_mutation_or_retry"
        in manifest["capabilities_blocked"]
    )
    route = next(
        item
        for item in manifest["routes"]
        if item["path"] == "/api/runtime/authority-state"
    )
    assert route["route_classification"] == "local_sensitive"
    assert route["side_effect_class"] == "local_dev_workspace_only"
    assert route["protected_route"] is True
    assert route["operation_id"] == "get_api_runtime_authority_state"
    assert route_side_effect_class(route["path"]).value == "local_dev_workspace_only"
    classification, _ = route_classification_for_path(
        "GET",
        route["path"],
        route_side_effect_class(route["path"]),
    )
    assert classification.value == "local_sensitive"

    operation = app.openapi()["paths"]["/api/runtime/authority-state"]["get"]
    assert operation["operationId"] == "get_api_runtime_authority_state"
    parameter = next(
        item for item in operation["parameters"] if item["name"] == "mission_step_ref"
    )
    assert parameter["required"] is False
    string_schema = next(
        item for item in parameter["schema"]["anyOf"] if item.get("type") == "string"
    )
    assert string_schema["maxLength"] == 320
    assert string_schema["minLength"] == 1
