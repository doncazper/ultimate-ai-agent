from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.api.manifest import (
    ApiRouteClassification,
    ApiRouteSideEffectClass,
    route_classification_for_path,
    route_side_effect_class,
)
from ultimate_ai_agent.core.news_signals.adoption import (
    NewsSignalsAdoptionMutationPreview,
    NewsSignalsAdoptionStore,
)


@pytest.fixture(autouse=True)
def _isolated_rate_limit_state():
    reset_api_rate_limit_state()
    yield
    reset_api_rate_limit_state()


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
        (datetime.now(timezone.utc) - timedelta(minutes=30))
        .isoformat()
        .replace("+00:00", "Z")
    )
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
    assert adoption["active_items_page"]["items"][0]["signal_ref"] == signal_ref
    assert adoption["live_fetch_enabled"] is False
    assert adoption["model_summarization_enabled"] is False

    searched = client.get(
        "/control-center/news-signals/adoption",
        params={"offset": 0, "limit": 1, "search_query": "governed systems"},
    )
    assert searched.status_code == 200
    searched_page = searched.json()["data"]["active_items_page"]
    assert searched_page["search_applied"] is True
    assert searched_page["returned_items"] == 1
    assert searched_page["items"][0]["signal_ref"] == signal_ref

    unsafe_search = client.get(
        "/control-center/news-signals/adoption",
        params={"search_query": "unsafe/path"},
    )
    assert unsafe_search.status_code == 400
    assert unsafe_search.json()["detail"]["code"] == ("SEARCH_QUERY_REDACTION_REQUIRED")

    today = client.get("/control-center/today/summary").json()["data"]
    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]
    assert today["news_signals_projection"]["item_refs"] == [signal_ref]
    assert briefing["news_signals_projection"]["candidate_refs"] == [signal_ref]


def test_api_mutations_require_idempotency_and_confirmation(
    tmp_path, monkeypatch
) -> None:
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

    assert (
        client.post(
            "/control-center/news-signals/adoption/preview", json=mutation
        ).status_code
        == 428
    )
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


@pytest.mark.parametrize(
    "damaged_state",
    (
        "lease-json",
        "lease-root",
        "lease-entry",
        "lease-entry-shape",
        "lease-depth",
        "receipt-json",
        "receipt-entry",
        "receipt-shape",
        "receipt-conflict",
        "receipt-filesystem",
    ),
)
def test_api_authority_state_failures_are_safe_and_do_not_mutate(
    tmp_path, monkeypatch, damaged_state
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app, raise_server_exceptions=False)
    source = {
        "safe_label": "Official source",
        "source_kind": "official",
        "freshness_ttl_seconds": 86400,
    }
    _commit(client, _mutation("register_source", 0, source_draft=source), "seed")
    mutation = _mutation("register_source", 1, source_draft=source)
    suffix = "damaged-authority"
    preview = client.post(
        "/control-center/news-signals/adoption/preview",
        json=mutation,
        headers=_headers(suffix),
    ).json()["data"]
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
    assert approval.status_code == 200
    store = NewsSignalsAdoptionStore(tmp_path)
    before = store.read_view()
    lease_store, _, lease_key, _, _, _ = store._lease_context(
        NewsSignalsAdoptionMutationPreview.model_validate(preview),
        idempotency_ref=_headers(suffix)["X-UAA-Idempotency-Key"],
    )
    if damaged_state.startswith("lease-"):
        payload = {
            "lease-json": "{",
            "lease-root": "[]",
            "lease-entry": '{"leases": [{}]}',
            "lease-entry-shape": '{"leases": [0]}',
            "lease-depth": "[" * 2000 + "0" + "]" * 2000,
        }[damaged_state]
        lease_store.leases_path.write_text(payload, encoding="utf-8")
    elif damaged_state == "receipt-conflict":
        recorded = json.loads(lease_store.receipts_path.read_text().splitlines()[0])
        recorded["idempotency_ref"] = lease_key
        rebound = {**recorded, "lease_ref": "authority-lease-ref:q34:substituted"}
        lease_store.receipts_path.write_text(
            json.dumps(recorded) + "\n" + json.dumps(rebound) + "\n",
            encoding="utf-8",
        )
    elif damaged_state == "receipt-filesystem":
        lease_store.receipts_path.unlink()
        lease_store.receipts_path.mkdir()
    else:
        lease_store.receipts_path.write_text(
            {"receipt-json": "{", "receipt-entry": "{}", "receipt-shape": "[]"}[
                damaged_state
            ],
            encoding="utf-8",
        )

    response = client.post(
        "/control-center/news-signals/adoption/commit",
        json=request,
        headers=_headers(suffix, confirmed=True),
    )

    conflict = damaged_state == "receipt-conflict"
    assert response.status_code == (409 if conflict else 403)
    assert response.json()["detail"]["code"] == (
        "NEWS_SIGNALS_ADOPTION_AUTHORITY_IDEMPOTENCY_CONFLICT"
        if conflict
        else "NEWS_SIGNALS_ADOPTION_AUTHORITY_STATE_INVALID"
    )
    assert str(tmp_path) not in response.text
    assert "Traceback" not in response.text
    assert "Official source" not in response.text
    assert store.read_view()["current_state_ref"] == before["current_state_ref"]


@pytest.mark.parametrize("failure", ("regular-file", "symlink-loop"))
def test_api_approval_directory_failure_is_safe_and_does_not_mutate(
    tmp_path, monkeypatch, failure
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path))
    client = TestClient(app, raise_server_exceptions=False)
    mutation = _mutation(
        "register_source",
        0,
        source_draft={
            "safe_label": "Official source",
            "source_kind": "official",
            "freshness_ttl_seconds": 86400,
        },
    )
    preview = client.post(
        "/control-center/news-signals/adoption/preview",
        json=mutation,
        headers=_headers("unsafe-authority-dir"),
    ).json()["data"]
    authority_path = tmp_path / "news_signals_authority"
    if failure == "regular-file":
        authority_path.write_text(
            "private invalid authority directory", encoding="utf-8",
        )
    else:
        authority_path.symlink_to(authority_path.name)
    response = client.post(
        "/control-center/news-signals/adoption/approval",
        json={
            "mutation": mutation,
            "preview_ref": preview["preview_ref"],
            "approval_ref": preview["approval_ref"],
        },
        headers=_headers("unsafe-authority-dir", confirmed=True),
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "NEWS_SIGNALS_ADOPTION_AUTHORITY_STATE_INVALID"
    )
    assert str(tmp_path) not in response.text
    assert "private invalid" not in response.text
    assert NewsSignalsAdoptionStore(tmp_path).read_view()["revision"] == 0


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
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:q34:api:invalid_value"},
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


@pytest.mark.parametrize(
    "path",
    [
        "/control-center/news-signals/adoption",
        "/control-center/news-signals/summary",
        "/control-center/today/summary",
        "/control-center/morning-briefing/summary",
    ],
)
def test_api_corrupt_local_state_fails_closed_without_raw_details(
    tmp_path, monkeypatch, path
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    (state_dir / "news_signals.sqlite3").write_text(
        "private corrupt database body", encoding="utf-8"
    )
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    response = TestClient(app, raise_server_exceptions=False).get(path)

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
    for suffix in (
        "adoption",
        "adoption/preview",
        "adoption/approval",
        "adoption/commit",
    ):
        assert f"/control-center/news-signals/{suffix}" in schema["paths"]
    assert (
        route_side_effect_class("/control-center/news-signals/adoption/commit")
        == ApiRouteSideEffectClass.local_dev_workspace_only
    )
    classification, description = route_classification_for_path(
        "POST",
        "/control-center/news-signals/adoption/commit",
        ApiRouteSideEffectClass.local_dev_workspace_only,
    )
    assert classification == ApiRouteClassification.mutating_requires_authority
    assert "operation-budget-one" in description
    assert "external authority stays blocked" in description
