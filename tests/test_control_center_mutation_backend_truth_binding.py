from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref,
)


SHA = "7" * 40
ACTION_PATH = "/control-center/actions/local-task-create-scorecard/approve"
ORIGIN = "http://127.0.0.1:5173"
TRUTH_REF = "proof-ref:backend-truth-envelope:sha256:" + "8" * 64


def _bound_headers() -> dict[str, str]:
    return {
        "Origin": ORIGIN,
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{SHA}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": TRUTH_REF,
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
    header_name: str,
    replacement: str,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    headers = _bound_headers()
    headers[header_name] = replacement

    response = TestClient(app).post(ACTION_PATH, headers=headers, json={})

    assert response.status_code == 409
    assert response.json()["code"] == (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )


def test_exact_browser_mutation_binding_reaches_existing_route_checks(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(
        ACTION_PATH,
        headers=_bound_headers(),
        json={},
    )

    assert response.status_code != 409
    assert response.json().get("code") != (
        "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    )


def test_repo_local_mutation_without_browser_origin_keeps_cli_parity(
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)

    response = TestClient(app).post(ACTION_PATH, json={})

    assert response.status_code != 409
