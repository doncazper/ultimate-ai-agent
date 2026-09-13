from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.runtime_gateway import (
    build_goal_mutation_approval_decision_idempotency_ref,
)


SHA = "7" * 40
ACTION_PATH = "/control-center/actions/local-task-create-scorecard/approve"
ORIGIN = "http://127.0.0.1:5173"


def _bound_headers(tmp_path, *, now=None) -> dict[str, str]:
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "binding-state"),
        now=now,
        identity=build_identity(env={"UAA_BUILD_COMMIT": SHA}),
    )
    return {
        "Origin": ORIGIN,
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{SHA}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }


def _authority_preview_payload() -> dict[str, object]:
    return {
        "action_ref": "authority-action-ref:backend-truth-preview",
        "domain": "workspace",
        "capability": "write",
        "safe_summary": "Evaluate exact local workspace authority.",
        "resource_refs": ["resource-ref:backend-truth-preview"],
        "route_ref": "POST /control-center/actions/example/local-task/commit",
        "lane_ref": "lane-ref:backend-truth-preview",
        "requested_mode": "ask_before_changes",
        "draft_fallback_available": True,
        "rollback_ref": "rollback-ref:backend-truth-preview",
        "safe_disable_ref": "safe-disable-ref:backend-truth-preview",
    }


def test_browser_critical_mutation_requires_backend_truth_binding(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        ACTION_PATH,
        headers={"Origin": ORIGIN},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["code"] == ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert (
        "X-UAA-Backend-Revision-Ref"
        in response.headers["access-control-expose-headers"]
    )


@pytest.mark.parametrize(
    ("header_name", "replacement"),
    [
        ("X-UAA-Control-Center-Mutation-Binding", "backend-truth.v0"),
        (
            "X-UAA-Expected-Backend-Revision-Ref",
            "commit-ref:git:" + "9" * 40,
        ),
        (
            "X-UAA-Expected-Backend-Instance-Ref",
            "backend-instance-ref:control-center:" + "a" * 32,
        ),
        ("X-UAA-Expected-Backend-Truth-Ref", "proof-ref:substituted"),
    ],
)
def test_browser_critical_mutation_rejects_provenance_substitution(
    monkeypatch,
    tmp_path,
    header_name: str,
    replacement: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    headers = _bound_headers(tmp_path)
    headers[header_name] = replacement

    response = TestClient(app).post(ACTION_PATH, headers=headers, json={})

    assert response.status_code == 409
    assert response.json()["code"] == ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_exact_browser_mutation_binding_reaches_existing_route_checks(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        ACTION_PATH,
        headers=_bound_headers(tmp_path),
        json={},
    )

    assert response.status_code != 409
    assert response.json().get("code") != ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")


def test_exact_browser_goal_binding_reaches_goal_route(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_GOAL_RUNTIME_STATE_DIR", str(tmp_path / "goals"))

    client = TestClient(app)
    payload = {
        "text_redaction_posture": ("operator_authored_redacted_summary_only"),
        "objective": "Verify exact browser provenance.",
        "desired_outcome": "One bounded local goal record.",
        "success_criteria": ["The exact provenance binding is current."],
        "constraints": ["No runtime execution."],
        "in_scope_resource_refs": ["resource-ref:browser-goal-binding"],
        "stop_condition": "Stop on provenance disagreement.",
    }
    mutation_headers = {
        **_bound_headers(tmp_path),
        "X-UAA-Idempotency-Key": "idempotency-ref:browser-goal-binding",
    }
    prepared = client.post(
        "/api/runtime/goals/approval-requests/create",
        headers=mutation_headers,
        json=payload,
    ).json()
    spec = prepared["data"]["approval_request"]
    decided = client.post(
        (
            "/api/runtime/goals/approval-requests/"
            f"{spec['approval_request_ref']}/decision"
        ),
        headers={
            **_bound_headers(tmp_path),
            "X-UAA-Idempotency-Key": (
                build_goal_mutation_approval_decision_idempotency_ref(
                    spec["approval_request_ref"]
                )
            ),
        },
        json={
            "decision": "approve",
            "decision_reason_ref": "reason-ref:browser-goal-binding",
        },
    )
    assert decided.status_code != 409
    assert decided.json()["success"] is True
    response = client.post(
        "/api/runtime/goals",
        headers={
            **mutation_headers,
            "X-UAA-Goal-Approval-Ref": spec["approval_ref"],
        },
        json=payload,
    )

    assert response.status_code != 409
    assert response.json().get("code") != ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")
    assert response.json()["success"] is True


def test_repo_local_mutation_without_browser_origin_keeps_cli_parity(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(ACTION_PATH, json={})

    assert response.status_code != 409


def test_chat_workspace_mutation_requires_truth_binding_without_browser_origin(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        "/control-center/chat/threads/chat-thread:binding-test/draft-checkpoint",
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:chat-workspace:binding-test"
        },
        json={
            "expected_revision": 0,
            "draft_present": False,
            "draft_character_count": 0,
            "draft_fingerprint_ref": "draft-fingerprint-ref:chat:empty",
            "metadata_refs": [],
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")


@pytest.mark.parametrize(
    ("headers", "expected_status", "expected_code"),
    [
        ({}, 428, "API_IDEMPOTENCY_REQUIRED"),
        ({"X-UAA-Idempotency-Key": "short"}, 400, "API_IDEMPOTENCY_INVALID"),
    ],
)
def test_chat_workspace_binding_preserves_idempotency_gate_precedence(
    monkeypatch,
    headers: dict[str, str],
    expected_status: int,
    expected_code: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        "/control-center/chat/threads/chat-thread:binding-test/draft-checkpoint",
        headers=headers,
        json={},
    )

    assert response.status_code == expected_status
    assert response.json()["code"] == expected_code


def test_well_shaped_but_unissued_truth_ref_is_rejected(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    headers = _bound_headers(tmp_path)
    headers["X-UAA-Expected-Backend-Truth-Ref"] = (
        "proof-ref:backend-truth-envelope:sha256:" + "8" * 64
    )

    response = TestClient(app).post(ACTION_PATH, headers=headers, json={})

    assert response.status_code == 409
    assert response.json()["code"] == ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")


def test_browser_authority_preview_requires_exact_backend_truth(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))

    response = TestClient(app).post(
        "/api/runtime/authority-decisions/preview",
        headers={"Origin": ORIGIN},
        json=_authority_preview_payload(),
    )

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_PREVIEW_PROVENANCE_MISMATCH"
    )
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_browser_authority_preview_rejects_unissued_truth_token(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    headers = _bound_headers(tmp_path)
    headers.pop("X-UAA-Control-Center-Mutation-Binding")
    headers["X-UAA-Expected-Backend-Truth-Ref"] = (
        "proof-ref:backend-truth-envelope:sha256:" + "8" * 64
    )

    response = TestClient(app).post(
        "/api/runtime/authority-decisions/preview",
        headers=headers,
        json=_authority_preview_payload(),
    )

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_PREVIEW_PROVENANCE_MISMATCH"
    )


def test_browser_authority_preview_rejects_expired_truth_token(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    headers = _bound_headers(tmp_path, now=utc_now() - timedelta(minutes=2))
    headers.pop("X-UAA-Control-Center-Mutation-Binding")

    response = TestClient(app).post(
        "/api/runtime/authority-decisions/preview",
        headers=headers,
        json=_authority_preview_payload(),
    )

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_PREVIEW_PROVENANCE_MISMATCH"
    )


def test_browser_authority_preview_accepts_current_truth_without_mutation_header(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    headers = _bound_headers(tmp_path)
    headers.pop("X-UAA-Control-Center-Mutation-Binding")

    response = TestClient(app).post(
        "/api/runtime/authority-decisions/preview",
        headers=headers,
        json=_authority_preview_payload(),
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_concurrent_reader_truth_envelopes_remain_admitted_until_expiry(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    first_headers = _bound_headers(tmp_path, now=utc_now() - timedelta(seconds=2))
    second_headers = _bound_headers(tmp_path, now=utc_now() - timedelta(seconds=1))

    first_response = TestClient(app).post(
        ACTION_PATH,
        headers=first_headers,
        json={},
    )
    second_response = TestClient(app).post(
        ACTION_PATH,
        headers=second_headers,
        json={},
    )

    assert first_response.status_code != 409
    assert second_response.status_code != 409


def test_expired_truth_envelope_is_rejected(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    headers = _bound_headers(tmp_path, now=utc_now() - timedelta(minutes=2))

    response = TestClient(app).post(ACTION_PATH, headers=headers, json={})

    assert response.status_code == 409


@pytest.mark.parametrize(
    "path",
    [
        "/control-center/today/action-envelope",
        "/control-center/chat/turns",
        "/control-center/chat/turns/chat-turn-ref/handoff",
        "/control-center/web-evidence/attach",
        "/control-center/memory/feedback",
        "/control-center/memory/review/manual-candidate",
        "/control-center/memory/review/candidate-ref/accept",
        "/control-center/memory/review/candidate-ref/forget-request",
        "/control-center/memory/context-packs/context-pack-ref/action-proposal",
        "/api/runtime/goals",
        "/api/runtime/goals/approval-requests/create",
        "/api/runtime/goals/approval-requests/revoke",
        (
            "/api/runtime/goals/approval-requests/"
            "approval-request-ref:browser/decision"
        ),
        "/api/runtime/goals/goal-ref/approval-requests/edit",
        "/api/runtime/goals/goal-ref/approval-requests/transition",
        "/api/runtime/goals/goal-ref/edit",
        "/api/runtime/goals/goal-ref/transition",
    ],
)
def test_browser_product_and_runtime_mutations_require_truth_binding(
    monkeypatch,
    path: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        path,
        headers={"Origin": ORIGIN},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["code"] == ("BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH")


@pytest.mark.parametrize(
    "path",
    [
        "/control-center/crm/adoption/approval",
        "/control-center/crm/adoption/commit",
        "/control-center/crm/adoption/restore",
    ],
)
def test_browser_crm_adoption_mutations_require_truth_binding(
    monkeypatch,
    path: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        path,
        headers={"Origin": ORIGIN},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )


@pytest.mark.parametrize(
    "path",
    [
        "/control-center/news-signals/adoption/approval",
        "/control-center/news-signals/adoption/commit",
    ],
)
def test_browser_news_adoption_mutations_require_truth_binding(
    monkeypatch,
    path: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        path,
        headers={"Origin": ORIGIN},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )
