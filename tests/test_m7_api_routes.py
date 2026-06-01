from fastapi.testclient import TestClient

from tests.m7_helpers import cloud_profile, local_profile, policy, route_request
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget


client = TestClient(app)


def test_model_profile_validate_endpoint_accepts_safe_metadata():
    response = client.post("/models/profiles/validate", json=local_profile().model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "validated"


def test_model_route_preview_endpoint_returns_decision_without_execution():
    request = route_request(profiles=[local_profile()], routing_policy=policy(prefer_local=True))

    response = client.post("/models/route/preview", json=request.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "selected"
    assert body["data"]["selected_profile_id"] == "local_coder"


def test_cost_budget_validate_and_estimate_endpoints():
    budget = CostBudget(budget_id="budget_api", scope=BudgetScope.run, max_cost_usd=1)

    validate_response = client.post("/costs/budgets/validate", json=budget.model_dump(mode="json"))
    assert validate_response.status_code == 200
    assert validate_response.json()["success"] is True

    estimate_response = client.post(
        "/costs/estimate/preview",
        json={"request": route_request(profiles=[cloud_profile()]).model_dump(mode="json"), "profile": cloud_profile().model_dump(mode="json")},
    )
    assert estimate_response.status_code == 200
    assert estimate_response.json()["success"] is True
    assert estimate_response.json()["data"]["estimated_cost_usd"] == 0.025


def test_cost_evaluate_endpoint_does_not_call_billing_provider():
    payload = {
        "estimate": {
            "estimate_id": "estimate_api",
            "input_tokens": 100,
            "output_tokens": 100,
            "total_tokens": 200,
            "estimated_cost_usd": 2,
        },
        "budgets": [CostBudget(budget_id="budget_api", scope=BudgetScope.run, max_cost_usd=1).model_dump(mode="json")],
    }

    response = client.post("/costs/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["allowed"] is False
