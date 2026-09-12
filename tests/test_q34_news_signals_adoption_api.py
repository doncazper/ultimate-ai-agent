from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import (
    ApiRouteClassification,
    ApiRouteSideEffectClass,
    route_classification_for_path,
    route_side_effect_class,
)


def _headers(suffix: str, *, confirmed: bool = False) -> dict[str, str]:
    headers = {"X-UAA-Idempotency-Key": f"idempotency-ref:q34:api:{suffix}"}
    if confirmed:
        headers["X-UAA-Operator-Confirmed"] = "true"
    return headers


def _mutation(action: str, revision: int, **values: object) -> dict[str, object]:
    return {"action": action, "expected_revision": revision, **values}


def _commit(client: TestClient, mutation: dict[str, object], suffix: str) -> dict:
    preview_response = client.post(
        "/control-center/news-signals/adoption/preview",
        json=mutation,
        headers=_headers(suffix),
    )
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()["data"]
    request = {
        "mutation": mutation,
        "preview_ref": preview["preview_ref"],
        "approval_ref": preview["approval_ref"],
    }
    approval = client.post(
        "/control-center/news-signals/adoption/approval",
        json=request,
        headers=_headers(suffix, confirmed=True),
    )
    assert approval.status_code == 200, approval.text
    receipt = client.post(
        "/control-center/news-signals/adoption/commit",
        json=request,
        headers=_headers(suffix, confirmed=True),
    )
    assert receipt.status_code == 200, receipt.text
    return receipt.json()["data"]


def test_api_runs_normal_founder_private_news_loop(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app)

    empty = client.get("/control-center/news-signals/adoption")
    assert empty.status_code == 200
    assert empty.headers["cache-control"] == "no-store"
    assert empty.json()["data"]["revision"] == 0

    source = _commit(
        client,
        _mutation(
            "register_source",
            0,
            source_draft={
                "safe_label": "Official source",
                "source_kind": "official",
                "freshness_ttl_seconds": 86400,
            },
        ),
        "register",
    )
    source_ref = source["source_ref"]
    published_at = (
        datetime.now(timezone.utc) - timedelta(minutes=30)
    ).isoformat().replace("+00:00", "Z")
    signal = _commit(
        client,
        _mutation(
            "ingest_signal",
            1,
            signal_draft={
                "source_ref": source_ref,
                "title": "Governed systems milestone",
                "safe_summary": "A bounded redacted summary for local review.",
                "topic_label": "Agent governance",
                "cluster_label": "Governed systems milestone",
                "claim_label": "Governed systems milestone verified",
                "published_at": published_at,
                "confidence_percent": 91,
                "evidence_class": "primary",
                "claim_stance": "supports",
            },
        ),
        "ingest",
    )
    signal_ref = signal["signal_ref"]

    adoption = client.get("/control-center/news-signals/adoption").json()["data"]
    assert adoption["revision"] == 2
    assert adoption["summary"]["items"][0]["signal_ref"] == signal_ref
    assert adoption["live_fetch_enabled"] is False
    assert adoption["model_summarization_enabled"] is False

    today = client.get("/control-center/today/summary").json()["data"]
    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]
    assert today["news_signals_projection"]["item_refs"] == [signal_ref]
    assert briefing["news_signals_projection"]["candidate_refs"] == [signal_ref]


def test_api_mutations_require_idempotency_and_confirmation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app)
    mutation = _mutation(
        "register_source",
        0,
        source_draft={
            "safe_label": "Official source",
            "source_kind": "official",
            "freshness_ttl_seconds": 86400,
        },
    )

    assert client.post(
        "/control-center/news-signals/adoption/preview", json=mutation
    ).status_code == 428
    preview = client.post(
        "/control-center/news-signals/adoption/preview",
        json=mutation,
        headers=_headers("confirmation"),
    ).json()["data"]
    scoped = {
        "mutation": mutation,
        "preview_ref": preview["preview_ref"],
        "approval_ref": preview["approval_ref"],
    }
    approval = client.post(
        "/control-center/news-signals/adoption/approval",
        json=scoped,
        headers=_headers("confirmation"),
    )
    commit = client.post(
        "/control-center/news-signals/adoption/commit",
        json=scoped,
        headers=_headers("confirmation"),
    )

    assert approval.status_code == 403
    assert approval.json()["detail"]["code"].endswith("CONFIRMATION_REQUIRED")
    assert commit.status_code == 403


def test_api_conflicts_are_safe_and_structured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app)
    _commit(
        client,
        _mutation(
            "register_source",
            0,
            source_draft={
                "safe_label": "Official source",
                "source_kind": "official",
                "freshness_ttl_seconds": 86400,
            },
        ),
        "register-conflict",
    )
    stale = client.post(
        "/control-center/news-signals/adoption/preview",
        json=_mutation(
            "register_source",
            0,
            source_draft={
                "safe_label": "Second source",
                "source_kind": "local",
                "freshness_ttl_seconds": 86400,
            },
        ),
        headers=_headers("stale"),
    )

    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "NEWS_SIGNALS_ADOPTION_STALE_REVISION"
    assert "Official source" not in stale.text


def test_api_rejects_non_safe_idempotency_refs_without_500(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/control-center/news-signals/adoption/preview",
        json=_mutation(
            "register_source",
            0,
            source_draft={
                "safe_label": "Official source",
                "source_kind": "official",
                "freshness_ttl_seconds": 86400,
            },
        ),
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:q34:api:invalid_value"
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "IDEMPOTENCY_REF_SAFE_REF_REQUIRED"


def test_api_rejects_oversized_and_deep_json_with_cors(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app)
    headers = {
        **_headers("bounded"),
        "Origin": "http://127.0.0.1:5173",
    }
    oversized = client.post(
        "/control-center/news-signals/adoption/preview",
        content=b"{" + (b" " * (256 * 1024)),
        headers={**headers, "Content-Type": "application/json"},
    )
    deeply_nested = client.post(
        "/control-center/news-signals/adoption/preview",
        content=(b"[" * 33) + b"0" + (b"]" * 33),
        headers={**headers, "Content-Type": "application/json"},
    )

    for response in (oversized, deeply_nested):
        assert response.status_code == 413
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["access-control-allow-origin"] == headers["Origin"]
        assert response.json()["code"] == (
            "NEWS_SIGNALS_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"
        )


def test_api_corrupt_local_state_fails_closed_without_raw_details(
    tmp_path, monkeypatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    (state_dir / "news_signals.sqlite3").write_text(
        "private corrupt database body", encoding="utf-8"
    )
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    response = TestClient(app, raise_server_exceptions=False).get(
        "/control-center/news-signals/adoption"
    )

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"]["code"] == (
        "NEWS_SIGNALS_ADOPTION_DATABASE_STATE_INVALID"
    )
    assert "private corrupt database body" not in response.text


def test_api_manifest_publishes_news_contract_and_authority_classification() -> None:
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    limit_schema = schema["components"]["schemas"][
        "NewsSignalsAdoptionBodyLimitResponse"
    ]

    assert limit_schema["properties"]["maximum_body_bytes"]["const"] == 262144
    for suffix in ("adoption", "adoption/preview", "adoption/approval", "adoption/commit"):
        assert f"/control-center/news-signals/{suffix}" in schema["paths"]
    assert route_side_effect_class(
        "/control-center/news-signals/adoption/commit"
    ) == ApiRouteSideEffectClass.local_dev_workspace_only
    classification, description = route_classification_for_path(
        "POST",
        "/control-center/news-signals/adoption/commit",
        ApiRouteSideEffectClass.local_dev_workspace_only,
    )
    assert classification == ApiRouteClassification.mutating_requires_authority
    assert "operation-budget-one" in description
    assert "external authority stays blocked" in description
