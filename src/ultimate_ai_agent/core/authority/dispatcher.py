from __future__ import annotations

import hashlib
import json
import math
import os
from collections import defaultdict
from contextlib import nullcontext
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol, Sequence

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_DISPATCH_RECEIPTS_FILE,
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.budget_contracts import (
    AuthorityBudgetExecutionStatus,
    AuthorityBudgetOperation,
    AuthorityBudgetStatus,
)
from ultimate_ai_agent.core.authority.budgets import (
    AuthorityBudgetConflictError,
    AuthorityBudgetReleaseRequest,
    AuthorityBudgetReservationRequest,
    AuthorityBudgetSettlementRequest,
    AuthorityBudgetStartRequest,
    AuthorityBudgetStore,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLeaseStore,
    authority_state_dir,
    authority_state_lock_manager,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchAdapterResult,
    AuthorityDispatchCancelRequest,
    AuthorityDispatchReadModel,
    AuthorityDispatchReceipt,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.decisions import CostDecision
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.costs.governor import CostGovernor
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime.adapters import ToolRuntimeAdapter
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import (
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemSafeRoot,
    filesystem_safe_path_ref,
    normalize_relative_metadata_path,
)
from ultimate_ai_agent.core.tools.runtime.policy import (
    validate_runtime_policy,
    validate_tool_invocation_request,
)
from ultimate_ai_agent.core.tools.runtime.validation import NOOP_TOOL_REF


class AuthorityDispatchConflictError(RuntimeError):
    """Raised when a dispatch ref or idempotency ref is reused inconsistently."""


class AuthorityDispatchCorruptionError(RuntimeError):
    """Raised when durable dispatch history fails validation."""


class AuthorityDispatchAdapter(Protocol):
    descriptor: AuthorityDispatchAdapterDescriptor
    binding_ref: str

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]: ...

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult: ...


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _request_fingerprint(request: AuthorityDispatchRequest) -> str:
    return _stable_ref(
        "request-fingerprint-ref:authority-dispatch",
        request.model_dump(mode="json"),
    )


def _entry_hash(receipt: AuthorityDispatchReceipt) -> str:
    return _stable_ref(
        "entry-hash-ref:authority-dispatch",
        receipt.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


def _execution_ref(request: AuthorityDispatchRequest) -> str:
    return _stable_ref(
        "authority-dispatch-execution-ref",
        {
            "dispatch_ref": request.dispatch_ref,
            "idempotency_ref": request.idempotency_ref,
            "adapter_ref": request.adapter_ref,
        },
    )


def build_authority_dispatch_cost_estimate_ref(estimate: CostEstimate) -> str:
    return _stable_ref(
        "cost-estimate-ref:authority-dispatch",
        estimate.model_dump(mode="json"),
    )


def _cost_decision_payload(decision: CostDecision) -> dict[str, Any]:
    return decision.model_dump(mode="json", exclude={"decision_id"})


def evaluate_authority_dispatch_cost(
    estimate: CostEstimate,
    budgets: Sequence[CostBudget],
) -> CostDecision:
    return CostGovernor().evaluate(estimate, list(budgets))


def build_authority_dispatch_cost_governor_decision_ref(
    estimate: CostEstimate,
    budgets: Sequence[CostBudget],
) -> str:
    decision = evaluate_authority_dispatch_cost(estimate, budgets)
    return _stable_ref(
        "cost-governor-decision-ref:authority-dispatch",
        {
            "estimate_ref": build_authority_dispatch_cost_estimate_ref(estimate),
            "budgets": [budget.model_dump(mode="json") for budget in budgets],
            "decision": _cost_decision_payload(decision),
        },
    )


def _estimated_cost_microusd(estimate: CostEstimate) -> int | None:
    if estimate.unknown_cost or estimate.estimated_cost_usd is None:
        return None
    try:
        value = Decimal(str(estimate.estimated_cost_usd)) * Decimal(1_000_000)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    if value != value.to_integral_value():
        return None
    return int(value)


def _contains_nonfinite_float(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_contains_nonfinite_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nonfinite_float(item) for item in value)
    return False


def _phase_idempotency_ref(request: AuthorityDispatchRequest, phase: str) -> str:
    return _stable_ref(
        f"idempotency-ref:authority-dispatch-{phase}",
        {
            "dispatch_ref": request.dispatch_ref,
            "idempotency_ref": request.idempotency_ref,
        },
    )


def _budget_release_idempotency_ref(
    pending: AuthorityDispatchReceipt,
) -> str:
    return _stable_ref(
        "idempotency-ref:authority-dispatch-budget-release",
        {
            "dispatch_ref": pending.dispatch_ref,
            "reservation_ref": pending.budget_reservation_ref,
            "cancellation_idempotency_ref": pending.cancellation_idempotency_ref,
        },
    )


def _filesystem_target_reason_refs(
    request: AuthorityDispatchRequest,
    tool_request: ToolInvocationRequest,
) -> list[str]:
    root_ref = tool_request.metadata.get("root_ref")
    relative_path = tool_request.metadata.get("relative_path")
    if not isinstance(root_ref, str) or not isinstance(relative_path, str):
        return ["reason-ref:authority-dispatch:filesystem-target-invalid"]
    normalized_path, path_reasons = normalize_relative_metadata_path(relative_path)
    if path_reasons or normalized_path is None:
        return ["reason-ref:authority-dispatch:filesystem-target-invalid"]
    reasons: list[str] = []
    expected_path_ref = filesystem_safe_path_ref(root_ref, normalized_path)
    if root_ref not in request.action_request.resource_refs:
        reasons.append("reason-ref:authority-dispatch:filesystem-root-unbound")
    path_claim = next(
        (
            claim
            for claim in request.action_request.constraint_claims
            if claim.kind == AuthorityConstraintKind.path_refs.value
        ),
        None,
    )
    if (
        expected_path_ref not in request.action_request.resource_refs
        or path_claim is None
        or set(path_claim.refs) != {expected_path_ref}
    ):
        reasons.append("reason-ref:authority-dispatch:filesystem-path-unbound")
    return reasons


_TOOL_AUTHORITY_BINDINGS = {
    NOOP_TOOL_REF: (AuthorityDomain.workspace.value, AuthorityCapability.execute.value),
    FILESYSTEM_METADATA_TOOL_REF: (
        AuthorityDomain.files.value,
        AuthorityCapability.read.value,
    ),
}


def _tool_authority_binding_reason_refs(
    descriptor: AuthorityDispatchAdapterDescriptor,
) -> list[str]:
    expected = _TOOL_AUTHORITY_BINDINGS.get(descriptor.tool_ref)
    if expected is None:
        return ["reason-ref:authority-dispatch:tool-not-allowlisted"]
    if (descriptor.domain, descriptor.capability) != expected:
        return ["reason-ref:authority-dispatch:tool-authority-binding-invalid"]
    return []


def _adapter_descriptor_reason_refs(
    request: AuthorityDispatchRequest,
    descriptor: AuthorityDispatchAdapterDescriptor,
) -> list[str]:
    reasons: list[str] = []
    try:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
    except ValueError:
        return ["reason-ref:authority-dispatch:tool-request-invalid"]
    reasons.extend(_tool_authority_binding_reason_refs(descriptor))
    if descriptor.adapter_ref != request.adapter_ref:
        reasons.append("reason-ref:authority-dispatch:adapter-ref-mismatch")
    if tool_request.tool_ref != descriptor.tool_ref:
        reasons.append("reason-ref:authority-dispatch:tool-ref-mismatch")
    if request.action_request.domain != descriptor.domain:
        reasons.append("reason-ref:authority-dispatch:domain-mismatch")
    if request.action_request.capability != descriptor.capability:
        reasons.append("reason-ref:authority-dispatch:capability-mismatch")
    if request.action_request.capability_ref != descriptor.capability_ref:
        reasons.append("reason-ref:authority-dispatch:capability-ref-mismatch")
    if request.operation_count != descriptor.operation_count:
        reasons.append("reason-ref:authority-dispatch:operation-count-mismatch")
    if request.estimated_cost_microusd != descriptor.estimated_cost_microusd:
        reasons.append("reason-ref:authority-dispatch:estimated-cost-mismatch")
    if descriptor.failure_cost_microusd is None:
        reasons.append("reason-ref:authority-dispatch:failure-cost-unknown")
    elif descriptor.failure_cost_microusd > (request.estimated_cost_microusd or 0):
        reasons.append(
            "reason-ref:authority-dispatch:failure-cost-exceeds-reservation"
        )
    if descriptor.approval_required and request.approval_validation_request is None:
        reasons.append("reason-ref:authority-dispatch:approval-missing")
    if descriptor.tool_ref == FILESYSTEM_METADATA_TOOL_REF:
        reasons.extend(_filesystem_target_reason_refs(request, tool_request))
    return list(dict.fromkeys(reasons))


class ToolRuntimeAuthorityDispatchAdapter:
    """Exact, injected bridge to the existing allowlisted safe tool runtime."""

    def __init__(
        self,
        descriptor: AuthorityDispatchAdapterDescriptor,
        *,
        safe_roots: Sequence[FilesystemSafeRoot] = (),
        runtime_adapter: ToolRuntimeAdapter | None = None,
    ) -> None:
        if descriptor.tool_ref not in {
            NOOP_TOOL_REF,
            FILESYSTEM_METADATA_TOOL_REF,
        }:
            raise ValueError("AUTHORITY_DISPATCH_TOOL_NOT_ALLOWLISTED")
        if _tool_authority_binding_reason_refs(descriptor):
            raise ValueError("AUTHORITY_DISPATCH_TOOL_AUTHORITY_BINDING_INVALID")
        root_refs = [root.root_ref for root in safe_roots]
        if len(root_refs) != len(set(root_refs)):
            raise ValueError("AUTHORITY_DISPATCH_DUPLICATE_SAFE_ROOT_REF")
        self.descriptor = descriptor
        self._safe_roots = tuple(root.model_copy(deep=True) for root in safe_roots)
        self.runtime_adapter = runtime_adapter or ToolRuntimeAdapter()

    @property
    def safe_roots(self) -> tuple[FilesystemSafeRoot, ...]:
        return tuple(root.model_copy(deep=True) for root in self._safe_roots)

    @property
    def binding_ref(self) -> str:
        return _stable_ref(
            "adapter-binding-ref:authority-dispatch",
            {
                "descriptor": self.descriptor.model_dump(mode="json"),
                "safe_roots": sorted(
                    [
                        {
                            "root_ref": root.root_ref,
                            "root_path_ref": _stable_ref(
                                "root-path-ref:authority-dispatch",
                                str(root.root_path.resolve(strict=False)),
                            ),
                        }
                        for root in self._safe_roots
                    ],
                    key=lambda item: item["root_ref"],
                ),
            },
        )

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        try:
            tool_request = ToolInvocationRequest.model_validate(
                request.tool_invocation_request
            )
        except ValueError:
            return ["reason-ref:authority-dispatch:tool-request-invalid"]
        runtime_reasons = [
            *validate_runtime_policy(self.runtime_adapter.manifest.policy),
            *validate_tool_invocation_request(
                tool_request,
                safe_roots=[root.model_copy(deep=True) for root in self._safe_roots],
            ),
        ]
        if runtime_reasons:
            reasons.append(
                "reason-ref:authority-dispatch:tool-runtime-preflight-denied"
            )
        if not request.cost_governor_allowed:
            reasons.append("reason-ref:authority-dispatch:cost-governor-denied")
        if self.descriptor.tool_ref == FILESYSTEM_METADATA_TOOL_REF:
            root_ref = tool_request.metadata.get("root_ref")
            if isinstance(root_ref, str) and root_ref not in {
                root.root_ref for root in self._safe_roots
            }:
                reasons.append(
                    "reason-ref:authority-dispatch:filesystem-root-not-injected"
                )
        return list(dict.fromkeys(reasons))

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        decision = self.runtime_adapter.invoke(
            ToolInvocationRequest.model_validate(request.tool_invocation_request),
            replay_keys_seen=[],
            safe_roots=[root.model_copy(deep=True) for root in self._safe_roots],
        )
        evidence_refs = [decision.decision_id]
        output_refs: list[str] = []
        safe_output: dict[str, Any] = {
            "decision_ref": decision.decision_id,
            "status": str(decision.status),
            "reason_codes": list(decision.reason_codes),
        }
        if decision.receipt_plan is not None:
            evidence_refs.append(decision.receipt_plan.receipt_plan_ref)
        if decision.result is not None:
            evidence_refs.append(decision.result.result_id)
            output_ref = decision.result.output.output_ref
            evidence_refs.append(output_ref)
            output_refs.append(output_ref)
            safe_output = decision.result.output.model_dump(mode="json")
        succeeded = bool(
            decision.invocation_allowed
            and decision.execution_performed
            and decision.result is not None
        )
        return AuthorityDispatchAdapterResult(
            execution_ref=_execution_ref(request),
            succeeded=succeeded,
            actual_operation_count=self.descriptor.operation_count,
            actual_cost_microusd=0,
            actual_cost_ref=_stable_ref(
                "actual-cost-ref:authority-dispatch",
                {"dispatch_ref": request.dispatch_ref, "cost_microusd": 0},
            ),
            evidence_refs=list(dict.fromkeys(evidence_refs)),
            output_refs=output_refs,
            safe_output=safe_output,
            safe_summary=(
                "Allowlisted safe tool runtime invocation completed."
                if succeeded
                else "Allowlisted safe tool runtime invocation failed closed."
            ),
        )


class AuthorityDispatcher:
    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        adapters: Sequence[AuthorityDispatchAdapter],
        lease_store: AuthorityLeaseStore | None = None,
        budget_store: AuthorityBudgetStore | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> None:
        self.state_dir = state_dir or authority_state_dir()
        self.receipts_path = self.state_dir / AUTHORITY_DISPATCH_RECEIPTS_FILE
        self.lease_store = lease_store or AuthorityLeaseStore(self.state_dir)
        self.budget_store = budget_store or AuthorityBudgetStore(
            self.state_dir, lease_store=self.lease_store
        )
        if self.lease_store.state_dir.resolve() != self.state_dir.resolve():
            raise ValueError("AUTHORITY_DISPATCH_LEASE_STATE_DIR_MISMATCH")
        if self.budget_store.state_dir.resolve() != self.state_dir.resolve():
            raise ValueError("AUTHORITY_DISPATCH_BUDGET_STATE_DIR_MISMATCH")
        if (
            self.budget_store.lease_store.state_dir.resolve()
            != self.lease_store.state_dir.resolve()
        ):
            raise ValueError("AUTHORITY_DISPATCH_BUDGET_LEASE_STORE_MISMATCH")
        self.approval_authority = approval_authority
        self.lock_manager = authority_state_lock_manager(str(self.state_dir.resolve()))
        for adapter in adapters:
            if _tool_authority_binding_reason_refs(adapter.descriptor):
                raise ValueError("AUTHORITY_DISPATCH_TOOL_AUTHORITY_BINDING_INVALID")
            binding_ref = getattr(adapter, "binding_ref", None)
            if not isinstance(binding_ref, str):
                raise ValueError("AUTHORITY_DISPATCH_ADAPTER_BINDING_REF_REQUIRED")
            validate_task_ref(binding_ref, "authority_dispatch_adapter_binding_ref")
        self.adapters = {adapter.descriptor.adapter_ref: adapter for adapter in adapters}
        if len(self.adapters) != len(adapters):
            raise ValueError("AUTHORITY_DISPATCH_DUPLICATE_ADAPTER_REF")

    def dispatch(self, request: AuthorityDispatchRequest) -> AuthorityDispatchResult:
        prepared = self.prepare(request)
        if prepared.receipt.status != AuthorityDispatchStatus.prepared.value:
            return prepared
        return self.execute(request)

    def prepare(self, request: AuthorityDispatchRequest) -> AuthorityDispatchResult:
        fingerprint = _request_fingerprint(request)
        initial_conflict: AuthorityDispatchConflictError | None = None
        receipts: list[AuthorityDispatchReceipt] = []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            try:
                replay = self._existing_result(receipts, request, fingerprint)
            except AuthorityDispatchConflictError as exc:
                initial_conflict = exc
            else:
                if replay is not None:
                    return replay
        if initial_conflict is not None:
            self._release_unclaimed_reservation(request)
            raise initial_conflict

        adapter = self.adapters.get(request.adapter_ref)
        reasons = self._cost_reason_refs(request)
        if adapter is None:
            reasons.append("reason-ref:authority-dispatch:adapter-not-registered")
        else:
            reasons.extend(
                _adapter_descriptor_reason_refs(request, adapter.descriptor)
            )
            reasons.extend(adapter.validate_request(request))
        reasons = list(dict.fromkeys(reasons))
        if reasons:
            self._release_unclaimed_reservation(request)
            return self._persist_initial_denial(
                request,
                fingerprint=fingerprint,
                reasons=reasons,
                adapter=adapter,
            )
        assert adapter is not None
        try:
            reservation = self.budget_store.reserve(
                AuthorityBudgetReservationRequest(
                    lease_ref=request.lease_ref,
                    action_request=request.action_request,
                    operation_count=request.operation_count,
                    estimated_cost_microusd=request.estimated_cost_microusd,
                    cost_estimate_ref=request.cost_estimate_ref,
                    cost_governor_decision_ref=request.cost_governor_decision_ref,
                    cost_governor_allowed=request.cost_governor_allowed,
                    approval_required=adapter.descriptor.approval_required,
                    approval_validation_request=request.approval_validation_request,
                    dispatch_fingerprint_ref=fingerprint,
                    idempotency_ref=_phase_idempotency_ref(request, "budget-reserve"),
                    safe_summary="Reserve exact governed dispatch capacity before adapter start.",
                ),
                approval_validator=(
                    self.approval_authority.validate
                    if self.approval_authority is not None
                    else None
                ),
            )
        except AuthorityBudgetConflictError as exc:
            raise AuthorityDispatchConflictError(
                "AUTHORITY_DISPATCH_BUDGET_BINDING_CONFLICT"
            ) from exc
        status = reservation.original_status or reservation.status
        if status != AuthorityBudgetStatus.reserved.value:
            return self._persist_initial_denial(
                request,
                fingerprint=fingerprint,
                reasons=(
                    reservation.reason_refs
                    or ["reason-ref:authority-dispatch:budget-reservation-denied"]
                ),
                adapter=adapter,
                reservation=reservation,
            )
        if reservation.dispatch_fingerprint_ref != fingerprint:
            raise AuthorityDispatchCorruptionError(
                "AUTHORITY_DISPATCH_BUDGET_FINGERPRINT_MISMATCH"
            )
        if reservation.status == AuthorityBudgetStatus.replayed.value:
            recovery_reasons = self._replayed_reservation_reason_refs(
                request,
                reservation,
                adapter,
            )
            if recovery_reasons:
                self._release_unclaimed_reservation(request)
                return self._persist_initial_denial(
                    request,
                    fingerprint=fingerprint,
                    reasons=[
                        "reason-ref:authority-dispatch:reservation-recovery-invalid",
                        *recovery_reasons,
                    ],
                    adapter=adapter,
                    reservation=reservation,
                )

        reservation_claimed = False
        try:
            with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
                receipts = self._load_receipts()
                try:
                    replay = self._existing_result(receipts, request, fingerprint)
                except AuthorityDispatchConflictError:
                    reservation_claimed = any(
                        receipt.budget_reservation_ref == reservation.reservation_ref
                        for receipt in receipts
                    )
                    raise
                if replay is not None:
                    return replay
                receipt = self._build_receipt(
                    request,
                    status=AuthorityDispatchStatus.prepared,
                    previous_entry_hash_ref=(
                        receipts[-1].entry_hash_ref if receipts else None
                    ),
                    descriptor=adapter.descriptor,
                    adapter_binding_ref=adapter.binding_ref,
                    authority_decision_ref=reservation.authority_decision_ref,
                    authority_policy_receipt_ref=reservation.authority_policy_receipt_ref,
                    approval_required=reservation.approval_required,
                    approval_ref=reservation.approval_ref,
                    approval_validation_ref=reservation.approval_validation_ref,
                    budget_reservation_ref=reservation.reservation_ref,
                    budget_reservation_receipt_ref=reservation.receipt_ref,
                    safe_summary="Governed dispatch prepared with exact authority and budget bindings.",
                )
                self._append(receipt)
                return AuthorityDispatchResult(receipt=receipt)
        except AuthorityDispatchConflictError:
            # A reserved receipt can lose a dispatch/idempotency race after the
            # budget check. Release it only when no durable dispatch claimed it;
            # this also reclaims a replayed reservation orphaned by an earlier
            # crash between reserve and prepared.
            if (
                (reservation.original_status or reservation.status)
                == AuthorityBudgetStatus.reserved.value
                and not reservation_claimed
            ):
                release = self.budget_store.release(
                    AuthorityBudgetReleaseRequest(
                        reservation_ref=reservation.reservation_ref,
                        idempotency_ref=_phase_idempotency_ref(
                            request, "budget-reserve-race-release"
                        ),
                        reason_ref=(
                            "reason-ref:authority-dispatch:reservation-lost-dispatch-race"
                        ),
                        safe_summary=(
                            "Release fresh capacity after losing the durable dispatch claim."
                        ),
                    )
                )
                release_status = release.original_status or release.status
                if release_status != AuthorityBudgetStatus.released.value:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_RACE_RESERVATION_RELEASE_FAILED"
                    )
            raise

    def execute(self, request: AuthorityDispatchRequest) -> AuthorityDispatchResult:
        fingerprint = _request_fingerprint(request)
        pending_cancellation: AuthorityDispatchReceipt | None = None
        pending_reason_ref: str | None = None
        approval_lock = (
            self.approval_authority.hold_validation_lock()
            if self.approval_authority is not None
            else nullcontext()
        )
        # Authority state is always acquired before approval state. Budget
        # reservation follows the same order when it validates approval, which
        # avoids an execute/prepare lock inversion while keeping validation and
        # the durable start claim in one approval-revocation critical section.
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY), approval_lock:
            receipts = self._load_receipts()
            history = self._history_for_request(receipts, request, fingerprint)
            latest = history[-1]
            if latest.status in {
                AuthorityDispatchStatus.denied.value,
                AuthorityDispatchStatus.succeeded.value,
                AuthorityDispatchStatus.failed.value,
                AuthorityDispatchStatus.cancelled_before_start.value,
            }:
                return AuthorityDispatchResult(receipt=latest, replayed=True)
            if latest.status == AuthorityDispatchStatus.started.value:
                return AuthorityDispatchResult(
                    receipt=latest, replayed=True, recovery_required=True
                )
            if latest.status == AuthorityDispatchStatus.cancellation_pending.value:
                return AuthorityDispatchResult(
                    receipt=latest, replayed=True, recovery_required=True
                )
            if latest.status != AuthorityDispatchStatus.prepared.value:
                raise AuthorityDispatchCorruptionError(
                    "AUTHORITY_DISPATCH_PREPARED_STATE_REQUIRED"
                )
            adapter = self.adapters.get(request.adapter_ref)
            prestart_reasons = self._prestart_reason_refs(request, latest, adapter)
            if not prestart_reasons:
                execution_ref = _execution_ref(request)
                budget_start = self.budget_store._start_locked(
                    AuthorityBudgetStartRequest(
                        reservation_ref=latest.budget_reservation_ref or "",
                        idempotency_ref=_phase_idempotency_ref(
                            request, "budget-start"
                        ),
                        dispatch_fingerprint_ref=fingerprint,
                        execution_ref=execution_ref,
                        safe_summary=(
                            "Bind exact reserved capacity before governed adapter start."
                        ),
                    )
                )
                budget_start_status = budget_start.original_status or budget_start.status
                if budget_start_status != AuthorityBudgetStatus.started.value:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_BUDGET_START_CLAIM_FAILED"
                    )
                started = self._build_receipt_from_existing(
                    latest,
                    status=AuthorityDispatchStatus.started,
                    previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                    budget_start_receipt_ref=budget_start.receipt_ref,
                    execution_ref=execution_ref,
                    execution_started=True,
                    safe_summary="Governed adapter start recorded before invocation.",
                )
                self._append(started)
            else:
                pending = self._build_receipt_from_existing(
                    latest,
                    status=AuthorityDispatchStatus.cancellation_pending,
                    previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                    cancellation_idempotency_ref=_phase_idempotency_ref(
                        request, "prestart-policy-release"
                    ),
                    cancellation_reason_ref=prestart_reasons[0],
                    reason_refs=prestart_reasons,
                    safe_summary="Dispatch cancellation claimed before adapter start.",
                )
                self._append(pending)
                pending_cancellation = pending
                pending_reason_ref = prestart_reasons[0]

        if pending_cancellation is not None and pending_reason_ref is not None:
            return self._complete_prestart_cancellation(
                pending_cancellation,
                reason_ref=pending_reason_ref,
            )

        assert adapter is not None
        try:
            adapter_result = adapter.invoke(request)
        except Exception:
            failure_cost = adapter.descriptor.failure_cost_microusd
            adapter_result = AuthorityDispatchAdapterResult(
                execution_ref=_execution_ref(request),
                succeeded=False,
                actual_operation_count=adapter.descriptor.operation_count,
                actual_cost_microusd=failure_cost,
                actual_cost_ref=(
                    _stable_ref(
                        "actual-cost-ref:authority-dispatch",
                        {
                            "dispatch_ref": request.dispatch_ref,
                            "cost_microusd": failure_cost,
                            "failure": True,
                        },
                    )
                    if failure_cost is not None
                    else None
                ),
                evidence_refs=[
                    _stable_ref(
                        "evidence-ref:authority-dispatch-adapter-failure",
                        {"dispatch_ref": request.dispatch_ref},
                    )
                ],
                safe_summary="Adapter invocation failed safely without raw exception data.",
            )
        if adapter_result.execution_ref != started.execution_ref:
            failure_cost = adapter.descriptor.failure_cost_microusd
            adapter_result = AuthorityDispatchAdapterResult(
                execution_ref=started.execution_ref or _execution_ref(request),
                succeeded=False,
                actual_operation_count=adapter.descriptor.operation_count,
                actual_cost_microusd=failure_cost,
                actual_cost_ref=(
                    _stable_ref(
                        "actual-cost-ref:authority-dispatch",
                        {
                            "dispatch_ref": request.dispatch_ref,
                            "cost_microusd": failure_cost,
                            "execution_ref_mismatch": True,
                        },
                    )
                    if failure_cost is not None
                    else None
                ),
                evidence_refs=[
                    _stable_ref(
                        "evidence-ref:authority-dispatch-execution-ref-mismatch",
                        {"dispatch_ref": request.dispatch_ref},
                    )
                ],
                safe_summary=(
                    "Adapter result rejected because its execution ref did not "
                    "match the durable start receipt."
                ),
            )

        settlement = self.budget_store._settle_dispatch(
            AuthorityBudgetSettlementRequest(
                reservation_ref=started.budget_reservation_ref or "",
                idempotency_ref=_phase_idempotency_ref(request, "budget-settle"),
                execution_ref=started.execution_ref,
                actual_operation_count=adapter_result.actual_operation_count,
                actual_cost_microusd=adapter_result.actual_cost_microusd,
                actual_cost_ref=adapter_result.actual_cost_ref,
                execution_status=(
                    AuthorityBudgetExecutionStatus.succeeded
                    if adapter_result.succeeded
                    else AuthorityBudgetExecutionStatus.failed
                ),
                evidence_refs=adapter_result.evidence_refs,
                safe_summary="Settle governed dispatch actual operation and cost usage.",
            )
        )
        settlement_status = settlement.original_status or settlement.status
        if settlement_status not in {
            AuthorityBudgetStatus.settled.value,
            AuthorityBudgetStatus.settled_overage.value,
            AuthorityBudgetStatus.settled_cost_unresolved.value,
        }:
            return AuthorityDispatchResult(
                receipt=started, replayed=True, recovery_required=True
            )

        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            history = self._history_for_request(receipts, request, fingerprint)
            latest = history[-1]
            if latest.status != AuthorityDispatchStatus.started.value:
                return AuthorityDispatchResult(receipt=latest, replayed=True)
            terminal = self._build_receipt_from_existing(
                latest,
                status=(
                    AuthorityDispatchStatus.succeeded
                    if adapter_result.succeeded
                    else AuthorityDispatchStatus.failed
                ),
                previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                execution_ref=adapter_result.execution_ref,
                execution_started=True,
                adapter_execution_performed=True,
                budget_settlement_receipt_ref=settlement.receipt_ref,
                actual_operation_count=adapter_result.actual_operation_count,
                actual_cost_microusd=adapter_result.actual_cost_microusd,
                actual_cost_ref=adapter_result.actual_cost_ref,
                evidence_refs=adapter_result.evidence_refs,
                output_refs=adapter_result.output_refs,
                reason_refs=(
                    []
                    if adapter_result.succeeded
                    else ["reason-ref:authority-dispatch:adapter-failed"]
                ),
                safe_summary=adapter_result.safe_summary,
            )
            self._append(terminal)
            return AuthorityDispatchResult(
                receipt=terminal,
                adapter_result=adapter_result,
            )

    def cancel(self, request: AuthorityDispatchCancelRequest) -> AuthorityDispatchResult:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            history = [
                receipt
                for receipt in receipts
                if receipt.dispatch_ref == request.dispatch_ref
            ]
            if not history:
                raise KeyError("AUTHORITY_DISPATCH_NOT_FOUND")
            latest = history[-1]
            if latest.status in {
                AuthorityDispatchStatus.denied.value,
                AuthorityDispatchStatus.succeeded.value,
                AuthorityDispatchStatus.failed.value,
                AuthorityDispatchStatus.cancelled_before_start.value,
            }:
                if latest.status == AuthorityDispatchStatus.cancelled_before_start.value and (
                    latest.cancellation_idempotency_ref != request.idempotency_ref
                    or latest.cancellation_reason_ref != request.reason_ref
                ):
                    raise AuthorityDispatchConflictError(
                        "AUTHORITY_DISPATCH_CANCELLATION_IDEMPOTENCY_CONFLICT"
                    )
                return AuthorityDispatchResult(receipt=latest, replayed=True)
            if latest.status == AuthorityDispatchStatus.started.value:
                return AuthorityDispatchResult(
                    receipt=latest, replayed=True, recovery_required=True
                )
            if latest.status == AuthorityDispatchStatus.prepared.value:
                pending = self._build_receipt_from_existing(
                    latest,
                    status=AuthorityDispatchStatus.cancellation_pending,
                    previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                    cancellation_idempotency_ref=request.idempotency_ref,
                    cancellation_reason_ref=request.reason_ref,
                    reason_refs=[request.reason_ref],
                    safe_summary=request.safe_summary,
                )
                self._append(pending)
            elif latest.status == AuthorityDispatchStatus.cancellation_pending.value:
                pending = latest
                if (
                    pending.cancellation_idempotency_ref != request.idempotency_ref
                    or pending.cancellation_reason_ref != request.reason_ref
                ):
                    raise AuthorityDispatchConflictError(
                        "AUTHORITY_DISPATCH_CANCELLATION_IDEMPOTENCY_CONFLICT"
                    )
            else:
                raise AuthorityDispatchCorruptionError(
                    "AUTHORITY_DISPATCH_CANCELLATION_STATE_INVALID"
                )
        return self._complete_prestart_cancellation(
            pending,
            reason_ref=request.reason_ref,
        )

    def list_receipts(self) -> list[AuthorityDispatchReceipt]:
        if not self.receipts_path.exists():
            return []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._load_receipts()

    def build_read_model(self, *, recent_limit: int = 12) -> AuthorityDispatchReadModel:
        if recent_limit < 0:
            raise ValueError("AUTHORITY_DISPATCH_RECENT_LIMIT_NONNEGATIVE_REQUIRED")
        if not self.receipts_path.exists():
            return AuthorityDispatchReadModel()
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
        latest_by_dispatch: dict[str, AuthorityDispatchReceipt] = {}
        for receipt in receipts:
            latest_by_dispatch.pop(receipt.dispatch_ref, None)
            latest_by_dispatch[receipt.dispatch_ref] = receipt
        latest = list(latest_by_dispatch.values())
        recent = latest[-recent_limit:] if recent_limit else []
        recovery_refs = [
            receipt.dispatch_ref
            for receipt in latest
            if receipt.status
            in {
                AuthorityDispatchStatus.started.value,
                AuthorityDispatchStatus.cancellation_pending.value,
            }
        ]
        return AuthorityDispatchReadModel(
            latest_receipts=recent,
            receipt_count=len(receipts),
            recovery_required_dispatch_refs=recovery_refs,
        )

    def _prestart_reason_refs(
        self,
        request: AuthorityDispatchRequest,
        prepared: AuthorityDispatchReceipt,
        adapter: AuthorityDispatchAdapter | None,
    ) -> list[str]:
        reasons: list[str] = []
        if adapter is None:
            reasons.append("reason-ref:authority-dispatch:adapter-not-registered")
        else:
            reasons.extend(
                _adapter_descriptor_reason_refs(request, adapter.descriptor)
            )
            reasons.extend(adapter.validate_request(request))
            descriptor = adapter.descriptor
            if (
                descriptor.adapter_ref != prepared.adapter_ref
                or descriptor.capability_ref != prepared.capability_ref
                or descriptor.rollback_ref != prepared.rollback_ref
                or descriptor.safe_disable_ref != prepared.safe_disable_ref
                or descriptor.approval_required
                != prepared.adapter_approval_required
                or adapter.binding_ref != prepared.adapter_binding_ref
            ):
                reasons.append(
                    "reason-ref:authority-dispatch:prestart-adapter-binding-drift"
                )
        lease = next(
            (
                item
                for item in self.lease_store._list_leases(active_only=True)
                if item.lease_ref == request.lease_ref
            ),
            None,
        )
        decision = evaluate_authority_request(
            request.action_request, [lease] if lease is not None else []
        )
        policy_allowed = decision.outcome == AuthorityDecisionOutcome.allow.value or (
            decision.outcome == AuthorityDecisionOutcome.ask.value
            and prepared.approval_required
            and prepared.approval_ref is not None
            and prepared.approval_validation_ref is not None
        )
        if not policy_allowed or decision.lease_ref != request.lease_ref:
            reasons.append("reason-ref:authority-dispatch:prestart-authority-invalid")
        if prepared.approval_required or prepared.approval_ref is not None:
            validation_request = request.approval_validation_request
            expected_resource_refs = {
                request.lease_ref,
                request.adapter_ref,
                *request.action_request.resource_refs,
            }
            if (
                validation_request is None
                or self.approval_authority is None
                or set(validation_request.resource_refs) != expected_resource_refs
            ):
                reasons.append(
                    "reason-ref:authority-dispatch:prestart-approval-invalid"
                )
            else:
                try:
                    approval_decision = self.approval_authority.validate(
                        validation_request
                    )
                except Exception:
                    approval_decision = None
                validation_ref = (
                    _stable_ref(
                        "approval-validation-ref:authority-budget",
                        {
                            "approval_ref": validation_request.approval_ref,
                            "action_ref": request.action_request.action_ref,
                            "allowed": approval_decision.allowed,
                            "matched_grant_ref": approval_decision.matched_grant_ref,
                            "reason_codes": approval_decision.reason_codes,
                            "status": approval_decision.status,
                        },
                    )
                    if approval_decision is not None
                    else None
                )
                if (
                    approval_decision is None
                    or not approval_decision.allowed
                    or approval_decision.matched_grant_ref
                    != validation_request.approval_ref
                    or validation_ref != prepared.approval_validation_ref
                ):
                    reasons.append(
                        "reason-ref:authority-dispatch:prestart-approval-invalid"
                    )
        # The dispatcher already holds the shared authority-state writer lock here.
        # Use the stores' lock-free internal reads to avoid recursively flocking the
        # same lock file through independent manager instances.
        budget_receipts = self.budget_store._load_receipts()
        budget_state = self.budget_store._reservation_state(
            budget_receipts,
            prepared.budget_reservation_ref or "",
        )
        reservation_receipt = next(
            (
                receipt
                for receipt in budget_receipts
                if receipt.reservation_ref == prepared.budget_reservation_ref
                and receipt.operation == AuthorityBudgetOperation.reserve.value
                and receipt.status == AuthorityBudgetStatus.reserved.value
            ),
            None,
        )
        fingerprint = _request_fingerprint(request)
        expected_approval_ref = (
            request.approval_validation_request.approval_ref
            if request.approval_validation_request is not None
            else None
        )
        budget_binding_valid = bool(
            budget_state
            and reservation_receipt is not None
            and reservation_receipt.receipt_ref
            == prepared.budget_reservation_receipt_ref
            and reservation_receipt.authority_decision_ref
            == prepared.authority_decision_ref
            and reservation_receipt.authority_policy_receipt_ref
            == prepared.authority_policy_receipt_ref
            and budget_state["lease_ref"] == request.lease_ref == prepared.lease_ref
            and budget_state["action_ref"]
            == request.action_request.action_ref
            == prepared.action_ref
            and budget_state["dispatch_fingerprint_ref"]
            == fingerprint
            == prepared.request_fingerprint_ref
            and budget_state["approval_required"] == prepared.approval_required
            and budget_state["approval_ref"]
            == expected_approval_ref
            == prepared.approval_ref
            and budget_state["approval_validation_ref"]
            == prepared.approval_validation_ref
            and budget_state["cost_estimate_ref"] == request.cost_estimate_ref
            and budget_state["cost_governor_decision_ref"]
            == request.cost_governor_decision_ref
            and budget_state["cost_governor_allowed"]
            == request.cost_governor_allowed
            and budget_state["reserved_operations"] == request.operation_count
            and budget_state["reserved_cost"] == request.estimated_cost_microusd
        )
        budget_active = bool(
            budget_binding_valid
            and (
                (
                    budget_state["status"] == AuthorityBudgetStatus.reserved.value
                    and budget_state["execution_ref"] is None
                )
                or (
                    budget_state["status"] == AuthorityBudgetStatus.started.value
                    and budget_state["execution_ref"] == _execution_ref(request)
                    and budget_state["dispatch_fingerprint_ref"]
                    == fingerprint
                )
            )
        )
        if not budget_binding_valid:
            reasons.append(
                "reason-ref:authority-dispatch:prestart-budget-binding-drift"
            )
        if not budget_active:
            reasons.append("reason-ref:authority-dispatch:prestart-budget-inactive")
        reasons.extend(self._cost_reason_refs(request))
        return list(dict.fromkeys(reasons))

    def _cost_reason_refs(
        self, request: AuthorityDispatchRequest
    ) -> list[str]:
        reasons: list[str] = []
        if _contains_nonfinite_float(request.cost_estimate.model_dump(mode="python")):
            reasons.append("reason-ref:authority-dispatch:cost-estimate-nonfinite")
        if any(
            _contains_nonfinite_float(budget.model_dump(mode="python"))
            for budget in request.cost_budgets
        ):
            reasons.append("reason-ref:authority-dispatch:cost-budget-nonfinite")
        run_budgets = [
            budget for budget in request.cost_budgets if budget.scope == "run"
        ]
        if not run_budgets:
            reasons.append("reason-ref:authority-dispatch:run-cost-budget-missing")
        if any(budget.scope_id != request.run_ref for budget in run_budgets):
            reasons.append("reason-ref:authority-dispatch:run-cost-budget-scope-mismatch")
        now = utc_now()
        for budget in request.cost_budgets:
            if budget.expires_at is None:
                continue
            try:
                expired = budget.expires_at <= now
            except TypeError:
                reasons.append(
                    "reason-ref:authority-dispatch:cost-budget-time-invalid"
                )
                continue
            if expired:
                reasons.append("reason-ref:authority-dispatch:cost-budget-expired")
        estimated_microusd = _estimated_cost_microusd(request.cost_estimate)
        if estimated_microusd is None:
            reasons.append("reason-ref:authority-dispatch:cost-estimate-unknown")
        elif estimated_microusd != request.estimated_cost_microusd:
            reasons.append("reason-ref:authority-dispatch:cost-estimate-amount-mismatch")
        expected_estimate_ref = build_authority_dispatch_cost_estimate_ref(
            request.cost_estimate
        )
        if expected_estimate_ref != request.cost_estimate_ref:
            reasons.append("reason-ref:authority-dispatch:cost-estimate-ref-mismatch")
        decision = evaluate_authority_dispatch_cost(
            request.cost_estimate,
            request.cost_budgets,
        )
        expected_decision_ref = (
            build_authority_dispatch_cost_governor_decision_ref(
                request.cost_estimate,
                request.cost_budgets,
            )
        )
        if expected_decision_ref != request.cost_governor_decision_ref:
            reasons.append(
                "reason-ref:authority-dispatch:cost-governor-decision-ref-mismatch"
            )
        if decision.estimate_id != request.cost_estimate.estimate_id:
            reasons.append(
                "reason-ref:authority-dispatch:cost-governor-estimate-binding-mismatch"
            )
        if decision.allowed != request.cost_governor_allowed:
            reasons.append(
                "reason-ref:authority-dispatch:cost-governor-posture-mismatch"
            )
        if not decision.allowed:
            reasons.append("reason-ref:authority-dispatch:cost-governor-denied")
        return list(dict.fromkeys(reasons))

    def _replayed_reservation_reason_refs(
        self,
        request: AuthorityDispatchRequest,
        reservation: Any,
        adapter: AuthorityDispatchAdapter,
    ) -> list[str]:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            try:
                replay = self._existing_result(
                    receipts,
                    request,
                    _request_fingerprint(request),
                )
            except AuthorityDispatchConflictError:
                return [
                    "reason-ref:authority-dispatch:reservation-recovery-conflict"
                ]
            if replay is not None:
                return []
            candidate = self._build_receipt(
                request,
                status=AuthorityDispatchStatus.prepared,
                previous_entry_hash_ref=(
                    receipts[-1].entry_hash_ref if receipts else None
                ),
                descriptor=adapter.descriptor,
                adapter_binding_ref=adapter.binding_ref,
                authority_decision_ref=reservation.authority_decision_ref,
                authority_policy_receipt_ref=(
                    reservation.authority_policy_receipt_ref
                ),
                approval_required=reservation.approval_required,
                approval_ref=reservation.approval_ref,
                approval_validation_ref=reservation.approval_validation_ref,
                budget_reservation_ref=reservation.reservation_ref,
                budget_reservation_receipt_ref=reservation.receipt_ref,
                safe_summary=(
                    "Revalidate an orphaned reservation before durable recovery."
                ),
            )
            return self._prestart_reason_refs(request, candidate, adapter)

    def _complete_prestart_cancellation(
        self,
        pending: AuthorityDispatchReceipt,
        *,
        reason_ref: str,
    ) -> AuthorityDispatchResult:
        reservation_ref = pending.budget_reservation_ref or ""
        release = next(
            (
                receipt
                for receipt in reversed(self.budget_store.list_receipts())
                if receipt.reservation_ref == reservation_ref
                and receipt.operation == AuthorityBudgetOperation.release.value
                and receipt.status == AuthorityBudgetStatus.released.value
            ),
            None,
        )
        if release is None:
            budget_receipts = self.budget_store.list_receipts()
            budget_state = self.budget_store._reservation_state(
                budget_receipts, reservation_ref
            )
            release_request = AuthorityBudgetReleaseRequest(
                reservation_ref=reservation_ref,
                idempotency_ref=_budget_release_idempotency_ref(pending),
                reason_ref=reason_ref,
                safe_summary="Release governed dispatch capacity before adapter start.",
            )
            if (
                budget_state is not None
                and budget_state["status"] == AuthorityBudgetStatus.started.value
                and budget_state["dispatch_fingerprint_ref"]
                == pending.request_fingerprint_ref
                and budget_state["execution_ref"] is not None
            ):
                release = self.budget_store._release_started_dispatch(
                    release_request,
                    dispatch_fingerprint_ref=pending.request_fingerprint_ref,
                    execution_ref=budget_state["execution_ref"],
                )
            else:
                release = self.budget_store.release(release_request)
        release_status = release.original_status or release.status
        if release_status != AuthorityBudgetStatus.released.value:
            release = next(
                (
                    receipt
                    for receipt in reversed(self.budget_store.list_receipts())
                    if receipt.reservation_ref == reservation_ref
                    and receipt.operation == AuthorityBudgetOperation.release.value
                    and receipt.status == AuthorityBudgetStatus.released.value
                ),
                release,
            )
            release_status = release.original_status or release.status
            if release_status != AuthorityBudgetStatus.released.value:
                return AuthorityDispatchResult(
                    receipt=pending, replayed=True, recovery_required=True
                )
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            latest = next(
                receipt
                for receipt in reversed(receipts)
                if receipt.dispatch_ref == pending.dispatch_ref
            )
            if latest.status == AuthorityDispatchStatus.cancelled_before_start.value:
                return AuthorityDispatchResult(receipt=latest, replayed=True)
            if latest.status != AuthorityDispatchStatus.cancellation_pending.value:
                raise AuthorityDispatchCorruptionError(
                    "AUTHORITY_DISPATCH_CANCELLATION_CLAIM_LOST"
                )
            cancelled = self._build_receipt_from_existing(
                latest,
                status=AuthorityDispatchStatus.cancelled_before_start,
                previous_entry_hash_ref=receipts[-1].entry_hash_ref,
                budget_release_receipt_ref=release.receipt_ref,
                reason_refs=[reason_ref],
                safe_summary="Governed dispatch cancelled and budget released before start.",
            )
            self._append(cancelled)
            return AuthorityDispatchResult(receipt=cancelled)

    def _release_unclaimed_reservation(
        self,
        request: AuthorityDispatchRequest,
    ) -> None:
        reserve_idempotency_ref = _phase_idempotency_ref(request, "budget-reserve")
        fingerprint = _request_fingerprint(request)
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            dispatch_receipts = self._load_receipts()
            budget_receipts = self.budget_store._load_receipts()
            reservation = next(
                (
                    receipt
                    for receipt in budget_receipts
                    if receipt.operation == AuthorityBudgetOperation.reserve.value
                    and receipt.idempotency_ref == reserve_idempotency_ref
                    and receipt.dispatch_fingerprint_ref == fingerprint
                ),
                None,
            )
            if reservation is None:
                return
            reservation_state = self.budget_store._reservation_state(
                budget_receipts,
                reservation.reservation_ref,
            )
            if (
                reservation_state is None
                or reservation_state["status"]
                != AuthorityBudgetStatus.reserved.value
                or any(
                    receipt.budget_reservation_ref == reservation.reservation_ref
                    for receipt in dispatch_receipts
                )
            ):
                return
            release = self.budget_store._release_locked(
                AuthorityBudgetReleaseRequest(
                    reservation_ref=reservation.reservation_ref,
                    idempotency_ref=_phase_idempotency_ref(
                        request, "budget-reserve-race-release"
                    ),
                    reason_ref=(
                        "reason-ref:authority-dispatch:reservation-lost-dispatch-race"
                    ),
                    safe_summary=(
                        "Release unclaimed capacity before returning a dispatch conflict."
                    ),
                )
            )
        if (release.original_status or release.status) != (
            AuthorityBudgetStatus.released.value
        ):
            raise AuthorityDispatchCorruptionError(
                "AUTHORITY_DISPATCH_RACE_RESERVATION_RELEASE_FAILED"
            )

    def _persist_initial_denial(
        self,
        request: AuthorityDispatchRequest,
        *,
        fingerprint: str,
        reasons: list[str],
        adapter: AuthorityDispatchAdapter | None,
        reservation: Any | None = None,
    ) -> AuthorityDispatchResult:
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            receipts = self._load_receipts()
            replay = self._existing_result(receipts, request, fingerprint)
            if replay is not None:
                return replay
            receipt = self._build_receipt(
                request,
                status=AuthorityDispatchStatus.denied,
                previous_entry_hash_ref=(
                    receipts[-1].entry_hash_ref if receipts else None
                ),
                descriptor=(adapter.descriptor if adapter is not None else None),
                adapter_binding_ref=(
                    adapter.binding_ref if adapter is not None else None
                ),
                authority_decision_ref=(
                    reservation.authority_decision_ref if reservation is not None else None
                ),
                authority_policy_receipt_ref=(
                    reservation.authority_policy_receipt_ref
                    if reservation is not None
                    else None
                ),
                approval_required=(
                    reservation.approval_required
                    if reservation is not None
                    else bool(adapter and adapter.descriptor.approval_required)
                ),
                approval_ref=(reservation.approval_ref if reservation is not None else None),
                approval_validation_ref=(
                    reservation.approval_validation_ref
                    if reservation is not None
                    else None
                ),
                budget_reservation_ref=(
                    reservation.reservation_ref if reservation is not None else None
                ),
                budget_reservation_receipt_ref=(
                    reservation.receipt_ref if reservation is not None else None
                ),
                reason_refs=list(dict.fromkeys(reasons)),
                safe_summary="Governed dispatch denied before adapter start.",
            )
            self._append(receipt)
            return AuthorityDispatchResult(receipt=receipt)

    def _existing_result(
        self,
        receipts: list[AuthorityDispatchReceipt],
        request: AuthorityDispatchRequest,
        fingerprint: str,
    ) -> AuthorityDispatchResult | None:
        by_dispatch = [
            receipt for receipt in receipts if receipt.dispatch_ref == request.dispatch_ref
        ]
        by_idempotency = [
            receipt
            for receipt in receipts
            if receipt.idempotency_ref == request.idempotency_ref
        ]
        by_action = [
            receipt
            for receipt in receipts
            if receipt.action_ref == request.action_request.action_ref
        ]
        existing = by_dispatch or by_idempotency or by_action
        if not existing:
            return None
        if any(
            receipt.dispatch_ref != request.dispatch_ref
            or receipt.idempotency_ref != request.idempotency_ref
            or receipt.request_fingerprint_ref != fingerprint
            for receipt in existing
        ):
            raise AuthorityDispatchConflictError(
                "AUTHORITY_DISPATCH_IDEMPOTENCY_CONFLICT"
            )
        latest = existing[-1]
        return AuthorityDispatchResult(
            receipt=latest,
            replayed=True,
            recovery_required=(
                latest.status
                in {
                    AuthorityDispatchStatus.started.value,
                    AuthorityDispatchStatus.cancellation_pending.value,
                }
            ),
        )

    def _history_for_request(
        self,
        receipts: list[AuthorityDispatchReceipt],
        request: AuthorityDispatchRequest,
        fingerprint: str,
    ) -> list[AuthorityDispatchReceipt]:
        history = [
            receipt for receipt in receipts if receipt.dispatch_ref == request.dispatch_ref
        ]
        if not history:
            raise KeyError("AUTHORITY_DISPATCH_NOT_PREPARED")
        if any(
            receipt.idempotency_ref != request.idempotency_ref
            or receipt.request_fingerprint_ref != fingerprint
            for receipt in history
        ):
            raise AuthorityDispatchConflictError(
                "AUTHORITY_DISPATCH_IDEMPOTENCY_CONFLICT"
            )
        return history

    def _build_receipt(
        self,
        request: AuthorityDispatchRequest,
        *,
        status: AuthorityDispatchStatus,
        previous_entry_hash_ref: str | None,
        descriptor: AuthorityDispatchAdapterDescriptor | None,
        adapter_binding_ref: str | None,
        previous: AuthorityDispatchReceipt | None = None,
        **updates: Any,
    ) -> AuthorityDispatchReceipt:
        base_values: dict[str, Any] = {
            "status": status,
            "receipt_ref": _stable_ref(
                "receipt-ref:authority-dispatch",
                {
                    "dispatch_ref": request.dispatch_ref,
                    "status": status.value,
                    "previous_entry_hash_ref": previous_entry_hash_ref,
                },
            ),
            "dispatch_ref": request.dispatch_ref,
            "run_ref": request.run_ref,
            "idempotency_ref": request.idempotency_ref,
            "request_fingerprint_ref": _request_fingerprint(request),
            "lease_ref": request.lease_ref,
            "action_ref": request.action_request.action_ref,
            "adapter_ref": request.adapter_ref,
            "adapter_binding_ref": adapter_binding_ref,
            "adapter_approval_required": (
                descriptor.approval_required if descriptor is not None else False
            ),
            "capability_ref": (
                descriptor.capability_ref
                if descriptor is not None
                else request.action_request.capability_ref
                or "authority-capability-ref:unknown-denied"
            ),
            "rollback_ref": (
                descriptor.rollback_ref
                if descriptor is not None
                else request.action_request.rollback_ref
            ),
            "safe_disable_ref": (
                descriptor.safe_disable_ref
                if descriptor is not None
                else request.action_request.safe_disable_ref
            ),
            "audit_ref": _stable_ref(
                "audit-ref:authority-dispatch",
                {"dispatch_ref": request.dispatch_ref, "status": status.value},
            ),
            "previous_entry_hash_ref": previous_entry_hash_ref,
            "entry_hash_ref": "entry-hash-ref:authority-dispatch:pending",
        }
        if previous is not None:
            for field_name in [
                "authority_decision_ref",
                "authority_policy_receipt_ref",
                "approval_required",
                "adapter_approval_required",
                "adapter_binding_ref",
                "approval_ref",
                "approval_validation_ref",
                "budget_reservation_ref",
                "budget_reservation_receipt_ref",
                "budget_start_receipt_ref",
                "budget_settlement_receipt_ref",
                "budget_release_receipt_ref",
                "cancellation_idempotency_ref",
                "cancellation_reason_ref",
                "execution_ref",
                "execution_started",
                "adapter_execution_performed",
                "actual_operation_count",
                "actual_cost_microusd",
                "actual_cost_ref",
                "evidence_refs",
                "output_refs",
                "reason_refs",
            ]:
                base_values[field_name] = getattr(previous, field_name)
        base_values.update(updates)
        base = AuthorityDispatchReceipt(**base_values)
        return AuthorityDispatchReceipt.model_validate(
            {
                **base.model_dump(mode="json"),
                "entry_hash_ref": _entry_hash(base),
            }
        )

    def _build_receipt_from_existing(
        self,
        previous: AuthorityDispatchReceipt,
        *,
        status: AuthorityDispatchStatus,
        previous_entry_hash_ref: str,
        **updates: Any,
    ) -> AuthorityDispatchReceipt:
        values = previous.model_dump(mode="json")
        values.update(
            {
                "status": status,
                "receipt_ref": _stable_ref(
                    "receipt-ref:authority-dispatch",
                    {
                        "dispatch_ref": previous.dispatch_ref,
                        "status": status.value,
                        "previous_entry_hash_ref": previous_entry_hash_ref,
                    },
                ),
                "audit_ref": _stable_ref(
                    "audit-ref:authority-dispatch",
                    {"dispatch_ref": previous.dispatch_ref, "status": status.value},
                ),
                "previous_entry_hash_ref": previous_entry_hash_ref,
                "entry_hash_ref": "entry-hash-ref:authority-dispatch:pending",
                "created_at": utc_now(),
                **updates,
            }
        )
        base = AuthorityDispatchReceipt(**values)
        return AuthorityDispatchReceipt.model_validate(
            {
                **base.model_dump(mode="json"),
                "entry_hash_ref": _entry_hash(base),
            }
        )

    def _load_receipts(self) -> list[AuthorityDispatchReceipt]:
        if not self.receipts_path.exists():
            return []
        receipts: list[AuthorityDispatchReceipt] = []
        previous_hash: str | None = None
        histories: dict[str, list[AuthorityDispatchReceipt]] = defaultdict(list)
        idempotency_dispatch: dict[str, str] = {}
        action_dispatch: dict[str, str] = {}
        with self.receipts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    receipt = AuthorityDispatchReceipt(**json.loads(line))
                except Exception as exc:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_RECEIPT_INVALID"
                    ) from exc
                if receipt.previous_entry_hash_ref != previous_hash:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_HASH_CHAIN_PREVIOUS_MISMATCH"
                    )
                if receipt.entry_hash_ref != _entry_hash(receipt):
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_ENTRY_HASH_MISMATCH"
                    )
                bound_dispatch = idempotency_dispatch.setdefault(
                    receipt.idempotency_ref, receipt.dispatch_ref
                )
                if bound_dispatch != receipt.dispatch_ref:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_IDEMPOTENCY_HISTORY_MISMATCH"
                    )
                bound_action_dispatch = action_dispatch.setdefault(
                    receipt.action_ref, receipt.dispatch_ref
                )
                if bound_action_dispatch != receipt.dispatch_ref:
                    raise AuthorityDispatchCorruptionError(
                        "AUTHORITY_DISPATCH_ACTION_HISTORY_MISMATCH"
                    )
                self._validate_history_transition(
                    receipt, histories[receipt.dispatch_ref]
                )
                histories[receipt.dispatch_ref].append(receipt)
                receipts.append(receipt)
                previous_hash = receipt.entry_hash_ref
        return receipts

    def _validate_history_transition(
        self,
        receipt: AuthorityDispatchReceipt,
        history: list[AuthorityDispatchReceipt],
    ) -> None:
        if not history:
            if receipt.status not in {
                AuthorityDispatchStatus.prepared.value,
                AuthorityDispatchStatus.denied.value,
            }:
                raise AuthorityDispatchCorruptionError(
                    "AUTHORITY_DISPATCH_INITIAL_STATUS_INVALID"
                )
            return
        previous = history[-1]
        for field_name in [
            "dispatch_ref",
            "run_ref",
            "idempotency_ref",
            "request_fingerprint_ref",
            "lease_ref",
            "action_ref",
            "adapter_ref",
            "capability_ref",
            "authority_decision_ref",
            "authority_policy_receipt_ref",
            "approval_required",
            "adapter_approval_required",
            "adapter_binding_ref",
            "approval_ref",
            "approval_validation_ref",
            "budget_reservation_ref",
            "budget_reservation_receipt_ref",
            "rollback_ref",
            "safe_disable_ref",
        ]:
            if getattr(receipt, field_name) != getattr(previous, field_name):
                raise AuthorityDispatchCorruptionError(
                    "AUTHORITY_DISPATCH_FOLLOWUP_BINDING_MISMATCH"
                )
        allowed = {
            AuthorityDispatchStatus.prepared.value: {
                AuthorityDispatchStatus.started.value,
                AuthorityDispatchStatus.cancellation_pending.value,
            },
            AuthorityDispatchStatus.cancellation_pending.value: {
                AuthorityDispatchStatus.cancelled_before_start.value,
            },
            AuthorityDispatchStatus.started.value: {
                AuthorityDispatchStatus.succeeded.value,
                AuthorityDispatchStatus.failed.value,
            },
        }
        if receipt.status not in allowed.get(previous.status, set()):
            raise AuthorityDispatchCorruptionError(
                "AUTHORITY_DISPATCH_HISTORY_TRANSITION_INVALID"
            )
        if previous.status == AuthorityDispatchStatus.started.value and (
            receipt.execution_ref != previous.execution_ref
            or receipt.budget_start_receipt_ref
            != previous.budget_start_receipt_ref
        ):
            raise AuthorityDispatchCorruptionError(
                "AUTHORITY_DISPATCH_EXECUTION_BINDING_MISMATCH"
            )
        if previous.status == AuthorityDispatchStatus.cancellation_pending.value and (
            receipt.cancellation_idempotency_ref
            != previous.cancellation_idempotency_ref
            or receipt.cancellation_reason_ref != previous.cancellation_reason_ref
        ):
            raise AuthorityDispatchCorruptionError(
                "AUTHORITY_DISPATCH_CANCELLATION_BINDING_MISMATCH"
            )

    def _append(self, receipt: AuthorityDispatchReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        new_file = not self.receipts_path.exists()
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(receipt.model_dump(mode="json"), sort_keys=True) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        if new_file:
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)


def validate_authority_dispatch_ref(value: str) -> str:
    validate_task_ref(value, "authority_dispatch_ref")
    return value
