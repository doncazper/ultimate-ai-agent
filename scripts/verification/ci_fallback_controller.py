from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime
from statistics import median
from typing import Any, Callable

from scripts.verification.ci_command_manifest import (
    MACHINE_PROFILE_REF,
    SCHEMA_VERSION,
    definition_fingerprint,
)
from scripts.verification.ci_fallback_contracts import (
    CAPACITY_COOLDOWN_SECONDS,
    CAPACITY_REASON,
    MAX_FINAL_GITHUB_RETRIES,
    MAX_PRIVATE_PASSES,
    SAFE_REF_PATTERN,
    ControllerStatus,
    FallbackState,
    GitHubObservation,
    PrivateExecutor,
    PrivateVerificationScope,
    PrivateVerificationResult,
    classify_github,
    status_payload,
)
from scripts.verification.ci_fallback_execution import (
    IsolatedPrivateExecutor,
    RemoteHeadAttestationError,
    _safe_subprocess,
)
from scripts.verification.ci_fallback_private_scope import (
    PrivateScopeFullGateRequiredError,
)
from scripts.verification.ci_fallback_storage import AttemptLedger, FullSuiteLock


class FallbackController:
    def __init__(
        self,
        ledger: AttemptLedger,
        executor: PrivateExecutor,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.ledger = ledger
        self.executor = executor
        self.sleeper = sleeper
        self.clock = clock

    def _events(self, sha: str, series_ref: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self.ledger.read()
            if record.get("repository_sha") == sha
            or record.get("series_ref") == series_ref
        ]

    @staticmethod
    def _timing_warnings(
        result: PrivateVerificationResult,
        records: list[dict[str, Any]],
    ) -> tuple[str, ...]:
        historical: dict[str, list[int]] = {}
        for record in records:
            if record.get("event") != "private_terminal" or record.get("status") != "pass":
                continue
            for command_ref, duration_ms in record.get("timings_ms", []):
                historical.setdefault(command_ref, []).append(duration_ms)
        warnings: list[str] = []
        for command_ref, duration_ms in result.timings_ms:
            values = historical.get(command_ref, [])
            if values and duration_ms > median(values) * 1.15:
                digest = hashlib.sha256(command_ref.encode()).hexdigest()[:16]
                warnings.append(f"warning-ref:ci-timing-regression:{digest}")
        return tuple(sorted(warnings))

    def evaluate(
        self,
        observation: GitHubObservation,
        *,
        series_ref: str,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> ControllerStatus:
        started = time.perf_counter()
        observation.validate()
        if not SAFE_REF_PATTERN.fullmatch(series_ref):
            raise ValueError("unsafe CI fallback series ref")
        allowed_diagnostics = {
            f"diagnostic-pytest-shard-{index}" for index in range(8)
        }
        if (
            not isinstance(diagnostic_unit_refs, tuple)
            or len(diagnostic_unit_refs) != len(set(diagnostic_unit_refs))
            or not set(diagnostic_unit_refs).issubset(allowed_diagnostics)
        ):
            raise ValueError("private CI diagnostics must be exact unique shard refs")
        state = classify_github(observation)
        records = self._events(observation.repository_sha, series_ref)
        private_starts = [record for record in records if record.get("event") == "private_start"]
        sha_private_starts = [
            record
            for record in private_starts
            if record.get("repository_sha") == observation.repository_sha
        ]
        private_terminals = [
            record for record in records if record.get("event") == "private_terminal"
        ]
        sha_private_terminals = [
            record
            for record in private_terminals
            if record.get("repository_sha") == observation.repository_sha
        ]
        final_retries = [
            record
            for record in records
            if record.get("event") == "github_final_retry"
            and record.get("repository_sha") == observation.repository_sha
        ]
        cooldowns = [
            record
            for record in records
            if record.get("event") == "capacity_cooldown"
            and record.get("repository_sha") == observation.repository_sha
        ]
        reason_refs = [observation.reason_ref]
        if diagnostic_unit_refs:
            reason_refs.append(
                "reason-ref:private-ci:explicit-failed-shard-diagnosis"
            )
        passed_private_terminals = [
            record
            for record in sha_private_terminals
            if record.get("status") == "pass"
        ]
        if state == FallbackState.GITHUB_GREEN and passed_private_terminals:
            private_completed = datetime.fromisoformat(
                str(passed_private_terminals[-1]["observed_at"]).replace("Z", "+00:00")
            )
            github_created = datetime.fromisoformat(
                observation.run_created_at.replace("Z", "+00:00")
            )
            if github_created <= private_completed:
                state = FallbackState.GITHUB_CODE_FAILURE
                reason_refs.append("reason-ref:github:final-run-predates-private-ci")
        github_green = state == FallbackState.GITHUB_GREEN
        commands_completed = 0
        timing_warnings: tuple[str, ...] = ()
        self._record_github_observation(observation, series_ref, state)

        if state == FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED or (
            state == FallbackState.GITHUB_CODE_FAILURE and diagnostic_unit_refs
        ):
            state, commands_completed, timing_warnings = self._handle_infrastructure(
                observation=observation,
                series_ref=series_ref,
                records=records,
                private_starts=private_starts,
                sha_private_starts=sha_private_starts,
                sha_private_terminals=sha_private_terminals,
                final_retries=final_retries,
                cooldowns=cooldowns,
                reason_refs=reason_refs,
                diagnostic_unit_refs=diagnostic_unit_refs,
            )
        return ControllerStatus(
            strategy="github-first-bounded-private-fallback",
            state=state,
            repository_sha=observation.repository_sha,
            manifest_version=SCHEMA_VERSION,
            manifest_fingerprint=definition_fingerprint(),
            github_run_ref=observation.run_ref,
            reason_refs=tuple(dict.fromkeys(reason_refs)),
            commands_completed=commands_completed,
            remaining_gate=(
                "none" if github_green else "green GitHub merge-gate run on the exact final SHA"
            ),
            github_attempt_count=observation.attempt,
            private_attempt_count=len(private_starts)
            + (
                1
                if state
                in {FallbackState.PRIVATE_FAILURE, FallbackState.PRIVATE_GREEN_PENDING_GITHUB}
                else 0
            ),
            duration_ms=max(0, int((time.perf_counter() - started) * 1000)),
            github_gate_satisfied=github_green,
            merge_gate_satisfied=github_green,
            timing_warning_refs=timing_warnings,
        )

    def _record_github_observation(
        self,
        observation: GitHubObservation,
        series_ref: str,
        state: FallbackState,
    ) -> None:
        event: dict[str, Any] = {
            "event": "github_observation",
            "repository_sha": observation.repository_sha,
            "series_ref": series_ref,
            "run_ref": observation.run_ref,
            "status": state.value,
            "reason_ref": observation.reason_ref,
            "observed_at": observation.observed_at,
            "manifest_attested": observation.manifest_attested,
            "observation_source": observation.observation_source,
            "run_created_at": observation.run_created_at,
            "machine_profile_ref": MACHINE_PROFILE_REF,
            "queue_duration_ms": observation.queue_duration_ms,
            "install_duration_ms": observation.install_duration_ms,
            "test_duration_ms": observation.test_duration_ms,
            "release_lane_duration_ms": observation.release_lane_duration_ms,
        }
        if observation.manifest_version:
            event["manifest_version"] = observation.manifest_version
        if observation.manifest_fingerprint:
            event["manifest_fingerprint"] = observation.manifest_fingerprint
        self.ledger.append(event)

    def _handle_infrastructure(
        self,
        *,
        observation: GitHubObservation,
        series_ref: str,
        records: list[dict[str, Any]],
        private_starts: list[dict[str, Any]],
        sha_private_starts: list[dict[str, Any]],
        sha_private_terminals: list[dict[str, Any]],
        final_retries: list[dict[str, Any]],
        cooldowns: list[dict[str, Any]],
        reason_refs: list[str],
        diagnostic_unit_refs: tuple[str, ...],
    ) -> tuple[FallbackState, int, tuple[str, ...]]:
        if sha_private_terminals and sha_private_terminals[-1].get("status") == "pass":
            try:
                current_scope = self.executor.prepare_scope(
                    observation.repository_sha,
                    diagnostic_unit_refs=diagnostic_unit_refs,
                )
            except RemoteHeadAttestationError as exc:
                reason_refs.append(exc.reason_ref)
                return FallbackState.EXTERNALLY_BLOCKED, 0, ()
            except PrivateScopeFullGateRequiredError as exc:
                reason_refs.extend(exc.reason_refs)
                return FallbackState.EXTERNALLY_BLOCKED, 0, ()
            current_scope.validate()
            terminal = sha_private_terminals[-1]
            exact_terminal_bindings = (
                terminal.get("base_sha"),
                terminal.get("source_branch_binding_ref"),
                terminal.get("authoritative_plan_fingerprint"),
                terminal.get("plan_fingerprint"),
                terminal.get("dependency_state_fingerprint"),
                terminal.get("selected_unit_refs"),
                terminal.get("diagnostic_unit_refs"),
                terminal.get("deferred_unit_refs"),
            )
            current_bindings = (
                current_scope.base_sha,
                current_scope.source_branch_binding_ref,
                current_scope.authoritative_plan_fingerprint,
                current_scope.plan_fingerprint,
                current_scope.dependency_state_fingerprint,
                list(current_scope.selected_unit_refs),
                list(current_scope.diagnostic_unit_refs),
                list(current_scope.deferred_unit_refs),
            )
            if exact_terminal_bindings != current_bindings:
                reason_refs.append("reason-ref:private-ci:scope-stale")
                return FallbackState.EXTERNALLY_BLOCKED, 0, ()
            return self._final_retry_state(
                observation, series_ref, final_retries, reason_refs
            ), 0, ()
        if sha_private_starts:
            latest_status = (
                sha_private_terminals[-1].get("status")
                if sha_private_terminals
                else None
            )
            recovery_required = latest_status == "recovery_required" or not (
                sha_private_terminals
            )
            state = (
                FallbackState.EXTERNALLY_BLOCKED
                if recovery_required
                else FallbackState.PRIVATE_FAILURE
            )
            reason_refs.append(
                "reason-ref:private-ci:recovery-required"
                if recovery_required
                else "reason-ref:private-ci:already-settled-for-sha"
            )
            return state, 0, ()
        if len(private_starts) >= MAX_PRIVATE_PASSES:
            reason_refs.append("reason-ref:private-ci:repair-pass-cap-exhausted")
            return FallbackState.EXTERNALLY_BLOCKED, 0, ()
        self._cooldown_once(observation, series_ref, cooldowns)
        try:
            expected_scope = self._record_private_start(
                observation,
                series_ref,
                diagnostic_unit_refs=diagnostic_unit_refs,
            )
        except RemoteHeadAttestationError as exc:
            reason_refs.append(exc.reason_ref)
            return FallbackState.EXTERNALLY_BLOCKED, 0, ()
        except PrivateScopeFullGateRequiredError as exc:
            reason_refs.extend(exc.reason_refs)
            return FallbackState.EXTERNALLY_BLOCKED, 0, ()
        try:
            result = self.executor.verify(
                observation.repository_sha,
                series_ref=series_ref,
                scope=expected_scope,
            )
            result.validate()
            if result.repository_sha != observation.repository_sha:
                raise ValueError(
                    "private result SHA does not match the GitHub observation"
                )
            expected_result_bindings = (
                expected_scope.base_sha,
                expected_scope.source_branch_binding_ref,
                expected_scope.authoritative_plan_fingerprint,
                expected_scope.plan_fingerprint,
                expected_scope.dependency_state_fingerprint,
                expected_scope.selected_unit_refs,
                expected_scope.diagnostic_unit_refs,
                expected_scope.deferred_unit_refs,
            )
            observed_result_bindings = (
                result.base_sha,
                result.source_branch_binding_ref,
                result.authoritative_plan_fingerprint,
                result.plan_fingerprint,
                result.dependency_state_fingerprint,
                result.selected_unit_refs,
                result.diagnostic_unit_refs,
                result.deferred_unit_refs,
            )
            if observed_result_bindings != expected_result_bindings:
                raise ValueError(
                    "private result does not match its exact prepared scope"
                )
        except BaseException as exc:  # noqa: BLE001 - fail closed after durable start
            reason_ref = (
                exc.reason_ref
                if isinstance(exc, RemoteHeadAttestationError)
                else "reason-ref:private-ci:executor-recovery-required"
            )
            self._record_private_recovery_required(
                observation.repository_sha,
                expected_scope,
                series_ref,
                reason_ref=reason_ref,
            )
            reason_refs.extend((reason_ref, "reason-ref:private-ci:recovery-required"))
            return FallbackState.EXTERNALLY_BLOCKED, 0, ()
        warnings = self._timing_warnings(result, records)
        self._record_private_terminal(result, series_ref)
        if result.status == "pass":
            reason_refs.append("reason-ref:github:final-exact-sha-run-required")
            return (
                FallbackState.PRIVATE_GREEN_PENDING_GITHUB,
                len(result.command_result_refs),
                warnings,
            )
        reason_refs.append("reason-ref:private-ci:verification-failed")
        return FallbackState.PRIVATE_FAILURE, len(result.command_result_refs), warnings

    def _final_retry_state(
        self,
        observation: GitHubObservation,
        series_ref: str,
        final_retries: list[dict[str, Any]],
        reason_refs: list[str],
    ) -> FallbackState:
        if len(final_retries) >= MAX_FINAL_GITHUB_RETRIES:
            reason_refs.append("reason-ref:github:final-retry-exhausted")
            return FallbackState.EXTERNALLY_BLOCKED
        self.ledger.append(
            {
                "event": "github_final_retry",
                "repository_sha": observation.repository_sha,
                "series_ref": series_ref,
                "status": FallbackState.GITHUB_FINAL_RETRY.value,
                "reason_ref": "reason-ref:github:final-exact-sha-run-required",
                "observed_at": self.clock().isoformat().replace("+00:00", "Z"),
            }
        )
        reason_refs.append("reason-ref:github:final-exact-sha-run-required")
        return FallbackState.GITHUB_FINAL_RETRY

    def _cooldown_once(
        self,
        observation: GitHubObservation,
        series_ref: str,
        cooldowns: list[dict[str, Any]],
    ) -> None:
        if observation.reason_ref != CAPACITY_REASON or cooldowns:
            return
        self.ledger.append(
            {
                "event": "capacity_cooldown",
                "repository_sha": observation.repository_sha,
                "series_ref": series_ref,
                "status": FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED.value,
                "reason_ref": "reason-ref:github:capacity-cooldown-once",
                "duration_ms": CAPACITY_COOLDOWN_SECONDS * 1000,
                "observed_at": self.clock().isoformat().replace("+00:00", "Z"),
            }
        )
        self.sleeper(CAPACITY_COOLDOWN_SECONDS)

    def _record_private_start(
        self,
        observation: GitHubObservation,
        series_ref: str,
        *,
        diagnostic_unit_refs: tuple[str, ...],
    ) -> PrivateVerificationScope:
        scope = self.executor.prepare_scope(
            observation.repository_sha,
            diagnostic_unit_refs=diagnostic_unit_refs,
        )
        scope.validate()
        self.ledger.append(
            {
                "event": "private_start",
                "repository_sha": observation.repository_sha,
                "series_ref": series_ref,
                "status": FallbackState.PRIVATE_VERIFYING.value,
                "reason_ref": observation.reason_ref,
                "base_sha": scope.base_sha,
                "source_branch_binding_ref": scope.source_branch_binding_ref,
                "authoritative_plan_fingerprint": scope.authoritative_plan_fingerprint,
                "plan_fingerprint": scope.plan_fingerprint,
                "dependency_state_fingerprint": scope.dependency_state_fingerprint,
                "selected_unit_refs": list(scope.selected_unit_refs),
                "diagnostic_unit_refs": list(scope.diagnostic_unit_refs),
                "deferred_unit_refs": list(scope.deferred_unit_refs),
                "github_gate_satisfied": False,
                "merge_gate_satisfied": False,
                "observed_at": self.clock().isoformat().replace("+00:00", "Z"),
            }
        )
        return scope

    def _record_private_recovery_required(
        self,
        repository_sha: str,
        scope: PrivateVerificationScope,
        series_ref: str,
        *,
        reason_ref: str,
    ) -> None:
        observed_at = self.clock().isoformat().replace("+00:00", "Z")
        receipt_payload = {
            "event": "private_terminal",
            "repository_sha": repository_sha,
            "series_ref": series_ref,
            "status": "recovery_required",
            "reason_ref": reason_ref,
            "base_sha": scope.base_sha,
            "source_branch_binding_ref": scope.source_branch_binding_ref,
            "authoritative_plan_fingerprint": scope.authoritative_plan_fingerprint,
            "plan_fingerprint": scope.plan_fingerprint,
            "dependency_state_fingerprint": scope.dependency_state_fingerprint,
            "selected_unit_refs": list(scope.selected_unit_refs),
            "diagnostic_unit_refs": list(scope.diagnostic_unit_refs),
            "deferred_unit_refs": list(scope.deferred_unit_refs),
            "github_gate_satisfied": False,
            "merge_gate_satisfied": False,
            "observed_at": observed_at,
        }
        receipt_payload["receipt_ref"] = (
            "receipt-ref:private-ci:"
            + hashlib.sha256(
                repr(sorted(receipt_payload.items())).encode()
            ).hexdigest()
        )
        self.ledger.append(receipt_payload)

    def _record_private_terminal(
        self,
        result: PrivateVerificationResult,
        series_ref: str,
    ) -> None:
        self.ledger.append(
            {
                "event": "private_terminal",
                "repository_sha": result.repository_sha,
                "series_ref": series_ref,
                "status": result.status,
                "reason_ref": (
                    "reason-ref:private-ci:verified"
                    if result.status == "pass"
                    else "reason-ref:private-ci:verification-failed"
                ),
                "receipt_ref": result.receipt_ref,
                "base_sha": result.base_sha,
                "source_branch_binding_ref": result.source_branch_binding_ref,
                "authoritative_plan_fingerprint": result.authoritative_plan_fingerprint,
                "plan_fingerprint": result.plan_fingerprint,
                "dependency_state_fingerprint": result.dependency_state_fingerprint,
                "selected_unit_refs": list(result.selected_unit_refs),
                "diagnostic_unit_refs": list(result.diagnostic_unit_refs),
                "deferred_unit_refs": list(result.deferred_unit_refs),
                "github_gate_satisfied": False,
                "merge_gate_satisfied": False,
                "timings_ms": [list(value) for value in result.timings_ms],
                "observed_at": result.completed_at,
            }
        )


__all__ = [
    "CAPACITY_COOLDOWN_SECONDS",
    "AttemptLedger",
    "ControllerStatus",
    "FallbackController",
    "FallbackState",
    "FullSuiteLock",
    "GitHubObservation",
    "IsolatedPrivateExecutor",
    "PrivateVerificationResult",
    "_safe_subprocess",
    "classify_github",
    "status_payload",
]
