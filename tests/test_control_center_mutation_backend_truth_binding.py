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
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )
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
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )
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
    assert response.json().get("code") != (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )


def test_exact_browser_goal_binding_reaches_goal_route(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    monkeypatch.setenv("UAA_GOAL_RUNTIME_STATE_DIR", str(tmp_path / "goals"))

    response = TestClient(app).post(
        "/api/runtime/goals",
        headers={
            **_bound_headers(tmp_path),
            "X-UAA-Idempotency-Key": "idempotency-ref:browser-goal-binding",
        },
        json={
            "objective": "Verify exact browser provenance.",
            "desired_outcome": "One bounded local goal record.",
            "success_criteria": ["The exact provenance binding is current."],
            "constraints": ["No runtime execution."],
            "in_scope_resource_refs": ["resource-ref:browser-goal-binding"],
            "stop_condition": "Stop on provenance disagreement.",
        },
    )

    assert response.status_code != 409
    assert response.json().get("code") != (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )
    assert response.json()["success"] is True


def test_repo_local_mutation_without_browser_origin_keeps_cli_parity(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(ACTION_PATH, json={})

    assert response.status_code != 409


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
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )


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
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )
