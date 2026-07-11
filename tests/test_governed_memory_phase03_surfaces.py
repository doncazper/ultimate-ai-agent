from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from tests.authority_helpers import issue_memory_write_authority_lease
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    ManualMemoryCandidateRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopAuthorityError,
    FounderLoopRepository,
)


def _lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:phase03-surface-memory-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.memory: [AuthorityCapability.write]},
        safe_summary="Phase 03 exact memory surface test lease.",
    )


def _request() -> MemoryReviewDecisionRequest:
    return MemoryReviewDecisionRequest(
        reviewer_ref="actor-ref:phase03-local-operator",
        source_refs=["source-ref:phase03:surface"],
        evidence_refs=["evidence-ref:phase03:surface"],
        blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    )


def _candidate(repo: FounderLoopRepository, slug: str) -> str:
    receipt = repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"{slug} governed candidate",
            safe_summary=f"{slug} bounded reviewed summary.",
            source_refs=[f"source-ref:phase03:{slug}"],
            provenance_refs=[f"provenance-ref:phase03:{slug}"],
            evidence_refs=[f"evidence-ref:phase03:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:phase03:candidate:{slug}",
    )
    return str(receipt["candidate_ref"])


def test_feedback_metadata_update_requires_exact_memory_lease(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = FounderLoopRepository(state_dir, active_authority_leases=[_lease()])
    accepted = repo.record_memory_review_decision(
        candidate_ref=_candidate(repo, "feedback-denied"),
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:feedback-denied-accept",
    )
    denied_repo = FounderLoopRepository(state_dir, active_authority_leases=[])
    request = MemoryFeedbackRequest(
        memory_record_ref=str(accepted["reviewed_recall_record_ref"]),
        feedback_kind="helpful",
        reviewer_ref="actor-ref:phase03-local-operator",
        source_refs=["source-ref:phase03:feedback-denied"],
        evidence_refs=["evidence-ref:phase03:feedback-denied"],
        blocked_state_refs=MEMORY_FEEDBACK_BLOCKED_STATE_REFS,
    )
    with pytest.raises(FounderLoopAuthorityError):
        denied_repo.record_memory_feedback(
            request=request,
            idempotency_key_ref="idempotency-ref:phase03:feedback-denied",
        )
    assert (
        denied_repo._fetch_all(
            "SELECT key_ref FROM memory_feedback_update_operations", ()
        )
        == []
    )
    assert denied_repo.list_memory_review_recall_records()[0][
        "trust_score"
    ] == pytest.approx(0.7)


def test_expire_api_and_cli_share_exact_replay_and_lease_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "founder-loop"
    authority_state_dir = tmp_path / "authority"
    issue_memory_write_authority_lease(authority_state_dir)
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    repo = FounderLoopRepository(state_dir)
    candidate_ref = _candidate(repo, "api-expire")
    accepted = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:api-expire-accept",
    )
    body = {
        "reviewer_ref": "actor-ref:phase03-api-expire",
        "source_refs": ["source-ref:phase03:api-expire"],
        "evidence_refs": ["evidence-ref:phase03:api-expire"],
    }
    client = TestClient(app)
    endpoint = f"/control-center/memory/review/{candidate_ref}/expire"
    assert client.post(endpoint, json=body).status_code == 428
    headers = {"x-uaa-idempotency-key": "idempotency-ref:phase03:api-expire"}
    response = client.post(endpoint, json=body, headers=headers)
    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["decision"] == "expire"
    assert receipt["suppressed_recall_record_refs"] == [
        accepted["reviewed_recall_record_ref"]
    ]
    assert (
        client.post(endpoint, json=body, headers=headers).json()["data"]["receipt_ref"]
        == receipt["receipt_ref"]
    )
    assert (
        client.post(
            endpoint,
            json={**body, "reviewer_ref": "actor-ref:phase03-api-changed"},
            headers=headers,
        ).status_code
        == 409
    )

    cli_state = tmp_path / "cli-founder-loop"
    cli_repo = FounderLoopRepository(cli_state)
    cli_candidate_ref = _candidate(cli_repo, "cli-expire")
    accept_result = cli_repo.record_memory_review_decision(
        candidate_ref=cli_candidate_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:cli-expire-accept",
    )
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(cli_state),
            "record-memory-decision",
            "--candidate-ref",
            cli_candidate_ref,
            "--decision",
            "expire",
            "--idempotency-ref",
            "idempotency-ref:phase03:cli-expire",
            "--reviewer-ref",
            "actor-ref:phase03-local-operator",
            "--source-ref",
            "source-ref:phase03:cli-expire",
            "--evidence-ref",
            "evidence-ref:phase03:cli-expire",
        ],
        env={**os.environ, AUTHORITY_STATE_DIR_ENV: str(authority_state_dir)},
        check=True,
        capture_output=True,
        text=True,
    )
    cli_receipt = json.loads(cli.stdout)["receipt"]
    assert cli_receipt["decision"] == "expire"
    assert cli_receipt["suppressed_recall_record_refs"] == [
        accept_result["reviewed_recall_record_ref"]
    ]

    denied_state = tmp_path / "denied-founder-loop"
    denied_repo = FounderLoopRepository(
        denied_state,
        active_authority_leases=[_lease()],
    )
    denied_ref = _candidate(denied_repo, "denied-expire")
    denied_repo.record_memory_review_decision(
        candidate_ref=denied_ref,
        decision="accept",
        request=_request(),
        idempotency_key_ref="idempotency-ref:phase03:denied-expire-accept",
    )
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(denied_state))
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "empty-authority"))
    denied_response = client.post(
        f"/control-center/memory/review/{denied_ref}/expire",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:phase03:no-lease"},
    )
    assert denied_response.status_code == 403
