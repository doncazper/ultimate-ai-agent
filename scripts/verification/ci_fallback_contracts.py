from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol


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
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
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
            raise ValueError("GitHub observation contains an unsafe manifest fingerprint")
        if self.observation_source not in {"live_github", "injected_simulation"}:
            raise ValueError("GitHub observation source is invalid")
        if not isinstance(self.manifest_attested, bool) or not isinstance(
            self.repository_command_started, bool
        ):
            raise ValueError("GitHub observation posture is invalid")
        validate_utc_timestamp(self.observed_at)
        validate_utc_timestamp(self.run_created_at)
        if self.status not in {"queued", "in_progress", "completed", "unavailable"}:
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
class PrivateVerificationResult:
    repository_sha: str
    plan_fingerprint: str
    status: str
    receipt_ref: str
    command_result_refs: tuple[str, ...]
    timings_ms: tuple[tuple[str, int], ...]
    started_at: str
    completed_at: str
    redaction_status: str = "content_free_refs_hashes_counts_and_durations_only"

    def validate(self) -> None:
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("private result requires an exact SHA")
        if self.status not in {"pass", "fail", "cancelled", "recovery_required"}:
            raise ValueError("unsupported private result status")
        if not re.fullmatch(r"[0-9a-f]{64}", self.plan_fingerprint):
            raise ValueError("private result contains an unsafe plan fingerprint")
        if self.redaction_status != "content_free_refs_hashes_counts_and_durations_only":
            raise ValueError("private result redaction status is unsafe")
        if len(self.command_result_refs) > MAX_LEDGER_RECORDS:
            raise ValueError("private result exceeds its command-result bound")
        if len(self.timings_ms) > MAX_LEDGER_RECORDS:
            raise ValueError("private result exceeds its timing bound")
        for value in (self.receipt_ref, *self.command_result_refs):
            if not SAFE_REF_PATTERN.fullmatch(value):
                raise ValueError("private result contains an unsafe ref")
        for command_ref, duration_ms in self.timings_ms:
            if (
                not SAFE_REF_PATTERN.fullmatch(command_ref)
                or duration_ms < 0
                or duration_ms > MAX_DURATION_MS
            ):
                raise ValueError("private result contains unsafe timing data")
        validate_utc_timestamp(self.started_at)
        validate_utc_timestamp(self.completed_at)


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
    def plan_fingerprint(self, repository_sha: str) -> str:
        ...

    def verify(self, repository_sha: str, *, series_ref: str) -> PrivateVerificationResult:
        ...


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
    if observation.status in {"queued", "in_progress"}:
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
