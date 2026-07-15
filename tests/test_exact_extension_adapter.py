from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.authority import (
    AuthorityBudgetStore,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchConflictError,
    AuthorityDispatcher,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.extension_catalog import (
    EXACT_EXTENSION_ADAPTER_REF,
    EXACT_EXTENSION_CAPABILITY_REF,
    EXACT_EXTENSION_REGISTRATION_REF,
    ExactExtensionBudgetStatus,
    ExactExtensionCompatibilityStatus,
    ExactExtensionConfigurationStatus,
    ExactExtensionHealthStatus,
    ExactExtensionKillSwitchStatus,
    ExactExtensionMetadataAuthorityAdapter,
    ExactExtensionRuntimePosture,
    ExactExtensionSafeDisableStatus,
    build_default_exact_extension_adapter_manifest,
    build_exact_extension_adapter_read_model,
    build_exact_extension_metadata_dispatch_request,
    load_exact_extension_adapter_manifest,
)
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


ROOT_REF = "safe-root:exact-extension-test"


def _ready_posture(**overrides: object) -> ExactExtensionRuntimePosture:
    checked_at = datetime.now(UTC)
    values: dict[str, object] = {
        "posture_ref": "extension-runtime-posture:metadata-inspection:test-ready",
        "compatibility_status": ExactExtensionCompatibilityStatus.supported,
        "configuration_status": ExactExtensionConfigurationStatus.configured,
        "health_status": ExactExtensionHealthStatus.healthy,
        "budget_status": ExactExtensionBudgetStatus.available,
        "safe_disable_status": ExactExtensionSafeDisableStatus.inactive,
        "kill_switch_status": ExactExtensionKillSwitchStatus.inactive,
        "checked_at": checked_at,
        "expires_at": checked_at + timedelta(minutes=4),
        "evidence_refs": ["evidence-ref:exact-extension:test-observation"],
        "safe_summary": (
            "Deterministic test observations permit one fresh request-scoped "
            "dispatcher evaluation and grant no authority."
        ),
    }
    values.update(overrides)
    return ExactExtensionRuntimePosture.model_validate(values)


def _safe_root(root: Path) -> FilesystemSafeRoot:
    identity = root.stat()
    return FilesystemSafeRoot(
        root_ref=ROOT_REF,
        root_path=root,
        safe_label="Exact extension test root",
        expected_device=identity.st_dev,
        expected_inode=identity.st_ino,
    )


def _lease_store(state_dir: Path) -> tuple[AuthorityLeaseStore, str]:
    store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref="constraint-ref:exact-extension:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=4,
                    safe_summary="Limit exact extension test operations.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:exact-extension:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Bound the zero-cost extension lane reservation.",
                ),
            ],
            decision_reason_ref="reason-ref:exact-extension:test-lease",
            safe_summary="Issue one exact files-read lease for the reference adapter.",
        ),
        idempotency_ref="idempotency-ref:exact-extension:test-lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return store, lease.lease_ref


def _request(lease_ref: str, *, suffix: str = "success", path: str = "notes/report.md"):
    return build_exact_extension_metadata_dispatch_request(
        lease_ref=lease_ref,
        run_ref=f"run-ref:exact-extension:{suffix}",
        request_ref=f"request-ref:exact-extension:{suffix}",
        idempotency_ref=f"idempotency-ref:exact-extension:{suffix}",
        root_ref=ROOT_REF,
        relative_path=path,
        start_deadline=datetime.now(UTC) + timedelta(minutes=5),
    )


def _dispatcher(
    state_dir: Path,
    root: Path,
    store: AuthorityLeaseStore,
    posture_provider,
) -> AuthorityDispatcher:
    adapter = ExactExtensionMetadataAuthorityAdapter(
        safe_roots=[_safe_root(root)],
        posture_provider=posture_provider,
    )
    return AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        budget_store=AuthorityBudgetStore(state_dir, lease_store=store),
    )


def test_exact_extension_executes_through_dispatcher_and_replays_once(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient content", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, _ready_posture)
    request = _request(lease_ref)

    first = dispatcher.dispatch(request)
    replay = dispatcher.dispatch(request)

    assert first.receipt.status == AuthorityDispatchStatus.succeeded, (
        first.receipt.reason_refs
    )
    assert first.receipt.adapter_ref == EXACT_EXTENSION_ADAPTER_REF
    assert first.receipt.capability_ref == EXACT_EXTENSION_CAPABILITY_REF
    assert EXACT_EXTENSION_REGISTRATION_REF in first.receipt.evidence_refs
    assert first.receipt.actual_cost_microusd == 0
    assert first.receipt.raw_paths_included is False
    assert replay.replayed is True
    assert replay.receipt.receipt_ref == first.receipt.receipt_ref
    ledger = dispatcher.receipts_path.read_text(encoding="utf-8")
    assert str(root) not in ledger
    assert "transient content" not in ledger
    assert "notes/report.md" not in ledger


def test_exact_extension_rechecks_safe_disable_between_prepare_and_start(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    posture = _ready_posture()
    dispatcher = _dispatcher(state_dir, root, store, lambda: posture)
    request = _request(lease_ref, suffix="safe-disable")

    prepared = dispatcher.prepare(request)
    assert prepared.receipt.status == AuthorityDispatchStatus.prepared, (
        prepared.receipt.reason_refs
    )
    posture = _ready_posture(
        safe_disable_status=ExactExtensionSafeDisableStatus.active
    )
    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start
    assert result.receipt.adapter_invocation_performed is False
    assert any("safe-disable" in ref for ref in result.receipt.reason_refs)


def test_exact_extension_rechecks_observation_expiry_before_start(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    posture = _ready_posture()
    dispatcher = _dispatcher(state_dir, root, store, lambda: posture)
    request = _request(lease_ref, suffix="observation-expired")

    prepared = dispatcher.prepare(request)
    assert prepared.receipt.status == AuthorityDispatchStatus.prepared
    checked_at = datetime.now(UTC) - timedelta(minutes=2)
    posture = _ready_posture(
        checked_at=checked_at,
        expires_at=checked_at + timedelta(minutes=1),
    )
    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start
    assert result.receipt.execution_started is False
    assert result.receipt.adapter_invocation_performed is False
    assert any("observation-stale" in ref for ref in result.receipt.reason_refs)


def test_exact_extension_observation_window_is_bounded() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="EXACT_EXTENSION_OBSERVATION_FUTURE_DATED"):
        _ready_posture(
            checked_at=now + timedelta(minutes=1),
            expires_at=now + timedelta(minutes=2),
        )
    with pytest.raises(ValueError, match="EXACT_EXTENSION_OBSERVATION_TTL_EXCEEDED"):
        _ready_posture(
            checked_at=now,
            expires_at=now + timedelta(minutes=6),
        )
    with pytest.raises(ValueError, match="EXACT_EXTENSION_OBSERVATION_WINDOW_INCOMPLETE"):
        _ready_posture(checked_at=now, expires_at=None)
    with pytest.raises(ValueError, match="EXACT_EXTENSION_OBSERVATION_TIMEZONE_REQUIRED"):
        _ready_posture(
            checked_at=now.replace(tzinfo=None),
            expires_at=(now + timedelta(minutes=1)).replace(tzinfo=None),
        )
    with pytest.raises(ValueError, match="EXACT_EXTENSION_OBSERVATION_WINDOW_INVALID"):
        _ready_posture(checked_at=now, expires_at=now)


def test_exact_extension_start_deadline_requires_timezone() -> None:
    with pytest.raises(
        ValueError, match="EXACT_EXTENSION_START_DEADLINE_TIMEZONE_REQUIRED"
    ):
        build_exact_extension_metadata_dispatch_request(
            lease_ref="authority-lease-ref:exact-extension:deadline-test",
            run_ref="run-ref:exact-extension:deadline-test",
            request_ref="request-ref:exact-extension:deadline-test",
            idempotency_ref="idempotency-ref:exact-extension:deadline-test",
            root_ref=ROOT_REF,
            relative_path="notes/report.md",
            start_deadline=datetime.now().replace(tzinfo=None),
        )
    with pytest.raises(ValueError, match="EXACT_EXTENSION_START_DEADLINE_TOO_DISTANT"):
        build_exact_extension_metadata_dispatch_request(
            lease_ref="authority-lease-ref:exact-extension:deadline-test",
            run_ref="run-ref:exact-extension:deadline-test",
            request_ref="request-ref:exact-extension:deadline-test",
            idempotency_ref="idempotency-ref:exact-extension:deadline-test",
            root_ref=ROOT_REF,
            relative_path="notes/report.md",
            start_deadline=datetime.now(UTC) + timedelta(days=1),
        )


def test_exact_extension_expired_start_deadline_denies_before_start(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, _ready_posture)
    request = _request(lease_ref, suffix="expired-deadline").model_copy(
        update={"start_deadline": datetime.now(UTC) - timedelta(seconds=1)}
    )

    result = dispatcher.dispatch(request)

    assert result.receipt.execution_started is False
    assert result.receipt.adapter_invocation_performed is False
    assert any("deadline-expired" in ref for ref in result.receipt.reason_refs)


@pytest.mark.parametrize(
    ("posture", "expected_fragment"),
    [
        (
            _ready_posture(
                compatibility_status=ExactExtensionCompatibilityStatus.unknown
            ),
            "compatibility",
        ),
        (
            _ready_posture(
                compatibility_status=ExactExtensionCompatibilityStatus.unsupported
            ),
            "compatibility",
        ),
        (
            _ready_posture(
                configuration_status=ExactExtensionConfigurationStatus.invalid
            ),
            "configuration",
        ),
        (
            _ready_posture(
                health_status=ExactExtensionHealthStatus.stale
            ),
            "health",
        ),
        (
            _ready_posture(
                health_status=ExactExtensionHealthStatus.degraded
            ),
            "health",
        ),
        (
            _ready_posture(
                budget_status=ExactExtensionBudgetStatus.unknown
            ),
            "budget",
        ),
        (
            _ready_posture(
                budget_status=ExactExtensionBudgetStatus.exhausted
            ),
            "budget",
        ),
        (
            _ready_posture(
                safe_disable_status=ExactExtensionSafeDisableStatus.unknown
            ),
            "safe-disable",
        ),
        (
            _ready_posture(
                kill_switch_status=ExactExtensionKillSwitchStatus.active
            ),
            "kill-switch",
        ),
    ],
)
def test_exact_extension_unknown_or_unsafe_posture_fails_before_start(
    tmp_path: Path,
    posture: ExactExtensionRuntimePosture,
    expected_fragment: str,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, lambda: posture)

    result = dispatcher.dispatch(_request(lease_ref, suffix=expected_fragment))

    assert result.receipt.status == AuthorityDispatchStatus.denied
    assert result.receipt.execution_started is False
    assert any(expected_fragment in ref for ref in result.receipt.reason_refs)


def test_exact_extension_requires_current_lease_and_exact_bindings(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, _ready_posture)
    missing_lease = _request(
        "authority-lease-ref:exact-extension:missing",
        suffix="missing-lease",
    )

    denied = dispatcher.dispatch(missing_lease)
    assert denied.receipt.status == AuthorityDispatchStatus.denied
    assert denied.receipt.execution_started is False

    store, lease_ref = _lease_store(tmp_path / "bound-authority")
    dispatcher = _dispatcher(
        tmp_path / "bound-authority",
        root,
        store,
        ExactExtensionRuntimePosture,
    )
    request = _request(lease_ref, suffix="binding")
    changed_action = request.action_request.model_copy(
        update={
            "resource_refs": [
                ref
                for ref in request.action_request.resource_refs
                if ref != EXACT_EXTENSION_REGISTRATION_REF
            ]
        }
    )
    changed = request.model_copy(update={"action_request": changed_action})
    result = dispatcher.dispatch(changed)
    assert result.receipt.status == AuthorityDispatchStatus.denied
    assert any("resource-binding" in ref for ref in result.receipt.reason_refs)


@pytest.mark.parametrize(
    "unsafe_path",
    ["../outside", "/denied-target", "notes/../../outside", ""],
)
def test_exact_extension_request_rejects_unbounded_targets(
    unsafe_path: str,
) -> None:
    with pytest.raises(ValueError, match="EXACT_EXTENSION_TARGET_PATH_INVALID"):
        build_exact_extension_metadata_dispatch_request(
            lease_ref="authority-lease-ref:exact-extension:path-test",
            run_ref="run-ref:exact-extension:path-test",
            request_ref="request-ref:exact-extension:path-test",
            idempotency_ref="idempotency-ref:exact-extension:path-test",
            root_ref=ROOT_REF,
            relative_path=unsafe_path,
            start_deadline=datetime.now(UTC) + timedelta(minutes=5),
        )


def test_exact_extension_changed_request_cannot_reuse_dispatch_identity(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("one", encoding="utf-8")
    (root / "notes" / "other.md").write_text("two", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, _ready_posture)
    first = _request(lease_ref, suffix="conflict")
    dispatcher.dispatch(first)
    other = _request(lease_ref, suffix="other", path="notes/other.md")
    conflicting = other.model_copy(
        update={
            "dispatch_ref": first.dispatch_ref,
            "idempotency_ref": first.idempotency_ref,
            "action_request": other.action_request.model_copy(
                update={"action_ref": first.action_request.action_ref}
            ),
            "tool_invocation_request": {
                **other.tool_invocation_request,
                "invocation_id": first.dispatch_ref,
                "replay_key": first.idempotency_ref,
            },
        }
    )
    with pytest.raises(AuthorityDispatchConflictError):
        dispatcher.dispatch(conflicting)


def test_exact_extension_manifest_loader_rejects_substitution(
    tmp_path: Path,
) -> None:
    manifest = build_default_exact_extension_adapter_manifest()
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(manifest.model_dump(mode="json")),
        encoding="utf-8",
    )
    loaded = load_exact_extension_adapter_manifest(path)
    assert loaded.registration_ref == EXACT_EXTENSION_REGISTRATION_REF

    changed = manifest.model_dump(mode="json")
    changed["adapter_ref"] = "authority-adapter-ref:unreviewed"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError):
        load_exact_extension_adapter_manifest(path)

    target = tmp_path / "target.json"
    target.write_text(json.dumps(manifest.model_dump(mode="json")), encoding="utf-8")
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(ValueError, match="SPECIAL_FILE_DENIED"):
        load_exact_extension_adapter_manifest(path)

    if hasattr(os, "mkfifo"):
        path.unlink()
        os.mkfifo(path)
        with pytest.raises(ValueError, match="SPECIAL_FILE_DENIED"):
            load_exact_extension_adapter_manifest(path)


def test_exact_extension_manifest_loader_rejects_unsafe_files(
    tmp_path: Path,
) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON_INVALID"):
        load_exact_extension_adapter_manifest(path)

    path.write_bytes(b" " * (64 * 1024 + 1))
    with pytest.raises(ValueError, match="TOO_LARGE"):
        load_exact_extension_adapter_manifest(path)

    target = tmp_path / "linked.json"
    target.write_text(
        json.dumps(build_default_exact_extension_adapter_manifest().model_dump()),
        encoding="utf-8",
    )
    path.unlink()
    os.link(target, path)
    with pytest.raises(ValueError, match="IDENTITY_DRIFT"):
        load_exact_extension_adapter_manifest(path)


def test_exact_extension_revoked_lease_cancels_before_start(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, _ready_posture)
    request = _request(lease_ref, suffix="revoked")
    dispatcher.prepare(request)
    store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease_ref,
            decision_reason_ref="reason-ref:exact-extension:test-revoked",
            safe_summary="Revoke the exact extension lease before adapter start.",
        ),
        idempotency_ref="idempotency-ref:exact-extension:test-revoked",
    )

    result = dispatcher.execute(request)

    assert result.receipt.status == AuthorityDispatchStatus.cancelled_before_start
    assert result.receipt.execution_started is False
    assert result.receipt.adapter_invocation_performed is False


def test_exact_extension_late_safe_disable_blocks_before_metadata_access(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text(
        "content-must-not-be-read",
        encoding="utf-8",
    )
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    posture_checks = 0

    def posture_provider() -> ExactExtensionRuntimePosture:
        nonlocal posture_checks
        posture_checks += 1
        if posture_checks >= 3:
            return _ready_posture(
                safe_disable_status=ExactExtensionSafeDisableStatus.active
            )
        return _ready_posture()

    adapter = ExactExtensionMetadataAuthorityAdapter(
        safe_roots=[_safe_root(root)],
        posture_provider=posture_provider,
    )

    def metadata_access_must_not_run(_request):
        raise AssertionError("bounded metadata tool ran after late safe-disable")

    adapter._inner.invoke = metadata_access_must_not_run  # type: ignore[method-assign]
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        budget_store=AuthorityBudgetStore(state_dir, lease_store=store),
    )

    result = dispatcher.dispatch(_request(lease_ref, suffix="late-disable"))

    assert posture_checks == 3
    assert result.receipt.status == AuthorityDispatchStatus.failed
    assert result.receipt.execution_started is True
    assert result.receipt.adapter_invocation_performed is True
    assert any("late-denial" in ref for ref in result.receipt.evidence_refs)
    assert any(
        "safe-disable-not-inactive" in ref for ref in result.receipt.evidence_refs
    )
    ledger = dispatcher.receipts_path.read_text(encoding="utf-8")
    assert "content-must-not-be-read" not in ledger
    assert str(root) not in ledger


def test_exact_extension_late_kill_switch_blocks_before_metadata_access(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text(
        "content-must-not-be-read",
        encoding="utf-8",
    )
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    posture_checks = 0

    def posture_provider() -> ExactExtensionRuntimePosture:
        nonlocal posture_checks
        posture_checks += 1
        return (
            _ready_posture(kill_switch_status=ExactExtensionKillSwitchStatus.active)
            if posture_checks >= 3
            else _ready_posture()
        )

    adapter = ExactExtensionMetadataAuthorityAdapter(
        safe_roots=[_safe_root(root)],
        posture_provider=posture_provider,
    )

    def metadata_access_must_not_run(_request):
        raise AssertionError("bounded metadata tool ran after late kill switch")

    adapter._inner.invoke = metadata_access_must_not_run  # type: ignore[method-assign]
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        budget_store=AuthorityBudgetStore(state_dir, lease_store=store),
    )

    result = dispatcher.dispatch(_request(lease_ref, suffix="late-kill-switch"))

    assert result.receipt.status == AuthorityDispatchStatus.failed
    assert result.receipt.execution_started is True
    assert any("kill-switch-not-inactive" in ref for ref in result.receipt.evidence_refs)
    ledger = dispatcher.receipts_path.read_text(encoding="utf-8")
    assert "content-must-not-be-read" not in ledger
    assert str(root) not in ledger


def test_exact_extension_posture_provider_failure_denies_before_start(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)

    def unavailable_posture() -> ExactExtensionRuntimePosture:
        raise RuntimeError("unsafe-provider-details")

    dispatcher = _dispatcher(state_dir, root, store, unavailable_posture)
    result = dispatcher.dispatch(_request(lease_ref, suffix="posture-failed"))

    assert result.receipt.status == AuthorityDispatchStatus.denied
    assert result.receipt.execution_started is False
    assert "unsafe-provider-details" not in dispatcher.receipts_path.read_text(
        encoding="utf-8"
    )
    assert any("posture-provider-failed" in ref for ref in result.receipt.reason_refs)


def test_exact_extension_read_model_and_cli_are_non_authorizing() -> None:
    read_model = build_exact_extension_adapter_read_model()
    assert read_model.ready_for_request_scoped_evaluation is False
    assert read_model.blocker_codes
    assert "CURRENT_RUNTIME_OBSERVATION_REQUIRED" in read_model.reason_codes
    assert read_model.invocation_authorized is False
    assert read_model.execution_performed is False
    assert read_model.global_extension_runtime_enabled is False
    assert read_model.arbitrary_runtime_import_enabled is False

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [sys.executable, "scripts/dev/uaa_extensions.py", "inspect-exact-adapter"],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert "General extension runtime: disabled" in result.stdout
    assert "Ready for request-scoped evaluation: no" in result.stdout
    assert "Blockers: none" not in result.stdout


def test_exact_extension_default_posture_is_unknown_and_fails_closed() -> None:
    posture = ExactExtensionRuntimePosture()
    assert posture.compatibility_status == "unknown"
    assert posture.configuration_status == "unknown"
    assert posture.health_status == "unknown"
    assert posture.budget_status == "unknown"
    assert posture.safe_disable_status == "unknown"
    assert posture.kill_switch_status == "unknown"
    assert posture.checked_at is None
    assert posture.expires_at is None

    read_model = build_exact_extension_adapter_read_model()
    assert read_model.ready_for_request_scoped_evaluation is False
    assert {
        "EXTENSION_COMPATIBILITY_NOT_SUPPORTED",
        "EXTENSION_CONFIGURATION_NOT_READY",
        "EXTENSION_HEALTH_NOT_READY",
        "EXTENSION_BUDGET_NOT_AVAILABLE",
        "EXTENSION_SAFE_DISABLE_NOT_INACTIVE",
        "EXTENSION_KILL_SWITCH_NOT_INACTIVE",
        "EXTENSION_FRESHNESS_UNKNOWN",
    }.issubset(read_model.blocker_codes)
    assert read_model.invocation_authorized is False
    assert read_model.execution_performed is False
    assert read_model.global_extension_runtime_enabled is False
    assert read_model.arbitrary_runtime_import_enabled is False


def test_exact_extension_observed_ready_posture_never_grants_authority() -> None:
    read_model = build_exact_extension_adapter_read_model(posture=_ready_posture())
    assert read_model.ready_for_request_scoped_evaluation is True
    assert read_model.blocker_codes == []
    assert "CURRENT_RUNTIME_OBSERVATION_EVALUATED" in read_model.reason_codes
    assert read_model.invocation_authorized is False
    assert read_model.execution_performed is False


def test_exact_extension_fresh_blocked_observation_is_evaluated() -> None:
    read_model = build_exact_extension_adapter_read_model(
        posture=_ready_posture(
            compatibility_status=ExactExtensionCompatibilityStatus.unsupported
        )
    )
    assert read_model.ready_for_request_scoped_evaluation is False
    assert "EXTENSION_COMPATIBILITY_NOT_SUPPORTED" in read_model.blocker_codes
    assert "CURRENT_RUNTIME_OBSERVATION_EVALUATED" in read_model.reason_codes
    assert "CURRENT_RUNTIME_OBSERVATION_REQUIRED" not in read_model.reason_codes


def test_exact_extension_default_posture_denies_before_start(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("transient", encoding="utf-8")
    state_dir = tmp_path / "authority"
    store, lease_ref = _lease_store(state_dir)
    dispatcher = _dispatcher(state_dir, root, store, ExactExtensionRuntimePosture)

    result = dispatcher.dispatch(_request(lease_ref, suffix="unknown-posture"))

    assert result.receipt.status == AuthorityDispatchStatus.denied
    assert result.receipt.execution_started is False
    assert result.receipt.adapter_invocation_performed is False
    for expected in (
        "compatibility-not-supported",
        "configuration-not-ready",
        "health-not-ready",
        "budget-not-available",
        "safe-disable-not-inactive",
        "kill-switch-not-inactive",
        "freshness-unknown",
    ):
        assert any(expected in ref for ref in result.receipt.reason_refs)


def test_exact_extension_cli_rejects_manifest_outside_repository(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "exact-extension.json"
    manifest_path.write_text(
        json.dumps(build_default_exact_extension_adapter_manifest().model_dump(mode="json")),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "validate-exact-adapter-manifest",
            str(manifest_path),
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == "EXACT_EXTENSION_MANIFEST_OUTSIDE_REPOSITORY"
    assert str(manifest_path) not in result.stderr


def test_exact_extension_cli_denial_code_does_not_echo_embedded_values() -> None:
    from scripts.dev.uaa_extensions import _safe_exact_extension_denial_code

    unsafe = ValueError(
        "validation failed for supplied value EXACT_EXTENSION_SECRETLIKE_VALUE"
    )
    assert (
        _safe_exact_extension_denial_code(unsafe)
        == "EXACT_EXTENSION_MANIFEST_VALIDATION_DENIED"
    )


def test_exact_extension_cli_validates_canonical_manifest_without_authority() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "validate-exact-adapter-manifest",
            "docs/tooling/exact_extension_adapter_manifest.json",
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0
    assert "Status: validated_exact_repo_owned_binding" in result.stdout
    assert f"Registration: {EXACT_EXTENSION_REGISTRATION_REF}" in result.stdout
    assert "Runtime import: not performed" in result.stdout
    assert "Execution: not performed" in result.stdout
    assert "Authority: not granted" in result.stdout


def test_exact_extension_cli_path_confinement_preserves_symlink_denial(
    tmp_path: Path,
) -> None:
    from scripts.dev.uaa_extensions import _repo_manifest_path

    root = tmp_path / "repo"
    root.mkdir()
    manifest = root / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    link = root / "manifest-link.json"
    link.symlink_to(manifest)

    with pytest.raises(ValueError, match="EXACT_EXTENSION_MANIFEST_SPECIAL_FILE_DENIED"):
        _repo_manifest_path(link, repository_root=root)


def test_exact_extension_cli_path_confinement_rejects_symlinked_parent(
    tmp_path: Path,
) -> None:
    from scripts.dev.uaa_extensions import _repo_manifest_path

    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "manifest.json").write_text("{}", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        ValueError, match="EXACT_EXTENSION_MANIFEST_OUTSIDE_REPOSITORY"
    ):
        _repo_manifest_path(root / "linked" / "manifest.json", repository_root=root)


def test_exact_extension_cli_path_confinement_rejects_in_repo_symlinked_parent(
    tmp_path: Path,
) -> None:
    from scripts.dev.uaa_extensions import _repo_manifest_path

    root = tmp_path / "repo"
    target = root / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text("{}", encoding="utf-8")
    (root / "linked").symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="EXACT_EXTENSION_MANIFEST_SPECIAL_FILE_DENIED"):
        _repo_manifest_path(root / "linked" / "manifest.json", repository_root=root)


def test_exact_extension_availability_is_visible_but_not_globally_callable() -> None:
    from ultimate_ai_agent.core.capability_availability import (
        build_capability_availability_read_model,
    )

    read_model = build_capability_availability_read_model()
    snapshot = next(
        item
        for item in read_model.snapshots
        if item.adapter_ref == EXACT_EXTENSION_ADAPTER_REF
    )
    assert snapshot.capability_ref == EXACT_EXTENSION_CAPABILITY_REF
    assert snapshot.runtime_readiness_status == "unknown"
    assert snapshot.authority_posture == "lease_required"
    assert "EXACT_AUTHORITY_LEASE_REQUIRED" in snapshot.blocker_codes
