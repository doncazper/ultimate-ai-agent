from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from scripts.verification.pytest_shard_plan import CANONICAL_PYTEST_SHARD_COUNT


SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,159}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_INFRASTRUCTURE_REASONS = frozenset(
    {
        "reason-ref:github:api-unavailable",
        "reason-ref:github:prestart-failure",
        "reason-ref:github:runner-capacity",
        "reason-ref:github:runner-lost-before-checkout",
        "reason-ref:github:superseded-churn",
        "reason-ref:github:time-budget-exceeded",
    }
)
CAPACITY_REASON = "reason-ref:github:runner-capacity"
CAPACITY_COOLDOWN_SECONDS = 180
MAX_PRIVATE_PASSES = 2
MAX_FINAL_GITHUB_RETRIES = 1
MAX_LEDGER_RECORDS = 128
MAX_LEDGER_BYTES = 512 * 1024
QUEUE_BUDGET_MS = 10 * 60 * 1000
CHURN_BUDGET = 2
MAX_DURATION_MS = 24 * 60 * 60 * 1000
INFRASTRUCTURE_WINDOW = timedelta(minutes=30)
GITHUB_QUEUE_STATUSES = frozenset({"requested", "waiting", "pending", "queued"})
GITHUB_ACTIVE_STATUSES = frozenset({*GITHUB_QUEUE_STATUSES, "in_progress"})
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
PYTEST_SHARD_EVIDENCE_FIELDS = frozenset(
    {
        "pytest_shard_evidence_status",
        "pytest_shard_plan_fingerprint_ref",
        "pytest_shard_count",
        "failed_shard_count",
        "failed_shard_refs",
    }
)
CI_COMMAND_RESULT_FIELDS = frozenset(
    {
        "command_ref",
        "category",
        "status",
        "started_at",
        "completed_at",
        "duration_ms",
        "output_byte_count",
        "output_digest",
        "result_ref",
        "reason_ref",
        "redaction_status",
        *PYTEST_SHARD_EVIDENCE_FIELDS,
    }
)
PASS_COMMAND_RESULT_FIELDS = frozenset(
    {
        "command_ref",
        "category",
        "status",
        "started_at",
        "completed_at",
        "duration_ms",
        "output_byte_count",
        "output_digest",
        "result_ref",
        "redaction_status",
    }
)
POSTURE_COMMAND_RESULT_FIELDS = frozenset(
    {
        "command_ref",
        "category",
        "status",
        "duration_ms",
        "reason_ref",
        "result_ref",
        "redaction_status",
    }
)


def has_valid_pytest_shard_evidence(
    result: dict[str, object],
    *,
    lane_ref: str,
    expected_plan_ref: str,
) -> bool:
    present_fields = set(result) & PYTEST_SHARD_EVIDENCE_FIELDS
    is_shard_command = (
        lane_ref == "ci-pytest-shards"
        and result.get("command_ref") == "command:pytest.sharded-suite"
    )
    if not is_shard_command:
        return not present_fields
    return (
        present_fields == PYTEST_SHARD_EVIDENCE_FIELDS
        and result.get("pytest_shard_evidence_status") == "available"
        and result.get("pytest_shard_plan_fingerprint_ref") == expected_plan_ref
        and result.get("pytest_shard_count") == CANONICAL_PYTEST_SHARD_COUNT
        and result.get("failed_shard_count") == 0
        and result.get("failed_shard_refs") == []
    )


def has_valid_command_result_evidence(
    result: dict[str, object],
    *,
    lane_ref: str,
    repository_sha: str,
    expected_category: str,
    expected_pytest_plan_ref: str,
    satisfied_by_dependency: bool,
) -> bool:
    command_ref = result.get("command_ref")
    result_ref = result.get("result_ref")
    if (
        not isinstance(command_ref, str)
        or result.get("category") != expected_category
        or result.get("redaction_status") != "content_free_output_metadata_only"
        or not isinstance(result_ref, str)
        or SAFE_REF_PATTERN.fullmatch(result_ref) is None
        or set(result) - CI_COMMAND_RESULT_FIELDS
    ):
        return False
    if satisfied_by_dependency:
        expected_ref = (
            "result-ref:ci:"
            + hashlib.sha256(
                (repository_sha + command_ref + lane_ref).encode()
            ).hexdigest()
        )
        return (
            set(result) == POSTURE_COMMAND_RESULT_FIELDS - {"reason_ref"}
            and result.get("status") == "satisfied_by_required_dependency"
            and result.get("duration_ms") == 0
            and result_ref == expected_ref
            and has_valid_pytest_shard_evidence(
                result,
                lane_ref=lane_ref,
                expected_plan_ref=expected_pytest_plan_ref,
            )
        )
    status = result.get("status")
    if status in {"skipped", "not_applicable"}:
        reason_ref = result.get("reason_ref")
        expected_posture = {
            "command:frontend.visual-regression": (
                "not_applicable",
                "reason-ref:visual-regression:not-affected",
            ),
            "command:desktop-packaging.proof": (
                "skipped",
                "reason-ref:github-hosted-macos-docker-unavailable",
            ),
        }.get(command_ref)
        expected_ref = (
            "result-ref:ci:"
            + hashlib.sha256(
                (repository_sha + command_ref + str(reason_ref)).encode()
            ).hexdigest()
        )
        return (
            set(result) == POSTURE_COMMAND_RESULT_FIELDS
            and (status, reason_ref) == expected_posture
            and result.get("duration_ms") == 0
            and result_ref == expected_ref
            and has_valid_pytest_shard_evidence(
                result,
                lane_ref=lane_ref,
                expected_plan_ref=expected_pytest_plan_ref,
            )
        )
    expected_fields = PASS_COMMAND_RESULT_FIELDS | (
        PYTEST_SHARD_EVIDENCE_FIELDS
        if command_ref == "command:pytest.sharded-suite"
        else frozenset()
    )
    duration_ms = result.get("duration_ms")
    output_bytes = result.get("output_byte_count")
    output_digest = result.get("output_digest")
    if (
        set(result) != expected_fields
        or status != "pass"
        or not has_valid_timing_window(
            result.get("started_at"), result.get("completed_at"), duration_ms
        )
        or not isinstance(output_bytes, int)
        or isinstance(output_bytes, bool)
        or not 0 <= output_bytes <= 32 * 1024 * 1024
        or not isinstance(output_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", output_digest) is None
    ):
        return False
    expected_ref = (
        "result-ref:ci:"
        + hashlib.sha256(
            "|".join(
                (command_ref, repository_sha, "0", output_digest, str(duration_ms))
            ).encode()
        ).hexdigest()
    )
    return result_ref == expected_ref and has_valid_pytest_shard_evidence(
        result,
        lane_ref=lane_ref,
        expected_plan_ref=expected_pytest_plan_ref,
    )


def has_valid_timing_window(
    started_at: object, completed_at: object, duration_ms: object
) -> bool:
    if (
        not isinstance(started_at, str)
        or not isinstance(completed_at, str)
        or not isinstance(duration_ms, int)
        or isinstance(duration_ms, bool)
        or not 0 <= duration_ms <= MAX_DURATION_MS
    ):
        return False
    try:
        validate_utc_timestamp(started_at)
        validate_utc_timestamp(completed_at)
    except ValueError:
        return False
    return datetime.fromisoformat(completed_at.replace("Z", "+00:00")) >= (
        datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    )


def validate_utc_timestamp(value: str) -> None:
    if not UTC_TIMESTAMP_PATTERN.fullmatch(value):
        raise ValueError("CI timestamp must be bounded canonical UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("CI timestamp must be bounded canonical UTC") from exc
    if parsed.tzinfo != UTC:
        raise ValueError("CI timestamp must be UTC")


class FallbackState(StrEnum):
    GITHUB_PRIMARY = "github_primary"
    GITHUB_RUNNING = "github_running"
    GITHUB_GREEN = "github_green"
    GITHUB_CODE_FAILURE = "github_code_failure"
    GITHUB_INFRASTRUCTURE_BLOCKED = "github_infrastructure_blocked"
    PRIVATE_DIAGNOSIS = "private_diagnosis"
    PRIVATE_VERIFYING = "private_verifying"
    PRIVATE_GREEN_PENDING_GITHUB = "private_green_pending_github"
    PRIVATE_FAILURE = "private_failure"
    GITHUB_FINAL_RETRY = "github_final_retry"
    EXTERNALLY_BLOCKED = "externally_blocked"


@dataclass(frozen=True)
class GitHubObservation:
    repository_sha: str
    run_ref: str
    status: str
    conclusion: str
    repository_command_started: bool
    reason_ref: str
    attempt: int = 1
    queue_duration_ms: int = 0
    install_duration_ms: int = 0
    test_duration_ms: int = 0
    release_lane_duration_ms: int = 0
    superseded_run_count: int = 0
    manifest_version: str = ""
    manifest_fingerprint: str = ""
    manifest_attested: bool = False
    observation_source: str = "injected_simulation"
    run_created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    observed_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )

    def validate(self) -> None:
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("GitHub observation requires an exact lowercase SHA")
        for value in (self.run_ref, self.reason_ref):
            if not SAFE_REF_PATTERN.fullmatch(value):
                raise ValueError("GitHub observation contains an unsafe ref")
        if self.manifest_version and not SAFE_REF_PATTERN.fullmatch(
            self.manifest_version
        ):
            raise ValueError("GitHub observation contains an unsafe manifest version")
        if self.manifest_fingerprint and not re.fullmatch(
            r"[0-9a-f]{64}", self.manifest_fingerprint
        ):
            raise ValueError(
                "GitHub observation contains an unsafe manifest fingerprint"
            )
        if self.observation_source not in {"live_github", "injected_simulation"}:
            raise ValueError("GitHub observation source is invalid")
        if not isinstance(self.manifest_attested, bool) or not isinstance(
            self.repository_command_started, bool
        ):
            raise ValueError("GitHub observation posture is invalid")
        validate_utc_timestamp(self.observed_at)
        validate_utc_timestamp(self.run_created_at)
        if self.status not in {*GITHUB_ACTIVE_STATUSES, "completed", "unavailable"}:
            raise ValueError("unsupported GitHub status")
        if self.conclusion not in {
            "",
            "success",
            "failure",
            "cancelled",
            "startup_failure",
            "timed_out",
            "stale",
            "action_required",
        }:
            raise ValueError("unsupported GitHub conclusion")
        for duration in (
            self.queue_duration_ms,
            self.install_duration_ms,
            self.test_duration_ms,
            self.release_lane_duration_ms,
        ):
            if duration < 0 or duration > MAX_DURATION_MS:
                raise ValueError("GitHub durations must be bounded non-negative values")
        if (
            self.attempt < 1
            or self.attempt > 10
            or self.superseded_run_count < 0
            or self.superseded_run_count > 50
        ):
            raise ValueError("GitHub attempt counts must be bounded positive values")


@dataclass(frozen=True)
class PrivateVerificationScope:
    """Exact, non-authoritative work admitted to private CI diagnosis."""

    schema_version: str
    repository_sha: str
    base_sha: str
    source_branch_binding_ref: str
    authoritative_plan_fingerprint: str
    plan_fingerprint: str
    dependency_state_fingerprint: str
    risk_tier: str
    selected_unit_refs: tuple[str, ...]
    selected_command_refs: tuple[str, ...]
    diagnostic_unit_refs: tuple[str, ...]
    deferred_unit_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]
    redaction_status: str = "content_free_refs_hashes_and_statuses_only"

    def validate(self) -> None:
        if self.schema_version != "uaa_ci_private_scope.v1":
            raise ValueError("unsupported private verification scope schema")
        if not SHA_PATTERN.fullmatch(self.repository_sha) or not SHA_PATTERN.fullmatch(
            self.base_sha
        ):
            raise ValueError("private verification scope requires exact SHAs")
        if re.fullmatch(
            r"branch-binding-ref:private-ci:[0-9a-f]{64}",
            self.source_branch_binding_ref,
        ) is None:
            raise ValueError("private verification scope branch binding is unsafe")
        for value in (
            self.authoritative_plan_fingerprint,
            self.plan_fingerprint,
            self.dependency_state_fingerprint,
        ):
            if re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError("private verification scope contains an unsafe fingerprint")
        if self.risk_tier not in {"tier_0", "tier_1", "tier_2", "tier_3"}:
            raise ValueError("private verification scope risk tier is invalid")
        bounded_refs = (
            ("selected units", self.selected_unit_refs, 128),
            ("selected commands", self.selected_command_refs, 256),
            (
                "diagnostic units",
                self.diagnostic_unit_refs,
                CANONICAL_PYTEST_SHARD_COUNT,
            ),
            ("deferred units", self.deferred_unit_refs, 128),
            ("reasons", self.reason_refs, 128),
        )
        for label, values, limit in bounded_refs:
            if (
                not isinstance(values, tuple)
                or len(values) > limit
                or len(values) != len(set(values))
                or any(SAFE_REF_PATTERN.fullmatch(value) is None for value in values)
            ):
                raise ValueError(f"private verification scope {label} are unsafe")
        if not self.selected_unit_refs or not self.selected_command_refs:
            raise ValueError("private verification scope must select bounded work")
        if set(self.selected_unit_refs).intersection(self.deferred_unit_refs):
            raise ValueError("private verification selected and deferred units overlap")
        allowed_diagnostics = {
            f"diagnostic-pytest-shard-{index}"
            for index in range(CANONICAL_PYTEST_SHARD_COUNT)
        }
        if not set(self.diagnostic_unit_refs).issubset(
            set(self.selected_unit_refs).intersection(allowed_diagnostics)
        ):
            raise ValueError("private verification diagnostics are not exact shard refs")
        if set(self.selected_unit_refs).intersection(
            {"pytest-shards", "pytest", "control-center-frontend"}
        ) or set(self.selected_command_refs).intersection(
            {
                "command:pytest.sharded-suite",
                "command:frontend.typecheck",
                "command:frontend.check",
            }
        ):
            raise ValueError("private verification scope contains a complete singleton")
        from scripts.verification.ci_command_manifest import VERIFICATION_DAG

        units_by_ref = {unit.unit_ref: unit for unit in VERIFICATION_DAG}
        try:
            units = tuple(units_by_ref[unit_ref] for unit_ref in self.selected_unit_refs)
        except KeyError as exc:
            raise ValueError("private verification scope contains an unknown unit") from exc
        expected_commands = tuple(
            dict.fromkeys(
                command_ref for unit in units for command_ref in unit.command_refs
            )
        )
        if expected_commands != self.selected_command_refs or any(
            unit.unit_kind.value in {"aggregate", "audit"}
            or "private" not in unit.execution_surfaces
            or "resource-ref:complete-pytest" in unit.exclusive_resource_refs
            or "resource-ref:typescript-typecheck" in unit.exclusive_resource_refs
            for unit in units
        ):
            raise ValueError("private verification scope is not canonical focused work")
        if self.redaction_status != "content_free_refs_hashes_and_statuses_only":
            raise ValueError("private verification scope redaction status is unsafe")


@dataclass(frozen=True)
class PrivateVerificationResult:
    repository_sha: str
    base_sha: str
    source_branch_binding_ref: str
    authoritative_plan_fingerprint: str
    plan_fingerprint: str
    dependency_state_fingerprint: str
    selected_unit_refs: tuple[str, ...]
    diagnostic_unit_refs: tuple[str, ...]
    deferred_unit_refs: tuple[str, ...]
    status: str
    receipt_ref: str
    command_result_refs: tuple[str, ...]
    timings_ms: tuple[tuple[str, int], ...]
    started_at: str
    completed_at: str
    github_gate_satisfied: bool = False
    merge_gate_satisfied: bool = False
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"

    def validate(self) -> None:
        if not SHA_PATTERN.fullmatch(self.repository_sha) or not SHA_PATTERN.fullmatch(
            self.base_sha
        ):
            raise ValueError("private result requires exact SHAs")
        if re.fullmatch(
            r"branch-binding-ref:private-ci:[0-9a-f]{64}",
            self.source_branch_binding_ref,
        ) is None:
            raise ValueError("private result branch binding is unsafe")
        if self.status not in {"pass", "fail", "cancelled", "recovery_required"}:
            raise ValueError("unsupported private result status")
        for fingerprint in (
            self.authoritative_plan_fingerprint,
            self.plan_fingerprint,
            self.dependency_state_fingerprint,
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                raise ValueError("private result contains an unsafe fingerprint")
        for label, refs, limit in (
            ("selected units", self.selected_unit_refs, 128),
            ("diagnostic units", self.diagnostic_unit_refs, 8),
            ("deferred units", self.deferred_unit_refs, 128),
        ):
            if (
                not isinstance(refs, tuple)
                or len(refs) > limit
                or len(refs) != len(set(refs))
                or any(SAFE_REF_PATTERN.fullmatch(ref) is None for ref in refs)
            ):
                raise ValueError(f"private result {label} are unsafe")
        if not set(self.diagnostic_unit_refs).issubset(self.selected_unit_refs):
            raise ValueError("private result diagnostics are outside its exact scope")
        if set(self.selected_unit_refs).intersection(self.deferred_unit_refs):
            raise ValueError("private result selected and deferred units overlap")
        if self.github_gate_satisfied is not False or self.merge_gate_satisfied is not False:
            raise ValueError("private result cannot satisfy an authoritative gate")
        if (
            self.redaction_status
            != "content_free_refs_hashes_counts_and_durations_only"
        ):
            raise ValueError("private result redaction status is unsafe")
        if len(self.command_result_refs) > MAX_LEDGER_RECORDS:
            raise ValueError("private result exceeds its command-result bound")
        if len(self.timings_ms) > MAX_LEDGER_RECORDS:
            raise ValueError("private result exceeds its timing bound")
        if (
            not self.receipt_ref.startswith("receipt-ref:private-ci:")
            or re.fullmatch(
                r"[0-9a-f]{64}",
                self.receipt_ref.removeprefix("receipt-ref:private-ci:"),
            )
            is None
        ):
            raise ValueError("private result receipt is not content-bound")
        for value in self.command_result_refs:
            if (
                not value.startswith("result-ref:ci:")
                or re.fullmatch(
                    r"[0-9a-f]{64}", value.removeprefix("result-ref:ci:")
                )
                is None
            ):
                raise ValueError("private result contains a non-content-bound result ref")
        for command_ref, duration_ms in self.timings_ms:
            if (
                not SAFE_REF_PATTERN.fullmatch(command_ref)
                or duration_ms < 0
                or duration_ms > MAX_DURATION_MS
            ):
                raise ValueError("private result contains unsafe timing data")
        validate_utc_timestamp(self.started_at)
        validate_utc_timestamp(self.completed_at)
        expected_receipt_ref = (
            "receipt-ref:private-ci:"
            + hashlib.sha256(
                json.dumps(
                    {
                        key: value
                        for key, value in asdict(self).items()
                        if key != "receipt_ref"
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("private result receipt does not bind its exact result")


@dataclass(frozen=True)
class ControllerStatus:
    strategy: str
    state: FallbackState
    repository_sha: str
    manifest_version: str
    manifest_fingerprint: str
    github_run_ref: str
    reason_refs: tuple[str, ...]
    commands_completed: int
    remaining_gate: str
    github_attempt_count: int
    private_attempt_count: int
    duration_ms: int
    github_gate_satisfied: bool
    merge_gate_satisfied: bool
    timing_warning_refs: tuple[str, ...] = ()
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"


class PrivateExecutor(Protocol):
    def prepare_scope(
        self,
        repository_sha: str,
        *,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> PrivateVerificationScope: ...

    def verify(
        self,
        repository_sha: str,
        *,
        series_ref: str,
        scope: PrivateVerificationScope,
    ) -> PrivateVerificationResult: ...


def classify_github(observation: GitHubObservation) -> FallbackState:
    observation.validate()
    if observation.status == "completed" and observation.conclusion == "success":
        from scripts.verification.ci_command_manifest import (
            SCHEMA_VERSION,
            definition_fingerprint,
        )

        if (
            observation.observation_source != "live_github"
            or not observation.manifest_attested
            or observation.manifest_version != SCHEMA_VERSION
            or observation.manifest_fingerprint != definition_fingerprint()
        ):
            return FallbackState.GITHUB_CODE_FAILURE
        return FallbackState.GITHUB_GREEN
    if observation.status in GITHUB_ACTIVE_STATUSES:
        if (
            observation.queue_duration_ms > QUEUE_BUDGET_MS
            or observation.superseded_run_count >= CHURN_BUDGET
        ):
            return FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
        return FallbackState.GITHUB_RUNNING
    if observation.status == "unavailable":
        return FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
    if observation.repository_command_started:
        return FallbackState.GITHUB_CODE_FAILURE
    if (
        observation.conclusion in {"failure", "startup_failure", "stale"}
        and observation.reason_ref in ALLOWED_INFRASTRUCTURE_REASONS
    ):
        return FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
    if (
        observation.conclusion == "cancelled"
        and observation.reason_ref == "reason-ref:github:superseded-churn"
        and observation.superseded_run_count >= CHURN_BUDGET
    ):
        return FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
    return FallbackState.GITHUB_CODE_FAILURE


def status_payload(status: ControllerStatus) -> dict[str, object]:
    return asdict(status)
