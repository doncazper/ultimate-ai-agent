from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.verification.ci_command_manifest import VERIFICATION_DAG, build_plan
from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationRiskTier,
    VerificationTerminalStatus,
    VerificationUnit,
    VerificationUnitKind,
    verification_dag_definition_fingerprint,
    verification_plan_contract_fingerprint,
    verification_unit_definition_fingerprint,
)
from scripts.verification.verification_execution_identity import (
    REDACTION_STATUS,
    VerificationExecutionFailureCategory,
    VerificationExecutionFence,
    VerificationExecutionFenceCapacityError,
    VerificationExecutionFenceDisposition,
    VerificationExecutionFenceError,
    VerificationExecutionFenceStateError,
    VerificationExecutionIdentityError,
    build_verification_execution_identity,
    build_verification_execution_terminal_proof,
    verification_execution_identity_fingerprint,
    verification_execution_terminal_proof_fingerprint,
)


SHA = "a" * 40
BASE_SHA = "b" * 40
DIGESTS = tuple(character * 64 for character in "123456789abcdef")
STARTED_AT = datetime(2026, 7, 15, 12, 0, 0, tzinfo=UTC)
COMPLETED_AT = "2026-07-15T12:00:01Z"


def _unit(**changes: object) -> VerificationUnit:
    unit = VerificationUnit(
        unit_ref="unit:focused",
        display_name="Focused verification",
        lane_ref="lane:focused",
        needs=(),
        command_refs=("command:focused",),
        execution_surfaces=("github", "local", "private"),
        proof_equivalence_ref="proof-equivalence-ref:focused",
    )
    return replace(unit, **changes)


def _refingerprint(plan: VerificationPlan) -> VerificationPlan:
    provisional = replace(plan, plan_fingerprint="0" * 64)
    return replace(
        provisional,
        plan_fingerprint=verification_plan_contract_fingerprint(provisional),
    )


def _plan(
    *,
    bound_units: tuple[VerificationUnit, ...] | None = None,
    **changes: object,
) -> VerificationPlan:
    units = bound_units or (_unit(),)
    lane_refs = tuple(
        dict.fromkeys(unit.lane_ref for unit in units if unit.lane_ref is not None)
    )
    command_refs = tuple(
        dict.fromkeys(command_ref for unit in units for command_ref in unit.command_refs)
    )
    plan = VerificationPlan(
        schema_version="uaa_verification_plan.v3",
        profile_ref="profile:focused",
        repository_sha=SHA,
        definition_fingerprint=DIGESTS[0],
        dependency_lock_fingerprints=(("uv.lock", DIGESTS[1]),),
        affected_path_classification="risk:tier_2",
        selected_lane_refs=lane_refs,
        selected_command_refs=command_refs,
        pytest_shard_plan_fingerprint=DIGESTS[2],
        frontend_visual_scope="visual:none",
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        plan_fingerprint="0" * 64,
        base_sha=BASE_SHA,
        risk_manifest_version="uaa_verification_risk_manifest.v1",
        risk_manifest_fingerprint=DIGESTS[3],
        risk_tier=VerificationRiskTier.TIER_2,
        changed_path_refs=("scripts/verification/example.py",),
        change_fingerprint=DIGESTS[4],
        escalation_reason_refs=(),
        selected_unit_refs=tuple(unit.unit_ref for unit in units),
        selected_test_refs=("tests/test_example.py",),
        audit_posture="audit:focused",
        full_pytest_required=False,
        typescript_typecheck_required=False,
        release_gate_required=False,
        platform_fingerprint=DIGESTS[5],
        command_manifest_fingerprint=DIGESTS[6],
        verifier_definition_fingerprint=DIGESTS[7],
        test_collection_fingerprint=DIGESTS[8],
        test_collection_posture="inventory_bound",
        typescript_project_fingerprint=DIGESTS[9],
        typescript_project_posture="project_bound",
        force_full=False,
        shadow_mode=False,
        verification_dag_fingerprint=verification_dag_definition_fingerprint(units),
        selected_unit_definition_fingerprints=tuple(
            (unit.unit_ref, verification_unit_definition_fingerprint(unit))
            for unit in units
        ),
    )
    return _refingerprint(replace(plan, **changes))


def _identity(
    plan: VerificationPlan | None = None,
    unit: VerificationUnit | None = None,
    *,
    surface: str = "surface-ref:local",
    typescript_runtime_fingerprint: str | None = None,
    typescript_version_ref: str | None = None,
):
    return build_verification_execution_identity(
        plan or _plan(),
        unit or _unit(),
        execution_surface_ref=surface,
        typescript_runtime_fingerprint=typescript_runtime_fingerprint,
        typescript_version_ref=typescript_version_ref,
    )


def _proof(
    identity,
    *,
    status: VerificationTerminalStatus = VerificationTerminalStatus.PASSED,
    completed_at: str = COMPLETED_AT,
    deterministic_failure: bool = False,
    receipt_ref: str = f"receipt:verification:{DIGESTS[12]}",
    result_refs: tuple[str, ...] = (
        f"result-ref:verification:{DIGESTS[13]}",
    ),
):
    if status is VerificationTerminalStatus.PASSED:
        failure_reason_ref = "reason-ref:verification:not-applicable"
        failure_evidence_ref = None
    elif status is VerificationTerminalStatus.FAILED and deterministic_failure:
        failure_reason_ref = "reason-ref:verification:deterministic-code-failure"
        failure_evidence_ref = result_refs[0]
    elif status is VerificationTerminalStatus.FAILED:
        failure_reason_ref = "reason-ref:verification:execution-result-unknown"
        failure_evidence_ref = result_refs[0]
    elif status is VerificationTerminalStatus.BLOCKED:
        failure_reason_ref = "reason-ref:verification:execution-blocked"
        failure_evidence_ref = result_refs[0]
    else:
        failure_reason_ref = "reason-ref:verification:execution-cancelled"
        failure_evidence_ref = result_refs[0]
    return build_verification_execution_terminal_proof(
        identity,
        status=status,
        receipt_ref=receipt_ref,
        result_refs=result_refs,
        output_digest=DIGESTS[11],
        completed_at=completed_at,
        failure_reason_ref=failure_reason_ref,
        failure_evidence_ref=failure_evidence_ref,
    )


def _store(tmp_path: Path, **kwargs: object) -> VerificationExecutionFence:
    return VerificationExecutionFence(
        tmp_path / "execution-fence",
        clock=lambda: STARTED_AT,
        **kwargs,
    )


def test_identity_is_content_bound_to_every_execution_dimension() -> None:
    baseline = _identity()
    mutations = (
        _identity(_plan(repository_sha="c" * 40)),
        _identity(_plan(definition_fingerprint=DIGESTS[12])),
        _identity(
            _plan(
                dependency_lock_fingerprints=(
                    ("uv.lock", DIGESTS[1]),
                    ("apps/control-center/package-lock.json", DIGESTS[12]),
                )
            )
        ),
        _identity(_plan(platform_fingerprint=DIGESTS[12])),
        _identity(_plan(command_manifest_fingerprint=DIGESTS[12])),
        _identity(_plan(verifier_definition_fingerprint=DIGESTS[12])),
        _identity(_plan(test_collection_fingerprint=DIGESTS[12])),
        _identity(_plan(selected_test_refs=("tests/test_other.py",))),
        _identity(_plan(pytest_shard_plan_fingerprint=DIGESTS[12])),
        _identity(_plan(typescript_project_fingerprint=DIGESTS[12])),
        _identity(
            _plan(bound_units=(_unit(timeout_minutes=44),)),
            _unit(timeout_minutes=44),
        ),
        _identity(surface="surface-ref:private"),
    )

    baseline.validate()
    assert baseline.identity_ref == (
        f"execution-identity:{baseline.identity_fingerprint}"
    )
    assert all(
        changed.identity_fingerprint != baseline.identity_fingerprint
        for changed in mutations
    )


def test_identity_rejects_noncanonical_plan_membership_and_surface() -> None:
    with pytest.raises(VerificationExecutionIdentityError, match="not a member"):
        _identity(_plan(bound_units=(_unit(unit_ref="unit:other"),)))
    with pytest.raises(VerificationExecutionIdentityError, match="unavailable"):
        _identity(surface="surface-ref:remote")
    with pytest.raises(VerificationExecutionIdentityError, match="namespace"):
        _identity(surface="local")
    with pytest.raises(VerificationExecutionIdentityError, match="cannot vary"):
        _identity(
            typescript_runtime_fingerprint=DIGESTS[10],
            typescript_version_ref="typescript-version-ref:7.0.2",
        )


def test_identity_rejects_forged_exclusive_resource_attempt_fingerprint() -> None:
    unit = _unit(exclusive_resource_refs=("resource-ref:complete-pytest",))
    identity = _identity(_plan(bound_units=(unit,)), unit)
    provisional = replace(
        identity,
        exclusive_resource_attempt_fingerprint="f" * 64,
        identity_ref="execution-identity:" + "0" * 64,
        identity_fingerprint="0" * 64,
    )
    fingerprint = verification_execution_identity_fingerprint(provisional)
    forged = replace(
        provisional,
        identity_ref=f"execution-identity:{fingerprint}",
        identity_fingerprint=fingerprint,
    )

    with pytest.raises(
        VerificationExecutionIdentityError,
        match="resource attempt fingerprint is not content bound",
    ):
        forged.validate()


def test_canonical_typescript_unit_requires_and_binds_exact_runtime() -> None:
    unit = next(unit for unit in VERIFICATION_DAG if unit.unit_ref == "risk-frontend-typecheck")
    plan = build_plan(
        Path(__file__).resolve().parents[1],
        SHA,
        selected_unit_refs=(unit.unit_ref,),
        verify_repository_state=False,
    )

    with pytest.raises(VerificationExecutionIdentityError, match="exact runtime"):
        build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref="surface-ref:local",
        )
    with pytest.raises(VerificationExecutionIdentityError, match="paired"):
        build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref="surface-ref:local",
            typescript_runtime_fingerprint=DIGESTS[10],
        )

    first = build_verification_execution_identity(
        plan,
        unit,
        execution_surface_ref="surface-ref:local",
        typescript_runtime_fingerprint=DIGESTS[10],
        typescript_version_ref="typescript-version-ref:7.0.2",
    )
    changed = build_verification_execution_identity(
        plan,
        unit,
        execution_surface_ref="surface-ref:local",
        typescript_runtime_fingerprint=DIGESTS[12],
        typescript_version_ref="typescript-version-ref:7.0.3",
    )

    assert first.identity_fingerprint != changed.identity_fingerprint


@pytest.mark.parametrize(
    "mutated_unit",
    (
        _unit(needs=("unit:dependency",)),
        _unit(unit_kind=VerificationUnitKind.AUDIT, command_refs=()),
        _unit(timeout_minutes=44),
        _unit(execution_surfaces=("local", "private")),
        _unit(command_refs=("command:other",)),
    ),
    ids=("needs", "kind", "timeout", "execution-surfaces", "commands"),
)
def test_supplied_unit_definition_must_match_exact_plan_binding(
    mutated_unit: VerificationUnit,
) -> None:
    with pytest.raises(VerificationExecutionIdentityError, match="exact plan binding"):
        _identity(unit=mutated_unit)


def test_correspondingly_rebound_unit_definition_is_accepted() -> None:
    dependency = _unit(
        unit_ref="unit:dependency",
        lane_ref="lane:dependency",
        command_refs=("command:dependency",),
    )
    changed = _unit(
        needs=(dependency.unit_ref,),
        timeout_minutes=44,
        execution_surfaces=("local", "private"),
        command_refs=("command:other",),
    )
    plan = _plan(bound_units=(dependency, changed))

    identity = _identity(plan, changed)

    assert identity.unit_definition_fingerprint == (
        verification_unit_definition_fingerprint(changed)
    )
    assert identity.verification_dag_fingerprint == plan.verification_dag_fingerprint


def test_exact_terminal_proof_is_reused_without_another_start(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()

    start = store.begin(identity)
    proof = _proof(identity)
    assert start.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert start.owner_token is not None
    assert store.complete(identity, owner_token=start.owner_token, terminal_proof=proof) == proof

    replay = store.begin(identity)
    assert replay.disposition is (
        VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )
    assert replay.terminal_proof == proof
    assert replay.owner_token is None


def test_deterministic_failure_is_terminal_and_cannot_rerun(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    proof = _proof(
        identity,
        status=VerificationTerminalStatus.FAILED,
        deterministic_failure=True,
    )
    assert start.owner_token is not None
    store.complete(identity, owner_token=start.owner_token, terminal_proof=proof)

    replay = store.begin(identity)
    assert replay.disposition is (
        VerificationExecutionFenceDisposition.DETERMINISTIC_FAILURE_REJECTED
    )
    assert replay.terminal_proof == proof
    assert replay.reason_ref == "reason-ref:verification:deterministic-failure-no-rerun"


def test_durable_start_without_terminal_requires_recovery(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()

    assert store.begin(identity).disposition is (
        VerificationExecutionFenceDisposition.START_GRANTED
    )
    replay = store.begin(identity)

    assert replay.disposition is VerificationExecutionFenceDisposition.RECOVERY_REQUIRED
    assert replay.reason_ref == "reason-ref:verification:durable-start-unsettled"
    assert replay.owner_token is None


def test_start_owner_can_abort_only_before_command_spawn(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    assert start.owner_token is not None

    with pytest.raises(VerificationExecutionFenceStateError, match="owner"):
        store.abort_prestart(identity, owner_token="f" * 64)

    store.abort_prestart(identity, owner_token=start.owner_token)
    retry = store.begin(identity)
    assert retry.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert retry.owner_token is not None

    proof = _proof(identity)
    store.complete(identity, owner_token=retry.owner_token, terminal_proof=proof)
    with pytest.raises(VerificationExecutionFenceStateError, match="cannot be aborted"):
        store.abort_prestart(identity, owner_token=retry.owner_token)


def test_concurrent_starts_converge_on_one_durable_start(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    barrier = threading.Barrier(12)

    def begin() -> VerificationExecutionFenceDisposition:
        barrier.wait(timeout=5)
        return store.begin(identity).disposition

    with ThreadPoolExecutor(max_workers=12) as pool:
        dispositions = tuple(pool.map(lambda _index: begin(), range(12)))

    assert dispositions.count(VerificationExecutionFenceDisposition.START_GRANTED) == 1
    assert dispositions.count(VerificationExecutionFenceDisposition.RECOVERY_REQUIRED) == 11


def test_different_exact_identity_has_an_independent_fence(tmp_path: Path) -> None:
    store = _store(tmp_path)

    first = store.begin(_identity())
    changed = store.begin(_identity(_plan(repository_sha="c" * 40)))

    assert first.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert changed.disposition is VerificationExecutionFenceDisposition.START_GRANTED


def test_exclusive_resource_attempt_is_global_to_sha_and_dependency_state(
    tmp_path: Path,
) -> None:
    unit = _unit(exclusive_resource_refs=("resource-ref:complete-pytest",))
    plan = _plan(bound_units=(unit,))
    store = _store(tmp_path)
    local_identity = _identity(plan, unit, surface="surface-ref:local")
    private_identity = _identity(plan, unit, surface="surface-ref:private")

    local_start = store.begin(local_identity)
    private_start = store.begin(private_identity)

    assert local_start.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert private_start.disposition is (
        VerificationExecutionFenceDisposition.EXCLUSIVE_RESOURCE_ATTEMPT_REJECTED
    )
    assert private_start.reason_ref == (
        "reason-ref:verification:exclusive-resource-attempt-already-recorded"
    )
    assert store.state_path_for(local_identity) == store.state_path_for(private_identity)


def test_changed_dependency_state_permits_a_new_exclusive_resource_attempt(
    tmp_path: Path,
) -> None:
    unit = _unit(exclusive_resource_refs=("resource-ref:complete-pytest",))
    plan = _plan(bound_units=(unit,))
    changed_plan = _plan(
        bound_units=(unit,),
        dependency_lock_fingerprints=(("uv.lock", DIGESTS[12]),),
    )
    store = _store(tmp_path)

    first = store.begin(_identity(plan, unit))
    changed = store.begin(_identity(changed_plan, unit))

    assert first.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert changed.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert store.state_path_for(_identity(plan, unit)) != store.state_path_for(
        _identity(changed_plan, unit)
    )


def test_exclusive_resource_terminal_proof_is_reused_only_by_exact_identity(
    tmp_path: Path,
) -> None:
    unit = _unit(exclusive_resource_refs=("resource-ref:complete-pytest",))
    plan = _plan(bound_units=(unit,))
    store = _store(tmp_path)
    local_identity = _identity(plan, unit, surface="surface-ref:local")
    private_identity = _identity(plan, unit, surface="surface-ref:private")
    start = store.begin(local_identity)
    assert start.owner_token is not None
    proof = _proof(local_identity)
    store.complete(local_identity, owner_token=start.owner_token, terminal_proof=proof)

    exact_replay = store.begin(local_identity)
    other_surface = store.begin(private_identity)

    assert exact_replay.disposition is (
        VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )
    assert exact_replay.terminal_proof == proof
    assert other_surface.disposition is (
        VerificationExecutionFenceDisposition.EXCLUSIVE_RESOURCE_ATTEMPT_REJECTED
    )
    assert other_surface.terminal_proof is None


def test_cross_identity_cannot_settle_or_abort_an_exclusive_resource_fence(
    tmp_path: Path,
) -> None:
    unit = _unit(exclusive_resource_refs=("resource-ref:complete-pytest",))
    plan = _plan(bound_units=(unit,))
    store = _store(tmp_path)
    local_identity = _identity(plan, unit, surface="surface-ref:local")
    private_identity = _identity(plan, unit, surface="surface-ref:private")
    start = store.begin(local_identity)
    assert start.owner_token is not None

    with pytest.raises(
        VerificationExecutionFenceStateError,
        match="another exact execution identity",
    ):
        store.complete(
            private_identity,
            owner_token=start.owner_token,
            terminal_proof=_proof(private_identity),
        )
    with pytest.raises(
        VerificationExecutionFenceStateError,
        match="another exact execution identity",
    ):
        store.abort_prestart(
            private_identity,
            owner_token=start.owner_token,
        )

    proof = _proof(local_identity)
    assert (
        store.complete(
            local_identity,
            owner_token=start.owner_token,
            terminal_proof=proof,
        )
        == proof
    )


def test_only_the_start_owner_can_settle_and_settlement_is_idempotent(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    proof = _proof(identity)
    assert start.owner_token is not None

    with pytest.raises(VerificationExecutionFenceStateError, match="owner"):
        store.complete(identity, owner_token="f" * 64, terminal_proof=proof)
    assert store.complete(identity, owner_token=start.owner_token, terminal_proof=proof) == proof
    assert store.complete(identity, owner_token=start.owner_token, terminal_proof=proof) == proof

    conflicting = build_verification_execution_terminal_proof(
        identity,
        status=VerificationTerminalStatus.PASSED,
        receipt_ref=f"receipt:verification:{DIGESTS[12]}",
        result_refs=(f"result-ref:verification:{DIGESTS[14]}",),
        output_digest=DIGESTS[11],
        completed_at=COMPLETED_AT,
    )
    with pytest.raises(VerificationExecutionFenceStateError, match="different"):
        store.complete(
            identity,
            owner_token=start.owner_token,
            terminal_proof=conflicting,
        )


def test_completion_before_durable_start_timestamp_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    assert start.owner_token is not None

    with pytest.raises(VerificationExecutionFenceStateError, match="precedes"):
        store.complete(
            identity,
            owner_token=start.owner_token,
            terminal_proof=_proof(identity, completed_at="2026-07-15T11:59:59Z"),
        )


def test_completion_after_bounded_execution_window_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    assert start.owner_token is not None

    with pytest.raises(VerificationExecutionFenceStateError, match="bounded duration"):
        store.complete(
            identity,
            owner_token=start.owner_token,
            terminal_proof=_proof(
                identity,
                completed_at="2026-07-17T12:00:01Z",
            ),
        )


def test_fence_is_bounded_by_exact_identity_count(tmp_path: Path) -> None:
    store = _store(tmp_path, max_entries=1)
    store.begin(_identity())

    with pytest.raises(VerificationExecutionFenceCapacityError, match="exhausted"):
        store.begin(_identity(_plan(repository_sha="c" * 40)))


@pytest.mark.parametrize("raw", (b"", b'{"schema_version":'))
def test_prelink_zero_or_partial_stage_is_reclaimed(
    tmp_path: Path,
    raw: bytes,
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    stage_path = state_path.parent / f".{state_path.name}.123.{'a' * 16}.tmp"
    stage_path.write_bytes(raw)
    stage_path.chmod(0o600)

    decision = store.begin(identity)

    assert decision.disposition is VerificationExecutionFenceDisposition.START_GRANTED
    assert not stage_path.exists()
    assert state_path.stat().st_nlink == 1


def test_repeated_prelink_crashes_do_not_grow_the_fence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    assert store.begin(identity).disposition is (
        VerificationExecutionFenceDisposition.START_GRANTED
    )

    for index in range(8):
        stage_path = state_path.parent / (
            f".{state_path.name}.{index + 1}.{'b' * 16}.tmp"
        )
        stage_path.write_bytes(b"partial")
        stage_path.chmod(0o600)
        assert store.begin(identity).disposition is (
            VerificationExecutionFenceDisposition.RECOVERY_REQUIRED
        )
        assert not stage_path.exists()

    assert {path.name for path in state_path.parent.iterdir()} == {
        ".verification-execution-fence.lock",
        state_path.name,
    }


def test_postlink_crash_is_recovered_to_one_durable_start(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    assert store.begin(identity).disposition is (
        VerificationExecutionFenceDisposition.START_GRANTED
    )
    stage_path = state_path.parent / f".{state_path.name}.123.{'c' * 16}.tmp"
    os.link(state_path, stage_path)
    assert state_path.stat().st_nlink == 2

    decision = store.begin(identity)

    assert decision.disposition is VerificationExecutionFenceDisposition.RECOVERY_REQUIRED
    assert not stage_path.exists()
    assert state_path.stat().st_nlink == 1


@pytest.mark.parametrize("unsafe_kind", ("symlink", "fifo", "hardlink", "mode"))
def test_publication_stage_substitution_fails_closed(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    stage_path = state_path.parent / f".{state_path.name}.123.{'d' * 16}.tmp"
    external = tmp_path / "external-stage"
    external.write_bytes(b"partial")
    external.chmod(0o600)
    if unsafe_kind == "symlink":
        stage_path.symlink_to(external)
    elif unsafe_kind == "fifo":
        os.mkfifo(stage_path, mode=0o600)
    elif unsafe_kind == "hardlink":
        os.link(external, stage_path)
    else:
        stage_path.write_bytes(b"partial")
        stage_path.chmod(0o644)

    with pytest.raises(VerificationExecutionFenceStateError, match="stage|publication"):
        store.begin(identity)


@pytest.mark.parametrize("unsafe_kind", ("symlink", "fifo", "hardlink"))
def test_state_target_rejects_symlink_fifo_and_hardlink(
    tmp_path: Path, unsafe_kind: str
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    external = tmp_path / "external"
    external.write_text("{}", encoding="utf-8")
    external.chmod(0o600)
    if unsafe_kind == "symlink":
        state_path.symlink_to(external)
    elif unsafe_kind == "fifo":
        os.mkfifo(state_path, mode=0o600)
    else:
        os.link(external, state_path)

    with pytest.raises(VerificationExecutionFenceStateError, match="unsafe"):
        store.begin(identity)


def test_symlinked_or_permissive_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(VerificationExecutionFenceError, match="root"):
        VerificationExecutionFence(linked)

    permissive = tmp_path / "permissive"
    permissive.mkdir(mode=0o755)
    with pytest.raises(VerificationExecutionFenceError, match="root"):
        VerificationExecutionFence(permissive)


def test_root_substitution_after_start_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    root = store.state_path_for(identity).parent
    moved = tmp_path / "moved-fence"
    root.rename(moved)
    root.mkdir(mode=0o700)

    with pytest.raises(VerificationExecutionFenceStateError, match="identity changed"):
        store.begin(identity)


def test_lock_is_initialized_once_and_deletion_fails_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    identity = _identity()
    lock_path = store.state_path_for(identity).parent / (
        ".verification-execution-fence.lock"
    )
    lock_path.unlink()

    with pytest.raises(VerificationExecutionFenceStateError, match="lock"):
        store.begin(identity)


@pytest.mark.parametrize("replacement_content", (b"", b"replacement"))
def test_valid_mode_lock_replacement_is_rejected(
    tmp_path: Path,
    replacement_content: bytes,
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    lock_path = store.state_path_for(identity).parent / (
        ".verification-execution-fence.lock"
    )
    lock_path.unlink()
    lock_path.write_bytes(replacement_content)
    lock_path.chmod(0o600)

    with pytest.raises(VerificationExecutionFenceStateError, match="lock"):
        store.begin(identity)


def test_preexisting_hardlinked_lock_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "hardlinked-lock-root"
    root.mkdir(mode=0o700)
    external = tmp_path / "external-lock"
    external.write_bytes(b"")
    external.chmod(0o600)
    os.link(external, root / ".verification-execution-fence.lock")

    with pytest.raises(VerificationExecutionFenceStateError, match="unsafe"):
        VerificationExecutionFence(root)


@pytest.mark.parametrize(
    "raw",
    (
        b"not-json",
        b'{"schema_version":"a","schema_version":"b"}',
        b'{"value":NaN}',
        b"[]",
        (b"[" * 1_100) + b"0" + (b"]" * 1_100),
        b'{"value":' + (b"9" * 5_000) + b"}",
    ),
)
def test_malformed_or_ambiguous_state_fails_closed(
    tmp_path: Path, raw: bytes
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    state_path = store.state_path_for(identity)
    state_path.write_bytes(raw)
    state_path.chmod(0o600)

    with pytest.raises(VerificationExecutionFenceStateError):
        store.begin(identity)


def test_terminal_state_is_content_free_and_never_persists_owner_token(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    identity = _identity()
    start = store.begin(identity)
    assert start.owner_token is not None
    store.complete(
        identity,
        owner_token=start.owner_token,
        terminal_proof=_proof(identity),
    )

    raw = store.state_path_for(identity).read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert start.owner_token not in raw
    assert str(tmp_path) not in raw
    assert payload["redaction_status"] == REDACTION_STATUS
    assert "raw_output" not in raw
    assert "environment" not in raw
    assert "credentials" not in raw


def test_terminal_proof_rejects_nonterminal_or_false_deterministic_claims() -> None:
    identity = _identity()
    with pytest.raises(VerificationExecutionIdentityError, match="must be typed"):
        build_verification_execution_terminal_proof(
            identity,
            status="passed",  # type: ignore[arg-type]
            receipt_ref=f"receipt:verification:{DIGESTS[12]}",
            result_refs=(f"result-ref:verification:{DIGESTS[13]}",),
            output_digest=DIGESTS[11],
            completed_at=COMPLETED_AT,
        )
    with pytest.raises(VerificationExecutionIdentityError, match="not terminal"):
        _proof(identity, status=VerificationTerminalStatus.UNKNOWN)
    with pytest.raises(VerificationExecutionIdentityError, match="contradicts"):
        build_verification_execution_terminal_proof(
            identity,
            status=VerificationTerminalStatus.PASSED,
            receipt_ref=f"receipt:verification:{DIGESTS[12]}",
            result_refs=(f"result-ref:verification:{DIGESTS[13]}",),
            output_digest=DIGESTS[11],
            completed_at=COMPLETED_AT,
            failure_reason_ref=(
                "reason-ref:verification:deterministic-code-failure"
            ),
            failure_evidence_ref=f"result-ref:verification:{DIGESTS[13]}",
        )


@pytest.mark.parametrize(
    ("reason_ref", "expected_category"),
    (
        (
            "reason-ref:verification:infrastructure-failure",
            VerificationExecutionFailureCategory.INFRASTRUCTURE_FAILURE,
        ),
        (
            "reason-ref:verification:execution-result-unknown",
            VerificationExecutionFailureCategory.UNKNOWN_EXECUTION,
        ),
    ),
)
def test_infrastructure_or_unknown_failure_cannot_be_relabelled_deterministic(
    reason_ref: str,
    expected_category: VerificationExecutionFailureCategory,
) -> None:
    identity = _identity()
    evidence_ref = f"result-ref:verification:{DIGESTS[13]}"
    proof = build_verification_execution_terminal_proof(
        identity,
        status=VerificationTerminalStatus.FAILED,
        receipt_ref=f"receipt:verification:{DIGESTS[12]}",
        result_refs=(evidence_ref,),
        output_digest=DIGESTS[11],
        completed_at=COMPLETED_AT,
        failure_reason_ref=reason_ref,
        failure_evidence_ref=evidence_ref,
    )
    assert proof.failure_category is expected_category
    assert proof.deterministic_failure is False

    relabelled = replace(
        proof,
        proof_ref=f"execution-proof:{'0' * 64}",
        proof_fingerprint="0" * 64,
        failure_category=(
            VerificationExecutionFailureCategory.DETERMINISTIC_CODE_FAILURE
        ),
    )
    fingerprint = verification_execution_terminal_proof_fingerprint(relabelled)
    relabelled = replace(
        relabelled,
        proof_ref=f"execution-proof:{fingerprint}",
        proof_fingerprint=fingerprint,
    )
    with pytest.raises(VerificationExecutionIdentityError, match="classification"):
        relabelled.validate()


def test_failure_evidence_must_be_in_the_terminal_result_set() -> None:
    with pytest.raises(VerificationExecutionIdentityError, match="member"):
        build_verification_execution_terminal_proof(
            _identity(),
            status=VerificationTerminalStatus.FAILED,
            receipt_ref=f"receipt:verification:{DIGESTS[12]}",
            result_refs=(f"result-ref:verification:{DIGESTS[13]}",),
            output_digest=DIGESTS[11],
            completed_at=COMPLETED_AT,
            failure_reason_ref=(
                "reason-ref:verification:deterministic-code-failure"
            ),
            failure_evidence_ref=f"result-ref:verification:{DIGESTS[14]}",
        )


@pytest.mark.parametrize(
    ("receipt_ref", "result_ref"),
    (
        ("receipt:focused", f"result-ref:verification:{DIGESTS[13]}"),
        (
            "receipt:verification:api_key_live",
            f"result-ref:verification:{DIGESTS[13]}",
        ),
        (f"receipt:verification:{DIGESTS[12]}", "result-ref:focused"),
        (f"receipt:verification:{DIGESTS[12]}", "result-ref:ci:secret_live"),
    ),
)
def test_terminal_proof_rejects_plain_or_secret_like_identifiers(
    receipt_ref: str,
    result_ref: str,
) -> None:
    with pytest.raises(VerificationExecutionIdentityError):
        build_verification_execution_terminal_proof(
            _identity(),
            status=VerificationTerminalStatus.PASSED,
            receipt_ref=receipt_ref,
            result_refs=(result_ref,),
            output_digest=DIGESTS[11],
            completed_at=COMPLETED_AT,
        )
