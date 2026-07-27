from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pytest

from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _readiness,
)
from tests.test_governed_browser_queue01_group03 import (
    _ExactEvidenceTransport,
    _exact_request as _observation_request,
    _observe,
    _recipe as _observation_recipe,
    _service as _observation_service,
)
from tests.test_governed_browser_queue01_group04 import (
    _ExactActionPlanTransport,
    _exact_request as _action_request,
    _plan as _action_plan,
    _recipe as _action_recipe,
    _service as _action_service,
)
from tests.test_governed_browser_queue01_group05 import (
    _ExactPostFormPlanTransport,
    _plan as _post_form_plan,
    _post_context,
    _service as _post_form_service,
)
from tests.test_governed_browser_queue01_group06 import (
    _FakeKeychain,
    _lifecycle_context,
)
from ultimate_ai_agent.core.governed_browser import (
    ExactGovernedBrowserOriginSessionRequest,
    ExactGovernedBrowserOriginSessionService,
    GovernedBrowserActionKind,
    GovernedBrowserOriginSessionOperation,
    GovernedBrowserOriginSessionStore,
)
from ultimate_ai_agent.core.governed_browser.operation_proofs import (
    GovernedBrowserOperationProofError,
    _operation_proof_store_for_kernel,
)


_SERVICE_BINDING_ERROR = (
    "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID"
)


class _RedirectDependency:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def invoke(self, *_args: object, **_kwargs: object) -> object:
        self.calls.append("redirected")
        raise AssertionError("substituted dependency or helper executed")

    def __call__(self, *_args: object, **_kwargs: object) -> object:
        return self.invoke(*_args, **_kwargs)

    resolve = invoke
    execute = invoke
    store = invoke
    probe = invoke
    delete = invoke
    prepare = invoke
    revalidate = invoke
    close = invoke
    mark_revoked = invoke
    save = invoke
    load = invoke


class _ExactClock:
    def __init__(self, value: datetime) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        return self.value


def _authorized_fixture_kernel(
    tmp_path: Path,
    request: Any,
) -> tuple[object, object]:
    readiness = _readiness(request)
    clock = _ExactClock(readiness.observed_at + timedelta(seconds=5))
    return _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=lambda _item: readiness,
        clock=clock,
    )


def _observation_case(
    tmp_path: Path,
) -> tuple[object, Callable[[], Any], _ExactEvidenceTransport, object]:
    request = _observation_request(suffix="service-binding-observation")
    recipe = _observation_recipe(request)
    kernel, _ = _authorized_fixture_kernel(
        tmp_path / "kernel",
        request,
    )
    transport = _ExactEvidenceTransport()
    service, _ = _observation_service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )
    return (
        service,
        lambda: _observe(service, request, recipe.recipe_ref),
        transport,
        kernel,
    )


def _action_case(
    tmp_path: Path,
) -> tuple[object, Callable[[], Any], _ExactActionPlanTransport, object]:
    operation = GovernedBrowserActionKind.visible_click
    request = _action_request(
        suffix="service-binding-action",
        operation=operation,
    )
    recipe = _action_recipe(request, operation)
    kernel, _ = _authorized_fixture_kernel(
        tmp_path / "kernel",
        request,
    )
    transport = _ExactActionPlanTransport()
    service, _ = _action_service(
        request=request,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )
    return (
        service,
        lambda: _action_plan(service, request, recipe.recipe_ref),
        transport,
        kernel,
    )


def _post_form_case(
    tmp_path: Path,
) -> tuple[object, Callable[[], Any], _ExactPostFormPlanTransport, object]:
    request, schema, recipe, _ = _post_context(
        suffix="service-binding-post-form"
    )
    kernel, _ = _authorized_fixture_kernel(
        tmp_path / "kernel",
        request,
    )
    transport = _ExactPostFormPlanTransport()
    service, _ = _post_form_service(
        request=request,
        schema=schema,
        recipe=recipe,
        kernel=kernel,
        transport=transport,
    )
    return (
        service,
        lambda: _post_form_plan(service, request, recipe.recipe_ref),
        transport,
        kernel,
    )


def _origin_session_case(
    tmp_path: Path,
) -> tuple[
    ExactGovernedBrowserOriginSessionService,
    Callable[[], Any],
    _FakeKeychain,
    GovernedBrowserOriginSessionStore,
    object,
    _ExactClock,
]:
    registration, contexts, registry = _lifecycle_context(
        suffix="service-binding-origin"
    )
    request, recipe = contexts[
        GovernedBrowserOriginSessionOperation.prepare_session
    ]
    keychain = _FakeKeychain()
    keychain.present.add(registration.registration_ref)
    sessions = GovernedBrowserOriginSessionStore(
        tmp_path / "sessions.sqlite3"
    )
    kernel, _ = _authorized_kernel(tmp_path / "kernel", request)
    clock = _ExactClock(recipe.created_at + timedelta(seconds=1))
    service = ExactGovernedBrowserOriginSessionService(
        registry=registry,
        kernel=kernel,
        keychain=keychain,
        sessions=sessions,
        clock=clock,
    )
    exact_request = ExactGovernedBrowserOriginSessionRequest(
        recipe_ref=recipe.recipe_ref,
        execution_request=request,
    )
    return (
        service,
        lambda: service.execute(exact_request),
        keychain,
        sessions,
        kernel,
        clock,
    )


@pytest.mark.parametrize("attribute", ["_registry", "_kernel", "_gateway"])
def test_observation_whole_dependency_substitution_cannot_redirect_replay(
    attribute: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, _ = _observation_case(tmp_path)
    assert invoke().receipt.status == "observation_ready"
    redirect = _RedirectDependency()

    monkeypatch.setattr(service, attribute, redirect)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match=_SERVICE_BINDING_ERROR,
    ):
        invoke()
    assert redirect.calls == []
    assert transport.calls == 1


@pytest.mark.parametrize("attribute", ["_registry", "_kernel", "_gateway"])
def test_action_whole_dependency_substitution_cannot_redirect_replay(
    attribute: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, _ = _action_case(tmp_path)
    assert invoke().receipt.status == "plan_ready"
    redirect = _RedirectDependency()

    monkeypatch.setattr(service, attribute, redirect)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match=_SERVICE_BINDING_ERROR,
    ):
        invoke()
    assert redirect.calls == []
    assert transport.calls == 1


@pytest.mark.parametrize("attribute", ["_registry", "_kernel", "_gateway"])
def test_post_form_whole_dependency_substitution_cannot_redirect_replay(
    attribute: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, _ = _post_form_case(tmp_path)
    assert invoke().receipt.status == "plan_ready"
    redirect = _RedirectDependency()

    monkeypatch.setattr(service, attribute, redirect)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match=_SERVICE_BINDING_ERROR,
    ):
        invoke()
    assert redirect.calls == []
    assert transport.calls == 1


@pytest.mark.parametrize(
    "attribute",
    ["_registry", "_kernel", "_keychain", "_sessions", "_clock"],
)
def test_origin_whole_dependency_substitution_cannot_redirect_replay(
    attribute: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, keychain, _, _, _ = _origin_session_case(tmp_path)
    assert invoke().receipt.status == "session_prepared"
    redirect = _RedirectDependency()

    monkeypatch.setattr(service, attribute, redirect)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match=_SERVICE_BINDING_ERROR,
    ):
        invoke()
    assert redirect.calls == []
    assert len(keychain.calls) == 1


def test_observation_instance_helper_shadows_cannot_redirect_execution_or_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, kernel = _observation_case(tmp_path)
    redirect = _RedirectDependency()
    proof_store = _operation_proof_store_for_kernel(kernel)

    monkeypatch.setattr(service, "_observe_via_gateway", redirect.invoke)
    monkeypatch.setattr(service._registry, "resolve", redirect.invoke)
    monkeypatch.setattr(service._kernel, "execute", redirect.invoke)
    monkeypatch.setattr(service._gateway, "execute", redirect.invoke)
    monkeypatch.setattr(proof_store, "save", redirect.invoke)
    monkeypatch.setattr(proof_store, "load", redirect.invoke)

    assert invoke().receipt.status == "observation_ready"
    assert invoke().receipt.status == "replayed_content_free"
    assert redirect.calls == []
    assert transport.calls == 1


def test_action_instance_helper_shadows_cannot_redirect_execution_or_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, kernel = _action_case(tmp_path)
    redirect = _RedirectDependency()
    proof_store = _operation_proof_store_for_kernel(kernel)

    monkeypatch.setattr(service, "_plan_via_gateway", redirect.invoke)
    monkeypatch.setattr(service._registry, "resolve", redirect.invoke)
    monkeypatch.setattr(service._kernel, "execute", redirect.invoke)
    monkeypatch.setattr(service._gateway, "execute", redirect.invoke)
    monkeypatch.setattr(proof_store, "save", redirect.invoke)
    monkeypatch.setattr(proof_store, "load", redirect.invoke)

    assert invoke().receipt.status == "plan_ready"
    assert invoke().receipt.status == "replayed_content_free"
    assert redirect.calls == []
    assert transport.calls == 1


def test_post_form_instance_helper_shadows_cannot_redirect_execution_or_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, transport, kernel = _post_form_case(tmp_path)
    redirect = _RedirectDependency()
    proof_store = _operation_proof_store_for_kernel(kernel)

    monkeypatch.setattr(service, "_plan_via_gateway", redirect.invoke)
    monkeypatch.setattr(service._registry, "resolve", redirect.invoke)
    monkeypatch.setattr(service._kernel, "execute", redirect.invoke)
    monkeypatch.setattr(service._gateway, "execute", redirect.invoke)
    monkeypatch.setattr(proof_store, "save", redirect.invoke)
    monkeypatch.setattr(proof_store, "load", redirect.invoke)

    assert invoke().receipt.status == "plan_ready"
    assert invoke().receipt.status == "replayed_content_free"
    assert redirect.calls == []
    assert transport.calls == 1


def test_origin_captured_helper_shadows_cannot_redirect_execution_or_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service, invoke, keychain, sessions, kernel, clock = _origin_session_case(
        tmp_path
    )
    redirect = _RedirectDependency()
    proof_store = _operation_proof_store_for_kernel(kernel)

    monkeypatch.setattr(service._registry, "resolve", redirect.invoke)
    monkeypatch.setattr(service._kernel, "execute", redirect.invoke)
    monkeypatch.setattr(keychain, "probe", redirect.invoke)
    monkeypatch.setattr(sessions, "prepare", redirect.invoke)
    monkeypatch.setattr(clock, "__call__", redirect.invoke)
    monkeypatch.setattr(proof_store, "save", redirect.invoke)
    monkeypatch.setattr(proof_store, "load", redirect.invoke)

    assert invoke().receipt.status == "session_prepared"
    assert invoke().receipt.status == "replayed"
    assert redirect.calls == []
    assert len(keychain.calls) == 1
    assert clock.calls >= 2
