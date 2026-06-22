from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from scripts.verification import api_lane
from scripts.verification import run_all_legacy


@pytest.fixture(scope="module")
def shared_context():
    return api_lane.default_api_verifier_context()


def test_default_api_verifier_context_is_cached() -> None:
    api_lane.default_api_verifier_context.cache_clear()
    first = api_lane.default_api_verifier_context()
    second = api_lane.default_api_verifier_context()

    assert first is second
    assert first.client is second.client
    assert first.manifest["route_count"] == 127


def test_individual_api_verifiers_accept_shared_context(shared_context) -> None:
    for _spec, module in api_lane._iter_verifiers():
        assert module.verify(shared_context) == []


@pytest.mark.parametrize("spec", api_lane.API_VERIFIER_SPECS)
def test_public_api_verifier_entrypoints_return_success_with_shared_context(
    monkeypatch,
    capsys,
    spec,
    shared_context,
) -> None:
    module = importlib.import_module(spec.module_name)
    monkeypatch.setattr(module, "default_api_verifier_context", lambda: shared_context)

    assert module.main() == 0
    assert module.SUCCESS_MESSAGE in capsys.readouterr().out


def test_combined_api_verifier_lane_executes_all_specs(monkeypatch) -> None:
    calls: list[str] = []
    context = object()

    def _module(milestone_id: str):
        def verify(received_context):
            calls.append(milestone_id)
            assert received_context is context
            return []

        return SimpleNamespace(SUCCESS_MESSAGE=f"{milestone_id} passed", verify=verify)

    monkeypatch.setattr(
        api_lane,
        "_iter_verifiers",
        lambda: [(spec, _module(spec.milestone_id)) for spec in api_lane.API_VERIFIER_SPECS],
    )

    assert api_lane.run_api_verifier_lane(context) == 0
    assert calls == [spec.milestone_id for spec in api_lane.API_VERIFIER_SPECS]


def test_verify_all_uses_cached_api_verifier_lane(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(run_all_legacy, "_P1_API_VERIFIER_LANE_RAN", False)
    monkeypatch.setattr(
        run_all_legacy,
        "run_cmd",
        lambda command, **_kwargs: pytest.fail(f"unexpected process launch: {command}"),
    )
    monkeypatch.setattr(
        api_lane,
        "run_api_verifier_lane",
        lambda: calls.append("lane") or 0,
    )

    run_all_legacy.verify_uaa_p1_080_api_route_classification()
    run_all_legacy.verify_uaa_p1_081_fastapi_security_headers()
    run_all_legacy.verify_uaa_p1_082_loopback_cors()
    run_all_legacy.verify_uaa_p1_083_local_auth_gate()
    run_all_legacy.verify_uaa_p1_084_mutating_route_idempotency()
    run_all_legacy.verify_uaa_p1_085_targeted_rate_limits()
    run_all_legacy.verify_uaa_p1_086_api_boundary_enforcement_tests()

    assert calls == ["lane"]
