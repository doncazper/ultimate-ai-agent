from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.verify_operational_maturity import _append_mock_fallback_fixture_failures


def test_operational_maturity_verifier_rejects_authoritative_action_mock_fixture() -> (
    None
):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = root / "apps/control-center/src/mocks/controlCenterData.ts"
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            """
export const mockControlCenterData = {
  founderActionsInbox: {
    items: [{
      status: "receipt_recorded",
      action_group_id: "receipt_recorded",
      local_task_commit_eligible: true,
      local_task_commit_receipt_ref: "receipt:founder-loop-local-task:mock",
      approval_envelope: {
        source: "python_core_action_inbox_read_model" as const,
        backend_owned: true,
      },
      receipt_visibility: {
        source: "mock_fallback_non_authoritative" as const,
        backend_owned: false,
        local_task_commit_receipt_ref: "receipt:founder-loop-local-task:mock",
        replay_posture: "idempotency_replay_available",
        conflict_posture: "conflicting_idempotency_payload_rejected",
        evidence_timeline_event_ref:
          "evidence-timeline-event:local-task:mock",
      },
    }],
  },
};
""",
            encoding="utf-8",
        )
        failures: list[str] = []

        _append_mock_fallback_fixture_failures(failures, root)

        assert any(
            "mock fallback must not claim python_core_action_inbox_read_model"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim local_task_commit_eligible true" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim committed local task receipt refs" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim receipt_recorded local task state" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim backend local task replay posture" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim backend local task conflict posture" in failure
            for failure in failures
        )


def test_operational_maturity_verifier_rejects_authoritative_source_readiness_mock_fixture() -> (
    None
):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = root / "apps/control-center/src/mocks/controlCenterData.ts"
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            """
const sourceReadinessPosture = {
  source: "python_core_source_readiness_read_model" as const,
  backend_owned: true,
};

const sourceReadinessProposalCandidates = [
  {
    source: "mock_fallback_non_authoritative" as const,
    backend_owned: true,
  },
];

export const mockControlCenterData = {
  founderSourceReadiness: {
    source: "python_core_source_readiness_read_model" as const,
    backend_owned: true,
    source_readiness_proposal_candidates: sourceReadinessProposalCandidates,
  },
  founderToday: {
    source_readiness_posture: sourceReadinessPosture,
  },
};
""",
            encoding="utf-8",
        )
        failures: list[str] = []

        _append_mock_fallback_fixture_failures(failures, root)

        assert any(
            "mock fallback must not claim backend-owned source readiness read models"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback source readiness posture must not claim backend_owned true"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback source readiness proposals must not be backend-owned"
            in failure
            for failure in failures
        )
