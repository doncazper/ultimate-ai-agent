from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime, timezone
try:
    from enum import StrEnum as _StringEnum
except ImportError:  # pragma: no cover - exercised by the Python 3.10 verifier
    from enum import Enum

    class _StringEnum(str, Enum):
        def __str__(self) -> str:
            return self.value
from pathlib import PurePosixPath
from typing import Any

SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_UNITS = 128
MAX_RECEIPTS = 256
MAX_CHANGED_PATHS = 1024
MAX_COMMAND_REFS = 512
MAX_TEST_REFS = 2048
MAX_LOCK_REFS = 64
MAX_DURATION_MS = 24 * 60 * 60 * 1000
MAX_DURATION_CLOCK_SKEW_MS = 5_000
TEST_EXECUTION_COMMAND_REFS = frozenset(
    {
        "command:frontend.check",
        "command:frontend.unit-tests",
        "command:frontend.browser-smoke",
        "command:frontend.visual-regression",
        "command:frontend.visual-regression-contract",
    }
)
TYPESCRIPT_EXECUTION_COMMAND_REFS = frozenset(
    {"command:frontend.check", "command:frontend.typecheck"}
)
V3_PLAN_ONLY_FIELDS = frozenset(
    {
        "verification_dag_fingerprint",
        "selected_unit_definition_fingerprints",
    }
)
SUPPORTED_PLAN_SCHEMA_VERSIONS = frozenset(
    {
        "uaa_ci_command_manifest.v2",
        "uaa_ci_command_manifest.v3",
        "uaa_ci_command_manifest.v4",
        "uaa_verification_plan.v1",
        "uaa_verification_plan.v2",
        "uaa_verification_plan.v3",
    }
)
V3_RECEIPT_ONLY_FIELDS = frozenset(
    {
        "dependency_lock_set_fingerprint",
        "pytest_shard_plan_fingerprint",
        "execution_identity_ref",
        "executed_command_result_bindings",
        "nonexecuted_command_result_bindings",
        "reused_command_receipt_bindings",
    }
)
V4_RECEIPT_ONLY_FIELDS = frozenset({"observed_platform_fingerprint"})
V3_RUN_ONLY_FIELDS = frozenset(
    {
        "dependency_lock_set_fingerprint",
        "platform_fingerprint",
        "verifier_definition_fingerprint",
        "test_collection_fingerprint",
        "pytest_shard_plan_fingerprint",
        "typescript_project_fingerprint",
        "required_unit_refs",
        "missing_unit_refs",
        "failed_unit_refs",
        "reason_refs",
        "observed_test_collection_bindings",
    }
)
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


class VerificationRiskTier(_StringEnum):
    TIER_0 = "tier_0"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

    @property
    def rank(self) -> int:
        return int(self.value.rsplit("_", maxsplit=1)[-1])


class VerificationUnitKind(_StringEnum):
    COMMAND = "command"
    AGGREGATE = "aggregate"
    AUDIT = "audit"


class VerificationTerminalStatus(_StringEnum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class VerificationGateStatus(_StringEnum):
    PASSED = "passed"
    DENIED = "denied"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


def _validate_ref(value: str, *, label: str) -> None:
    if not isinstance(value, str) or SAFE_REF_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a bounded safe ref")


def _validate_digest(value: str, *, label: str) -> None:
    if not isinstance(value, str) or DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _validate_digest_ref(value: str, *, prefix: str, label: str) -> None:
    _validate_ref(value, label=label)
    if not value.startswith(prefix):
        raise ValueError(f"{label} must be a content-bound ref")
    _validate_digest(value.removeprefix(prefix), label=label)


def _validate_v3_result_ref(value: str, *, label: str) -> None:
    for prefix in (
        "result-ref:ci:",
        "result-ref:verification:",
        "receipt:verification:",
    ):
        if value.startswith(prefix):
            _validate_digest_ref(value, prefix=prefix, label=label)
            return
    raise ValueError(f"{label} must be a content-bound verification result ref")


def _validate_v3_executed_result_ref(value: str, *, label: str) -> None:
    for prefix in ("result-ref:ci:", "result-ref:verification:"):
        if value.startswith(prefix):
            _validate_digest_ref(value, prefix=prefix, label=label)
            return
    raise ValueError(f"{label} must be a content-bound executed result ref")


def _validate_unique_refs(values: tuple[str, ...], *, label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")
    for value in values:
        _validate_ref(value, label=label)


def _validate_repo_path(value: str, *, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or "\\" in value
        or value.startswith("./")
        or unicodedata.normalize("NFC", value) != value
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value
        )
    ):
        raise ValueError(f"{label} must be a safe repository-relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() in {"", "."}
        or path.as_posix() != value
        or any(
            not part or len(part) > 255 or part != part.strip() for part in path.parts
        )
    ):
        raise ValueError(f"{label} must be a safe repository-relative path")


def _validated_timestamp(value: str, *, label: str) -> datetime:
    if UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be bounded canonical UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be bounded canonical UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{label} must be bounded canonical UTC")
    return parsed


@dataclass(frozen=True)
class VerificationUnit:
    unit_ref: str
    display_name: str
    lane_ref: str | None
    needs: tuple[str, ...]
    timeout_minutes: int = 45
    command_refs: tuple[str, ...] = ()
    unit_kind: VerificationUnitKind = VerificationUnitKind.COMMAND
    minimum_risk_tier: VerificationRiskTier = VerificationRiskTier.TIER_0
    execution_surfaces: tuple[str, ...] = ("github", "local", "private")
    parallel_safe: bool = True
    exclusive_resource_refs: tuple[str, ...] = ()
    proof_equivalence_ref: str = "proof-equivalence-ref:none"
    resource_class_ref: str = "resource-class:lightweight"
    resource_stage_ref: str = "resource-stage:unconstrained"
    cpu_units: int = 1
    memory_units: int = 1
    evidence_posture: str = "required"

    @property
    def job_ref(self) -> str:
        """Compatibility alias while the workflow remains a static DAG projection."""

        return self.unit_ref

    def validate(self) -> None:
        _validate_ref(self.unit_ref, label="verification unit ref")
        if not self.display_name or len(self.display_name) > 160:
            raise ValueError("verification unit display name is invalid")
        if self.lane_ref is not None:
            _validate_ref(self.lane_ref, label="verification lane ref")
        _validate_unique_refs(self.needs, label="verification dependency refs")
        _validate_unique_refs(self.command_refs, label="verification command refs")
        if len(self.command_refs) > MAX_COMMAND_REFS:
            raise ValueError("verification unit command count is invalid")
        _validate_unique_refs(
            self.execution_surfaces, label="verification execution surfaces"
        )
        _validate_unique_refs(
            self.exclusive_resource_refs,
            label="verification exclusive resource refs",
        )
        _validate_ref(self.proof_equivalence_ref, label="proof equivalence ref")
        _validate_ref(self.resource_class_ref, label="resource class ref")
        _validate_ref(self.resource_stage_ref, label="resource stage ref")
        if self.evidence_posture not in {"required", "derived", "typed_optional"}:
            raise ValueError("verification unit evidence posture is invalid")
        for value, label in (
            (self.cpu_units, "verification unit CPU units"),
            (self.memory_units, "verification unit memory units"),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 < value <= 4
            ):
                raise ValueError(f"{label} are invalid")
        if not isinstance(self.unit_kind, VerificationUnitKind):
            raise ValueError("verification unit kind is invalid")
        if not isinstance(self.minimum_risk_tier, VerificationRiskTier):
            raise ValueError("verification unit risk tier is invalid")
        if not isinstance(self.parallel_safe, bool):
            raise ValueError("verification unit parallel posture is invalid")
        if (
            not isinstance(self.timeout_minutes, int)
            or isinstance(self.timeout_minutes, bool)
            or not 0 < self.timeout_minutes <= 60
        ):
            raise ValueError("verification unit timeout is invalid")
        if self.unit_kind is VerificationUnitKind.AGGREGATE and (
            self.command_refs or self.lane_ref is not None
        ):
            raise ValueError("aggregate verification units cannot execute commands")
        if self.unit_kind is VerificationUnitKind.AUDIT and self.command_refs:
            raise ValueError("audit verification units cannot embed commands")


def verification_unit_definition_fingerprint(unit: VerificationUnit) -> str:
    """Bind every execution-relevant field in one canonical unit definition."""

    unit.validate()
    payload = {
        field_name: getattr(unit, field_name)
        for field_name in VerificationUnit.__dataclass_fields__
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verification_dag_definition_fingerprint(
    units: tuple[VerificationUnit, ...],
) -> str:
    """Bind the ordered, validated canonical verification graph."""

    validate_verification_dag(units)
    _validate_canonical_verification_dag_order(units)
    payload = tuple(
        (unit.unit_ref, verification_unit_definition_fingerprint(unit))
        for unit in units
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationPlan:
    schema_version: str
    profile_ref: str
    repository_sha: str
    definition_fingerprint: str
    dependency_lock_fingerprints: tuple[tuple[str, str], ...]
    affected_path_classification: str
    selected_lane_refs: tuple[str, ...]
    selected_command_refs: tuple[str, ...]
    pytest_shard_plan_fingerprint: str
    frontend_visual_scope: str
    redaction_status: str
    plan_fingerprint: str
    base_sha: str
    risk_manifest_version: str
    risk_manifest_fingerprint: str
    risk_tier: VerificationRiskTier
    changed_path_refs: tuple[str, ...]
    change_fingerprint: str
    escalation_reason_refs: tuple[str, ...]
    selected_unit_refs: tuple[str, ...]
    selected_test_refs: tuple[str, ...]
    audit_posture: str
    full_pytest_required: bool
    typescript_typecheck_required: bool
    release_gate_required: bool
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str
    test_collection_posture: str
    typescript_project_fingerprint: str
    typescript_project_posture: str
    force_full: bool
    shadow_mode: bool
    verification_dag_fingerprint: str | None = None
    selected_unit_definition_fingerprints: tuple[tuple[str, str], ...] = ()

    def validate(self) -> None:
        for value, label in (
            (self.schema_version, "verification plan schema version"),
            (self.profile_ref, "verification plan profile ref"),
            (self.affected_path_classification, "affected path classification"),
            (self.risk_manifest_version, "risk manifest version"),
            (self.audit_posture, "verification audit posture"),
            (self.frontend_visual_scope, "frontend visual scope"),
            (self.test_collection_posture, "test collection posture"),
            (self.typescript_project_posture, "TypeScript project posture"),
        ):
            _validate_ref(value, label=label)
        if self.schema_version not in SUPPORTED_PLAN_SCHEMA_VERSIONS:
            raise ValueError("unsupported verification plan schema version")
        if not SHA_PATTERN.fullmatch(self.repository_sha) or not SHA_PATTERN.fullmatch(
            self.base_sha
        ):
            raise ValueError("verification plan requires exact lowercase SHAs")
        for value, label in (
            (self.definition_fingerprint, "definition fingerprint"),
            (self.risk_manifest_fingerprint, "risk manifest fingerprint"),
            (self.change_fingerprint, "change fingerprint"),
            (self.pytest_shard_plan_fingerprint, "pytest shard fingerprint"),
            (self.platform_fingerprint, "platform fingerprint"),
            (self.command_manifest_fingerprint, "command manifest fingerprint"),
            (self.verifier_definition_fingerprint, "verifier definition fingerprint"),
            (self.test_collection_fingerprint, "test collection fingerprint"),
            (self.typescript_project_fingerprint, "TypeScript project fingerprint"),
            (self.plan_fingerprint, "plan fingerprint"),
        ):
            _validate_digest(value, label=label)
        if not isinstance(self.risk_tier, VerificationRiskTier):
            raise ValueError("verification plan risk tier is invalid")
        lock_refs: list[str] = []
        for ref, digest in self.dependency_lock_fingerprints:
            _validate_repo_path(ref, label="dependency lock ref")
            lock_refs.append(ref)
            _validate_digest(digest, label="dependency lock fingerprint")
        if len(lock_refs) != len(set(lock_refs)):
            raise ValueError("dependency lock refs must be unique")
        if len(lock_refs) > MAX_LOCK_REFS:
            raise ValueError("dependency lock ref count is invalid")
        if len(self.changed_path_refs) != len(set(self.changed_path_refs)):
            raise ValueError("changed path refs must be unique")
        if len(self.changed_path_refs) > MAX_CHANGED_PATHS:
            raise ValueError("changed path ref count is invalid")
        for path_ref in self.changed_path_refs:
            _validate_repo_path(path_ref, label="changed path ref")
        if len(self.selected_test_refs) != len(set(self.selected_test_refs)):
            raise ValueError("selected test refs must be unique")
        if len(self.selected_test_refs) > MAX_TEST_REFS:
            raise ValueError("selected test ref count is invalid")
        for test_ref in self.selected_test_refs:
            if test_ref.startswith("test-ref:"):
                _validate_ref(test_ref, label="selected test ref")
            else:
                _validate_repo_path(test_ref, label="selected test ref")
        _validate_unique_refs(
            self.escalation_reason_refs, label="verification escalation reasons"
        )
        _validate_unique_refs(self.selected_unit_refs, label="selected unit refs")
        if self.schema_version in {
            "uaa_ci_command_manifest.v4",
            "uaa_ci_command_manifest.v3",
            "uaa_verification_plan.v3",
        }:
            if self.verification_dag_fingerprint is None:
                raise ValueError("v3 verification plan requires an exact DAG binding")
            _validate_digest(
                self.verification_dag_fingerprint,
                label="verification DAG fingerprint",
            )
            definition_unit_refs: list[str] = []
            for unit_ref, fingerprint in self.selected_unit_definition_fingerprints:
                _validate_ref(unit_ref, label="selected unit definition ref")
                _validate_digest(
                    fingerprint,
                    label="selected unit definition fingerprint",
                )
                definition_unit_refs.append(unit_ref)
            if tuple(definition_unit_refs) != self.selected_unit_refs:
                raise ValueError(
                    "selected unit definition bindings must exactly match plan membership"
                )
        elif (
            self.verification_dag_fingerprint is not None
            or self.selected_unit_definition_fingerprints
        ):
            raise ValueError("legacy verification plans cannot claim v3 DAG bindings")
        _validate_unique_refs(self.selected_lane_refs, label="selected lane refs")
        _validate_unique_refs(self.selected_command_refs, label="selected command refs")
        if len(self.selected_command_refs) > MAX_COMMAND_REFS:
            raise ValueError("verification plan command count is invalid")
        if len(self.selected_unit_refs) > MAX_UNITS:
            raise ValueError("verification plan exceeds its unit bound")
        if not self.selected_unit_refs:
            raise ValueError("verification plan must select at least one unit")
        if self.redaction_status != "content_free_refs_hashes_and_repo_paths_only":
            raise ValueError("verification plan redaction posture is invalid")
        if self.risk_manifest_version != "uaa_verification_risk_manifest.v1":
            raise ValueError("verification plan risk manifest version is invalid")
        if self.test_collection_posture not in {
            "not_applicable",
            "inventory_bound",
            "collected",
        }:
            raise ValueError("verification test collection posture is invalid")
        if self.typescript_project_posture not in {"not_applicable", "project_bound"}:
            raise ValueError("verification TypeScript project posture is invalid")
        if self.typescript_typecheck_required and (
            self.typescript_project_posture != "project_bound"
        ):
            raise ValueError("TypeScript verification requires an exact project binding")
        if not all(
            isinstance(value, bool)
            for value in (
                self.full_pytest_required,
                self.typescript_typecheck_required,
                self.release_gate_required,
                self.force_full,
                self.shadow_mode,
            )
        ):
            raise ValueError("verification plan boolean posture is invalid")
        if self.plan_fingerprint != verification_plan_contract_fingerprint(self):
            raise ValueError("verification plan fingerprint does not match its payload")
        if self.force_full and self.risk_tier is not VerificationRiskTier.TIER_3:
            raise ValueError("force-full verification plans must be Tier 3")
        if self.risk_tier is VerificationRiskTier.TIER_3 and (
            not self.full_pytest_required or not self.release_gate_required
        ):
            raise ValueError("Tier 3 verification plans require full release proof")
        if self.release_gate_required and self.risk_tier is not VerificationRiskTier.TIER_3:
            raise ValueError("release verification requires Tier 3 risk")


def verification_plan_payload(
    plan: VerificationPlan,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    excluded = set()
    if plan.schema_version not in {
        "uaa_ci_command_manifest.v4",
        "uaa_ci_command_manifest.v3",
        "uaa_verification_plan.v3",
    }:
        excluded.update(V3_PLAN_ONLY_FIELDS)
    if not include_content_identity:
        excluded.add("plan_fingerprint")
    return {
        field_name: getattr(plan, field_name)
        for field_name in VerificationPlan.__dataclass_fields__
        if field_name not in excluded
    }


def verification_plan_contract_fingerprint(plan: VerificationPlan) -> str:
    payload = verification_plan_payload(plan, include_content_identity=False)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationReceipt:
    schema_version: str
    receipt_ref: str
    plan_fingerprint: str
    unit_ref: str
    repository_sha: str
    dependency_state_fingerprint: str
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str
    status: VerificationTerminalStatus
    started_at: str
    completed_at: str
    duration_ms: int
    result_refs: tuple[str, ...]
    output_byte_count: int
    output_digest: str
    equivalent_receipt_ref: str | None = None
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"
    command_refs: tuple[str, ...] = ()
    command_result_bindings: tuple[tuple[str, str], ...] = ()
    execution_surface_ref: str = "surface-ref:unbound"
    proof_equivalence_ref: str = "proof-equivalence-ref:none"
    test_collection_posture: str = "not_applicable"
    observed_test_collection_fingerprint: str | None = None
    observed_test_count: int = 0
    typescript_binding_posture: str = "not_applicable"
    typescript_project_fingerprint: str | None = None
    typescript_runtime_fingerprint: str | None = None
    typescript_version_ref: str | None = None
    receipt_fingerprint: str | None = None
    dependency_lock_set_fingerprint: str | None = None
    pytest_shard_plan_fingerprint: str | None = None
    execution_identity_ref: str | None = None
    executed_command_result_bindings: tuple[tuple[str, str], ...] = ()
    nonexecuted_command_result_bindings: tuple[tuple[str, str, str], ...] = ()
    reused_command_receipt_bindings: tuple[tuple[str, str], ...] = ()
    observed_platform_fingerprint: str | None = None

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification receipt schema version")
        _validate_ref(self.receipt_ref, label="verification receipt ref")
        _validate_ref(self.unit_ref, label="verification receipt unit ref")
        if self.schema_version not in {
            "uaa_verification_receipt.v1",
            "uaa_verification_receipt.v2",
            "uaa_verification_receipt.v3",
            "uaa_verification_receipt.v4",
        }:
            raise ValueError("unsupported verification receipt schema version")
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("verification receipt requires an exact SHA")
        for value, label in (
            (self.plan_fingerprint, "receipt plan fingerprint"),
            (self.dependency_state_fingerprint, "dependency state fingerprint"),
            (self.platform_fingerprint, "receipt platform fingerprint"),
            (self.command_manifest_fingerprint, "receipt command fingerprint"),
            (self.verifier_definition_fingerprint, "receipt verifier fingerprint"),
            (self.test_collection_fingerprint, "receipt collection fingerprint"),
            (self.output_digest, "receipt output digest"),
        ):
            _validate_digest(value, label=label)
        _validate_unique_refs(self.result_refs, label="verification result refs")
        _validate_unique_refs(self.command_refs, label="verification receipt command refs")
        _validate_ref(self.execution_surface_ref, label="verification execution surface")
        _validate_ref(self.proof_equivalence_ref, label="verification proof equivalence")
        if len(self.result_refs) > MAX_RECEIPTS:
            raise ValueError("verification receipt result count is invalid")
        if not isinstance(self.status, VerificationTerminalStatus):
            raise ValueError("verification receipt status is invalid")
        if self.status is VerificationTerminalStatus.PASSED and not self.result_refs:
            raise ValueError("passed verification receipt requires result evidence")
        if self.equivalent_receipt_ref is not None:
            _validate_ref(
                self.equivalent_receipt_ref, label="equivalent verification receipt ref"
            )
        if self.test_collection_posture not in {
            "not_applicable",
            "collected",
            "rejected",
            "unavailable",
        }:
            raise ValueError("verification receipt collection posture is invalid")
        if (
            not isinstance(self.observed_test_count, int)
            or isinstance(self.observed_test_count, bool)
            or not 0 <= self.observed_test_count <= 1_000_000
        ):
            raise ValueError("verification receipt observed test count is invalid")
        if self.test_collection_posture == "collected":
            if self.observed_test_collection_fingerprint is None:
                raise ValueError("collected verification receipt requires collection proof")
            _validate_digest(
                self.observed_test_collection_fingerprint,
                label="observed test collection fingerprint",
            )
            if self.observed_test_count <= 0:
                raise ValueError("collected verification receipt requires observed tests")
        elif (
            self.observed_test_collection_fingerprint is not None
            or self.observed_test_count != 0
        ):
            raise ValueError("uncollected verification receipt cannot claim observed tests")
        if self.typescript_binding_posture not in {
            "not_applicable",
            "resolved",
            "rejected",
            "unavailable",
        }:
            raise ValueError("verification receipt TypeScript posture is invalid")
        if self.typescript_binding_posture == "resolved":
            if (
                self.typescript_project_fingerprint is None
                or self.typescript_runtime_fingerprint is None
                or self.typescript_version_ref is None
            ):
                raise ValueError("resolved TypeScript receipt requires exact bindings")
            _validate_digest(
                self.typescript_project_fingerprint,
                label="receipt TypeScript project fingerprint",
            )
            _validate_digest(
                self.typescript_runtime_fingerprint,
                label="receipt TypeScript runtime fingerprint",
            )
            _validate_ref(self.typescript_version_ref, label="TypeScript version ref")
        elif any(
            value is not None
            for value in (
                self.typescript_project_fingerprint,
                self.typescript_runtime_fingerprint,
                self.typescript_version_ref,
            )
        ):
            raise ValueError("unresolved TypeScript receipt cannot claim exact bindings")
        if self.schema_version == "uaa_verification_receipt.v4":
            if self.observed_platform_fingerprint is None:
                raise ValueError(
                    "v4 verification receipt requires observed platform proof"
                )
            _validate_digest(
                self.observed_platform_fingerprint,
                label="receipt observed platform fingerprint",
            )
        elif self.observed_platform_fingerprint is not None:
            raise ValueError(
                "legacy verification receipt cannot claim observed platform proof"
            )
        if (
            not isinstance(self.duration_ms, int)
            or isinstance(self.duration_ms, bool)
            or not 0 <= self.duration_ms <= MAX_DURATION_MS
        ):
            raise ValueError("verification receipt duration is invalid")
        if (
            not isinstance(self.output_byte_count, int)
            or isinstance(self.output_byte_count, bool)
            or not 0 <= self.output_byte_count <= 32 * 1024 * 1024
        ):
            raise ValueError("verification receipt output count is invalid")
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("verification receipt redaction posture is invalid")
        started = _validated_timestamp(self.started_at, label="receipt start timestamp")
        completed = _validated_timestamp(
            self.completed_at, label="receipt completion timestamp"
        )
        if completed < started:
            raise ValueError("verification receipt completion precedes its start")
        wall_duration_ms = int((completed - started).total_seconds() * 1_000)
        if (
            wall_duration_ms > MAX_DURATION_MS
            or abs(wall_duration_ms - self.duration_ms)
            > MAX_DURATION_CLOCK_SKEW_MS
        ):
            raise ValueError("verification receipt duration evidence is inconsistent")
        if self.schema_version in {
            "uaa_verification_receipt.v2",
            "uaa_verification_receipt.v3",
            "uaa_verification_receipt.v4",
        }:
            binding_commands: list[str] = []
            binding_results: list[str] = []
            for command_ref, result_ref in self.command_result_bindings:
                _validate_ref(command_ref, label="receipt command binding ref")
                _validate_ref(result_ref, label="receipt result binding ref")
                binding_commands.append(command_ref)
                binding_results.append(result_ref)
            if self.schema_version == "uaa_verification_receipt.v2":
                if (
                    tuple(binding_commands) != self.command_refs
                    or (
                        bool(self.command_refs)
                        and tuple(binding_results) != self.result_refs
                    )
                    or (not self.command_refs and bool(binding_results))
                    or len(binding_commands) != len(set(binding_commands))
                    or len(binding_results) != len(set(binding_results))
                ):
                    raise ValueError(
                        "verification receipt command results are not exactly bound"
                    )
            else:
                if (
                    self.dependency_lock_set_fingerprint is None
                    or self.pytest_shard_plan_fingerprint is None
                    or self.execution_identity_ref is None
                ):
                    raise ValueError(
                        "modern verification receipt requires exact execution bindings"
                    )
                _validate_digest(
                    self.dependency_lock_set_fingerprint,
                    label="receipt dependency lock set fingerprint",
                )
                _validate_digest(
                    self.pytest_shard_plan_fingerprint,
                    label="receipt pytest shard plan fingerprint",
                )
                _validate_digest_ref(
                    self.execution_identity_ref,
                    prefix="execution-identity:",
                    label="receipt execution identity ref",
                )
                for result_ref in self.result_refs:
                    _validate_v3_result_ref(
                        result_ref,
                        label="v3 verification result ref",
                    )
                if self.equivalent_receipt_ref is not None:
                    equivalent_prefix = (
                        "receipt:verification:"
                        if self.equivalent_receipt_ref.startswith(
                            "receipt:verification:"
                        )
                        else "receipt-ref:ci-lane:"
                    )
                    _validate_digest_ref(
                        self.equivalent_receipt_ref,
                        prefix=equivalent_prefix,
                        label="equivalent verification receipt ref",
                    )
                executed_commands: list[str] = []
                executed_results: list[str] = []
                for command_ref, result_ref in self.executed_command_result_bindings:
                    _validate_ref(command_ref, label="executed command binding ref")
                    _validate_v3_executed_result_ref(
                        result_ref,
                        label="executed command result ref",
                    )
                    executed_commands.append(command_ref)
                    executed_results.append(result_ref)
                nonexecuted_commands: list[str] = []
                nonexecuted_results: list[str] = []
                for (
                    command_ref,
                    result_ref,
                    reason_ref,
                ) in self.nonexecuted_command_result_bindings:
                    _validate_ref(command_ref, label="nonexecuted command binding ref")
                    _validate_v3_executed_result_ref(
                        result_ref,
                        label="nonexecuted command result ref",
                    )
                    _validate_ref(reason_ref, label="nonexecuted command reason ref")
                    nonexecuted_commands.append(command_ref)
                    nonexecuted_results.append(result_ref)
                reused_commands: list[str] = []
                reused_receipts: list[str] = []
                for command_ref, receipt_ref in self.reused_command_receipt_bindings:
                    _validate_ref(command_ref, label="reused command binding ref")
                    _validate_digest_ref(
                        receipt_ref,
                        prefix="receipt:verification:",
                        label="reused command receipt ref",
                    )
                    reused_commands.append(command_ref)
                    reused_receipts.append(receipt_ref)
                command_evidence = {
                    **dict(self.executed_command_result_bindings),
                    **{
                        command_ref: result_ref
                        for command_ref, result_ref, _reason_ref in (
                            self.nonexecuted_command_result_bindings
                        )
                    },
                    **dict(self.reused_command_receipt_bindings),
                }
                if (
                    len(executed_commands) != len(set(executed_commands))
                    or len(executed_results) != len(set(executed_results))
                    or len(nonexecuted_commands) != len(set(nonexecuted_commands))
                    or len(nonexecuted_results) != len(set(nonexecuted_results))
                    or len(reused_commands) != len(set(reused_commands))
                    or len(reused_receipts) != len(set(reused_receipts))
                    or set(executed_commands)
                    & (set(nonexecuted_commands) | set(reused_commands))
                    or set(nonexecuted_commands) & set(reused_commands)
                    or tuple(binding_commands) != tuple(executed_commands)
                    or tuple(binding_results) != tuple(executed_results)
                    or set(command_evidence) != set(self.command_refs)
                    or (
                        bool(self.command_refs)
                        and tuple(command_evidence[ref] for ref in self.command_refs)
                        != self.result_refs
                    )
                ):
                    raise ValueError(
                        "modern verification receipt command evidence is not exactly bound"
                    )
                if self.nonexecuted_command_result_bindings and (
                    self.status is not VerificationTerminalStatus.BLOCKED
                ):
                    raise ValueError(
                        "modern nonexecution evidence requires blocked terminal posture"
                    )
            if self.status is VerificationTerminalStatus.PASSED and any(
                command_ref.startswith("command:pytest.")
                or command_ref in TEST_EXECUTION_COMMAND_REFS
                for command_ref in self.command_refs
            ) and self.test_collection_posture != "collected":
                raise ValueError("passed test receipt requires observed collection proof")
            if self.schema_version in {
                "uaa_verification_receipt.v3",
                "uaa_verification_receipt.v4",
            }:
                typescript_execution = any(
                    command_ref in TYPESCRIPT_EXECUTION_COMMAND_REFS
                    for command_ref in (
                        *(
                            binding[0]
                            for binding in self.executed_command_result_bindings
                        ),
                        *(
                            binding[0]
                            for binding in self.reused_command_receipt_bindings
                        ),
                    )
                )
                if (
                    typescript_execution
                    and self.typescript_binding_posture != "resolved"
                ):
                    raise ValueError(
                        "modern TypeScript receipt requires a pre-start runtime binding"
                    )
                if (
                    not typescript_execution
                    and self.typescript_binding_posture != "not_applicable"
                ):
                    raise ValueError(
                        "modern non-TypeScript receipt cannot claim a runtime binding"
                    )
            if self.status is VerificationTerminalStatus.PASSED and any(
                command_ref in TYPESCRIPT_EXECUTION_COMMAND_REFS
                for command_ref in self.command_refs
            ) and self.typescript_binding_posture != "resolved":
                raise ValueError("passed TypeScript receipt requires runtime binding")
            expected_fingerprint = verification_receipt_fingerprint(self)
            if self.receipt_fingerprint != expected_fingerprint:
                raise ValueError("verification receipt fingerprint does not match its payload")
            if self.receipt_ref != f"receipt:verification:{expected_fingerprint}":
                raise ValueError("verification receipt ref is not content bound")


def verification_receipt_payload(
    receipt: VerificationReceipt,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    excluded = set()
    if receipt.schema_version not in {
        "uaa_verification_receipt.v3",
        "uaa_verification_receipt.v4",
    }:
        excluded.update(V3_RECEIPT_ONLY_FIELDS)
    if receipt.schema_version != "uaa_verification_receipt.v4":
        excluded.update(V4_RECEIPT_ONLY_FIELDS)
    if (
        receipt.schema_version == "uaa_verification_receipt.v3"
        and not receipt.nonexecuted_command_result_bindings
    ):
        # Preserve the content identity of existing v3 receipts. The new field
        # is an additive typed-optional extension and is serialized only when
        # it carries proof.
        excluded.add("nonexecuted_command_result_bindings")
    if not include_content_identity:
        excluded.update({"receipt_ref", "receipt_fingerprint"})
    return {
        field_name: getattr(receipt, field_name)
        for field_name in VerificationReceipt.__dataclass_fields__
        if field_name not in excluded
    }


def verification_receipt_fingerprint(receipt: VerificationReceipt) -> str:
    payload = verification_receipt_payload(
        receipt,
        include_content_identity=False,
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationRunManifest:
    schema_version: str
    run_ref: str
    plan_fingerprint: str
    repository_sha: str
    receipt_refs: tuple[str, ...]
    started_at: str
    completed_at: str
    status: VerificationTerminalStatus
    run_fingerprint: str
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"
    dependency_state_fingerprint: str | None = None
    command_manifest_fingerprint: str | None = None
    execution_surface_ref: str = "surface-ref:unbound"
    unit_receipt_bindings: tuple[tuple[str, str], ...] = ()
    dependency_lock_set_fingerprint: str | None = None
    platform_fingerprint: str | None = None
    verifier_definition_fingerprint: str | None = None
    test_collection_fingerprint: str | None = None
    pytest_shard_plan_fingerprint: str | None = None
    typescript_project_fingerprint: str | None = None
    required_unit_refs: tuple[str, ...] = ()
    missing_unit_refs: tuple[str, ...] = ()
    failed_unit_refs: tuple[str, ...] = ()
    reason_refs: tuple[str, ...] = ()
    observed_test_collection_bindings: tuple[tuple[str, str], ...] = ()

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification run schema version")
        _validate_ref(self.run_ref, label="verification run ref")
        if self.schema_version not in {
            "uaa_verification_run.v1",
            "uaa_verification_run.v2",
            "uaa_verification_run.v3",
        }:
            raise ValueError("unsupported verification run schema version")
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("verification run requires an exact SHA")
        _validate_digest(self.plan_fingerprint, label="run plan fingerprint")
        _validate_digest(self.run_fingerprint, label="run fingerprint")
        _validate_unique_refs(self.receipt_refs, label="run receipt refs")
        _validate_ref(self.execution_surface_ref, label="run execution surface")
        if not isinstance(self.status, VerificationTerminalStatus):
            raise ValueError("verification run status is invalid")
        if len(self.receipt_refs) > MAX_RECEIPTS or (
            self.schema_version != "uaa_verification_run.v3"
            and not self.receipt_refs
        ):
            raise ValueError("verification run receipt count is invalid")
        started = _validated_timestamp(self.started_at, label="run start timestamp")
        completed = _validated_timestamp(
            self.completed_at, label="run completion timestamp"
        )
        if completed < started:
            raise ValueError("verification run completion precedes its start")
        if int((completed - started).total_seconds() * 1_000) > MAX_DURATION_MS:
            raise ValueError("verification run exceeds its bounded duration")
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("verification run redaction posture is invalid")
        unit_refs: list[str] = []
        binding_receipt_refs: list[str] = []
        for unit_ref, receipt_ref in self.unit_receipt_bindings:
            _validate_ref(unit_ref, label="run unit binding ref")
            _validate_ref(receipt_ref, label="run receipt binding ref")
            unit_refs.append(unit_ref)
            binding_receipt_refs.append(receipt_ref)
        if len(unit_refs) != len(set(unit_refs)) or len(binding_receipt_refs) != len(
            set(binding_receipt_refs)
        ):
            raise ValueError("run unit receipt bindings must be one-to-one")
        if self.schema_version in {
            "uaa_verification_run.v2",
            "uaa_verification_run.v3",
        }:
            if (
                self.dependency_state_fingerprint is None
                or self.command_manifest_fingerprint is None
            ):
                raise ValueError("v2 verification run requires exact dependency bindings")
            _validate_digest(
                self.dependency_state_fingerprint,
                label="run dependency state fingerprint",
            )
            _validate_digest(
                self.command_manifest_fingerprint,
                label="run command manifest fingerprint",
            )
            if tuple(binding_receipt_refs) != self.receipt_refs:
                raise ValueError("run receipt refs do not match unit bindings")
            if self.schema_version == "uaa_verification_run.v3":
                if self.status not in {
                    VerificationTerminalStatus.PASSED,
                    VerificationTerminalStatus.FAILED,
                    VerificationTerminalStatus.BLOCKED,
                }:
                    raise ValueError("v3 verification run status is unsupported")
                for receipt_ref in self.receipt_refs:
                    _validate_digest_ref(
                        receipt_ref,
                        prefix="receipt:verification:",
                        label="v3 run receipt ref",
                    )
                for receipt_ref in binding_receipt_refs:
                    _validate_digest_ref(
                        receipt_ref,
                        prefix="receipt:verification:",
                        label="v3 run receipt binding ref",
                    )
                exact_digest_fields = (
                    (
                        self.dependency_lock_set_fingerprint,
                        "run dependency lock set fingerprint",
                    ),
                    (self.platform_fingerprint, "run platform fingerprint"),
                    (
                        self.verifier_definition_fingerprint,
                        "run verifier definition fingerprint",
                    ),
                    (
                        self.test_collection_fingerprint,
                        "run test collection fingerprint",
                    ),
                    (
                        self.pytest_shard_plan_fingerprint,
                        "run pytest shard plan fingerprint",
                    ),
                    (
                        self.typescript_project_fingerprint,
                        "run TypeScript project fingerprint",
                    ),
                )
                if any(value is None for value, _label in exact_digest_fields):
                    raise ValueError("v3 verification run requires complete exact bindings")
                for value, label in exact_digest_fields:
                    assert value is not None
                    _validate_digest(value, label=label)
                _validate_unique_refs(
                    self.required_unit_refs,
                    label="run required unit refs",
                )
                _validate_unique_refs(
                    self.missing_unit_refs,
                    label="run missing unit refs",
                )
                _validate_unique_refs(
                    self.failed_unit_refs,
                    label="run failed unit refs",
                )
                _validate_unique_refs(self.reason_refs, label="run reason refs")
                if not self.required_unit_refs:
                    raise ValueError("v3 verification run requires whole-plan membership")
                bound_units = tuple(unit_refs)
                if (
                    tuple(
                        unit_ref
                        for unit_ref in self.required_unit_refs
                        if unit_ref not in set(self.missing_unit_refs)
                    )
                    != bound_units
                    or tuple(
                        unit_ref
                        for unit_ref in self.required_unit_refs
                        if unit_ref not in set(bound_units)
                    )
                    != self.missing_unit_refs
                    or not set(self.failed_unit_refs).issubset(bound_units)
                ):
                    raise ValueError("v3 verification run membership is not exact")
                observed_units: list[str] = []
                for unit_ref, collection_fingerprint in (
                    self.observed_test_collection_bindings
                ):
                    _validate_ref(unit_ref, label="run observed collection unit ref")
                    _validate_digest(
                        collection_fingerprint,
                        label="run observed collection fingerprint",
                    )
                    observed_units.append(unit_ref)
                if (
                    len(observed_units) != len(set(observed_units))
                    or not set(observed_units).issubset(bound_units)
                ):
                    raise ValueError("v3 run collection bindings are invalid")
                if self.status is VerificationTerminalStatus.PASSED and (
                    self.missing_unit_refs
                    or self.failed_unit_refs
                    or bound_units != self.required_unit_refs
                    or self.reason_refs
                ):
                    raise ValueError("passed v3 verification run requires exact success")
                if self.status is VerificationTerminalStatus.FAILED and not (
                    self.failed_unit_refs and self.reason_refs
                ):
                    raise ValueError("failed v3 verification run requires failed evidence")
                if self.status is VerificationTerminalStatus.BLOCKED and not (
                    self.missing_unit_refs or self.reason_refs
                ):
                    raise ValueError("blocked v3 verification run requires blockers")
                if (
                    self.status is VerificationTerminalStatus.BLOCKED
                    and self.failed_unit_refs
                ):
                    raise ValueError("blocked v3 verification run cannot claim failures")
            expected_fingerprint = verification_run_manifest_fingerprint(self)
            if self.run_fingerprint != expected_fingerprint:
                raise ValueError("verification run fingerprint does not match its payload")
            if self.run_ref != f"run:verification:{expected_fingerprint}":
                raise ValueError("verification run ref is not content bound")


def verification_run_manifest_payload(
    run: VerificationRunManifest,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    excluded = set()
    if run.schema_version != "uaa_verification_run.v3":
        excluded.update(V3_RUN_ONLY_FIELDS)
    if not include_content_identity:
        excluded.update({"run_ref", "run_fingerprint"})
    return {
        field_name: getattr(run, field_name)
        for field_name in VerificationRunManifest.__dataclass_fields__
        if field_name not in excluded
    }


def verification_run_manifest_fingerprint(run: VerificationRunManifest) -> str:
    payload = verification_run_manifest_payload(
        run,
        include_content_identity=False,
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationGithubGateProof:
    schema_version: str
    proof_ref: str
    repository_sha: str
    plan_fingerprint: str
    run_manifest_fingerprint: str
    command_manifest_fingerprint: str
    workflow_ref: str
    github_run_ref: str
    workflow_attempt: int
    runner_pool_ref: str
    required_check_refs: tuple[str, ...]
    completed_check_refs: tuple[str, ...]
    status: VerificationTerminalStatus
    started_at: str
    completed_at: str
    proof_fingerprint: str
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"

    def validate(self) -> None:
        if self.schema_version != "uaa_verification_github_gate_proof.v1":
            raise ValueError("unsupported GitHub gate proof schema version")
        for value, label in (
            (self.schema_version, "GitHub proof schema version"),
            (self.proof_ref, "GitHub proof ref"),
            (self.workflow_ref, "GitHub workflow ref"),
            (self.github_run_ref, "GitHub run ref"),
            (self.runner_pool_ref, "GitHub runner pool ref"),
        ):
            _validate_ref(value, label=label)
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("GitHub gate proof requires an exact SHA")
        for value, label in (
            (self.plan_fingerprint, "GitHub proof plan fingerprint"),
            (self.run_manifest_fingerprint, "GitHub proof run fingerprint"),
            (self.command_manifest_fingerprint, "GitHub proof command fingerprint"),
            (self.proof_fingerprint, "GitHub proof fingerprint"),
        ):
            _validate_digest(value, label=label)
        if (
            not isinstance(self.workflow_attempt, int)
            or isinstance(self.workflow_attempt, bool)
            or not 1 <= self.workflow_attempt <= 100
        ):
            raise ValueError("GitHub workflow attempt is invalid")
        _validate_unique_refs(self.required_check_refs, label="required GitHub check refs")
        _validate_unique_refs(self.completed_check_refs, label="completed GitHub check refs")
        if not isinstance(self.status, VerificationTerminalStatus):
            raise ValueError("GitHub gate proof status is invalid")
        if self.status is VerificationTerminalStatus.PASSED and (
            not self.required_check_refs
            or self.required_check_refs != self.completed_check_refs
        ):
            raise ValueError("passed GitHub proof requires exact check coverage")
        started = _validated_timestamp(self.started_at, label="GitHub proof start timestamp")
        completed = _validated_timestamp(
            self.completed_at, label="GitHub proof completion timestamp"
        )
        if completed < started:
            raise ValueError("GitHub proof completion precedes its start")
        if self.redaction_status != "content_free_refs_hashes_counts_and_durations_only":
            raise ValueError("GitHub proof redaction posture is invalid")
        expected_fingerprint = verification_github_gate_proof_fingerprint(self)
        if self.proof_fingerprint != expected_fingerprint:
            raise ValueError("GitHub proof fingerprint does not match its payload")
        if self.proof_ref != f"proof:github:{expected_fingerprint}":
            raise ValueError("GitHub proof ref is not content bound")


def verification_github_gate_proof_fingerprint(
    proof: VerificationGithubGateProof,
) -> str:
    payload = {
        field_name: getattr(proof, field_name)
        for field_name in VerificationGithubGateProof.__dataclass_fields__
        if field_name not in {"proof_ref", "proof_fingerprint"}
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationGateDecision:
    schema_version: str
    decision_ref: str
    repository_sha: str
    plan_fingerprint: str
    status: VerificationGateStatus
    required_unit_refs: tuple[str, ...]
    validated_receipt_refs: tuple[str, ...]
    missing_unit_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]
    github_run_ref: str
    github_gate_satisfied: bool
    merge_gate_satisfied: bool
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"
    github_proof_ref: str | None = None
    run_manifest_ref: str | None = None

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification gate schema version")
        if self.schema_version not in {
            "uaa_verification_gate_decision.v1",
            "uaa_verification_gate_decision.v2",
        }:
            raise ValueError("unsupported verification gate schema version")
        _validate_ref(self.decision_ref, label="verification gate decision ref")
        _validate_ref(self.github_run_ref, label="GitHub run ref")
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("verification gate decision requires an exact SHA")
        _validate_digest(self.plan_fingerprint, label="gate plan fingerprint")
        _validate_unique_refs(self.required_unit_refs, label="required unit refs")
        _validate_unique_refs(
            self.validated_receipt_refs, label="validated receipt refs"
        )
        _validate_unique_refs(self.missing_unit_refs, label="missing unit refs")
        _validate_unique_refs(self.reason_refs, label="gate reason refs")
        if (
            len(self.required_unit_refs) > MAX_UNITS
            or len(self.validated_receipt_refs) > MAX_RECEIPTS
            or len(self.missing_unit_refs) > MAX_UNITS
        ):
            raise ValueError("verification gate membership count is invalid")
        if not isinstance(self.status, VerificationGateStatus):
            raise ValueError("verification gate status is invalid")
        if not isinstance(self.github_gate_satisfied, bool) or not isinstance(
            self.merge_gate_satisfied, bool
        ):
            raise ValueError("verification gate boolean posture is invalid")
        if self.status is VerificationGateStatus.PASSED and (
            not self.required_unit_refs
            or self.missing_unit_refs
            or len(self.validated_receipt_refs) != len(self.required_unit_refs)
        ):
            raise ValueError("passed verification gate requires exact receipt coverage")
        if self.github_proof_ref is not None:
            _validate_ref(self.github_proof_ref, label="GitHub gate proof ref")
        if self.run_manifest_ref is not None:
            _validate_ref(self.run_manifest_ref, label="verification run manifest ref")
        if self.schema_version == "uaa_verification_gate_decision.v1" and (
            self.status is VerificationGateStatus.PASSED or self.merge_gate_satisfied
        ):
            raise ValueError("v1 verification gates cannot replace typed GitHub proof")
        if self.schema_version == "uaa_verification_gate_decision.v2" and (
            self.github_proof_ref is None or self.run_manifest_ref is None
        ):
            raise ValueError("v2 verification gate requires typed GitHub and run proof")
        if (
            self.schema_version == "uaa_verification_gate_decision.v2"
            and self.decision_ref
            != f"decision:verification:{verification_gate_decision_fingerprint(self)}"
        ):
            raise ValueError("verification gate decision ref is not content bound")
        if self.merge_gate_satisfied and (
            self.status is not VerificationGateStatus.PASSED
            or not self.github_gate_satisfied
            or self.missing_unit_refs
        ):
            raise ValueError(
                "merge gate cannot be satisfied without exact GitHub proof"
            )
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("verification gate redaction posture is invalid")


def verification_gate_decision_fingerprint(
    decision: VerificationGateDecision,
) -> str:
    payload = {
        field_name: getattr(decision, field_name)
        for field_name in VerificationGateDecision.__dataclass_fields__
        if field_name != "decision_ref"
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerificationValueRecord:
    schema_version: str
    value_ref: str
    unit_ref: str
    verifier_ref: str
    synthetic_mutation_ref: str
    defect_ref: str
    outcome: str
    receipt_ref: str
    overlap_ref: str
    disposition: str
    duration_ms: int
    repository_sha: str
    dependency_state_fingerprint: str
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str
    probe_definition_fingerprint: str
    detection_ref: str
    value_fingerprint: str
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"

    def validate(self) -> None:
        if self.schema_version != "uaa_verification_value.v2":
            raise ValueError("verification value schema version is unsupported")
        for value, label in (
            (self.value_ref, "verification value ref"),
            (self.unit_ref, "verification value unit ref"),
            (self.verifier_ref, "verifier ref"),
            (self.synthetic_mutation_ref, "synthetic mutation ref"),
            (self.defect_ref, "defect ref"),
            (self.receipt_ref, "value receipt ref"),
            (self.overlap_ref, "value overlap ref"),
            (self.disposition, "value disposition"),
            (self.detection_ref, "verification value detection ref"),
        ):
            _validate_ref(value, label=label)
        if SHA_PATTERN.fullmatch(self.repository_sha) is None:
            raise ValueError("verification value repository SHA is invalid")
        for value, label in (
            (
                self.dependency_state_fingerprint,
                "verification value dependency state fingerprint",
            ),
            (self.platform_fingerprint, "verification value platform fingerprint"),
            (
                self.command_manifest_fingerprint,
                "verification value command manifest fingerprint",
            ),
            (
                self.verifier_definition_fingerprint,
                "verification value verifier definition fingerprint",
            ),
            (
                self.test_collection_fingerprint,
                "verification value test collection fingerprint",
            ),
            (
                self.probe_definition_fingerprint,
                "verification value probe definition fingerprint",
            ),
            (self.value_fingerprint, "verification value fingerprint"),
        ):
            _validate_digest(value, label=label)
        if self.outcome not in {"killed", "survived", "blocked", "unknown"}:
            raise ValueError("verification value outcome is invalid")
        allowed_dispositions = {
            "retain",
            "retain-fast-loop",
            "retain-release-only",
            "retain-outside-fast-loop",
            "retain-unmeasured",
            "retain-consolidated",
        }
        if self.disposition not in allowed_dispositions:
            raise ValueError("verification value disposition is invalid")
        if self.disposition == "retain-consolidated" and self.outcome != "killed":
            raise ValueError(
                "verification consolidation requires a killed synthetic mutation"
            )
        if (
            not isinstance(self.duration_ms, int)
            or isinstance(self.duration_ms, bool)
            or not 0 <= self.duration_ms <= MAX_DURATION_MS
        ):
            raise ValueError("verification value duration is invalid")
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("verification value redaction posture is invalid")
        expected = verification_value_record_fingerprint(self)
        if self.value_fingerprint != expected:
            raise ValueError("verification value fingerprint is not content bound")
        if self.value_ref != f"value:verification:{expected}":
            raise ValueError("verification value ref is not content bound")
        if self.receipt_ref != f"receipt:verification-value:{expected}":
            raise ValueError("verification value receipt ref is not content bound")


def verification_value_record_fingerprint(record: VerificationValueRecord) -> str:
    payload = {
        field_name: getattr(record, field_name)
        for field_name in VerificationValueRecord.__dataclass_fields__
        if field_name not in {"value_ref", "receipt_ref", "value_fingerprint"}
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_verification_dag(units: tuple[VerificationUnit, ...]) -> None:
    if not units or len(units) > MAX_UNITS:
        raise ValueError("verification DAG unit count is invalid")
    refs = [unit.unit_ref for unit in units]
    if len(refs) != len(set(refs)):
        raise ValueError("verification DAG unit refs must be unique")
    known = set(refs)
    for unit in units:
        unit.validate()
        if unit.unit_ref in unit.needs:
            raise ValueError("verification DAG cannot contain a self dependency")
        if unknown := set(unit.needs) - known:
            raise ValueError(
                f"verification DAG has unknown dependencies: {sorted(unknown)}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()
    by_ref = {unit.unit_ref: unit for unit in units}

    def visit(ref: str) -> None:
        if ref in visiting:
            raise ValueError("verification DAG cannot contain a cycle")
        if ref in visited:
            return
        visiting.add(ref)
        for dependency in by_ref[ref].needs:
            visit(dependency)
        visiting.remove(ref)
        visited.add(ref)

    for ref in refs:
        visit(ref)


def _validate_canonical_verification_dag_order(
    units: tuple[VerificationUnit, ...],
) -> None:
    """Require dependency-first order only for canonical graph serialization."""

    seen: set[str] = set()
    for unit in units:
        if not set(unit.needs).issubset(seen):
            raise ValueError("verification DAG must be topologically ordered")
        seen.add(unit.unit_ref)


def dependency_closed_unit_refs(
    units: tuple[VerificationUnit, ...],
    selected_unit_refs: tuple[str, ...],
) -> tuple[str, ...]:
    validate_verification_dag(units)
    if len(selected_unit_refs) != len(set(selected_unit_refs)):
        raise ValueError("selected verification unit refs must be unique")
    by_ref = {unit.unit_ref: unit for unit in units}
    unknown = set(selected_unit_refs) - set(by_ref)
    if unknown:
        raise ValueError(f"selected verification units are unknown: {sorted(unknown)}")
    selected = set(selected_unit_refs)
    pending = list(selected_unit_refs)
    while pending:
        unit = by_ref[pending.pop()]
        for dependency in unit.needs:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return tuple(unit.unit_ref for unit in units if unit.unit_ref in selected)


def dependency_lock_set_fingerprint(plan: VerificationPlan) -> str:
    return hashlib.sha256(
        json.dumps(
            plan.dependency_lock_fingerprints,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def dependency_state_fingerprint(plan: VerificationPlan) -> str:
    payload: dict[str, Any] = {
        "locks": plan.dependency_lock_fingerprints,
        "platform": plan.platform_fingerprint,
        "commands": plan.command_manifest_fingerprint,
        "verifiers": plan.verifier_definition_fingerprint,
        "collection": plan.test_collection_fingerprint,
        "pytest_shard_plan": plan.pytest_shard_plan_fingerprint,
        "typescript_project": plan.typescript_project_fingerprint,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def evaluate_verification_gate(
    plan: VerificationPlan,
    receipts: tuple[VerificationReceipt, ...],
    *,
    github_run_ref: str,
    github_gate_satisfied: bool,
) -> VerificationGateDecision:
    plan.validate()
    if not isinstance(github_gate_satisfied, bool):
        raise ValueError("GitHub gate posture must be boolean")
    expected_dependency_state = dependency_state_fingerprint(plan)
    required = plan.selected_unit_refs
    by_unit: dict[str, VerificationReceipt] = {}
    invalid_units: set[str] = set()
    invalid_evidence_present = False
    for receipt in receipts:
        try:
            receipt.validate()
        except (TypeError, ValueError):
            invalid_evidence_present = True
            if receipt.unit_ref in required:
                invalid_units.add(receipt.unit_ref)
            continue
        if receipt.unit_ref in by_unit:
            invalid_evidence_present = True
            invalid_units.add(receipt.unit_ref)
            continue
        if (
            receipt.unit_ref not in required
            or receipt.plan_fingerprint != plan.plan_fingerprint
            or receipt.repository_sha != plan.repository_sha
            or receipt.dependency_state_fingerprint != expected_dependency_state
            or receipt.platform_fingerprint != plan.platform_fingerprint
            or receipt.command_manifest_fingerprint != plan.command_manifest_fingerprint
            or receipt.verifier_definition_fingerprint
            != plan.verifier_definition_fingerprint
            or receipt.test_collection_fingerprint != plan.test_collection_fingerprint
            or receipt.status is not VerificationTerminalStatus.PASSED
        ):
            invalid_evidence_present = True
            if receipt.unit_ref in required:
                invalid_units.add(receipt.unit_ref)
            continue
        by_unit[receipt.unit_ref] = receipt

    missing_units = {
        unit_ref for unit_ref in required if unit_ref not in by_unit
    } | invalid_units
    test_execution_required = plan.full_pytest_required or any(
        command_ref.startswith("command:pytest.")
        or command_ref in TEST_EXECUTION_COMMAND_REFS
        for command_ref in plan.selected_command_refs
    )
    collection_unverified = (
        test_execution_required and plan.test_collection_posture != "collected"
    )
    if collection_unverified:
        missing_units.update(required)
    if invalid_evidence_present:
        missing_units.update(required)
    validated = tuple(
        by_unit[unit_ref].receipt_ref
        for unit_ref in required
        if unit_ref in by_unit and unit_ref not in missing_units
    )
    reason_refs: list[str] = []
    if invalid_evidence_present:
        reason_refs.append("reason-ref:verification:invalid-receipt-binding")
    if collection_unverified:
        reason_refs.append("reason-ref:verification:test-collection-unverified")
    if missing_units:
        reason_refs.append("reason-ref:verification:required-receipt-missing")
        status = VerificationGateStatus.DENIED
    else:
        reason_refs.append(
            "reason-ref:verification:shadow-plan-non-authoritative"
            if plan.shadow_mode
            else "reason-ref:verification:typed-github-proof-unavailable"
        )
        status = VerificationGateStatus.BLOCKED
    merge_gate_satisfied = False
    unsigned = {
        "repository_sha": plan.repository_sha,
        "plan_fingerprint": plan.plan_fingerprint,
        "status": status,
        "required_unit_refs": required,
        "validated_receipt_refs": validated,
        "missing_unit_refs": tuple(sorted(missing_units)),
        "reason_refs": tuple(reason_refs),
        "github_run_ref": github_run_ref,
        "github_gate_satisfied": False,
        "merge_gate_satisfied": merge_gate_satisfied,
    }
    decision = VerificationGateDecision(
        schema_version="uaa_verification_gate_decision.v1",
        decision_ref=(
            "decision:verification:"
            + hashlib.sha256(
                json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        ),
        redaction_status="content_free_refs_hashes_counts_and_durations_only",
        **unsigned,
    )
    decision.validate()
    return decision


def evaluate_verification_gate_v2(
    plan: VerificationPlan,
    receipts: tuple[VerificationReceipt, ...],
    *,
    canonical_units: tuple[VerificationUnit, ...],
    run_manifest: VerificationRunManifest,
    github_proof: VerificationGithubGateProof,
) -> VerificationGateDecision:
    """Evaluate exact typed evidence; never infer GitHub success from a boolean."""

    plan.validate()
    validate_verification_dag(canonical_units)
    canonical_by_ref = {unit.unit_ref: unit for unit in canonical_units}
    if any(unit_ref not in canonical_by_ref for unit_ref in plan.selected_unit_refs):
        raise ValueError("verification plan contains a noncanonical unit")
    if dependency_closed_unit_refs(
        canonical_units, plan.selected_unit_refs
    ) != plan.selected_unit_refs:
        raise ValueError("verification plan unit membership is not dependency closed")
    expected_dependency_state = dependency_state_fingerprint(plan)
    required = plan.selected_unit_refs
    by_unit: dict[str, VerificationReceipt] = {}
    invalid = False
    for receipt in receipts:
        try:
            receipt.validate()
        except (TypeError, ValueError):
            invalid = True
            continue
        if receipt.schema_version != "uaa_verification_receipt.v2":
            invalid = True
            continue
        if receipt.unit_ref in by_unit:
            invalid = True
            continue
        if (
            receipt.unit_ref not in required
            or receipt.plan_fingerprint != plan.plan_fingerprint
            or receipt.repository_sha != plan.repository_sha
            or receipt.dependency_state_fingerprint != expected_dependency_state
            or receipt.platform_fingerprint != plan.platform_fingerprint
            or receipt.command_manifest_fingerprint != plan.command_manifest_fingerprint
            or receipt.verifier_definition_fingerprint
            != plan.verifier_definition_fingerprint
            or receipt.test_collection_fingerprint != plan.test_collection_fingerprint
            or receipt.command_refs
            != canonical_by_ref[receipt.unit_ref].command_refs
            or receipt.proof_equivalence_ref
            != canonical_by_ref[receipt.unit_ref].proof_equivalence_ref
            or receipt.status is not VerificationTerminalStatus.PASSED
        ):
            invalid = True
            continue
        if any(
            command_ref in TYPESCRIPT_EXECUTION_COMMAND_REFS
            for command_ref in receipt.command_refs
        ) and receipt.typescript_project_fingerprint != plan.typescript_project_fingerprint:
            invalid = True
            continue
        by_unit[receipt.unit_ref] = receipt

    missing = tuple(unit_ref for unit_ref in required if unit_ref not in by_unit)
    expected_bindings = tuple(
        (unit_ref, by_unit[unit_ref].receipt_ref)
        for unit_ref in required
        if unit_ref in by_unit
    )
    try:
        run_manifest.validate()
    except (TypeError, ValueError):
        invalid = True
    run_valid = (
        run_manifest.schema_version == "uaa_verification_run.v2"
        and run_manifest.repository_sha == plan.repository_sha
        and run_manifest.plan_fingerprint == plan.plan_fingerprint
        and run_manifest.dependency_state_fingerprint == expected_dependency_state
        and run_manifest.command_manifest_fingerprint
        == plan.command_manifest_fingerprint
        and run_manifest.unit_receipt_bindings == expected_bindings
        and run_manifest.receipt_refs
        == tuple(receipt_ref for _, receipt_ref in expected_bindings)
        and run_manifest.status is VerificationTerminalStatus.PASSED
    )
    if not run_valid:
        invalid = True

    try:
        github_proof.validate()
    except (TypeError, ValueError):
        invalid = True
    github_valid = (
        github_proof.repository_sha == plan.repository_sha
        and github_proof.plan_fingerprint == plan.plan_fingerprint
        and github_proof.run_manifest_fingerprint == run_manifest.run_fingerprint
        and github_proof.command_manifest_fingerprint
        == plan.command_manifest_fingerprint
        and github_proof.status is VerificationTerminalStatus.PASSED
    )
    if not github_valid:
        invalid = True

    if plan.shadow_mode:
        status = VerificationGateStatus.BLOCKED
        reason_refs = ("reason-ref:verification:shadow-plan-non-authoritative",)
    elif invalid or missing:
        status = VerificationGateStatus.DENIED
        reason_refs = ("reason-ref:verification:invalid-typed-proof",)
    else:
        status = VerificationGateStatus.BLOCKED
        reason_refs = (
            "reason-ref:verification:trusted-github-attestation-unavailable",
        )
    merge_gate_satisfied = False
    validated_receipt_refs = tuple(
        by_unit[unit_ref].receipt_ref
        for unit_ref in required
        if unit_ref in by_unit and unit_ref not in missing
    )
    unsigned = {
        "repository_sha": plan.repository_sha,
        "plan_fingerprint": plan.plan_fingerprint,
        "status": status,
        "required_unit_refs": required,
        "validated_receipt_refs": validated_receipt_refs,
        "missing_unit_refs": missing,
        "reason_refs": reason_refs,
        "github_run_ref": github_proof.github_run_ref,
        "github_gate_satisfied": False,
        "merge_gate_satisfied": merge_gate_satisfied,
        "github_proof_ref": github_proof.proof_ref,
        "run_manifest_ref": run_manifest.run_ref,
    }
    decision = VerificationGateDecision(
        schema_version="uaa_verification_gate_decision.v2",
        decision_ref=f"decision:verification:{'0' * 64}",
        redaction_status="content_free_refs_hashes_counts_and_durations_only",
        **unsigned,
    )
    decision = replace(
        decision,
        decision_ref=(
            "decision:verification:"
            + verification_gate_decision_fingerprint(decision)
        ),
    )
    decision.validate()
    return decision
