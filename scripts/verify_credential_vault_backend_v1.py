#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from pydantic import SecretStr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.secrets import (  # noqa: E402
    LocalCredentialVaultBackend,
    LocalCredentialVaultEnrollmentRequest,
    LocalCredentialVaultRevokeRequest,
    LocalCredentialVaultRotationRequiredRequest,
    ProviderCredentialVaultPosture,
    build_local_credential_vault_enrollment_approval_request,
    build_local_credential_vault_revoke_approval_request,
    build_local_credential_vault_rotation_approval_request,
)


REQUIRED_DECLARED_CAPABILITIES = {
    "provider_credential_vault_local_secret_ref_backend_v1",
    "provider_credential_vault_backend_cli_inspection",
}
REQUIRED_BLOCKED_CAPABILITIES = {
    "provider_credential_vault_raw_secret_storage",
    "provider_credential_vault_secret_resolution_api",
    "provider_credential_vault_raw_secret_display",
    "provider_credential_vault_validation_authority",
    "provider_credential_vault_invocation_authority",
    "provider_credential_vault_presence_as_authority",
}
REQUIRED_DOC_FRAGMENTS = {
    "Credential Vault Backend V1",
    "local safe-ref ledger",
    "does not persist recoverable secret material",
    "LocalApprovalAuthority",
    "does not authorize provider validation",
    "does not authorize provider invocation",
    "scripts/inspect_credential_vault_backend.py",
}
FORBIDDEN_OUTPUT = (
    "api_key=",
    "raw prompt",
    "raw response",
    "provider payload",
    "/users/",
    "username=",
    "hostname=",
)


def _enrollment_request(secret_value: str) -> LocalCredentialVaultEnrollmentRequest:
    return LocalCredentialVaultEnrollmentRequest(
        run_id="run-ref:credential-vault:verify",
        provider_ref="provider-ref:openai-compatible:reference",
        model_ref="model-ref:openai-compatible:review-only",
        credential_ref="credential-ref:openai-compatible:scoped-local",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        approval_ref="approval-ref:credential-vault:verify-enroll",
        approval_scope_ref="approval-scope-ref:provider-runtime:required",
        budget_decision_ref="budget-decision-ref:openai-compatible:required",
        expected_receipt_ref="receipt-ref:credential-vault:verify-enroll",
        idempotency_ref="idempotency-ref:credential-vault:verify-enroll",
        secret_value=SecretStr(secret_value),
    )


def _authority_for_enrollment(
    request: LocalCredentialVaultEnrollmentRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_enrollment_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def _authority_for_rotation(
    request: LocalCredentialVaultRotationRequiredRequest,
) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_rotation_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def _authority_for_revoke(request: LocalCredentialVaultRevokeRequest) -> LocalApprovalAuthority:
    authority = LocalApprovalAuthority()
    approval_request = build_local_credential_vault_revoke_approval_request(request)
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator:local",
        approval_ref=request.approval_ref,
    )
    return authority


def main() -> int:
    failures: list[str] = []
    transient_value = f"transient-{uuid.uuid4().hex}"
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = Path(tmp) / "vault"
        backend = LocalCredentialVaultBackend(state_dir)
        missing_snapshot = backend.inspect()
        if missing_snapshot.posture != ProviderCredentialVaultPosture.vault_not_configured:
            failures.append("missing vault state did not inspect as vault_not_configured")
        if state_dir.exists():
            failures.append("read-only missing-state inspection created vault state")

        enrollment_request = _enrollment_request(transient_value)
        try:
            backend.enroll_secret(enrollment_request)
        except ValueError:
            pass
        else:
            failures.append("vault backend enrollment wrote without exact approval")
        enroll_receipt = backend.enroll_secret(
            enrollment_request,
            approval_authority=_authority_for_enrollment(enrollment_request),
        )
        enroll_replay = backend.enroll_secret(
            enrollment_request,
            approval_authority=_authority_for_enrollment(enrollment_request),
        )
        if not enroll_receipt.allowed:
            failures.append("vault backend enrollment did not return an allowed safe-ref receipt")
        if enroll_replay != enroll_receipt:
            failures.append("vault backend enrollment idempotency replay drifted")
        if enroll_receipt.secret_resolution_enabled or enroll_receipt.provider_invocation_enabled:
            failures.append("enrollment receipt enables secret resolution or invocation")

        rotation_receipt = backend.mark_rotation_required(
            rotation_request := LocalCredentialVaultRotationRequiredRequest(
                run_id=enrollment_request.run_id,
                secret_ref=enroll_receipt.secret_ref,
                provider_ref=enrollment_request.provider_ref,
                model_ref=enrollment_request.model_ref,
                credential_ref=enrollment_request.credential_ref,
                rotation_required_ref="rotation-ref:credential-vault:verify-required",
                policy_ref="policy-ref:provider-runtime:disabled-by-default",
                approval_ref="approval-ref:credential-vault:verify-rotation",
                approval_scope_ref="approval-scope-ref:provider-runtime:required",
                budget_decision_ref=enrollment_request.budget_decision_ref,
                expected_receipt_ref="receipt-ref:credential-vault:verify-rotation",
                idempotency_ref="idempotency-ref:credential-vault:verify-rotation",
            ),
            approval_authority=_authority_for_rotation(rotation_request),
        )
        if rotation_receipt.posture != ProviderCredentialVaultPosture.rotation_required:
            failures.append("rotation-required receipt posture drifted")

        revoke_receipt = backend.revoke_secret_ref(
            revoke_request := LocalCredentialVaultRevokeRequest(
                run_id=enrollment_request.run_id,
                secret_ref=enroll_receipt.secret_ref,
                provider_ref=enrollment_request.provider_ref,
                model_ref=enrollment_request.model_ref,
                credential_ref=enrollment_request.credential_ref,
                revocation_ref="revocation-ref:credential-vault:verify-revoked",
                policy_ref="policy-ref:provider-runtime:disabled-by-default",
                approval_ref="approval-ref:credential-vault:verify-revoke",
                approval_scope_ref="approval-scope-ref:provider-runtime:required",
                budget_decision_ref=enrollment_request.budget_decision_ref,
                expected_receipt_ref="receipt-ref:credential-vault:verify-revoke",
                idempotency_ref="idempotency-ref:credential-vault:verify-revoke",
            ),
            approval_authority=_authority_for_revoke(revoke_request),
        )
        if revoke_receipt.posture != ProviderCredentialVaultPosture.secret_ref_revoked:
            failures.append("revoke receipt posture drifted")
        wrong_run_revoke = LocalCredentialVaultRevokeRequest(
            run_id="run-ref:credential-vault:wrong-run",
            secret_ref=enroll_receipt.secret_ref,
            provider_ref=enrollment_request.provider_ref,
            model_ref=enrollment_request.model_ref,
            credential_ref=enrollment_request.credential_ref,
            revocation_ref="revocation-ref:credential-vault:wrong-run",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            approval_ref="approval-ref:credential-vault:wrong-run-revoke",
            approval_scope_ref="approval-scope-ref:provider-runtime:required",
            budget_decision_ref=enrollment_request.budget_decision_ref,
            expected_receipt_ref="receipt-ref:credential-vault:wrong-run-revoke",
            idempotency_ref="idempotency-ref:credential-vault:wrong-run-revoke",
        )
        try:
            backend.revoke_secret_ref(
                wrong_run_revoke,
                approval_authority=_authority_for_revoke(wrong_run_revoke),
            )
        except ValueError as exc:
            if "RECORD_SCOPE_MISMATCH" not in str(exc):
                failures.append(f"wrong-run revoke failed with wrong error: {exc}")
        else:
            failures.append("wrong-run revoke approval mutated an existing secret_ref")

        terminal_rotation = LocalCredentialVaultRotationRequiredRequest(
            run_id=enrollment_request.run_id,
            secret_ref=enroll_receipt.secret_ref,
            provider_ref=enrollment_request.provider_ref,
            model_ref=enrollment_request.model_ref,
            credential_ref=enrollment_request.credential_ref,
            rotation_required_ref="rotation-ref:credential-vault:after-revoke",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            approval_ref="approval-ref:credential-vault:after-revoke-rotation",
            approval_scope_ref="approval-scope-ref:provider-runtime:required",
            budget_decision_ref=enrollment_request.budget_decision_ref,
            expected_receipt_ref="receipt-ref:credential-vault:after-revoke-rotation",
            idempotency_ref="idempotency-ref:credential-vault:after-revoke-rotation",
        )
        try:
            backend.mark_rotation_required(
                terminal_rotation,
                approval_authority=_authority_for_rotation(terminal_rotation),
            )
        except ValueError as exc:
            if "REVOKED_REF_TERMINAL" not in str(exc):
                failures.append(f"post-revoke rotation failed with wrong error: {exc}")
        else:
            failures.append("revoked secret_ref was reopened as rotation_required")
        try:
            backend.mark_rotation_required(
                rotation_request,
                approval_authority=_authority_for_rotation(rotation_request),
            )
        except ValueError as exc:
            if "REVOKED_REF_TERMINAL" not in str(exc):
                failures.append(f"post-revoke rotation replay failed with wrong error: {exc}")
        else:
            failures.append("revoked secret_ref returned a stale allowed rotation replay")

        snapshot = backend.inspect()
        payload_text = json.dumps(snapshot.model_dump(mode="json"), sort_keys=True).lower()
        ledger_text = backend.ledger_path.read_text(encoding="utf-8")
        if transient_value in payload_text or transient_value in ledger_text:
            failures.append("transient secret value leaked into snapshot or ledger")
        for record in snapshot.records:
            if record.secret_resolution_enabled or record.credential_validation_enabled:
                failures.append(f"{record.secret_ref} enables secret resolution or validation")
            if record.provider_sdk_call_enabled or record.provider_invocation_enabled:
                failures.append(f"{record.secret_ref} enables provider SDK or invocation")
            if record.raw_secret_material_persisted or record.raw_secret_material_returned:
                failures.append(f"{record.secret_ref} persisted or returned raw secret material")

        inspect_result = subprocess.run(
            [
                sys.executable,
                "scripts/inspect_credential_vault_backend.py",
                "--state-dir",
                str(state_dir),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if inspect_result.returncode != 0:
            failures.append("inspect_credential_vault_backend.py failed")
        if transient_value in inspect_result.stdout:
            failures.append("transient secret value leaked into CLI inspection")
        for forbidden in FORBIDDEN_OUTPUT:
            if forbidden in inspect_result.stdout.lower():
                failures.append(f"unsafe vault backend CLI text found: {forbidden}")

    manifest = build_api_manifest(app)
    declared = set(manifest.capabilities_declared)
    blocked = set(manifest.capabilities_blocked)
    if missing := REQUIRED_DECLARED_CAPABILITIES - declared:
        failures.append(f"manifest missing backend declarations: {sorted(missing)}")
    if missing := REQUIRED_BLOCKED_CAPABILITIES - blocked:
        failures.append(f"manifest missing backend blocked authority: {sorted(missing)}")

    doc_path = ROOT / "docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md"
    if not doc_path.exists():
        failures.append("credential vault backend v1 doc is missing")
    else:
        doc_text = doc_path.read_text(encoding="utf-8")
        for fragment in REQUIRED_DOC_FRAGMENTS:
            if fragment not in doc_text:
                failures.append(f"credential vault backend doc missing fragment: {fragment}")
        lowered_doc = doc_text.lower()
        for forbidden in FORBIDDEN_OUTPUT:
            if forbidden in lowered_doc:
                failures.append(f"unsafe credential vault backend doc text found: {forbidden}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("credential vault backend v1 verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
