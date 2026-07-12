from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app


client = TestClient(app)


def _lease_request() -> dict[str, object]:
    return {
        "mode": "approved_safe_local_work_session",
        "requested_domains": {"workspace": ["read"]},
        "decision_reason_ref": "reason-ref:authority-local-operator-hardening",
        "safe_summary": "Request one exact local workspace read lease.",
    }


@pytest.mark.parametrize(
    ("payload", "idempotency_ref"),
    [
        (
            {
                "lease_issue_request": _lease_request(),
                "approved_by_actor_ref": "operator-ref:caller-controlled",
            },
            "idempotency-ref:authority-spoofed-approver",
        ),
        (
            {
                "lease_issue_request": {
                    **_lease_request(),
                    "operator_ref": "operator-ref:caller-controlled",
                }
            },
            "idempotency-ref:authority-spoofed-operator",
        ),
    ],
)
def test_approve_and_issue_rejects_caller_controlled_operator_identity(
    payload: dict[str, object],
    idempotency_ref: str,
) -> None:
    response = client.post(
        "/api/runtime/authority-leases/approve-and-issue",
        headers={"x-uaa-idempotency-key": idempotency_ref},
        json=payload,
    )

    assert response.status_code == 422
