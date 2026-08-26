from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.social_publishing.contracts import (
    ApprovalDecision,
    ReconciliationObservation,
    RightsPosture,
    SocialPostDraft,
    DryRunScenario,
    SocialPublishingDryRunKernel,
    build_retry_plan,
    build_q30_fixture,
    build_q30_proposal_read_model,
    build_review_envelope,
    build_scenario,
    evaluate_variant_compatibility,
    reconcile_unknown_settlement,
)
from scripts.verify_social_publishing_q30 import verify


def test_q30_fixture_is_exact_content_free_and_non_authoritative() -> None:
    fixture = build_q30_fixture()
    assert [item.platform.value for item in fixture.capabilities] == [
        "instagram",
        "x",
        "tiktok",
    ]
    assert len(fixture.plan.targets) == 3
    assert fixture.draft.raw_content_included is False
    assert fixture.live_account_access_enabled is False
    assert fixture.network_access_enabled is False
    assert fixture.background_scheduler_enabled is False
    assert fixture.publishing_enabled is False
    assert fixture.plan.dry_run_only is True
    assert fixture.plan.external_write_enabled is False


def test_q30_backend_read_model_is_content_free_and_fail_closed() -> None:
    proposal = build_q30_proposal_read_model()
    assert proposal.status == "proposal_dry_run_ready"
    assert proposal.backend_owned is True
    assert proposal.read_only is True
    assert proposal.dry_run_only is True
    assert proposal.raw_content_included is False
    assert proposal.publishing_enabled is False
    assert proposal.external_write_enabled is False
    assert proposal.external_side_effect_performed is False
    assert "blocked-state:q30:no-live-publish" in proposal.blocked_authority_refs


def test_q30_p0_p6_verifier_passes() -> None:
    assert verify() == []


def test_q30_plan_and_approval_are_deterministic_and_exact_bound() -> None:
    first = build_q30_fixture()
    second = build_q30_fixture()
    assert first.plan == second.plan
    envelope = build_review_envelope(first.plan, ApprovalDecision.approved_for_dry_run)
    assert envelope.plan_fingerprint_ref == first.plan.plan_fingerprint_ref
    assert envelope.reviewed_target_refs == first.plan.target_refs
    assert envelope.live_authority_granted is False

    changed_identity = first.plan.model_dump(mode="python")
    changed_identity["plan_ref"] = "social-publish-plan-ref:q30:substituted"
    with pytest.raises(ValidationError, match="Q30_PLAN_FINGERPRINT_DRIFT"):
        type(first.plan).model_validate(changed_identity)


def test_q30_compatibility_blocks_unknown_rights_and_constraints() -> None:
    fixture = build_q30_fixture()
    variant = fixture.variants[0].model_copy(
        update={"rights_posture": RightsPosture.unknown}
    )
    finding = evaluate_variant_compatibility(variant, fixture.capabilities[0])[0]
    assert finding.severity.value == "blocking"

    capability = fixture.capabilities[0].model_copy(
        update={"unknown_constraint_refs": ("constraint-ref:q30:fixture-unknown",)}
    )
    finding = evaluate_variant_compatibility(fixture.variants[0], capability)[0]
    assert finding.severity.value == "unknown"


def test_q30_mixed_dry_run_preserves_success_and_limits_retry() -> None:
    fixture = build_q30_fixture()
    result = SocialPublishingDryRunKernel().execute(
        plan=fixture.plan,
        envelope=build_review_envelope(
            fixture.plan, ApprovalDecision.approved_for_dry_run
        ),
        scenario=build_scenario(fixture.plan, "mixed"),
    )
    assert len(result.succeeded_target_refs) == 1
    assert result.succeeded_target_refs[0] not in result.retry_eligible_target_refs
    assert len(result.retry_eligible_target_refs) == 2
    assert result.reconciliation_required_target_refs == ()
    assert all(item.external_side_effect_performed is False for item in result.receipts)
    retry = build_retry_plan(
        result, target_refs=(result.retry_eligible_target_refs[0],)
    )
    assert retry.new_approval_required is True
    with pytest.raises(ValueError, match="Q30_RETRY_TARGET_NOT_ELIGIBLE"):
        build_retry_plan(result, target_refs=result.succeeded_target_refs)


def test_q30_replay_is_idempotent_and_conflict_fails_closed() -> None:
    fixture = build_q30_fixture()
    envelope = build_review_envelope(
        fixture.plan, ApprovalDecision.approved_for_dry_run
    )
    kernel = SocialPublishingDryRunKernel()
    scenario = build_scenario(fixture.plan, "success")
    first = kernel.execute(plan=fixture.plan, envelope=envelope, scenario=scenario)
    replay = kernel.execute(plan=fixture.plan, envelope=envelope, scenario=scenario)
    assert replay.result_ref == first.result_ref
    assert replay.replayed is True
    with pytest.raises(ValueError, match="Q30_IDEMPOTENCY_CONFLICT"):
        kernel.execute(
            plan=fixture.plan,
            envelope=envelope,
            scenario=build_scenario(fixture.plan, "mixed"),
        )


def test_q30_concurrent_exact_replay_has_one_owner_and_no_drift() -> None:
    fixture = build_q30_fixture()
    envelope = build_review_envelope(
        fixture.plan, ApprovalDecision.approved_for_dry_run
    )
    scenario = build_scenario(fixture.plan, "success")
    kernel = SocialPublishingDryRunKernel()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: kernel.execute(
                    plan=fixture.plan, envelope=envelope, scenario=scenario
                ),
                range(8),
            )
        )

    assert len({result.result_ref for result in results}) == 1
    assert sum(result.replayed for result in results) == 7
    assert all(result.external_side_effect_performed is False for result in results)


def test_q30_unknown_requires_reconciliation_before_retry() -> None:
    fixture = build_q30_fixture()
    result = SocialPublishingDryRunKernel().execute(
        plan=fixture.plan,
        envelope=build_review_envelope(
            fixture.plan, ApprovalDecision.approved_for_dry_run
        ),
        scenario=build_scenario(fixture.plan, "unknown"),
    )
    target_ref = result.reconciliation_required_target_refs[0]
    assert target_ref not in result.retry_eligible_target_refs
    still_unknown = reconcile_unknown_settlement(
        result,
        target_ref=target_ref,
        observation=ReconciliationObservation.still_unknown,
    )
    assert still_unknown.retry_eligible is False
    assert still_unknown.new_approval_required is False
    unmatched = reconcile_unknown_settlement(
        result,
        target_ref=target_ref,
        observation=ReconciliationObservation.unmatched,
    )
    assert unmatched.retry_eligible is True
    assert unmatched.new_approval_required is True


def test_q30_rejected_review_cannot_run() -> None:
    fixture = build_q30_fixture()
    with pytest.raises(ValueError, match="Q30_DRY_RUN_NOT_APPROVED"):
        SocialPublishingDryRunKernel().execute(
            plan=fixture.plan,
            envelope=build_review_envelope(fixture.plan, ApprovalDecision.rejected),
            scenario=build_scenario(fixture.plan, "success"),
        )


def test_q30_kernel_revalidates_fast_copies_at_authority_boundary() -> None:
    fixture = build_q30_fixture()
    envelope = build_review_envelope(
        fixture.plan, ApprovalDecision.approved_for_dry_run
    )
    scenario = build_scenario(fixture.plan, "success")

    forged_plan = fixture.plan.model_copy(update={"publishing_enabled": True})
    with pytest.raises(ValidationError):
        SocialPublishingDryRunKernel().execute(
            plan=forged_plan, envelope=envelope, scenario=scenario
        )

    forged_envelope = envelope.model_copy(update={"live_authority_granted": True})
    with pytest.raises(ValidationError):
        SocialPublishingDryRunKernel().execute(
            plan=fixture.plan, envelope=forged_envelope, scenario=scenario
        )


def test_q30_retry_rejects_forged_result_inventory() -> None:
    fixture = build_q30_fixture()
    result = SocialPublishingDryRunKernel().execute(
        plan=fixture.plan,
        envelope=build_review_envelope(
            fixture.plan, ApprovalDecision.approved_for_dry_run
        ),
        scenario=build_scenario(fixture.plan, "success"),
    )
    forged = result.model_copy(
        update={
            "succeeded_target_refs": (),
            "retry_eligible_target_refs": (result.succeeded_target_refs[0],),
        }
    )
    with pytest.raises(ValidationError, match="Q30_RESULT_SUCCESS_INVENTORY_DRIFT"):
        build_retry_plan(forged, target_refs=forged.retry_eligible_target_refs)


def test_q30_secret_like_or_raw_content_fields_fail_closed() -> None:
    fixture = build_q30_fixture()
    payload = fixture.draft.model_dump(mode="json")
    payload["campaign_ref"] = "campaign-ref:api_key-value"
    with pytest.raises(ValidationError, match="unsafe content"):
        SocialPostDraft.model_validate(payload)
    payload = fixture.draft.model_dump(mode="json")
    payload["rights_posture"] = RightsPosture.unknown
    payload["raw_content_included"] = True
    with pytest.raises(ValidationError):
        SocialPostDraft.model_validate(payload)

    with pytest.raises(ValidationError, match="unsafe content"):
        DryRunScenario.model_validate(
            {
                "scenario_ref": "dry-run-scenario-ref:q30:unsafe",
                "plan_ref": fixture.plan.plan_ref,
                "outcome_by_target_ref": {
                    "social-target-ref:api_key-value": "succeeded"
                },
            }
        )


@pytest.mark.parametrize(
    "command",
    [
        ["validate"],
        ["dry-run", "--scenario", "mixed"],
        ["reconcile", "--observation", "unmatched"],
    ],
)
def test_q30_cli_emits_structured_non_authoritative_json(command: list[str]) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/dev/uaa_social_publishing.py", *command],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload.get("publishing_enabled", False) is False
    assert payload.get("external_side_effect_performed", False) is False
