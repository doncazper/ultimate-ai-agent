from __future__ import annotations

import copy

import pytest

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

    assert any(item.startswith("schema:validation_failed") for item in failures)


def test_secret_like_ref_is_rejected() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["implementation_plan"]["key_plan_ref"] = "plan-ref:sk_live_abc123"

    failures = verifier.verify(payload)

    assert any("secret-like durable content" in item for item in failures)
    assert all("sk_live_abc123" not in item for item in failures)


def test_schema_error_never_echoes_secret_value() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["task_ref"] = "dev-task:sk_live_abc123"

    failures = verifier.verify(payload)

    assert failures
    assert any("secret-like durable content" in item for item in failures)
    assert all("sk_live_abc123" not in item for item in failures)


def test_implementation_plan_drift_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["implementation_plan"]["rollback_plan_ref"] = (
        "plan-ref:finance/FIN-001/no-rollback"
    )

    failures = verifier.verify(payload)

    assert failures


def test_blocked_queue_handoff_drift_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["board_claim_plan"]["task_state_at_recording"] = "queued"

    failures = verifier.verify(payload)

    assert failures


def test_arbitrary_operator_financial_values_remain_blocked() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["first_slice"]["arbitrary_operator_values_allowed"] = True

    failures = verifier.verify(payload)

    assert failures


def test_dependency_commit_must_be_in_current_history(monkeypatch) -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))

    class MissingCommit:
        returncode = 1

    monkeypatch.setattr(
        verifier.subprocess, "run", lambda *args, **kwargs: MissingCommit()
    )

    failures = verifier.verify(payload)

    assert any(
        "dependency commit evidence is not in current history" in item
        for item in failures
    )


def test_duplicate_json_keys_fail_closed(tmp_path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"authority_posture":{},"authority_posture":{}}')

    with pytest.raises(ValueError, match="duplicate object key"):
        verifier._load(duplicate)
