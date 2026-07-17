from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.enums import BudgetScope
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import (
    MatrixIntelligenceAuthorityDispatchAdapter,
    MatrixIntelligenceOperationResult,
)
from .authority_surfaces import (
    build_matrix_intelligence_approval_request,
    build_matrix_intelligence_authority_action,
)
from .constants import (
    MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS,
    MatrixIntelligenceOperation,
    matrix_intelligence_lane,
)
from .contracts import (
    MatrixIntelligenceCommand,
    MatrixIntelligenceDispatchMetadata,
    MatrixIntelligenceProposalDraft,
    MatrixIntelligenceReadiness,
    MatrixRoomAIPolicyMode,
    MatrixRoomContextManifest,
    stable_matrix_intelligence_ref,
)
from .store import MatrixIntelligenceStore


@dataclass(frozen=True, repr=False)
class MatrixTransientRoomMessage:
    event_ref: str
    content: str

    def __repr__(self) -> str:
        return "MatrixTransientRoomMessage(<redacted>)"


@dataclass(frozen=True, repr=False)
class MatrixIntelligenceRuntimeInput:
    messages: tuple[MatrixTransientRoomMessage, ...] = ()
    proposal_draft: MatrixIntelligenceProposalDraft | None = None

    def __repr__(self) -> str:
        return "MatrixIntelligenceRuntimeInput(<redacted>)"


class MatrixIntelligenceRuntime:
    """Sealed local owner for accepted MSG-MX-010 Stage B operations."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("MATRIX_INTELLIGENCE_RUNTIME_FACTORY_REQUIRED")

    @classmethod
    def blocked(cls) -> "MatrixIntelligenceRuntime":
        runtime = object.__new__(cls)
        runtime._mode = "blocked"
        runtime.binding_ref = stable_matrix_intelligence_ref(
            "runtime-binding-ref:matrix-intelligence",
            {"mode": "blocked", "side_effect": False},
        )
        return runtime

    @classmethod
    def local(
        cls,
        *,
        store: MatrixIntelligenceStore,
        runtime_input: MatrixIntelligenceRuntimeInput | None = None,
    ) -> "MatrixIntelligenceRuntime":
        if type(store) is not MatrixIntelligenceStore:
            raise TypeError("MATRIX_INTELLIGENCE_STORE_OWNER_REQUIRED")
        if (
            runtime_input is not None
            and type(runtime_input) is not MatrixIntelligenceRuntimeInput
        ):
            raise TypeError("MATRIX_INTELLIGENCE_RUNTIME_INPUT_REQUIRED")
        runtime = object.__new__(cls)
        runtime._mode = "local"
        runtime._store = store
        runtime._runtime_input = runtime_input or MatrixIntelligenceRuntimeInput()
        runtime.binding_ref = stable_matrix_intelligence_ref(
            "runtime-binding-ref:matrix-intelligence",
            {
                "mode": "local",
                "store_binding_ref": store.binding_ref,
                "provider_invocation": False,
                "attachment_analysis": False,
            },
        )
        return runtime

    def execute(
        self, command: MatrixIntelligenceCommand, approval_ref: str
    ) -> MatrixIntelligenceOperationResult:
        del approval_ref
        if self._mode == "blocked":
            return _result(
                command,
                succeeded=False,
                status="configuration_required",
                evidence_ref="evidence-ref:matrix-intelligence:runtime-not-bound",
            )
        if self._mode != "local":
            raise RuntimeError("MATRIX_INTELLIGENCE_RUNTIME_BINDING_INVALID")
        now = datetime.now(UTC)
        if command.operation == MatrixIntelligenceOperation.room_ai_policy_read:
            policy = self._store.read_policy(command, now=now)
            return _result(
                command,
                succeeded=True,
                status="policy_read",
                evidence_ref=policy.receipt_ref,
                extra={"policy": policy.model_dump(mode="json")},
            )
        if command.operation == MatrixIntelligenceOperation.room_ai_policy_write:
            policy, replayed = self._store.write_policy(command, now=now)
            return _result(
                command,
                succeeded=True,
                status="policy_updated",
                evidence_ref=policy.receipt_ref,
                extra={"policy": policy.model_dump(mode="json"), "replayed": replayed},
            )
        if command.operation == MatrixIntelligenceOperation.context_materialize:
            return self._materialize_context(command, now=now)
        if command.operation == MatrixIntelligenceOperation.proposal_read:
            proposal = self._store.read_proposal(command, now=now)
            return _result(
                command,
                succeeded=True,
                status="proposal_read",
                evidence_ref=proposal.receipt_ref,
                extra={"proposal": proposal.model_dump(mode="json")},
            )
        if command.operation == MatrixIntelligenceOperation.proposal_persist:
            draft = self._runtime_input.proposal_draft
            if draft is None:
                raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_DRAFT_REQUIRED")
            proposal, replayed = self._store.persist_proposal(command, draft, now=now)
            return _result(
                command,
                succeeded=True,
                status="proposal_persisted_review_only",
                evidence_ref=proposal.receipt_ref,
                extra={
                    "proposal": proposal.model_dump(mode="json"),
                    "replayed": replayed,
                },
            )
        if command.operation == MatrixIntelligenceOperation.proposal_delete:
            receipt_ref, replayed = self._store.delete_proposal(command, now=now)
            return _result(
                command,
                succeeded=True,
                status="proposal_deleted",
                evidence_ref=receipt_ref,
                extra={
                    "proposal_ref": command.proposal_ref,
                    "replayed": replayed,
                    "path_absent": True,
                },
            )
        raise RuntimeError("MATRIX_INTELLIGENCE_OPERATION_UNSUPPORTED")

    def _materialize_context(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
    ) -> MatrixIntelligenceOperationResult:
        policy = self._store.read_policy(command, now=now)
        if policy.policy == MatrixRoomAIPolicyMode.off:
            return _result(
                command,
                succeeded=False,
                status="blocked_room_ai_off",
                evidence_ref="evidence-ref:matrix-intelligence:room-ai-off",
            )
        if policy.policy == MatrixRoomAIPolicyMode.scoped_allow and (
            policy.context_grant_ref != command.context_grant_ref
            or policy.expires_at is None
            or policy.expires_at <= now
        ):
            return _result(
                command,
                succeeded=False,
                status="blocked_context_grant_mismatch",
                evidence_ref="evidence-ref:matrix-intelligence:context-grant-denied",
            )
        messages = self._runtime_input.messages
        if tuple(message.event_ref for message in messages) != command.event_refs:
            return _result(
                command,
                succeeded=False,
                status="blocked_cross_scope_or_substitution",
                evidence_ref="evidence-ref:matrix-intelligence:event-scope-denied",
            )
        if not messages or len(messages) > command.max_events:
            return _result(
                command,
                succeeded=False,
                status="blocked_event_budget",
                evidence_ref="evidence-ref:matrix-intelligence:event-budget-denied",
            )
        encoded = [message.content.encode("utf-8") for message in messages]
        byte_count = sum(len(value) for value in encoded)
        content_unit_estimate = sum(max(1, (len(value) + 3) // 4) for value in encoded)
        if byte_count > command.max_bytes or content_unit_estimate > command.max_tokens:
            return _result(
                command,
                succeeded=False,
                status="blocked_content_budget",
                evidence_ref="evidence-ref:matrix-intelligence:content-budget-denied",
            )
        fingerprints = tuple(
            stable_matrix_intelligence_ref(
                "content-fingerprint-ref:matrix-intelligence",
                {
                    "account_ref": command.account_ref,
                    "room_ref": command.room_ref,
                    "event_ref": message.event_ref,
                    "sha256": hashlib.sha256(content).hexdigest(),
                },
            )
            for message, content in zip(messages, encoded, strict=True)
        )
        expires_at = min(
            command.start_deadline,
            now
            + timedelta(
                seconds=min(
                    command.context_ttl_seconds,
                    MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS,
                )
            ),
            *([policy.expires_at] if policy.expires_at is not None else []),
        )
        manifest_basis = {
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "account_ref": command.account_ref,
            "room_ref": command.room_ref,
            "event_range_ref": command.event_range_ref,
            "event_refs": command.event_refs,
            "content_fingerprint_refs": fingerprints,
            "content_unit_estimate": content_unit_estimate,
            "byte_count": byte_count,
            "expires_at": expires_at.isoformat(),
        }
        manifest = MatrixRoomContextManifest(
            context_manifest_ref=stable_matrix_intelligence_ref(
                "context-manifest-ref:matrix-intelligence", manifest_basis
            ),
            context_receipt_ref=stable_matrix_intelligence_ref(
                "receipt-ref:matrix-intelligence-context", manifest_basis
            ),
            account_ref=command.account_ref,
            room_ref=command.room_ref,
            event_range_ref=command.event_range_ref,
            event_refs=command.event_refs,
            content_fingerprint_refs=fingerprints,
            source_count=len(messages),
            content_unit_estimate=content_unit_estimate,
            byte_count=byte_count,
            policy_ref=policy.policy_ref,
            context_grant_ref=command.context_grant_ref
            or "grant-ref:matrix-intelligence:ask-each-time",
            created_at=now,
            expires_at=expires_at,
        )
        return _result(
            command,
            succeeded=True,
            status="context_manifest_materialized_transiently",
            evidence_ref=manifest.context_receipt_ref,
            extra={"context_manifest": manifest.model_dump(mode="json")},
        )


def _result(
    command: MatrixIntelligenceCommand,
    *,
    succeeded: bool,
    status: str,
    evidence_ref: str,
    extra: dict[str, object] | None = None,
) -> MatrixIntelligenceOperationResult:
    safe_output: dict[str, object] = {
        "runtime_status": status,
        "operation": command.operation.value,
        "request_fingerprint_ref": command.request_fingerprint_ref,
        "raw_content_included": False,
        "raw_content_persisted": False,
        "provider_invocation_performed": False,
        "attachment_analysis_performed": False,
        "autonomous_send_performed": False,
        "action_execution_performed": False,
        "memory_write_performed": False,
        "context_injection_performed": False,
    }
    safe_output.update(extra or {})
    return MatrixIntelligenceOperationResult(
        succeeded=succeeded,
        safe_output=safe_output,
        evidence_refs=(evidence_ref,),
        safe_summary="The exact Matrix intelligence operation returned redacted review metadata or content-free evidence without provider, attachment, send, action, context-injection, or Memory authority.",
    )


def build_matrix_intelligence_dispatch_request(
    command: MatrixIntelligenceCommand,
    *,
    adapter: MatrixIntelligenceAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_intelligence_lane(command.operation)
    action = build_matrix_intelligence_authority_action(command)
    metadata = MatrixIntelligenceDispatchMetadata(command=command)
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_intelligence,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute one exact Matrix intelligence {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            command.account_ref,
            command.room_ref,
            command.readiness_ref,
            command.request_fingerprint_ref,
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_intelligence_ref(
            "cost-estimate-ref:matrix-intelligence",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=30,
        estimated_memory_gb=0.25,
        created_at=command.request_created_at,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_intelligence_ref(
                "cost-budget-ref:matrix-intelligence", {"run_ref": command.run_ref}
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=30,
            max_local_memory_gb=0.25,
            created_at=command.request_created_at,
        )
    ]
    pending = AuthorityDispatchRequest(
        dispatch_ref=command.dispatch_ref,
        run_ref=command.run_ref,
        idempotency_ref=command.idempotency_ref,
        lease_ref=command.lease_ref,
        adapter_ref=lane.adapter_ref,
        action_request=action,
        tool_invocation_request=tool_request.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=estimate,
        cost_budgets=budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(estimate),
        cost_governor_decision_ref=build_authority_dispatch_cost_governor_decision_ref(
            estimate, budgets
        ),
        cost_governor_allowed=True,
        start_deadline=command.start_deadline,
        safe_summary="Run one exact approved local Matrix intelligence operation.",
    )
    policy_ref = adapter.policy_decision_ref(pending)
    return pending.model_copy(
        update={
            "action_request": action.model_copy(
                update={
                    "constraints": {
                        **action.constraints,
                        "policy_decision_ref": policy_ref,
                    }
                }
            )
        }
    )


def attach_exact_matrix_intelligence_approval(
    request: AuthorityDispatchRequest,
    command: MatrixIntelligenceCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_intelligence_approval_request(command)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_intelligence_command(
    command: MatrixIntelligenceCommand,
    *,
    authority_state_dir: Path,
    runtime: MatrixIntelligenceRuntime,
    readiness_provider: Callable[
        [MatrixIntelligenceCommand], MatrixIntelligenceReadiness
    ],
    approval_ref: str | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
) -> AuthorityDispatchResult:
    if type(runtime) is not MatrixIntelligenceRuntime:
        raise TypeError("MATRIX_INTELLIGENCE_RUNTIME_OWNER_REQUIRED")
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    adapter = MatrixIntelligenceAuthorityDispatchAdapter(
        operation=command.operation,
        executor=runtime.execute,
        executor_binding_ref=runtime.binding_ref,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
        readiness_provider=readiness_provider,
    )
    request = build_matrix_intelligence_dispatch_request(command, adapter=adapter)
    if approval_ref is not None:
        request = attach_exact_matrix_intelligence_approval(
            request,
            command,
            approval_authority=approvals,
            approval_ref=approval_ref,
        )
    dispatcher = AuthorityDispatcher(
        authority_state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approvals,
    )
    return dispatcher.dispatch(request)


__all__ = [
    "MatrixIntelligenceRuntime",
    "MatrixIntelligenceRuntimeInput",
    "MatrixTransientRoomMessage",
    "attach_exact_matrix_intelligence_approval",
    "build_matrix_intelligence_dispatch_request",
    "execute_matrix_intelligence_command",
]
