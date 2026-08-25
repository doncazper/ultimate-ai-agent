from __future__ import annotations

import copy

from scripts import verify_fin001_activation as verifier


def test_checked_in_fin001_activation_is_valid() -> None:
    assert verifier.verify() == []


def test_dependency_removal_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["dependency_evidence"].pop()

    failures = verifier.verify(payload)

    assert failures


def test_scope_expansion_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["first_slice"]["scope_refs"].append(
        "scope-ref:finance/FIN-001/live-connector"
    )

    failures = verifier.verify(payload)

    assert "FIN-001 first-slice scope drifted" in failures


def test_authority_promotion_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["authority_posture"]["real_financial_data_allowed"] = True

    failures = verifier.verify(payload)

    assert any("real_financial_data_allowed" in item for item in failures)


def test_secret_like_ref_is_rejected() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["implementation_plan"]["key_plan_ref"] = "plan-ref:sk_live_abc123"

    failures = verifier.verify(payload)

    assert any("secret-like durable content" in item for item in failures)
