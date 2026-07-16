from __future__ import annotations

from dataclasses import dataclass

from scripts.verification.verification_contracts import (
    MAX_UNITS,
    SAFE_REF_PATTERN,
    VerificationTerminalStatus,
    VerificationUnit,
    dependency_closed_unit_refs,
    validate_verification_dag,
)


SCHEDULE_SCHEMA_VERSION = "uaa_verification_schedule.v1"
SCHEDULE_REDACTION_STATUS = "content_free_refs_and_statuses_only"
DEFAULT_MAX_PARALLELISM = 4
MAX_PARALLELISM = 8

_UNSUCCESSFUL_REASON_REFS = {
    VerificationTerminalStatus.FAILED: "reason-ref:verification:dependency-failed",
    VerificationTerminalStatus.BLOCKED: "reason-ref:verification:dependency-blocked",
    VerificationTerminalStatus.CANCELLED: (
        "reason-ref:verification:dependency-cancelled"
    ),
    VerificationTerminalStatus.SKIPPED: "reason-ref:verification:dependency-skipped",
    VerificationTerminalStatus.UNKNOWN: "reason-ref:verification:dependency-unknown",
}


def _validate_ref(value: str, *, label: str) -> None:
    if not isinstance(value, str) or SAFE_REF_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a bounded safe ref")


def _validate_unique_refs(values: tuple[str, ...], *, label: str) -> None:
    if not isinstance(values, tuple) or len(values) != len(set(values)):
        raise ValueError(f"{label} must be a unique tuple")
    if len(values) > MAX_UNITS:
        raise ValueError(f"{label} exceeds the unit bound")
    for value in values:
        _validate_ref(value, label=label)


@dataclass(frozen=True)
class VerificationUnitObservation:
    """Content-free terminal evidence used by the pure scheduler."""

    unit_ref: str
    status: VerificationTerminalStatus
    receipt_ref: str

    def validate(self) -> None:
        _validate_ref(self.unit_ref, label="observed verification unit ref")
        _validate_ref(self.receipt_ref, label="observed verification receipt ref")
        if not isinstance(self.status, VerificationTerminalStatus):
            raise ValueError("observed verification status is invalid")


@dataclass(frozen=True)
class VerificationBlockedUnit:
    unit_ref: str
    blocker_unit_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]

    def validate(self) -> None:
        _validate_ref(self.unit_ref, label="blocked verification unit ref")
        _validate_unique_refs(
            self.blocker_unit_refs,
            label="blocked verification blocker refs",
        )
        _validate_unique_refs(
            self.reason_refs,
            label="blocked verification reason refs",
        )
        if not self.blocker_unit_refs or not self.reason_refs:
            raise ValueError("blocked verification units require blockers and reasons")


@dataclass(frozen=True)
class VerificationScheduleWave:
    wave_ref: str
    unit_refs: tuple[str, ...]
    exclusive_resource_refs: tuple[str, ...]

    def validate(self) -> None:
        _validate_ref(self.wave_ref, label="verification wave ref")
        _validate_unique_refs(self.unit_refs, label="verification wave unit refs")
        _validate_unique_refs(
            self.exclusive_resource_refs,
            label="verification wave resource refs",
        )
        if not self.unit_refs:
            raise ValueError("verification waves cannot be empty")


@dataclass(frozen=True)
class VerificationSchedule:
    schema_version: str
    selected_unit_refs: tuple[str, ...]
    max_parallelism: int
    completed_unit_refs: tuple[str, ...]
    running_unit_refs: tuple[str, ...]
    waves: tuple[VerificationScheduleWave, ...]
    blocked_units: tuple[VerificationBlockedUnit, ...]
    pending_unit_refs: tuple[str, ...]
    redaction_status: str = SCHEDULE_REDACTION_STATUS

    def validate(self) -> None:
        if self.schema_version != SCHEDULE_SCHEMA_VERSION:
            raise ValueError("unsupported verification schedule schema version")
        for values, label in (
            (self.selected_unit_refs, "selected verification unit refs"),
            (self.completed_unit_refs, "completed verification unit refs"),
            (self.running_unit_refs, "running verification unit refs"),
            (self.pending_unit_refs, "pending verification unit refs"),
        ):
            _validate_unique_refs(values, label=label)
        if not self.selected_unit_refs:
            raise ValueError("verification schedule must select at least one unit")
        if (
            not isinstance(self.max_parallelism, int)
            or isinstance(self.max_parallelism, bool)
            or not 1 <= self.max_parallelism <= MAX_PARALLELISM
        ):
            raise ValueError("verification schedule parallelism is invalid")
        if len(self.running_unit_refs) > self.max_parallelism:
            raise ValueError("running verification units exceed the parallelism cap")
        for wave in self.waves:
            wave.validate()
            available_parallelism = self.max_parallelism - len(
                self.running_unit_refs
            )
            if len(wave.unit_refs) > available_parallelism:
                raise ValueError("verification wave exceeds the parallelism cap")
        for blocked in self.blocked_units:
            blocked.validate()
        if len(self.waves) > MAX_UNITS or len(self.blocked_units) > MAX_UNITS:
            raise ValueError("verification schedule exceeds the unit bound")

        selected = set(self.selected_unit_refs)
        wave_refs = tuple(unit_ref for wave in self.waves for unit_ref in wave.unit_refs)
        blocked_refs = tuple(blocked.unit_ref for blocked in self.blocked_units)
        disposition_refs = (
            self.completed_unit_refs
            + self.running_unit_refs
            + wave_refs
            + blocked_refs
            + self.pending_unit_refs
        )
        if len(disposition_refs) != len(set(disposition_refs)):
            raise ValueError("verification schedule dispositions must not overlap")
        if set(disposition_refs) != selected:
            raise ValueError("verification schedule must classify every selected unit")
        if any(
            not set(blocked.blocker_unit_refs).issubset(selected)
            for blocked in self.blocked_units
        ):
            raise ValueError("verification blockers must be selected units")
        if len(tuple(wave.wave_ref for wave in self.waves)) != len(
            {wave.wave_ref for wave in self.waves}
        ):
            raise ValueError("verification wave refs must be unique")
        if self.redaction_status != SCHEDULE_REDACTION_STATUS:
            raise ValueError("verification schedule redaction posture is invalid")


def _canonical_selected_units(
    units: tuple[VerificationUnit, ...],
    selected_unit_refs: tuple[str, ...],
) -> tuple[VerificationUnit, ...]:
    if not isinstance(units, tuple) or not all(
        isinstance(unit, VerificationUnit) for unit in units
    ):
        raise ValueError("verification DAG units must be a typed tuple")
    validate_verification_dag(units)
    _validate_unique_refs(selected_unit_refs, label="selected verification unit refs")
    if not selected_unit_refs:
        raise ValueError("verification scheduler must select at least one unit")
    closed_refs = dependency_closed_unit_refs(units, selected_unit_refs)
    if closed_refs != selected_unit_refs:
        if set(closed_refs) != set(selected_unit_refs):
            raise ValueError("selected verification units must be dependency closed")
        raise ValueError("selected verification units must use canonical DAG order")
    selected = set(selected_unit_refs)
    return tuple(unit for unit in units if unit.unit_ref in selected)


def _waves_for_ready_units(
    ready_units: tuple[VerificationUnit, ...],
    *,
    max_parallelism: int,
) -> tuple[VerificationScheduleWave, ...]:
    grouped: list[list[VerificationUnit]] = []
    current_group: list[VerificationUnit] = []
    current_resources: set[str] = set()

    def flush_current() -> None:
        nonlocal current_group, current_resources
        if current_group:
            grouped.append(current_group)
            current_group = []
            current_resources = set()

    for unit in ready_units:
        if not unit.parallel_safe:
            flush_current()
            grouped.append([unit])
            continue
        resources = set(unit.exclusive_resource_refs)
        if (
            len(current_group) >= max_parallelism
            or resources.intersection(current_resources)
        ):
            flush_current()
        current_group.append(unit)
        current_resources.update(resources)
    flush_current()

    return tuple(
        VerificationScheduleWave(
            wave_ref=f"wave-ref:verification:{index:03d}",
            unit_refs=tuple(unit.unit_ref for unit in group),
            exclusive_resource_refs=tuple(
                resource_ref
                for unit in group
                for resource_ref in unit.exclusive_resource_refs
            ),
        )
        for index, group in enumerate(grouped, start=1)
    )


def build_verification_schedule(
    units: tuple[VerificationUnit, ...],
    selected_unit_refs: tuple[str, ...],
    *,
    observations: tuple[VerificationUnitObservation, ...] = (),
    running_unit_refs: tuple[str, ...] = (),
    max_parallelism: int = DEFAULT_MAX_PARALLELISM,
) -> VerificationSchedule:
    """Derive deterministic execution waves without executing or granting authority."""

    selected_units = _canonical_selected_units(units, selected_unit_refs)
    selected = set(selected_unit_refs)
    if (
        not isinstance(max_parallelism, int)
        or isinstance(max_parallelism, bool)
        or not 1 <= max_parallelism <= MAX_PARALLELISM
    ):
        raise ValueError("verification scheduler parallelism must be between 1 and 8")

    if not isinstance(observations, tuple):
        raise ValueError("verification observations must be an immutable tuple")
    observations_by_ref: dict[str, VerificationUnitObservation] = {}
    observation_receipt_refs: set[str] = set()
    for observation in observations:
        if not isinstance(observation, VerificationUnitObservation):
            raise ValueError("verification observations must be typed")
        observation.validate()
        if observation.unit_ref not in selected:
            raise ValueError("verification observation is outside selected membership")
        if observation.unit_ref in observations_by_ref:
            raise ValueError("verification observations must be unique by unit")
        if observation.receipt_ref in observation_receipt_refs:
            raise ValueError("verification observation receipt refs must be unique")
        observations_by_ref[observation.unit_ref] = observation
        observation_receipt_refs.add(observation.receipt_ref)

    _validate_unique_refs(running_unit_refs, label="running verification unit refs")
    running = set(running_unit_refs)
    if not running.issubset(selected):
        raise ValueError("running verification units must be selected")
    canonical_running = tuple(
        unit.unit_ref for unit in selected_units if unit.unit_ref in running
    )
    if canonical_running != running_unit_refs:
        raise ValueError("running verification units must use canonical DAG order")
    if running.intersection(observations_by_ref):
        raise ValueError("running verification units cannot have terminal observations")
    if len(running_unit_refs) > max_parallelism:
        raise ValueError("running verification units exceed the parallelism cap")

    by_ref = {unit.unit_ref: unit for unit in selected_units}
    if len(running_unit_refs) > 1 and any(
        not by_ref[unit_ref].parallel_safe for unit_ref in running_unit_refs
    ):
        raise ValueError("parallel-unsafe running verification unit must be a singleton")
    running_resource_refs = tuple(
        resource_ref
        for unit_ref in running_unit_refs
        for resource_ref in by_ref[unit_ref].exclusive_resource_refs
    )
    if len(running_resource_refs) != len(set(running_resource_refs)):
        raise ValueError("running verification resources must not conflict")
    for unit in selected_units:
        observation = observations_by_ref.get(unit.unit_ref)
        if (
            observation is not None
            and observation.status is VerificationTerminalStatus.PASSED
            and any(
                dependency not in observations_by_ref
                or observations_by_ref[dependency].status
                is not VerificationTerminalStatus.PASSED
                for dependency in unit.needs
            )
        ):
            raise ValueError(
                "passed verification units require passed dependency observations"
            )
    for running_ref in running_unit_refs:
        dependencies = by_ref[running_ref].needs
        if any(
            dependency not in observations_by_ref
            or observations_by_ref[dependency].status
            is not VerificationTerminalStatus.PASSED
            for dependency in dependencies
        ):
            raise ValueError(
                "running verification units require passed dependency observations"
            )

    direct_unsuccessful_roots: dict[str, tuple[str, ...]] = {}
    direct_unsuccessful_reasons: dict[str, tuple[str, ...]] = {}
    for unit in selected_units:
        observation = observations_by_ref.get(unit.unit_ref)
        if observation is None or observation.status is VerificationTerminalStatus.PASSED:
            continue
        reason_ref = _UNSUCCESSFUL_REASON_REFS[observation.status]
        direct_unsuccessful_roots[unit.unit_ref] = (unit.unit_ref,)
        direct_unsuccessful_reasons[unit.unit_ref] = (reason_ref,)

    unsuccessful_roots: dict[str, tuple[str, ...]] = {}
    unsuccessful_reasons: dict[str, tuple[str, ...]] = {}

    def resolve_unsuccessful_dependencies(unit_ref: str) -> tuple[str, ...]:
        if unit_ref in unsuccessful_roots:
            return unsuccessful_roots[unit_ref]
        if unit_ref in direct_unsuccessful_roots:
            unsuccessful_roots[unit_ref] = direct_unsuccessful_roots[unit_ref]
            unsuccessful_reasons[unit_ref] = direct_unsuccessful_reasons[unit_ref]
            return unsuccessful_roots[unit_ref]
        blockers = {
            blocker
            for dependency in by_ref[unit_ref].needs
            for blocker in resolve_unsuccessful_dependencies(dependency)
        }
        if blockers:
            unsuccessful_roots[unit_ref] = tuple(
                ref for ref in selected_unit_refs if ref in blockers
            )
            unsuccessful_reasons[unit_ref] = tuple(
                sorted(
                    {
                        reason
                        for dependency in by_ref[unit_ref].needs
                        for reason in unsuccessful_reasons.get(dependency, ())
                    }
                )
            )
        return unsuccessful_roots.get(unit_ref, ())

    for unit in selected_units:
        resolve_unsuccessful_dependencies(unit.unit_ref)

    running_resources = {
        resource_ref
        for unit_ref in running
        for resource_ref in by_ref[unit_ref].exclusive_resource_refs
    }
    running_has_singleton = any(not by_ref[unit_ref].parallel_safe for unit_ref in running)
    completed = tuple(
        unit.unit_ref
        for unit in selected_units
        if (
            (observation := observations_by_ref.get(unit.unit_ref)) is not None
            and observation.status is VerificationTerminalStatus.PASSED
        )
    )
    blocked = tuple(
        VerificationBlockedUnit(
            unit_ref=unit.unit_ref,
            blocker_unit_refs=unsuccessful_roots[unit.unit_ref],
            reason_refs=unsuccessful_reasons[unit.unit_ref],
        )
        for unit in selected_units
        if unit.unit_ref in unsuccessful_roots
    )

    ready: list[VerificationUnit] = []
    pending: list[str] = []
    for unit in selected_units:
        if (
            unit.unit_ref in observations_by_ref
            or unit.unit_ref in running
            or unit.unit_ref in unsuccessful_roots
        ):
            continue
        dependencies_passed = all(
            dependency in observations_by_ref
            and observations_by_ref[dependency].status
            is VerificationTerminalStatus.PASSED
            for dependency in unit.needs
        )
        unavailable_while_running = bool(running) and (
            running_has_singleton
            or not unit.parallel_safe
            or bool(set(unit.exclusive_resource_refs).intersection(running_resources))
        )
        if (
            dependencies_passed
            and not unavailable_while_running
            and len(running_unit_refs) < max_parallelism
        ):
            ready.append(unit)
        else:
            pending.append(unit.unit_ref)

    waves = _waves_for_ready_units(
        tuple(ready),
        max_parallelism=max_parallelism - len(running_unit_refs),
    )
    schedule = VerificationSchedule(
        schema_version=SCHEDULE_SCHEMA_VERSION,
        selected_unit_refs=selected_unit_refs,
        max_parallelism=max_parallelism,
        completed_unit_refs=completed,
        running_unit_refs=running_unit_refs,
        waves=waves,
        blocked_units=blocked,
        pending_unit_refs=tuple(pending),
    )
    schedule.validate()
    return schedule
