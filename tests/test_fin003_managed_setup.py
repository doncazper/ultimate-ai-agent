"""Synthetic-only managed setup transaction and exact authority regressions."""

import pytest


def _service(tmp_path, *, environment=None, source=None):
    from datetime import datetime, timezone
    from hashlib import sha256
    from dataclasses import replace
    from ultimate_ai_agent.core.finance_managed_profile import (
        FinanceManagedLayout,
        InstalledBundleSourceV1,
        FinanceManagedHelperIdentityV1,
        VerifiedFinanceHelper,
        managed_ref,
        managed_wire_payload,
    )
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupService

    def bind(record, field, kind):
        payload = managed_wire_payload(record)
        del payload[field]
        return replace(record, **{field: managed_ref(kind, payload)})

    provenance = bind(
        InstalledBundleSourceV1(
            source_provenance_ref="pending",
            bundle_ref="macos-bundle-ref:sha256:" + "1" * 64,
            bundle_inventory_ref="bundle-inventory-ref:sha256:" + "2" * 64,
            source_commit_ref="git-commit:" + "3" * 40,
            source_version_ref="macos-version-ref:sha256:" + "4" * 64,
        ),
        "source_provenance_ref",
        "source",
    )
    data = b"synthetic-test-helper-never-executed"
    identity = bind(
        FinanceManagedHelperIdentityV1(
            helper_ref="pending",
            helper_fingerprint_ref="helper-bytes-ref:sha256:"
            + sha256(data).hexdigest(),
            helper_size_bytes=len(data),
            architecture="arm64",
            source=provenance,
            signing_kind="ad-hoc",
        ),
        "helper_ref",
        "helper",
    )
    helper = VerifiedFinanceHelper(identity=identity, executable_bytes=data)
    return ManagedFinanceSetupService(
        layout=FinanceManagedLayout(root=tmp_path / "managed"),
        source_provider=source or (lambda: helper),
        environment_provider=lambda: environment or {},
        clock=lambda: datetime.now(timezone.utc),
    )


def _prepare(service, suffix="first", operation="enroll"):
    return service.prepare(
        operation, "request-ref:setup:" + suffix, "idempotency-ref:setup:" + suffix
    ).preparation


def test_read_only_prepare_confirm_and_source_independent_replay(tmp_path):
    from ultimate_ai_agent.core.finance.managed_setup import (
        parse_managed_setup_preparation,
        serialize_managed_setup_preparation,
    )

    service = _service(tmp_path)
    assert service.inspect().status == "missing"
    preparation = _prepare(service)
    assert not service.layout.root.exists()
    raw = serialize_managed_setup_preparation(preparation)
    assert parse_managed_setup_preparation(raw) == preparation
    result = service.confirm(preparation, confirmed=True)
    assert result.outcome == "committed" and result.mutation_performed
    assert result.authority_state_written
    assert service.inspect().status == "present"
    assert not service.layout.repository_dir.exists()
    assert not result.receipt.finance_key_created
    assert not result.receipt.keychain_item_created
    service.source_provider = lambda: pytest.fail(
        "historical replay opened original source"
    )
    replay = service.confirm(preparation, confirmed=True)
    assert (
        replay.replayed
        and not replay.mutation_performed
        and not replay.authority_state_written
    )
    assert replay.receipt == result.receipt
    assert (
        service.prepare(
            "enroll", preparation.intent.request_ref, preparation.intent.idempotency_ref
        ).status
        == "historical"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("operator_confirmation_required", 1),
        ("mutation_performed", 0),
        ("policy_revision_ref", "policy-ref:untrusted"),
        ("observed_state_ref", "state-ref:untrusted"),
        ("resource_refs", ["resource-ref:untrusted"]),
    ],
)
def test_preparation_tampering_rejected_before_writes(tmp_path, field, value):
    import json
    from ultimate_ai_agent.core.finance.managed_setup import (
        ManagedFinanceSetupError,
        parse_managed_setup_preparation,
        serialize_managed_setup_preparation,
    )

    service = _service(tmp_path)
    preparation = _prepare(service)
    payload = json.loads(serialize_managed_setup_preparation(preparation))
    payload[field] = value
    with pytest.raises(ManagedFinanceSetupError):
        parse_managed_setup_preparation(json.dumps(payload).encode())
    assert not service.layout.root.exists()


@pytest.mark.parametrize(
    "raw",
    [b'{"intent":1,"intent":2}', b"[" * 40 + b"]" * 40, b"{}" + b" " * (128 * 1024)],
    ids=["duplicate-key", "depth-limit", "byte-limit"],
)
def test_preparation_transport_bounds(raw):
    from ultimate_ai_agent.core.finance.managed_setup import (
        ManagedFinanceSetupError,
        parse_managed_setup_preparation,
    )

    with pytest.raises(ManagedFinanceSetupError):
        parse_managed_setup_preparation(raw)


@pytest.mark.parametrize(
    "environment",
    [
        {"UAA_FINANCE_SAFE_DISABLE": ""},
        {"UAA_FINANCE_SAFE_DISABLE": "true"},
        {"UAA_FINANCE_NATIVE_HELPER_PATH": ""},
        {"UAA_FINANCE_NATIVE_HELPER_SHA256": "invalid"},
        {"UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR": ""},
    ],
)
def test_override_and_disable_reject_without_writes(tmp_path, environment):
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path, environment=environment)
    with pytest.raises(ManagedFinanceSetupError):
        _prepare(service)
    assert not service.layout.root.exists()


def test_strict_confirmation_and_expired_window_leave_no_state(tmp_path):
    from datetime import timedelta
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    with pytest.raises(ManagedFinanceSetupError, match="CONFIRMATION_REQUIRED"):
        service.confirm(preparation, confirmed=1)
    service.clock = lambda: preparation.expires_at + timedelta(seconds=1)
    with pytest.raises(ManagedFinanceSetupError, match="PREPARATION_EXPIRED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.root.exists()


def test_changed_source_rejected_before_authority_bootstrap(tmp_path):
    from dataclasses import replace
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = service.source_provider()
    from hashlib import sha256
    from ultimate_ai_agent.core.finance_managed_profile import (
        managed_ref,
        managed_wire_payload,
    )

    data = b"different-valid-helper"
    identity = replace(
        original.identity,
        helper_fingerprint_ref="helper-bytes-ref:sha256:" + sha256(data).hexdigest(),
        helper_size_bytes=len(data),
    )
    payload = managed_wire_payload(identity)
    del payload["helper_ref"]
    identity = replace(identity, helper_ref=managed_ref("helper", payload))
    service.source_provider = lambda: replace(
        original, identity=identity, executable_bytes=data
    )
    with pytest.raises(ManagedFinanceSetupError, match="SOURCE_CHANGED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.root.exists()


@pytest.mark.parametrize("phase", ["before_stage", "before_promote", "before_terminal"])
def test_interrupted_enrollment_refreshes_same_intent(tmp_path, monkeypatch, phase):
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    if phase == "before_stage":
        original = service._enroll
        monkeypatch.setattr(
            service,
            "_enroll",
            lambda *args: (_ for _ in ()).throw(OSError("synthetic fault")),
        )
    elif phase == "before_promote":
        original = service._promote
        monkeypatch.setattr(
            service,
            "_promote",
            lambda *args: (_ for _ in ()).throw(OSError("synthetic fault")),
        )
    else:
        original = service._write_state
        calls = 0

        def fault(*args):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError("synthetic fault")
            return original(*args)

        monkeypatch.setattr(service, "_write_state", fault)
    with pytest.raises(ManagedFinanceSetupError, match="MUTATION_INTERRUPTED"):
        service.confirm(preparation, confirmed=True)
    pending = read_managed_state(service.layout).state.pending_attempt
    assert pending.intent == preparation.intent
    monkeypatch.undo()
    refreshed = service.refresh(preparation).preparation
    assert refreshed.intent == preparation.intent
    assert refreshed.preview_ref != preparation.preview_ref
    assert service.confirm(refreshed, confirmed=True).outcome == "committed"
    assert len(read_managed_state(service.layout).state.terminal_receipts) == 1


@pytest.mark.parametrize("phase", ["before_stage", "before_promote", "before_terminal"])
def test_discard_needs_no_original_source_and_retains_both_intents(
    tmp_path, monkeypatch, phase
):
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    if phase == "before_stage":
        monkeypatch.setattr(
            service, "_enroll", lambda *args: (_ for _ in ()).throw(OSError())
        )
    elif phase == "before_promote":
        monkeypatch.setattr(
            service, "_promote", lambda *args: (_ for _ in ()).throw(OSError())
        )
    else:
        original = service._write_state
        calls = 0

        def fault(*args):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError()
            return original(*args)

        monkeypatch.setattr(service, "_write_state", fault)
    with pytest.raises(ManagedFinanceSetupError, match="MUTATION_INTERRUPTED"):
        service.confirm(preparation, confirmed=True)
    monkeypatch.undo()
    source = service.source_provider
    service.source_provider = lambda: pytest.fail("discard consulted original source")
    discard = _prepare(service, "discard", "discard_incomplete")
    result = service.confirm(discard, confirmed=True)
    assert result.outcome == "abandoned"
    assert result.receipt.original_enrollment_intent == preparation.intent
    assert result.receipt.intent == discard.intent
    assert service.inspect().status == "unconfigured"
    assert service.confirm(preparation, confirmed=True).receipt == result.receipt
    service.source_provider = source
    next_preparation = _prepare(service, "second")
    service.confirm(next_preparation, confirmed=True)
    assert len(read_managed_state(service.layout).state.terminal_receipts) == 2
    # Historical abandonment is independent of a later enrollment's helper readiness.
    service.layout.helper_path(
        next_preparation.desired_profile.helper.helper_sha256
    ).unlink()
    service.source_provider = lambda: pytest.fail("historical discard consulted source")
    assert service.confirm(discard, confirmed=True).receipt == result.receipt


def test_mutable_nested_approval_cannot_bypass_binding(tmp_path):
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    preparation.approval_request.metadata["synthetic_only"] = 1
    with pytest.raises(ManagedFinanceSetupError, match="PREPARATION_INVALID"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.root.exists()


def test_lost_policy_and_disable_are_checked_before_pending_write(
    tmp_path, monkeypatch
):
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = module.issue_authority_lease_with_backend_approval

    def issue(*args, **kwargs):
        result = original(*args, **kwargs)
        service.environment_provider = lambda: {"UAA_FINANCE_SAFE_DISABLE": ""}
        return result

    monkeypatch.setattr(module, "issue_authority_lease_with_backend_approval", issue)
    with pytest.raises(ManagedFinanceSetupError, match="SAFE_DISABLE_ENGAGED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.state_file.exists()
    assert not service.layout.staging_dir.exists()


def test_revoked_lease_cannot_be_reissued_by_same_preparation(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.authority import AuthorityLeaseRevokeRequest

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = module.issue_authority_lease_with_backend_approval

    def issue(store, *args, **kwargs):
        result = original(store, *args, **kwargs)
        store.revoke_lease(
            AuthorityLeaseRevokeRequest(
                lease_ref=result[2].lease_ref,
                decision_reason_ref="reason-ref:test:revoked",
                safe_summary="Synthetic revocation.",
            ),
            idempotency_ref="idempotency-ref:test:revoke",
        )
        return result

    monkeypatch.setattr(module, "issue_authority_lease_with_backend_approval", issue)
    with pytest.raises(module.ManagedFinanceSetupError, match="LEASE_DENIED"):
        service.confirm(preparation, confirmed=True)
    monkeypatch.undo()
    with pytest.raises(module.ManagedFinanceSetupError, match="LEASE_DENIED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.state_file.exists()
    assert not service.layout.staging_dir.exists()


def test_revoked_action_grant_blocks_pending_write(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

    service = _service(tmp_path)
    preparation = _prepare(service)
    approvals = LocalApprovalAuthority()
    monkeypatch.setattr(module, "LocalApprovalAuthority", lambda: approvals)
    original = module.issue_authority_lease_with_backend_approval

    def issue(*args, **kwargs):
        result = original(*args, **kwargs)
        approvals.revoke(preparation.expected_approval_ref, "Synthetic revocation.")
        return result

    monkeypatch.setattr(module, "issue_authority_lease_with_backend_approval", issue)
    with pytest.raises(module.ManagedFinanceSetupError, match="APPROVAL_DENIED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.state_file.exists()


def test_policy_denial_does_not_create_local_authority(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    monkeypatch.setattr(
        service.policy,
        "can_execute",
        lambda *args: SimpleNamespace(
            status="denied", allowed=False, requires_approval=False
        ),
    )
    with pytest.raises(ManagedFinanceSetupError, match="POLICY_DENIED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.root.exists()


def test_global_kill_switch_cannot_be_overridden_by_mapping(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup_authority as authority

    service = _service(tmp_path)
    preparation = _prepare(service)
    monkeypatch.setattr(authority, "authority_lease_kill_switch_engaged", lambda: True)
    with pytest.raises(
        authority.ManagedFinanceSetupError, match="SAFE_DISABLE_ENGAGED"
    ):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.root.exists()


def test_unknown_staged_artifact_is_preserved_on_discard(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = service._write_state
    calls = 0

    def fault(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError()
        return original(*args)

    monkeypatch.setattr(service, "_write_state", fault)
    with pytest.raises(module.ManagedFinanceSetupError):
        service.confirm(preparation, confirmed=True)
    monkeypatch.undo()
    pending = read_managed_state(service.layout).state.pending_attempt
    assert pending.staging_directory_identity_ref is None
    directory = service.layout.staging_attempt_dir(pending.attempt_ref)
    before = directory.stat()
    discard = _prepare(service, "discard", "discard_incomplete")
    with pytest.raises(module.ManagedFinanceSetupError, match="OWNERSHIP_UNVERIFIED"):
        service.confirm(discard, confirmed=True)
    assert directory.stat().st_ino == before.st_ino
    assert read_managed_state(service.layout).state.pending_attempt == pending


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "public-mode"])
def test_enrolled_helper_tamper_blocks_committed_replay(tmp_path, kind):
    import os
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    service.confirm(preparation, confirmed=True)
    helper = service.layout.helper_path(
        preparation.desired_profile.helper.helper_sha256
    )
    if kind == "symlink":
        target = tmp_path / "other-helper"
        helper.rename(target)
        helper.symlink_to(target)
    elif kind == "hardlink":
        os.link(helper, tmp_path / "other-helper")
    else:
        helper.chmod(0o555)
    service.source_provider = lambda: pytest.fail("replay called source")
    with pytest.raises(ManagedFinanceSetupError, match="STATE_INVALID"):
        service.confirm(preparation, confirmed=True)


def test_reused_identity_with_changed_operation_or_id_conflicts(tmp_path):
    from ultimate_ai_agent.core.finance.managed_setup import ManagedFinanceSetupError

    service = _service(tmp_path)
    preparation = _prepare(service)
    service.confirm(preparation, confirmed=True)
    for operation, request, idem in [
        (
            "discard_incomplete",
            preparation.intent.request_ref,
            preparation.intent.idempotency_ref,
        ),
        ("enroll", preparation.intent.request_ref, "idempotency-ref:different"),
        ("enroll", "request-ref:different", preparation.intent.idempotency_ref),
    ]:
        with pytest.raises(ManagedFinanceSetupError, match="STATE_CONFLICT"):
            service.prepare(operation, request, idem)


def test_capacity_refusal_precedes_state_or_staging(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup as module

    service = _service(tmp_path)

    def exhausted(_state):
        raise ValueError("synthetic capacity")

    monkeypatch.setattr(module, "serialize_managed_state", exhausted)
    with pytest.raises(module.ManagedFinanceSetupError, match="CAPACITY_EXHAUSTED"):
        _prepare(service)
    assert not service.layout.root.exists()


@pytest.mark.parametrize(
    "change",
    [
        "coarse",
        "wrong-domain",
        "wrong-operation",
        "two-operations",
        "missing-lease",
    ],
)
def test_exact_lease_admission_and_local_full_binding(tmp_path, change):
    from ultimate_ai_agent.core.authority.contracts import (
        _exact_authority_issue_binding,
    )
    from ultimate_ai_agent.core.finance.managed_setup_authority import (
        build_setup_lease_request,
    )

    service = _service(tmp_path)
    request = build_setup_lease_request(_prepare(service))
    assert _exact_authority_issue_binding(request) is not None
    if change == "coarse":
        request = request.model_copy(update={"constraints": {}})
    elif change == "wrong-domain":
        request = request.model_copy(
            update={"requested_domains": {"browser": ["write"]}}
        )
    elif change == "wrong-operation":
        request.constraints["exact_operation_ref"] = (
            "finance-operation-ref:FIN-003:replace_active"
        )
    elif change == "two-operations":
        request.authority_constraints[1].maximum = 2
    else:
        request = request.model_copy(update={"requested_lease_ref": None})
    assert _exact_authority_issue_binding(request) is None


def test_extra_resources_in_stored_lease_are_denied_by_local_gate(
    tmp_path, monkeypatch
):
    import ultimate_ai_agent.core.finance.managed_setup as module

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = module.issue_authority_lease_with_backend_approval

    def issue(store, request, **kwargs):
        request.authority_constraints[0].allowed_refs.append("resource-ref:unrelated")
        return original(store, request, **kwargs)

    monkeypatch.setattr(module, "issue_authority_lease_with_backend_approval", issue)
    with pytest.raises(module.ManagedFinanceSetupError, match="LEASE_DENIED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.state_file.exists()
    assert not service.layout.staging_dir.exists()


def test_concurrent_same_intent_has_one_commit_and_one_replay(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    helper = service.source_provider()
    barrier = Barrier(2)

    def source():
        barrier.wait(timeout=5)
        return helper

    service.source_provider = source
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(service.confirm, preparation, True) for _ in range(2)
        ]
        results = [future.result(timeout=15) for future in futures]
    assert sorted(result.replayed for result in results) == [False, True]
    assert results[0].receipt == results[1].receipt
    assert len(read_managed_state(service.layout).state.terminal_receipts) == 1


def test_interrupted_discard_resumes_after_owned_helper_removed(tmp_path, monkeypatch):
    import ultimate_ai_agent.core.finance.managed_setup as module

    service = _service(tmp_path)
    preparation = _prepare(service)
    monkeypatch.setattr(
        service, "_promote", lambda *args: (_ for _ in ()).throw(OSError())
    )
    with pytest.raises(module.ManagedFinanceSetupError):
        service.confirm(preparation, confirmed=True)
    monkeypatch.undo()
    service.source_provider = lambda: pytest.fail("discard consulted source")
    discard = _prepare(service, "discard", "discard_incomplete")
    original = module.os.rmdir
    monkeypatch.setattr(
        module.os, "rmdir", lambda *args, **kwargs: (_ for _ in ()).throw(OSError())
    )
    with pytest.raises(module.ManagedFinanceSetupError):
        service.confirm(discard, confirmed=True)
    monkeypatch.setattr(module.os, "rmdir", original)
    refreshed = service.refresh(discard).preparation
    assert service.confirm(refreshed, confirmed=True).outcome == "abandoned"


def test_terminal_serialization_failure_precedes_helper_promotion(
    tmp_path, monkeypatch
):
    import ultimate_ai_agent.core.finance.managed_setup as module

    service = _service(tmp_path)
    preparation = _prepare(service)
    original = module.serialize_managed_state

    def serialization(state):
        if state.active_profile:
            raise ValueError("synthetic final capacity failure")
        return original(state)

    monkeypatch.setattr(module, "serialize_managed_state", serialization)
    with pytest.raises(module.ManagedFinanceSetupError, match="CAPACITY_EXHAUSTED"):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.helper_path(
        preparation.desired_profile.helper.helper_sha256
    ).exists()
    assert service.inspect().status == "incomplete"


def test_recomputed_resource_wrapper_is_not_execution_authority(tmp_path):
    from dataclasses import replace
    import ultimate_ai_agent.core.finance.managed_setup_authority as authority

    service = _service(tmp_path)
    preparation = _prepare(service)
    refs = tuple(sorted((*preparation.resource_refs, "resource-ref:unrelated")))
    approval = authority._approval(
        preparation.intent,
        preparation.exact_scope_ref,
        preparation.action_envelope_ref,
        preparation.expected_approval_ref,
        refs,
        preparation.prepared_at,
        preparation.expires_at,
    )
    changed = replace(preparation, resource_refs=refs, approval_request=approval)
    payload = authority.preparation_payload(changed)
    del payload["preview_ref"]
    changed = replace(changed, preview_ref=authority._ref("preview", payload))
    parsed = authority.parse_managed_setup_preparation(
        authority.serialize_managed_setup_preparation(changed)
    )
    with pytest.raises(authority.ManagedFinanceSetupError, match="PREPARATION_INVALID"):
        service.confirm(parsed, confirmed=True)
    assert not service.layout.root.exists()


def test_replacing_grant_under_same_ref_cannot_continue_pending_write(
    tmp_path, monkeypatch
):
    from datetime import timedelta
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    approvals = LocalApprovalAuthority()
    monkeypatch.setattr(module, "LocalApprovalAuthority", lambda: approvals)
    original = service._write_state
    calls = 0

    def replace_grant(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            approvals.grant(
                preparation.approval_request.approval_request_id,
                approved_by_actor_id=module.MANAGED_SETUP_APPROVER_REF,
                approval_ref=preparation.expected_approval_ref,
                expires_at=preparation.expires_at - timedelta(seconds=1),
            )
        return original(*args)

    monkeypatch.setattr(service, "_write_state", replace_grant)
    with pytest.raises(module.ManagedFinanceSetupError, match="APPROVAL_DENIED"):
        service.confirm(preparation, confirmed=True)
    assert (
        read_managed_state(
            service.layout
        ).state.pending_attempt.staging_directory_identity_ref
        is None
    )
    assert not service.layout.helper_path(
        preparation.desired_profile.helper.helper_sha256
    ).exists()


@pytest.mark.parametrize("changed", ["expired", "replaced-grant"])
def test_admission_revalidated_after_authority_lock_before_lease_issue(
    tmp_path, monkeypatch, changed
):
    from contextlib import contextmanager
    from datetime import timedelta
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
    from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager

    service = _service(tmp_path)
    preparation = _prepare(service)
    approvals = LocalApprovalAuthority()
    monkeypatch.setattr(module, "LocalApprovalAuthority", lambda: approvals)
    acquire = FileSingleWriterLockManager.acquire

    @contextmanager
    def waited(manager, key, *args, **kwargs):
        with acquire(manager, key, *args, **kwargs):
            if key == module.AUTHORITY_STATE_LOCK_KEY:
                if changed == "expired":
                    service.clock = lambda: preparation.expires_at
                else:
                    approvals.grant(
                        preparation.approval_request.approval_request_id,
                        approved_by_actor_id=module.MANAGED_SETUP_APPROVER_REF,
                        approval_ref=preparation.expected_approval_ref,
                        expires_at=preparation.expires_at - timedelta(seconds=1),
                    )
            yield

    monkeypatch.setattr(FileSingleWriterLockManager, "acquire", waited)
    monkeypatch.setattr(
        module,
        "issue_authority_lease_with_backend_approval",
        lambda *args, **kwargs: pytest.fail("expired/replaced admission issued lease"),
    )
    expected = "PREPARATION_EXPIRED" if changed == "expired" else "APPROVAL_DENIED"
    with pytest.raises(module.ManagedFinanceSetupError, match=expected):
        service.confirm(preparation, confirmed=True)
    assert not service.layout.state_file.exists()
    assert not service.layout.staging_dir.exists()
    assert not list(service.layout.authority_dir.rglob("*.json"))
    assert (
        list(
            (
                service.layout.root / module.AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_DIR
            ).iterdir()
        )
        == []
    )


@pytest.mark.parametrize("promoted", [False, True])
@pytest.mark.parametrize("sibling_kind", ["file", "directory"])
def test_recovery_refuses_unrecorded_siblings_without_adoption_or_deletion(
    tmp_path, monkeypatch, promoted, sibling_kind
):
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.finance_managed_profile import read_managed_state

    service = _service(tmp_path)
    preparation = _prepare(service)
    if promoted:
        original = service._write_state
        calls = 0

        def fault(*args):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError()
            return original(*args)

        monkeypatch.setattr(service, "_write_state", fault)
    else:
        monkeypatch.setattr(
            service, "_promote", lambda *args: (_ for _ in ()).throw(OSError())
        )
    with pytest.raises(module.ManagedFinanceSetupError, match="MUTATION_INTERRUPTED"):
        service.confirm(preparation, confirmed=True)
    monkeypatch.undo()
    pending = read_managed_state(service.layout).state.pending_attempt
    parent = (
        service.layout.helper_path(pending.desired_profile.helper.helper_sha256).parent
        if promoted
        else service.layout.staging_dir / pending.attempt_ref.rsplit(":", 1)[1]
    )
    extra = parent / "unrecorded"
    if sibling_kind == "directory":
        extra.mkdir(mode=0o700)
    else:
        extra.write_bytes(b"synthetic-unrecorded")
        extra.chmod(0o600)
    refreshed = service.refresh(preparation).preparation
    with pytest.raises(module.ManagedFinanceSetupError, match="OWNERSHIP_UNVERIFIED"):
        service.confirm(refreshed, confirmed=True)
    assert extra.exists()
    assert service.inspect().status == "incomplete"
    discard = _prepare(service, "discard", "discard_incomplete")
    with pytest.raises(module.ManagedFinanceSetupError, match="OWNERSHIP_UNVERIFIED"):
        service.confirm(discard, confirmed=True)
    assert extra.exists()
    assert (parent / "helper").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("observed_state_ref", 7),
        ("observed_state_ref", "not-a-ref"),
        ("observed_pending_attempt_ref", False),
        ("observed_pending_attempt_ref", "state-ref:wrong-kind"),
        ("exact_scope_ref", "scope-ref:wrong-kind"),
        ("action_envelope_ref", 7),
        ("expected_approval_ref", False),
        ("requested_lease_ref", "lease-ref:wrong-kind"),
    ],
)
def test_rehashed_preparation_still_requires_exact_reference_types(
    tmp_path, field, value
):
    from dataclasses import replace
    import json
    import ultimate_ai_agent.core.finance.managed_setup_authority as module

    preparation = replace(_prepare(_service(tmp_path)), **{field: value})
    payload = module.preparation_payload(preparation)
    del payload["preview_ref"]
    preparation = replace(preparation, preview_ref=module._ref("preview", payload))
    with pytest.raises(module.ManagedFinanceSetupError, match="PREPARATION_INVALID"):
        module.serialize_managed_setup_preparation(preparation)
    raw = json.dumps(module.preparation_payload(preparation)).encode()
    with pytest.raises(module.ManagedFinanceSetupError, match="PREPARATION_INVALID"):
        module.parse_managed_setup_preparation(raw)


@pytest.mark.parametrize("rebound", ["root", "authority"])
def test_rebound_managed_directory_at_lock_never_reaches_lease_issuer(
    tmp_path, monkeypatch, rebound
):
    from contextlib import contextmanager
    import ultimate_ai_agent.core.finance.managed_setup as module
    from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager

    service = _service(tmp_path)
    preparation = _prepare(service)
    acquire = FileSingleWriterLockManager.acquire
    replacement = (
        service.layout.root if rebound == "root" else service.layout.authority_dir
    )

    @contextmanager
    def waited(manager, key, *args, **kwargs):
        with acquire(manager, key, *args, **kwargs):
            if key == module.AUTHORITY_STATE_LOCK_KEY:
                replacement.rename(
                    replacement.with_name(replacement.name + "-retained")
                )
                replacement.mkdir(mode=0o700)
            yield

    monkeypatch.setattr(FileSingleWriterLockManager, "acquire", waited)
    monkeypatch.setattr(
        module,
        "issue_authority_lease_with_backend_approval",
        lambda *args, **kwargs: pytest.fail("rebound location issued authority"),
    )
    with pytest.raises(module.ManagedFinanceSetupError, match="OWNERSHIP_UNVERIFIED"):
        service.confirm(preparation, confirmed=True)
    assert list(replacement.iterdir()) == []
    assert not service.layout.state_file.exists()
