from __future__ import annotations

import threading
from enum import Enum
from typing import Any, Callable

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchAdapterResult,
    AuthorityDispatchRequest,
    AuthorityDomain,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.evidence_signing.backend import (
    PortableEvidenceSigningBackendStatus,
    PortableEvidenceSigningKeyBackend,
)
from ultimate_ai_agent.core.evidence_signing.artifact_store import (
    PortableEvidenceSignedArtifactStore,
)
from ultimate_ai_agent.core.evidence_signing.constants import (
    PORTABLE_EVIDENCE_KEY_CREATE_ADAPTER_REF,
    PORTABLE_EVIDENCE_KEY_CREATE_CAPABILITY_REF,
    PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_CLEANUP_ADAPTER_REF,
    PORTABLE_EVIDENCE_KEY_CLEANUP_CAPABILITY_REF,
    PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_MARK_LOST_ADAPTER_REF,
    PORTABLE_EVIDENCE_KEY_MARK_LOST_CAPABILITY_REF,
    PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_REVOKE_ADAPTER_REF,
    PORTABLE_EVIDENCE_KEY_REVOKE_CAPABILITY_REF,
    PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_ROTATE_ADAPTER_REF,
    PORTABLE_EVIDENCE_KEY_ROTATE_CAPABILITY_REF,
    PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF,
    PORTABLE_EVIDENCE_SIGN_ADAPTER_REF,
    PORTABLE_EVIDENCE_SIGN_CAPABILITY_REF,
    PORTABLE_EVIDENCE_SIGN_TOOL_REF,
)
from ultimate_ai_agent.core.evidence_signing.lifecycle import (
    PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH,
    PortableEvidenceKeyLifecycleError,
    PortableEvidenceKeyLifecycleLedger,
)
from ultimate_ai_agent.core.evidence_signing.portable import (
    PortableEvidenceSignedArtifact,
    _decode_base64url,
    _stable_ref,
    build_portable_evidence_signing_attestation,
    build_signed_portable_evidence_artifact,
    portable_evidence_signature_preimage,
)
from ultimate_ai_agent.core.execution.portable_mission_evidence import (
    PortableMissionEvidenceBundle,
    verify_portable_mission_evidence_bundle,
)
from ultimate_ai_agent.core.tools.runtime import ToolInvocationRequest


class PortableEvidenceSigningOperation(str, Enum):
    bundle_sign = "bundle_sign"
    key_create = "key_create"
    key_rotate = "key_rotate"
    key_revoke = "key_revoke"
    key_mark_lost = "key_mark_lost"
    key_material_cleanup = "key_material_cleanup"


_OPERATION_BINDINGS = {
    PortableEvidenceSigningOperation.bundle_sign: (
        PORTABLE_EVIDENCE_SIGN_ADAPTER_REF,
        PORTABLE_EVIDENCE_SIGN_CAPABILITY_REF,
        PORTABLE_EVIDENCE_SIGN_TOOL_REF,
        AuthorityCapability.execute,
    ),
    PortableEvidenceSigningOperation.key_create: (
        PORTABLE_EVIDENCE_KEY_CREATE_ADAPTER_REF,
        PORTABLE_EVIDENCE_KEY_CREATE_CAPABILITY_REF,
        PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF,
        AuthorityCapability.mutate,
    ),
    PortableEvidenceSigningOperation.key_rotate: (
        PORTABLE_EVIDENCE_KEY_ROTATE_ADAPTER_REF,
        PORTABLE_EVIDENCE_KEY_ROTATE_CAPABILITY_REF,
        PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF,
        AuthorityCapability.mutate,
    ),
    PortableEvidenceSigningOperation.key_revoke: (
        PORTABLE_EVIDENCE_KEY_REVOKE_ADAPTER_REF,
        PORTABLE_EVIDENCE_KEY_REVOKE_CAPABILITY_REF,
        PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF,
        AuthorityCapability.mutate,
    ),
    PortableEvidenceSigningOperation.key_mark_lost: (
        PORTABLE_EVIDENCE_KEY_MARK_LOST_ADAPTER_REF,
        PORTABLE_EVIDENCE_KEY_MARK_LOST_CAPABILITY_REF,
        PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF,
        AuthorityCapability.mutate,
    ),
    PortableEvidenceSigningOperation.key_material_cleanup: (
        PORTABLE_EVIDENCE_KEY_CLEANUP_ADAPTER_REF,
        PORTABLE_EVIDENCE_KEY_CLEANUP_CAPABILITY_REF,
        PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF,
        AuthorityCapability.mutate,
    ),
}
PORTABLE_EVIDENCE_PENDING_BUNDLE_LIMIT = 8


class PortableEvidenceSigningAuthorityAdapter:
    def __init__(
        self,
        *,
        operation: PortableEvidenceSigningOperation,
        backend: PortableEvidenceSigningKeyBackend,
        lifecycle: PortableEvidenceKeyLifecycleLedger,
        lease_store: AuthorityLeaseStore,
        safe_disable_engaged: Callable[[], bool],
        artifact_store: PortableEvidenceSignedArtifactStore,
    ) -> None:
        adapter_ref, capability_ref, tool_ref, capability = _OPERATION_BINDINGS[
            operation
        ]
        self.operation = operation
        self.backend = backend
        self.lifecycle = lifecycle
        self.lease_store = lease_store
        self._safe_disable_engaged = safe_disable_engaged
        self.artifact_store = artifact_store
        self._descriptor = AuthorityDispatchAdapterDescriptor(
            adapter_ref=adapter_ref,
            domain=AuthorityDomain.evidence_signing,
            capability=capability,
            capability_ref=capability_ref,
            tool_ref=tool_ref,
            approval_required=True,
            operation_count=1,
            estimated_cost_microusd=0,
            failure_cost_microusd=0,
            idempotent_replay_supported=False,
            rollback_ref=("rollback-ref:portable-evidence-signing:recovery-required"),
            safe_disable_ref="safe-disable-ref:portable-evidence-signing:v1",
            safe_summary=(
                "Run one exact approval- and lease-governed portable evidence "
                "signing lifecycle operation."
            ),
        )
        self.binding_ref = _stable_ref(
            "adapter-binding-ref:portable-evidence-signing",
            {
                "adapter_ref": adapter_ref,
                "backend_binding_ref": backend.binding_ref,
                "capability_ref": capability_ref,
                "artifact_store_ref": artifact_store.store_ref,
                "lifecycle_store_ref": lifecycle.store_ref,
                "operation": operation.value,
                "tool_ref": tool_ref,
            },
        )
        self._pending_bundles: dict[str, PortableMissionEvidenceBundle] = {}
        self._active_request_refs: set[str] = set()
        self._lock = threading.RLock()

    @property
    def binding_resource_refs(self) -> set[str]:
        return {
            self.descriptor.adapter_ref,
            self.descriptor.capability_ref,
            self.descriptor.tool_ref,
            self.backend.binding_ref,
            self.artifact_store.store_ref,
            self.lifecycle.store_ref,
        }

    @property
    def descriptor(self) -> AuthorityDispatchAdapterDescriptor:
        return self._descriptor.model_copy(deep=True)

    def bind_bundle(
        self,
        *,
        dispatch_ref: str,
        bundle: PortableMissionEvidenceBundle,
    ) -> None:
        if self.operation != PortableEvidenceSigningOperation.bundle_sign:
            raise ValueError("PORTABLE_EVIDENCE_SIGN_ADAPTER_REQUIRED")
        verification = verify_portable_mission_evidence_bundle(bundle)
        if not verification.valid or not verification.chain_verified:
            raise ValueError("PORTABLE_EVIDENCE_UNSIGNED_BUNDLE_INVALID")
        with self._lock:
            existing = self._pending_bundles.get(dispatch_ref)
            if existing is not None and existing.bundle_ref != bundle.bundle_ref:
                raise ValueError("PORTABLE_EVIDENCE_SIGN_BUNDLE_CONFLICT")
            if (
                existing is None
                and len(self._pending_bundles) >= PORTABLE_EVIDENCE_PENDING_BUNDLE_LIMIT
            ):
                raise ValueError("PORTABLE_EVIDENCE_PENDING_BUNDLE_LIMIT_EXCEEDED")
            self._pending_bundles[dispatch_ref] = bundle.model_copy(deep=True)

    def artifact_for_dispatch(
        self, dispatch_ref: str
    ) -> PortableEvidenceSignedArtifact:
        return self.artifact_store.load(dispatch_ref=dispatch_ref)

    def release_request_state(self, dispatch_ref: str) -> None:
        if self.operation == PortableEvidenceSigningOperation.bundle_sign:
            with self._lock:
                self._pending_bundles.pop(dispatch_ref, None)
                self._active_request_refs.discard(dispatch_ref)

    def claim_request_state(self, dispatch_ref: str) -> None:
        if self.operation != PortableEvidenceSigningOperation.bundle_sign:
            return
        with self._lock:
            if dispatch_ref not in self._pending_bundles:
                raise RuntimeError("PORTABLE_EVIDENCE_SIGN_BUNDLE_UNAVAILABLE")
            self._active_request_refs.add(dispatch_ref)

    def request_state_active(self, dispatch_ref: str) -> bool:
        if self.operation != PortableEvidenceSigningOperation.bundle_sign:
            return False
        with self._lock:
            return dispatch_ref in self._active_request_refs

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        return self._validate_request(request, include_lease_binding=True)

    def _validate_request(
        self,
        request: AuthorityDispatchRequest,
        *,
        include_lease_binding: bool,
    ) -> list[str]:
        reasons: list[str] = []
        try:
            tool = ToolInvocationRequest.model_validate(request.tool_invocation_request)
        except ValueError:
            return ["reason-ref:portable-evidence-signing:tool-request-invalid"]
        if tool.invocation_kind != "portable_evidence_signing":
            reasons.append("reason-ref:portable-evidence-signing:kind-mismatch")
        if tool.metadata.get("operation") != self.operation.value:
            reasons.append("reason-ref:portable-evidence-signing:operation-mismatch")
        allowed_metadata = {
            "operation",
            "key_ref",
            "key_version_ref",
            "bundle_ref",
            "bundle_terminal_entry_hash_ref",
            "revocation_ref",
            "predecessor_key_version_ref",
            "deletion_reason",
        }
        if set(tool.metadata) - allowed_metadata:
            reasons.append("reason-ref:portable-evidence-signing:metadata-unsafe")
        key_ref = tool.metadata.get("key_ref")
        key_version_ref = tool.metadata.get("key_version_ref")
        if not isinstance(key_ref, str) or not isinstance(key_version_ref, str):
            reasons.append("reason-ref:portable-evidence-signing:key-binding-missing")
            return reasons
        if self.operation != PortableEvidenceSigningOperation.bundle_sign:
            persisted_refs = (
                request.dispatch_ref,
                key_ref,
                key_version_ref,
                tool.metadata.get("revocation_ref"),
                tool.metadata.get("predecessor_key_version_ref"),
            )
            if any(
                isinstance(ref, str)
                and len(ref) > PORTABLE_EVIDENCE_KEY_LEDGER_REF_MAX_LENGTH
                for ref in persisted_refs
            ):
                reasons.append(
                    "reason-ref:portable-evidence-signing:lifecycle-ref-too-long"
                )
        expected_resources = self.binding_resource_refs | {key_ref, key_version_ref}
        if self._safe_disable_engaged():
            reasons.append("reason-ref:portable-evidence-signing:safe-disabled")
        try:
            inspection = self.lifecycle.inspect()
        except (PortableEvidenceKeyLifecycleError, OSError, UnicodeError, ValueError):
            reasons.append(
                "reason-ref:portable-evidence-signing:lifecycle-state-invalid"
            )
            return list(dict.fromkeys(reasons))
        if self.operation == PortableEvidenceSigningOperation.key_create:
            if inspection.status != "not_configured":
                reasons.append(
                    "reason-ref:portable-evidence-signing:key-already-configured"
                )
        elif self.operation == PortableEvidenceSigningOperation.key_material_cleanup:
            try:
                pending, deletion_reason, pending_revocation_ref = (
                    self.lifecycle.pending_key_deletion()
                )
            except RuntimeError:
                reasons.append(
                    "reason-ref:portable-evidence-signing:key-delete-not-pending"
                )
            else:
                if (pending.key_ref, pending.key_version_ref) != (
                    key_ref,
                    key_version_ref,
                ):
                    reasons.append(
                        "reason-ref:portable-evidence-signing:key-binding-mismatch"
                    )
                if tool.metadata.get("deletion_reason") != deletion_reason:
                    reasons.append(
                        "reason-ref:portable-evidence-signing:delete-reason-mismatch"
                    )
                if deletion_reason == "revocation":
                    revocation_ref = tool.metadata.get("revocation_ref")
                    if revocation_ref != pending_revocation_ref:
                        reasons.append(
                            "reason-ref:portable-evidence-signing:revocation-ref-mismatch"
                        )
                    elif isinstance(revocation_ref, str):
                        expected_resources.add(revocation_ref)
        else:
            if inspection.status != "active":
                reasons.append(
                    "reason-ref:portable-evidence-signing:lifecycle-not-settled"
                )
            try:
                active = self.lifecycle.active_record()
            except RuntimeError:
                reasons.append(
                    "reason-ref:portable-evidence-signing:active-key-required"
                )
            else:
                if (active.key_ref, active.key_version_ref) != (
                    key_ref,
                    key_version_ref,
                ) and self.operation != PortableEvidenceSigningOperation.key_rotate:
                    reasons.append(
                        "reason-ref:portable-evidence-signing:key-binding-mismatch"
                    )
                if (
                    self.operation == PortableEvidenceSigningOperation.key_rotate
                    and active.key_ref != key_ref
                ):
                    reasons.append(
                        "reason-ref:portable-evidence-signing:key-ref-mismatch"
                    )
                if self.operation == PortableEvidenceSigningOperation.key_rotate:
                    if any(
                        entry.key_version_ref == key_version_ref
                        for entry in self.lifecycle.load_entries()
                    ):
                        reasons.append(
                            "reason-ref:portable-evidence-signing:key-version-reused"
                        )
                    predecessor_ref = tool.metadata.get("predecessor_key_version_ref")
                    if predecessor_ref != active.key_version_ref:
                        reasons.append(
                            "reason-ref:portable-evidence-signing:predecessor-mismatch"
                        )
                    elif isinstance(predecessor_ref, str):
                        expected_resources.add(predecessor_ref)
                    if key_version_ref == active.key_version_ref:
                        reasons.append(
                            "reason-ref:portable-evidence-signing:new-key-version-required"
                        )
        if self.operation == PortableEvidenceSigningOperation.bundle_sign:
            bundle_ref = tool.metadata.get("bundle_ref")
            terminal_ref = tool.metadata.get("bundle_terminal_entry_hash_ref")
            if not isinstance(bundle_ref, str) or not isinstance(terminal_ref, str):
                reasons.append(
                    "reason-ref:portable-evidence-signing:bundle-binding-missing"
                )
            else:
                expected_resources.update({bundle_ref, terminal_ref})
                with self._lock:
                    bundle = self._pending_bundles.get(request.dispatch_ref)
                if (
                    bundle is None
                    or bundle.bundle_ref != bundle_ref
                    or bundle.terminal_entry_hash_ref != terminal_ref
                ):
                    reasons.append(
                        "reason-ref:portable-evidence-signing:bundle-unavailable"
                    )
        elif self.operation == PortableEvidenceSigningOperation.key_revoke:
            revocation_ref = tool.metadata.get("revocation_ref")
            if not isinstance(revocation_ref, str):
                reasons.append(
                    "reason-ref:portable-evidence-signing:revocation-ref-required"
                )
            else:
                expected_resources.add(revocation_ref)
        if set(request.action_request.resource_refs) != expected_resources:
            reasons.append(
                "reason-ref:portable-evidence-signing:resource-scope-mismatch"
            )
        if include_lease_binding:
            lease = next(
                (
                    item
                    for item in self.lease_store.list_leases(active_only=False)
                    if item.lease_ref == request.lease_ref
                ),
                None,
            )
            resource_constraint = (
                next(
                    (
                        constraint
                        for constraint in lease.authority_constraints
                        if constraint.kind
                        == AuthorityConstraintKind.resource_refs.value
                    ),
                    None,
                )
                if lease is not None
                else None
            )
            if (
                lease is None
                or resource_constraint is None
                or set(resource_constraint.allowed_refs) != expected_resources
            ):
                reasons.append(
                    "reason-ref:portable-evidence-signing:exact-lease-required"
                )
        return list(dict.fromkeys(reasons))

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        try:
            # Direct adapter callers still fail closed on the exact lease. The
            # authority read completes before taking the lifecycle writer lock,
            # preserving the global authority->lifecycle lock order.
            reasons = self.validate_request(request)
            if reasons:
                raise RuntimeError(
                    "PORTABLE_EVIDENCE_SIGNING_PRESTART_STATE_CHANGED"
                )
            with self.lifecycle.operation_lock():
                # Authority and lease truth were committed at the dispatcher's
                # durable start boundary. Avoid reversing the global
                # authority->lifecycle lock order after start; this recheck is
                # limited to immutable request and lifecycle/runtime bindings.
                reasons = self._validate_request(
                    request,
                    include_lease_binding=False,
                )
                if not reasons:
                    reasons = self._locked_runtime_prestart_reason_refs(request)
                if reasons:
                    raise RuntimeError(
                        "PORTABLE_EVIDENCE_SIGNING_PRESTART_STATE_CHANGED"
                    )
                return self._invoke_locked(request)
        finally:
            self.release_request_state(request.dispatch_ref)

    def runtime_prestart_reason_refs(
        self,
        request: AuthorityDispatchRequest,
    ) -> list[str]:
        """Probe governed runtime readiness before durable execution start."""
        # Complete the authority read before taking the lifecycle writer lock.
        # Direct hook callers therefore preserve the same global
        # authority->lifecycle order as dispatcher-owned calls and invoke().
        reasons = self.validate_request(request)
        if reasons:
            return reasons
        with self.lifecycle.operation_lock():
            reasons = self._validate_request(
                request,
                include_lease_binding=False,
            )
            if not reasons:
                reasons = self._locked_runtime_prestart_reason_refs(request)
            return list(dict.fromkeys(reasons))

    def _locked_runtime_prestart_reason_refs(
        self,
        request: AuthorityDispatchRequest,
    ) -> list[str]:
        if self._safe_disable_engaged():
            return ["reason-ref:portable-evidence-signing:safe-disabled"]
        try:
            readiness = self.backend.readiness()
        except (OSError, RuntimeError, ValueError):
            return ["reason-ref:portable-evidence-signing:backend-readiness-invalid"]
        if readiness.status != PortableEvidenceSigningBackendStatus.ready.value:
            return list(readiness.reason_refs) or [
                "reason-ref:portable-evidence-signing:backend-not-ready"
            ]
        if self.operation in {
            PortableEvidenceSigningOperation.key_create,
            PortableEvidenceSigningOperation.key_rotate,
            PortableEvidenceSigningOperation.key_revoke,
            PortableEvidenceSigningOperation.key_mark_lost,
            PortableEvidenceSigningOperation.key_material_cleanup,
        }:
            if self.operation == PortableEvidenceSigningOperation.key_create:
                required_entries = 3
            elif self.operation == PortableEvidenceSigningOperation.key_rotate:
                required_entries = 4
            elif self.operation in {
                PortableEvidenceSigningOperation.key_revoke,
                PortableEvidenceSigningOperation.key_mark_lost,
            }:
                required_entries = 2
            else:
                try:
                    _pending, deletion_reason, _revocation_ref = (
                        self.lifecycle.pending_key_deletion()
                    )
                except (PortableEvidenceKeyLifecycleError, RuntimeError, ValueError):
                    return [
                        "reason-ref:portable-evidence-signing:key-delete-not-pending"
                    ]
                required_entries = 3 if deletion_reason == "rotation" else 1
            try:
                self.lifecycle._require_entry_capacity_locked(
                    required_entries=required_entries
                )
            except (PortableEvidenceKeyLifecycleError, OSError, ValueError):
                return [
                    "reason-ref:portable-evidence-signing:ledger-capacity-exhausted"
                ]
        if self.operation in {
            PortableEvidenceSigningOperation.key_create,
            PortableEvidenceSigningOperation.key_mark_lost,
            PortableEvidenceSigningOperation.key_revoke,
            PortableEvidenceSigningOperation.key_material_cleanup,
        }:
            return []
        try:
            active = self.lifecycle.active_record()
            probed = self.backend.probe_key(
                key_ref=active.key_ref,
                key_version_ref=active.key_version_ref,
                request_ref=request.dispatch_ref,
            )
        except (OSError, RuntimeError, ValueError):
            return ["reason-ref:portable-evidence-signing:key-inaccessible"]
        if probed.public_key_fingerprint_ref != active.public_key_fingerprint_ref:
            return ["reason-ref:portable-evidence-signing:key-fingerprint-mismatch"]
        return []

    def _invoke_locked(
        self,
        request: AuthorityDispatchRequest,
    ) -> AuthorityDispatchAdapterResult:
        tool = ToolInvocationRequest.model_validate(request.tool_invocation_request)
        key_ref = str(tool.metadata["key_ref"])
        key_version_ref = str(tool.metadata["key_version_ref"])
        request_fingerprint_ref = _stable_ref(
            "request-fingerprint-ref:portable-evidence-signing",
            request.model_dump(mode="json"),
        )
        receipt_ref = _stable_ref(
            "receipt-ref:portable-evidence-signing",
            {"dispatch_ref": request.dispatch_ref, "operation": self.operation.value},
        )
        evidence_refs = [receipt_ref, request_fingerprint_ref]
        output_refs: list[str] = []
        safe_output: dict[str, Any] = {
            "operation": self.operation.value,
            "key_ref": key_ref,
            "key_version_ref": key_version_ref,
            "receipt_ref": receipt_ref,
        }
        if self.operation == PortableEvidenceSigningOperation.key_create:
            created = self.backend.create_key(
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                request_ref=request.dispatch_ref,
            )
            lifecycle = self.lifecycle.append_created(
                request_ref=request.dispatch_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                public_key_base64url=created.public_key_base64url,
                public_key_fingerprint_ref=created.public_key_fingerprint_ref,
            )
            evidence_refs.extend([created.helper_receipt_ref, lifecycle.entry_hash_ref])
            output_refs.append(created.public_key_fingerprint_ref)
            safe_output["public_key_fingerprint_ref"] = (
                created.public_key_fingerprint_ref
            )
        elif self.operation == PortableEvidenceSigningOperation.key_rotate:
            predecessor = self.lifecycle.active_record()
            created = self.backend.create_key(
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                request_ref=request.dispatch_ref,
            )
            lifecycle = self.lifecycle.append_rotated(
                request_ref=request.dispatch_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                public_key_base64url=created.public_key_base64url,
                public_key_fingerprint_ref=created.public_key_fingerprint_ref,
            )
            evidence_refs.extend([created.helper_receipt_ref, lifecycle.entry_hash_ref])
            output_refs.append(created.public_key_fingerprint_ref)
            safe_output["public_key_fingerprint_ref"] = (
                created.public_key_fingerprint_ref
            )
            deleted = self.backend.delete_key(
                key_ref=predecessor.key_ref,
                key_version_ref=predecessor.key_version_ref,
                request_ref=request.dispatch_ref,
            )
            settlement = self.lifecycle.append_retired_key_delete_completed(
                request_ref=_stable_ref(
                    "request-ref:portable-evidence:rotation-delete-settlement",
                    request.dispatch_ref,
                ),
                request_fingerprint_ref=_stable_ref(
                    "request-fingerprint-ref:portable-evidence:rotation-delete-settlement",
                    request_fingerprint_ref,
                ),
                receipt_ref=receipt_ref,
                retired_key_version_ref=predecessor.key_version_ref,
            )
            evidence_refs.extend(
                [deleted.helper_receipt_ref, settlement.entry_hash_ref]
            )
            safe_output["retired_key_material_deleted_or_absent"] = True
        elif self.operation == PortableEvidenceSigningOperation.key_revoke:
            revocation_ref = str(tool.metadata["revocation_ref"])
            lifecycle = self.lifecycle.append_revoked(
                request_ref=request.dispatch_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
                revocation_ref=revocation_ref,
            )
            deleted = self.backend.delete_key(
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                request_ref=request.dispatch_ref,
            )
            settlement = self.lifecycle.append_revocation_delete_completed(
                request_ref=_stable_ref(
                    "request-ref:portable-evidence:revocation-delete-settlement",
                    request.dispatch_ref,
                ),
                request_fingerprint_ref=_stable_ref(
                    "request-fingerprint-ref:portable-evidence:revocation-delete-settlement",
                    request_fingerprint_ref,
                ),
                receipt_ref=receipt_ref,
                revocation_ref=revocation_ref,
            )
            evidence_refs.extend(
                [
                    lifecycle.entry_hash_ref,
                    deleted.helper_receipt_ref,
                    settlement.entry_hash_ref,
                ]
            )
            output_refs.append(revocation_ref)
            safe_output["revocation_ref"] = revocation_ref
            safe_output["key_material_deleted_or_absent"] = True
        elif self.operation == PortableEvidenceSigningOperation.key_mark_lost:
            lifecycle = self.lifecycle.append_marked_lost(
                request_ref=request.dispatch_ref,
                request_fingerprint_ref=request_fingerprint_ref,
                receipt_ref=receipt_ref,
            )
            deleted = self.backend.delete_key(
                key_ref=key_ref,
                key_version_ref=key_version_ref,
                request_ref=request.dispatch_ref,
            )
            settlement = self.lifecycle.append_lost_key_delete_completed(
                request_ref=_stable_ref(
                    "request-ref:portable-evidence:lost-delete-settlement",
                    request.dispatch_ref,
                ),
                request_fingerprint_ref=_stable_ref(
                    "request-fingerprint-ref:portable-evidence:lost-delete-settlement",
                    request_fingerprint_ref,
                ),
                receipt_ref=receipt_ref,
            )
            evidence_refs.extend(
                [
                    lifecycle.entry_hash_ref,
                    deleted.helper_receipt_ref,
                    settlement.entry_hash_ref,
                ]
            )
            safe_output["signing_blocked"] = True
            safe_output["key_material_deleted_or_absent"] = True
        elif self.operation == PortableEvidenceSigningOperation.key_material_cleanup:
            pending, deletion_reason, revocation_ref = (
                self.lifecycle.pending_key_deletion()
            )
            deleted = self.backend.delete_key(
                key_ref=pending.key_ref,
                key_version_ref=pending.key_version_ref,
                request_ref=request.dispatch_ref,
            )
            if deletion_reason == "rotation":
                settlement = self.lifecycle.append_retired_key_delete_completed(
                    request_ref=request.dispatch_ref,
                    request_fingerprint_ref=request_fingerprint_ref,
                    receipt_ref=receipt_ref,
                    retired_key_version_ref=pending.key_version_ref,
                )
            elif deletion_reason == "revocation":
                if revocation_ref is None:
                    raise RuntimeError("PORTABLE_EVIDENCE_REVOCATION_REF_REQUIRED")
                settlement = self.lifecycle.append_revocation_delete_completed(
                    request_ref=request.dispatch_ref,
                    request_fingerprint_ref=request_fingerprint_ref,
                    receipt_ref=receipt_ref,
                    revocation_ref=revocation_ref,
                )
                output_refs.append(revocation_ref)
                safe_output["revocation_ref"] = revocation_ref
            else:
                settlement = self.lifecycle.append_lost_key_delete_completed(
                    request_ref=request.dispatch_ref,
                    request_fingerprint_ref=request_fingerprint_ref,
                    receipt_ref=receipt_ref,
                )
            evidence_refs.extend(
                [deleted.helper_receipt_ref, settlement.entry_hash_ref]
            )
            safe_output["deletion_reason"] = deletion_reason
            safe_output["key_material_deleted_or_absent"] = True
        else:
            with self._lock:
                bundle = self._pending_bundles[request.dispatch_ref]
            key = self.lifecycle.active_record()
            attestation = build_portable_evidence_signing_attestation(
                bundle,
                key_record=key,
                signing_request_ref=request.dispatch_ref,
                signing_receipt_ref=receipt_ref,
                key_management_ref=self.backend.binding_ref,
                managed_key_backend_attested=True,
            )
            signed = self.backend.sign(
                key_ref=key.key_ref,
                key_version_ref=key.key_version_ref,
                request_ref=request.dispatch_ref,
                payload=portable_evidence_signature_preimage(attestation),
            )
            artifact = build_signed_portable_evidence_artifact(
                bundle,
                key_record=key,
                signing_request_ref=request.dispatch_ref,
                signing_receipt_ref=receipt_ref,
                signature=_decode_base64url(
                    signed.signature_base64url,
                    expected_bytes=64,
                ),
                key_management_ref=self.backend.binding_ref,
                managed_key_backend_attested=True,
            )
            self.artifact_store.save(
                dispatch_ref=request.dispatch_ref,
                artifact=artifact,
            )
            evidence_refs.extend([signed.helper_receipt_ref, artifact.signature_ref])
            output_refs.extend([artifact.artifact_ref, artifact.signature_ref])
            safe_output.update(
                {
                    "artifact_ref": artifact.artifact_ref,
                    "bundle_ref": artifact.unsigned_bundle.bundle_ref,
                    "signature_ref": artifact.signature_ref,
                    "managed_key_backend_attested": True,
                }
            )
        return AuthorityDispatchAdapterResult(
            execution_ref=_stable_ref(
                "authority-dispatch-execution-ref",
                {
                    "dispatch_ref": request.dispatch_ref,
                    "idempotency_ref": request.idempotency_ref,
                    "adapter_ref": request.adapter_ref,
                },
            ),
            succeeded=True,
            failure_category=None,
            actual_operation_count=1,
            actual_cost_microusd=0,
            actual_cost_ref=_stable_ref(
                "actual-cost-ref:portable-evidence-signing", request.dispatch_ref
            ),
            evidence_refs=evidence_refs,
            output_refs=output_refs,
            safe_output=safe_output,
            safe_summary="Completed one exact governed portable evidence signing operation.",
        )


def portable_evidence_signing_adapters(
    *,
    backend: PortableEvidenceSigningKeyBackend,
    lifecycle: PortableEvidenceKeyLifecycleLedger,
    lease_store: AuthorityLeaseStore,
    safe_disable_engaged: Callable[[], bool],
    artifact_store: PortableEvidenceSignedArtifactStore,
) -> tuple[PortableEvidenceSigningAuthorityAdapter, ...]:
    return tuple(
        PortableEvidenceSigningAuthorityAdapter(
            operation=operation,
            backend=backend,
            lifecycle=lifecycle,
            lease_store=lease_store,
            safe_disable_engaged=safe_disable_engaged,
            artifact_store=artifact_store,
        )
        for operation in PortableEvidenceSigningOperation
    )
