from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.verification.ci_fallback_controller import (
    CAPACITY_COOLDOWN_SECONDS,
    AttemptLedger,
    FallbackController,
    FallbackState,
    FullSuiteLock,
    GitHubObservation,
    PrivateVerificationScope,
    PrivateVerificationResult,
    _safe_subprocess,
    classify_github,
    status_payload,
)
from scripts.verification.ci_command_manifest import (
    SCHEMA_VERSION,
    definition_fingerprint,
)
from scripts.verification.ci_fallback_storage import (
    FULL_SUITE_ATTEMPT_PATH,
    FULL_SUITE_LOCK_PATH,
    TYPESCRIPT_TYPECHECK_ATTEMPT_PATH,
    FullSuiteAttemptAlreadyRecordedError,
    full_suite_resource_paths,
)
from scripts.verification.ci_fallback_execution import RemoteHeadAttestationError
from scripts.verification.ci_fallback_private_scope import (
    PrivateScopeFullGateRequiredError,
)


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
BASE_SHA = "f" * 40
SOURCE_BRANCH_BINDING_REF = "branch-binding-ref:private-ci:" + "b" * 64
RESOURCE_ATTEMPT_A = "1" * 64
RESOURCE_ATTEMPT_B = "2" * 64


def private_scope(
    repository_sha: str,
    diagnostics: tuple[str, ...] = (),
) -> PrivateVerificationScope:
    return PrivateVerificationScope(
        schema_version="uaa_ci_private_scope.v1",
        repository_sha=repository_sha,
        base_sha=BASE_SHA,
        source_branch_binding_ref=SOURCE_BRANCH_BINDING_REF,
        authoritative_plan_fingerprint="a" * 64,
        plan_fingerprint="d" * 64,
        dependency_state_fingerprint="c" * 64,
        risk_tier="tier_3",
        selected_unit_refs=("risk-diff-check", *diagnostics),
        selected_command_refs=(
            "command:git.diff-check",
            *(
                f"command:pytest.shard-{ref.rsplit('-', 1)[-1]}-reproduce"
                for ref in diagnostics
            ),
        ),
        diagnostic_unit_refs=diagnostics,
        deferred_unit_refs=("pytest-shards", "control-center-frontend"),
        reason_refs=("reason-ref:private-ci:github-final-gate-required",),
    )


class FakeExecutor:
    def __init__(
        self,
        statuses: list[str] | None = None,
        *,
        wrong_sha: bool = False,
        wrong_plan: bool = False,
        timings: list[int] | None = None,
    ) -> None:
        self.statuses = list(statuses or ["pass"])
        self.calls: list[str] = []
        self.wrong_sha = wrong_sha
        self.wrong_plan = wrong_plan
        self.timings = list(timings or [100] * len(self.statuses))
        self.prepared_diagnostics: list[tuple[str, ...]] = []

    def prepare_scope(
        self,
        repository_sha: str,
        *,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> PrivateVerificationScope:
        self.prepared_diagnostics.append(diagnostic_unit_refs)
        return private_scope(repository_sha, diagnostic_unit_refs)

    def verify(
        self,
        repository_sha: str,
        *,
        series_ref: str,
        scope: PrivateVerificationScope,
    ) -> PrivateVerificationResult:
        del series_ref
        self.calls.append(repository_sha)
        status = self.statuses.pop(0)
        duration_ms = self.timings.pop(0)
        result_sha = SHA_B if self.wrong_sha else repository_sha
        result = PrivateVerificationResult(
            repository_sha=result_sha,
            base_sha=scope.base_sha,
            source_branch_binding_ref=scope.source_branch_binding_ref,
            authoritative_plan_fingerprint=scope.authoritative_plan_fingerprint,
            plan_fingerprint=("e" if self.wrong_plan else "d") * 64,
            dependency_state_fingerprint=scope.dependency_state_fingerprint,
            selected_unit_refs=scope.selected_unit_refs,
            diagnostic_unit_refs=scope.diagnostic_unit_refs,
            deferred_unit_refs=scope.deferred_unit_refs,
            status=status,
            receipt_ref="receipt-ref:private-ci:" + "0" * 64,
            command_result_refs=("result-ref:ci:" + "1" * 64,),
            timings_ms=(("lane-ref:test", duration_ms),),
            started_at="2026-01-01T00:00:00Z",
            completed_at="2026-01-01T00:00:01Z",
        )
        payload = {
            key: value for key, value in asdict(result).items() if key != "receipt_ref"
        }
        return replace(
            result,
            receipt_ref=(
                "receipt-ref:private-ci:"
                + hashlib.sha256(
                    json.dumps(
                        payload, sort_keys=True, separators=(",", ":")
                    ).encode()
                ).hexdigest()
            ),
        )


class UnavailableRemoteExecutor(FakeExecutor):
    def prepare_scope(
        self,
        repository_sha: str,
        *,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> PrivateVerificationScope:
        del repository_sha, diagnostic_unit_refs
        raise RemoteHeadAttestationError(
            "reason-ref:private-ci:remote-attestation-unavailable"
        )


class FullGateRequiredExecutor(FakeExecutor):
    def prepare_scope(
        self,
        repository_sha: str,
        *,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> PrivateVerificationScope:
        del repository_sha, diagnostic_unit_refs
        raise PrivateScopeFullGateRequiredError(
            ("reason-ref:affected:unknown-path",)
        )


class RemoteLostBeforeVerifyExecutor(FakeExecutor):
    def verify(
        self,
        repository_sha: str,
        *,
        series_ref: str,
        scope: PrivateVerificationScope,
    ) -> PrivateVerificationResult:
        del repository_sha, series_ref, scope
        raise RemoteHeadAttestationError(
            "reason-ref:private-ci:remote-attestation-unavailable"
        )


class UnexpectedFailureExecutor(FakeExecutor):
    def verify(
        self,
        repository_sha: str,
        *,
        series_ref: str,
        scope: PrivateVerificationScope,
    ) -> PrivateVerificationResult:
        del repository_sha, series_ref, scope
        self.calls.append(SHA_A)
        raise RuntimeError("unsafe failure detail from /private/secret/path")


def observation(
    *,
    sha: str = SHA_A,
    status: str = "completed",
    conclusion: str = "success",
    started: bool = True,
    reason: str = "reason-ref:github:exact-sha-green",
    superseded: int = 0,
    queue_ms: int = 0,
) -> GitHubObservation:
    return GitHubObservation(
        repository_sha=sha,
        run_ref="run-ref:github:test",
        status=status,
        conclusion=conclusion,
        repository_command_started=started,
        reason_ref=reason,
        superseded_run_count=superseded,
        queue_duration_ms=queue_ms,
        manifest_version=SCHEMA_VERSION,
        manifest_fingerprint=definition_fingerprint(),
        manifest_attested=True,
        observation_source="live_github",
    )


def controller(
    tmp_path: Path,
    executor: FakeExecutor,
    *,
    sleeper=lambda _seconds: None,
) -> FallbackController:
    return FallbackController(
        AttemptLedger(tmp_path / "ledger"),
        executor,
        sleeper=sleeper,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_github_green_never_invokes_private_fallback(tmp_path: Path) -> None:
    executor = FakeExecutor()
    status = controller(tmp_path, executor).evaluate(
        observation(), series_ref="series-ref:ci:test"
    )
    assert status.state == FallbackState.GITHUB_GREEN
    assert status.merge_gate_satisfied is True
    assert executor.calls == []


def test_prestart_infrastructure_failure_invokes_private_but_cannot_merge(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    status = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:test",
    )
    assert status.state == FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    assert status.github_gate_satisfied is False
    assert status.merge_gate_satisfied is False
    assert executor.calls == [SHA_A]


def test_live_remote_attestation_unavailable_is_externally_blocked(
    tmp_path: Path,
) -> None:
    executor = UnavailableRemoteExecutor()

    status = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:remote-unavailable",
    )

    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert status.github_gate_satisfied is False
    assert status.merge_gate_satisfied is False
    assert (
        "reason-ref:private-ci:remote-attestation-unavailable"
        in status.reason_refs
    )
    assert executor.calls == []


def test_private_full_gate_requirement_is_safe_and_externally_blocked(
    tmp_path: Path,
) -> None:
    status = controller(tmp_path, FullGateRequiredExecutor()).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:full-gate-required",
    )

    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:full-gate-required" in status.reason_refs
    assert "reason-ref:affected:unknown-path" in status.reason_refs


def test_remote_attestation_loss_before_private_start_is_externally_blocked(
    tmp_path: Path,
) -> None:
    executor = RemoteLostBeforeVerifyExecutor()

    status = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:remote-lost",
    )

    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert status.github_gate_satisfied is False
    assert status.merge_gate_satisfied is False
    assert (
        "reason-ref:private-ci:remote-attestation-unavailable"
        in status.reason_refs
    )
    terminal = AttemptLedger(tmp_path / "ledger").read()[-1]
    assert terminal["status"] == "recovery_required"
    assert terminal["source_branch_binding_ref"] == SOURCE_BRANCH_BINDING_REF


def test_unexpected_executor_failure_after_start_is_redacted_and_terminal(
    tmp_path: Path,
) -> None:
    executor = UnexpectedFailureExecutor()
    sut = controller(tmp_path, executor)
    infrastructure = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )

    status = sut.evaluate(
        infrastructure,
        series_ref="series-ref:ci:unexpected-executor",
    )

    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:executor-recovery-required" in status.reason_refs
    assert "reason-ref:private-ci:recovery-required" in status.reason_refs
    records = AttemptLedger(tmp_path / "ledger").read()
    assert [record["event"] for record in records[-2:]] == [
        "private_start",
        "private_terminal",
    ]
    terminal = records[-1]
    assert terminal["status"] == "recovery_required"
    assert terminal["source_branch_binding_ref"] == SOURCE_BRANCH_BINDING_REF
    serialized = json.dumps((status_payload(status), terminal), sort_keys=True)
    assert "/private/secret/path" not in serialized
    assert "unsafe failure detail" not in serialized

    replay = sut.evaluate(
        infrastructure,
        series_ref="series-ref:ci:unexpected-executor",
    )
    assert replay.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:recovery-required" in replay.reason_refs
    assert executor.calls == [SHA_A]


@pytest.mark.parametrize(
    ("conclusion", "reason"),
    (
        ("failure", "reason-ref:github:repository-command-failed"),
        ("timed_out", "reason-ref:github:repository-command-failed"),
        ("action_required", "reason-ref:github:repository-command-failed"),
    ),
)
def test_code_failure_cannot_be_relabeled_as_infrastructure(
    tmp_path: Path,
    conclusion: str,
    reason: str,
) -> None:
    executor = FakeExecutor()
    result = controller(tmp_path, executor).evaluate(
        observation(conclusion=conclusion, reason=reason),
        series_ref="series-ref:ci:test",
    )
    assert result.state == FallbackState.GITHUB_CODE_FAILURE
    assert executor.calls == []


def test_explicit_failed_shard_diagnosis_is_bounded_and_non_authoritative(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    result = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            reason="reason-ref:github:repository-command-failed",
        ),
        series_ref="series-ref:ci:diagnosis",
        diagnostic_unit_refs=("diagnostic-pytest-shard-3",),
    )

    assert result.state == FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    assert result.github_gate_satisfied is False
    assert result.merge_gate_satisfied is False
    assert (
        "reason-ref:private-ci:explicit-failed-shard-diagnosis"
        in result.reason_refs
    )
    assert executor.prepared_diagnostics == [("diagnostic-pytest-shard-3",)]
    assert executor.calls == [SHA_A]


def test_changed_private_diagnostic_scope_invalidates_prior_private_evidence(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    sut = controller(tmp_path, executor)
    infrastructure = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    assert sut.evaluate(
        infrastructure, series_ref="series-ref:ci:scope-change"
    ).state == FallbackState.PRIVATE_GREEN_PENDING_GITHUB

    changed = sut.evaluate(
        infrastructure,
        series_ref="series-ref:ci:scope-change",
        diagnostic_unit_refs=("diagnostic-pytest-shard-4",),
    )

    assert changed.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:scope-stale" in changed.reason_refs
    assert executor.calls == [SHA_A]


def test_code_failure_repair_requires_new_sha_and_final_github_green(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    sut = controller(tmp_path, executor)
    failed = observation(
        conclusion="failure",
        reason="reason-ref:github:repository-command-failed",
    )
    assert sut.evaluate(failed, series_ref="series-ref:ci:drill-c").state == (
        FallbackState.GITHUB_CODE_FAILURE
    )
    repaired_green = replace(observation(), repository_sha=SHA_B)
    result = sut.evaluate(repaired_green, series_ref="series-ref:ci:drill-c")
    assert result.state == FallbackState.GITHUB_GREEN
    assert result.merge_gate_satisfied is True
    assert executor.calls == []


def test_exact_final_github_green_is_required_after_private_pass(tmp_path: Path) -> None:
    executor = FakeExecutor()
    sut = controller(tmp_path, executor)
    blocked = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    assert sut.evaluate(blocked, series_ref="series-ref:ci:test").state == (
        FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    )
    final = sut.evaluate(observation(), series_ref="series-ref:ci:test")
    assert final.state == FallbackState.GITHUB_GREEN
    assert final.merge_gate_satisfied is True
    assert executor.calls == [SHA_A]


def test_final_github_green_must_start_after_private_terminal(tmp_path: Path) -> None:
    executor = FakeExecutor()
    sut = controller(tmp_path, executor)
    blocked = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    assert sut.evaluate(blocked, series_ref="series-ref:ci:chronology").state == (
        FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    )
    stale_green = replace(
        observation(),
        run_created_at="2025-12-31T23:59:59Z",
    )

    status = sut.evaluate(stale_green, series_ref="series-ref:ci:chronology")

    assert status.state == FallbackState.GITHUB_CODE_FAILURE
    assert status.merge_gate_satisfied is False
    assert "reason-ref:github:final-run-predates-private-ci" in status.reason_refs


def test_green_with_stale_manifest_cannot_satisfy_merge_gate(tmp_path: Path) -> None:
    executor = FakeExecutor()
    stale = replace(observation(), manifest_fingerprint="0" * 64)
    result = controller(tmp_path, executor).evaluate(
        stale, series_ref="series-ref:ci:test"
    )
    assert result.state == FallbackState.GITHUB_CODE_FAILURE
    assert result.merge_gate_satisfied is False
    assert executor.calls == []


def test_changed_sha_invalidates_private_evidence(tmp_path: Path) -> None:
    executor = FakeExecutor(["pass", "pass"])
    sut = controller(tmp_path, executor)
    infra_a = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    infra_b = replace(infra_a, repository_sha=SHA_B)
    assert sut.evaluate(infra_a, series_ref="series-ref:ci:test").state == (
        FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    )
    assert sut.evaluate(infra_b, series_ref="series-ref:ci:test").state == (
        FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    )
    assert executor.calls == [SHA_A, SHA_B]


def test_private_result_for_foreign_sha_is_recovery_required(tmp_path: Path) -> None:
    executor = FakeExecutor(wrong_sha=True)
    status = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:test",
    )
    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:executor-recovery-required" in status.reason_refs


def test_private_result_for_foreign_plan_is_recovery_required(tmp_path: Path) -> None:
    executor = FakeExecutor(wrong_plan=True)
    status = controller(tmp_path, executor).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:test",
    )
    assert status.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:executor-recovery-required" in status.reason_refs


def test_capacity_cooldown_occurs_once_and_is_bounded(tmp_path: Path) -> None:
    sleeps: list[float] = []
    executor = FakeExecutor()
    sut = controller(tmp_path, executor, sleeper=sleeps.append)
    capacity = observation(
        status="queued",
        conclusion="",
        started=False,
        reason="reason-ref:github:runner-capacity",
        queue_ms=11 * 60 * 1000,
    )
    sut.evaluate(capacity, series_ref="series-ref:ci:test")
    sut.evaluate(capacity, series_ref="series-ref:ci:test")
    assert sleeps == [CAPACITY_COOLDOWN_SECONDS]
    assert executor.calls == [SHA_A]


@pytest.mark.parametrize(
    "status", ("requested", "waiting", "pending", "queued", "in_progress")
)
def test_all_github_active_statuses_remain_running(status: str) -> None:
    active = observation(
        status=status,
        conclusion="",
        started=False,
        reason="reason-ref:github:run-active",
    )
    assert classify_github(active) == FallbackState.GITHUB_RUNNING


def test_private_failure_is_not_rerun_for_same_sha(tmp_path: Path) -> None:
    executor = FakeExecutor(["fail", "pass"])
    sut = controller(tmp_path, executor)
    infra = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    assert sut.evaluate(infra, series_ref="series-ref:ci:test").state == (
        FallbackState.PRIVATE_FAILURE
    )
    assert sut.evaluate(infra, series_ref="series-ref:ci:test").state == (
        FallbackState.PRIVATE_FAILURE
    )
    assert executor.calls == [SHA_A]


def test_two_private_repair_passes_cap_the_series(tmp_path: Path) -> None:
    executor = FakeExecutor(["fail", "fail", "pass"])
    sut = controller(tmp_path, executor)
    base = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    assert sut.evaluate(base, series_ref="series-ref:ci:test").state == FallbackState.PRIVATE_FAILURE
    assert sut.evaluate(replace(base, repository_sha=SHA_B), series_ref="series-ref:ci:test").state == FallbackState.PRIVATE_FAILURE
    capped = sut.evaluate(
        replace(base, repository_sha=SHA_C), series_ref="series-ref:ci:test"
    )
    assert capped.state == FallbackState.EXTERNALLY_BLOCKED
    assert executor.calls == [SHA_A, SHA_B]


def test_private_timing_warns_above_same_machine_median_regression(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor(["pass", "pass"], timings=[100, 116])
    sut = controller(tmp_path, executor)
    base = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    sut.evaluate(base, series_ref="series-ref:ci:timing")
    second = sut.evaluate(
        replace(base, repository_sha=SHA_B),
        series_ref="series-ref:ci:timing",
    )
    assert second.state == FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    assert len(second.timing_warning_refs) == 1


def test_crash_after_private_start_requires_recovery_not_replay(tmp_path: Path) -> None:
    ledger = AttemptLedger(tmp_path / "ledger")
    ledger.append(
        {
            "event": "private_start",
            "repository_sha": SHA_A,
            "source_branch_binding_ref": SOURCE_BRANCH_BINDING_REF,
            "series_ref": "series-ref:ci:test",
            "status": "private_verifying",
            "reason_ref": "reason-ref:github:prestart-failure",
        }
    )
    executor = FakeExecutor()
    result = FallbackController(ledger, executor, sleeper=lambda _seconds: None).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:test",
    )
    assert result.state == FallbackState.EXTERNALLY_BLOCKED
    assert "reason-ref:private-ci:recovery-required" in result.reason_refs
    assert executor.calls == []


def test_final_github_retry_is_bounded_then_external_blocked(tmp_path: Path) -> None:
    executor = FakeExecutor()
    sut = controller(tmp_path, executor)
    infra = observation(
        conclusion="failure",
        started=False,
        reason="reason-ref:github:prestart-failure",
    )
    sut.evaluate(infra, series_ref="series-ref:ci:test")
    assert sut.evaluate(infra, series_ref="series-ref:ci:test").state == FallbackState.GITHUB_FINAL_RETRY
    assert sut.evaluate(infra, series_ref="series-ref:ci:test").state == FallbackState.EXTERNALLY_BLOCKED


def test_superseded_churn_classifies_as_infrastructure_only_at_cap() -> None:
    below = observation(
        conclusion="cancelled",
        started=False,
        reason="reason-ref:github:superseded-churn",
        superseded=1,
    )
    capped = replace(below, superseded_run_count=2)
    assert classify_github(below) == FallbackState.GITHUB_CODE_FAILURE
    assert classify_github(capped) == FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED


def test_ledger_rejects_symlink_fifo_corruption_and_tamper(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("[]", encoding="utf-8")
    symlink_dir = tmp_path / "symlink-ledger"
    symlink_dir.mkdir(mode=0o700)
    (symlink_dir / "attempts.v1.json").symlink_to(target)
    with pytest.raises(OSError):
        AttemptLedger(symlink_dir).read()

    fifo_dir = tmp_path / "fifo-ledger"
    fifo_dir.mkdir(mode=0o700)
    os.mkfifo(fifo_dir / "attempts.v1.json")
    with pytest.raises(ValueError, match="unsafe"):
        AttemptLedger(fifo_dir).read()

    corrupt = AttemptLedger(tmp_path / "corrupt-ledger")
    corrupt._prepare_directory()
    corrupt.path.write_text("{", encoding="utf-8")
    corrupt.path.chmod(0o600)
    with pytest.raises(ValueError, match="corrupt"):
        corrupt.read()

    valid = AttemptLedger(tmp_path / "valid-ledger")
    valid.append({"event": "probe", "repository_sha": SHA_A})
    records = json.loads(valid.path.read_text(encoding="utf-8"))
    records[0]["repository_sha"] = SHA_B
    valid.path.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(ValueError, match="hash chain"):
        valid.read()


def test_ledger_migrates_unbound_private_history_as_non_authoritative(
    tmp_path: Path,
) -> None:
    ledger = AttemptLedger(tmp_path / "legacy-ledger")
    ledger._prepare_directory()
    legacy_record = {
        "event": "private_start",
        "repository_sha": SHA_A,
        "series_ref": "series-ref:ci:legacy",
        "status": "private_verifying",
        "reason_ref": "reason-ref:github:prestart-failure",
        "sequence": 1,
        "previous_record_ref": "ledger-ref:ci:genesis",
    }
    legacy_record["record_ref"] = ledger._record_ref(legacy_record)
    ledger.path.write_text(json.dumps([legacy_record]), encoding="utf-8")
    ledger.path.chmod(0o600)

    migrated = ledger.read()

    assert migrated[0]["event"] == "legacy_private_start"
    assert migrated[0]["status"] == "legacy_non_authoritative"
    assert migrated[0]["reason_ref"] == (
        "reason-ref:private-ci:legacy-unbound-history"
    )
    assert migrated[0]["record_ref"] == ledger._record_ref(migrated[0])
    assert ledger.read() == migrated

    executor = FakeExecutor()
    result = FallbackController(
        ledger,
        executor,
        sleeper=lambda _seconds: None,
    ).evaluate(
        observation(
            conclusion="failure",
            started=False,
            reason="reason-ref:github:prestart-failure",
        ),
        series_ref="series-ref:ci:legacy",
    )

    assert result.state == FallbackState.PRIVATE_GREEN_PENDING_GITHUB
    assert executor.calls == [SHA_A]


def test_ledger_rejects_raw_or_unknown_event_fields(tmp_path: Path) -> None:
    ledger = AttemptLedger(tmp_path / "ledger")
    with pytest.raises(ValueError, match="forbidden fields"):
        ledger.append(
            {
                "event": "probe",
                "repository_sha": SHA_A,
                "raw_log": "must-never-persist",
            }
        )
    with pytest.raises(ValueError, match="canonical UTC"):
        ledger.append(
            {
                "event": "probe",
                "repository_sha": SHA_A,
                "observed_at": "secret-material",
            }
        )
    with pytest.raises(ValueError, match="authoritative gate"):
        ledger.append(
            {
                "event": "private_start",
                "repository_sha": SHA_A,
                "merge_gate_satisfied": True,
            }
        )
    with pytest.raises(ValueError, match="scope refs"):
        ledger.append(
            {
                "event": "private_start",
                "repository_sha": SHA_A,
                "selected_unit_refs": ["unsafe/raw/path"],
            }
        )


def test_observations_and_private_results_reject_unsafe_timestamps() -> None:
    with pytest.raises(ValueError, match="canonical UTC"):
        replace(observation(), observed_at="secret-material").validate()
    scope = private_scope(SHA_A)
    result = FakeExecutor().verify(
        SHA_A,
        series_ref="series-ref:ci:test",
        scope=scope,
    )
    with pytest.raises(ValueError, match="canonical UTC"):
        replace(result, completed_at="raw-log-content").validate()


def test_concurrent_private_full_suites_are_denied_and_stale_lock_recovers(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "full-suite.lock"
    assert FullSuiteLock(lock_path).attempt_path == tmp_path / (
        "full-suite.lock.attempts.json"
    )
    with FullSuiteLock(lock_path):
        with pytest.raises(RuntimeError, match="already active"):
            FullSuiteLock(lock_path).__enter__()
    with FullSuiteLock(lock_path):
        pass


def test_independent_resource_classes_have_independent_locks_and_attempt_ledgers(
    tmp_path: Path,
) -> None:
    pytest_lock_path, pytest_attempt_path = full_suite_resource_paths(
        "resource-ref:complete-pytest",
        root=tmp_path,
    )
    typescript_lock_path, typescript_attempt_path = full_suite_resource_paths(
        "resource-ref:typescript-typecheck",
        root=tmp_path,
    )

    assert pytest_lock_path != typescript_lock_path
    assert pytest_attempt_path != typescript_attempt_path
    typescript_lock = FullSuiteLock(
        resource_ref="resource-ref:typescript-typecheck"
    )
    assert typescript_lock.path.name == "typescript-typecheck.lock"
    assert typescript_lock.attempt_path.name == "typescript-typecheck-attempts.json"

    with FullSuiteLock(
        pytest_lock_path,
        attempt_path=pytest_attempt_path,
        resource_ref="resource-ref:complete-pytest",
    ):
        with FullSuiteLock(
            typescript_lock_path,
            attempt_path=typescript_attempt_path,
            resource_ref="resource-ref:typescript-typecheck",
        ):
            pass
        with pytest.raises(RuntimeError, match="already active"):
            FullSuiteLock(
                pytest_lock_path,
                attempt_path=pytest_attempt_path,
                resource_ref="resource-ref:complete-pytest",
            ).__enter__()

    for lock_path, attempt_path, resource_ref, expected_error in (
        (
            pytest_lock_path,
            pytest_attempt_path,
            "resource-ref:typescript-typecheck",
            "lock path does not match resource ref",
        ),
        (
            typescript_lock_path,
            pytest_attempt_path,
            "resource-ref:typescript-typecheck",
            "attempt path does not match resource ref",
        ),
        (
            pytest_lock_path,
            typescript_attempt_path,
            "resource-ref:complete-pytest",
            "attempt path does not match resource ref",
        ),
    ):
        with pytest.raises(ValueError, match=expected_error):
            FullSuiteLock(
                lock_path,
                attempt_path=attempt_path,
                resource_ref=resource_ref,
            )

    for resource_ref, lock_path, attempt_path in (
        (
            "resource-ref:complete-pytest",
            pytest_lock_path,
            pytest_attempt_path,
        ),
        (
            "resource-ref:typescript-typecheck",
            typescript_lock_path,
            typescript_attempt_path,
        ),
    ):
        with FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="local",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempt_path,
            resource_ref=resource_ref,
        ) as resource_lock:
            resource_lock.ensure_start_available()
            resource_lock.record_start()

    with pytest.raises(FullSuiteAttemptAlreadyRecordedError):
        with FullSuiteLock(
            pytest_lock_path,
            repository_sha=SHA_A,
            attempt_scope="local",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=pytest_attempt_path,
            resource_ref="resource-ref:complete-pytest",
        ) as pytest_lock:
            pytest_lock.ensure_start_available()

    with pytest.raises(ValueError, match="attempt path does not match resource ref"):
        with FullSuiteLock(
            typescript_lock_path,
            repository_sha=SHA_A,
            attempt_scope="local",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_B,
            attempt_path=pytest_attempt_path,
            resource_ref="resource-ref:typescript-typecheck",
        ) as substituted_lock:
            substituted_lock.ensure_start_available()


def test_full_suite_resource_paths_reject_unknown_resources(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="resource ref is invalid"):
        full_suite_resource_paths("resource-ref:unknown", root=tmp_path)


def test_canonical_resource_paths_cannot_be_cross_bound() -> None:
    with pytest.raises(ValueError, match="lock path does not match resource ref"):
        FullSuiteLock(
            FULL_SUITE_LOCK_PATH,
            resource_ref="resource-ref:typescript-typecheck",
        )
    with pytest.raises(ValueError, match="attempt path does not match resource ref"):
        FullSuiteLock(
            resource_ref="resource-ref:typescript-typecheck",
            attempt_path=FULL_SUITE_ATTEMPT_PATH,
        )
    for attempt_path, resource_ref in (
        (FULL_SUITE_ATTEMPT_PATH, "resource-ref:complete-pytest"),
        (
            TYPESCRIPT_TYPECHECK_ATTEMPT_PATH,
            "resource-ref:typescript-typecheck",
        ),
    ):
        with pytest.raises(ValueError, match="lock path does not match resource ref"):
            FullSuiteLock(
                attempt_path.with_name("custom.lock"),
                attempt_path=attempt_path,
                resource_ref=resource_ref,
            )


def test_aliased_canonical_attempt_paths_cannot_use_custom_locks(
    tmp_path: Path,
) -> None:
    dotdot_alias = (
        FULL_SUITE_ATTEMPT_PATH.parent
        / "unused-directory"
        / ".."
        / FULL_SUITE_ATTEMPT_PATH.name
    )
    with pytest.raises(ValueError, match="lock path does not match resource ref"):
        FullSuiteLock(
            tmp_path / "custom.lock",
            attempt_path=dotdot_alias,
            resource_ref="resource-ref:complete-pytest",
            shared_across_accounts=True,
        )

    symlinked_parent = tmp_path / "canonical-ledger-parent"
    try:
        symlinked_parent.symlink_to(
            FULL_SUITE_ATTEMPT_PATH.parent,
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ValueError, match="lock path does not match resource ref"):
        FullSuiteLock(
            tmp_path / "other-custom.lock",
            attempt_path=symlinked_parent / FULL_SUITE_ATTEMPT_PATH.name,
            resource_ref="resource-ref:complete-pytest",
            shared_across_accounts=True,
        )


def test_aliased_canonical_lock_identity_cannot_cross_resources() -> None:
    aliased_lock = (
        FULL_SUITE_LOCK_PATH.parent
        / "unused-directory"
        / ".."
        / FULL_SUITE_LOCK_PATH.name
    )
    with pytest.raises(ValueError, match="lock path does not match resource ref"):
        FullSuiteLock(
            aliased_lock,
            resource_ref="resource-ref:typescript-typecheck",
        )


def test_existing_complete_pytest_attempt_ledger_remains_compatible(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "pytest.lock"
    attempt_path = tmp_path / "attempts.json"
    legacy_record = {
        "repository_sha": SHA_A,
        "attempt_scope": "local",
        "resource_attempt_fingerprint": RESOURCE_ATTEMPT_A,
    }
    legacy_record["attempt_ref"] = "attempt-ref:ci:" + hashlib.sha256(
        json.dumps(
            legacy_record,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    attempt_path.write_text(
        json.dumps([legacy_record], sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    attempt_path.chmod(0o600)

    with pytest.raises(FullSuiteAttemptAlreadyRecordedError):
        with FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="local",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempt_path,
            resource_ref="resource-ref:complete-pytest",
        ) as lock:
            lock.ensure_start_available()


def test_new_complete_pytest_attempt_record_remains_legacy_reader_compatible(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "active.lock"
    attempt_path = tmp_path / "attempts.json"

    with FullSuiteLock(
        lock_path,
        repository_sha=SHA_A,
        attempt_scope="local",
        resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
        attempt_path=attempt_path,
        resource_ref="resource-ref:complete-pytest",
    ) as lock:
        lock.record_start()

    records = json.loads(attempt_path.read_text(encoding="utf-8"))
    assert len(records) == 1
    record = records[0]
    assert set(record) == {
        "repository_sha",
        "attempt_scope",
        "resource_attempt_fingerprint",
        "attempt_ref",
    }
    unhashed = {key: value for key, value in record.items() if key != "attempt_ref"}
    assert record["attempt_ref"] == "attempt-ref:ci:" + hashlib.sha256(
        json.dumps(unhashed, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_typescript_attempt_records_retain_explicit_resource_binding(
    tmp_path: Path,
) -> None:
    lock_path, attempt_path = full_suite_resource_paths(
        "resource-ref:typescript-typecheck",
        root=tmp_path,
    )

    with FullSuiteLock(
        lock_path,
        repository_sha=SHA_A,
        attempt_scope="local",
        resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
        attempt_path=attempt_path,
        resource_ref="resource-ref:typescript-typecheck",
    ) as lock:
        lock.record_start()

    records = json.loads(attempt_path.read_text(encoding="utf-8"))
    assert records[0]["resource_ref"] == "resource-ref:typescript-typecheck"


def test_full_suite_attempt_bound_is_shared_across_local_accounts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_dir = tmp_path / "shared-v3"
    lock_path = shared_dir / "active.lock"
    attempts = shared_dir / "attempts.json"
    with FullSuiteLock(
        lock_path,
        repository_sha=SHA_A,
        attempt_scope="github",
        resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
        attempt_path=attempts,
        shared_across_accounts=True,
    ) as lock:
        lock.record_start()

    first_account_uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: first_account_uid + 1000)

    with pytest.raises(
        FullSuiteAttemptAlreadyRecordedError, match="already attempted"
    ):
        with FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="github",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempts,
            shared_across_accounts=True,
        ) as lock:
            lock.ensure_start_available()

    assert shared_dir.stat().st_mode & 0o777 == 0o770
    assert lock_path.stat().st_mode & 0o777 == 0o660
    assert attempts.stat().st_mode & 0o777 == 0o660


def test_full_suite_attempts_are_bounded_across_execution_planes(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "full-suite.lock"
    attempts = tmp_path / "attempts.json"
    with FullSuiteLock(
        lock_path,
        repository_sha=SHA_A,
        attempt_scope="private",
        resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
        attempt_path=attempts,
    ) as lock:
        lock.record_start()
    with pytest.raises(
        FullSuiteAttemptAlreadyRecordedError, match="already attempted"
    ):
        lock = FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="private",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempts,
        )
        with lock:
            lock.ensure_start_available()
    with pytest.raises(
        FullSuiteAttemptAlreadyRecordedError, match="already attempted"
    ):
        with FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="github",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempts,
        ) as lock:
            lock.ensure_start_available()
    with pytest.raises(FullSuiteAttemptAlreadyRecordedError, match="already attempted"):
        with FullSuiteLock(
            lock_path,
            repository_sha=SHA_A,
            attempt_scope="local",
            resource_attempt_fingerprint=RESOURCE_ATTEMPT_A,
            attempt_path=attempts,
        ) as lock:
            lock.ensure_start_available()

    with FullSuiteLock(
        lock_path,
        repository_sha=SHA_A,
        attempt_scope="github",
        resource_attempt_fingerprint=RESOURCE_ATTEMPT_B,
        attempt_path=attempts,
    ) as lock:
        lock.record_start()


def test_private_process_timeout_reaps_child_process_group(tmp_path: Path) -> None:
    child_pid_file = tmp_path / "child.pid"
    script = (
        "import pathlib,subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_file)!r}).write_text(str(p.pid)); time.sleep(60)"
    )
    returncode, _duration_ms, _result_ref = _safe_subprocess(
        (sys.executable, "-c", script),
        cwd=tmp_path,
        timeout=1,
    )
    assert returncode == 124
    child_pid = int(child_pid_file.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 2
    while True:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        if time.monotonic() >= deadline:
            pytest.fail("timed-out process group was not reaped within the bound")
        time.sleep(0.01)


def test_status_and_receipts_contain_no_raw_logs_paths_env_or_credentials(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    status = controller(tmp_path, executor).evaluate(
        observation(), series_ref="series-ref:ci:test"
    )
    serialized = json.dumps(status_payload(status), sort_keys=True)
    for forbidden in (
        str(tmp_path),
        "raw_log",
        "environment",
        "credential",
        "username",
        "hostname",
    ):
        assert forbidden not in serialized
