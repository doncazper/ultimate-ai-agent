from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def actor_payload():
    return {
        "actor_type": "human_user",
        "actor_id": "user_123",
        "authority_source": "explicit_user_request",
    }


def canonical_source():
    return {
        "source_id": "src_canonical",
        "source_type": "canonical_file",
        "authority_level": "authoritative",
        "display_name": "Roadmap",
        "owner": "tests",
        "allowed_scopes": ["project"],
        "allowed_purposes": ["project_truth"],
        "data_classification": "project_private",
        "file_ref": "docs/canonical/09_roadmap.md",
    }


def test_truth_source_validate_endpoint_blocks_secret_metadata():
    payload = canonical_source()
    payload["metadata"] = {"note": "api_key='abcdefghijklmnop'"}

    response = client.post("/truth/sources/validate", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "TRUTH_SOURCE_INVALID"
    assert "abcdefghijklmnop" not in response.text


def test_grounding_policy_validate_endpoint():
    response = client.post(
        "/truth/grounding-policy/validate",
        json={
            "policy_id": "gp_project",
            "task_class": "project_truth",
            "grounding_mode": "canonical_required",
            "required_source_types": ["canonical_file"],
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_evidence_validate_endpoint():
    response = client.post(
        "/truth/evidence/validate",
        json={
            "manifest_id": "em_api",
            "run_id": "run_123",
            "claims": [
                {
                    "claim_id": "claim_1",
                    "claim_text": "Project truth uses canonical files.",
                    "verification_status": "supported",
                    "evidence_refs": ["ev_1"],
                    "source_ids": ["src_canonical"],
                }
            ],
            "evidence_items": [
                {
                    "evidence_id": "ev_1",
                    "source_id": "src_canonical",
                    "source_type": "canonical_file",
                    "locator": "docs/canonical/09_roadmap.md",
                    "summary": "Roadmap names M4.5.",
                    "freshness_status": "current",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_truth_route_endpoint_is_non_executing():
    response = client.post(
        "/truth/route",
        json={
            "request_id": "trr_api",
            "run_id": "run_123",
            "actor_context": actor_payload(),
            "task_class": "project_truth",
            "question_or_claim": "What governs project truth?",
            "grounding_policy": {
                "policy_id": "gp_project",
                "task_class": "project_truth",
                "grounding_mode": "canonical_required",
                "required_source_types": ["canonical_file"],
            },
            "available_sources": [canonical_source()],
            "data_classification": "project_private",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["selected_source_ids"] == ["src_canonical"]


def test_truth_freshness_check_endpoint():
    response = client.post(
        "/truth/freshness/check",
        json={
            "evidence_item": {
                "evidence_id": "ev_api",
                "source_id": "src_provider",
                "source_type": "provider_result",
                "summary": "Weather",
                "observed_at": "2026-06-01T11:45:00",
                "freshness_status": "unknown",
            },
            "policy": {
                "policy_id": "fresh_weather",
                "freshness_window_seconds": 3600,
                "fetched_at_required": True,
                "stale_behavior": "reject",
                "applies_to_source_types": ["provider_result"],
                "applies_to_task_classes": ["weather"],
            },
            "current_time": "2026-06-01T12:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["freshness_status"] == "current"


def test_truth_conflicts_validate_endpoint():
    response = client.post(
        "/truth/conflicts/validate",
        json={
            "conflict_id": "conflict_api",
            "source_ids": ["src_canonical", "src_memory"],
            "severity": "medium",
            "description": "Canonical conflicts with memory.",
            "resolution_policy": "canonical_wins",
            "preferred_source_id": "src_canonical",
            "reason_codes": ["CANONICAL_OVERRIDES_MEMORY"],
            "requires_human_review": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
