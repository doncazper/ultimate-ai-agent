from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

import ultimate_ai_agent.core.communications.matrix_session.backend as matrix_session_backend_module
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
from ultimate_ai_agent.core.communications.matrix_session.observations import (
    MatrixDiscoveryObservationStore,
)
from ultimate_ai_agent.core.communications.matrix_session.backend import (
    MatrixSessionExecutionHandle,
    create_matrix_runtime_snapshot,
    remove_matrix_runtime_snapshot,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
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
        "request_created_at": deadline - timedelta(minutes=2),
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
    exit_code: int | None = None,
    runner_body: str | None = None,
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
    resolved_exit_code = (0 if response_ok else 2) if exit_code is None else exit_code
    runner.write_text(
        runner_body
        or (
            "import json,sys\n"
            "json.load(sys.stdin)\n"
            f"sys.stdout.write({json.dumps(json.dumps(response))})\n"
            f"raise SystemExit({resolved_exit_code})\n"
        ),
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
    node = repo / "node-test-wrapper"
    node.write_text(
        (
            "#!/bin/sh\n"
            '[ "$1" = "--permission" ] || exit 64\n'
            "shift\n"
            'case "$1" in --allow-fs-read=*) shift ;; *) exit 64 ;; esac\n'
            'exec /usr/bin/python3 "$@"\n'
        ),
        encoding="utf-8",
    )
    os.chmod(node, 0o700)
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


def test_abort_closes_streams_and_releases_lifecycle_when_termination_fails() -> None:
    class Stream:
        def __init__(self, *, fail_close: bool = False) -> None:
            self.closed = False
            self.fail_close = fail_close

        def close(self) -> None:
            self.closed = True
            if self.fail_close:
                raise OSError("injected stream close failure")

    class Process:
        def __init__(self) -> None:
            self.stdin = Stream(fail_close=True)
            self.stdout = Stream()
            self.stderr = Stream()

    class FailingBackend:
        def __init__(self) -> None:
            self.released = False

        def _terminate_process_group(self, _process: object) -> None:
            raise RuntimeError("MATRIX_SESSION_TEST_TERMINATION_UNCONFIRMED")

        def _release_lifecycle(self) -> None:
            self.released = True

    backend = FailingBackend()
    process = Process()
    handle = MatrixSessionExecutionHandle(
        backend=backend,  # type: ignore[arg-type]
        execution_ref="execution-ref:matrix-session:abort-streams",
        process=process,  # type: ignore[arg-type]
        commit_validated_at=utc_now(),
        expected_operation=MatrixSessionOperation.discovery_read,
        runtime_snapshot=None,  # type: ignore[arg-type]
    )

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="MATRIX_SESSION_CONFIRMATION_ABORT_CLEANUP_UNCERTAIN",
    ):
        handle.abort()

    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True
    assert backend.released is True


@pytest.mark.parametrize("failure_stage", ("termination", "lifecycle"))
def test_collect_attempts_all_cleanup_when_one_step_fails(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    class Stream:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class Process:
        def __init__(self) -> None:
            self.stdin = Stream()
            self.stdout = Stream()
            self.stderr = Stream()

    class FailingBackend:
        def __init__(self) -> None:
            self.terminated = False
            self.released = False

        def _terminate_process_group(self, _process: object) -> None:
            self.terminated = True
            if failure_stage == "termination":
                raise RuntimeError("MATRIX_SESSION_TEST_TERMINATION_UNCONFIRMED")

        def _release_lifecycle(self) -> None:
            self.released = True
            if failure_stage == "lifecycle":
                raise RuntimeError("MATRIX_SESSION_TEST_LIFECYCLE_RELEASE_UNCONFIRMED")

    snapshot_released = False

    def fail_collection(*_args: object, **_kwargs: object) -> bytes:
        raise RuntimeError("MATRIX_SESSION_TEST_COLLECTION_FAILED")

    def record_snapshot_release(_snapshot: object) -> None:
        nonlocal snapshot_released
        snapshot_released = True

    monkeypatch.setattr(
        matrix_session_backend_module,
        "_communicate_bounded",
        fail_collection,
    )
    monkeypatch.setattr(
        matrix_session_backend_module,
        "remove_matrix_runtime_snapshot",
        record_snapshot_release,
    )
    backend = FailingBackend()
    process = Process()
    handle = MatrixSessionExecutionHandle(
        backend=backend,  # type: ignore[arg-type]
        execution_ref=f"execution-ref:matrix-session:collect-{failure_stage}",
        process=process,  # type: ignore[arg-type]
        commit_validated_at=utc_now(),
        expected_operation=MatrixSessionOperation.credential_auth_create,
        runtime_snapshot=object(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="MATRIX_SESSION_COLLECTION_CLEANUP_UNCERTAIN",
    ):
        handle.collect()

    assert backend.terminated is True
    assert backend.released is True
    assert snapshot_released is True
    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_runtime_snapshot_reconciliation_preserves_active_and_removes_stale(
    tmp_path: Path,
) -> None:
    backend = _backend(tmp_path)
    config = backend.config
    snapshot_parent = tmp_path / "runtime-snapshots"

    active = create_matrix_runtime_snapshot(
        adapter_root=config.adapter_root,
        node_binary=config.node_binary,
        runner_path=config.runner_path,
        expected_node_sha256=config.expected_node_sha256,
        expected_runner_sha256=config.expected_runner_sha256,
        snapshot_parent=snapshot_parent,
    )
    sibling = create_matrix_runtime_snapshot(
        adapter_root=config.adapter_root,
        node_binary=config.node_binary,
        runner_path=config.runner_path,
        expected_node_sha256=config.expected_node_sha256,
        expected_runner_sha256=config.expected_runner_sha256,
        snapshot_parent=snapshot_parent,
    )
    assert active.root.exists()
    assert sibling.root.exists()

    stale_root = sibling.root
    os.close(sibling.owner_lock_fd)
    replacement = create_matrix_runtime_snapshot(
        adapter_root=config.adapter_root,
        node_binary=config.node_binary,
        runner_path=config.runner_path,
        expected_node_sha256=config.expected_node_sha256,
        expected_runner_sha256=config.expected_runner_sha256,
        snapshot_parent=snapshot_parent,
    )
    assert not stale_root.exists()
    assert active.root.exists()
    assert replacement.root.exists()

    remove_matrix_runtime_snapshot(active)
    remove_matrix_runtime_snapshot(replacement)


def test_runtime_snapshot_rejects_symlinked_integrity_tree_directory(
    tmp_path: Path,
) -> None:
    backend = _backend(tmp_path)
    config = backend.config
    external = tmp_path / "external-runtime"
    external.mkdir()
    (external / "unreviewed.mjs").write_text(
        "export const unreviewed = true;\n",
        encoding="utf-8",
    )
    (config.adapter_root / "runtime" / "linked").symlink_to(
        external,
        target_is_directory=True,
    )

    with pytest.raises(ValueError, match="MATRIX_SESSION_RUNTIME_TREE_UNSAFE"):
        create_matrix_runtime_snapshot(
            adapter_root=config.adapter_root,
            node_binary=config.node_binary,
            runner_path=config.runner_path,
            expected_node_sha256=config.expected_node_sha256,
            expected_runner_sha256=config.expected_runner_sha256,
            snapshot_parent=tmp_path / "runtime-snapshots",
        )


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


def test_terminal_discovery_replay_reconciles_missing_observation_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authority_state = tmp_path / "authority"
    store = AuthorityLeaseStore(authority_state)
    command = _command(MatrixSessionOperation.discovery_read)
    issue_exact_matrix_session_lease(command, store=store, confirmed=False)
    original = MatrixDiscoveryObservationStore.record_success
    attempts = 0

    def fail_first_append(
        observation_store: MatrixDiscoveryObservationStore, **values: object
    ) -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("simulated observation append failure")
        return original(observation_store, **values)  # type: ignore[arg-type]

    monkeypatch.setattr(
        MatrixDiscoveryObservationStore, "record_success", fail_first_append
    )
    with pytest.raises(OSError, match="simulated observation append failure"):
        execute_matrix_session_command(
            command,
            repo_root=tmp_path / "first" / "repo",
            authority_state_dir=authority_state,
            transient_input=MatrixSessionTransientInput(
                discovery_origin="http://127.0.0.1:18008"
            ),
            backend=_backend(tmp_path / "first"),
            lease_store=store,
        )

    replay = execute_matrix_session_command(
        command,
        repo_root=tmp_path / "replay" / "repo",
        authority_state_dir=authority_state,
        transient_input=MatrixSessionTransientInput(
            discovery_origin="http://127.0.0.1:18008"
        ),
        backend=_backend(tmp_path / "replay"),
        lease_store=store,
    )
    assert replay.replayed is True
    assert replay.adapter_result is None
    observation_ref = matrix_homeserver_observation_ref("http://127.0.0.1:18008")
    assert (
        MatrixDiscoveryObservationStore(
            authority_state / "matrix_session_observations"
        )._latest(observation_ref)
        is not None
    )


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


def test_adapter_output_is_terminated_at_the_streaming_byte_limit(
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
        backend=_backend(
            tmp_path,
            runner_body=(
                "import json,sys,time\n"
                "json.load(sys.stdin)\n"
                f"sys.stdout.write('x' * {128 * 1024 + 1})\n"
                "sys.stdout.flush()\n"
                "time.sleep(30)\n"
            ),
        ),
        lease_store=store,
    )
    assert result.receipt.status == "failed"
    assert result.adapter_result is not None
    assert result.adapter_result.succeeded is False
    assert result.receipt.raw_response_included is False


@pytest.mark.parametrize(
    ("response_ok", "exit_code"),
    [(True, 2), (False, 0)],
)
def test_adapter_response_and_process_exit_must_agree(
    tmp_path: Path, response_ok: bool, exit_code: int
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
        backend=_backend(
            tmp_path,
            response_ok=response_ok,
            exit_code=exit_code,
        ),
        lease_store=store,
    )
    assert result.receipt.status == "failed"
    assert result.adapter_result is not None
    assert result.adapter_result.succeeded is False
    assert result.adapter_result.safe_output == {}


def test_python_target_refs_require_canonical_ascii_and_match_ipv6_origins() -> None:
    assert matrix_homeserver_ref("https://xn--mnich-kva.example").startswith(
        "homeserver-ref:matrix:sha256:"
    )
    assert matrix_homeserver_observation_ref(
        "https://[2606:4700:4700:0:0:0:0:1111]"
    ) == matrix_homeserver_observation_ref("https://[2606:4700:4700::1111]")
    for raw in (
        "https://m\u00fcnich.example",
        "https://fa\u00df.de",
        "https://\u03bf\u03c3.example",
        "https://a\u200db.example",
        "https://%65xample.com",
    ):
        with pytest.raises(ValueError, match="MATRIX_TARGET_HOSTNAME_NONCANONICAL"):
            matrix_homeserver_ref(raw)


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
