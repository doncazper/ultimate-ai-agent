"""Content-free portable evidence derived from verified mission completions.

The bundle proves local SHA-256 chain integrity only.  It is neither signed nor
an authority grant, and it never contains source payloads.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator

from ultimate_ai_agent.core.authority.contracts import AuthorityLease
from ultimate_ai_agent.core.authority.dispatch_contracts import AuthorityDispatchReceipt
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_receipt_entry_hash,
)
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionManifest,
    PortableMissionEvidenceInspectionSummary,
    authority_lease_issuance_scope_fingerprint_ref,
    verify_mission_completion,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


PORTABLE_MISSION_EVIDENCE_VERIFIER_REF = (
    "verifier-ref:portable-mission-evidence:sha256-chain:v1"
)
PORTABLE_MISSION_EVIDENCE_MAX_ENVELOPES = 1_000
PORTABLE_MISSION_EVIDENCE_MAX_BYTES = 4 * 1024 * 1024


class _PortableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class PortableMissionEvidenceEnvelope(_PortableModel):
    schema_version: Literal["uaa-portable-mission-evidence-envelope.v1"] = (
        "uaa-portable-mission-evidence-envelope.v1"
    )
    sequence: StrictInt = Field(..., ge=1, le=PORTABLE_MISSION_EVIDENCE_MAX_ENVELOPES)
    completion_ref: str
    plan_ref: str
    plan_fingerprint_ref: str
    mission_ref: str
    run_ref: str
    step_ref: str
    dispatch_ref: str
    dispatch_receipt_ref: str
    dispatch_entry_hash_ref: str
    lease_ref: str
    lease_scope_fingerprint_ref: str
    approval_ref: str | None = None
    approval_validation_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    authority_decision_ref: str
    authority_policy_receipt_ref: str
    budget_reservation_ref: str
    budget_settlement_receipt_ref: str
    capability_ref: str
    adapter_ref: str
    provider_ref: str
    target_binding_ref: str
    request_fingerprint_ref: str
    terminal_outcome: Literal["succeeded"] = "succeeded"
    predecessor_entry_hash_ref: str | None = None
    entry_hash_ref: str
    verifier_version_ref: str = PORTABLE_MISSION_EVIDENCE_VERIFIER_REF
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"
    execution_evidence_grants_authority: Literal[False] = False
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_envelope(self) -> "PortableMissionEvidenceEnvelope":
        _validate_refs(self.model_dump(mode="python"))
        if bool(self.approval_ref) != bool(self.approval_validation_ref):
            raise ValueError("PORTABLE_EVIDENCE_APPROVAL_BINDING_INCOMPLETE")
        if bool(self.approval_ref) != bool(self.approval_scope_fingerprint_ref):
            raise ValueError("PORTABLE_EVIDENCE_APPROVAL_SCOPE_INCOMPLETE")
        return self


class PortableMissionEvidenceBundle(_PortableModel):
    schema_version: Literal["uaa-portable-mission-evidence-bundle.v1"] = (
        "uaa-portable-mission-evidence-bundle.v1"
    )
    bundle_ref: str
    verifier_version_ref: str = PORTABLE_MISSION_EVIDENCE_VERIFIER_REF
    envelope_count: StrictInt = Field(..., ge=1, le=PORTABLE_MISSION_EVIDENCE_MAX_ENVELOPES)
    completion_count: StrictInt = Field(..., ge=1, le=PORTABLE_MISSION_EVIDENCE_MAX_ENVELOPES)
    genesis_entry_hash_ref: str
    terminal_entry_hash_ref: str
    envelopes: tuple[PortableMissionEvidenceEnvelope, ...] = Field(
        ..., min_length=1, max_length=PORTABLE_MISSION_EVIDENCE_MAX_ENVELOPES
    )
    integrity_posture: Literal["local_sha256_hash_chain"] = "local_sha256_hash_chain"
    signature_present: Literal[False] = False
    signing_status: Literal["blocked_signing_lifecycle_not_implemented"] = (
        "blocked_signing_lifecycle_not_implemented"
    )
    cryptographic_authenticity_verified: Literal[False] = False
    external_anchor_verified: Literal[False] = False
    source_ledgers_verified: Literal[False] = False
    source_receipts_bound: Literal[True] = True
    execution_evidence_grants_authority: Literal[False] = False
    safe_refs_only: Literal[True] = True
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self) -> "PortableMissionEvidenceBundle":
        _validate_refs(self.model_dump(mode="python"))
        if self.envelope_count != len(self.envelopes):
            raise ValueError("PORTABLE_EVIDENCE_COUNT_MISMATCH")
        return self


class PortableMissionEvidenceVerification(_PortableModel):
    valid: StrictBool
    bundle_ref: str | None = None
    envelope_count: StrictInt = Field(default=0, ge=0)
    chain_verified: StrictBool = False
    caller_expected_binding_matched: StrictBool = False
    external_anchor_verified: Literal[False] = False
    source_ledgers_verified: Literal[False] = False
    signature_verified: Literal[False] = False
    cryptographic_authenticity_verified: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    reason_refs: tuple[str, ...] = ()


def build_portable_mission_evidence_inspection(
    state_dir: Any,
) -> PortableMissionEvidenceInspectionSummary:
    """Build the bounded backend-owned inspection posture for API/CLI/UI parity."""

    from ultimate_ai_agent.core.authority.contracts import AuthorityLeaseStore
    from ultimate_ai_agent.core.authority.dispatcher import (
        AuthorityDispatchCorruptionError,
        AuthorityDispatcher,
    )
    from ultimate_ai_agent.core.execution.mission_completion import MissionCompletionStore

    manifests = MissionCompletionStore(state_dir).list_manifests()
    if not manifests:
        return PortableMissionEvidenceInspectionSummary(
            status="not_recorded",
            completion_count=0,
            envelope_count=0,
            reason_refs=("reason-ref:portable-mission-evidence:not-recorded",),
        )
    try:
        bundle = build_portable_mission_evidence_bundle(
            manifests,
            leases=AuthorityLeaseStore(state_dir).list_leases(),
            dispatch_receipts=AuthorityDispatcher(state_dir, adapters=[]).list_receipts(),
        )
        verification = verify_portable_mission_evidence_bundle(bundle)
        if not verification.valid or not verification.chain_verified:
            raise ValueError("PORTABLE_EVIDENCE_LOCAL_VERIFICATION_FAILED")
    except (AuthorityDispatchCorruptionError, OSError, UnicodeError, ValueError):
        return PortableMissionEvidenceInspectionSummary(
            status="unavailable",
            completion_count=len(manifests),
            envelope_count=0,
            reason_refs=("reason-ref:portable-mission-evidence:source-unavailable",),
        )
    return PortableMissionEvidenceInspectionSummary(
        status="verified_local_hash_chain",
        bundle_ref=bundle.bundle_ref,
        completion_count=bundle.completion_count,
        envelope_count=bundle.envelope_count,
        terminal_entry_hash_ref=bundle.terminal_entry_hash_ref,
        local_hash_chain_verified=True,
        source_receipts_bound=bundle.source_receipts_bound,
        reason_refs=verification.reason_refs,
    )


def build_portable_mission_evidence_bundle(
    manifests: Sequence[MissionCompletionManifest],
    *,
    leases: Sequence[AuthorityLease],
    dispatch_receipts: Sequence[AuthorityDispatchReceipt],
) -> PortableMissionEvidenceBundle:
    if not manifests:
        raise ValueError("PORTABLE_EVIDENCE_COMPLETION_REQUIRED")
    leases_by_ref = {item.lease_ref: item for item in leases}
    receipts_by_ref = {item.receipt_ref: item for item in dispatch_receipts}
    if len(leases_by_ref) != len(leases) or len(receipts_by_ref) != len(dispatch_receipts):
        raise ValueError("PORTABLE_EVIDENCE_DUPLICATE_SOURCE_REF")
    envelopes: list[PortableMissionEvidenceEnvelope] = []
    predecessor: str | None = None
    completion_predecessor: str | None = None
    seen_completion_runs: set[tuple[str, str]] = set()
    sequence = 0
    for manifest_sequence, manifest in enumerate(manifests, 1):
        if (
            manifest.sequence != manifest_sequence
            or manifest.previous_entry_hash_ref != completion_predecessor
            or not verify_mission_completion(manifest).valid
            or (manifest.mission_ref, manifest.run_ref) in seen_completion_runs
        ):
            raise ValueError("PORTABLE_EVIDENCE_COMPLETION_CHAIN_INVALID")
        completion_predecessor = manifest.entry_hash_ref
        seen_completion_runs.add((manifest.mission_ref, manifest.run_ref))
        lease = leases_by_ref.get(manifest.lease_ref)
        if (
            lease is None
            or lease.lease_ref != manifest.lease_ref
            or lease.scope != "mission"
            or lease.mission_ref != manifest.mission_ref
            or lease.issued_at != manifest.lease_issued_at
            or lease.expires_at != manifest.lease_expires_at
            or manifest.lease_scope_fingerprint_ref is None
            or authority_lease_issuance_scope_fingerprint_ref(lease)
            != manifest.lease_scope_fingerprint_ref
        ):
            raise ValueError("PORTABLE_EVIDENCE_LEASE_SCOPE_MISSING")
        lease_scope_ref = manifest.lease_scope_fingerprint_ref
        steps_by_dispatch = {item.dispatch_ref: item for item in manifest.step_bindings}
        for binding in manifest.dispatch_bindings:
            source = receipts_by_ref.get(binding.receipt_ref)
            step = steps_by_dispatch.get(binding.dispatch_ref)
            if source is None or step is None or not _dispatch_source_matches(
                manifest=manifest,
                binding=binding,
                source=source,
            ):
                raise ValueError("PORTABLE_EVIDENCE_DISPATCH_SOURCE_MISMATCH")
            sequence += 1
            base = PortableMissionEvidenceEnvelope(
                sequence=sequence,
                completion_ref=manifest.completion_ref,
                plan_ref=manifest.plan_ref,
                plan_fingerprint_ref=manifest.plan_fingerprint_ref,
                mission_ref=manifest.mission_ref,
                run_ref=manifest.run_ref,
                step_ref=step.step_ref,
                dispatch_ref=binding.dispatch_ref,
                dispatch_receipt_ref=binding.receipt_ref,
                dispatch_entry_hash_ref=binding.entry_hash_ref,
                lease_ref=binding.lease_ref,
                lease_scope_fingerprint_ref=lease_scope_ref,
                approval_ref=binding.approval_ref,
                approval_validation_ref=binding.approval_validation_ref,
                approval_scope_fingerprint_ref=source.approval_scope_fingerprint_ref,
                authority_decision_ref=binding.authority_decision_ref,
                authority_policy_receipt_ref=binding.authority_policy_receipt_ref,
                budget_reservation_ref=binding.budget_reservation_ref,
                budget_settlement_receipt_ref=binding.budget_settlement_receipt_ref,
                capability_ref=binding.capability_ref,
                adapter_ref=binding.adapter_ref,
                provider_ref=source.provider_ref,
                target_binding_ref=source.target_binding_ref,
                request_fingerprint_ref=binding.request_fingerprint_ref,
                predecessor_entry_hash_ref=predecessor,
                entry_hash_ref="portable-evidence-entry-hash-ref:pending",
            )
            envelope = base.model_copy(
                update={"entry_hash_ref": _entry_hash(base)}
            )
            envelopes.append(envelope)
            predecessor = envelope.entry_hash_ref
    if not envelopes:
        raise ValueError("PORTABLE_EVIDENCE_ENVELOPE_REQUIRED")
    completion_count = len({item.completion_ref for item in envelopes})
    provisional = {
        "schema_version": "uaa-portable-mission-evidence-bundle.v1",
        "verifier_version_ref": PORTABLE_MISSION_EVIDENCE_VERIFIER_REF,
        "envelope_count": len(envelopes),
        "completion_count": completion_count,
        "genesis_entry_hash_ref": envelopes[0].entry_hash_ref,
        "terminal_entry_hash_ref": envelopes[-1].entry_hash_ref,
        "envelopes": [item.model_dump(mode="json") for item in envelopes],
        "integrity_posture": "local_sha256_hash_chain",
        "signature_present": False,
        "signing_status": "blocked_signing_lifecycle_not_implemented",
        "cryptographic_authenticity_verified": False,
        "external_anchor_verified": False,
        "source_ledgers_verified": False,
        "source_receipts_bound": True,
        "execution_evidence_grants_authority": False,
        "safe_refs_only": True,
        "raw_content_included": False,
    }
    bundle = PortableMissionEvidenceBundle(
        bundle_ref=_stable_ref("portable-mission-evidence-bundle-ref", provisional),
        **provisional,
    )
    if len(_canonical_json_bytes(bundle.model_dump(mode="json"))) > PORTABLE_MISSION_EVIDENCE_MAX_BYTES:
        raise ValueError("PORTABLE_EVIDENCE_BUNDLE_TOO_LARGE")
    return bundle


def verify_portable_mission_evidence_bundle(
    value: PortableMissionEvidenceBundle | dict[str, Any],
    *,
    expected_bundle_ref: str | None = None,
    expected_envelope_count: int | None = None,
) -> PortableMissionEvidenceVerification:
    try:
        bundle = PortableMissionEvidenceBundle.model_validate(value)
        if (expected_bundle_ref is None) != (expected_envelope_count is None):
            raise ValueError("PORTABLE_EVIDENCE_EXPECTED_BINDING_INCOMPLETE")
        previous: str | None = None
        seen_receipts: set[str] = set()
        for sequence, envelope in enumerate(bundle.envelopes, 1):
            if (
                envelope.sequence != sequence
                or envelope.predecessor_entry_hash_ref != previous
                or envelope.entry_hash_ref != _entry_hash(envelope)
                or envelope.dispatch_receipt_ref in seen_receipts
            ):
                raise ValueError("PORTABLE_EVIDENCE_CHAIN_INVALID")
            previous = envelope.entry_hash_ref
            seen_receipts.add(envelope.dispatch_receipt_ref)
        payload = bundle.model_dump(mode="json", exclude={"bundle_ref"})
        if (
            bundle.genesis_entry_hash_ref != bundle.envelopes[0].entry_hash_ref
            or bundle.terminal_entry_hash_ref != bundle.envelopes[-1].entry_hash_ref
            or bundle.completion_count
            != len({item.completion_ref for item in bundle.envelopes})
            or bundle.bundle_ref
            != _stable_ref("portable-mission-evidence-bundle-ref", payload)
        ):
            raise ValueError("PORTABLE_EVIDENCE_BUNDLE_INVALID")
        _validate_bundle_semantics(bundle)
        if expected_bundle_ref is not None and bundle.bundle_ref != expected_bundle_ref:
            raise ValueError("PORTABLE_EVIDENCE_EXTERNAL_ANCHOR_MISMATCH")
        if (
            expected_envelope_count is not None
            and bundle.envelope_count != expected_envelope_count
        ):
            raise ValueError("PORTABLE_EVIDENCE_EXPECTED_COUNT_MISMATCH")
    except (TypeError, ValueError):
        return PortableMissionEvidenceVerification(
            valid=False,
            reason_refs=("reason-ref:portable-mission-evidence:invalid",),
        )
    expected_binding_matched = (
        expected_bundle_ref is not None and expected_envelope_count is not None
    )
    reasons = ["reason-ref:portable-mission-evidence:hash-chain-verified"]
    if expected_binding_matched:
        reasons.append(
            "reason-ref:portable-mission-evidence:caller-expected-binding-matched"
        )
    return PortableMissionEvidenceVerification(
        valid=True,
        bundle_ref=bundle.bundle_ref,
        envelope_count=bundle.envelope_count,
        chain_verified=True,
        caller_expected_binding_matched=expected_binding_matched,
        reason_refs=tuple(reasons),
    )


def _dispatch_source_matches(
    *,
    manifest: MissionCompletionManifest,
    binding: Any,
    source: AuthorityDispatchReceipt,
) -> bool:
    return bool(
        source.status == "succeeded"
        and source.receipt_ref == binding.receipt_ref
        and source.dispatch_ref == binding.dispatch_ref
        and source.entry_hash_ref == binding.entry_hash_ref
        and source.entry_hash_ref == authority_dispatch_receipt_entry_hash(source)
        and source.run_ref == manifest.run_ref
        and source.request_fingerprint_ref == binding.request_fingerprint_ref
        and source.lease_ref == binding.lease_ref
        and source.action_ref == binding.action_ref
        and source.adapter_ref == binding.adapter_ref
        and source.capability_ref == binding.capability_ref
        and source.authority_decision_ref == binding.authority_decision_ref
        and source.authority_policy_receipt_ref
        == binding.authority_policy_receipt_ref
        and source.approval_required == binding.approval_required
        and source.approval_ref == binding.approval_ref
        and source.approval_validation_ref == binding.approval_validation_ref
        and source.budget_reservation_ref == binding.budget_reservation_ref
        and source.budget_reservation_receipt_ref
        == binding.budget_reservation_receipt_ref
        and source.budget_start_receipt_ref == binding.budget_start_receipt_ref
        and source.budget_settlement_receipt_ref
        == binding.budget_settlement_receipt_ref
        and source.execution_ref == binding.execution_ref
        and source.execution_started is True
        and source.adapter_invocation_performed is True
        and source.actual_operation_count == binding.actual_operation_count
        and source.actual_cost_microusd == binding.actual_cost_microusd
        and source.actual_cost_ref == binding.actual_cost_ref
        and source.provider_ref is not None
        and source.target_binding_ref is not None
        and (
            not binding.approval_required
            or source.approval_scope_fingerprint_ref is not None
        )
    )


def _validate_bundle_semantics(bundle: PortableMissionEvidenceBundle) -> None:
    completion_bindings: dict[str, tuple[str, ...]] = {}
    completed_groups: set[str] = set()
    active_completion: str | None = None
    seen_steps: set[tuple[str, str]] = set()
    seen_dispatches: set[tuple[str, str]] = set()
    for envelope in bundle.envelopes:
        binding = (
            envelope.plan_ref,
            envelope.plan_fingerprint_ref,
            envelope.mission_ref,
            envelope.run_ref,
            envelope.lease_ref,
            envelope.lease_scope_fingerprint_ref,
        )
        if completion_bindings.setdefault(envelope.completion_ref, binding) != binding:
            raise ValueError("PORTABLE_EVIDENCE_COMPLETION_BINDING_MISMATCH")
        if active_completion != envelope.completion_ref:
            if active_completion is not None:
                completed_groups.add(active_completion)
            if envelope.completion_ref in completed_groups:
                raise ValueError("PORTABLE_EVIDENCE_COMPLETION_ORDER_INVALID")
            active_completion = envelope.completion_ref
        step_key = (envelope.completion_ref, envelope.step_ref)
        dispatch_key = (envelope.completion_ref, envelope.dispatch_ref)
        if step_key in seen_steps or dispatch_key in seen_dispatches:
            raise ValueError("PORTABLE_EVIDENCE_DUPLICATE_MEMBERSHIP")
        seen_steps.add(step_key)
        seen_dispatches.add(dispatch_key)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _entry_hash(envelope: PortableMissionEvidenceEnvelope) -> str:
    return _stable_ref(
        "portable-evidence-entry-hash-ref",
        envelope.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


def _stable_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json_bytes(value)).hexdigest()}"


def _validate_refs(value: Any) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"portable_evidence_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"portable_evidence_{name}")
            else:
                _validate_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested)


__all__ = [
    "PORTABLE_MISSION_EVIDENCE_VERIFIER_REF",
    "PORTABLE_MISSION_EVIDENCE_MAX_BYTES",
    "PortableMissionEvidenceBundle",
    "PortableMissionEvidenceEnvelope",
    "PortableMissionEvidenceVerification",
    "build_portable_mission_evidence_inspection",
    "build_portable_mission_evidence_bundle",
    "verify_portable_mission_evidence_bundle",
]
