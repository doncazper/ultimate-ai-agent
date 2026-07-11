from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path

import pytest

from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepCorruptionError,
    MissionStepDefinition,
    MissionStepOrchestrationContext,
    MissionStepStatus,
    MissionStepStore,
    _entry_hash,
)
from ultimate_ai_agent.core.time import utc_now


def _definition(
    suffix: str = "one", *, dependencies: list[str] | None = None
) -> MissionStepDefinition:
    return MissionStepDefinition(
        mission_ref=f"mission-ref:test:{suffix}",
        run_ref=f"run-ref:test:{suffix}",
        step_ref=f"mission-step-ref:test:{suffix}",
        capability_ref="authority-capability-ref:filesystem-metadata-v1",
        adapter_ref="authority-adapter-ref:filesystem-metadata-v1",
        lease_ref=f"authority-lease-ref:test:{suffix}",
        dependency_step_refs=dependencies or [],
        deadline=utc_now() + timedelta(minutes=5),
        safe_summary="Run one exact governed metadata mission step.",
    )


def _plan_context(definition: MissionStepDefinition) -> MissionStepOrchestrationContext:
    return MissionStepOrchestrationContext(
        plan_ref=definition.orchestration_plan_ref or "mission-plan-ref:test:missing",
        plan_fingerprint_ref="mission-plan-fingerprint-ref:test:unit",
        plan_receipt_ref="durable-mission-plan-receipt-ref:test:unit",
        ordered_step_refs=[definition.step_ref],
    )


def test_store_creates_and_claims_without_granting_execution_authority(
    tmp_path: Path,
) -> None:
    store = MissionStepStore(tmp_path)
    pending = store.create(_definition())
    claimed = store.claim(
        pending.definition.step_ref,
        owner_ref="mission-owner-ref:test:a",
        ttl_seconds=30,
    )
    read_model = store.read(pending.definition.step_ref)

    assert pending.status == MissionStepStatus.pending.value
    assert claimed.status == MissionStepStatus.claimed.value
    assert claimed.generation == 1
    assert read_model.execution_authority_granted is False
    assert read_model.autonomous_retry_enabled is False


def test_two_store_instances_cannot_both_claim_one_step(tmp_path: Path) -> None:
    first = MissionStepStore(tmp_path)
    second = MissionStepStore(tmp_path)
    step = first.create(_definition("race"))

    def claim(store: MissionStepStore, owner: str) -> str:
        try:
            store.claim(step.definition.step_ref, owner_ref=owner, ttl_seconds=30)
            return "claimed"
        except MissionStepConflictError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda item: claim(*item),
                [
                    (first, "mission-owner-ref:test:first"),
                    (second, "mission-owner-ref:test:second"),
                ],
            )
        )

    assert sorted(results) == ["blocked", "claimed"]
    assert len(first.receipts()) == 2


def test_expired_owner_is_fenced_after_reclaim(tmp_path: Path) -> None:
    start = utc_now()
    current = [start]
    store = MissionStepStore(tmp_path, clock=lambda: current[0])
    step = store.create(_definition("fence"))
    first = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:first",
        ttl_seconds=1,
    )
    current[0] += timedelta(seconds=2)
    second = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:second",
        ttl_seconds=30,
    )

    assert second.generation == first.generation + 1
    with pytest.raises(MissionStepConflictError, match="MISSION_STEP_STALE_FENCE"):
        store.complete(
            step.definition.step_ref,
            owner_ref=first.owner_ref or "",
            claim_ref=first.claim_ref or "",
            generation=first.generation,
            status=MissionStepStatus.succeeded,
            reason_refs=["reason-ref:mission-step:succeeded"],
        )


def test_dispatch_intent_is_immutable_and_survives_reclaim(tmp_path: Path) -> None:
    start = utc_now()
    current = [start]
    store = MissionStepStore(tmp_path, clock=lambda: current[0])
    step = store.create(_definition("intent"))
    first = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:first",
        ttl_seconds=1,
    )
    intent = store.record_dispatch_intent(
        step.definition.step_ref,
        owner_ref=first.owner_ref or "",
        claim_ref=first.claim_ref or "",
        generation=first.generation,
        dispatch_ref="authority-dispatch-ref:test:intent",
        dispatch_request_fingerprint_ref="request-fingerprint-ref:test:intent",
    )
    current[0] += timedelta(seconds=2)
    second = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:second",
        ttl_seconds=30,
        dispatch_ref=intent.dispatch_ref,
        dispatch_request_fingerprint_ref=(intent.dispatch_request_fingerprint_ref),
    )

    assert second.dispatch_ref == intent.dispatch_ref
    assert (
        second.dispatch_request_fingerprint_ref
        == intent.dispatch_request_fingerprint_ref
    )
    with pytest.raises(
        MissionStepConflictError, match="MISSION_STEP_DISPATCH_INTENT_CONFLICT"
    ):
        store.record_dispatch_intent(
            step.definition.step_ref,
            owner_ref=second.owner_ref or "",
            claim_ref=second.claim_ref or "",
            generation=second.generation,
            dispatch_ref="authority-dispatch-ref:test:other",
            dispatch_request_fingerprint_ref="request-fingerprint-ref:test:other",
        )
    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT",
    ):
        store.record_dispatch_intent(
            step.definition.step_ref,
            owner_ref=second.owner_ref or "",
            claim_ref=second.claim_ref or "",
            generation=second.generation,
            dispatch_ref=intent.dispatch_ref or "",
            dispatch_request_fingerprint_ref=(
                "request-fingerprint-ref:test:changed-target"
            ),
        )


def test_dependency_and_deadline_fail_closed(tmp_path: Path) -> None:
    store = MissionStepStore(tmp_path)
    dependency = store.create(_definition("dependency"))
    child = store.create(
        _definition("child", dependencies=[dependency.definition.step_ref]).model_copy(
            update={
                "mission_ref": dependency.definition.mission_ref,
                "run_ref": dependency.definition.run_ref,
            }
        )
    )

    with pytest.raises(
        MissionStepConflictError, match="MISSION_STEP_DEPENDENCY_NOT_READY"
    ):
        store.claim(
            child.definition.step_ref,
            owner_ref="mission-owner-ref:test:child",
            ttl_seconds=30,
        )

    expired = _definition("expired").model_copy(
        update={"deadline": utc_now() - timedelta(seconds=1)}
    )
    store.create(expired)
    result = store.claim(
        expired.step_ref,
        owner_ref="mission-owner-ref:test:expired",
        ttl_seconds=30,
    )
    assert result.status == MissionStepStatus.failed.value
    assert "reason-ref:mission-step:deadline-expired" in result.reason_refs


def test_hash_chain_and_definition_conflicts_fail_closed(tmp_path: Path) -> None:
    store = MissionStepStore(tmp_path)
    definition = _definition("tamper")
    store.create(definition)

    with pytest.raises(
        MissionStepConflictError, match="MISSION_STEP_DEFINITION_CONFLICT"
    ):
        store.create(
            definition.model_copy(
                update={"safe_summary": "Conflicting mission step definition."}
            )
        )

    payload = store.receipts_path.read_text(encoding="utf-8")
    store.receipts_path.write_text(
        payload.replace("pending a fenced", "tampered unsafe"),
        encoding="utf-8",
    )
    with pytest.raises(
        MissionStepCorruptionError, match="MISSION_STEP_HASH_CHAIN_INVALID"
    ):
        store.receipts()


def test_correctly_rehashed_generation_jump_fails_closed(tmp_path: Path) -> None:
    store = MissionStepStore(tmp_path)
    step = store.create(_definition("semantic-tamper"))
    claimed = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:semantic-tamper",
        ttl_seconds=30,
    )
    receipts = store.receipts()
    tampered = claimed.model_copy(
        update={
            "generation": 9,
            "entry_hash_ref": "mission-step-entry-hash-ref:pending",
        }
    )
    tampered = tampered.model_copy(update={"entry_hash_ref": _entry_hash(tampered)})
    store.receipts_path.write_text(
        "\n".join(
            json.dumps(item.model_dump(mode="json"), sort_keys=True)
            for item in [receipts[0], tampered]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        MissionStepCorruptionError, match="MISSION_STEP_TRANSITION_INVALID"
    ):
        store.receipts()


def test_correctly_rehashed_owner_swap_fails_closed(tmp_path: Path) -> None:
    store = MissionStepStore(tmp_path)
    step = store.create(_definition("owner-tamper"))
    claimed = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:owner-a",
        ttl_seconds=30,
    )
    receipts = store.receipts()
    tampered = claimed.model_copy(
        update={
            "owner_ref": "mission-owner-ref:test:owner-b",
            "claim_ref": "mission-step-claim-ref:test:forged",
            "sequence": 3,
            "previous_entry_hash_ref": claimed.entry_hash_ref,
            "entry_hash_ref": "mission-step-entry-hash-ref:pending",
        }
    )
    tampered = tampered.model_copy(update={"entry_hash_ref": _entry_hash(tampered)})
    store.receipts_path.write_text(
        "\n".join(
            json.dumps(item.model_dump(mode="json"), sort_keys=True)
            for item in [*receipts, tampered]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        MissionStepCorruptionError,
        match="MISSION_STEP_CLAIM_BINDING_INVALID",
    ):
        store.receipts()


def test_success_without_durable_dispatch_evidence_is_rejected(
    tmp_path: Path,
) -> None:
    store = MissionStepStore(tmp_path)
    step = store.create(_definition("forged-success"))
    claimed = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:forged-success",
        ttl_seconds=30,
    )

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_SUCCEEDED_DISPATCH_EVIDENCE_REQUIRED",
    ):
        store.complete(
            step.definition.step_ref,
            owner_ref=claimed.owner_ref or "",
            claim_ref=claimed.claim_ref or "",
            generation=claimed.generation,
            status=MissionStepStatus.succeeded,
            reason_refs=["reason-ref:mission-step:forged-success"],
        )


@pytest.mark.parametrize("ttl_seconds", [0, 301])
def test_heartbeat_rejects_out_of_bounds_ttl(
    tmp_path: Path,
    ttl_seconds: int,
) -> None:
    store = MissionStepStore(tmp_path)
    step = store.create(_definition(f"heartbeat-{ttl_seconds}"))
    claimed = store.claim(
        step.definition.step_ref,
        owner_ref="mission-owner-ref:test:heartbeat",
        ttl_seconds=30,
    )

    with pytest.raises(ValueError, match="MISSION_STEP_CLAIM_TTL_INVALID"):
        store.heartbeat(
            step.definition.step_ref,
            owner_ref=claimed.owner_ref or "",
            claim_ref=claimed.claim_ref or "",
            generation=claimed.generation,
            ttl_seconds=ttl_seconds,
        )


def test_unsafe_refs_and_naive_deadlines_are_rejected() -> None:
    with pytest.raises(ValueError):
        _definition("unsafe").model_copy(
            update={"mission_ref": "malformed safe ref"}
        ).__class__.model_validate(
            {
                **_definition("unsafe").model_dump(mode="python"),
                "mission_ref": "malformed safe ref",
            }
        )
    with pytest.raises(ValueError, match="MISSION_STEP_DEADLINE_TIMEZONE_REQUIRED"):
        MissionStepDefinition.model_validate(
            {
                **_definition("naive").model_dump(mode="python"),
                "deadline": utc_now().replace(tzinfo=None),
            }
        )


def test_planned_dispatch_binding_rejects_claim_drift(tmp_path: Path) -> None:
    store = MissionStepStore(tmp_path)
    definition = MissionStepDefinition.model_validate(
        {
            **_definition("planned-binding").model_dump(mode="python"),
            "orchestration_plan_ref": "mission-plan-ref:test:planned-binding",
            "planned_dispatch_ref": "authority-dispatch-ref:test:planned-binding",
            "planned_dispatch_request_fingerprint_ref": (
                "request-fingerprint-ref:test:planned-binding"
            ),
        }
    )
    context = _plan_context(definition)
    store._bind_plan_binding_resolver(  # noqa: SLF001
        lambda candidate: context if candidate == definition else None
    )
    store.create(definition)

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_PLANNED_DISPATCH_FINGERPRINT_CONFLICT",
    ):
        store.claim(
            definition.step_ref,
            owner_ref="mission-owner-ref:test:planned-binding",
            ttl_seconds=30,
            dispatch_ref=definition.planned_dispatch_ref,
            dispatch_request_fingerprint_ref=(
                "request-fingerprint-ref:test:planned-binding-drift"
            ),
            orchestration_context=context,
        )


def test_planned_step_cannot_assert_terminal_dispatch_truth_without_receipt(
    tmp_path: Path,
) -> None:
    store = MissionStepStore(tmp_path)
    definition = MissionStepDefinition.model_validate(
        {
            **_definition("planned-terminal-proof").model_dump(mode="python"),
            "orchestration_plan_ref": "mission-plan-ref:test:planned-terminal-proof",
            "planned_dispatch_ref": "authority-dispatch-ref:test:planned-terminal-proof",
            "planned_dispatch_request_fingerprint_ref": (
                "request-fingerprint-ref:test:planned-terminal-proof"
            ),
        }
    )
    context = _plan_context(definition)
    store._bind_plan_binding_resolver(  # noqa: SLF001
        lambda candidate: context if candidate == definition else None
    )
    store.create(definition)
    claimed = store.claim(
        definition.step_ref,
        owner_ref="mission-owner-ref:test:planned-terminal-proof",
        ttl_seconds=30,
        dispatch_ref=definition.planned_dispatch_ref,
        dispatch_request_fingerprint_ref=(
            definition.planned_dispatch_request_fingerprint_ref
        ),
        orchestration_context=context,
    )

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_TERMINAL_DISPATCH_EVIDENCE_REQUIRED",
    ):
        store.complete(
            definition.step_ref,
            owner_ref=claimed.owner_ref or "",
            claim_ref=claimed.claim_ref or "",
            generation=claimed.generation,
            status=MissionStepStatus.failed,
            reason_refs=["reason-ref:mission-step:dispatch-failed"],
        )


def test_fail_fast_halt_rejects_terminal_evidence_from_another_plan(
    tmp_path: Path,
) -> None:
    store = MissionStepStore(tmp_path)
    target = MissionStepDefinition.model_validate(
        {
            **_definition("halt-target").model_dump(mode="python"),
            "orchestration_plan_ref": "mission-plan-ref:test:halt-target",
            "planned_dispatch_ref": "authority-dispatch-ref:test:halt-target",
            "planned_dispatch_request_fingerprint_ref": (
                "request-fingerprint-ref:test:halt-target"
            ),
        }
    )
    context = _plan_context(target)
    store._bind_plan_binding_resolver(  # noqa: SLF001
        lambda candidate: context if candidate == target else None
    )
    store.create(target)
    foreign = _definition("halt-foreign").model_copy(
        update={"mission_ref": target.mission_ref, "run_ref": target.run_ref}
    )
    foreign_pending = store.create(foreign)
    foreign_claim = store.claim(
        foreign_pending.definition.step_ref,
        owner_ref="mission-owner-ref:test:halt-foreign",
        ttl_seconds=30,
    )
    store.complete(
        foreign.step_ref,
        owner_ref=foreign_claim.owner_ref or "",
        claim_ref=foreign_claim.claim_ref or "",
        generation=foreign_claim.generation,
        status=MissionStepStatus.failed,
        reason_refs=["reason-ref:mission-step:test-foreign-failed"],
    )

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_FAIL_FAST_SCOPE_MISMATCH",
    ):
        store.halt_from_fail_fast_terminal(
            target.step_ref,
            terminal_step_ref=foreign.step_ref,
        )


def test_dependency_block_is_durable_and_forged_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    store = MissionStepStore(tmp_path)
    plan_ref = "mission-plan-ref:test:dependency-block"
    dependency_definition = MissionStepDefinition.model_validate(
        {
            **_definition("dependency-block-parent").model_dump(mode="python"),
            "orchestration_plan_ref": plan_ref,
            "planned_dispatch_ref": "authority-dispatch-ref:test:dependency-block-parent",
            "planned_dispatch_request_fingerprint_ref": (
                "request-fingerprint-ref:test:dependency-block-parent"
            ),
            "deadline": utc_now() - timedelta(seconds=1),
        }
    )
    child_definition = MissionStepDefinition.model_validate(
        {
            **_definition("dependency-block-child").model_dump(mode="python"),
            "mission_ref": dependency_definition.mission_ref,
            "run_ref": dependency_definition.run_ref,
            "dependency_step_refs": [dependency_definition.step_ref],
            "orchestration_plan_ref": plan_ref,
            "planned_dispatch_ref": "authority-dispatch-ref:test:dependency-block-child",
            "planned_dispatch_request_fingerprint_ref": (
                "request-fingerprint-ref:test:dependency-block-child"
            ),
        }
    )
    context = MissionStepOrchestrationContext(
        plan_ref=plan_ref,
        plan_fingerprint_ref="mission-plan-fingerprint-ref:test:dependency-block",
        plan_receipt_ref="durable-mission-plan-receipt-ref:test:dependency-block",
        ordered_step_refs=[dependency_definition.step_ref, child_definition.step_ref],
    )
    store._bind_plan_binding_resolver(  # noqa: SLF001
        lambda candidate: (
            context
            if candidate == dependency_definition or candidate == child_definition
            else None
        )
    )
    dependency = store.create(dependency_definition)
    child = store.create(child_definition)
    store.expire_deadline(dependency.definition.step_ref)
    blocked = store.block_from_terminal_dependency(
        child.definition.step_ref,
        dependency_step_ref=dependency.definition.step_ref,
    )
    assert blocked.status == MissionStepStatus.dependency_blocked.value
    assert blocked.blocked_dependency_step_ref == dependency.definition.step_ref

    receipts = store.receipts()
    tampered = blocked.model_copy(
        update={
            "evidence_refs": [receipts[-2].receipt_ref],
            "entry_hash_ref": "mission-step-entry-hash-ref:pending",
        }
    )
    tampered = tampered.model_copy(update={"entry_hash_ref": _entry_hash(tampered)})
    store.receipts_path.write_text(
        "\n".join(
            json.dumps(item.model_dump(mode="json"), sort_keys=True)
            for item in [*receipts[:-1], tampered]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        MissionStepCorruptionError,
        match="MISSION_STEP_DEPENDENCY_BLOCK_EVIDENCE_INVALID",
    ):
        store.receipts()
