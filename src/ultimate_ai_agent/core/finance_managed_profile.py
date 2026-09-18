"""Closed FIN003 managed-profile wire codec and read-only startup discovery.

Hashes establish consistency, never authority. This module is deliberately
stdlib-only apart from the existing descriptor metadata/ACL policy helpers.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Literal

MANAGED_LAYOUT_REF = "layout-ref:finance/FIN-003/managed-v1"
MANAGED_REPOSITORY_SLOT_REF = "slot-ref:finance/FIN-003/synthetic-book-v1"
MANAGED_HELPER_VERSION_REF = "helper-version-ref:matrix-protected-cache:v1"
MANAGED_HELPER_NAME = "uaa-matrix-protected-cache-helper"
MANAGED_BUILD_RECIPE_REF = "build-recipe-ref:finance/FIN-003/native-helper:v1"
MANAGED_STATE_MAX_BYTES = 128 * 1024
MANAGED_BUILD_MANIFEST_MAX_BYTES = 16 * 1024
MANAGED_HELPER_MAX_BYTES = 32 * 1024 * 1024
MANAGED_MAX_TERMINAL_RECEIPTS = 16
MANAGED_JSON_MAX_DEPTH = 32
MANAGED_REF_MAX_ASCII_BYTES = 200
MANAGED_PROFILE_REVISION = 1
MANAGED_BUILDER_SOURCE_REF = "repo-ref:scripts/macos/build_finance_helper.py"
MANAGED_SOURCE_FILE_REFS = (
    "repo-ref:tools/macos/matrix-protected-cache-helper/Package.swift",
    "repo-ref:tools/macos/matrix-protected-cache-helper/Sources/"
    "UAAMatrixProtectedCacheHelper/main.swift",
)
FINANCE_WORKSPACE_REPOSITORY_ENV = "UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR"
FINANCE_WORKSPACE_HELPER_ENV = "UAA_FINANCE_NATIVE_HELPER_PATH"
FINANCE_WORKSPACE_HELPER_DIGEST_ENV = "UAA_FINANCE_NATIVE_HELPER_SHA256"
FINANCE_WORKSPACE_DISABLE_ENV = "UAA_FINANCE_SAFE_DISABLE"
FINANCE_EXPLICIT_ENV_NAMES = (
    FINANCE_WORKSPACE_REPOSITORY_ENV,
    FINANCE_WORKSPACE_HELPER_ENV,
    FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
)
FINANCE_CONFIGURATION_ENV_NAMES = (
    *FINANCE_EXPLICIT_ENV_NAMES,
    FINANCE_WORKSPACE_DISABLE_ENV,
)

ManagedRefKind = Literal[
    "source",
    "helper",
    "profile",
    "payload",
    "intent",
    "attempt",
    "receipt",
    "state",
    "absent-state",
    "staging-directory",
    "staged-helper",
    "build-manifest",
    "source-files",
    "builder",
]
_REF_KINDS = (
    "source",
    "helper",
    "profile",
    "payload",
    "intent",
    "attempt",
    "receipt",
    "state",
    "absent-state",
    "staging-directory",
    "staged-helper",
    "build-manifest",
    "source-files",
    "builder",
)
_HEX = re.compile(r"[0-9a-f]{64}")
_SAFE_REF = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*")
_TRANSPORT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,199}")
_UNSAFE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|"
    r"secret|token|client[_-]?secret|-----BEGIN)"
)
_RAW_PATH = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")
ReadStatus = Literal["missing", "unconfigured", "present", "incomplete", "invalid"]


class ManagedProfileError(ValueError):
    """A content-free finite error; never retain a filesystem exception."""

    def __init__(self, code: str = "FIN003_MANAGED_STATE_INVALID") -> None:
        allowed = {
            "FIN003_MANAGED_STATE_INVALID",
            "FIN003_MANAGED_CAPACITY_EXCEEDED",
            "FIN003_MANAGED_PATH_INVALID",
            "FIN003_MANAGED_PLATFORM_UNSUPPORTED",
            "FIN003_MANAGED_HELPER_INVALID",
            "FIN003_MANAGED_CONFIGURATION_INVALID",
            "FIN003_MANAGED_SETUP_INCOMPLETE",
        }
        self.code = code if code in allowed else "FIN003_MANAGED_STATE_INVALID"
        super().__init__(self.code)


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceManagedLayout:
    root: Path = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path) or not self.root.is_absolute():
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        if (
            ".." in self.root.parts
            or "\0" in str(self.root)
            or self.root == self.root.parent
        ):
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")

    @property
    def state_file(self) -> Path:
        return self.root / "state-v1.json"

    @property
    def lock_file(self) -> Path:
        return self.root / ".setup-v1.lock"

    @property
    def staging_dir(self) -> Path:
        return self.root / "staging"

    @property
    def helpers_dir(self) -> Path:
        return self.root / "helpers"

    @property
    def authority_dir(self) -> Path:
        return self.root / "authority"

    @property
    def repository_dir(self) -> Path:
        return self.root / "book"

    def staging_attempt_dir(self, attempt_ref: str) -> Path:
        _hash_ref_shape(attempt_ref, "attempt")
        return self.staging_dir / attempt_ref.rsplit(":", 1)[1]

    def staged_helper_path(self, attempt_ref: str) -> Path:
        return self.staging_attempt_dir(attempt_ref) / "helper"

    def helper_path(self, helper_sha256: str) -> Path:
        _hex(helper_sha256)
        return self.helpers_dir / helper_sha256 / "helper"


@dataclass(frozen=True, slots=True, kw_only=True)
class InstalledBundleSourceV1:
    source_provenance_ref: str
    bundle_ref: str
    bundle_inventory_ref: str
    source_commit_ref: str
    source_version_ref: str
    kind: Literal["verified_installed_bundle"] = "verified_installed_bundle"
    verification: Literal["fresh-app-signature-and-exact-helper-bytes"] = (
        "fresh-app-signature-and-exact-helper-bytes"
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DeveloperBuildSourceV1:
    source_provenance_ref: str
    build_manifest_ref: str
    source_fingerprint_ref: str
    builder_fingerprint_ref: str
    artifact_selector_ref: str
    kind: Literal["verified_developer_artifact"] = "verified_developer_artifact"
    build_recipe_ref: str = MANAGED_BUILD_RECIPE_REF
    verification: Literal["current-source-and-build-manifest-match"] = (
        "current-source-and-build-manifest-match"
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceManagedHelperIdentityV1:
    helper_ref: str
    helper_fingerprint_ref: str
    helper_size_bytes: int
    architecture: Literal["arm64", "x86_64"]
    source: InstalledBundleSourceV1 | DeveloperBuildSourceV1
    signing_kind: Literal["ad-hoc", "developer-id"]
    schema_version: str = "uaa-finance-managed-helper.v1"
    helper_version_ref: str = MANAGED_HELPER_VERSION_REF
    publisher_verified: Literal[False] = False
    source_attestation_verified: Literal[False] = False

    @property
    def helper_sha256(self) -> str:
        return self.helper_fingerprint_ref.rsplit(":", 1)[1]


@dataclass(frozen=True, slots=True, kw_only=True)
class VerifiedFinanceHelper:
    identity: FinanceManagedHelperIdentityV1
    executable_bytes: bytes = field(repr=False)

    def __post_init__(self) -> None:
        validate_managed_record(self.identity)
        if (
            type(self.executable_bytes) is not bytes
            or len(self.executable_bytes) != self.identity.helper_size_bytes
            or hashlib.sha256(self.executable_bytes).hexdigest()
            != self.identity.helper_sha256
        ):
            raise ManagedProfileError("FIN003_MANAGED_HELPER_INVALID")


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceManagedProfileV1:
    profile_ref: str
    repository_ref: str
    helper: FinanceManagedHelperIdentityV1
    schema_version: str = "uaa-finance-managed-profile.v1"
    profile_revision: Literal[1] = 1
    layout_ref: str = MANAGED_LAYOUT_REF
    repository_slot_ref: str = MANAGED_REPOSITORY_SLOT_REF
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False
    finance_book_created: Literal[False] = False
    finance_key_created: Literal[False] = False
    keychain_item_created: Literal[False] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceManagedSetupIntentV1:
    intent_ref: str
    payload_fingerprint_ref: str
    operation: Literal["enroll", "discard_incomplete"]
    expected_state_ref: str
    request_ref: str
    idempotency_ref: str
    schema_version: str = "uaa-finance-managed-setup-intent.v1"
    layout_ref: str = MANAGED_LAYOUT_REF
    expected_profile_revision: Literal[0] = 0
    pending_attempt_ref: str | None = None
    desired_profile_ref: str | None = None
    helper_ref: str | None = None
    source_provenance_ref: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedPendingAttemptV1:
    attempt_ref: str
    intent: FinanceManagedSetupIntentV1
    desired_profile: FinanceManagedProfileV1
    schema_version: str = "uaa-finance-managed-setup-pending.v1"
    staging_directory_identity_ref: str | None = None
    staged_helper_identity_ref: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedTerminalReceiptV1:
    receipt_ref: str
    phase: Literal["committed", "abandoned"]
    intent: FinanceManagedSetupIntentV1
    attempt_ref: str
    after_profile_revision: Literal[0, 1]
    profile_ref: str
    helper_ref: str
    source_provenance_ref: str
    policy_revision_ref: str
    preview_ref: str
    exact_scope_ref: str
    policy_decision_ref: str
    approval_ref: str
    approval_decision_ref: str
    approval_grant_fingerprint_ref: str
    authority_lease_ref: str
    authority_decision_ref: str
    lease_issue_receipt_ref: str
    permit_ref: str
    audit_event_ref: str
    rollback_ref: str
    safe_disable_ref: str
    schema_version: str = "uaa-finance-managed-setup-receipt.v1"
    original_enrollment_intent: FinanceManagedSetupIntentV1 | None = None
    before_profile_revision: Literal[0] = 0
    finance_book_created: Literal[False] = False
    finance_key_created: Literal[False] = False
    keychain_item_created: Literal[False] = False
    real_financial_data_allowed: Literal[False] = False
    publisher_verified: Literal[False] = False
    source_attestation_verified: Literal[False] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedSetupStateV1:
    state_ref: str
    schema_version: str = "uaa-finance-managed-setup-state.v1"
    active_profile: FinanceManagedProfileV1 | None = None
    pending_attempt: ManagedPendingAttemptV1 | None = None
    terminal_receipts: tuple[ManagedTerminalReceiptV1, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedSourceFileDigestV1:
    source_ref: str
    sha256: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DeveloperHelperBuildManifestV1:
    manifest_ref: str
    artifact_selector_ref: str
    source_files: tuple[ManagedSourceFileDigestV1, ...]
    source_fingerprint_ref: str
    builder_sha256: str
    helper_sha256: str
    helper_size_bytes: int
    architecture: Literal["arm64", "x86_64"]
    schema_version: str = "uaa-finance-helper-build-manifest.v1"
    build_recipe_ref: str = MANAGED_BUILD_RECIPE_REF
    builder_source_ref: str = MANAGED_BUILDER_SOURCE_REF
    helper_version_ref: str = MANAGED_HELPER_VERSION_REF
    signing_kind: Literal["ad-hoc"] = "ad-hoc"
    publisher_verified: Literal[False] = False
    source_attestation_verified: Literal[False] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class StateReadResult:
    status: ReadStatus
    state_ref: str | None = None
    state: ManagedSetupStateV1 | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ProfileReadResult:
    status: ReadStatus
    state_ref: str | None = None
    state: ManagedSetupStateV1 | None = None
    profile: FinanceManagedProfileV1 | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceConfigurationResolution:
    mode: Literal["explicit", "managed", "absent", "invalid"]
    effective_environment: tuple[tuple[str, str], ...] = field(repr=False)
    repository_dir: Path | None = field(default=None, repr=False)
    helper_path: Path | None = field(default=None, repr=False)
    helper_sha256: str | None = None
    profile_ref: str | None = None
    state_ref: str | None = None
    error_code: str | None = None


ManagedWireRecord = (
    InstalledBundleSourceV1
    | DeveloperBuildSourceV1
    | FinanceManagedHelperIdentityV1
    | FinanceManagedProfileV1
    | FinanceManagedSetupIntentV1
    | ManagedPendingAttemptV1
    | ManagedTerminalReceiptV1
    | ManagedSetupStateV1
    | ManagedSourceFileDigestV1
    | DeveloperHelperBuildManifestV1
)
_WIRE_TYPES = (
    InstalledBundleSourceV1,
    DeveloperBuildSourceV1,
    FinanceManagedHelperIdentityV1,
    FinanceManagedProfileV1,
    FinanceManagedSetupIntentV1,
    ManagedPendingAttemptV1,
    ManagedTerminalReceiptV1,
    ManagedSetupStateV1,
    ManagedSourceFileDigestV1,
    DeveloperHelperBuildManifestV1,
)


def _require(condition: bool) -> None:
    if not condition:
        raise ManagedProfileError()


def _hex(value: object) -> None:
    _require(type(value) is str and _HEX.fullmatch(value) is not None)


def _ref(value: object) -> None:
    _require(
        type(value) is str
        and len(value) <= MANAGED_REF_MAX_ASCII_BYTES
        and value.isascii()
        and _SAFE_REF.fullmatch(value) is not None
        and _UNSAFE.search(value) is None
        and _RAW_PATH.search(value) is None
    )


def _hash_ref_shape(value: object, kind: str) -> None:
    _digest_ref(value, f"managed-finance-{kind}-ref:sha256:")


def _digest_ref(value: object, prefix: str) -> None:
    _require(type(value) is str and value.startswith(prefix))
    _hex(value[len(prefix) :])


def _literal(value: object, expected: object) -> None:
    _require(type(value) is type(expected) and value == expected)


def _integer(value: object, low: int, high: int) -> None:
    _require(type(value) is int and low <= value <= high)


def _plain(value: object, depth: int = 0) -> object:
    _require(depth <= MANAGED_JSON_MAX_DEPTH)
    if value is None or type(value) in (str, bool, int):
        if type(value) is int:
            _require(abs(value) < 2**128)
        return value
    if type(value) in (list, tuple):
        return [_plain(item, depth + 1) for item in value]
    if type(value) is dict:
        _require(all(type(key) is str for key in value))
        return {key: _plain(item, depth + 1) for key, item in value.items()}
    raise ManagedProfileError()


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            _plain(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ManagedProfileError() from None


def managed_ref(kind: ManagedRefKind, payload: object) -> str:
    _require(type(kind) is str and kind in _REF_KINDS)
    encoded = _canonical(payload)
    _require(len(encoded) <= MANAGED_STATE_MAX_BYTES)
    digest = hashlib.sha256(
        b"uaa:finance-managed:v1:" + kind.encode("ascii") + b"\0" + encoded
    ).hexdigest()
    return f"managed-finance-{kind}-ref:sha256:{digest}"


def managed_wire_payload(record: ManagedWireRecord) -> dict[str, object]:
    """Map only the finite wire types; includes every null and literal field."""
    _require(type(record) in _WIRE_TYPES)
    result: dict[str, object] = {}
    for item in fields(record):
        value = getattr(record, item.name)
        if type(value) in _WIRE_TYPES:
            result[item.name] = managed_wire_payload(value)
        elif type(value) is tuple:
            result[item.name] = [managed_wire_payload(nested) for nested in value]
        else:
            _require(value is None or type(value) in (str, int, bool))
            result[item.name] = value
    return result


def _bound_hash(
    data: dict[str, object], name: str, kind: str, *, excluded: tuple[str, ...] = ()
) -> None:
    _hash_ref_shape(data[name], kind)
    material = {
        key: value for key, value in data.items() if key not in (name, *excluded)
    }
    _require(data[name] == managed_ref(kind, material))


def _selector(architecture: object) -> str:
    _require(type(architecture) is str and architecture in ("arm64", "x86_64"))
    return f"artifact-selector-ref:finance/FIN-003/native-helper:{architecture}:v1"


def _source(data: object) -> InstalledBundleSourceV1 | DeveloperBuildSourceV1:
    _require(type(data) is dict)
    kind = data.get("kind")
    if kind == "verified_installed_bundle":
        return _decode(InstalledBundleSourceV1, data)
    if kind == "verified_developer_artifact":
        return _decode(DeveloperBuildSourceV1, data)
    raise ManagedProfileError()


def _decode(record_type: type, payload: object):
    _require(record_type in _WIRE_TYPES and type(payload) is dict)
    _require(set(payload) == {item.name for item in fields(record_type)})
    data = dict(payload)
    nullable_refs = {
        FinanceManagedSetupIntentV1: (
            "pending_attempt_ref",
            "desired_profile_ref",
            "helper_ref",
            "source_provenance_ref",
        ),
        ManagedPendingAttemptV1: (
            "staging_directory_identity_ref",
            "staged_helper_identity_ref",
        ),
    }.get(record_type, ())
    # Ref syntax is checked even for fields whose exact hash is also checked.
    for name, value in data.items():
        if name.endswith("_ref"):
            if value is None:
                _require(name in nullable_refs)
                continue
            if name in ("request_ref", "idempotency_ref"):
                _require(
                    type(value) is str
                    and _TRANSPORT.fullmatch(value) is not None
                    and _UNSAFE.search(value) is None
                )
                if name == "request_ref":
                    _require(":" in value)
            else:
                _ref(value)
    if record_type is InstalledBundleSourceV1:
        _literal(data["kind"], "verified_installed_bundle")
        _literal(data["verification"], "fresh-app-signature-and-exact-helper-bytes")
        for key, prefix in (
            ("bundle_ref", "macos-bundle-ref:sha256:"),
            ("bundle_inventory_ref", "bundle-inventory-ref:sha256:"),
            ("source_version_ref", "macos-version-ref:sha256:"),
        ):
            _digest_ref(data[key], prefix)
        _require(
            re.fullmatch(r"git-commit:[0-9a-f]{40}", data["source_commit_ref"])
            is not None
        )
        _bound_hash(data, "source_provenance_ref", "source")
    elif record_type is DeveloperBuildSourceV1:
        _literal(data["kind"], "verified_developer_artifact")
        _literal(data["verification"], "current-source-and-build-manifest-match")
        _literal(data["build_recipe_ref"], MANAGED_BUILD_RECIPE_REF)
        for key, kind in (
            ("build_manifest_ref", "build-manifest"),
            ("source_fingerprint_ref", "source-files"),
            ("builder_fingerprint_ref", "builder"),
        ):
            _hash_ref_shape(data[key], kind)
        _require(
            data["artifact_selector_ref"] in (_selector("arm64"), _selector("x86_64"))
        )
        _bound_hash(data, "source_provenance_ref", "source")
    elif record_type is FinanceManagedHelperIdentityV1:
        _literal(data["schema_version"], "uaa-finance-managed-helper.v1")
        _literal(data["helper_version_ref"], MANAGED_HELPER_VERSION_REF)
        _digest_ref(data["helper_fingerprint_ref"], "helper-bytes-ref:sha256:")
        _integer(data["helper_size_bytes"], 1, MANAGED_HELPER_MAX_BYTES)
        selector = _selector(data["architecture"])
        _require(data["signing_kind"] in ("ad-hoc", "developer-id"))
        for name in ("publisher_verified", "source_attestation_verified"):
            _literal(data[name], False)
        source = _source(data["source"])
        if type(source) is DeveloperBuildSourceV1:
            _literal(data["signing_kind"], "ad-hoc")
            _require(source.artifact_selector_ref == selector)
        _bound_hash(data, "helper_ref", "helper")
        data["source"] = source
    elif record_type is FinanceManagedProfileV1:
        _literal(data["schema_version"], "uaa-finance-managed-profile.v1")
        _literal(data["profile_revision"], 1)
        _literal(data["layout_ref"], MANAGED_LAYOUT_REF)
        _literal(data["repository_slot_ref"], MANAGED_REPOSITORY_SLOT_REF)
        _digest_ref(data["repository_ref"], "repository-ref:finance/FIN-001:sha256:")
        _literal(data["synthetic_only"], True)
        for name in (
            "real_financial_data_allowed",
            "finance_book_created",
            "finance_key_created",
            "keychain_item_created",
        ):
            _literal(data[name], False)
        helper = _decode(FinanceManagedHelperIdentityV1, data["helper"])
        _bound_hash(data, "profile_ref", "profile")
        data["helper"] = helper
    elif record_type is FinanceManagedSetupIntentV1:
        _literal(data["schema_version"], "uaa-finance-managed-setup-intent.v1")
        _literal(data["layout_ref"], MANAGED_LAYOUT_REF)
        _literal(data["expected_profile_revision"], 0)
        _require(
            any(
                str(data["expected_state_ref"]).startswith(
                    f"managed-finance-{kind}-ref:sha256:"
                )
                for kind in ("state", "absent-state")
            )
        )
        expected_kind = (
            "absent-state"
            if "-absent-state-" in data["expected_state_ref"]
            else "state"
        )
        _hash_ref_shape(data["expected_state_ref"], expected_kind)
        if data["operation"] == "enroll":
            _literal(data["pending_attempt_ref"], None)
            for name, kind in (
                ("desired_profile_ref", "profile"),
                ("helper_ref", "helper"),
                ("source_provenance_ref", "source"),
            ):
                _hash_ref_shape(data[name], kind)
        elif data["operation"] == "discard_incomplete":
            _hash_ref_shape(data["pending_attempt_ref"], "attempt")
            for name in ("desired_profile_ref", "helper_ref", "source_provenance_ref"):
                _literal(data[name], None)
        else:
            raise ManagedProfileError()
        _bound_hash(
            data, "payload_fingerprint_ref", "payload", excluded=("intent_ref",)
        )
        _bound_hash(data, "intent_ref", "intent")
    elif record_type is ManagedPendingAttemptV1:
        _literal(data["schema_version"], "uaa-finance-managed-setup-pending.v1")
        intent = _decode(FinanceManagedSetupIntentV1, data["intent"])
        profile = _decode(FinanceManagedProfileV1, data["desired_profile"])
        _require(intent.operation == "enroll")
        _require(data["attempt_ref"] == managed_ref("attempt", data["intent"]))
        _require(
            (
                intent.desired_profile_ref,
                intent.helper_ref,
                intent.source_provenance_ref,
            )
            == _profile_binding(profile)
        )
        for name, kind in (
            ("staging_directory_identity_ref", "staging-directory"),
            ("staged_helper_identity_ref", "staged-helper"),
        ):
            if data[name] is not None:
                _hash_ref_shape(data[name], kind)
        _require(
            data["staged_helper_identity_ref"] is None
            or data["staging_directory_identity_ref"] is not None
        )
        data.update(intent=intent, desired_profile=profile)
    elif record_type is ManagedTerminalReceiptV1:
        _literal(data["schema_version"], "uaa-finance-managed-setup-receipt.v1")
        _literal(data["before_profile_revision"], 0)
        for name in (
            "finance_book_created",
            "finance_key_created",
            "keychain_item_created",
            "real_financial_data_allowed",
            "publisher_verified",
            "source_attestation_verified",
        ):
            _literal(data[name], False)
        own = _decode(FinanceManagedSetupIntentV1, data["intent"])
        original = None
        if data["phase"] == "committed":
            _literal(data["after_profile_revision"], 1)
            _literal(data["original_enrollment_intent"], None)
            _require(own.operation == "enroll")
            enrollment = own
        elif data["phase"] == "abandoned":
            _literal(data["after_profile_revision"], 0)
            original = _decode(
                FinanceManagedSetupIntentV1, data["original_enrollment_intent"]
            )
            _require(
                own.operation == "discard_incomplete" and original.operation == "enroll"
            )
            _require(own.pending_attempt_ref == data["attempt_ref"])
            enrollment = original
        else:
            raise ManagedProfileError()
        _require(
            data["attempt_ref"]
            == managed_ref("attempt", managed_wire_payload(enrollment))
        )
        _require(
            (data["profile_ref"], data["helper_ref"], data["source_provenance_ref"])
            == (
                enrollment.desired_profile_ref,
                enrollment.helper_ref,
                enrollment.source_provenance_ref,
            )
        )
        _bound_hash(data, "receipt_ref", "receipt")
        data.update(intent=own, original_enrollment_intent=original)
    elif record_type is ManagedSetupStateV1:
        _literal(data["schema_version"], "uaa-finance-managed-setup-state.v1")
        _require(
            type(data["terminal_receipts"]) is list
            and len(data["terminal_receipts"]) <= MANAGED_MAX_TERMINAL_RECEIPTS
        )
        active = (
            None
            if data["active_profile"] is None
            else _decode(FinanceManagedProfileV1, data["active_profile"])
        )
        pending = (
            None
            if data["pending_attempt"] is None
            else _decode(ManagedPendingAttemptV1, data["pending_attempt"])
        )
        receipts = tuple(
            _decode(ManagedTerminalReceiptV1, value)
            for value in data["terminal_receipts"]
        )
        _require(not (active and pending) and bool(active or pending or receipts))
        commits = [item for item in receipts if item.phase == "committed"]
        _require(len(commits) == (1 if active else 0))
        if active:
            _require(
                (
                    commits[0].profile_ref,
                    commits[0].helper_ref,
                    commits[0].source_provenance_ref,
                )
                == _profile_binding(active)
            )
        attempts = [item.attempt_ref for item in receipts]
        if pending:
            attempts.append(pending.attempt_ref)
            _require(len(receipts) < MANAGED_MAX_TERMINAL_RECEIPTS)
        _require(len(attempts) == len(set(attempts)))
        intents = [item.intent for item in receipts]
        intents.extend(
            item.original_enrollment_intent
            for item in receipts
            if item.original_enrollment_intent is not None
        )
        if pending:
            intents.append(pending.intent)
        for name in ("request_ref", "idempotency_ref"):
            seen: dict[str, str] = {}
            for intent in intents:
                identity = getattr(intent, name)
                _require(identity not in seen or seen[identity] == intent.intent_ref)
                seen[identity] = intent.intent_ref
        _bound_hash(data, "state_ref", "state")
        if pending and _pending_capacity(data) > MANAGED_STATE_MAX_BYTES:
            raise ManagedProfileError("FIN003_MANAGED_CAPACITY_EXCEEDED")
        data.update(
            active_profile=active, pending_attempt=pending, terminal_receipts=receipts
        )
    elif record_type is ManagedSourceFileDigestV1:
        _require(data["source_ref"] in MANAGED_SOURCE_FILE_REFS)
        _hex(data["sha256"])
    elif record_type is DeveloperHelperBuildManifestV1:
        _literal(data["schema_version"], "uaa-finance-helper-build-manifest.v1")
        _literal(data["build_recipe_ref"], MANAGED_BUILD_RECIPE_REF)
        _literal(data["builder_source_ref"], MANAGED_BUILDER_SOURCE_REF)
        _literal(data["helper_version_ref"], MANAGED_HELPER_VERSION_REF)
        _literal(data["signing_kind"], "ad-hoc")
        _literal(data["publisher_verified"], False)
        _literal(data["source_attestation_verified"], False)
        _require(data["artifact_selector_ref"] == _selector(data["architecture"]))
        for name in ("builder_sha256", "helper_sha256"):
            _hex(data[name])
        _integer(data["helper_size_bytes"], 1, MANAGED_HELPER_MAX_BYTES)
        _require(type(data["source_files"]) is list)
        source_files = tuple(
            _decode(ManagedSourceFileDigestV1, value) for value in data["source_files"]
        )
        _require(
            tuple(value.source_ref for value in source_files)
            == MANAGED_SOURCE_FILE_REFS
        )
        _require(
            data["source_fingerprint_ref"]
            == managed_ref("source-files", data["source_files"])
        )
        _bound_hash(data, "manifest_ref", "build-manifest")
        data["source_files"] = source_files
    return record_type(**data)


def _profile_binding(profile: FinanceManagedProfileV1) -> tuple[str, str, str]:
    return (
        profile.profile_ref,
        profile.helper.helper_ref,
        profile.helper.source.source_provenance_ref,
    )


def _pending_capacity(data: dict[str, object]) -> int:
    """Size only: placeholders are never accepted as observations or persisted."""
    pending = data["pending_attempt"]
    profile = pending["desired_profile"]
    original = pending["intent"]

    def placeholder(kind: str) -> str:
        return f"managed-finance-{kind}-ref:sha256:" + "0" * 64

    receipt = {
        item.name: "evidence-ref:" + "a" * (MANAGED_REF_MAX_ASCII_BYTES - 13)
        for item in fields(ManagedTerminalReceiptV1)
    }
    receipt.update(
        schema_version="uaa-finance-managed-setup-receipt.v1",
        receipt_ref=placeholder("receipt"),
        phase="committed",
        intent=original,
        original_enrollment_intent=None,
        attempt_ref=pending["attempt_ref"],
        before_profile_revision=0,
        after_profile_revision=1,
        profile_ref=profile["profile_ref"],
        helper_ref=profile["helper"]["helper_ref"],
        source_provenance_ref=profile["helper"]["source"]["source_provenance_ref"],
    )
    for name in (
        "finance_book_created",
        "finance_key_created",
        "keychain_item_created",
        "real_financial_data_allowed",
        "publisher_verified",
        "source_attestation_verified",
    ):
        receipt[name] = False
    full_pending = {
        **pending,
        "staging_directory_identity_ref": placeholder("staging-directory"),
        "staged_helper_identity_ref": placeholder("staged-helper"),
    }
    committed = {
        **data,
        "pending_attempt": None,
        "active_profile": profile,
        "terminal_receipts": [*data["terminal_receipts"], receipt],
    }
    discard = {
        **original,
        "operation": "discard_incomplete",
        "expected_state_ref": placeholder("state"),
        "intent_ref": placeholder("intent"),
        "payload_fingerprint_ref": placeholder("payload"),
        "pending_attempt_ref": pending["attempt_ref"],
        "desired_profile_ref": None,
        "helper_ref": None,
        "source_provenance_ref": None,
        "request_ref": "r:" + "a" * 198,
        "idempotency_ref": "i" * 200,
    }
    abandoned_receipt = {
        **receipt,
        "phase": "abandoned",
        "intent": discard,
        "original_enrollment_intent": original,
        "after_profile_revision": 0,
    }
    abandoned = {
        **data,
        "pending_attempt": None,
        "active_profile": None,
        "terminal_receipts": [*data["terminal_receipts"], abandoned_receipt],
    }
    return max(
        len(_canonical(value))
        for value in (
            {**data, "pending_attempt": full_pending},
            committed,
            abandoned,
        )
    )


def _json(raw: bytes, maximum: int) -> object:
    _require(type(raw) is bytes and 0 < len(raw) <= maximum)
    # Bound nesting before json.loads can construct recursive containers.
    depth = 0
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            _require(depth <= MANAGED_JSON_MAX_DEPTH)
        elif byte in (93, 125):
            depth -= 1
            _require(depth >= 0)

    def pairs(values):
        result = {}
        for key, value in values:
            _require(key not in result)
            result[key] = value
        return result

    def denied(_value):
        raise ManagedProfileError()

    def integer(value):
        _require(len(value) <= 39)
        return int(value)

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=denied,
            parse_float=denied,
            parse_int=integer,
        )
    except (ValueError, UnicodeError, RecursionError, TypeError):
        raise ManagedProfileError() from None


def validate_managed_record(record: ManagedWireRecord) -> None:
    _decode(type(record), managed_wire_payload(record))


def parse_managed_state(raw: bytes) -> ManagedSetupStateV1:
    return _decode(ManagedSetupStateV1, _json(raw, MANAGED_STATE_MAX_BYTES))


def parse_managed_profile(raw: bytes) -> FinanceManagedProfileV1:
    return _decode(FinanceManagedProfileV1, _json(raw, MANAGED_STATE_MAX_BYTES))


def parse_setup_intent(raw: bytes) -> FinanceManagedSetupIntentV1:
    return _decode(FinanceManagedSetupIntentV1, _json(raw, MANAGED_STATE_MAX_BYTES))


def parse_helper_build_manifest(raw: bytes) -> DeveloperHelperBuildManifestV1:
    return _decode(
        DeveloperHelperBuildManifestV1, _json(raw, MANAGED_BUILD_MANIFEST_MAX_BYTES)
    )


def serialize_managed_state(state: ManagedSetupStateV1) -> bytes:
    _require(type(state) is ManagedSetupStateV1)
    validate_managed_record(state)
    encoded = _canonical(managed_wire_payload(state))
    if len(encoded) > MANAGED_STATE_MAX_BYTES:
        raise ManagedProfileError("FIN003_MANAGED_CAPACITY_EXCEEDED")
    return encoded


def serialize_helper_build_manifest(manifest: DeveloperHelperBuildManifestV1) -> bytes:
    _require(type(manifest) is DeveloperHelperBuildManifestV1)
    validate_managed_record(manifest)
    encoded = _canonical(managed_wire_payload(manifest))
    _require(len(encoded) <= MANAGED_BUILD_MANIFEST_MAX_BYTES)
    return encoded


def _private_security():
    # ctypes initializes a native handle on import; keep that out of pure codecs
    # and the explicit-environment startup branch.
    from ultimate_ai_agent.core import private_path_security

    return private_path_security


def _descriptor_support() -> None:
    try:
        _private_security().require_posix_private_path_support()
        for name in ("O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC", "O_NONBLOCK"):
            if not getattr(os, name, 0):
                raise ValueError
        if not all(
            callable(getattr(os, name, None)) for name in ("fstat", "read", "close")
        ):
            raise ValueError
        if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
            raise ValueError
        if os.stat not in os.supports_follow_symlinks:
            raise ValueError
    except (ValueError, AttributeError):
        raise ManagedProfileError("FIN003_MANAGED_PLATFORM_UNSUPPORTED") from None


def _ancestor_metadata(metadata: os.stat_result) -> None:
    mode = stat.S_IMODE(metadata.st_mode)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid not in (0, os.getuid())
        or (mode & 0o022 and not mode & stat.S_ISVTX)
    ):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")


def _same(initial: os.stat_result, current: os.stat_result) -> None:
    # Unrelated entry activity does not change a retained directory's identity.
    # Files and symlinks still bind size/timestamps/link count around the read.
    if stat.S_ISDIR(initial.st_mode) and stat.S_ISDIR(current.st_mode):

        def directory_identity(metadata):
            return metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid

        if directory_identity(initial) != directory_identity(current):
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        return
    if _private_security()._private_identity(
        initial
    ) != _private_security()._private_identity(current):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")


class _ManagedReadScope:
    """Retain exact layout directory/name bindings until the observation ends."""

    def __init__(self, layout: FinanceManagedLayout) -> None:
        self.layout = layout
        self.descriptors: list[int] = []
        self.bindings: list[tuple[int, str, int, os.stat_result, bool]] = []
        self.lexical: list[tuple[Path, os.stat_result]] = []
        self.missing: tuple[int, str] | None = None
        self.root_fd: int | None = None
        self.anchor: Path | None = None
        self.canonical_anchor: Path | None = None
        self.canonical_root: Path | None = None

    def __enter__(self) -> _ManagedReadScope:
        try:
            _descriptor_support()
            self._open_root()
            return self
        except BaseException:
            self._close()
            raise

    def __exit__(self, exc_type, exc, traceback) -> None:
        try:
            if exc_type is None:
                self.recheck()
        finally:
            self._close()

    def _close(self) -> None:
        for descriptor in reversed(self.descriptors):
            os.close(descriptor)
        self.descriptors.clear()

    def _open_root(self) -> None:
        anchor = self.layout.root.parent
        while True:
            try:
                os.lstat(anchor)
                break
            except FileNotFoundError:
                if anchor.parent == anchor:
                    raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID") from None
                anchor = anchor.parent
        self.anchor = anchor
        lexical = Path(anchor.anchor)
        for name in (None, *anchor.parts[1:]):
            if name is not None:
                lexical /= name
            metadata = os.lstat(lexical)
            if stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid != 0:
                    raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
            else:
                _ancestor_metadata(metadata)
            self.lexical.append((lexical, metadata))
        _private_security().require_safe_private_ancestor_chain(
            anchor, purpose="managed Finance ancestor"
        )
        canonical = anchor.resolve(strict=True)
        self.canonical_anchor = canonical
        root_descriptor = os.open(
            canonical.anchor,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        self.descriptors.append(root_descriptor)
        metadata = os.fstat(root_descriptor)
        _ancestor_metadata(metadata)
        _private_security()._require_no_extended_acl_grants_fd(
            root_descriptor, purpose="managed Finance ancestor"
        )
        self.bindings.append((root_descriptor, ".", root_descriptor, metadata, False))
        descriptor = root_descriptor
        for name in canonical.parts[1:]:
            descriptor = self.directory(descriptor, name, private=False)
        remaining = self.layout.root.relative_to(anchor).parts
        self.canonical_root = canonical.joinpath(*remaining)
        for index, name in enumerate(remaining):
            try:
                descriptor = self.directory(
                    descriptor, name, private=index == len(remaining) - 1
                )
            except FileNotFoundError:
                self.missing = (descriptor, name)
                return
        self.root_fd = descriptor

    def directory(self, parent: int, name: str, *, private: bool = True) -> int:
        initial = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(initial.st_mode):
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent,
        )
        self.descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        _same(initial, opened)
        if private:
            _private_security()._require_private_tree_metadata(
                opened, purpose="managed Finance directory"
            )
            _private_security().require_no_extended_acl_fd(
                descriptor, purpose="managed Finance directory"
            )
        else:
            _ancestor_metadata(opened)
            _private_security()._require_no_extended_acl_grants_fd(
                descriptor, purpose="managed Finance ancestor"
            )
        _same(opened, os.fstat(descriptor))
        _same(opened, os.stat(name, dir_fd=parent, follow_symlinks=False))
        self.bindings.append((parent, name, descriptor, opened, private))
        return descriptor

    def leaf(
        self,
        parent: int,
        name: str,
        *,
        maximum: int,
        exact: int | None = None,
        executable: bool = False,
    ) -> bytes:
        initial = os.stat(name, dir_fd=parent, follow_symlinks=False)
        _private_security()._require_private_regular_metadata(
            initial,
            purpose="managed Finance file",
            maximum_bytes=maximum,
            exact_bytes=exact,
        )
        if executable and not initial.st_mode & stat.S_IXUSR:
            raise ManagedProfileError("FIN003_MANAGED_HELPER_INVALID")
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent,
        )
        self.descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        _same(initial, opened)
        _private_security()._require_private_regular_metadata(
            opened,
            purpose="managed Finance file",
            maximum_bytes=maximum,
            exact_bytes=exact,
        )
        _private_security().require_no_extended_acl_fd(
            descriptor, purpose="managed Finance file"
        )
        chunks = []
        length = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, maximum + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
            if length > maximum:
                raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        _same(opened, os.fstat(descriptor))
        _same(opened, os.stat(name, dir_fd=parent, follow_symlinks=False))
        if length != opened.st_size:
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        self.bindings.append((parent, name, descriptor, opened, True))
        return b"".join(chunks)

    def recheck(self) -> None:
        for parent, name, descriptor, initial, private in self.bindings:
            _same(initial, os.fstat(descriptor))
            _same(initial, os.stat(name, dir_fd=parent, follow_symlinks=False))
            if private:
                _private_security().require_no_extended_acl_fd(
                    descriptor, purpose="managed Finance path"
                )
            else:
                _private_security()._require_no_extended_acl_grants_fd(
                    descriptor, purpose="managed Finance ancestor"
                )
            _same(initial, os.fstat(descriptor))
        if self.missing is not None:
            parent, name = self.missing
            try:
                os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        for path, metadata in self.lexical:
            _same(metadata, os.lstat(path))
        if self.anchor.resolve(strict=True) != self.canonical_anchor:
            raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
        _private_security().require_safe_private_ancestor_chain(
            self.anchor, purpose="managed Finance ancestor"
        )


def default_finance_managed_layout() -> FinanceManagedLayout:
    try:
        _descriptor_support()
        import pwd

        account_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        return FinanceManagedLayout(
            root=account_home
            / "Library"
            / "Application Support"
            / "Ultimate AI Agent"
            / "finance"
            / "managed-v1"
        )
    except (ImportError, KeyError, OSError, ValueError, TypeError):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID") from None


def _repository_ref(canonical_root: Path) -> str:
    digest = hashlib.sha256(
        _canonical({"canonical_path": str(canonical_root / "book")})
    ).hexdigest()
    return f"repository-ref:finance/FIN-001:sha256:{digest}"


def managed_repository_ref(layout: FinanceManagedLayout) -> str:
    try:
        with _ManagedReadScope(layout) as scope:
            return _repository_ref(scope.canonical_root)
    except ManagedProfileError:
        raise
    except (OSError, ValueError, TypeError, AttributeError):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID") from None


def _read_managed(
    layout: FinanceManagedLayout, *, verify_helper: bool
) -> ProfileReadResult:
    try:
        with _ManagedReadScope(layout) as scope:
            repository_ref = _repository_ref(scope.canonical_root)
            absent_ref = managed_ref(
                "absent-state",
                {
                    "layout_ref": MANAGED_LAYOUT_REF,
                    "repository_ref": repository_ref,
                },
            )
            if scope.root_fd is None:
                return ProfileReadResult(status="missing", state_ref=absent_ref)
            try:
                raw = scope.leaf(
                    scope.root_fd, "state-v1.json", maximum=MANAGED_STATE_MAX_BYTES
                )
            except FileNotFoundError:
                scope.missing = (scope.root_fd, "state-v1.json")
                return ProfileReadResult(status="missing", state_ref=absent_ref)
            state = parse_managed_state(raw)
            for profile in (
                state.active_profile,
                state.pending_attempt.desired_profile
                if state.pending_attempt
                else None,
            ):
                if profile is not None and profile.repository_ref != repository_ref:
                    raise ManagedProfileError()
            if state.pending_attempt is not None:
                return ProfileReadResult(
                    status="incomplete", state_ref=state.state_ref, state=state
                )
            profile = state.active_profile
            if profile is None:
                return ProfileReadResult(
                    status="unconfigured", state_ref=state.state_ref, state=state
                )
            if verify_helper:
                try:
                    helpers = scope.directory(scope.root_fd, "helpers")
                    slot = scope.directory(helpers, profile.helper.helper_sha256)
                    captured = scope.leaf(
                        slot,
                        "helper",
                        maximum=MANAGED_HELPER_MAX_BYTES,
                        exact=profile.helper.helper_size_bytes,
                        executable=True,
                    )
                    if (
                        hashlib.sha256(captured).hexdigest()
                        != profile.helper.helper_sha256
                    ):
                        raise ValueError
                except (OSError, ValueError):
                    raise ManagedProfileError("FIN003_MANAGED_HELPER_INVALID") from None
            return ProfileReadResult(
                status="present",
                state_ref=state.state_ref,
                state=state,
                profile=profile if verify_helper else None,
            )
    except ManagedProfileError as exc:
        return ProfileReadResult(status="invalid", error_code=exc.code)
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        return ProfileReadResult(
            status="invalid", error_code="FIN003_MANAGED_PATH_INVALID"
        )


def read_managed_state(layout: FinanceManagedLayout) -> StateReadResult:
    result = _read_managed(layout, verify_helper=False)
    return StateReadResult(
        status=result.status,
        state_ref=result.state_ref,
        state=result.state,
        error_code=result.error_code,
    )


def read_managed_profile(layout: FinanceManagedLayout) -> ProfileReadResult:
    return _read_managed(layout, verify_helper=True)


def _absolute_setting(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and "\0" not in value
        and Path(value).is_absolute()
    )


def resolve_finance_configuration(
    environ: Mapping[str, str],
    layout: FinanceManagedLayout | None = None,
) -> FinanceConfigurationResolution:
    effective = tuple(
        (name, environ[name])
        for name in FINANCE_CONFIGURATION_ENV_NAMES
        if name in environ
    )
    if any(name in environ for name in FINANCE_EXPLICIT_ENV_NAMES):
        repository = environ.get(FINANCE_WORKSPACE_REPOSITORY_ENV)
        helper = environ.get(FINANCE_WORKSPACE_HELPER_ENV)
        digest = environ.get(FINANCE_WORKSPACE_HELPER_DIGEST_ENV)
        if (
            _absolute_setting(repository)
            and _absolute_setting(helper)
            and type(digest) is str
            and _HEX.fullmatch(digest) is not None
        ):
            return FinanceConfigurationResolution(
                mode="explicit",
                effective_environment=effective,
                repository_dir=Path(repository),
                helper_path=Path(helper),
                helper_sha256=digest,
            )
        return FinanceConfigurationResolution(
            mode="invalid",
            effective_environment=effective,
            error_code="FIN003_MANAGED_CONFIGURATION_INVALID",
        )
    try:
        actual_layout = (
            layout if layout is not None else default_finance_managed_layout()
        )
        result = read_managed_profile(actual_layout)
    except ManagedProfileError as exc:
        return FinanceConfigurationResolution(
            mode="invalid", effective_environment=effective, error_code=exc.code
        )
    if result.status in ("missing", "unconfigured"):
        return FinanceConfigurationResolution(
            mode="absent", effective_environment=effective, state_ref=result.state_ref
        )
    if result.status != "present":
        return FinanceConfigurationResolution(
            mode="invalid",
            effective_environment=effective,
            state_ref=result.state_ref,
            error_code=result.error_code or "FIN003_MANAGED_SETUP_INCOMPLETE",
        )
    profile = result.profile
    values = {
        FINANCE_WORKSPACE_REPOSITORY_ENV: str(actual_layout.repository_dir),
        FINANCE_WORKSPACE_HELPER_ENV: str(
            actual_layout.helper_path(profile.helper.helper_sha256)
        ),
        FINANCE_WORKSPACE_HELPER_DIGEST_ENV: profile.helper.helper_sha256,
    }
    if FINANCE_WORKSPACE_DISABLE_ENV in environ:
        values[FINANCE_WORKSPACE_DISABLE_ENV] = environ[FINANCE_WORKSPACE_DISABLE_ENV]
    return FinanceConfigurationResolution(
        mode="managed",
        effective_environment=tuple(
            (name, values[name])
            for name in FINANCE_CONFIGURATION_ENV_NAMES
            if name in values
        ),
        repository_dir=actual_layout.repository_dir,
        helper_path=actual_layout.helper_path(profile.helper.helper_sha256),
        helper_sha256=profile.helper.helper_sha256,
        profile_ref=profile.profile_ref,
        state_ref=result.state_ref,
    )


def managed_directory_ownership_ref(
    metadata: os.stat_result, *, attempt_ref: str
) -> str:
    _hash_ref_shape(attempt_ref, "attempt")
    try:
        _private_security()._require_private_tree_metadata(
            metadata, purpose="managed Finance staging"
        )
    except (ValueError, OSError):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID") from None
    if not stat.S_ISDIR(metadata.st_mode):
        raise ManagedProfileError("FIN003_MANAGED_PATH_INVALID")
    return managed_ref(
        "staging-directory",
        {
            "attempt_ref": attempt_ref,
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "type": stat.S_IFMT(metadata.st_mode),
            "uid": metadata.st_uid,
            "mode": stat.S_IMODE(metadata.st_mode),
        },
    )


def managed_helper_ownership_ref(
    metadata: os.stat_result, *, attempt_ref: str, helper_sha256: str
) -> str:
    _hash_ref_shape(attempt_ref, "attempt")
    _hex(helper_sha256)
    try:
        _private_security()._require_private_regular_metadata(
            metadata,
            purpose="managed Finance staging",
            maximum_bytes=MANAGED_HELPER_MAX_BYTES,
            exact_bytes=None,
        )
    except (ValueError, OSError):
        raise ManagedProfileError("FIN003_MANAGED_HELPER_INVALID") from None
    if not metadata.st_mode & stat.S_IXUSR:
        raise ManagedProfileError("FIN003_MANAGED_HELPER_INVALID")
    return managed_ref(
        "staged-helper",
        {
            "attempt_ref": attempt_ref,
            "helper_sha256": helper_sha256,
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "type": stat.S_IFMT(metadata.st_mode),
            "uid": metadata.st_uid,
            "mode": stat.S_IMODE(metadata.st_mode),
            "links": metadata.st_nlink,
            "size": metadata.st_size,
        },
    )
