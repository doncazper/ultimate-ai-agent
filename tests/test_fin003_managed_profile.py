"""Exact managed wire, descriptor snapshot and startup discovery regressions."""

import hashlib
import json
import os
import stat
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest


def _module():
    from ultimate_ai_agent.core import finance_managed_profile

    return finance_managed_profile


def _encoded(payload):
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _bind(m, cls, kind, field_name, **values):
    record = cls(**{field_name: m.managed_ref(kind, {}), **values})
    payload = m.managed_wire_payload(record)
    return replace(
        record,
        **{
            field_name: m.managed_ref(
                kind,
                {key: value for key, value in payload.items() if key != field_name},
            )
        },
    )


def _helper(m, data=b"synthetic-native-helper", *, developer=False):
    if developer:
        source = _bind(
            m,
            m.DeveloperBuildSourceV1,
            "source",
            "source_provenance_ref",
            build_manifest_ref=m.managed_ref("build-manifest", {}),
            source_fingerprint_ref=m.managed_ref("source-files", []),
            builder_fingerprint_ref=m.managed_ref("builder", {}),
            artifact_selector_ref="artifact-selector-ref:finance/FIN-003/native-helper:arm64:v1",
        )
    else:
        source = _bind(
            m,
            m.InstalledBundleSourceV1,
            "source",
            "source_provenance_ref",
            bundle_ref="macos-bundle-ref:sha256:" + "a" * 64,
            bundle_inventory_ref="bundle-inventory-ref:sha256:" + "b" * 64,
            source_commit_ref="git-commit:" + "c" * 40,
            source_version_ref="macos-version-ref:sha256:" + "d" * 64,
        )
    return _bind(
        m,
        m.FinanceManagedHelperIdentityV1,
        "helper",
        "helper_ref",
        helper_fingerprint_ref="helper-bytes-ref:sha256:"
        + hashlib.sha256(data).hexdigest(),
        helper_size_bytes=len(data),
        architecture="arm64",
        source=source,
        signing_kind="ad-hoc",
    )


def _profile(m, layout, *, data=b"synthetic-native-helper", developer=False):
    return _bind(
        m,
        m.FinanceManagedProfileV1,
        "profile",
        "profile_ref",
        repository_ref=m.managed_repository_ref(layout),
        helper=_helper(m, data, developer=developer),
    )


def _intent(m, profile, label="first", *, expected=None, discard=None, long=False):
    absent = m.managed_ref(
        "absent-state",
        {
            "layout_ref": m.MANAGED_LAYOUT_REF,
            "repository_ref": profile.repository_ref,
        },
    )
    request = "request-ref:" + label
    idempotency = "idempotency-ref:" + label
    if long:
        request = request.ljust(200, "x")
        idempotency = idempotency.ljust(200, "x")
    values = dict(
        intent_ref=m.managed_ref("intent", {}),
        payload_fingerprint_ref=m.managed_ref("payload", {}),
        operation="discard_incomplete" if discard else "enroll",
        expected_state_ref=expected or absent,
        request_ref=request,
        idempotency_ref=idempotency,
        pending_attempt_ref=discard,
        desired_profile_ref=None if discard else profile.profile_ref,
        helper_ref=None if discard else profile.helper.helper_ref,
        source_provenance_ref=None
        if discard
        else profile.helper.source.source_provenance_ref,
    )
    record = m.FinanceManagedSetupIntentV1(**values)
    payload = m.managed_wire_payload(record)
    record = replace(
        record,
        payload_fingerprint_ref=m.managed_ref(
            "payload",
            {
                key: value
                for key, value in payload.items()
                if key not in ("intent_ref", "payload_fingerprint_ref")
            },
        ),
    )
    payload = m.managed_wire_payload(record)
    return replace(
        record,
        intent_ref=m.managed_ref(
            "intent",
            {key: value for key, value in payload.items() if key != "intent_ref"},
        ),
    )


def _pending(m, profile, label="first", *, long=False):
    intent = _intent(m, profile, label, long=long)
    return m.ManagedPendingAttemptV1(
        attempt_ref=m.managed_ref("attempt", m.managed_wire_payload(intent)),
        intent=intent,
        desired_profile=profile,
    )


def _receipt(m, pending, *, abandoned=False, long=False):
    own = (
        _intent(
            m,
            pending.desired_profile,
            pending.intent.request_ref.split(":", 1)[1][:32] + "-discard",
            discard=pending.attempt_ref,
            long=long,
        )
        if abandoned
        else pending.intent
    )
    refs = {
        name: "evidence-ref:" + ("a" * 187 if long else name.replace("_", "-"))
        for name in (
            "policy_revision_ref",
            "preview_ref",
            "exact_scope_ref",
            "policy_decision_ref",
            "approval_ref",
            "approval_decision_ref",
            "approval_grant_fingerprint_ref",
            "authority_lease_ref",
            "authority_decision_ref",
            "lease_issue_receipt_ref",
            "permit_ref",
            "audit_event_ref",
            "rollback_ref",
            "safe_disable_ref",
        )
    }
    return _bind(
        m,
        m.ManagedTerminalReceiptV1,
        "receipt",
        "receipt_ref",
        **refs,
        phase="abandoned" if abandoned else "committed",
        intent=own,
        original_enrollment_intent=pending.intent if abandoned else None,
        attempt_ref=pending.attempt_ref,
        after_profile_revision=0 if abandoned else 1,
        profile_ref=pending.desired_profile.profile_ref,
        helper_ref=pending.desired_profile.helper.helper_ref,
        source_provenance_ref=pending.desired_profile.helper.source.source_provenance_ref,
    )


def _state(m, *, pending=None, active=None, receipts=()):
    return _bind(
        m,
        m.ManagedSetupStateV1,
        "state",
        "state_ref",
        pending_attempt=pending,
        active_profile=active,
        terminal_receipts=receipts,
    )


def _save(m, layout, state, *, helper=None):
    layout.root.mkdir(mode=0o700, parents=True, exist_ok=True)
    layout.root.chmod(0o700)
    layout.state_file.write_bytes(m.serialize_managed_state(state))
    layout.state_file.chmod(0o600)
    if helper is not None:
        path = layout.helper_path(state.active_profile.helper.helper_sha256)
        layout.helpers_dir.mkdir(mode=0o700, exist_ok=True)
        path.parent.mkdir(mode=0o700, exist_ok=True)
        path.write_bytes(helper)
        path.chmod(0o700)


@pytest.fixture
def layout(tmp_path):
    m = _module()
    return m.FinanceManagedLayout(root=tmp_path / "managed")


@pytest.mark.parametrize("developer", [False, True])
def test_profile_roundtrip_hash_dag_and_immutable_records(layout, developer):
    m = _module()
    profile = _profile(m, layout, developer=developer)
    assert m.parse_managed_profile(_encoded(m.managed_wire_payload(profile))) == profile
    verified = m.VerifiedFinanceHelper(
        identity=profile.helper, executable_bytes=b"synthetic-native-helper"
    )
    assert "synthetic-native-helper" not in repr(verified)
    with pytest.raises(FrozenInstanceError):
        profile.profile_revision = 2
    with pytest.raises(m.ManagedProfileError):
        m.VerifiedFinanceHelper(identity=profile.helper, executable_bytes=b"different")
    material = {"proof": [1, True, None]}
    digest = hashlib.sha256(
        b"uaa:finance-managed:v1:source\0" + _encoded(material)
    ).hexdigest()
    assert (
        m.managed_ref("source", material)
        == "managed-finance-source-ref:sha256:" + digest
    )


def test_developer_manifest_exact_source_inventory_roundtrip():
    m = _module()
    sources = tuple(
        m.ManagedSourceFileDigestV1(source_ref=ref, sha256="a" * 64)
        for ref in m.MANAGED_SOURCE_FILE_REFS
    )
    manifest = _bind(
        m,
        m.DeveloperHelperBuildManifestV1,
        "build-manifest",
        "manifest_ref",
        artifact_selector_ref="artifact-selector-ref:finance/FIN-003/native-helper:arm64:v1",
        source_files=sources,
        source_fingerprint_ref=m.managed_ref(
            "source-files", [m.managed_wire_payload(item) for item in sources]
        ),
        builder_sha256="b" * 64,
        helper_sha256="c" * 64,
        helper_size_bytes=42,
        architecture="arm64",
    )
    assert (
        m.parse_helper_build_manifest(m.serialize_helper_build_manifest(manifest))
        == manifest
    )
    for invalid in (
        replace(manifest, source_files=sources[::-1]),
        replace(manifest, publisher_verified=True),
        replace(manifest, helper_size_bytes=True),
    ):
        with pytest.raises(m.ManagedProfileError):
            m.serialize_helper_build_manifest(invalid)


def test_state_history_allows_abandon_a_then_commit_b(layout):
    m = _module()
    first = _pending(m, _profile(m, layout), "first")
    second_profile = _profile(m, layout, data=b"another-helper")
    second = _pending(m, second_profile, "second")
    abandoned = _receipt(m, first, abandoned=True)
    pending = _state(m, pending=second, receipts=(abandoned,))
    assert m.parse_managed_state(m.serialize_managed_state(pending)) == pending
    state = _state(m, active=second_profile, receipts=(abandoned, _receipt(m, second)))
    assert m.parse_managed_state(m.serialize_managed_state(state)) == state
    for invalid in (
        _state(m, active=second_profile, receipts=(abandoned,)),
        _state(
            m, active=second_profile, pending=second, receipts=state.terminal_receipts
        ),
        _state(m, active=first.desired_profile, receipts=state.terminal_receipts),
        _state(m, receipts=(abandoned, abandoned)),
    ):
        with pytest.raises(m.ManagedProfileError):
            m.serialize_managed_state(invalid)


def test_history_rejects_request_and_idempotency_conflict(layout):
    m = _module()
    profile = _profile(m, layout)
    first = _pending(m, profile)
    abandoned = _receipt(m, first, abandoned=True)
    second = _pending(m, _profile(m, layout, data=b"different"))
    with pytest.raises(m.ManagedProfileError):
        m.serialize_managed_state(_state(m, pending=second, receipts=(abandoned,)))


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("profile_revision", True),
        ("synthetic_only", 1),
        ("finance_key_created", True),
        ("real_financial_data_allowed", True),
        ("schema_version", "other.v1"),
        ("profile_ref", "managed-finance-profile-ref:sha256:" + "a" * 63),
    ],
)
def test_profile_semantics_rejected_even_with_rehashed_envelope(
    layout, field_name, value
):
    m = _module()
    payload = m.managed_wire_payload(_profile(m, layout))
    payload[field_name] = value
    if field_name != "profile_ref":
        payload["profile_ref"] = m.managed_ref(
            "profile",
            {key: item for key, item in payload.items() if key != "profile_ref"},
        )
    with pytest.raises(m.ManagedProfileError):
        m.parse_managed_profile(_encoded(payload))


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":1.0}',
        b'{"x":' + b"1" * 100 + b"}",
        b"[" * 33 + b"0" + b"]" * 33,
        b"\xff",
        b"null",
        b"{}",
        b"[]",
        b"",
        b"x" * (128 * 1024 + 1),
    ],
    ids=[
        "duplicate-key",
        "nan",
        "float",
        "big-integer",
        "depth",
        "utf8",
        "null",
        "empty-object",
        "array",
        "empty",
        "oversize",
    ],
)
def test_untrusted_json_bounds_and_grammar(raw):
    m = _module()
    with pytest.raises(m.ManagedProfileError, match="^FIN003_MANAGED_"):
        m.parse_managed_state(raw)


def test_optional_fields_must_be_explicit_and_no_extra_fields(layout):
    m = _module()
    intent = _pending(m, _profile(m, layout)).intent
    payload = m.managed_wire_payload(intent)
    assert m.parse_setup_intent(_encoded(payload)) == intent
    del payload["pending_attempt_ref"]
    with pytest.raises(m.ManagedProfileError):
        m.parse_setup_intent(_encoded(payload))
    payload = {**m.managed_wire_payload(intent), "unexpected": None}
    with pytest.raises(m.ManagedProfileError):
        m.parse_setup_intent(_encoded(payload))


def test_ref_bounds_and_prospective_terminal_capacity(layout, monkeypatch):
    m = _module()
    profile = _profile(m, layout, developer=True)
    history = tuple(
        _receipt(
            m,
            _pending(m, profile, f"old-{index}", long=True),
            abandoned=True,
            long=True,
        )
        for index in range(15)
    )
    pending = _pending(m, profile, "new", long=True)
    state = _state(m, pending=pending, receipts=history)
    raw = m.serialize_managed_state(state)
    assert len(raw) < 128 * 1024
    completed = _state(
        m, active=profile, receipts=(*history, _receipt(m, pending, long=True))
    )
    assert len(m.serialize_managed_state(completed)) < 128 * 1024
    capacity = m._pending_capacity(m.managed_wire_payload(state))
    assert len(raw) < capacity < 128 * 1024
    monkeypatch.setattr(m, "MANAGED_STATE_MAX_BYTES", capacity)
    assert m.serialize_managed_state(state) == raw
    monkeypatch.setattr(m, "MANAGED_STATE_MAX_BYTES", capacity - 1)
    with pytest.raises(m.ManagedProfileError, match="CAPACITY_EXCEEDED"):
        m.serialize_managed_state(state)
    monkeypatch.setattr(m, "MANAGED_STATE_MAX_BYTES", 128 * 1024)
    terminal = _receipt(m, pending, abandoned=True, long=True)
    full = _state(m, receipts=(*history, terminal))
    assert m.parse_managed_state(m.serialize_managed_state(full)) == full
    with pytest.raises(m.ManagedProfileError):
        m.serialize_managed_state(
            _state(
                m, pending=_pending(m, profile, "next"), receipts=full.terminal_receipts
            )
        )
    for bad in (
        "evidence-ref:" + "a" * 188,
        "evidence-ref:" + "é" * 10,
        "evidence-ref:raw\\content",
        "evidence-ref:/home/private",
        "evidence-ref:password",
    ):
        invalid = replace(terminal, policy_revision_ref=bad)
        with pytest.raises(m.ManagedProfileError):
            m.validate_managed_record(invalid)


@pytest.mark.parametrize(
    "name", ["policy_revision_ref", "approval_ref", "authority_lease_ref"]
)
def test_required_receipt_refs_cannot_be_null_even_when_rehashed(layout, name):
    m = _module()
    receipt = _receipt(m, _pending(m, _profile(m, layout)))
    payload = m.managed_wire_payload(receipt)
    payload[name] = None
    payload.pop("receipt_ref")
    invalid = replace(
        receipt, **{name: None, "receipt_ref": m.managed_ref("receipt", payload)}
    )
    with pytest.raises(m.ManagedProfileError):
        m.validate_managed_record(invalid)


def test_missing_unconfigured_pending_and_active_read_results(layout):
    m = _module()
    missing = m.read_managed_state(layout)
    assert (
        missing.status == "missing" and missing.state_ref and not layout.root.exists()
    )
    profile = _profile(m, layout)
    pending = _pending(m, profile)
    _save(m, layout, _state(m, pending=pending))
    result = m.read_managed_profile(layout)
    assert result.status == "incomplete" and result.state.pending_attempt == pending
    assert not layout.staging_dir.exists() and not layout.authority_dir.exists()
    _save(m, layout, _state(m, receipts=(_receipt(m, pending, abandoned=True),)))
    result = m.read_managed_state(layout)
    assert result.status == "unconfigured" and result.state_ref != missing.state_ref
    second = _pending(m, profile, "second")
    active = _state(
        m,
        active=profile,
        receipts=(*result.state.terminal_receipts, _receipt(m, second)),
    )
    _save(m, layout, active)
    assert m.read_managed_state(layout).status == "present"
    invalid = m.read_managed_profile(layout)
    assert (
        invalid.status == "invalid"
        and invalid.state is None
        and invalid.profile is None
    )
    _save(m, layout, active, helper=b"synthetic-native-helper")
    assert m.read_managed_profile(layout).profile == profile
    assert not layout.repository_dir.exists() and not layout.authority_dir.exists()


@pytest.mark.parametrize(
    "problem",
    [
        "invalid-json",
        "directory-state",
        "state-link",
        "root-link",
        "state-permissions",
        "root-permissions",
        "helper-no-execute",
        "helper-digest",
        "helper-hardlink",
        "helper-link",
        "helper-size",
        "helper-directory",
        "helper-parent-file",
    ],
)
def test_unsafe_state_or_helper_is_not_absence(layout, tmp_path, problem):
    m = _module()
    profile = _profile(m, layout)
    pending = _pending(m, profile)
    _save(
        m,
        layout,
        _state(m, active=profile, receipts=(_receipt(m, pending),)),
        helper=b"synthetic-native-helper",
    )
    helper = layout.helper_path(profile.helper.helper_sha256)
    if problem == "invalid-json":
        layout.state_file.write_bytes(b"{broken")
    elif problem == "directory-state":
        layout.state_file.unlink()
        layout.state_file.mkdir(mode=0o700)
    elif problem == "state-link":
        layout.state_file.unlink()
        layout.state_file.symlink_to("missing")
    elif problem == "root-link":
        target = tmp_path / "moved"
        layout.root.rename(target)
        layout.root.symlink_to(target, target_is_directory=True)
    elif problem == "state-permissions":
        layout.state_file.chmod(0o644)
    elif problem == "root-permissions":
        layout.root.chmod(0o755)
    elif problem == "helper-no-execute":
        helper.chmod(0o600)
    elif problem == "helper-digest":
        helper.write_bytes(b"x" * helper.stat().st_size)
    elif problem == "helper-hardlink":
        os.link(helper, helper.parent / "another")
    elif problem == "helper-link":
        helper.unlink()
        helper.symlink_to("missing")
    elif problem == "helper-size":
        helper.write_bytes(b"short")
    elif problem == "helper-directory":
        helper.unlink()
        helper.mkdir(mode=0o700)
    else:
        helper.unlink()
        helper.parent.rmdir()
        helper.parent.write_bytes(b"not a directory")
        helper.parent.chmod(0o600)
    result = m.read_managed_profile(layout)
    assert (
        result.status == "invalid" and result.state_ref is None and result.state is None
    )


def test_missing_nested_parent_and_repository_identity_without_book_traversal(tmp_path):
    m = _module()
    nested = m.FinanceManagedLayout(root=tmp_path / "not-created" / "managed")
    assert m.read_managed_state(nested).status == "missing"
    assert not nested.root.parent.exists()
    layout = m.FinanceManagedLayout(root=tmp_path / "managed")
    before = m.managed_repository_ref(layout)
    layout.root.mkdir(mode=0o700)
    layout.repository_dir.symlink_to(tmp_path / "different")
    assert m.managed_repository_ref(layout) == before
    from ultimate_ai_agent.core.finance.service import finance_repository_ref

    layout.repository_dir.unlink()
    assert before == finance_repository_ref(layout.repository_dir)


def test_permission_uncertainty_and_descriptor_capability_fail_closed(
    layout, monkeypatch
):
    m = _module()
    real_lstat = m.os.lstat

    def denied(path, *args, **kwargs):
        if Path(path) == layout.root.parent:
            raise PermissionError("private details must not escape")
        return real_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(m.os, "lstat", denied)
        result = m.read_managed_state(layout)
        assert result.status == "invalid" and "private details" not in repr(result)
    with monkeypatch.context() as patch:
        patch.setattr(m.os, "O_NOFOLLOW", 0)
        assert (
            m.read_managed_state(layout).error_code
            == "FIN003_MANAGED_PLATFORM_UNSUPPORTED"
        )


def test_descriptor_acl_failure_is_invoked_and_redacted(layout, monkeypatch):
    m = _module()
    pending = _pending(m, _profile(m, layout))
    _save(m, layout, _state(m, pending=pending))
    calls = []

    def denied(fd, *, purpose):
        calls.append((stat.S_IFMT(os.fstat(fd).st_mode), purpose))
        raise ValueError("unsafe ACL details")

    monkeypatch.setattr(m._private_security(), "require_no_extended_acl_fd", denied)
    result = m.read_managed_state(layout)
    assert (
        calls
        and result.status == "invalid"
        and "unsafe ACL details" not in repr(result)
    )


@pytest.mark.parametrize("location", ["ancestor", "managed-root"])
def test_unrelated_directory_activity_preserves_retained_path_identity(
    layout, monkeypatch, location
):
    m = _module()
    pending = _pending(m, _profile(m, layout))
    _save(m, layout, _state(m, pending=pending))
    original = m._private_security().require_no_extended_acl_fd
    changed = False

    def check(fd, *, purpose):
        nonlocal changed
        original(fd, purpose=purpose)
        if not changed and stat.S_ISREG(os.fstat(fd).st_mode):
            changed = True
            parent = layout.root.parent if location == "ancestor" else layout.root
            (parent / "unrelated-private-directory").mkdir(mode=0o700)

    monkeypatch.setattr(m._private_security(), "require_no_extended_acl_fd", check)
    result = m.read_managed_state(layout)
    assert changed and result.status == "incomplete"
    assert result.state.pending_attempt == pending


def test_state_leaf_replacement_between_stat_and_open_rejected(layout, monkeypatch):
    m = _module()
    _save(m, layout, _state(m, pending=_pending(m, _profile(m, layout))))
    original_open = m.os.open
    original_support = m._descriptor_support

    def opening(path, flags, *args, **kwargs):
        if path == "state-v1.json":
            layout.state_file.rename(layout.root / "retained.json")
            layout.state_file.symlink_to("retained.json")
        return original_open(path, flags, *args, **kwargs)

    original_support()
    monkeypatch.setattr(m, "_descriptor_support", lambda: None)
    monkeypatch.setattr(m.os, "open", opening)
    assert m.read_managed_state(layout).status == "invalid"


def test_state_swap_while_reading_helper_invalidates_whole_observation(
    layout, monkeypatch
):
    m = _module()
    profile = _profile(m, layout)
    _save(
        m,
        layout,
        _state(m, active=profile, receipts=(_receipt(m, _pending(m, profile)),)),
        helper=b"synthetic-native-helper",
    )
    original_leaf = m._ManagedReadScope.leaf

    def leaf(scope, parent, name, **kwargs):
        raw = original_leaf(scope, parent, name, **kwargs)
        if name == "helper":
            replacement = layout.root / "replacement.json"
            replacement.write_bytes(layout.state_file.read_bytes())
            replacement.chmod(0o600)
            replacement.replace(layout.state_file)
        return raw

    monkeypatch.setattr(m._ManagedReadScope, "leaf", leaf)
    result = m.read_managed_profile(layout)
    assert result.status == "invalid" and result.profile is None


def test_ancestor_rebinding_and_disappearing_absence_are_not_accepted(
    layout, monkeypatch
):
    m = _module()
    original_recheck = m._ManagedReadScope.recheck

    def recheck(scope):
        layout.root.mkdir(mode=0o700)
        original_recheck(scope)

    monkeypatch.setattr(m._ManagedReadScope, "recheck", recheck)
    assert m.read_managed_state(layout).status == "invalid"


def test_user_owned_ancestor_symlink_rejected(tmp_path):
    m = _module()
    actual = tmp_path / "actual"
    actual.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    assert (
        m.read_managed_state(m.FinanceManagedLayout(root=alias / "managed")).status
        == "invalid"
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="native macOS ancestor alias")
def test_root_owned_macos_alias_uses_existing_policy(tmp_path):
    m = _module()
    canonical = str(tmp_path)
    if not canonical.startswith("/private/var/"):
        pytest.skip("temporary directory is not under the fixed macOS var alias")
    alias = Path(canonical.removeprefix("/private")) / "managed"
    assert m.read_managed_state(m.FinanceManagedLayout(root=alias)).status == "missing"


@pytest.mark.skipif(sys.platform != "darwin", reason="native Darwin descriptor ACL")
def test_native_extended_acl_on_private_state_is_rejected(layout):
    import subprocess

    m = _module()
    _save(m, layout, _state(m, pending=_pending(m, _profile(m, layout))))
    try:
        subprocess.run(
            ["/bin/chmod", "+a", "everyone allow read", str(layout.state_file)],
            check=True,
            capture_output=True,
        )
        assert m.read_managed_state(layout).status == "invalid"
    finally:
        subprocess.run(
            ["/bin/chmod", "-N", str(layout.state_file)],
            check=True,
            capture_output=True,
        )


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR": ""},
        {"UAA_FINANCE_NATIVE_HELPER_PATH": "/unused"},
        {"UAA_FINANCE_NATIVE_HELPER_SHA256": "a" * 64},
        {
            "UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR": "/unused",
            "UAA_FINANCE_NATIVE_HELPER_PATH": "/helper",
            "UAA_FINANCE_NATIVE_HELPER_SHA256": "A" * 64,
        },
    ],
)
def test_explicit_precedence_preserves_invalid_raw_values(
    layout, monkeypatch, settings
):
    m = _module()
    if not settings:
        result = m.resolve_finance_configuration(
            {"UAA_FINANCE_SAFE_DISABLE": ""}, layout
        )
        assert result.mode == "absent" and result.effective_environment == (
            ("UAA_FINANCE_SAFE_DISABLE", ""),
        )
        return

    def forbidden():
        raise AssertionError("explicit discovery must not look up the account")

    monkeypatch.setattr(m, "default_finance_managed_layout", forbidden)
    values = {
        **settings,
        "UAA_FINANCE_SAFE_DISABLE": "",
        "UAA_FINANCE_STARTUP_MODE": "managed",
    }
    result = m.resolve_finance_configuration(values)
    assert result.mode == "invalid"
    assert dict(result.effective_environment) == {
        key: value for key, value in values.items() if key != "UAA_FINANCE_STARTUP_MODE"
    }
    assert not layout.root.exists()


def test_valid_explicit_and_managed_resolution_have_exact_order_and_private_repr(
    layout,
):
    m = _module()
    values = dict(
        zip(m.FINANCE_EXPLICIT_ENV_NAMES, ("/unused-book", "/unused-helper", "a" * 64))
    )
    explicit = m.resolve_finance_configuration({**values, "UNRELATED": "ignored"})
    assert explicit.mode == "explicit" and explicit.effective_environment == tuple(
        values.items()
    )
    assert "unused" not in repr(explicit)
    bad = {**values, m.FINANCE_WORKSPACE_REPOSITORY_ENV: "/bad\0path"}
    assert m.resolve_finance_configuration(bad).mode == "invalid"
    profile = _profile(m, layout)
    _save(
        m,
        layout,
        _state(m, active=profile, receipts=(_receipt(m, _pending(m, profile)),)),
        helper=b"synthetic-native-helper",
    )
    managed = m.resolve_finance_configuration(
        {m.FINANCE_WORKSPACE_DISABLE_ENV: "unexpected"}, layout
    )
    assert managed.mode == "managed" and managed.profile_ref == profile.profile_ref
    assert (
        tuple(name for name, _value in managed.effective_environment)
        == m.FINANCE_CONFIGURATION_ENV_NAMES
    )
    assert (
        dict(managed.effective_environment)[m.FINANCE_WORKSPACE_DISABLE_ENV]
        == "unexpected"
    )
    assert str(layout.root) not in repr(managed)


def test_directory_and_helper_ownership_omit_rename_timestamps(layout):
    m = _module()
    pending = _pending(m, _profile(m, layout))
    staging = layout.staging_attempt_dir(pending.attempt_ref)
    staging.mkdir(mode=0o700, parents=True)
    before = m.managed_directory_ownership_ref(
        staging.stat(), attempt_ref=pending.attempt_ref
    )
    helper = staging / "helper"
    helper.write_bytes(b"synthetic-native-helper")
    helper.chmod(0o700)
    assert (
        m.managed_directory_ownership_ref(
            staging.stat(), attempt_ref=pending.attempt_ref
        )
        == before
    )
    helper_ref = m.managed_helper_ownership_ref(
        helper.stat(),
        attempt_ref=pending.attempt_ref,
        helper_sha256=pending.desired_profile.helper.helper_sha256,
    )
    moved = staging / "moved"
    helper.rename(moved)
    assert (
        m.managed_helper_ownership_ref(
            moved.stat(),
            attempt_ref=pending.attempt_ref,
            helper_sha256=pending.desired_profile.helper.helper_sha256,
        )
        == helper_ref
    )


def test_plain_python_import_has_no_finance_graph_or_host_lookup():
    import subprocess

    root = Path(__file__).resolve().parents[1]
    script = """
import sys
sys.path.insert(0, sys.argv[1])
def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'ctypes.dlopen')):
        raise AssertionError('host operation during pure import')
sys.addaudithook(audit)
import ultimate_ai_agent.core.finance_managed_profile as profile
assert 'pydantic' not in sys.modules
assert 'ultimate_ai_agent.core.finance' not in sys.modules
assert 'pwd' not in sys.modules
assert profile.resolve_finance_configuration({profile.FINANCE_WORKSPACE_HELPER_ENV: ''}).mode == 'invalid'
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", script, str(root / "src")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, "isolated stdlib-only profile import failed"
