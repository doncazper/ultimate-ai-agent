from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
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
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


class VerificationRiskTier(StrEnum):
    TIER_0 = "tier_0"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

    @property
    def rank(self) -> int:
        return int(self.value.rsplit("_", maxsplit=1)[-1])


class VerificationUnitKind(StrEnum):
    COMMAND = "command"
    AGGREGATE = "aggregate"
    AUDIT = "audit"


class VerificationTerminalStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class VerificationGateStatus(StrEnum):
    PASSED = "passed"
    DENIED = "denied"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


def _validate_ref(value: str, *, label: str) -> None:
    if SAFE_REF_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a bounded safe ref")


def _validate_digest(value: str, *, label: str) -> None:
    if DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


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
    if parsed.tzinfo != UTC:
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
    force_full: bool
    shadow_mode: bool

    def validate(self) -> None:
        for value, label in (
            (self.schema_version, "verification plan schema version"),
            (self.profile_ref, "verification plan profile ref"),
            (self.affected_path_classification, "affected path classification"),
            (self.risk_manifest_version, "risk manifest version"),
            (self.audit_posture, "verification audit posture"),
            (self.frontend_visual_scope, "frontend visual scope"),
            (self.test_collection_posture, "test collection posture"),
        ):
            _validate_ref(value, label=label)
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

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification receipt schema version")
        _validate_ref(self.receipt_ref, label="verification receipt ref")
        _validate_ref(self.unit_ref, label="verification receipt unit ref")
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

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification run schema version")
        _validate_ref(self.run_ref, label="verification run ref")
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("verification run requires an exact SHA")
        _validate_digest(self.plan_fingerprint, label="run plan fingerprint")
        _validate_digest(self.run_fingerprint, label="run fingerprint")
        _validate_unique_refs(self.receipt_refs, label="run receipt refs")
        if not isinstance(self.status, VerificationTerminalStatus):
            raise ValueError("verification run status is invalid")
        if not 0 < len(self.receipt_refs) <= MAX_RECEIPTS:
            raise ValueError("verification run receipt count is invalid")
        started = _validated_timestamp(self.started_at, label="run start timestamp")
        completed = _validated_timestamp(
            self.completed_at, label="run completion timestamp"
        )
        if completed < started:
            raise ValueError("verification run completion precedes its start")
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("verification run redaction posture is invalid")


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

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification gate schema version")
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
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"

    def validate(self) -> None:
        _validate_ref(self.schema_version, label="verification value schema version")
        for value, label in (
            (self.value_ref, "verification value ref"),
            (self.unit_ref, "verification value unit ref"),
            (self.verifier_ref, "verifier ref"),
            (self.synthetic_mutation_ref, "synthetic mutation ref"),
            (self.defect_ref, "defect ref"),
            (self.receipt_ref, "value receipt ref"),
            (self.overlap_ref, "value overlap ref"),
            (self.disposition, "value disposition"),
        ):
            _validate_ref(value, label=label)
        if self.outcome not in {"killed", "survived", "blocked", "unknown"}:
            raise ValueError("verification value outcome is invalid")
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


def dependency_state_fingerprint(plan: VerificationPlan) -> str:
    import hashlib
    import json

    payload: dict[str, Any] = {
        "locks": plan.dependency_lock_fingerprints,
        "platform": plan.platform_fingerprint,
        "commands": plan.command_manifest_fingerprint,
        "verifiers": plan.verifier_definition_fingerprint,
        "collection": plan.test_collection_fingerprint,
        "pytest_shard_plan": plan.pytest_shard_plan_fingerprint,
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
    import hashlib
    import json

    plan.validate()
    if not isinstance(github_gate_satisfied, bool):
        raise ValueError("GitHub gate posture must be boolean")
    expected_dependency_state = dependency_state_fingerprint(plan)
    required = plan.selected_unit_refs
    by_unit: dict[str, VerificationReceipt] = {}
    invalid_units: set[str] = set()
    for receipt in receipts:
        try:
            receipt.validate()
        except ValueError:
            invalid_units.add(receipt.unit_ref)
            continue
        if receipt.unit_ref in by_unit:
            invalid_units.add(receipt.unit_ref)
            continue
        by_unit[receipt.unit_ref] = receipt
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
            invalid_units.add(receipt.unit_ref)

    missing_units = {
        unit_ref for unit_ref in required if unit_ref not in by_unit
    } | invalid_units
    test_execution_required = plan.full_pytest_required or any(
        command_ref.startswith("command:pytest.")
        for command_ref in plan.selected_command_refs
    )
    collection_unverified = (
        test_execution_required and plan.test_collection_posture != "collected"
    )
    if collection_unverified:
        missing_units.update(required)
    validated = tuple(
        by_unit[unit_ref].receipt_ref
        for unit_ref in required
        if unit_ref in by_unit and unit_ref not in missing_units
    )
    reason_refs: list[str] = []
    if invalid_units:
        reason_refs.append("reason-ref:verification:invalid-receipt-binding")
    if collection_unverified:
        reason_refs.append("reason-ref:verification:test-collection-unverified")
    if missing_units:
        reason_refs.append("reason-ref:verification:required-receipt-missing")
        status = VerificationGateStatus.DENIED
    elif not github_gate_satisfied:
        reason_refs.append("reason-ref:verification:github-gate-pending")
        status = VerificationGateStatus.BLOCKED
    else:
        reason_refs.append("reason-ref:verification:all-required-receipts-valid")
        status = VerificationGateStatus.PASSED
    merge_gate_satisfied = (
        status is VerificationGateStatus.PASSED and github_gate_satisfied
    )
    unsigned = {
        "repository_sha": plan.repository_sha,
        "plan_fingerprint": plan.plan_fingerprint,
        "status": status,
        "required_unit_refs": required,
        "validated_receipt_refs": validated,
        "missing_unit_refs": tuple(sorted(missing_units)),
        "reason_refs": tuple(reason_refs),
        "github_run_ref": github_run_ref,
        "github_gate_satisfied": github_gate_satisfied,
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
