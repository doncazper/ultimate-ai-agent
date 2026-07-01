#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.secrets import (  # noqa: E402
    ProviderCredentialVaultPosture,
    ProviderCredentialVaultRecord,
    ProviderCredentialVaultSnapshot,
    build_provider_credential_vault_snapshot,
)


REQUIRED_POSTURES = {
    "vault_not_configured",
    "vault_blocked",
    "secret_ref_available",
    "secret_ref_revoked",
    "rotation_required",
    "validation_required_but_blocked",
    "invocation_requires_approval",
}
REQUIRED_BLOCKERS = {
    "CREDENTIAL_VAULT_METADATA_ONLY",
    "RAW_SECRET_MATERIAL_DENIED",
    "PROVIDER_VALIDATION_BLOCKED",
    "PROVIDER_INVOCATION_APPROVAL_REQUIRED",
    "PROVIDER_SDK_CALL_BLOCKED",
    "MODEL_INVOCATION_BLOCKED",
}
REQUIRED_DECLARED_CAPABILITIES = {
    "provider_credential_vault_contract_shell_metadata_only",
    "provider_credential_vault_contract_cli_inspection",
}
REQUIRED_BLOCKED_CAPABILITIES = {
    "provider_credential_vault_secret_collection",
    "provider_credential_vault_raw_secret_storage",
    "provider_credential_vault_os_backend_access",
    "provider_credential_vault_validation_authority",
    "provider_credential_vault_invocation_authority",
    "provider_credential_vault_presence_as_authority",
}
FORBIDDEN_TEXT = (
    "api_key=",
    "paste key",
    "save key",
    "raw prompt",
    "raw response",
    "provider payload",
    "/users/",
    "username=",
    "hostname=",
    "bearer ",
)
REQUIRED_DOC_FRAGMENTS = {
    "Credential Vault Contract Shell",
    "ProviderCredentialVaultPosture",
    "metadata-only",
    "does not authorize provider validation",
    "does not authorize provider invocation",
    "No secret collection UI",
    "No OS keychain or credential manager access",
}


def main() -> int:
    failures: list[str] = []
    snapshot = build_provider_credential_vault_snapshot()
    payload = snapshot.model_dump(mode="json")
    text = json.dumps(payload, sort_keys=True).lower()

    if set(payload["supported_postures"]) != REQUIRED_POSTURES:
        failures.append("credential vault posture vocabulary drifted")
    if snapshot.status != "metadata_only":
        failures.append("credential vault snapshot status is not metadata_only")
    if not REQUIRED_BLOCKERS.issubset(set(snapshot.blocker_codes)):
        failures.append("credential vault snapshot blocker codes are incomplete")
    denied_snapshot_flags = [
        snapshot.secret_collection_enabled,
        snapshot.raw_secret_storage_enabled,
        snapshot.os_credential_backend_access_enabled,
        snapshot.credential_validation_enabled,
        snapshot.provider_invocation_enabled,
        snapshot.provider_sdk_call_enabled,
        snapshot.model_invocation_enabled,
        snapshot.vault_presence_authorizes_validation,
        snapshot.vault_presence_authorizes_invocation,
    ]
    if any(denied_snapshot_flags):
        failures.append("credential vault snapshot grants runtime authority")
    for record in snapshot.records:
        denied_record_flags = [
            record.vault_record_grants_authority,
            record.secret_collection_enabled,
            record.raw_secret_material_available,
            record.secret_material_persisted_by_repo,
            record.os_credential_backend_access_enabled,
            record.credential_validation_call_enabled,
            record.validation_authority_granted,
            record.provider_sdk_call_enabled,
            record.model_invocation_enabled,
            record.invocation_authority_granted,
        ]
        if any(denied_record_flags):
            failures.append(f"{record.record_ref} grants validation or invocation authority")
        if not REQUIRED_BLOCKERS.issubset(set(record.blocker_codes)):
            failures.append(f"{record.record_ref} blocker codes are incomplete")
        for field_name in [
            "provider_ref",
            "model_ref",
            "credential_ref",
            "policy_ref",
            "approval_scope_ref",
            "budget_decision_ref",
            "expected_receipt_ref",
            "revocation_ref",
        ]:
            value = getattr(record, field_name)
            if not value or ":" not in value:
                failures.append(f"{record.record_ref} has malformed {field_name}")

    available_record = ProviderCredentialVaultRecord(
        record_ref="credential-vault-record-ref:verifier:available",
        posture=ProviderCredentialVaultPosture.secret_ref_available,
        provider_ref="provider-ref:verifier:reference",
        model_ref="model-ref:verifier:review-only",
        credential_ref="credential-ref:verifier:reference",
        secret_ref="secret-ref:verifier:metadata-only",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        budget_decision_ref="budget-decision-ref:verifier:required",
        expected_receipt_ref="receipt-ref:verifier:future-required",
        revocation_ref="revocation-ref:verifier:not-active",
    )
    if available_record.validation_authority_granted or available_record.invocation_authority_granted:
        failures.append("secret_ref_available posture grants authority")
    try:
        ProviderCredentialVaultSnapshot(status="provider_connected")
    except Exception:
        pass
    else:
        failures.append("credential vault snapshot accepted authority-shaped status")
    for raw_secret_ref in (
        "secret-ref:verifier:sk-test-token",
        "secret-ref:verifier:xoxb-test-token",
        "secret-ref:verifier:token-test-secret",
    ):
        try:
            ProviderCredentialVaultRecord(secret_ref=raw_secret_ref)
        except Exception:
            pass
        else:
            failures.append("credential vault record accepted raw token-shaped secret ref")

    inspect_result = subprocess.run(
        [sys.executable, "scripts/inspect_credential_vault_contract.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if inspect_result.returncode != 0:
        failures.append("inspect_credential_vault_contract.py failed")
    else:
        try:
            cli_payload = json.loads(inspect_result.stdout)
        except json.JSONDecodeError:
            failures.append("inspect_credential_vault_contract.py did not emit JSON")
        else:
            if cli_payload.get("contract_ref") != "contract-ref:provider-credential-vault-shell:v1":
                failures.append("CLI credential vault contract ref drifted")
            if set(cli_payload.get("supported_postures", [])) != REQUIRED_POSTURES:
                failures.append("CLI credential vault postures drifted")

    combined_text = (text + "\n" + inspect_result.stdout.lower()).lower()
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in combined_text:
            failures.append(f"unsafe credential vault text found: {forbidden}")

    manifest = build_api_manifest(app)
    missing_declared = REQUIRED_DECLARED_CAPABILITIES - set(manifest.capabilities_declared)
    missing_blocked = REQUIRED_BLOCKED_CAPABILITIES - set(manifest.capabilities_blocked)
    if missing_declared:
        failures.append(f"manifest missing declared vault capabilities: {sorted(missing_declared)}")
    if missing_blocked:
        failures.append(f"manifest missing blocked vault capabilities: {sorted(missing_blocked)}")

    doc_path = ROOT / "docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md"
    if not doc_path.exists():
        failures.append("credential vault contract shell doc is missing")
    else:
        doc_text = doc_path.read_text(encoding="utf-8")
        for fragment in REQUIRED_DOC_FRAGMENTS:
            if fragment not in doc_text:
                failures.append(f"credential vault doc missing fragment: {fragment}")
        lowered_doc = doc_text.lower()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in lowered_doc:
                failures.append(f"unsafe credential vault doc text found: {forbidden}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("credential vault contract shell verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
