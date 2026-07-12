#!/usr/bin/env python3
"""Verify runtime capability foundation Phase 09 extensibility hardening."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    build_extension_install_disabled_approval_request,
    build_extension_install_disabled_delete_approval_request,
    build_extension_install_disabled_record_delete_receipt,
    build_extension_install_disabled_record_receipt,
)


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOC_REFS = {
    "doc:plugin-skill-ecosystem-boundary",
    "doc:inspectable-extension-catalog",
    "doc:extension-activation-grants",
    "doc:runtime-extensibility-final",
}

REQUIRED_BLOCKED = {
    "callable_extension_catalog",
    "plugin_runtime_import",
    "arbitrary_plugin_execution",
    "skill_runtime_import",
    "connector_writes",
    "shell_subprocess_execution",
    "unrestricted_network_access",
    "browser_automation",
    "public_distribution",
}

DENIED_TRUE_FLAGS = (
    "callable_catalog_enabled",
    "automatic_instruction_loading_enabled",
    "full_instruction_auto_load_enabled",
    "hidden_skill_activation_enabled",
    "skill_runtime_import_enabled",
    "external_marketplace_fetch_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "network_access_enabled",
    "browser_automation_enabled",
    "mobile_control_enabled",
    "public_distribution_claimed",
)


class VerificationError(RuntimeError):
    """Raised when Phase 09 verification fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _catalog_payload() -> dict[str, object]:
    return build_default_inspectable_extension_catalog().model_dump(mode="json")


def _verify_catalog_contract(payload: dict[str, object]) -> None:
    _require(
        payload["catalog_status"] == "read_only_inspection", "catalog is not read-only"
    )
    for field in DENIED_TRUE_FLAGS:
        _require(payload[field] is False, f"catalog enables denied flag: {field}")

    _require(
        REQUIRED_DOC_REFS.issubset(set(payload["docs_refs"])),
        "catalog missing required docs refs",
    )
    _require(
        REQUIRED_BLOCKED.issubset(set(payload["blocked_capabilities"])),
        "catalog missing blocked capability refs",
    )
    _require(
        "doc:runtime-extensibility-final"
        in payload["developer_guidance_refs"],
        "catalog missing Phase 09 developer guidance ref",
    )
    _require(
        "verifier:runtime-extensibility-final"
        in payload["final_hardening_refs"],
        "catalog missing Phase 09 verifier ref",
    )
    install_posture = payload["install_disabled_posture"]
    _require(
        install_posture["status"] == "blocked_pending_authority_and_approval",
        "install-disabled posture drifted",
    )
    for field in (
        "plugin_install_enabled",
        "plugin_enablement_enabled",
        "plugin_execution_enabled",
        "runtime_import_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "provider_model_call_enabled",
        "production_authority_granted",
    ):
        _require(install_posture[field] is False, f"install posture enables {field}")
    candidates = install_posture["candidates"]
    _require(
        isinstance(candidates, list) and len(candidates) == 1,
        "install-disabled candidate missing",
    )
    candidate = candidates[0]
    _require(candidate["exact_approval_required"] is True, "exact approval not required")
    _require(candidate["approval_ref_authority"] is False, "approval ref claims authority")
    _require(
        candidate["disabled_install_record_persisted"] is False,
        "disabled install record was persisted",
    )
    _require(candidate["file_hashes"], "install-disabled hash refs missing")
    _verify_authorized_install_disabled_record_receipt()

    entries = payload["entries"]
    _require(isinstance(entries, list) and len(entries) >= 2, "catalog entries missing")
    for entry in entries:
        for field in (
            "visibility_status",
            "trust_posture",
            "callable_posture",
            "required_grant_refs",
            "blocked_reason",
            "review_evidence_refs",
            "safe_adoption_posture",
        ):
            _require(field in entry, f"catalog entry missing {field}")
        _require(
            entry["callable_posture"] != "callable", "entry claims callable posture"
        )
        _require(entry["review_evidence_refs"], "entry missing review evidence refs")


def _verify_authorized_install_disabled_record_receipt() -> None:
    approval_authority = LocalApprovalAuthority()
    request = approval_authority.create_request(
        build_extension_install_disabled_approval_request()
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled:verifier",
    )
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:extension-install-disabled:verifier",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Allow verifier to inspect disabled extension install receipt.",
    )
    receipt = build_extension_install_disabled_record_receipt(
        leases=[lease],
        approval_authority=approval_authority,
        approval_ref=grant.approval_ref,
    ).model_dump(mode="json")
    delete_approval_authority = LocalApprovalAuthority()
    delete_request = delete_approval_authority.create_request(
        build_extension_install_disabled_delete_approval_request()
    )
    delete_grant = delete_approval_authority.grant(
        delete_request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled-delete:verifier",
    )
    delete_receipt = build_extension_install_disabled_record_delete_receipt(
        leases=[lease],
        approval_authority=delete_approval_authority,
        approval_ref=delete_grant.approval_ref,
    ).model_dump(mode="json")

    _require(
        receipt["status"] == "disabled_install_record_receipt_recorded",
        "authorized install-disabled receipt was not recorded",
    )
    _require(receipt["authority_decision_outcome"] == "allow", "receipt not allowed")
    _require(receipt["authority_lease_ref"] == lease.lease_ref, "lease ref missing")
    _require(receipt["approval_ref"] == grant.approval_ref, "approval ref missing")
    _require(receipt["approval_ref_authority"] is False, "approval ref is authority")
    _require(
        receipt["record_storage_mode"] == "receipt_only",
        "verifier receipt unexpectedly persisted",
    )
    _require(
        receipt["durable_store_persistence"] is False,
        "verifier receipt wrote durable store",
    )
    _require(
        delete_receipt["status"] == "disabled_install_record_delete_receipt_recorded",
        "authorized install-disabled delete receipt was not recorded",
    )
    _require(
        delete_receipt["authority_decision_outcome"] == "allow",
        "delete receipt not allowed",
    )
    _require(
        delete_receipt["deletion_status"] == "record_already_absent",
        "delete receipt unexpectedly observed durable state",
    )
    _require(
        delete_receipt["approval_ref"] == delete_grant.approval_ref,
        "delete approval ref missing",
    )
    for field in (
        "plugin_install_enabled",
        "plugin_enablement_enabled",
        "plugin_execution_enabled",
        "runtime_import_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "provider_model_call_enabled",
        "production_authority_granted",
    ):
        _require(receipt[field] is False, f"receipt enables {field}")
        _require(delete_receipt[field] is False, f"delete receipt enables {field}")


def _verify_api_route(payload: dict[str, object]) -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/extensions/catalog")
    _require(response.status_code == 200, "extension catalog route failed")
    body = response.json()
    _require(body["success"] is True, "extension catalog route did not succeed")
    _require(
        body["operation"] == "inspect_extension_catalog", "route operation drifted"
    )
    _require(
        body["data"]["catalog_ref"] == payload["catalog_ref"], "route catalog drifted"
    )
    for field in DENIED_TRUE_FLAGS:
        _require(body["data"][field] is False, f"route enables denied flag: {field}")
    paths = app.openapi()["paths"]
    _require(
        "/extensions/disabled-install-records" in paths,
        "disabled-install record route missing",
    )
    _require(
        paths["/extensions/disabled-install-records"]["post"]["operationId"]
        == "post_extensions_disabled_install_records",
        "disabled-install record route operation drifted",
    )
    _require(
        "/extensions/disabled-install-records/rollback" in paths,
        "disabled-install rollback route missing",
    )
    _require(
        paths["/extensions/disabled-install-records/rollback"]["post"]["operationId"]
        == "post_extensions_disabled_install_records_rollback",
        "disabled-install rollback route operation drifted",
    )


def _verify_cli(payload: dict[str, object]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    cli_payload = json.loads(result.stdout)
    _require(
        cli_payload["catalog_ref"] == payload["catalog_ref"], "CLI catalog drifted"
    )
    _require(
        cli_payload["callable_catalog_enabled"] is False,
        "CLI claims callable catalog authority",
    )
    _require(
        cli_payload["install_disabled_posture"]["plugin_install_enabled"] is False,
        "CLI claims plugin install authority",
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-install-disabled-posture",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    posture_payload = json.loads(result.stdout)
    _require(
        posture_payload["posture_ref"] == "extension-install-disabled-posture:uaa:v1",
        "CLI install-disabled posture drifted",
    )
    _require(
        posture_payload["plugin_install_enabled"] is False,
        "CLI install-disabled posture enables plugin install",
    )
    help_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "--help",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    _require(
        "record-install-disabled-receipt" in help_result.stdout,
        "CLI disabled-install receipt command missing",
    )
    _require(
        "rollback-install-disabled-receipt" in help_result.stdout,
        "CLI disabled-install rollback command missing",
    )


def _verify_docs() -> None:
    doc = (
        ROOT
        / "docs"
        / "control_center"
        / "UAA_RUNTIME_EXTENSIBILITY_FINAL.md"
    ).read_text(encoding="utf-8")
    scoreboard = (
        ROOT / "docs" / "control_center" / "UAA_RUNTIME_CAPABILITY_SCOREBOARD.md"
    ).read_text(encoding="utf-8")

    for text, name in ((doc, "Phase 09 doc"), (scoreboard, "scoreboard")):
        lowered = text.lower()
        for phrase in (
            "plugin runtime import remains blocked",
            "connector writes remain blocked",
            "production authority remains blocked",
            "safe refs",
        ):
            _require(phrase in lowered, f"{name} missing phrase: {phrase}")
        terminal_phrase = "30-day plan" if name == "Phase 09 doc" else "optional next program"
        _require(
            terminal_phrase in lowered,
            f"{name} missing phrase: {terminal_phrase}",
        )
        for unsafe in (
            "plugin runtime import is enabled",
            "connector writes are enabled",
            "production authority is enabled",
            "broad autonomy is enabled",
        ):
            _require(unsafe not in lowered, f"{name} contains unsafe claim: {unsafe}")


def main() -> int:
    try:
        payload = _catalog_payload()
        _verify_catalog_contract(payload)
        _verify_api_route(payload)
        _verify_cli(payload)
        _verify_docs()
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("UAA runtime extensibility final verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
