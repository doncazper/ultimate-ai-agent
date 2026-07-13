import json
import os
import subprocess
import sys

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
)


def test_phase09_extension_catalog_has_operator_posture_without_callability() -> None:
    catalog = build_default_inspectable_extension_catalog()
    payload = catalog.model_dump(mode="json")

    assert payload["read_only"] is True
    assert payload["inspectable_catalog_enabled"] is True
    assert payload["callable_catalog_enabled"] is False
    assert payload["automatic_instruction_loading_enabled"] is False
    assert payload["full_instruction_auto_load_enabled"] is False
    assert payload["hidden_skill_activation_enabled"] is False
    assert payload["skill_runtime_import_enabled"] is False
    assert payload["external_marketplace_fetch_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert "doc:runtime-extensibility-final" in payload["docs_refs"]
    assert (
        "verifier:runtime-extensibility-final"
        in payload["final_hardening_refs"]
    )
    install_posture = payload["install_disabled_posture"]
    assert install_posture["status"] == "blocked_pending_authority_and_approval"
    assert install_posture["plugin_install_enabled"] is False
    assert install_posture["runtime_import_enabled"] is False
    assert install_posture["plugin_execution_enabled"] is False
    assert install_posture["candidates"][0]["exact_approval_required"] is True
    assert install_posture["candidates"][0]["approval_ref_authority"] is False

    for entry in payload["entries"]:
        assert entry["visibility_status"] in {
            "implemented",
            "partial",
            "planned",
            "mock_only",
            "blocked",
            "deprecated",
            "contradicted",
            "unknown",
        }
        assert entry["callable_posture"] in {
            "inspectable_only",
            "blocked_runtime",
            "future_exact_lane_required",
        }
        assert entry["callable_posture"] != "callable"
        assert entry["blocked_reason"]
        assert entry["review_evidence_refs"]
        assert entry["safe_adoption_posture"] in {
            "repo_owned_metadata_only",
            "reviewed_adaptation_required",
            "blocked_until_scoped_milestone",
        }


def test_uaa_extensions_cli_inspects_same_safe_catalog() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
            "--json",
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )

    payload = json.loads(result.stdout)
    assert payload["catalog_ref"] == "inspectable-catalog:uaa-extension-catalog-v1"
    assert payload["callable_catalog_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["install_disabled_posture"]["plugin_install_enabled"] is False
    assert payload["install_disabled_posture"]["candidate_count"] == 1
    assert payload["entries"]


def test_uaa_extensions_cli_inspects_install_disabled_posture() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-install-disabled-posture",
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )

    payload = json.loads(result.stdout)
    assert payload["posture_ref"] == "extension-install-disabled-posture:uaa:v1"
    assert payload["plugin_install_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["plugin_execution_enabled"] is False
    assert payload["candidates"][0]["disabled_install_record_persisted"] is False


def test_uaa_extensions_cli_records_install_disabled_receipt(tmp_path) -> None:
    authority_state_dir = tmp_path / "authority"
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(authority_state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.approved_safe_local_work_session,
            requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:extension-cli-record",
            safe_summary="Allow exact disabled extension install metadata CLI receipt.",
        ),
        idempotency_ref="idempotency-ref:extension-cli-record-lease",
        approval_ref="approval-ref:test-authority:extension-cli-record-lease",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "record-install-disabled-receipt",
            "--authority-state-dir",
            str(authority_state_dir),
            "--approval-ref",
            "approval-ref:extension-install-disabled:cli",
            "--idempotency-ref",
            "idempotency-ref:extension-install-disabled:cli",
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert "EXTENSION_INSTALL_DISABLED_ATOMIC_AUTHORITY_STATE_REQUIRED" in result.stderr
    assert not (authority_state_dir / "extension_install_disabled_records").exists()


def test_uaa_extensions_cli_rolls_back_install_disabled_receipt(tmp_path) -> None:
    authority_state_dir = tmp_path / "authority"
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(authority_state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.approved_safe_local_work_session,
            requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
            decision_reason_ref="decision-reason-ref:extension-cli-rollback",
            safe_summary=(
                "Allow exact disabled extension install metadata CLI rollback."
            ),
        ),
        idempotency_ref="idempotency-ref:extension-cli-rollback-lease",
        approval_ref="approval-ref:test-authority:extension-cli-rollback-lease",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "rollback-install-disabled-receipt",
            "--authority-state-dir",
            str(authority_state_dir),
            "--approval-ref",
            "approval-ref:extension-install-disabled-delete:cli",
            "--idempotency-ref",
            "idempotency-ref:extension-install-disabled-delete:cli",
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert (
        "EXTENSION_INSTALL_DISABLED_DELETE_ATOMIC_AUTHORITY_STATE_REQUIRED"
        in result.stderr
    )
