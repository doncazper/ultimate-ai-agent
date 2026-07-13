from __future__ import annotations

import hashlib
import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalStatus
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDispatchStatus,
    AuthorityDomain,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.control_center.founder_loop_mission import (
    FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
    FounderLoopFilesystemMissionRequest,
    FounderLoopFilesystemMissionResult,
    FounderLoopFilesystemMissionService,
    FounderLoopMissionPrepared,
)
from ultimate_ai_agent.core.control_center.founder_loop_mission_refs import (
    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
)
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionError,
    verify_mission_completion,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopActionRecord,
    FounderLoopRepository,
)
from ultimate_ai_agent.core.storage.founder_loop_exact_action import (
    FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,
    FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF,
)
from ultimate_ai_agent.core.time import utc_now


FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF = (
    "contract-ref:founder-loop-attention-workflow:v1"
)
FOUNDER_LOOP_ATTENTION_WORKFLOW_ROLLBACK_REF = (
    "rollback-ref:founder-loop-attention-workflow:read-only-no-mutation"
)
FOUNDER_LOOP_ATTENTION_SAFE_GOAL_SUMMARY = (
    "Inspect metadata for the predeclared canonical repository overview."
)
_ACTION_DEFINITION_REF_PREFIX = "action-definition-ref:founder-loop-attention:sha256:"


class _AttentionWorkflowModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FounderLoopAttentionWorkflowRequest(_AttentionWorkflowModel):
    workflow_ref: str
    today_item_ref: str
    inspected_source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    source_review_receipt_ref: str
    mission_request: FounderLoopFilesystemMissionRequest

    @model_validator(mode="after")
    def validate_request(self) -> "FounderLoopAttentionWorkflowRequest":
        validate_task_ref(self.workflow_ref, "founder_loop_attention_workflow_ref")
        validate_task_ref(self.today_item_ref, "founder_loop_attention_today_item_ref")
        if len(set(self.inspected_source_refs)) != len(self.inspected_source_refs):
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REF_DUPLICATE")
        for ref in self.inspected_source_refs:
            validate_task_ref(ref, "founder_loop_attention_source_ref")
        validate_task_ref(
            self.source_review_receipt_ref,
            "founder_loop_attention_source_review_receipt_ref",
        )
        return self


class FounderLoopAttentionSourceReview(_AttentionWorkflowModel):
    today_item_ref: str
    inspected_source_refs: tuple[str, ...]
    source_review_receipt_ref: str
    audit_ref: str
    mission_ref: str
    lease_ref: str
    authority_decision_ref: str
    status: str = "source_refs_reviewed"
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_review(self) -> "FounderLoopAttentionSourceReview":
        for ref in (
            self.today_item_ref,
            self.source_review_receipt_ref,
            self.audit_ref,
            self.mission_ref,
            self.lease_ref,
            self.authority_decision_ref,
            *self.inspected_source_refs,
        ):
            validate_task_ref(ref, "founder_loop_attention_source_review_ref")
        return self


class FounderLoopAttentionWorkflowPrepared(_AttentionWorkflowModel):
    workflow_ref: str
    today_item_ref: str
    proposal_ref: str
    approval_request_ref: str
    intent_ref: str
    plan_revision_ref: str
    target_ref: str
    inspected_source_refs: tuple[str, ...]
    status: str = "awaiting_exact_approval"
    safe_summary: str = "Exact metadata-only Founder Loop action awaits review."

    @model_validator(mode="after")
    def validate_prepared(self) -> "FounderLoopAttentionWorkflowPrepared":
        for ref in (
            self.workflow_ref,
            self.today_item_ref,
            self.proposal_ref,
            self.approval_request_ref,
            self.intent_ref,
            self.plan_revision_ref,
            self.target_ref,
            *self.inspected_source_refs,
        ):
            validate_task_ref(ref, "founder_loop_attention_prepared_ref")
        validate_safe_task_text(self.safe_summary, "founder_loop_attention_summary")
        return self


class FounderLoopAttentionWorkflowResult(_AttentionWorkflowModel):
    workflow_ref: str
    today_item_ref: str
    proposal_ref: str
    approval_ref: str
    completion_ref: str
    receipt_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    memory_candidate_ref: None = None
    memory_candidate_created: bool = False
    status: str = "receipt_recorded"
    terminal_replay: bool = False
    backend_today_refreshed: bool = True
    execution_path_ref: str = (
        "execution-path-ref:mission-orchestrator-runner-dispatcher-adapter"
    )
    safe_summary: str = (
        "Exact metadata inspection completed and backend Today state was refreshed."
    )

    @model_validator(mode="after")
    def validate_result(self) -> "FounderLoopAttentionWorkflowResult":
        for ref in (
            self.workflow_ref,
            self.today_item_ref,
            self.proposal_ref,
            self.approval_ref,
            self.completion_ref,
            self.execution_path_ref,
            *self.receipt_refs,
            *self.evidence_refs,
        ):
            validate_task_ref(ref, "founder_loop_attention_result_ref")
        validate_safe_task_text(self.safe_summary, "founder_loop_attention_summary")
        return self


class FounderLoopAttentionWorkflowStatus(_AttentionWorkflowModel):
    action: FounderLoopActionRecord
    execution_performed: bool | None = False
    exact_approval_required: bool = True
    recovery_required: bool = False
    execution_truth_status: str
    approval_truth_status: str

    @model_validator(mode="after")
    def validate_status(self) -> "FounderLoopAttentionWorkflowStatus":
        validate_safe_task_text(
            self.execution_truth_status,
            "founder_loop_attention_execution_truth_status",
        )
        validate_safe_task_text(
            self.approval_truth_status,
            "founder_loop_attention_approval_truth_status",
        )
        return self


def attention_workflow_operator_request_ref(
    *,
    workflow_ref: str,
    today_item_ref: str,
    inspected_source_refs: tuple[str, ...],
    source_review_receipt_ref: str,
    proposal_ref: str,
    target_ref: str,
) -> str:
    for ref in (
        workflow_ref,
        today_item_ref,
        proposal_ref,
        target_ref,
        source_review_receipt_ref,
        *inspected_source_refs,
    ):
        validate_task_ref(ref, "founder_loop_attention_binding_ref")
    canonical = json.dumps(
        {
            "workflow_ref": workflow_ref,
            "today_item_ref": today_item_ref,
            "inspected_source_refs": sorted(inspected_source_refs),
            "source_review_receipt_ref": source_review_receipt_ref,
            "proposal_ref": proposal_ref,
            "target_ref": target_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (
        "operator-request-ref:founder-loop-attention:sha256:"
        f"{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
    )


def build_attention_workflow_request(
    *,
    workflow_ref: str,
    today_item_ref: str,
    inspected_source_refs: tuple[str, ...],
    source_review_receipt_ref: str,
    mission_ref: str,
    run_ref: str,
    lease_ref: str,
    start_deadline: datetime,
    idempotency_ref: str,
    target_ref: str,
) -> FounderLoopAttentionWorkflowRequest:
    """Build the exact immutable request shared by API and repo-local CLI."""

    bindings = {
        "workflow_ref": workflow_ref,
        "today_item_ref": today_item_ref,
        "mission_ref": mission_ref,
        "run_ref": run_ref,
        "target_ref": target_ref,
        "idempotency_ref": idempotency_ref,
        "inspected_source_refs": sorted(inspected_source_refs),
        "source_review_receipt_ref": source_review_receipt_ref,
    }

    def stable_ref(prefix: str) -> str:
        canonical = json.dumps(
            bindings,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return (
            f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
        )

    proposal_ref = stable_ref("action-proposal-ref:founder-loop-attention")
    return FounderLoopAttentionWorkflowRequest(
        workflow_ref=workflow_ref,
        today_item_ref=today_item_ref,
        inspected_source_refs=inspected_source_refs,
        source_review_receipt_ref=source_review_receipt_ref,
        mission_request=FounderLoopFilesystemMissionRequest(
            operator_request_ref=attention_workflow_operator_request_ref(
                workflow_ref=workflow_ref,
                today_item_ref=today_item_ref,
                inspected_source_refs=inspected_source_refs,
                source_review_receipt_ref=source_review_receipt_ref,
                proposal_ref=proposal_ref,
                target_ref=target_ref,
            ),
            intent_ref=stable_ref("intent-ref:founder-loop-attention"),
            plan_lineage_ref=stable_ref("plan-lineage-ref:founder-loop-attention"),
            plan_revision_ref=stable_ref("plan-revision-ref:founder-loop-attention"),
            proposal_ref=proposal_ref,
            mission_ref=mission_ref,
            run_ref=run_ref,
            plan_ref=stable_ref("mission-plan-ref:founder-loop-attention"),
            step_ref=stable_ref("mission-step-ref:founder-loop-attention"),
            target_ref=target_ref,
            lease_ref=lease_ref,
            start_deadline=start_deadline,
            safe_goal_summary=FOUNDER_LOOP_ATTENTION_SAFE_GOAL_SUMMARY,
        ),
    )


def _attention_action_definition_ref(
    *,
    action: FounderLoopActionRecord,
    target_ref: str,
    path_ref: str,
) -> str:
    evidence_refs = sorted(
        ref
        for ref in action.evidence_refs
        if not ref.startswith(_ACTION_DEFINITION_REF_PREFIX)
    )
    payload = {
        "item_ref": action.item_ref,
        "title": action.title,
        "safe_summary": action.safe_summary,
        "surface": action.surface,
        "action_kind": action.action_kind,
        "status": action.status,
        "side_effect_class": action.side_effect_class,
        "authority_boundary": action.authority_boundary,
        "approval_required": action.approval_required,
        "approval_envelope_ref": action.approval_envelope_ref,
        "approval_envelope_status": action.approval_envelope_status,
        "state_change_contract_ref": action.state_change_contract_ref,
        "state_change_readiness": action.state_change_readiness,
        "blocked_state": action.blocked_state,
        "evidence_refs": evidence_refs,
        "receipt_refs": sorted(action.receipt_refs),
        "audit_refs": sorted(action.audit_refs),
        "idempotency_key_ref": action.idempotency_key_ref,
        "expires_at": action.expires_at,
        "stale_state": action.stale_state,
        "rollback_ref": action.rollback_ref,
        "safe_disable_ref": action.safe_disable_ref,
        "next_safe_action": action.next_safe_action,
        "target_ref": target_ref,
        "path_ref": path_ref,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (
        _ACTION_DEFINITION_REF_PREFIX
        + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    )


def _source_review_refs(
    *,
    today_item_ref: str,
    inspected_source_refs: tuple[str, ...],
    idempotency_ref: str,
    mission_ref: str,
    lease_ref: str,
) -> tuple[str, str]:
    canonical = json.dumps(
        {
            "today_item_ref": today_item_ref,
            "inspected_source_refs": list(inspected_source_refs),
            "idempotency_ref": idempotency_ref,
            "mission_ref": mission_ref,
            "lease_ref": lease_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return (
        f"source-review-receipt-ref:founder-loop-attention:sha256:{digest}",
        f"audit-ref:founder-loop-attention-source-review:sha256:{digest}",
    )


class FounderLoopAttentionWorkflow:
    """Bind one Today item to the existing exact metadata-only mission."""

    def __init__(
        self,
        *,
        repository: FounderLoopRepository,
        mission_service: FounderLoopFilesystemMissionService,
    ) -> None:
        self.repository = repository
        self.mission_service = mission_service

    def required_source_refs(self, today_item_ref: str) -> tuple[str, ...]:
        self._action(today_item_ref)
        target = next(iter(self.mission_service.targets.values()))
        return tuple(
            sorted(
                {
                    today_item_ref,
                    target.target_ref,
                    target.path_ref,
                    FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF,
                }
            )
        )

    def action_status(self, today_item_ref: str) -> FounderLoopActionRecord:
        return self._action(today_item_ref).model_copy(deep=True)

    def verified_status(
        self,
        today_item_ref: str,
    ) -> FounderLoopAttentionWorkflowStatus:
        action = self._action(today_item_ref)
        approval_refs = [
            ref
            for ref in action.audit_refs
            if ref.startswith("approval-ref:founder-loop-attention:")
        ]
        approval_status = "exact_approval_not_recorded"
        current_approval = False
        if len(approval_refs) == 1:
            grant = self.mission_service.approval_authority.get_grant(approval_refs[0])
            if (
                grant is not None
                and grant.status == ApprovalStatus.granted
                and (grant.expires_at is None or grant.expires_at > utc_now())
            ):
                current_approval = True
                approval_status = (
                    "exact_approval_current_but_execution_revalidation_pending"
                )
            else:
                approval_status = "recorded_approval_not_current"
        elif len(approval_refs) > 1:
            approval_status = "approval_evidence_ambiguous"

        if action.status != "receipt_recorded":
            return FounderLoopAttentionWorkflowStatus(
                action=action,
                execution_truth_status="execution_not_recorded",
                approval_truth_status=approval_status,
                exact_approval_required=not current_approval,
            )

        try:
            completion_refs = {
                ref
                for ref in action.receipt_refs
                if ref.startswith("mission-completion-ref:")
            }
            manifests = [
                item
                for item in self.mission_service.orchestrator.completion_store.list_manifests()
                if item.completion_ref in completion_refs
            ]
            if len(completion_refs) != 1 or len(manifests) != 1:
                raise ValueError("FOUNDER_LOOP_ATTENTION_COMPLETION_EVIDENCE_MISSING")
            manifest = manifests[0]
            orchestrator = self.mission_service.orchestrator
            plan_receipts = [
                item
                for item in orchestrator.plan_store.list_receipts()
                if item.receipt_ref == manifest.plan_receipt_ref
            ]
            lease = self.mission_service.lease_store.get_lease(manifest.lease_ref)
            step_receipts = {
                item.receipt_ref: item for item in orchestrator.step_store.receipts()
            }
            all_dispatch_receipts = orchestrator.runner.dispatcher.list_receipts()
            dispatch_receipts = {
                item.receipt_ref: item for item in all_dispatch_receipts
            }
            for binding in manifest.dispatch_bindings:
                receipt = dispatch_receipts.get(binding.receipt_ref)
                if (
                    receipt is None
                    or receipt.status != AuthorityDispatchStatus.succeeded.value
                    or receipt.dispatch_ref != binding.dispatch_ref
                    or receipt.request_fingerprint_ref
                    != binding.request_fingerprint_ref
                ):
                    raise ValueError("FOUNDER_LOOP_ATTENTION_DISPATCH_EVIDENCE_INVALID")
                if (
                    binding.adapter_ref != FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF
                    or binding.capability_ref != FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF
                    or not binding.approval_required
                    or binding.approval_ref is None
                    or binding.approval_validation_ref is None
                ):
                    raise ValueError("FOUNDER_LOOP_ATTENTION_DISPATCH_SCOPE_INVALID")
            selected_steps = [
                step_receipts[item.step_receipt_ref]
                for item in manifest.step_bindings
                if item.step_receipt_ref in step_receipts
            ]
            selected_dispatches = [
                dispatch_receipts[item.receipt_ref]
                for item in manifest.dispatch_bindings
                if item.receipt_ref in dispatch_receipts
            ]
            verification = verify_mission_completion(
                manifest,
                plan_receipt=plan_receipts[0] if len(plan_receipts) == 1 else None,
                lease=lease,
                step_receipts=selected_steps,
                dispatch_receipts=selected_dispatches,
                budget_receipts=orchestrator.runner.dispatcher.budget_store.list_receipts(),
                control_receipts=orchestrator.control_store.receipts(),
            )
            if not verification.valid or not verification.source_ledgers_verified:
                raise ValueError("FOUNDER_LOOP_ATTENTION_COMPLETION_EVIDENCE_INVALID")
            if (
                action.state_change_contract_ref
                != FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF
                or not any(
                    ref.startswith("source-review-receipt-ref:founder-loop-attention:")
                    for ref in action.receipt_refs
                )
            ):
                raise ValueError("FOUNDER_LOOP_ATTENTION_TERMINAL_BINDING_DRIFT")
        except (MissionCompletionError, RuntimeError, ValueError):
            return FounderLoopAttentionWorkflowStatus(
                action=action,
                execution_performed=None,
                execution_truth_status="completion_or_dispatch_evidence_unknown",
                approval_truth_status=approval_status,
                exact_approval_required=True,
                recovery_required=True,
            )
        return FounderLoopAttentionWorkflowStatus(
            action=action,
            execution_performed=manifest.status == "succeeded",
            exact_approval_required=False,
            execution_truth_status="verified_terminal_success",
            approval_truth_status="validated_in_terminal_dispatch_evidence",
        )

    def review_source_refs(
        self,
        *,
        today_item_ref: str,
        inspected_source_refs: tuple[str, ...],
        idempotency_ref: str,
        mission_ref: str,
        lease_ref: str,
    ) -> FounderLoopAttentionSourceReview:
        validate_task_ref(
            idempotency_ref, "founder_loop_attention_source_review_idempotency"
        )
        action = self._action(today_item_ref)
        required = self.required_source_refs(today_item_ref)
        if tuple(sorted(inspected_source_refs)) != required:
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_REQUIRED")
        target = next(iter(self.mission_service.targets.values()))
        authority_decision_ref = self._validate_current_mission_lease(
            operation="source-review",
            mission_ref=mission_ref,
            lease_ref=lease_ref,
            target_ref=target.target_ref,
        )
        receipt_ref, audit_ref = _source_review_refs(
            today_item_ref=today_item_ref,
            inspected_source_refs=required,
            idempotency_ref=idempotency_ref,
            mission_ref=mission_ref,
            lease_ref=lease_ref,
        )
        existing_receipts = [
            ref
            for ref in action.receipt_refs
            if ref.startswith("source-review-receipt-ref:founder-loop-attention:")
        ]
        if existing_receipts:
            if existing_receipts != [receipt_ref]:
                raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_REPLAY_CONFLICT")
            return FounderLoopAttentionSourceReview(
                today_item_ref=today_item_ref,
                inspected_source_refs=required,
                source_review_receipt_ref=receipt_ref,
                audit_ref=audit_ref,
                mission_ref=mission_ref,
                lease_ref=lease_ref,
                authority_decision_ref=authority_decision_ref,
            )
        if action.status != "review_ready":
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_STATE_DENIED")
        updated = self._validated_action_update(
            action,
            update={
                "status": "source_refs_reviewed",
                "state_change_readiness": "source_review_receipt_recorded",
                "blocked_state": "Exact approval and mission lease are required.",
                "receipt_refs": [*action.receipt_refs, receipt_ref],
                "audit_refs": [
                    *action.audit_refs,
                    audit_ref,
                    authority_decision_ref,
                ],
                "idempotency_key_ref": idempotency_ref,
                "next_safe_action": (
                    "Prepare the exact source-bound metadata action for approval."
                ),
                "updated_at": utc_now(),
            },
        )
        self.repository.upsert_action(updated)
        return FounderLoopAttentionSourceReview(
            today_item_ref=today_item_ref,
            inspected_source_refs=required,
            source_review_receipt_ref=receipt_ref,
            audit_ref=audit_ref,
            mission_ref=mission_ref,
            lease_ref=lease_ref,
            authority_decision_ref=authority_decision_ref,
        )

    def prepare(
        self,
        request: FounderLoopAttentionWorkflowRequest,
    ) -> FounderLoopAttentionWorkflowPrepared:
        action = self._action(request.today_item_ref)
        target = self.mission_service.targets.get(request.mission_request.target_ref)
        if target is None:
            raise ValueError("FOUNDER_LOOP_ATTENTION_TARGET_NOT_PREDECLARED")
        required_sources = {
            request.today_item_ref,
            target.target_ref,
            target.path_ref,
            FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF,
        }
        if set(request.inspected_source_refs) != required_sources:
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_BINDING_REQUIRED")
        expected_operator_ref = attention_workflow_operator_request_ref(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=request.mission_request.proposal_ref,
            target_ref=target.target_ref,
        )
        if request.mission_request.operator_request_ref != expected_operator_ref:
            raise ValueError("FOUNDER_LOOP_ATTENTION_OPERATOR_BINDING_MISMATCH")
        stored_request = self.mission_service.prepared_request(
            request.mission_request.proposal_ref
        )
        if stored_request is not None:
            if stored_request.model_dump(
                mode="json"
            ) != request.mission_request.model_dump(mode="json"):
                raise ValueError("FOUNDER_LOOP_ATTENTION_PREPARE_REPLAY_CONFLICT")
            if action.status != "source_refs_reviewed":
                prepared = self.mission_service.prepared_proposal(
                    request.mission_request.proposal_ref
                )
                if (
                    prepared is None
                    or request.source_review_receipt_ref not in action.receipt_refs
                    or action.idempotency_key_ref
                    != request.mission_request.proposal_ref
                    or action.approval_envelope_ref
                    != prepared.proposal.approval_request_ref
                    or prepared.proposal.target_ref != target.target_ref
                ):
                    raise ValueError(
                        "FOUNDER_LOOP_ATTENTION_PREPARE_REPLAY_BINDING_INVALID"
                    )
                self._validate_current_action_definition(
                    action=action,
                    target_ref=target.target_ref,
                )
                return self._prepared_response(request=request, prepared=prepared)
        authority_decision_ref = self._validate_current_mission_lease(
            operation="prepare",
            mission_ref=request.mission_request.mission_ref,
            lease_ref=request.mission_request.lease_ref,
            target_ref=target.target_ref,
        )
        if (
            action.status != "source_refs_reviewed"
            or request.source_review_receipt_ref not in action.receipt_refs
            or action.idempotency_key_ref is None
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_RECEIPT_REQUIRED")
        expected_source_review_ref, _ = _source_review_refs(
            today_item_ref=request.today_item_ref,
            inspected_source_refs=tuple(sorted(request.inspected_source_refs)),
            idempotency_ref=action.idempotency_key_ref,
            mission_ref=request.mission_request.mission_ref,
            lease_ref=request.mission_request.lease_ref,
        )
        if request.source_review_receipt_ref != expected_source_review_ref:
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_RECEIPT_INVALID")
        prepared = self.mission_service.prepare(request.mission_request)
        updated_without_definition = self._validated_action_update(
            action,
            update={
                "action_kind": "exact_filesystem_metadata_inspection",
                "status": "awaiting_exact_approval",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Python Agent Core requires exact approval and a mission-scoped "
                    "files/read AuthorityLease before metadata inspection."
                ),
                "approval_required": True,
                "approval_envelope_ref": prepared.proposal.approval_request_ref,
                "approval_envelope_status": "awaiting_exact_approval",
                "state_change_contract_ref": (
                    FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF
                ),
                "state_change_readiness": "exact_metadata_mission_prepared",
                "blocked_state": "exact_approval_required_before_execution",
                "evidence_refs": list(
                    dict.fromkeys(
                        [
                            *request.inspected_source_refs,
                            prepared.proposal.intent_fingerprint_ref,
                            prepared.proposal.plan_revision_fingerprint_ref,
                            prepared.proposal.policy_decision_ref,
                        ]
                    )
                ),
                "audit_refs": list(
                    dict.fromkeys([*action.audit_refs, authority_decision_ref])
                ),
                "idempotency_key_ref": request.mission_request.proposal_ref,
                "expires_at": request.mission_request.start_deadline.isoformat(),
                "stale_state": "recheck_sources_approval_and_lease_before_start",
                "rollback_ref": FOUNDER_LOOP_ATTENTION_WORKFLOW_ROLLBACK_REF,
                "safe_disable_ref": FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
                "next_safe_action": (
                    "Review and grant the exact approval request before execution."
                ),
                "updated_at": datetime.now(
                    tz=request.mission_request.start_deadline.tzinfo
                ),
            },
        )
        definition_ref = _attention_action_definition_ref(
            action=updated_without_definition,
            target_ref=target.target_ref,
            path_ref=target.path_ref,
        )
        updated = self._validated_action_update(
            updated_without_definition,
            update={
                "evidence_refs": [
                    *updated_without_definition.evidence_refs,
                    definition_ref,
                ]
            },
        )
        self.repository.upsert_action(updated)
        return self._prepared_response(request=request, prepared=prepared)

    @staticmethod
    def _prepared_response(
        *,
        request: FounderLoopAttentionWorkflowRequest,
        prepared: FounderLoopMissionPrepared,
    ) -> FounderLoopAttentionWorkflowPrepared:
        proposal = prepared.proposal
        return FounderLoopAttentionWorkflowPrepared(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            proposal_ref=proposal.proposal_ref,
            approval_request_ref=proposal.approval_request_ref,
            intent_ref=proposal.intent_ref,
            plan_revision_ref=proposal.plan_revision_ref,
            target_ref=proposal.target_ref,
            inspected_source_refs=request.inspected_source_refs,
        )

    def grant_exact_approval(
        self,
        *,
        workflow_ref: str,
        today_item_ref: str,
        inspected_source_refs: tuple[str, ...],
        source_review_receipt_ref: str,
        proposal_ref: str,
        approved_by_actor_ref: str,
        approval_ref: str,
    ) -> str:
        validate_task_ref(proposal_ref, "founder_loop_attention_proposal_ref")
        validate_task_ref(approved_by_actor_ref, "founder_loop_attention_actor_ref")
        validate_task_ref(approval_ref, "founder_loop_attention_approval_ref")
        prepared = self.mission_service.prepared_proposal(proposal_ref)
        prepared_request = self.mission_service.prepared_request(proposal_ref)
        approval_request = self.mission_service.prepared_approval_request(proposal_ref)
        if prepared is None or prepared_request is None or approval_request is None:
            raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_NOT_PREPARED")
        self._validate_prepared_binding(
            workflow_ref=workflow_ref,
            today_item_ref=today_item_ref,
            inspected_source_refs=inspected_source_refs,
            source_review_receipt_ref=source_review_receipt_ref,
            proposal_ref=proposal_ref,
            prepared_target_ref=prepared.proposal.target_ref,
            prepared_operator_request_ref=prepared_request.operator_request_ref,
        )
        self._validate_current_action_definition(
            action=self._action(today_item_ref),
            target_ref=prepared.proposal.target_ref,
        )
        authority_decision_ref = self._validate_current_mission_lease(
            operation="approve",
            mission_ref=prepared_request.mission_ref,
            lease_ref=prepared_request.lease_ref,
            target_ref=prepared.proposal.target_ref,
        )
        with self.mission_service.approval_authority.hold_validation_lock():
            authority = self.mission_service.approval_authority
            matching_grants = [
                grant
                for grant in authority.list_grants()
                if grant.approval_request_id == approval_request.approval_request_id
            ]
            durable_approval_refs = {
                ref
                for ref in self._action(today_item_ref).audit_refs
                if ref.startswith("approval-ref:founder-loop-attention:")
            }
            if len(matching_grants) > 1 or len(durable_approval_refs) > 1:
                raise ValueError("FOUNDER_LOOP_ATTENTION_APPROVAL_EVIDENCE_AMBIGUOUS")
            if durable_approval_refs and (
                not matching_grants
                or durable_approval_refs != {matching_grants[0].approval_ref}
            ):
                raise ValueError("FOUNDER_LOOP_ATTENTION_APPROVAL_EVIDENCE_MISSING")
            existing = matching_grants[0] if matching_grants else None
            if existing is not None:
                if (
                    existing.approval_request_id != approval_request.approval_request_id
                    or existing.approved_by_actor_id != approved_by_actor_ref
                    or existing.approved_actions != [approval_request.requested_action]
                    or existing.approved_resource_refs
                    != list(approval_request.resource_refs)
                ):
                    raise ValueError("FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_CONFLICT")
                if existing.status != ApprovalStatus.granted:
                    raise ValueError("FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_DENIED")
                if existing.expires_at is not None and existing.expires_at <= utc_now():
                    raise ValueError("FOUNDER_LOOP_ATTENTION_APPROVAL_REPLAY_DENIED")
                grant = existing
            else:
                grant = authority.grant(
                    prepared.proposal.approval_request_ref,
                    approved_by_actor_id=approved_by_actor_ref,
                    approval_ref=approval_ref,
                )
            self._record_approval_posture(
                today_item_ref=today_item_ref,
                target_ref=prepared.proposal.target_ref,
                approval_ref=grant.approval_ref,
                authority_decision_ref=authority_decision_ref,
            )
        return grant.approval_ref

    def execute(
        self,
        *,
        workflow_ref: str,
        today_item_ref: str,
        inspected_source_refs: tuple[str, ...],
        source_review_receipt_ref: str,
        proposal_ref: str,
        approval_ref: str,
        owner_ref: str,
    ) -> FounderLoopAttentionWorkflowResult:
        action = self._action(today_item_ref)
        prepared = self.mission_service.prepared_proposal(proposal_ref)
        prepared_request = self.mission_service.prepared_request(proposal_ref)
        if prepared is None or prepared_request is None:
            raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_NOT_PREPARED")
        self._validate_prepared_binding(
            workflow_ref=workflow_ref,
            today_item_ref=today_item_ref,
            inspected_source_refs=inspected_source_refs,
            source_review_receipt_ref=source_review_receipt_ref,
            proposal_ref=proposal_ref,
            prepared_target_ref=prepared.proposal.target_ref,
            prepared_operator_request_ref=prepared_request.operator_request_ref,
        )
        terminal_replay_expected = action.status == "receipt_recorded"
        if not terminal_replay_expected:
            self._validate_current_action_definition(
                action=action,
                target_ref=prepared.proposal.target_ref,
            )
        result = self.mission_service.execute(
            proposal_ref=proposal_ref,
            approval_ref=approval_ref,
            owner_ref=owner_ref,
        )
        if terminal_replay_expected:
            if (
                result.completion.completion_ref not in action.receipt_refs
                or action.state_change_contract_ref
                != FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF
            ):
                raise ValueError("FOUNDER_LOOP_ATTENTION_TERMINAL_BINDING_DRIFT")
        recorded = self._record_completion(
            workflow_ref=workflow_ref,
            today_item_ref=today_item_ref,
            approval_ref=approval_ref,
            action=action,
            result=result,
        )
        verified = self.verified_status(today_item_ref)
        if verified.execution_performed is not True:
            raise ValueError("FOUNDER_LOOP_ATTENTION_TERMINAL_EVIDENCE_UNVERIFIED")
        return recorded

    def _record_completion(
        self,
        *,
        workflow_ref: str,
        today_item_ref: str,
        approval_ref: str,
        action: FounderLoopActionRecord,
        result: FounderLoopFilesystemMissionResult,
    ) -> FounderLoopAttentionWorkflowResult:
        receipt_refs = tuple(
            dict.fromkeys(
                [
                    *action.receipt_refs,
                    result.completion.completion_ref,
                    result.completion.plan_receipt_ref,
                    *(
                        item.dispatch_receipt_ref
                        for item in result.completion.step_bindings
                    ),
                ]
            )
        )
        evidence_refs = tuple(
            dict.fromkeys(
                [
                    *action.evidence_refs,
                    *result.memory_candidate.source_refs,
                ]
            )
        )
        updated_without_definition = self._validated_action_update(
            action,
            update={
                "status": "receipt_recorded",
                "approval_envelope_status": "exact_approval_validated",
                "state_change_readiness": "exact_metadata_inspection_completed",
                "blocked_state": None,
                "evidence_refs": list(evidence_refs),
                "receipt_refs": list(receipt_refs),
                "audit_refs": list(
                    dict.fromkeys(
                        [*action.audit_refs, result.completion.completion_ref]
                    )
                ),
                "stale_state": "completed_receipt_replayable",
                "next_safe_action": (
                    "Inspect the content-free execution and completion receipts."
                ),
                "updated_at": result.completion.created_at,
            },
        )
        target = self.mission_service.targets[result.proposal.target_ref]
        definition_ref = _attention_action_definition_ref(
            action=updated_without_definition,
            target_ref=target.target_ref,
            path_ref=target.path_ref,
        )
        updated = self._validated_action_update(
            updated_without_definition,
            update={
                "evidence_refs": [
                    *(
                        ref
                        for ref in updated_without_definition.evidence_refs
                        if not ref.startswith(_ACTION_DEFINITION_REF_PREFIX)
                    ),
                    definition_ref,
                ]
            },
        )
        self.repository.upsert_action(updated)
        evidence_refs = tuple(updated.evidence_refs)
        return FounderLoopAttentionWorkflowResult(
            workflow_ref=workflow_ref,
            today_item_ref=today_item_ref,
            proposal_ref=result.proposal.proposal_ref,
            approval_ref=approval_ref,
            completion_ref=result.completion.completion_ref,
            receipt_refs=receipt_refs,
            evidence_refs=evidence_refs,
            terminal_replay=result.terminal_replay,
        )

    def _record_approval_posture(
        self,
        *,
        today_item_ref: str,
        target_ref: str,
        approval_ref: str,
        authority_decision_ref: str,
    ) -> None:
        action = self._action(today_item_ref)
        updated_without_definition = self._validated_action_update(
            action,
            update={
                "status": "approval_recorded_execution_validation_pending",
                "approval_envelope_status": (
                    "exact_approval_recorded_current_validation_pending"
                ),
                "state_change_readiness": "execution_revalidation_pending",
                "blocked_state": (
                    "current approval lease policy budget readiness and kill switch "
                    "must be re-evaluated inside the dispatcher before start"
                ),
                "audit_refs": list(
                    dict.fromkeys(
                        [*action.audit_refs, approval_ref, authority_decision_ref]
                    )
                ),
                "next_safe_action": (
                    "Execute through the governed mission path for fresh validation."
                ),
                "updated_at": utc_now(),
            },
        )
        target = self.mission_service.targets[target_ref]
        definition_ref = _attention_action_definition_ref(
            action=updated_without_definition,
            target_ref=target.target_ref,
            path_ref=target.path_ref,
        )
        evidence_refs = [
            ref
            for ref in updated_without_definition.evidence_refs
            if not ref.startswith(_ACTION_DEFINITION_REF_PREFIX)
        ]
        updated = self._validated_action_update(
            updated_without_definition,
            update={"evidence_refs": [*evidence_refs, definition_ref]},
        )
        self.repository.upsert_action(updated)

    def _validate_current_mission_lease(
        self,
        *,
        operation: str,
        mission_ref: str,
        lease_ref: str,
        target_ref: str,
    ) -> str:
        validate_safe_task_text(operation, "founder_loop_attention_operation")
        validate_task_ref(mission_ref, "founder_loop_attention_mission_ref")
        validate_task_ref(lease_ref, "founder_loop_attention_lease_ref")
        target = self.mission_service.targets.get(target_ref)
        if target is None:
            raise ValueError("FOUNDER_LOOP_ATTENTION_TARGET_NOT_PREDECLARED")
        lease = self.mission_service.lease_store.get_lease(lease_ref)
        if (
            lease is None
            or lease.scope != "mission"
            or lease.mission_ref != mission_ref
            or not lease.is_active(now=utc_now())
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED")
        resource_constraints = [
            constraint
            for constraint in lease.authority_constraints
            if constraint.kind == AuthorityConstraintKind.resource_refs.value
        ]
        expected_resources = {
            FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
            FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
            target.target_ref,
            target.root_ref,
            target.path_ref,
            mission_ref,
        }
        if (
            len(resource_constraints) != 1
            or set(resource_constraints[0].allowed_refs) != expected_resources
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED")
        constraints_by_kind = {
            str(constraint.kind): constraint
            for constraint in lease.authority_constraints
        }
        path_constraint = constraints_by_kind.get(
            AuthorityConstraintKind.path_refs.value
        )
        operation_constraint = constraints_by_kind.get(
            AuthorityConstraintKind.operation_budget.value
        )
        cost_constraint = constraints_by_kind.get(
            AuthorityConstraintKind.cost_budget_microusd.value
        )
        domain_values = {
            str(getattr(domain, "value", domain)): [
                str(getattr(capability, "value", capability))
                for capability in capabilities
            ]
            for domain, capabilities in lease.domains.items()
        }
        if (
            domain_values
            != {AuthorityDomain.files.value: [AuthorityCapability.read.value]}
            or path_constraint is None
            or path_constraint.allowed_refs != [target.path_ref]
            or operation_constraint is None
            or operation_constraint.maximum != 1
            or cost_constraint is None
            or cost_constraint.maximum != 1
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED")
        action_ref = (
            "authority-action-ref:founder-loop-attention-"
            f"{operation}:sha256:"
            f"{hashlib.sha256(f'{mission_ref}:{lease_ref}:{target_ref}'.encode()).hexdigest()}"
        )
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=action_ref,
                domain=AuthorityDomain.files,
                capability=AuthorityCapability.read,
                safe_summary=(
                    "Validate one exact Founder Loop metadata workflow mutation."
                ),
                resource_refs=[
                    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
                    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                    target.target_ref,
                    target.root_ref,
                    target.path_ref,
                    mission_ref,
                ],
                capability_ref=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
                adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.resource_refs,
                    ),
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.path_refs,
                        refs=[target.path_ref],
                    ),
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget,
                        value=1,
                    ),
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.cost_budget_microusd,
                        value=0,
                    ),
                ],
                constraints={"mission_ref": mission_ref},
                draft_fallback_available=False,
                unsupported_adapter=False,
                rollback_ref=FOUNDER_LOOP_ATTENTION_WORKFLOW_ROLLBACK_REF,
                safe_disable_ref=FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
            ),
            [lease],
            now=utc_now(),
        )
        if (
            decision.outcome != AuthorityDecisionOutcome.allow.value
            or decision.lease_ref != lease_ref
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_CURRENT_MISSION_LEASE_REQUIRED")
        return decision.decision_ref

    @staticmethod
    def _validated_action_update(
        action: FounderLoopActionRecord,
        *,
        update: dict[str, object],
    ) -> FounderLoopActionRecord:
        payload = action.model_dump(mode="python")
        payload.update(update)
        return FounderLoopActionRecord.model_validate(payload)

    @staticmethod
    def _validate_prepared_binding(
        *,
        workflow_ref: str,
        today_item_ref: str,
        inspected_source_refs: tuple[str, ...],
        source_review_receipt_ref: str,
        proposal_ref: str,
        prepared_target_ref: str,
        prepared_operator_request_ref: str,
    ) -> None:
        expected_operator_ref = attention_workflow_operator_request_ref(
            workflow_ref=workflow_ref,
            today_item_ref=today_item_ref,
            inspected_source_refs=inspected_source_refs,
            source_review_receipt_ref=source_review_receipt_ref,
            proposal_ref=proposal_ref,
            target_ref=prepared_target_ref,
        )
        if prepared_operator_request_ref != expected_operator_ref:
            raise ValueError("FOUNDER_LOOP_ATTENTION_SOURCE_BINDING_DRIFT")

    def _validate_current_action_definition(
        self,
        *,
        action: FounderLoopActionRecord,
        target_ref: str,
    ) -> None:
        target = self.mission_service.targets.get(target_ref)
        if target is None:
            raise ValueError("FOUNDER_LOOP_ATTENTION_TARGET_NOT_PREDECLARED")
        bound_refs = [
            ref
            for ref in action.evidence_refs
            if ref.startswith(_ACTION_DEFINITION_REF_PREFIX)
        ]
        if len(bound_refs) != 1:
            raise ValueError("FOUNDER_LOOP_ATTENTION_ACTION_DEFINITION_MISSING")
        expected = _attention_action_definition_ref(
            action=action,
            target_ref=target.target_ref,
            path_ref=target.path_ref,
        )
        if bound_refs[0] != expected:
            raise ValueError("FOUNDER_LOOP_ATTENTION_ACTION_DEFINITION_DRIFT")

    def _action(self, today_item_ref: str) -> FounderLoopActionRecord:
        validate_task_ref(today_item_ref, "founder_loop_attention_today_item_ref")
        if today_item_ref != FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF:
            raise ValueError("FOUNDER_LOOP_ATTENTION_ITEM_NOT_ELIGIBLE")
        action = next(
            (
                item
                for item in self.repository.list_action_inbox(limit=100)
                if item.get("item_ref") == today_item_ref
            ),
            None,
        )
        if action is None:
            raise ValueError("FOUNDER_LOOP_ATTENTION_ITEM_NOT_FOUND")
        payload = {
            field_name: action[field_name]
            for field_name in FounderLoopActionRecord.model_fields
            if field_name in action
        }
        return FounderLoopActionRecord.model_validate(payload)
