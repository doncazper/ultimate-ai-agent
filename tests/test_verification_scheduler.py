from __future__ import annotations

from dataclasses import replace

import pytest

from scripts.verification.verification_contracts import (
    VerificationTerminalStatus,
    VerificationUnit,
)
from scripts.verification.verification_scheduler import (
    VerificationBlockedUnit,
    VerificationSchedule,
    VerificationScheduleWave,
    VerificationUnitObservation,
    build_verification_schedule,
)


def _unit(
    unit_ref: str,
    *,
    needs: tuple[str, ...] = (),
    parallel_safe: bool = True,
    resources: tuple[str, ...] = (),
) -> VerificationUnit:
    return VerificationUnit(
        unit_ref=unit_ref,
        display_name=f"Verification {unit_ref}",
        lane_ref=f"lane:{unit_ref}",
        needs=needs,
        command_refs=(f"command:{unit_ref}",),
        parallel_safe=parallel_safe,
        exclusive_resource_refs=resources,
    )


def _observation(
    unit_ref: str,
    status: VerificationTerminalStatus = VerificationTerminalStatus.PASSED,
) -> VerificationUnitObservation:
    return VerificationUnitObservation(
        unit_ref=unit_ref,
        status=status,
        receipt_ref=f"receipt-ref:{unit_ref}:{status.value}",
    )


def _refs(schedule: VerificationSchedule) -> tuple[tuple[str, ...], ...]:
    return tuple(wave.unit_refs for wave in schedule.waves)


def test_scheduler_preserves_canonical_order_and_waits_for_dependencies() -> None:
    units = (
        _unit("prepare"),
        _unit("test", needs=("prepare",)),
        _unit("release", needs=("test",)),
    )

    initial = build_verification_schedule(units, ("prepare", "test", "release"))
    after_prepare = build_verification_schedule(
        units,
        ("prepare", "test", "release"),
        observations=(_observation("prepare"),),
    )

    assert _refs(initial) == (("prepare",),)
    assert initial.pending_unit_refs == ("test", "release")
    assert _refs(after_prepare) == (("test",),)
    assert after_prepare.completed_unit_refs == ("prepare",)
    assert after_prepare.pending_unit_refs == ("release",)


def test_ready_units_are_partitioned_by_exclusive_resources() -> None:
    units = (
        _unit("one", resources=("resource-ref:database",)),
        _unit("two", resources=("resource-ref:database",)),
        _unit("three", resources=("resource-ref:browser",)),
    )

    schedule = build_verification_schedule(units, ("one", "two", "three"))

    assert _refs(schedule) == (("one",), ("two", "three"))
    assert schedule.waves[0].exclusive_resource_refs == (
        "resource-ref:database",
    )


def test_parallel_unsafe_unit_is_always_a_singleton_wave() -> None:
    units = (
        _unit("parallel-one"),
        _unit("serial", parallel_safe=False),
        _unit("parallel-two"),
    )

    schedule = build_verification_schedule(
        units,
        ("parallel-one", "serial", "parallel-two"),
    )

    assert _refs(schedule) == (
        ("parallel-one",),
        ("serial",),
        ("parallel-two",),
    )


def test_parallelism_cap_is_bounded_and_deterministic() -> None:
    units = tuple(_unit(f"unit-{index}") for index in range(5))
    refs = tuple(unit.unit_ref for unit in units)

    first = build_verification_schedule(units, refs, max_parallelism=2)
    second = build_verification_schedule(units, refs, max_parallelism=2)

    assert _refs(first) == (("unit-0", "unit-1"), ("unit-2", "unit-3"), ("unit-4",))
    assert first == second


@pytest.mark.parametrize("parallelism", (0, 9, True, 1.5))
def test_parallelism_cap_rejects_invalid_values(parallelism: object) -> None:
    with pytest.raises(ValueError, match="parallelism"):
        build_verification_schedule(
            (_unit("one"),),
            ("one",),
            max_parallelism=parallelism,  # type: ignore[arg-type]
        )


def test_failed_dependency_blocks_all_descendants_but_not_independent_work() -> None:
    units = (
        _unit("root"),
        _unit("child", needs=("root",)),
        _unit("grandchild", needs=("child",)),
        _unit("independent"),
    )

    schedule = build_verification_schedule(
        units,
        ("root", "child", "grandchild", "independent"),
        observations=(_observation("root", VerificationTerminalStatus.FAILED),),
    )

    assert _refs(schedule) == (("independent",),)
    assert tuple(blocked.unit_ref for blocked in schedule.blocked_units) == (
        "root",
        "child",
        "grandchild",
    )
    assert schedule.blocked_units[-1].blocker_unit_refs == ("root",)
    assert schedule.blocked_units[-1].reason_refs == (
        "reason-ref:verification:dependency-failed",
    )


def test_already_running_independent_sibling_may_settle_after_failure() -> None:
    units = (
        _unit("failed-root"),
        _unit("blocked-child", needs=("failed-root",)),
        _unit("running-independent"),
    )

    schedule = build_verification_schedule(
        units,
        ("failed-root", "blocked-child", "running-independent"),
        observations=(
            _observation("failed-root", VerificationTerminalStatus.FAILED),
        ),
        running_unit_refs=("running-independent",),
    )

    assert schedule.running_unit_refs == ("running-independent",)
    assert tuple(blocked.unit_ref for blocked in schedule.blocked_units) == (
        "failed-root",
        "blocked-child",
    )


def test_dependency_blocking_is_independent_of_dag_declaration_order() -> None:
    units = (
        _unit("grandchild", needs=("child",)),
        _unit("child", needs=("root",)),
        _unit("root"),
    )

    schedule = build_verification_schedule(
        units,
        ("grandchild", "child", "root"),
        observations=(_observation("root", VerificationTerminalStatus.FAILED),),
    )

    assert tuple(blocked.unit_ref for blocked in schedule.blocked_units) == (
        "grandchild",
        "child",
        "root",
    )
    assert schedule.blocked_units[0].blocker_unit_refs == ("root",)


@pytest.mark.parametrize(
    ("status", "reason_ref"),
    (
        (
            VerificationTerminalStatus.BLOCKED,
            "reason-ref:verification:dependency-blocked",
        ),
        (
            VerificationTerminalStatus.CANCELLED,
            "reason-ref:verification:dependency-cancelled",
        ),
        (
            VerificationTerminalStatus.SKIPPED,
            "reason-ref:verification:dependency-skipped",
        ),
        (
            VerificationTerminalStatus.UNKNOWN,
            "reason-ref:verification:dependency-unknown",
        ),
    ),
)
def test_all_non_success_terminal_states_fail_closed(
    status: VerificationTerminalStatus,
    reason_ref: str,
) -> None:
    units = (_unit("root"), _unit("child", needs=("root",)))

    schedule = build_verification_schedule(
        units,
        ("root", "child"),
        observations=(_observation("root", status),),
    )

    assert schedule.waves == ()
    assert schedule.blocked_units[-1].reason_refs == (reason_ref,)


def test_running_independent_sibling_can_settle_and_reserves_its_resource() -> None:
    units = (
        _unit("running", resources=("resource-ref:shared",)),
        _unit("conflict", resources=("resource-ref:shared",)),
        _unit("independent", resources=("resource-ref:other",)),
    )

    schedule = build_verification_schedule(
        units,
        ("running", "conflict", "independent"),
        running_unit_refs=("running",),
    )

    assert schedule.running_unit_refs == ("running",)
    assert _refs(schedule) == (("independent",),)
    assert schedule.pending_unit_refs == ("conflict",)


def test_running_units_consume_the_parallelism_cap() -> None:
    units = tuple(_unit(f"unit-{index}") for index in range(7))
    refs = tuple(unit.unit_ref for unit in units)

    schedule = build_verification_schedule(
        units,
        refs,
        running_unit_refs=("unit-0", "unit-1"),
        max_parallelism=4,
    )

    assert _refs(schedule) == (
        ("unit-2", "unit-3"),
        ("unit-4", "unit-5"),
        ("unit-6",),
    )
    assert all(len(wave.unit_refs) <= 2 for wave in schedule.waves)


def test_full_running_cap_leaves_ready_units_pending() -> None:
    units = (_unit("running-one"), _unit("running-two"), _unit("ready"))

    schedule = build_verification_schedule(
        units,
        ("running-one", "running-two", "ready"),
        running_unit_refs=("running-one", "running-two"),
        max_parallelism=2,
    )

    assert schedule.waves == ()
    assert schedule.pending_unit_refs == ("ready",)


def test_running_units_cannot_exceed_parallelism_cap() -> None:
    units = (_unit("running-one"), _unit("running-two"))

    with pytest.raises(ValueError, match="exceed the parallelism cap"):
        build_verification_schedule(
            units,
            ("running-one", "running-two"),
            running_unit_refs=("running-one", "running-two"),
            max_parallelism=1,
        )


def test_running_unit_requires_successful_dependency_evidence() -> None:
    units = (_unit("prepare"), _unit("running", needs=("prepare",)))

    with pytest.raises(ValueError, match="passed dependency observations"):
        build_verification_schedule(
            units,
            ("prepare", "running"),
            running_unit_refs=("running",),
        )


def test_passed_unit_requires_successful_dependency_evidence() -> None:
    units = (_unit("prepare"), _unit("test", needs=("prepare",)))

    with pytest.raises(ValueError, match="passed dependency observations"):
        build_verification_schedule(
            units,
            ("prepare", "test"),
            observations=(_observation("test"),),
        )


def test_running_membership_must_use_canonical_order() -> None:
    units = (_unit("one"), _unit("two"))

    with pytest.raises(ValueError, match="canonical DAG order"):
        build_verification_schedule(
            units,
            ("one", "two"),
            running_unit_refs=("two", "one"),
        )


def test_missing_unknown_cycle_and_noncanonical_membership_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown dependencies"):
        build_verification_schedule(
            (_unit("one", needs=("missing",)),),
            ("one",),
        )
    with pytest.raises(ValueError, match="cycle"):
        build_verification_schedule(
            (_unit("one", needs=("two",)), _unit("two", needs=("one",))),
            ("one", "two"),
        )

    units = (_unit("one"), _unit("two", needs=("one",)))
    with pytest.raises(ValueError, match="dependency closed"):
        build_verification_schedule(units, ("two",))
    with pytest.raises(ValueError, match="canonical DAG order"):
        build_verification_schedule(units, ("two", "one"))
    with pytest.raises(ValueError, match="unknown"):
        build_verification_schedule(units, ("one", "missing"))


def test_observations_require_typed_status_safe_refs_and_exact_membership() -> None:
    unit = _unit("one")
    with pytest.raises(ValueError, match="status"):
        build_verification_schedule(
            (unit,),
            ("one",),
            observations=(
                VerificationUnitObservation(
                    unit_ref="one",
                    status="passed",  # type: ignore[arg-type]
                    receipt_ref="receipt-ref:one",
                ),
            ),
        )
    with pytest.raises(ValueError, match="safe ref"):
        build_verification_schedule(
            (unit,),
            ("one",),
            observations=(
                VerificationUnitObservation(
                    unit_ref="one",
                    status=VerificationTerminalStatus.PASSED,
                    receipt_ref="unsafe receipt ref",
                ),
            ),
        )
    with pytest.raises(ValueError, match="outside selected"):
        build_verification_schedule(
            (unit, _unit("two")),
            ("one",),
            observations=(_observation("two"),),
        )


def test_duplicate_observations_and_running_terminal_overlap_are_rejected() -> None:
    units = (_unit("one"),)
    observation = _observation("one")
    with pytest.raises(ValueError, match="unique by unit"):
        build_verification_schedule(
            units,
            ("one",),
            observations=(observation, observation),
        )
    with pytest.raises(ValueError, match="cannot have terminal"):
        build_verification_schedule(
            units,
            ("one",),
            observations=(observation,),
            running_unit_refs=("one",),
        )


def test_duplicate_receipts_and_conflicting_running_units_are_rejected() -> None:
    duplicate_receipt = "receipt-ref:shared"
    observations = (
        replace(_observation("one"), receipt_ref=duplicate_receipt),
        replace(_observation("two"), receipt_ref=duplicate_receipt),
    )
    with pytest.raises(ValueError, match="receipt refs must be unique"):
        build_verification_schedule(
            (_unit("one"), _unit("two")),
            ("one", "two"),
            observations=observations,
        )

    shared = ("resource-ref:shared",)
    with pytest.raises(ValueError, match="resources must not conflict"):
        build_verification_schedule(
            (_unit("one", resources=shared), _unit("two", resources=shared)),
            ("one", "two"),
            running_unit_refs=("one", "two"),
        )
    with pytest.raises(ValueError, match="must be a singleton"):
        build_verification_schedule(
            (_unit("one", parallel_safe=False), _unit("two")),
            ("one", "two"),
            running_unit_refs=("one", "two"),
        )


def test_schedule_contract_rejects_overlapping_or_unsafe_dispositions() -> None:
    schedule = VerificationSchedule(
        schema_version="uaa_verification_schedule.v1",
        selected_unit_refs=("one",),
        max_parallelism=4,
        completed_unit_refs=(),
        running_unit_refs=(),
        waves=(
            VerificationScheduleWave(
                wave_ref="wave-ref:verification:001",
                unit_refs=("one",),
                exclusive_resource_refs=(),
            ),
        ),
        blocked_units=(),
        pending_unit_refs=(),
    )
    schedule.validate()

    with pytest.raises(ValueError, match="must not overlap"):
        replace(schedule, completed_unit_refs=("one",)).validate()
    with pytest.raises(ValueError, match="safe ref"):
        replace(
            schedule,
            waves=(replace(schedule.waves[0], wave_ref="unsafe wave"),),
        ).validate()
    with pytest.raises(ValueError, match="blockers and reasons"):
        VerificationBlockedUnit(
            unit_ref="one",
            blocker_unit_refs=(),
            reason_refs=(),
        ).validate()
    with pytest.raises(ValueError, match="parallelism cap"):
        replace(
            schedule,
            max_parallelism=1,
            waves=(
                VerificationScheduleWave(
                    wave_ref="wave-ref:verification:001",
                    unit_refs=("one", "two"),
                    exclusive_resource_refs=(),
                ),
            ),
            selected_unit_refs=("one", "two"),
        ).validate()
    with pytest.raises(ValueError, match="running verification units exceed"):
        replace(
            schedule,
            max_parallelism=1,
            selected_unit_refs=("one", "two"),
            running_unit_refs=("one", "two"),
            waves=(),
        ).validate()
