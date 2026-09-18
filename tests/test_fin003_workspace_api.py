from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.finance_workspace import (
    FINANCE_WORKSPACE_MAX_BODY_BYTES,
    FINANCE_WORKSPACE_PATH,
    FinanceWorkspaceCommitRateLimitResponse,
    get_finance_workspace,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.api.idempotency import idempotency_value_valid
from ultimate_ai_agent.core.safe_contract_text import (
    IDEMPOTENCY_VALUE_PATTERN,
    MAX_IDEMPOTENCY_VALUE_LENGTH,
    MIN_IDEMPOTENCY_VALUE_LENGTH,
)
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.workspace import (
    FinanceWorkspace,
    FinanceWorkspaceConfiguration,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ORIGIN = "http://127.0.0.1:5173"
SHA = "8" * 40


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    reset_api_rate_limit_state()
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    workspace = FinanceWorkspace(
        FinanceWorkspaceConfiguration(tmp_path / "book", tmp_path / "helper", "a" * 64),
        crypto_backend=InMemoryFinanceCryptoBackend(),
    )
    app.dependency_overrides[get_finance_workspace] = lambda: workspace
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "truth"),
        identity=build_identity(env={"UAA_BUILD_COMMIT": SHA}),
    )
    headers = {
        "Origin": ORIGIN,
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{SHA}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }
    try:
        yield TestClient(app), workspace, headers
    finally:
        app.dependency_overrides.pop(get_finance_workspace, None)
        reset_api_rate_limit_state()


def _intent(operation="create", revision=0, suffix="create", **fields):
    return {
        "operation": operation,
        "expected_revision": revision,
        "request_ref": f"request-ref:finance:api:{suffix}",
        "idempotency_ref": f"idempotency-ref:finance:api:{suffix}",
        **fields,
    }


def _prepare(boundary, intent):
    client, _workspace, headers = boundary
    bound = {**headers, "X-UAA-Idempotency-Key": intent["idempotency_ref"]}
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview", json=intent, headers=bound
    )
    assert response.status_code == 200, response.text
    return response.json(), bound


def _commit(boundary, intent):
    prepared, headers = _prepare(boundary, intent)
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 200, response.text
    return prepared, response.json(), headers


def test_api_setup_import_review_reopen_replay_and_undo(boundary):
    client, workspace, _headers = boundary
    initial = client.get(FINANCE_WORKSPACE_PATH)
    assert initial.status_code == 200
    assert initial.json()["status"] == "book_setup_required"
    assert initial.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()
    _commit(boundary, _intent())
    _commit(boundary, _intent("import_commit", 1, "import"))
    read = client.get(FINANCE_WORKSPACE_PATH).json()
    assert read["item_count"] == 2
    prepared, result, headers = _commit(
        boundary,
        _intent(
            "review_decision",
            2,
            "review",
            review_item_ref=read["review_items"][0]["review_item_ref"],
            decision="confirm",
        ),
    )
    reopened = client.get(FINANCE_WORKSPACE_PATH).json()
    assert reopened["review_items"][0]["state"] == "confirmed"
    replay = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert replay.status_code == 200
    assert replay.json()["receipt"]["replayed"] is True
    assert replay.json()["receipt"]["receipt_ref"] == result["receipt"]["receipt_ref"]
    _commit(
        boundary,
        _intent(
            "review_undo",
            3,
            "undo",
            review_item_ref=reopened["review_items"][0]["review_item_ref"],
            compensates_event_ref=reopened["review_items"][0]["effective_decision_ref"],
        ),
    )
    final = client.get(FINANCE_WORKSPACE_PATH).json()
    assert final["review_items"][0]["state"] == "needs_review"
    assert final["history_count"] == 2


def test_api_authentication_is_required_even_for_setup_status(boundary, monkeypatch):
    client, workspace, _headers = boundary
    monkeypatch.delenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", raising=False)
    bearer = uuid4().hex
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", bearer)
    response = client.get(FINANCE_WORKSPACE_PATH)
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert (
        client.get(
            FINANCE_WORKSPACE_PATH, headers={"Authorization": f"Bearer {bearer}"}
        ).status_code
        == 200
    )
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("value", ["id:abcde", "id:a_B-9.c:D", "id:" + "a" * 197])
def test_published_idempotency_bounds_are_callable_through_the_header_gate(
    boundary, value
):
    assert idempotency_value_valid(value)
    request = _intent(idempotency_ref=value)
    prepared, _headers = _prepare(boundary, request)
    assert prepared["bundle"]["request"]["idempotency_ref"] == value
    schema = boundary[0].get("/openapi.json").json()["components"]["schemas"]
    constraints = schema["FinanceWorkspaceIntent"]["properties"]["idempotency_ref"]
    assert constraints["minLength"] == MIN_IDEMPOTENCY_VALUE_LENGTH
    assert constraints["maxLength"] == MAX_IDEMPOTENCY_VALUE_LENGTH
    assert constraints["pattern"] == IDEMPOTENCY_VALUE_PATTERN
    nested = schema["FinanceWorkspacePreparation"]["properties"]["bundle"][
        "properties"
    ]["request"]["properties"]["idempotency_ref"]
    assert nested["minLength"] == constraints["minLength"]
    assert nested["maxLength"] == constraints["maxLength"]
    assert nested["pattern"] == constraints["pattern"]
    assert not boundary[1].configuration.repository_dir.exists()


@pytest.mark.parametrize(
    "value", ["id:a", "idempotency-ref:finance/action", "id:review@account"]
)
def test_api_rejects_noncallable_body_idempotency_before_preparing(boundary, value):
    client, workspace, headers = boundary
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview",
        json=_intent(idempotency_ref=value),
        headers={
            **headers,
            "X-UAA-Idempotency-Key": "idempotency-ref:finance:valid-header",
        },
    )
    assert response.status_code == 422
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("route", ["preview", "refresh", "commit"])
def test_api_always_requires_current_backend_identity(boundary, route):
    client, workspace, headers = boundary
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/{route}",
        json={},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:finance:missing-binding"},
    )
    assert response.status_code == 409
    changed = {
        **headers,
        "X-UAA-Expected-Backend-Instance-Ref": "backend-instance-ref:stale",
    }
    stale = client.post(f"{FINANCE_WORKSPACE_PATH}/{route}", json={}, headers=changed)
    assert stale.status_code == 409
    assert stale.headers["access-control-allow-origin"] == ORIGIN
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("confirmation", [None, "false", "1", "TRUE"])
def test_api_requires_literal_confirmation_of_exact_preparation(boundary, confirmation):
    prepared, headers = _prepare(boundary, _intent())
    if confirmation is not None:
        headers["X-UAA-Operator-Confirmed"] = confirmation
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit", json=prepared, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"]["commit_outcome"] == "not_attempted"
    assert not boundary[1].configuration.repository_dir.exists()


@pytest.mark.parametrize("action", ["preview", "refresh", "commit"])
def test_idempotency_aliases_and_body_are_exactly_bound(boundary, action):
    client, workspace, headers = boundary
    request = _intent()
    prepared, _bound = _prepare(boundary, request)
    for extra, expected_status in (
        ({}, 428),
        ({"X-UAA-Idempotency-Key": "idempotency-ref:finance:other"}, 409),
        (
            {
                "X-UAA-Idempotency-Key": request["idempotency_ref"],
                "X-UAA-Idempotency-Ref": "idempotency-ref:finance:conflict",
            },
            400,
        ),
    ):
        response = client.post(
            f"{FINANCE_WORKSPACE_PATH}/{action}",
            json=request if action == "preview" else prepared,
            headers={**headers, **extra, "X-UAA-Operator-Confirmed": "true"},
        )
        assert response.status_code == expected_status
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("action", ["preview", "refresh", "commit"])
@pytest.mark.parametrize("aliases", [("key",), ("ref",), ("key", "ref")])
def test_either_or_both_equal_idempotency_aliases_remain_callable(
    boundary, monkeypatch, action, aliases
):
    client, workspace, headers = boundary
    request = _intent()
    prepared, _bound = _prepare(boundary, request)
    # Refresh eligibility is a Core concern; this test isolates its alias gate.
    monkeypatch.setattr(workspace, "refresh_preparation", lambda value: value)
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/{action}",
        json=request if action == "preview" else prepared,
        headers={
            **headers,
            **{
                f"X-UAA-Idempotency-{alias.title()}": request["idempotency_ref"]
                for alias in aliases
            },
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        b" " * (FINANCE_WORKSPACE_MAX_BODY_BYTES + 1),
        b"[" * 10_000 + b"0" + b"]" * 10_000,
        ("[" * 100 + "0" + "]" * 100).encode("utf-16"),
    ],
    ids=["oversized-body", "excessive-depth", "unsupported-utf16"],
)
def test_body_guard_rejects_before_decode_with_cors_and_no_store(boundary, payload):
    client, workspace, headers = boundary
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview",
        content=payload,
        headers={
            **headers,
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": "idempotency-ref:finance:body-bound",
        },
    )
    assert response.status_code == 413
    assert response.json()["code"] == "FINANCE_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()


def test_body_guard_ignores_structural_characters_inside_json_strings(boundary):
    client, _workspace, headers = boundary
    payload = _intent()
    payload["request_ref"] = "request-ref:" + "[" * 100
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview",
        json=payload,
        headers={**headers, "X-UAA-Idempotency-Key": payload["idempotency_ref"]},
    )
    assert response.status_code == 422


def test_unexpected_commit_failure_does_not_claim_no_change_or_leak_details(
    boundary, monkeypatch
):
    prepared, headers = _prepare(boundary, _intent())

    def fail(*args, **kwargs):
        raise RuntimeError("sensitive implementation diagnostic must not leave Core")

    monkeypatch.setattr(boundary[1], "commit", fail)
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["commit_outcome"] == "unconfirmed"
    assert "sensitive implementation" not in response.text


def test_recovery_lock_busy_is_not_attempted_before_confirmation(boundary, monkeypatch):
    from ultimate_ai_agent.core.finance import workspace as workspace_module
    from ultimate_ai_agent.core.finance.workspace_recovery import (
        FinanceWorkspaceRecoveryStore,
    )

    client, workspace, _headers = boundary
    prepared, headers = _prepare(boundary, _intent())
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)

    def must_not_confirm(*args, **kwargs):
        pytest.fail("Recovery lock contention entered the confirming mutation path")

    monkeypatch.setattr(workspace_module, "confirm_finance_mutation", must_not_confirm)
    with store.confirmed_attempt():
        response = client.post(
            f"{FINANCE_WORKSPACE_PATH}/commit",
            json=prepared,
            headers={**headers, "X-UAA-Operator-Confirmed": "true"},
        )
    assert response.status_code == 409
    assert (
        response.json()["detail"]["code"] == "FINANCE_WORKSPACE_RECOVERY_ATTEMPT_BUSY"
    )
    assert response.json()["detail"]["commit_outcome"] == "not_attempted"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert store.read() is None
    assert not workspace.configuration.repository_dir.exists()
    assert {path.name for path in store.directory.iterdir()} == {store.lock_path.name}


def test_initial_recovery_write_failure_is_not_attempted_before_confirmation(
    boundary, monkeypatch
):
    from ultimate_ai_agent.core.finance import workspace as workspace_module
    from ultimate_ai_agent.core.finance.workspace_recovery import (
        FinanceWorkspaceRecoveryStore,
    )

    client, workspace, _headers = boundary
    prepared, headers = _prepare(boundary, _intent())
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    attempted_writes = 0

    def failed_write(self, payload):
        nonlocal attempted_writes
        attempted_writes += 1
        raise OSError("synthetic storage diagnostic must stay private")

    def must_not_confirm(*args, **kwargs):
        pytest.fail(
            "Initial recovery write failure entered the confirming mutation path"
        )

    monkeypatch.setattr(FinanceWorkspaceRecoveryStore, "write", failed_write)
    monkeypatch.setattr(workspace_module, "confirm_finance_mutation", must_not_confirm)
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "FINANCE_WORKSPACE_REQUEST_FAILED"
    assert response.json()["detail"]["commit_outcome"] == "not_attempted"
    assert "synthetic storage diagnostic" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert attempted_writes == 1
    assert store.read() is None
    assert not workspace.configuration.repository_dir.exists()
    assert {path.name for path in store.directory.iterdir()} == {store.lock_path.name}


@pytest.mark.parametrize(
    "operation", ["create", "import_commit", "review_decision", "review_undo"]
)
def test_server_expiry_race_is_not_attempted_before_confirmation(
    boundary, monkeypatch, operation
):
    from ultimate_ai_agent.core.finance import workspace as workspace_module

    client, workspace, _headers = boundary
    request = _intent()
    if operation != "create":
        _commit(boundary, request)
        request = _intent("import_commit", 1, "import")
    if operation in {"review_decision", "review_undo"}:
        _commit(boundary, request)
        view = workspace.read_view()
        request = _intent(
            "review_decision",
            2,
            "review",
            review_item_ref=view.review_items[0].review_item_ref,
            decision="confirm",
        )
    if operation == "review_undo":
        _commit(boundary, request)
        view = workspace.read_view()
        request = _intent(
            "review_undo",
            3,
            "undo",
            review_item_ref=view.review_items[0].review_item_ref,
            compensates_event_ref=view.review_items[0].effective_decision_ref,
        )
    prepared, headers = _prepare(boundary, request)
    before = workspace.read_view()
    from ultimate_ai_agent.core.finance.workspace_recovery import (
        FinanceWorkspaceRecoveryStore,
    )

    recovery_store = FinanceWorkspaceRecoveryStore(
        workspace.configuration.repository_dir
    )
    retained_before = recovery_store.read()
    expired = datetime.fromisoformat(
        prepared["bundle"]["preview"]["expires_at"]
    ) + timedelta(microseconds=1)

    class ServerClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return expired

    def must_not_confirm(*args, **kwargs):
        pytest.fail("Expired preflight entered the confirming mutation path")

    monkeypatch.setattr(workspace_module, "datetime", ServerClock)
    monkeypatch.setattr(workspace_module, "confirm_finance_mutation", must_not_confirm)
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"]["code"] == "FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT"
    )
    assert response.json()["detail"]["commit_outcome"] == "not_attempted"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    # GET freshly re-presents the same retained payload; only presentation time
    # changes. The exact stored attempt, historical result and book stay intact.
    assert workspace.read_view().model_dump(
        exclude={"recovery": {"preparation"}}
    ) == before.model_dump(exclude={"recovery": {"preparation"}})
    assert recovery_store.read() == retained_before
    if operation == "create":
        assert not workspace.configuration.repository_dir.exists()
        assert not (
            workspace.configuration.repository_dir.parent / ".uaa-finance-authority"
        ).exists()


@pytest.mark.parametrize("write_first", [False, True])
def test_preflight_shaped_error_after_confirmation_stays_unconfirmed(
    boundary, monkeypatch, write_first
):
    from ultimate_ai_agent.core.finance import workspace as workspace_module

    client, workspace, _headers = boundary
    prepared, headers = _prepare(boundary, _intent())
    confirm = workspace_module.confirm_finance_mutation

    def fail_after_boundary(*args, **kwargs):
        if write_first:
            confirm(*args, **kwargs)
        raise ValueError("FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT")

    monkeypatch.setattr(
        workspace_module, "confirm_finance_mutation", fail_after_boundary
    )
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["commit_outcome"] == "unconfirmed"
    assert workspace.read_view().revision == (1 if write_first else 0)


def test_finance_openapi_and_manifest_publish_exact_contracts(boundary):
    client, _workspace, _headers = boundary
    schema = client.get("/openapi.json").json()
    for action in ("preview", "refresh", "commit"):
        route = schema["paths"][f"{FINANCE_WORKSPACE_PATH}/{action}"]["post"]
        body_limit = route["responses"]["413"]["content"]["application/json"]["schema"]
        assert body_limit["$ref"].endswith("FinanceWorkspaceBodyLimitResponse")
        parameters = {item["name"]: item for item in route["parameters"]}
        for header in (
            "X-UAA-Expected-Backend-Revision-Ref",
            "X-UAA-Expected-Backend-Instance-Ref",
            "X-UAA-Expected-Backend-Truth-Ref",
            "X-UAA-Control-Center-Mutation-Binding",
        ):
            assert parameters[header]["in"] == "header"
            assert parameters[header]["required"] is True
        assert "x-uaa-idempotency-key" in parameters
        assert "x-uaa-idempotency-ref" in parameters
        idempotency = route["x-uaa-idempotency"]
        assert idempotency["required"] is True
        assert idempotency["header_names_case_insensitive"] is True
        assert idempotency["supplied_aliases_must_agree"] is True
        assert idempotency["must_equal_body_idempotency_ref"] is True
        header_validator = Draft202012Validator(idempotency["headers_schema"])
        assert not header_validator.is_valid({})
        for aliases in (("key",), ("ref",), ("key", "ref")):
            valid_headers = {
                f"x-uaa-idempotency-{alias}": "idempotency-ref:finance:schema"
                for alias in aliases
            }
            header_validator.validate(valid_headers)
        for bad_value in (None, "", "short", "id:bad/path", "x" * 201):
            for alias in ("key", "ref"):
                assert not header_validator.is_valid(
                    {f"x-uaa-idempotency-{alias}": bad_value}
                )
        if action == "commit":
            rate_limit = route["responses"]["429"]["content"]["application/json"][
                "schema"
            ]
            assert rate_limit["$ref"].endswith(
                "FinanceWorkspaceCommitRateLimitResponse"
            )
    manifest = build_api_manifest(app)
    routes = [
        route
        for route in manifest.routes
        if route.path.startswith(FINANCE_WORKSPACE_PATH)
    ]
    assert len(routes) == 4
    for route in routes:
        assert route.auth_posture == "protected_local_bearer_required"
        assert route.blocked_from_production is True
        assert route.side_effect_class == "local_dev_workspace_only"
        if route.method == "POST":
            assert route.rate_limit_targeted is True
            assert route.rate_limit_group == "finance_workspace"
            assert route.idempotency_required is True
        else:
            assert route.rate_limit_targeted is False
            assert route.idempotency_required is False
        if route.path.endswith("/commit"):
            assert route.route_classification == "mutating_requires_authority"
            assert route.idempotency_enforcement == "route_owned_durable_replay"
            assert (
                route.durable_idempotency_owner_ref
                == "idempotency-owner:finance-protected-repository-receipts:v1"
            )
        else:
            assert route.route_classification == "local_sensitive"
            if route.method == "POST":
                assert route.idempotency_posture == "required_for_exact_request_binding"
                assert route.idempotency_enforcement == "route_owned_exact_binding"
                assert route.durable_idempotency_owner_ref is None
                assert route.approval_posture == "not_required_for_route_classification"
    assert len({route.operation_id for route in routes}) == 4


def test_finance_originless_commit_cannot_bypass_idempotency_or_backend_binding(
    boundary,
):
    client, workspace, _headers = boundary
    assert client.post(f"{FINANCE_WORKSPACE_PATH}/commit", json={}).status_code == 428
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json={},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:finance:originless"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    assert not workspace.configuration.repository_dir.exists()


def test_finance_exact_post_routes_share_a_bounded_request_budget(
    boundary, monkeypatch
):
    from ultimate_ai_agent.api.rate_limits import (
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
        reset_api_rate_limit_state,
    )

    reset_api_rate_limit_state()
    monkeypatch.setenv(API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV, "2")
    client, workspace, headers = boundary
    prepared, bound = _prepare(boundary, _intent())

    def must_not_commit(*args, **kwargs):
        pytest.fail("Rate-limited request entered the Finance commit handler")

    monkeypatch.setattr(workspace, "commit", must_not_commit)
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/refresh", json=prepared, headers=bound
    )
    # Create is not an eligible review refresh; the rejected request still counts.
    assert response.status_code == 409
    denied = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**bound, "X-UAA-Operator-Confirmed": "true"},
    )
    assert denied.status_code == 429
    assert denied.json()["rate_limit_group"] == "finance_workspace"
    proof = FinanceWorkspaceCommitRateLimitResponse.model_validate(denied.json())
    assert proof.commit_outcome == "not_attempted"
    assert proof.rejection_phase == "before_commit_handler"
    assert proof.request_path == f"{FINANCE_WORKSPACE_PATH}/commit"
    assert (
        denied.headers["X-UAA-Backend-Revision-Ref"]
        == bound["X-UAA-Expected-Backend-Revision-Ref"]
    )
    assert (
        denied.headers["X-UAA-Backend-Instance-Ref"]
        == bound["X-UAA-Expected-Backend-Instance-Ref"]
    )
    assert denied.headers["access-control-allow-origin"] == ORIGIN
    assert denied.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()
    assert client.get(FINANCE_WORKSPACE_PATH, headers=headers).status_code == 200


@pytest.mark.parametrize("action", ["preview", "refresh"])
def test_other_finance_rate_limits_never_claim_commit_phase(
    boundary, monkeypatch, action
):
    from ultimate_ai_agent.api.rate_limits import (
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
    )

    monkeypatch.setenv(API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV, "1")
    client, _workspace, _headers = boundary
    prepared, bound = _prepare(boundary, _intent())
    denied = client.post(
        f"{FINANCE_WORKSPACE_PATH}/{action}", json=prepared, headers=bound
    )
    assert denied.status_code == 429
    assert denied.json()["code"] == "API_TARGETED_RATE_LIMITED"
    assert "commit_outcome" not in denied.json()
    assert "rejection_phase" not in denied.json()
