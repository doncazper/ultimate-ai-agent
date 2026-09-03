from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import pytest

from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalStore,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts/manage_tool_aware_cognition_taw08_live_lease.py"


def _load(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


helper = _load("taw08_live_lease_helper_test", HELPER_PATH)


LEASE_REF = "authority-lease-ref:taw08-live-unit-test"
ISSUE_IDEMPOTENCY_REF = "idempotency-ref:taw08-live-issue-unit-test"
REVOKE_IDEMPOTENCY_REF = "idempotency-ref:taw08-live-revoke-unit-test"
CANDIDATE_REVISION_REF = "git-sha:" + "a" * 40
CANDIDATE_MANIFEST_DIGEST_REF = "sha256:" + "b" * 64
RUN_REF = "run-ref:taw08:live-unit-test"
ISSUED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
EXPIRES_AT = ISSUED_AT + timedelta(minutes=helper.LEASE_DURATION_MINUTES)
DOMAINS = {
    helper.AuthorityDomain.provider_model_calls: [helper.AuthorityCapability.execute]
}


class _LeaseFixture(SimpleNamespace):
    def is_active(self) -> bool:
        return True


def _state_dir(tmp_path: Path) -> Path:
    state_dir = tmp_path / "authority-state"
    state_dir.mkdir(mode=0o700)
    state_dir.chmod(0o700)
    return state_dir.resolve()


def _active_lease(**updates: object) -> SimpleNamespace:
    binding = helper.lease_constraints(
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    constraints, _requirement = helper._expected_stored_constraints(
        binding,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
    )
    request = helper._issue_request(binding)
    values: dict[str, object] = {
        "lease_ref": LEASE_REF,
        "status": helper.AuthorityLeaseStatus.active,
        "mode": helper.TrustMode.full_machine_access_session,
        "scope": helper.AuthorityLeaseScope.mission,
        "mission_ref": RUN_REF,
        "authority_constraints": request.authority_constraints,
        "operator_ref": helper.AUTHORITY_LEASE_LOCAL_OPERATOR_REF,
        "domains": DOMAINS,
        "issued_at": ISSUED_AT,
        "expires_at": EXPIRES_AT,
        "constraints": constraints,
    }
    values.update(updates)
    return _LeaseFixture(**values)


def _issue_receipt(**updates: object) -> SimpleNamespace:
    constraints, requirement = helper._expected_stored_constraints(
        helper.lease_constraints(
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        ),
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
    )
    values: dict[str, object] = {
        "lease_ref": LEASE_REF,
        "status": "issued",
        "receipt_ref": "receipt-ref:taw08-live-issue-unit-test",
        "requested_domains": DOMAINS,
        "granted_domains": DOMAINS,
        "lease_issued_at": ISSUED_AT,
        "lease_expires_at": EXPIRES_AT,
        "denied_domain_refs": [],
        "unsupported_adapter_refs": [],
        "approval_required": True,
        "approval_validated": True,
        "idempotency_ref": ISSUE_IDEMPOTENCY_REF,
        "approval_ref": constraints["approval_ref"],
        "approval_scope_ref": requirement.approval_scope_ref,
        "approval_request_ref": requirement.approval_request_ref,
        "approval_status": "approved",
        "execution_performed": False,
        "raw_paths_included": False,
        "raw_prompt_included": False,
        "raw_response_included": False,
        "raw_provider_payload_included": False,
    }
    values.update(updates)
    return SimpleNamespace(**values)


def _revoke_receipt(**updates: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "lease_ref": LEASE_REF,
        "status": "revoked",
        "receipt_ref": "receipt-ref:taw08-live-revoke-unit-test",
        "mode": helper.TrustMode.full_machine_access_session,
        "scope": helper.AuthorityLeaseScope.mission,
        "granted_domains": {},
        "lease_issued_at": ISSUED_AT,
        "lease_expires_at": EXPIRES_AT,
        "execution_performed": False,
        "raw_paths_included": False,
        "raw_prompt_included": False,
        "raw_response_included": False,
        "raw_provider_payload_included": False,
    }
    values.update(updates)
    return SimpleNamespace(**values)


def test_issue_builds_only_the_exact_live_lease_and_safe_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = _state_dir(tmp_path)
    observed = SimpleNamespace()

    def fake_issue(store, request, **kwargs):
        observed.store = store
        observed.request = request
        observed.idempotency_ref = kwargs["idempotency_ref"]
        observed.approved_by_actor_id = kwargs["approved_by_actor_id"]
        return (
            SimpleNamespace(approval_required=True),
            SimpleNamespace(approval_ref="approval-ref:taw08-live-unit-test"),
            _active_lease(),
            _issue_receipt(),
        )

    monkeypatch.setattr(
        helper, "issue_authority_lease_with_backend_approval", fake_issue
    )
    active_census = iter(([], [_active_lease()]))
    monkeypatch.setattr(
        helper.AuthorityLeaseStore,
        "list_leases",
        lambda _store, *, active_only=False: (
            next(active_census) if active_only else []
        ),
    )
    result = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )

    request = observed.request
    assert request.mode == helper.TrustMode.full_machine_access_session
    assert request.scope == helper.AuthorityLeaseScope.mission
    assert request.mission_ref == RUN_REF
    assert request.authority_constraints == [
        helper.AuthorityConstraint(
            constraint_ref=helper.LEASE_RUN_CONSTRAINT_REF,
            kind=helper.AuthorityConstraintKind.resource_refs,
            allowed_refs=sorted(
                [
                    RUN_REF,
                    helper.runtime_local_model_endpoint_ref(
                        helper.LOCAL_MODEL_BASE_URL
                    ),
                    helper.runtime_local_model_model_ref(helper.LOCAL_MODEL_REF),
                ]
            ),
            safe_summary=(
                "Limit local model execution to the exact TAW-08 run, "
                "loopback endpoint, and model."
            ),
        )
    ]
    assert request.operator_ref == helper.AUTHORITY_LEASE_LOCAL_OPERATOR_REF
    assert request.requested_domains == DOMAINS
    assert request.duration_minutes == 120
    assert request.constraints == helper.lease_constraints(
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    assert observed.idempotency_ref == ISSUE_IDEMPOTENCY_REF
    assert observed.approved_by_actor_id == helper.AUTHORITY_LEASE_LOCAL_OPERATOR_REF
    assert observed.store.state_dir == state_dir
    assert result == {
        "lease_ref": LEASE_REF,
        "status": "issued",
        "expires_at": EXPIRES_AT.isoformat(),
        "granted_domains": {"provider_model_calls": ["execute"]},
        "receipt_ref": "receipt-ref:taw08-live-issue-unit-test",
        "candidate_revision_ref": CANDIDATE_REVISION_REF,
        "candidate_manifest_digest_ref": CANDIDATE_MANIFEST_DIGEST_REF,
        "run_ref": RUN_REF,
        "lease_helper_digest_ref": helper._helper_digest_ref(),
        "lease_posture_ref": helper.LEASE_POSTURE_REF,
    }
    assert set(result) == {
        "lease_ref",
        "status",
        "expires_at",
        "granted_domains",
        "receipt_ref",
        "candidate_revision_ref",
        "candidate_manifest_digest_ref",
        "run_ref",
        "lease_helper_digest_ref",
        "lease_posture_ref",
    }
    assert str(state_dir) not in json.dumps(result)
    assert [path.name for path in state_dir.iterdir()] == ["authority-state.lock"]


def test_issue_fails_closed_on_authority_or_receipt_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = _state_dir(tmp_path)

    def fake_issue(*_args, **_kwargs):
        return (
            SimpleNamespace(approval_required=True),
            None,
            _active_lease(status=helper.AuthorityLeaseStatus.revoked),
            _issue_receipt(
                status="replayed",
                granted_domains={
                    helper.AuthorityDomain.provider_model_calls: [
                        helper.AuthorityCapability.read,
                        helper.AuthorityCapability.execute,
                    ]
                }
            ),
        )

    monkeypatch.setattr(
        helper, "issue_authority_lease_with_backend_approval", fake_issue
    )
    with pytest.raises(RuntimeError, match="binding drift"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )


def test_postcheck_drift_does_not_revoke_foreign_active_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    foreign = _active_lease(
        lease_ref="authority-lease-ref:foreign-live-unit-test",
        mission_ref="run-ref:taw08:foreign-live-unit-test",
    )
    monkeypatch.setattr(
        helper,
        "issue_authority_lease_with_backend_approval",
        lambda *_args, **_kwargs: (
            SimpleNamespace(approval_required=True),
            None,
            foreign,
            _issue_receipt(lease_ref=foreign.lease_ref),
        ),
    )
    monkeypatch.setattr(
        helper,
        "_compensating_revoke_new_issue",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("foreign lease must not be revoked")
        ),
    )

    with pytest.raises(RuntimeError, match="binding drift"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    assert helper.AuthorityLeaseStore(state_dir).list_leases() == []


def test_new_issue_is_compensating_revoked_when_postcheck_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)

    def fail_safe_receipt(**_kwargs: object) -> dict[str, object]:
        raise RuntimeError("forced post-issue receipt failure")

    monkeypatch.setattr(helper, "_safe_receipt", fail_safe_receipt)
    with pytest.raises(RuntimeError, match="forced post-issue"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    store = helper.AuthorityLeaseStore(state_dir)
    assert store.list_leases(active_only=True) == []
    leases = store.list_leases()
    assert len(leases) == 1
    assert leases[0].status == helper.AuthorityLeaseStatus.revoked
    assert leases[0].constraints["revocation_reason_ref"] == (
        helper.ISSUE_ROLLBACK_REASON_REF
    )


def test_active_lease_is_compensating_revoked_when_receipt_status_drifts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    store = helper.AuthorityLeaseStore(state_dir)
    issued = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    active = store.get_lease(str(issued["lease_ref"]))
    assert active is not None
    receipt = _issue_receipt(status="unexpected")

    monkeypatch.setattr(
        helper,
        "issue_authority_lease_with_backend_approval",
        lambda *_args, **_kwargs: (
            SimpleNamespace(approval_required=True),
            None,
            active,
            receipt,
        ),
    )
    with pytest.raises(RuntimeError, match="binding drift"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    refreshed = helper.AuthorityLeaseStore(state_dir)
    assert refreshed.list_leases(active_only=True) == []
    assert refreshed.list_leases()[0].status == helper.AuthorityLeaseStatus.revoked


def test_interrupted_issue_receipt_write_compensating_revokes_active_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    original_append = helper.AuthorityLeaseStore._append_receipt
    failed = False

    def fail_first_issue_receipt(self, receipt):
        nonlocal failed
        if receipt.operation == "issue" and not failed:
            failed = True
            raise OSError("forced receipt persistence failure")
        return original_append(self, receipt)

    monkeypatch.setattr(
        helper.AuthorityLeaseStore,
        "_append_receipt",
        fail_first_issue_receipt,
    )
    with pytest.raises(helper.AuthorityLeaseApprovalStateError):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    store = helper.AuthorityLeaseStore(state_dir)
    assert store.list_leases(active_only=True) == []
    leases = store.list_leases()
    assert len(leases) == 1
    assert leases[0].status == helper.AuthorityLeaseStatus.revoked
    receipts = store.list_receipts(limit=10)
    assert len(receipts) == 1
    assert receipts[0].operation == "revoke"
    assert receipts[0].status == "revoked"


def test_helper_source_drift_compensating_revokes_captured_active_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    digests = iter(("sha256:" + "a" * 64, "sha256:" + "b" * 64))
    monkeypatch.setattr(helper, "_helper_digest_ref", lambda: next(digests))

    with pytest.raises(RuntimeError, match="binding drift"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    store = helper.AuthorityLeaseStore(state_dir)
    assert store.list_leases(active_only=True) == []
    assert store.list_leases()[0].status == helper.AuthorityLeaseStatus.revoked


def test_replayed_issue_is_revoked_when_output_postcheck_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    issued = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )

    def fail_safe_receipt(**_kwargs: object) -> dict[str, object]:
        raise RuntimeError("forced replay output failure")

    monkeypatch.setattr(helper, "_safe_receipt", fail_safe_receipt)
    with pytest.raises(RuntimeError, match="forced replay"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )

    store = helper.AuthorityLeaseStore(state_dir)
    assert store.list_leases(active_only=True) == []
    leases = store.list_leases()
    assert len(leases) == 1
    assert leases[0].lease_ref == issued["lease_ref"]
    assert leases[0].status == helper.AuthorityLeaseStatus.revoked
    assert leases[0].constraints["revocation_reason_ref"] == (
        helper.ISSUE_ROLLBACK_REASON_REF
    )
    with pytest.raises(RuntimeError, match="binding drift"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=ISSUE_IDEMPOTENCY_REF,
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        )


def test_revoke_targets_only_the_exact_live_lease_and_safe_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = _state_dir(tmp_path)
    existing = _active_lease()
    revoked = _active_lease(status=helper.AuthorityLeaseStatus.revoked)
    observed = SimpleNamespace()

    class FakeStore:
        def __init__(self, received_state_dir: Path) -> None:
            observed.state_dir = received_state_dir

        def get_lease(self, lease_ref: str):
            observed.get_lease_ref = lease_ref
            return existing

        def revoke_lease(self, request, **kwargs):
            observed.request = request
            observed.idempotency_ref = kwargs["idempotency_ref"]
            return revoked, _revoke_receipt()

    monkeypatch.setattr(helper, "AuthorityLeaseStore", FakeStore)
    result = helper.revoke_live_lease(
        state_dir=state_dir,
        lease_ref=LEASE_REF,
        idempotency_ref=REVOKE_IDEMPOTENCY_REF,
    )

    request = observed.request
    assert observed.state_dir == state_dir
    assert observed.get_lease_ref == LEASE_REF
    assert request.lease_ref == LEASE_REF
    assert observed.idempotency_ref == REVOKE_IDEMPOTENCY_REF
    assert result == {
        "lease_ref": LEASE_REF,
        "status": "revoked",
        "expires_at": EXPIRES_AT.isoformat(),
        "granted_domains": {},
        "receipt_ref": "receipt-ref:taw08-live-revoke-unit-test",
        "candidate_revision_ref": CANDIDATE_REVISION_REF,
        "candidate_manifest_digest_ref": CANDIDATE_MANIFEST_DIGEST_REF,
        "run_ref": RUN_REF,
        "lease_helper_digest_ref": helper._helper_digest_ref(),
        "lease_posture_ref": helper.LEASE_POSTURE_REF,
    }
    assert set(result) == {
        "lease_ref",
        "status",
        "expires_at",
        "granted_domains",
        "receipt_ref",
        "candidate_revision_ref",
        "candidate_manifest_digest_ref",
        "run_ref",
        "lease_helper_digest_ref",
        "lease_posture_ref",
    }
    assert str(state_dir) not in json.dumps(result)


def test_revoke_rejects_non_taw08_lease_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = _state_dir(tmp_path)

    class FakeStore:
        def __init__(self, _state_dir: Path) -> None:
            pass

        def get_lease(self, _lease_ref: str):
            return _active_lease(expires_at=ISSUED_AT + timedelta(minutes=60))

        def revoke_lease(self, *_args, **_kwargs):
            raise AssertionError("unsafe target reached mutation")

    monkeypatch.setattr(helper, "AuthorityLeaseStore", FakeStore)
    with pytest.raises(ValueError, match="not the exact live lease"):
        helper.revoke_live_lease(
            state_dir=state_dir,
            lease_ref=LEASE_REF,
            idempotency_ref=REVOKE_IDEMPOTENCY_REF,
        )


def test_real_issue_replay_and_revoke_preserve_exact_candidate_binding(
    tmp_path: Path,
) -> None:
    state_dir = _state_dir(tmp_path)
    issued = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    assert issued["status"] == "issued"
    store = helper.AuthorityLeaseStore(state_dir)
    approval_records = AuthorityLeaseApprovalStore(state_dir).list_records()
    assert len(approval_records) == 1
    assert approval_records[0].grant.expires_at is not None
    approval_lifetime = (
        approval_records[0].grant.expires_at
        - approval_records[0].grant.created_at
    )
    assert timedelta(minutes=119) < approval_lifetime <= timedelta(
        minutes=helper.LEASE_DURATION_MINUTES
    )
    lease = store.get_lease(str(issued["lease_ref"]))
    assert lease is not None
    assert helper._stored_constraints_match(
        lease.constraints,
        expected_binding=helper.lease_constraints(
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref=RUN_REF,
        ),
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        receipt=store.list_receipts(limit=10)[0],
    )

    replayed = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    assert replayed["status"] == "replayed"
    assert replayed["lease_ref"] == issued["lease_ref"]
    assert len(store.list_leases(active_only=True)) == 1

    revoked = helper.revoke_live_lease(
        state_dir=state_dir,
        lease_ref=str(issued["lease_ref"]),
        idempotency_ref=REVOKE_IDEMPOTENCY_REF,
    )
    assert revoked["status"] == "revoked"
    assert store.get_lease(str(issued["lease_ref"])).status == (
        helper.AuthorityLeaseStatus.revoked
    )

    revoke_replay = helper.revoke_live_lease(
        state_dir=state_dir,
        lease_ref=str(issued["lease_ref"]),
        idempotency_ref=REVOKE_IDEMPOTENCY_REF,
    )
    assert revoke_replay["status"] == "replayed"
    assert revoke_replay["lease_ref"] == issued["lease_ref"]


def test_real_issue_rejects_second_distinct_active_lease(
    tmp_path: Path,
) -> None:
    state_dir = _state_dir(tmp_path)
    issued = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )

    with pytest.raises(RuntimeError, match="another active lease"):
        helper.issue_live_lease(
            state_dir=state_dir,
            idempotency_ref="idempotency-ref:taw08-live-issue-distinct-unit-test",
            candidate_revision_ref=CANDIDATE_REVISION_REF,
            candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
            run_ref="run-ref:taw08:distinct-live-unit-test",
        )

    store = helper.AuthorityLeaseStore(state_dir)
    active = store.list_leases(active_only=True)
    assert len(active) == 1
    assert active[0].lease_ref == issued["lease_ref"]
    assert len(store.list_leases()) == 1
    assert len(AuthorityLeaseApprovalStore(state_dir).list_records()) == 1


def test_revoke_remains_available_after_helper_source_digest_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _state_dir(tmp_path)
    issued = helper.issue_live_lease(
        state_dir=state_dir,
        idempotency_ref=ISSUE_IDEMPOTENCY_REF,
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        candidate_manifest_digest_ref=CANDIDATE_MANIFEST_DIGEST_REF,
        run_ref=RUN_REF,
    )
    monkeypatch.setattr(helper, "_helper_digest_ref", lambda: "sha256:" + "f" * 64)

    revoked = helper.revoke_live_lease(
        state_dir=state_dir,
        lease_ref=str(issued["lease_ref"]),
        idempotency_ref=REVOKE_IDEMPOTENCY_REF,
    )

    assert revoked["status"] == "revoked"


def test_state_dir_must_be_absolute_owner_only_and_symlink_free(
    tmp_path: Path,
) -> None:
    state_dir = _state_dir(tmp_path)
    assert helper._owner_only_state_dir(state_dir) == state_dir

    state_dir.chmod(0o755)
    with pytest.raises(ValueError, match="owner-only"):
        helper._owner_only_state_dir(state_dir)
    state_dir.chmod(0o700)

    relative = Path("authority-state")
    with pytest.raises(ValueError, match="absolute"):
        helper._owner_only_state_dir(relative)

    linked = tmp_path / "linked-state"
    linked.symlink_to(state_dir, target_is_directory=True)
    with pytest.raises(ValueError, match="owner-only"):
        helper._owner_only_state_dir(linked)

    unsafe_file = state_dir / "unsafe.json"
    unsafe_file.write_text("{}\n", encoding="utf-8")
    unsafe_file.chmod(0o644)
    with pytest.raises(ValueError, match="unsafe entry"):
        helper._owner_only_state_dir(state_dir)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_state_dir_rejects_extended_acl(tmp_path: Path) -> None:
    state_dir = _state_dir(tmp_path)
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow read", str(state_dir)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            helper._owner_only_state_dir(state_dir)
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(state_dir)),
            check=False,
            capture_output=True,
        )


def test_cli_has_only_issue_and_revoke_fixed_surfaces() -> None:
    state_dir = Path("/absolute/owner-only/state")
    issue = helper._parser().parse_args(
        [
            "issue",
            "--state-dir",
            str(state_dir),
            "--idempotency-ref",
            ISSUE_IDEMPOTENCY_REF,
            "--candidate-revision-ref",
            CANDIDATE_REVISION_REF,
            "--candidate-manifest-digest-ref",
            CANDIDATE_MANIFEST_DIGEST_REF,
            "--run-ref",
            RUN_REF,
        ]
    )
    assert vars(issue) == {
        "operation": "issue",
        "state_dir": state_dir,
        "idempotency_ref": ISSUE_IDEMPOTENCY_REF,
        "candidate_revision_ref": CANDIDATE_REVISION_REF,
        "candidate_manifest_digest_ref": CANDIDATE_MANIFEST_DIGEST_REF,
        "run_ref": RUN_REF,
    }
    revoke = helper._parser().parse_args(
        [
            "revoke",
            "--state-dir",
            str(state_dir),
            "--lease-ref",
            LEASE_REF,
            "--idempotency-ref",
            REVOKE_IDEMPOTENCY_REF,
        ]
    )
    assert vars(revoke) == {
        "operation": "revoke",
        "state_dir": state_dir,
        "lease_ref": LEASE_REF,
        "idempotency_ref": REVOKE_IDEMPOTENCY_REF,
    }
    with pytest.raises(SystemExit):
        helper._parser().parse_args(
            [
                "issue",
                "--state-dir",
                str(state_dir),
                "--idempotency-ref",
                ISSUE_IDEMPOTENCY_REF,
                "--candidate-revision-ref",
                CANDIDATE_REVISION_REF,
                "--candidate-manifest-digest-ref",
                CANDIDATE_MANIFEST_DIGEST_REF,
                "--run-ref",
                RUN_REF,
                "--duration-minutes",
                "480",
            ]
        )


def test_main_emits_only_safe_json_and_errors_are_generic(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    safe = {
        "lease_ref": LEASE_REF,
        "status": "issued",
        "expires_at": EXPIRES_AT.isoformat(),
        "granted_domains": {"provider_model_calls": ["execute"]},
        "receipt_ref": "receipt-ref:taw08-live-issue-unit-test",
        "candidate_revision_ref": CANDIDATE_REVISION_REF,
        "candidate_manifest_digest_ref": CANDIDATE_MANIFEST_DIGEST_REF,
        "run_ref": RUN_REF,
        "lease_helper_digest_ref": helper._helper_digest_ref(),
        "lease_posture_ref": helper.LEASE_POSTURE_REF,
    }
    monkeypatch.setattr(helper, "issue_live_lease", lambda **_kwargs: safe)
    assert (
        helper.main(
            [
                "issue",
                "--state-dir",
                "/owner/private/state",
                "--idempotency-ref",
                ISSUE_IDEMPOTENCY_REF,
                "--candidate-revision-ref",
                CANDIDATE_REVISION_REF,
                "--candidate-manifest-digest-ref",
                CANDIDATE_MANIFEST_DIGEST_REF,
                "--run-ref",
                RUN_REF,
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert json.loads(output.out) == safe
    assert output.err == ""
    assert "/owner/private/state" not in output.out

    def blocked(**_kwargs):
        raise RuntimeError("sensitive state detail /owner/private/state")

    monkeypatch.setattr(helper, "issue_live_lease", blocked)
    assert (
        helper.main(
            [
                "issue",
                "--state-dir",
                "/owner/private/state",
                "--idempotency-ref",
                ISSUE_IDEMPOTENCY_REF,
                "--candidate-revision-ref",
                CANDIDATE_REVISION_REF,
                "--candidate-manifest-digest-ref",
                CANDIDATE_MANIFEST_DIGEST_REF,
                "--run-ref",
                RUN_REF,
            ]
        )
        == 1
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "TAW-08 live lease operation blocked.\n"


def test_helper_contains_no_model_provider_or_network_call_surface() -> None:
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden = (
        "RuntimeGateway",
        "execute_provider",
        "subprocess",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "openai",
        "anthropic",
    )
    assert not any(token in source for token in forbidden)
