import pytest

from tests.test_authority_dispatcher import _constraints
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    TrustMode,
)
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanConflictError,
)


def test_other_mission_lease_is_denied_before_plan_or_dispatch(tmp_path) -> None:
    orchestrator, dispatcher, lease_store, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="other-mission-lease",
    )
    other_lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref="mission-ref:test-orchestration:other-mission",
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=_constraints(operation_limit=8),
            decision_reason_ref="reason-ref:test-orchestration-other-mission",
            safe_summary="Issue a lease for a different exact mission.",
        ),
        idempotency_ref="idempotency-ref:test-orchestration-other-mission",
    )
    assert other_lease is not None
    assert receipt.status == "issued"
    second = request.steps[1]
    changed_second = second.model_copy(
        update={
            "definition": second.definition.model_copy(
                update={"lease_ref": other_lease.lease_ref}
            ),
            "request": second.request.model_copy(
                update={"lease_ref": other_lease.lease_ref}
            ),
        }
    )
    changed = request.model_copy(update={"steps": [request.steps[0], changed_second]})

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_MISSION_LEASE_REQUIRED",
    ):
        orchestrator.run(
            changed,
            owner_ref="mission-owner-ref:test-orchestration:other-mission",
        )
    assert orchestrator.plan_store.list_receipts() == []
    assert orchestrator.step_store.receipts() == []
    assert dispatcher.list_receipts() == []


def test_accepted_plan_dependency_edge_drift_is_rejected(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="dependency-drift",
    )
    orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:dependency-drift-first",
    )
    started_before = sum(
        receipt.status == "started" for receipt in dispatcher.list_receipts()
    )
    changed_second = request.steps[1].model_copy(
        update={
            "definition": request.steps[1].definition.model_copy(
                update={"dependency_step_refs": []}
            )
        }
    )
    changed = request.model_copy(update={"steps": [request.steps[0], changed_second]})

    with pytest.raises(
        DurableMissionPlanConflictError,
        match="DURABLE_MISSION_PLAN_IMMUTABLE_CONFLICT",
    ):
        orchestrator.run(
            changed,
            owner_ref="mission-owner-ref:test-orchestration:dependency-drift-second",
        )
    assert (
        sum(receipt.status == "started" for receipt in dispatcher.list_receipts())
        == started_before
    )


def test_duplicate_self_and_cross_scope_graph_inputs_fail_before_mutation(
    tmp_path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="invalid-contract-graphs",
    )
    first_payload = request.steps[0].model_dump(mode="python")
    second_payload = request.steps[1].model_dump(mode="python")
    cases = [
        [first_payload, first_payload],
        [
            first_payload,
            {
                **second_payload,
                "definition": {
                    **second_payload["definition"],
                    "dependency_step_refs": [
                        request.steps[0].definition.step_ref,
                        request.steps[0].definition.step_ref,
                    ],
                },
            },
        ],
        [
            first_payload,
            {
                **second_payload,
                "definition": {
                    **second_payload["definition"],
                    "dependency_step_refs": [
                        request.steps[1].definition.step_ref,
                    ],
                },
            },
        ],
        [
            first_payload,
            {
                **second_payload,
                "definition": {
                    **second_payload["definition"],
                    "mission_ref": "mission-ref:test-orchestration:cross-mission",
                },
            },
        ],
        [
            first_payload,
            {
                **second_payload,
                "definition": {
                    **second_payload["definition"],
                    "run_ref": "run-ref:test-orchestration:cross-run",
                },
            },
        ],
    ]
    for steps in cases:
        payload = request.model_dump(mode="python")
        payload["steps"] = steps
        with pytest.raises(ValueError):
            type(request).model_validate(payload)

    assert orchestrator.plan_store.list_receipts() == []
    assert orchestrator.step_store.receipts() == []
    assert dispatcher.list_receipts() == []
