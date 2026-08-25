from __future__ import annotations

import copy
import json
import sys

import pytest

from scripts import verify_fin001_activation as verifier


def test_checked_in_fin001_activation_is_valid() -> None:
    assert verifier.verify() == []


def test_cli_reports_pending_unblock_not_claim_readiness(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["verify_fin001_activation.py"])
    assert verifier.main() == 0
    result = json.loads(capsys.readouterr().out)

    assert result["status"] == "BLOCKED_PENDING_ACTIVATION_MERGE_AND_EXPLICIT_UNBLOCK"
    assert result["claim_ready"] is False
    assert result["task_claimed"] is False


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

    assert "FIN-001 complete first-slice boundary drifted" in failures


def test_authority_promotion_fails_closed() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["authority_posture"]["real_financial_data_allowed"] = True

    failures = verifier.verify(payload)

    assert "FIN-001 complete authority posture drifted" in failures


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


def test_schema_annotations_are_included_in_secret_scan() -> None:
    schema = {"description": "credential-ref:ghp_abcdef123456"}

    assert verifier._has_secret_like_durable_content(schema) is True


def test_schema_credential_property_default_is_included_in_secret_scan() -> None:
    schema = {
        "properties": {"service_api_key": {"type": "string", "default": "opaque-value"}}
    }

    assert verifier._has_secret_like_durable_content(schema) is True


def test_nested_schema_credential_annotation_is_included_in_secret_scan() -> None:
    schema = {
        "properties": {"service_api_key": {"allOf": [{"default": "abcdefghijklmnop"}]}}
    }

    assert verifier._has_secret_like_durable_content(schema) is True


def test_schema_raw_local_path_is_rejected() -> None:
    slash = chr(47)
    backslash = chr(92)
    for raw_path in (
        f"{slash}home{slash}example{slash}private",
        f"{slash}workspace{slash}ultimate-ai-agent{slash}private",
        f"{slash}root{slash}private",
        f"{slash}tmp{slash}private",
        f"{backslash}{backslash}server{backslash}share{backslash}private",
    ):
        assert verifier._has_raw_local_path({"description": raw_path}) is True


def test_invalid_schema_returns_bounded_failure(monkeypatch) -> None:
    def invalid_schema(_schema) -> None:
        raise RuntimeError("sensitive local diagnostic")

    monkeypatch.setattr(verifier.Draft202012Validator, "check_schema", invalid_schema)

    failures = verifier.verify()

    assert failures == ["activation schema is invalid or unresolvable"]
    assert all("sensitive local diagnostic" not in failure for failure in failures)


def test_top_level_binding_is_independently_pinned() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["task_ref"] = "dev-task:queue-v2-q26-finance-compliance-local-product"

    failures = verifier.verify(payload)

    assert "FIN-001 top-level activation binding drifted" in failures


def test_top_level_shape_is_independently_pinned() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    payload["runtime_authority_override"] = False

    failures = verifier.verify(payload)

    assert "FIN-001 top-level activation shape drifted" in failures


def test_founder_direction_artifact_receipt_is_resolved(monkeypatch) -> None:
    original_load = verifier._load

    def load_with_drift(path):
        loaded = original_load(path)
        if path.name == "private_dogfood_direction_acceptance_v1.json":
            loaded["decision_receipt_ref"] = "receipt-ref:founder-direction:drifted"
        return loaded

    monkeypatch.setattr(verifier, "_load", load_with_drift)

    failures = verifier.verify()

    assert "founder direction decision receipt drifted" in failures


def test_complete_founder_direction_artifact_is_verified(monkeypatch) -> None:
    original_load = verifier._load

    def load_with_scope_drift(path):
        loaded = original_load(path)
        if path.name == "private_dogfood_direction_acceptance_v1.json":
            loaded["programs"]["q26"]["implementation_scope_refs"] = []
        return loaded

    monkeypatch.setattr(verifier, "_load", load_with_scope_drift)

    failures = verifier.verify()

    assert "founder direction acceptance verification failed" in failures


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

    assert "FIN-001 complete first-slice boundary drifted" in failures


def test_complete_authority_posture_is_independently_pinned() -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    del payload["authority_posture"]["browser_runtime_allowed"]

    failures = verifier.verify(payload)

    assert "FIN-001 complete authority posture drifted" in failures


def test_nonlocal_schema_reference_is_rejected_before_validation() -> None:
    schema = {"$ref": "https://schemas.example.invalid/finance.json"}

    assert verifier._schema_has_nonlocal_ref(schema) is True


def test_nonlocal_dynamic_schema_reference_is_rejected_before_validation() -> None:
    schema = {"$dynamicRef": "https://schemas.example.invalid/finance.json"}

    assert verifier._schema_has_nonlocal_ref(schema) is True


def test_dependency_commit_must_be_in_current_history(monkeypatch) -> None:
    payload = copy.deepcopy(verifier._load(verifier.LEDGER_PATH))
    original_run = verifier.subprocess.run

    class MissingCommit:
        returncode = 1

    def run_with_missing_commit(*args, **kwargs):
        if args[0][0:2] == ["git", "merge-base"]:
            return MissingCommit()
        return original_run(*args, **kwargs)

    monkeypatch.setattr(verifier.subprocess, "run", run_with_missing_commit)

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
