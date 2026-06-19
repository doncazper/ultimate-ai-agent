from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
from ultimate_ai_agent.core.consent import ConsentGrant
from ultimate_ai_agent.core.consent.enums import ConsentScopeType, ConsentSubjectType, DataBoundary, PermissionAction
from ultimate_ai_agent.core.files import FileKind, FilePatchProposal, FileSensitivity, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskStatus, KernelTaskType, MinimumKernelRunner
from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.memory import MemoryStore


class ShadowReplayScenario(BaseModel):
    scenario_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    workspace_policy: str = Field(..., min_length=1)
    expected_event_names: List[str] = Field(default_factory=list)
    expected_final_status: str = Field(..., min_length=1)
    requires_rollback: bool = True
    requires_receipt: bool = True

    model_config = ConfigDict(extra="forbid")


class ShadowReplayResult(BaseModel):
    scenario_id: str
    passed: bool
    event_ids: List[str] = Field(default_factory=list)
    event_names: List[str] = Field(default_factory=list)
    receipt_ref: Optional[str] = None
    rollback_verified: bool = False
    final_status: str
    failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def default_m5_shadow_replay_scenario() -> ShadowReplayScenario:
    return ShadowReplayScenario(
        scenario_id="m5_minimum_lovable_kernel_replay",
        name="M5 Minimum Lovable Kernel Replay",
        description="Replay the governed local/dev file mutation, receipt, memory, world state, and rollback path.",
        workspace_policy="explicit_temp_dev_workspace_only",
        expected_event_names=[
            "run.created",
            "execution_contract.created",
            "context_pack.created",
            "tool.call.requested",
            "file.change.proposed",
            "file.change.applied",
            "memory.write.proposed",
            "event.receipt.generated",
            "run.completed",
        ],
        expected_final_status="completed",
        requires_rollback=True,
        requires_receipt=True,
    )


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _consent() -> ConsentGrant:
    return ConsentGrant(
        consent_id="consent_shadow_file_write",
        subject_type=ConsentSubjectType.user,
        subject_id="user_123",
        granted_to_actor="user_123",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.workspace,
        scope_id="workspace_shadow",
        allowed_actions=[PermissionAction.create, PermissionAction.update, PermissionAction.write],
        allowed_resources=["file.write.local_dev"],
        allowed_data_boundaries=[DataBoundary.project_private],
        allowed_purposes=["shadow_replay"],
        source="foundation_gate",
    )


def _request(workspace_root: Path, *, with_consent: bool) -> KernelTaskRequest:
    return KernelTaskRequest(
        request_id="ktr_shadow_m5",
        actor_context=_actor(),
        user_id="user_123",
        workspace_root=str(workspace_root),
        task_type=KernelTaskType.create_dev_file,
        user_request="Replay a governed local dev file update.",
        target_path="notes/m5.md",
        new_content="after\n",
        purpose="shadow_replay",
        consent_grants=[_consent()] if with_consent else [],
        approval_ref="approval_test_shadow",
        idempotency_key="idem_shadow_m5",
        data_classification=DataBoundary.project_private,
        tags=["m6", "shadow_replay"],
    )


def _rollback_request(workspace_root: Path, rollback_ref: str) -> KernelTaskRequest:
    return KernelTaskRequest(
        request_id="ktr_shadow_m5_rollback",
        actor_context=_actor(),
        user_id="user_123",
        workspace_root=str(workspace_root),
        task_type=KernelTaskType.rollback_dev_file,
        user_request="Rollback the shadow replay local dev file.",
        purpose="shadow_replay",
        consent_grants=[_consent()],
        approval_ref="approval_test_shadow_rollback",
        idempotency_key="idem_shadow_m5_rollback",
        rollback_ref=rollback_ref,
        data_classification=DataBoundary.project_private,
        tags=["m6", "shadow_replay", "rollback"],
    )


def _grant_for_request(authority: LocalApprovalAuthority, request: KernelTaskRequest):
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_tool_request(
            SimpleNamespace(
                request_id=f"tr_{request.request_id}",
                run_id=request.run_id,
                tool_id="file.write.local_dev",
                actor_context=request.actor_context,
                requested_action="create",
                purpose=request.purpose,
                data_classification=request.data_classification,
                consent_refs=[grant.consent_id for grant in request.consent_grants],
            ),
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=f"tr_{request.request_id}",
            resource_refs=["file.write.local_dev"],
            risk_level=ApprovalRiskLevel.high,
        )
    )
    return authority.grant(approval_request.approval_request_id, approved_by_actor_id="foundation_gate")


def _grant_workspace_patch_for_request(authority: LocalApprovalAuthority, request: KernelTaskRequest):
    manager = LocalFileManager(request.workspace_root)
    current_ref = manager.build_file_ref(request.target_path)
    patch = FilePatchProposal(
        proposal_id=f"file-patch-proposal:kernel:{request.request_id}",
        run_id=request.run_id,
        actor_context=request.actor_context,
        file_ref=current_ref.file_ref,
        target_path=request.target_path,
        purpose=request.purpose,
        new_content=request.new_content or "",
        expected_existing_hash=request.expected_existing_hash or current_ref.content_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        risk_class=ApprovalRiskLevel.high,
        idempotency_key=request.idempotency_key,
        audit_ref=f"file-patch-audit:{request.request_id}",
    )
    approval_request = manager.approval_request_for_patch(patch)
    authority.create_request(approval_request)
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="foundation_gate",
        approved_actions=[approval_request.requested_action],
        approved_resource_refs=approval_request.resource_refs,
    )


def _grant_workspace_rollback_for_request(
    authority: LocalApprovalAuthority,
    runner: MinimumKernelRunner,
    request: KernelTaskRequest,
):
    manager = runner._file_manager(request.workspace_root)
    approval_request = manager.approval_request_for_rollback(
        manager.get_rollback_plan(request.rollback_ref),
        run_id=request.run_id,
        actor_context=request.actor_context,
        purpose=request.purpose,
    )
    authority.create_request(approval_request)
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="foundation_gate",
        approved_actions=[approval_request.requested_action],
        approved_resource_refs=approval_request.resource_refs,
    )


def run_m5_shadow_replay(
    scenario: Optional[ShadowReplayScenario] = None,
    *,
    denial_path: bool = False,
    workspace_root: Optional[Path] = None,
) -> ShadowReplayResult:
    scenario = scenario or default_m5_shadow_replay_scenario()
    if workspace_root is None:
        with TemporaryDirectory(prefix="uaa_m6_shadow_") as workspace:
            return _run_m5_shadow_replay_at(Path(workspace), scenario, denial_path=denial_path)
    return _run_m5_shadow_replay_at(Path(workspace_root), scenario, denial_path=denial_path)


def _run_m5_shadow_replay_at(
    workspace_root: Path,
    scenario: ShadowReplayScenario,
    *,
    denial_path: bool,
) -> ShadowReplayResult:
    workspace_root.mkdir(parents=True, exist_ok=True)
    target = workspace_root / "notes/m5.md"
    failures: List[str] = []
    memory_store = MemoryStore()
    approval_authority = LocalApprovalAuthority()
    runner = MinimumKernelRunner(memory_store=memory_store, approval_authority=approval_authority)

    if not denial_path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("before\n", encoding="utf-8")

    shadow_request = _request(workspace_root, with_consent=not denial_path).model_copy(
        update={"run_id": "run_shadow_m5", "approval_ref": None}
    )
    if not denial_path:
        grant = _grant_for_request(approval_authority, shadow_request)
        workspace_grant = _grant_workspace_patch_for_request(approval_authority, shadow_request)
        shadow_request = shadow_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    result = runner.run_task(shadow_request)
    events = runner.event_ledger.list_events(result.run_id)
    event_names = [str(event.event_name) for event in events]
    event_ids = [event.event_id for event in events]
    receipt_ref = result.receipt.receipt_id if result.receipt else None
    rollback_verified = False
    final_status = str(result.status)

    expected_status = "denied" if denial_path else scenario.expected_final_status
    if final_status != expected_status:
        failures.append(f"expected status {expected_status}, got {final_status}")

    if denial_path:
        if target.exists():
            failures.append("denial path wrote a file")
        expected_events = ["run.created", "execution_contract.created", "context_pack.created", "tool.call.requested"]
    else:
        # Expected-event presence is checked once below via `expected_events`.
        if scenario.requires_receipt and not receipt_ref:
            failures.append("receipt missing")
        if not result.rollback_ref:
            failures.append("rollback_ref missing")
        if not result.world_state or not result.world_state.completed_steps:
            failures.append("world state missing")
        elif result.world_state.completed_steps[0].event_ids != result.event_ids:
            failures.append("world state event ids do not match result event ids")
        if result.memory_decision is None or not result.memory_decision.memory_id:
            failures.append("memory decision missing")
        else:
            stored = memory_store.get_memory(result.memory_decision.memory_id)
            if stored is None or not stored.source_refs or stored.source_refs[0].file_ref != "notes/m5.md":
                failures.append("memory source refs missing file reference")
        if scan_payload_for_secrets(result.model_dump(mode="json")):
            failures.append("shadow replay result leaked secret-like payload")
        if result.rollback_ref:
            rollback_request = _rollback_request(workspace_root, result.rollback_ref).model_copy(
                update={"run_id": "run_shadow_m5_rollback"}
            )
            rollback_grant = _grant_workspace_rollback_for_request(
                approval_authority,
                runner,
                rollback_request,
            )
            rollback_result = runner.run_task(
                rollback_request.model_copy(update={"workspace_approval_ref": rollback_grant.approval_ref})
            )
            rollback_verified = (
                str(rollback_result.status) == str(KernelTaskStatus.completed.value)
                and target.exists()
                and target.read_text(encoding="utf-8") == "before\n"
            )
            if scenario.requires_rollback and not rollback_verified:
                failures.append("rollback did not restore previous content")
        expected_events = scenario.expected_event_names

    for expected_name in expected_events:
        if expected_name not in event_names:
            failures.append(f"missing expected event {expected_name}")

    return ShadowReplayResult(
        scenario_id=scenario.scenario_id,
        passed=not failures,
        event_ids=event_ids,
        event_names=event_names,
        receipt_ref=receipt_ref,
        rollback_verified=rollback_verified,
        final_status=final_status,
        failures=failures,
    )
