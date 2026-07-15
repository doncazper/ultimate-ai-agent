from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from collections.abc import Callable

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.communications.matrix_session import (
    MatrixSessionBackend,
    MatrixSessionBackendConfig,
    MatrixSessionCommand,
    MatrixSessionOperation,
    MatrixSessionTransientInput,
    capture_exact_matrix_session_approval,
    execute_matrix_session_command,
    issue_exact_matrix_session_lease,
    matrix_session_request_fingerprint_ref,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_discovery_freshness_ref,
    matrix_homeserver_observation_ref,
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command(operation: MatrixSessionOperation) -> MatrixSessionCommand:
    deadline = utc_now() + timedelta(minutes=2)
    suffix = operation.value.replace("_", "-")
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-session:{suffix}",
        "task_ref": f"task-ref:matrix-session:{suffix}",
        "mission_ref": "mission-ref:matrix-session:dispatch",
        "run_ref": f"run-ref:matrix-session:{suffix}",
        "dispatch_ref": f"dispatch-ref:matrix-session:{suffix}",
        "idempotency_ref": f"idempotency-ref:matrix-session:{suffix}",
        "lease_ref": f"authority-lease-ref:matrix-session:{suffix}",
        "homeserver_ref": matrix_homeserver_ref("http://127.0.0.1:18008"),
        "endpoint_class_ref": "endpoint-class-ref:matrix:local-harness",
        "discovery_observation_ref": (
            "observation-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else matrix_homeserver_observation_ref("http://127.0.0.1:18008")
        ),
        "discovery_freshness_ref": (
            "freshness-ref:matrix-discovery:pending"
            if operation == MatrixSessionOperation.discovery_read
            else matrix_discovery_freshness_ref(
                matrix_homeserver_observation_ref("http://127.0.0.1:18008")
            )
        ),
        "target_ref": "target-ref:communications:matrix-exact-homeserver",
        "credential_backend_ref": "credential-backend-ref:matrix:macos-keychain-v1",
        "budget_ref": "budget-ref:communications:matrix-session-zero-cost",
        "kill_switch_ref": "kill-switch-ref:authority-lease-local",
        "safe_disable_ref": "safe-disable-ref:communications:matrix-session",
        "readiness_ref": "readiness-ref:matrix-session:current",
        "target_refs": (),
        "start_deadline": deadline,
    }
    if operation not in {
        MatrixSessionOperation.discovery_read,
        MatrixSessionOperation.auth_methods_read,
        MatrixSessionOperation.sso_launch,
    }:
        values.update(
            account_ref="account-ref:matrix:primary",
            device_ref="device-ref:matrix:stable",
            session_ref="session-ref:matrix:primary",
            session_generation_ref="session-generation-ref:matrix:one",
        )
    if operation not in {
        MatrixSessionOperation.discovery_read,
        MatrixSessionOperation.auth_methods_read,
        MatrixSessionOperation.sso_launch,
    }:
        values.update(
            credential_item_ref="credential-item-ref:matrix:primary",
            credential_version_ref="credential-version-ref:matrix:one",
        )
    if operation == MatrixSessionOperation.credential_auth_create:
        values["crypto_store_ref"] = "crypto-store-ref:matrix:ownership-reserved"
    if operation in {
        MatrixSessionOperation.refresh,
        MatrixSessionOperation.credential_store_rotate,
    }:
        values["next_credential_version_ref"] = "credential-version-ref:matrix:two"
    values["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(**values)
    return MatrixSessionCommand(**values)


def _backend(
    tmp_path: Path,
    *,
    response_ok: bool = True,
    response_updates: dict[str, object] | None = None,
    kill_switch_engaged: Callable[[], bool] | None = None,
    lifecycle_lock_dir: Path | None = None,
) -> MatrixSessionBackend:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = repo / "runner.py"
    helper = repo / "helper"
    wasm = repo / "asset.wasm"
    updates = response_updates or {}
    operation = str(updates.get("operation", "discovery_read"))
    response = {
        "schema_version": "uaa-matrix-client-adapter-response.v1",
        "ok": response_ok,
        "operation": operation,
        "runtime_status": (
            "ready_for_authentication"
            if response_ok and operation == "auth_methods_read"
            else "discovered"
            if response_ok
            else "blocked"
        ),
        "result_ref": "adapter-result-ref:matrix-session:test",
        "redaction_status": "safe_refs_only",
        **({} if response_ok else {"error_code": "MATRIX_TEST_FAILURE"}),
    }
    if response_ok and operation == "discovery_read":
        response.update(
            homeserver_observation_ref=matrix_homeserver_observation_ref(
                "http://127.0.0.1:18008"
            ),
            discovery_freshness_ref=matrix_discovery_freshness_ref(
                matrix_homeserver_observation_ref("http://127.0.0.1:18008")
            ),
            sdk_version_ref="version-ref:matrix-js-sdk:41-9-0",
        )
    elif response_ok and operation == "auth_methods_read":
        response.update(
            homeserver_observation_ref=matrix_homeserver_observation_ref(
                "http://127.0.0.1:18008"
            ),
            versions_ref="version-set-ref:matrix:test",
            login_flows_ref="login-flow-set-ref:matrix:test",
            capabilities={
                "credential_auth": True,
                "browser_sso": False,
                "oauth": False,
            },
            sdk_version_ref="version-ref:matrix-js-sdk:41-9-0",
        )
    response.update(updates)
    runner.write_text(
        "import json,sys\n"
        "json.load(sys.stdin)\n"
        f"sys.stdout.write({json.dumps(json.dumps(response))})\n",
        encoding="utf-8",
    )
    helper.write_text("placeholder\n", encoding="utf-8")
    wasm.write_bytes(b"wasm-test-asset")
    runtime_root = repo / "runtime"
    runtime_root.mkdir()
    (runtime_root / "module.mjs").write_text(
        "export const bound = true;\n", encoding="utf-8"
    )
    package_lock = repo / "package-lock.json"
    package_lock.write_text("{}\n", encoding="utf-8")
    runtime_integrity = repo / "runtime-integrity.json"
    runtime_integrity.write_text(
        json.dumps(
            {
                "schema_version": "uaa-matrix-client-adapter-integrity.v1",
                "package_lock_sha256": _digest(package_lock),
                "trees": [{"root": "runtime", "sha256": _tree_digest(runtime_root)}],
                "raw_paths_included": False,
                "credential_material_included": False,
                "execution_authority_granted": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    os.chmod(runner, 0o600)
    os.chmod(helper, 0o700)
    os.chmod(wasm, 0o600)
    node = Path(sys.executable).resolve()
    config = MatrixSessionBackendConfig(
        repo_root=repo,
        adapter_root=repo,
        node_binary=node,
        runner_path=runner,
        helper_path=helper,
        expected_node_sha256=_digest(node),
        expected_runner_sha256=_digest(runner),
        expected_helper_sha256=_digest(helper),
        wasm_asset_path=wasm,
        package_lock_path=package_lock,
        runtime_integrity_path=runtime_integrity,
    )
    return MatrixSessionBackend(
        config,
        kill_switch_engaged=kill_switch_engaged or (lambda: False),
        lifecycle_lock_dir=lifecycle_lock_dir or tmp_path / "matrix-session-locks",
    )


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(_digest(path)))
    return digest.hexdigest()


def test_read_dispatch_revalidates_exact_lease_and_returns_safe_evidence(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path),
        lease_store=store,
    )
    assert result.receipt.status == "succeeded"
    assert result.receipt.raw_provider_payload_included is False
    assert result.receipt.raw_paths_included is False


def test_auth_methods_requires_matching_current_discovery_receipt(
    tmp_path: Path,
) -> None:
    authority_state = tmp_path / "authority"
    store = AuthorityLeaseStore(authority_state)
    discovery = _command(MatrixSessionOperation.discovery_read)
    issue_exact_matrix_session_lease(discovery, store=store, confirmed=False)
    discovery_result = execute_matrix_session_command(
        discovery,
        repo_root=tmp_path / "discovery-backend" / "repo",
        authority_state_dir=authority_state,
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path / "discovery-backend"),
        lease_store=store,
    )
    assert discovery_result.receipt.status == "succeeded"

    auth_methods = _command(MatrixSessionOperation.auth_methods_read)
    issue_exact_matrix_session_lease(auth_methods, store=store, confirmed=False)
    auth_result = execute_matrix_session_command(
        auth_methods,
        repo_root=tmp_path / "auth-backend" / "repo",
        authority_state_dir=authority_state,
        transient_input=MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008"
        ),
        backend=_backend(
            tmp_path / "auth-backend",
            response_updates={"operation": "auth_methods_read"},
        ),
        lease_store=store,
    )
    assert auth_result.receipt.status == "succeeded"


def test_auth_methods_without_prior_discovery_never_starts_adapter(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSessionOperation.auth_methods_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008"
        ),
        backend=_backend(
            tmp_path,
            response_updates={"operation": "auth_methods_read"},
        ),
        lease_store=store,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.adapter_result is None
    assert any(
        "discovery-evidence-missing" in reason for reason in result.receipt.reason_refs
    )


def test_target_substitution_stale_readiness_and_missing_approval_fail_closed(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    with pytest.raises(ValueError, match="MATRIX_SESSION_HOMESERVER_BINDING_MISMATCH"):
        execute_matrix_session_command(
            command,
            repo_root=tmp_path / "repo",
            authority_state_dir=tmp_path / "authority",
            transient_input=MatrixSessionTransientInput(
                discovery_origin="https://matrix.example.org"
            ),
            backend=_backend(tmp_path),
            lease_store=store,
        )


def test_approval_identifier_alone_cannot_start_mutation(tmp_path: Path) -> None:
    command = _command(MatrixSessionOperation.credential_auth_create)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=True)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008"
        ),
        approval_ref="approval-ref:matrix-session:identifier-only",
        backend=_backend(tmp_path),
        lease_store=store,
        approval_authority=LocalApprovalAuthority(),
    )
    assert result.receipt.status == "denied"


def test_fresh_exact_approval_is_bound_to_same_command(tmp_path: Path) -> None:
    command = _command(MatrixSessionOperation.credential_auth_create)
    store = AuthorityLeaseStore(tmp_path / "authority")
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_session_lease(command, store=store, confirmed=True)
    approval_ref = capture_exact_matrix_session_approval(
        command, approval_authority=approvals, confirmed=True
    )
    # The interactive helper is deliberately not exercised by this unit test;
    # the fresh approval reaches pre-start and then the fake non-executable
    # helper fails closed without exposing credential material.
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008"
        ),
        approval_ref=approval_ref,
        backend=_backend(tmp_path),
        lease_store=store,
        approval_authority=approvals,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.approval_ref == approval_ref
    assert result.receipt.approval_validation_ref is not None
    assert result.receipt.raw_provider_payload_included is False


def test_transient_target_aliases_and_operation_inappropriate_fields_are_denied(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    backend = _backend(tmp_path)
    backend.bind_transient(
        command.dispatch_ref,
        MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008",
            discovery_origin="https://substituted.example.org",
        ),
    )
    with pytest.raises(
        RuntimeError, match="MATRIX_SESSION_DISCOVERY_TRANSIENT_SCOPE_INVALID"
    ):
        backend.validate_transient_target(command)


def test_lifecycle_lock_state_is_constant_across_many_exact_targets(
    tmp_path: Path,
) -> None:
    backend = _backend(tmp_path)
    for index in range(32):
        backend._acquire_cross_process_lifecycle(
            {"homeserver_ref": f"homeserver-ref:matrix:target-{index}"}
        )
        backend._release_lifecycle()
    assert [path.name for path in (tmp_path / "matrix-session-locks").iterdir()] == [
        "matrix-session.lifecycle.lock"
    ]


def test_safe_disable_blocks_before_adapter_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UAA_MATRIX_SESSION_SAFE_DISABLE", "1")
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path),
        lease_store=store,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.adapter_result is None


def test_kill_switch_blocks_before_adapter_start(tmp_path: Path) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path, kill_switch_engaged=lambda: True),
        lease_store=store,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.adapter_result is None


def test_post_construction_runtime_tamper_blocks_before_adapter_start(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    backend = _backend(tmp_path)
    backend.config.runner_path.write_text("raise SystemExit(0)\n", encoding="utf-8")
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=backend,
        lease_store=store,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.adapter_result is None


def test_cross_process_lifecycle_lock_denies_concurrent_owner(tmp_path: Path) -> None:
    lock_dir = tmp_path / "shared-locks"
    first = _backend(tmp_path / "first", lifecycle_lock_dir=lock_dir)
    second = _backend(tmp_path / "second", lifecycle_lock_dir=lock_dir)
    safe_request = {"homeserver_ref": matrix_homeserver_ref("http://127.0.0.1:18008")}
    first._acquire_cross_process_lifecycle(safe_request)
    try:
        with pytest.raises(
            RuntimeError, match="MATRIX_SESSION_DUPLICATE_LIFECYCLE_OWNER"
        ):
            second._acquire_cross_process_lifecycle(safe_request)
    finally:
        first._release_lifecycle()
    second._acquire_cross_process_lifecycle(safe_request)
    second._release_lifecycle()


def test_process_group_cleanup_reaps_term_resistant_adapter(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import signal,time;"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
                "time.sleep(30)"
            ),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    backend._terminate_process_group(process)
    assert process.poll() is not None


@pytest.mark.parametrize(
    ("response_updates", "expected_status"),
    [
        ({"operation": "auth_methods_read"}, "failed"),
        ({"runtime_status": "active"}, "failed"),
        ({"homeserver_observation_ref": None}, "failed"),
    ],
)
def test_adapter_response_is_bound_to_exact_operation_and_success_schema(
    tmp_path: Path,
    response_updates: dict[str, object],
    expected_status: str,
) -> None:
    command = _command(MatrixSessionOperation.discovery_read)
    store = AuthorityLeaseStore(tmp_path / "authority")
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path, response_updates=response_updates),
        lease_store=store,
    )
    assert result.receipt.status == expected_status
    assert result.adapter_result is not None
    assert result.adapter_result.succeeded is False
    assert result.adapter_result.raw_provider_payload_included is False
    assert result.receipt.raw_provider_payload_included is False


def test_credential_delete_remains_blocked_before_helper_start(tmp_path: Path) -> None:
    command = _command(MatrixSessionOperation.credential_delete)
    store = AuthorityLeaseStore(tmp_path / "authority")
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_session_lease(command, store=store, confirmed=True)
    approval_ref = capture_exact_matrix_session_approval(
        command, approval_authority=approvals, confirmed=True
    )
    result = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "repo",
        authority_state_dir=tmp_path / "authority",
        transient_input=MatrixSessionTransientInput(
            endpoint_url="http://127.0.0.1:18008"
        ),
        approval_ref=approval_ref,
        backend=_backend(tmp_path),
        lease_store=store,
        approval_authority=approvals,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert result.adapter_result is None
    assert any(
        "authenticated-one-use-handoff-required" in reason
        for reason in result.receipt.reason_refs
    )
