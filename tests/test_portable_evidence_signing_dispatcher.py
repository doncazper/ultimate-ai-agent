from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.test_authority_dispatcher import _approval
from tests.test_portable_mission_evidence import _bundle
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDispatchRequest,
    AuthorityDispatchStatus,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate
from ultimate_ai_agent.core.evidence_signing.backend import (
    PortableEvidenceSigningBackendDeletion,
    PortableEvidenceSigningBackendPublicKey,
    PortableEvidenceSigningBackendReadiness,
    PortableEvidenceSigningBackendSignature,
    PortableEvidenceSigningBackendStatus,
)
from ultimate_ai_agent.core.evidence_signing.artifact_store import (
    PortableEvidenceSignedArtifactStoreError,
    PortableEvidenceSignedArtifactStore,
)
from ultimate_ai_agent.core.evidence_signing.dispatcher_adapter import (
    PortableEvidenceSigningAuthorityAdapter,
    PortableEvidenceSigningOperation,
)
from ultimate_ai_agent.core.evidence_signing.lifecycle import (
    PortableEvidenceKeyLifecycleLedger,
)
from ultimate_ai_agent.core.evidence_signing.portable import (
    _stable_ref,
    ed25519_public_key_fingerprint_ref,
    verify_signed_portable_evidence_artifact,
)
from ultimate_ai_agent.core.tools.runtime import (
    ToolInvocationKind,
    ToolInvocationRequest,
)


class _FakeManagedBackend:
    adapter_ref = "adapter-ref:portable-evidence-signing:test-managed"
    binding_ref = "backend-binding-ref:portable-evidence-signing:test-managed"

    def __init__(self) -> None:
        self.keys: dict[str, Ed25519PrivateKey] = {}
        self.create_count = 0
        self.sign_count = 0
        self.delete_count = 0
        self.fail_delete = False
        self.readiness_count = 0
        self.probe_count = 0

    def readiness(self) -> PortableEvidenceSigningBackendReadiness:
        self.readiness_count += 1
        return PortableEvidenceSigningBackendReadiness(
            adapter_ref=self.adapter_ref,
            status=PortableEvidenceSigningBackendStatus.ready,
            helper_version_ref="helper-version-ref:portable-evidence:test",
            helper_fingerprint_ref=("helper-fingerprint-ref:sha256:" + "a" * 64),
            reason_refs=("reason-ref:portable-evidence-signing:test-ready",),
        )

    def create_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        created = key_version_ref not in self.keys
        self.keys.setdefault(key_version_ref, Ed25519PrivateKey.generate())
        self.create_count += 1
        raw = self.keys[key_version_ref].public_key().public_bytes_raw()
        return PortableEvidenceSigningBackendPublicKey(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            public_key_base64url=base64.urlsafe_b64encode(raw)
            .rstrip(b"=")
            .decode("ascii"),
            public_key_fingerprint_ref=ed25519_public_key_fingerprint_ref(raw),
            helper_receipt_ref=_stable_ref(
                "helper-receipt-ref:test-create", request_ref
            ),
            created=created,
        )

    def sign(
        self,
        *,
        key_ref: str,
        key_version_ref: str,
        request_ref: str,
        payload: bytes,
    ) -> PortableEvidenceSigningBackendSignature:
        self.sign_count += 1
        signature = self.keys[key_version_ref].sign(payload)
        encoded = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        return PortableEvidenceSigningBackendSignature(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            request_ref=request_ref,
            signature_base64url=encoded,
            signature_ref=_stable_ref(
                "portable-evidence-signature-ref", signature.hex()
            ),
            helper_receipt_ref=_stable_ref("helper-receipt-ref:test-sign", request_ref),
        )

    def probe_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        self.probe_count += 1
        raw = self.keys[key_version_ref].public_key().public_bytes_raw()
        return PortableEvidenceSigningBackendPublicKey(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            public_key_base64url=base64.urlsafe_b64encode(raw)
            .rstrip(b"=")
            .decode("ascii"),
            public_key_fingerprint_ref=ed25519_public_key_fingerprint_ref(raw),
            helper_receipt_ref=_stable_ref(
                "helper-receipt-ref:test-probe", request_ref
            ),
            created=False,
        )

    def delete_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendDeletion:
        self.delete_count += 1
        if self.fail_delete:
            raise RuntimeError("PORTABLE_EVIDENCE_TEST_DELETE_FAILED")
        self.keys.pop(key_version_ref, None)
        return PortableEvidenceSigningBackendDeletion(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            helper_receipt_ref=_stable_ref(
                "helper-receipt-ref:test-delete", request_ref
            ),
        )


def _lease(
    store: AuthorityLeaseStore,
    *,
    capability: AuthorityCapability,
    resources: set[str],
    suffix: str,
):  # type: ignore[no-untyped-def]
    lease, receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={AuthorityDomain.evidence_signing: [capability]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=f"authority-constraint-ref:portable-evidence:{suffix}:resources",
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=sorted(resources),
                    safe_summary="Limit signing authority to the exact operation resources.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"authority-constraint-ref:portable-evidence:{suffix}:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Allow one portable evidence signing operation.",
                ),
                AuthorityConstraint(
                    constraint_ref=f"authority-constraint-ref:portable-evidence:{suffix}:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Require the local zero-cost signing lane.",
                ),
            ],
            decision_reason_ref="reason-ref:portable-evidence:test-lease",
            safe_summary="Issue one exact portable evidence signing test lease.",
        ),
        idempotency_ref=f"idempotency-ref:portable-evidence:lease:{suffix}",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return lease


def _request(
    *,
    adapter: PortableEvidenceSigningAuthorityAdapter,
    lease_ref: str,
    resources: set[str],
    metadata: dict[str, Any],
    suffix: str,
) -> AuthorityDispatchRequest:
    dispatch_ref = f"authority-dispatch-ref:portable-evidence:{suffix}"
    run_ref = f"run-ref:portable-evidence:{suffix}"
    idempotency_ref = f"idempotency-ref:portable-evidence:{suffix}"
    estimate = CostEstimate(
        estimate_id=f"cost-estimate:portable-evidence:{suffix}",
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
    )
    budgets = [
        CostBudget(
            budget_id=f"cost-budget:portable-evidence:{suffix}",
            scope=BudgetScope.run,
            scope_id=run_ref,
            max_cost_usd=1,
            max_total_tokens=1,
        )
    ]
    action = AuthorityActionRequest(
        action_ref=f"authority-action-ref:portable-evidence:{suffix}",
        domain=AuthorityDomain.evidence_signing,
        capability=adapter.descriptor.capability,
        capability_ref=adapter.descriptor.capability_ref,
        adapter_ref=adapter.descriptor.adapter_ref,
        resource_refs=sorted(resources),
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=1,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
        ],
        safe_summary="Run one exact governed portable evidence signing operation.",
    )
    tool = ToolInvocationRequest(
        invocation_id=dispatch_ref,
        tool_ref=adapter.descriptor.tool_ref,
        tool_name="UAA portable evidence signing operation",
        invocation_kind=ToolInvocationKind.portable_evidence_signing,
        replay_key=idempotency_ref,
        safe_summary="Run one exact portable evidence signing operation.",
        input_refs=sorted(resources),
        metadata=metadata,
    )
    return AuthorityDispatchRequest(
        dispatch_ref=dispatch_ref,
        run_ref=run_ref,
        idempotency_ref=idempotency_ref,
        lease_ref=lease_ref,
        adapter_ref=adapter.descriptor.adapter_ref,
        action_request=action,
        tool_invocation_request=tool.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=estimate,
        cost_budgets=budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(estimate),
        cost_governor_decision_ref=(
            build_authority_dispatch_cost_governor_decision_ref(estimate, budgets)
        ),
        cost_governor_allowed=True,
        safe_summary="Dispatch one exact portable evidence signing operation.",
    )


def _adapter_setup(
    tmp_path: Path,
    operation: PortableEvidenceSigningOperation,
    backend: _FakeManagedBackend | None = None,
):  # type: ignore[no-untyped-def]
    state_dir = tmp_path / "authority"
    store = AuthorityLeaseStore(state_dir)
    lifecycle = PortableEvidenceKeyLifecycleLedger(state_dir / "signing")
    artifact_store = PortableEvidenceSignedArtifactStore(state_dir / "signing")
    managed = backend or _FakeManagedBackend()
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=operation,
        backend=managed,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=artifact_store,
    )
    return state_dir, store, lifecycle, managed, adapter


def _approved_dispatch(
    *,
    state_dir: Path,
    store: AuthorityLeaseStore,
    adapter: PortableEvidenceSigningAuthorityAdapter,
    resources: set[str],
    metadata: dict[str, Any],
    suffix: str,
    approval: LocalApprovalAuthority | None = None,
):  # type: ignore[no-untyped-def]
    approval_authority = approval or LocalApprovalAuthority()
    lease = _lease(
        store,
        capability=AuthorityCapability(adapter.descriptor.capability),
        resources=resources,
        suffix=suffix,
    )
    request = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata=metadata,
        suffix=suffix,
    )
    request = request.model_copy(
        update={"approval_validation_request": _approval(approval_authority, request)}
    )
    result = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approval_authority,
    ).dispatch(request)
    return result, request


def _create_active_key(
    *,
    state_dir: Path,
    store: AuthorityLeaseStore,
    lifecycle: PortableEvidenceKeyLifecycleLedger,
    backend: _FakeManagedBackend,
    suffix: str,
) -> tuple[str, str]:
    adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.key_create,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    key_ref = f"signing-key-ref:portable-evidence:{suffix}"
    key_version_ref = f"signing-key-version-ref:portable-evidence:{suffix}:1"
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    result, _request_value = _approved_dispatch(
        state_dir=state_dir,
        store=store,
        adapter=adapter,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix=f"{suffix}-create",
    )
    assert result.receipt.status == "succeeded"
    return key_ref, key_version_ref


def test_key_create_requires_exact_approval_and_terminal_replay_is_exactly_once(
    tmp_path: Path,
) -> None:
    state_dir, store, lifecycle, backend, adapter = _adapter_setup(
        tmp_path, PortableEvidenceSigningOperation.key_create
    )
    key_ref = "signing-key-ref:portable-evidence:operator"
    key_version_ref = "signing-key-version-ref:portable-evidence:operator:1"
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    lease = _lease(
        store,
        capability=AuthorityCapability.mutate,
        resources=resources,
        suffix="create",
    )
    pending = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="create",
    )
    approval = LocalApprovalAuthority()
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approval,
    )

    assert dispatcher.dispatch(pending).receipt.status == "denied"
    assert backend.create_count == 0
    assert backend.readiness_count == 0
    assert backend.probe_count == 0

    approved_pending = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="create-approved",
    )
    validation = _approval(approval, approved_pending)
    approved = approved_pending.model_copy(
        update={"approval_validation_request": validation}
    )
    result = dispatcher.dispatch(approved)
    replay = dispatcher.dispatch(approved)

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert replay.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert lifecycle.inspect().status == "active"
    assert backend.create_count == 1
    assert backend.readiness_count == 1


def test_managed_bundle_signing_verifies_offline_and_cannot_use_broad_lease(
    tmp_path: Path,
) -> None:
    backend = _FakeManagedBackend()
    state_dir, store, lifecycle, _backend, create_adapter = _adapter_setup(
        tmp_path,
        PortableEvidenceSigningOperation.key_create,
        backend,
    )
    key_ref = "signing-key-ref:portable-evidence:operator"
    key_version_ref = "signing-key-version-ref:portable-evidence:operator:1"
    create_resources = create_adapter.binding_resource_refs | {
        key_ref,
        key_version_ref,
    }
    create_lease = _lease(
        store,
        capability=AuthorityCapability.mutate,
        resources=create_resources,
        suffix="sign-create",
    )
    approval = LocalApprovalAuthority()
    create_request = _request(
        adapter=create_adapter,
        lease_ref=create_lease.lease_ref,
        resources=create_resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="sign-create",
    )
    create_request = create_request.model_copy(
        update={"approval_validation_request": _approval(approval, create_request)}
    )
    AuthorityDispatcher(
        state_dir,
        adapters=[create_adapter],
        lease_store=store,
        approval_authority=approval,
    ).dispatch(create_request)

    sign_adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.bundle_sign,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    bundle = _bundle(tmp_path / "bundle")
    sign_resources = sign_adapter.binding_resource_refs | {
        key_ref,
        key_version_ref,
        bundle.bundle_ref,
        bundle.terminal_entry_hash_ref,
    }
    sign_lease = _lease(
        store,
        capability=AuthorityCapability.execute,
        resources=sign_resources,
        suffix="sign",
    )
    sign_request = _request(
        adapter=sign_adapter,
        lease_ref=sign_lease.lease_ref,
        resources=sign_resources,
        metadata={
            "operation": "bundle_sign",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "bundle_ref": bundle.bundle_ref,
            "bundle_terminal_entry_hash_ref": bundle.terminal_entry_hash_ref,
        },
        suffix="sign",
    )
    sign_adapter.bind_bundle(dispatch_ref=sign_request.dispatch_ref, bundle=bundle)
    sign_request = sign_request.model_copy(
        update={"approval_validation_request": _approval(approval, sign_request)}
    )
    result = AuthorityDispatcher(
        state_dir,
        adapters=[sign_adapter],
        lease_store=store,
        approval_authority=approval,
    ).dispatch(sign_request)
    artifact = sign_adapter.artifact_for_dispatch(sign_request.dispatch_ref)
    restarted_adapter = PortableEvidenceSigningAuthorityAdapter(
        operation=PortableEvidenceSigningOperation.bundle_sign,
        backend=backend,
        lifecycle=lifecycle,
        lease_store=store,
        safe_disable_engaged=lambda: False,
        artifact_store=PortableEvidenceSignedArtifactStore(state_dir / "signing"),
    )
    assert (
        restarted_adapter.artifact_for_dispatch(sign_request.dispatch_ref) == artifact
    )
    trust = lifecycle.public_key_bundle(
        issuer_ref="issuer-ref:portable-evidence:local-operator"
    )
    verification = verify_signed_portable_evidence_artifact(
        artifact,
        public_key_bundle=trust,
        expected_public_key_bundle_ref=trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=(
            lifecycle.active_record().public_key_fingerprint_ref
        ),
    )

    assert result.receipt.status == "succeeded"
    assert artifact.managed_key_backend_attested is True
    assert verification.valid is True
    assert backend.sign_count == 1

    artifact_path = sign_adapter.artifact_store._path(sign_request.dispatch_ref)
    pending = artifact_path.with_name(f".{artifact_path.name}.pending")
    os.link(artifact_path, pending)
    assert sign_adapter.artifact_for_dispatch(sign_request.dispatch_ref) == artifact
    assert pending.exists() is False

    hardlink = artifact_path.with_name("hardlink.json")
    os.link(artifact_path, hardlink)
    with pytest.raises(
        PortableEvidenceSignedArtifactStoreError,
        match="PORTABLE_EVIDENCE_SIGNED_ARTIFACT_FILE_INVALID",
    ):
        sign_adapter.artifact_for_dispatch(sign_request.dispatch_ref)
    hardlink.unlink()


def test_broad_domain_lease_without_exact_resources_denies_before_keychain(
    tmp_path: Path,
) -> None:
    state_dir, store, _lifecycle, backend, adapter = _adapter_setup(
        tmp_path,
        PortableEvidenceSigningOperation.key_create,
    )
    key_ref = "signing-key-ref:portable-evidence:broad-denied"
    key_version_ref = "signing-key-version-ref:portable-evidence:broad-denied:1"
    resources = adapter.binding_resource_refs | {key_ref, key_version_ref}
    lease, _receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={
                AuthorityDomain.evidence_signing: [AuthorityCapability.mutate]
            },
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref="authority-constraint-ref:portable-evidence:broad:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Bound one broad-domain denial test operation.",
                ),
                AuthorityConstraint(
                    constraint_ref="authority-constraint-ref:portable-evidence:broad:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Bound the zero-cost broad-domain denial test.",
                ),
            ],
            decision_reason_ref="reason-ref:portable-evidence:broad-lease-test",
            safe_summary="Issue a deliberately non-resource-scoped test lease.",
        ),
        idempotency_ref="idempotency-ref:portable-evidence:broad-lease-test",
    )
    assert lease is not None
    approval = LocalApprovalAuthority()
    request = _request(
        adapter=adapter,
        lease_ref=lease.lease_ref,
        resources=resources,
        metadata={
            "operation": "key_create",
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
        },
        suffix="broad-denied",
    )
    request = request.model_copy(
        update={"approval_validation_request": _approval(approval, request)}
    )

    result = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approval,
    ).dispatch(request)

    assert result.receipt.status == "denied"
    assert (
        "reason-ref:portable-evidence-signing:exact-lease-required"
        in result.receipt.reason_refs
    )
    assert backend.create_count == 0
