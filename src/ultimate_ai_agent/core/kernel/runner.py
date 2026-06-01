import uuid
from ultimate_ai_agent.core.time import utc_now
from pathlib import Path
from typing import Callable, Dict, Optional

from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.consent.decisions import ConsentQuery
from ultimate_ai_agent.core.consent.enums import DataBoundary, PermissionAction, PermissionRisk
from ultimate_ai_agent.core.consent.ledger import ConsentLedger
from ultimate_ai_agent.core.contracts.context_pack import ContextPack
from ultimate_ai_agent.core.contracts.enums import AgentMode, AutonomyLevel, ContractStatus, GroundingMode, RiskLevel, TaskClass
from ultimate_ai_agent.core.contracts.execution_contract import ExecutionContract
from ultimate_ai_agent.core.files.enums import FileKind, FileSensitivity
from ultimate_ai_agent.core.files.manager import LocalFileManager
from ultimate_ai_agent.core.files.operations import FileWriteProposal
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
    IdempotencyPolicy,
    OperationType,
    OutcomeStatus,
    RedactionAction,
    RedactionPolicy,
    RedactionSurface,
    RetryClass,
)
from ultimate_ai_agent.core.hygiene.temporal_context import FreshnessClass, StalenessPolicy, TemporalContext
from ultimate_ai_agent.core.kernel.enums import KernelTaskStatus, KernelTaskType
from ultimate_ai_agent.core.kernel.receipts import generate_kernel_receipt
from ultimate_ai_agent.core.kernel.requests import KernelTaskRequest
from ultimate_ai_agent.core.kernel.results import KernelTaskResult
from ultimate_ai_agent.core.kernel.validation import validate_kernel_payload
from ultimate_ai_agent.core.ledger.enums import EventName
from ultimate_ai_agent.core.ledger.events import EventLedgerEvent
from ultimate_ai_agent.core.ledger.ledger import EventLedger
from ultimate_ai_agent.core.memory import MemoryStore
from ultimate_ai_agent.core.memory.enums import MemoryAuthority, MemoryScope, MemorySensitivity, MemoryType
from ultimate_ai_agent.core.memory.records import MemorySourceRef
from ultimate_ai_agent.core.memory.requests import MemoryWriteRequest
from ultimate_ai_agent.core.tools import (
    CapabilityFirewallPolicy,
    ToolBroker,
    ToolExecutionMode,
    ToolManifest,
    ToolPermissionKind,
    ToolPermissionManifest,
    ToolRegistry,
    ToolRequest,
    ToolRiskLevel,
)
from ultimate_ai_agent.core.tools.enums import ToolCategory, ToolDecisionStatus
from ultimate_ai_agent.core.truth import TruthSourceRouter
from ultimate_ai_agent.core.world_state import StructuredWorldState, WorldStateStep


FILE_WRITE_TOOL_ID = "file.write.local_dev"


class MinimumKernelRunner:
    def __init__(
        self,
        event_ledger: Optional[EventLedger] = None,
        memory_store: Optional[MemoryStore] = None,
        tool_registry: Optional[ToolRegistry] = None,
        consent_ledger: Optional[ConsentLedger] = None,
        truth_router: Optional[TruthSourceRouter] = None,
        file_manager_factory: Optional[Callable[[str], LocalFileManager]] = None,
        approval_authority: Optional[LocalApprovalAuthority] = None,
    ):
        self.event_ledger = event_ledger or EventLedger()
        self.memory_store = memory_store or MemoryStore()
        self.tool_registry = tool_registry or ToolRegistry()
        self.consent_ledger = consent_ledger
        self.truth_router = truth_router or TruthSourceRouter()
        self.file_manager_factory = file_manager_factory or (lambda root: LocalFileManager(root))
        self.approval_authority = approval_authority
        self._file_managers: Dict[str, LocalFileManager] = {}

    def run_payload(self, payload: dict) -> KernelTaskResult:
        run_id = str(payload.get("run_id") or f"run_{uuid.uuid4().hex[:10]}")
        try:
            request = validate_kernel_payload(payload)
        except ValueError as exc:
            code = str(exc) or "KERNEL_REQUEST_INVALID"
            return self._synthetic_failure(run_id, KernelTaskStatus.blocked, "Kernel request was blocked.", [code], ["secret_value"])
        except ValidationError as exc:
            safe_errors = [error["type"].upper() for error in exc.errors()]
            return self._synthetic_failure(run_id, KernelTaskStatus.blocked, "Kernel request validation failed.", safe_errors)
        return self.run_task(request)

    def run_task(self, request: KernelTaskRequest) -> KernelTaskResult:
        run_id = request.run_id or f"run_{uuid.uuid4().hex[:10]}"
        trace_id = f"trace_{run_id}"
        self._append_event(request, run_id, trace_id, EventName.run_created, "run", "Kernel run", "create", "created")

        if request.task_type == KernelTaskType.rollback_dev_file:
            return self._run_rollback(request, run_id, trace_id)
        if request.task_type == KernelTaskType.validate_only:
            return self._complete_without_write(request, run_id, trace_id)

        contract = self._build_execution_contract(request, run_id)
        self._append_event(request, run_id, trace_id, EventName.execution_contract_created, "contract", contract.contract_id, "create", "created")
        context_pack = self._build_context_pack(request, run_id, contract.contract_id)
        self._append_event(request, run_id, trace_id, EventName.context_pack_created, "context", context_pack.context_pack_id, "create", "created")

        consent_ledger = self._build_consent_ledger(request)
        consent_decision = self._preview_consent(request, consent_ledger)
        registry = self._build_tool_registry(request.workspace_root, dry_run=request.dry_run)
        tool_request = self._build_tool_request(request, run_id)
        broker = ToolBroker(
            registry=registry,
            firewall_policy=CapabilityFirewallPolicy(
                allowed_filesystem_roots=[str(Path(request.workspace_root).resolve())],
                max_risk_level=ToolRiskLevel.high,
            ),
            approval_authority=self.approval_authority,
        )

        self._append_event(
            request,
            run_id,
            trace_id,
            EventName.tool_call_requested,
            "tool",
            FILE_WRITE_TOOL_ID,
            tool_request.requested_action,
            "requested",
            tool_call_ref=FILE_WRITE_TOOL_ID,
        )
        tool_decision = broker.evaluate_request(tool_request, consent_ledger, contract, context_pack)
        if tool_decision.status in {
            ToolDecisionStatus.denied,
            ToolDecisionStatus.approval_required,
            ToolDecisionStatus.blocked_by_foundation_gate,
        }:
            status = KernelTaskStatus.approval_required if tool_decision.status == ToolDecisionStatus.approval_required else KernelTaskStatus.denied
            return self._fail_with_receipt(
                request,
                run_id,
                trace_id,
                status,
                tool_decision.safe_message,
                tool_decision.reason_codes,
                tool_decision=tool_decision,
                consent_decision=consent_decision,
            )

        proposal = self._build_file_write_proposal(request, run_id)
        manager = self._file_manager(request.workspace_root)
        write_decision = manager.propose_write(proposal)
        if not write_decision.allowed:
            return self._fail_with_receipt(
                request,
                run_id,
                trace_id,
                KernelTaskStatus.blocked,
                write_decision.safe_message,
                write_decision.reason_codes,
                tool_decision=tool_decision,
                consent_decision=consent_decision,
                write_decision=write_decision,
                redactions=write_decision.redactions_applied,
            )

        self._append_event(
            request,
            run_id,
            trace_id,
            EventName.file_change_proposed,
            "file",
            request.target_path or "file",
            "propose_write",
            "proposed",
            tool_call_ref=request.target_path,
            evidence_refs=[request.target_path or "file"],
        )

        if request.dry_run:
            return self._finish(
                request,
                run_id,
                trace_id,
                KernelTaskStatus.dry_run,
                "Kernel dry run produced a safe file proposal.",
                True,
                tool_decision=tool_decision,
                consent_decision=consent_decision,
                write_decision=write_decision,
            )

        file_change = manager.apply_write(proposal)
        self._append_event(
            request,
            run_id,
            trace_id,
            EventName.file_change_applied,
            "file",
            file_change.target_path,
            "apply_write",
            "applied",
            tool_call_ref=file_change.target_path,
            rollback_ref=file_change.rollback_ref,
            evidence_refs=[file_change.target_path],
        )

        memory_decision = self._write_memory(request, run_id, file_change.target_path, file_change.rollback_ref)
        self._append_event(
            request,
            run_id,
            trace_id,
            EventName.memory_write_proposed,
            "memory",
            memory_decision.memory_id or "memory_write",
            "write",
            "retained" if memory_decision.allowed else "blocked",
            evidence_refs=[file_change.target_path],
        )

        return self._finish(
            request,
            run_id,
            trace_id,
            KernelTaskStatus.completed,
            "Minimum kernel completed the governed local/dev file mutation.",
            True,
            file_change=file_change,
            rollback_ref=file_change.rollback_ref,
            tool_decision=tool_decision,
            consent_decision=consent_decision,
            write_decision=write_decision,
            memory_decision=memory_decision,
            evidence_refs=[file_change.target_path],
        )

    def _run_rollback(self, request: KernelTaskRequest, run_id: str, trace_id: str) -> KernelTaskResult:
        try:
            manager = self._file_manager(request.workspace_root)
            rollback_plan = manager.get_rollback_plan(request.rollback_ref)
            file_change = manager.rollback(rollback_plan)
            self._append_event(
                request,
                run_id,
                trace_id,
                EventName.file_change_applied,
                "file",
                file_change.target_path,
                "rollback",
                "rolled_back",
                tool_call_ref=file_change.target_path,
                rollback_ref=file_change.rollback_ref,
            )
            return self._finish(
                request,
                run_id,
                trace_id,
                KernelTaskStatus.completed,
                "Rollback restored the previous local/dev workspace snapshot.",
                True,
                file_change=file_change,
                rollback_ref=file_change.rollback_ref,
            )
        except Exception as exc:
            return self._fail_with_receipt(request, run_id, trace_id, KernelTaskStatus.failed, str(exc), ["ROLLBACK_UNAVAILABLE"])

    def _complete_without_write(self, request: KernelTaskRequest, run_id: str, trace_id: str) -> KernelTaskResult:
        return self._finish(request, run_id, trace_id, KernelTaskStatus.completed, "Kernel request validated without side effects.", True)

    def _finish(
        self,
        request: KernelTaskRequest,
        run_id: str,
        trace_id: str,
        status: KernelTaskStatus,
        safe_message: str,
        success: bool,
        *,
        file_change=None,
        rollback_ref: Optional[str] = None,
        tool_decision=None,
        consent_decision=None,
        write_decision=None,
        memory_decision=None,
        evidence_refs: Optional[list[str]] = None,
    ) -> KernelTaskResult:
        evidence_refs = evidence_refs or []
        self._append_event(request, run_id, trace_id, EventName.event_receipt_generated, "receipt", f"rcpt_{run_id}", "generate", "generated")
        final_event = EventName.run_completed if success else EventName.run_failed
        self._append_event(request, run_id, trace_id, final_event, "run", "Kernel run", "complete", status.value)
        event_ids = [event.event_id for event in self.event_ledger.list_events(run_id)]
        world_state = self._build_world_state(request, run_id, status, event_ids, rollback_ref, evidence_refs)
        receipt = generate_kernel_receipt(self.event_ledger, run_id)
        return KernelTaskResult(
            result_id=f"kres_{uuid.uuid4().hex[:10]}",
            run_id=run_id,
            success=success,
            status=status,
            safe_message=safe_message,
            file_change=file_change,
            write_decision=write_decision,
            tool_decision=tool_decision,
            consent_decision=consent_decision,
            memory_decision=memory_decision,
            world_state=world_state,
            receipt=receipt,
            rollback_ref=rollback_ref,
            evidence_refs=evidence_refs,
            event_ids=event_ids,
        )

    def _fail_with_receipt(
        self,
        request: KernelTaskRequest,
        run_id: str,
        trace_id: str,
        status: KernelTaskStatus,
        safe_message: str,
        errors: list[str],
        *,
        tool_decision=None,
        consent_decision=None,
        write_decision=None,
        redactions: Optional[list[str]] = None,
    ) -> KernelTaskResult:
        self._append_event(request, run_id, trace_id, EventName.run_failed, "run", "Kernel run", "fail", status.value, severity="warning")
        self._append_event(request, run_id, trace_id, EventName.event_receipt_generated, "receipt", f"rcpt_{run_id}", "generate", "generated")
        event_ids = [event.event_id for event in self.event_ledger.list_events(run_id)]
        receipt = generate_kernel_receipt(self.event_ledger, run_id)
        return KernelTaskResult(
            result_id=f"kres_{uuid.uuid4().hex[:10]}",
            run_id=run_id,
            success=False,
            status=status,
            safe_message=safe_message,
            write_decision=write_decision,
            tool_decision=tool_decision,
            consent_decision=consent_decision,
            receipt=receipt,
            event_ids=event_ids,
            redactions_applied=redactions or [],
            errors=errors,
        )

    def _synthetic_failure(
        self,
        run_id: str,
        status: KernelTaskStatus,
        safe_message: str,
        errors: list[str],
        redactions: Optional[list[str]] = None,
    ) -> KernelTaskResult:
        return KernelTaskResult(
            result_id=f"kres_{uuid.uuid4().hex[:10]}",
            run_id=run_id,
            success=False,
            status=status,
            safe_message=safe_message,
            errors=errors,
            redactions_applied=redactions or [],
        )

    def _append_event(
        self,
        request: KernelTaskRequest,
        run_id: str,
        trace_id: str,
        event_name: EventName,
        event_type: str,
        subject: str,
        action: str,
        outcome: str,
        *,
        severity: str = "info",
        tool_call_ref: Optional[str] = None,
        rollback_ref: Optional[str] = None,
        evidence_refs: Optional[list[str]] = None,
    ) -> EventLedgerEvent:
        event = EventLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            event_name=event_name,
            run_id=run_id,
            trace_id=trace_id,
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            correlation_id=request.request_id,
            actor_context=request.actor_context,
            temporal_context=TemporalContext(freshness_class=FreshnessClass.near_real_time, staleness_policy=StalenessPolicy.unknown),
            data_classification=DataClassification(
                classification=ClassificationValue(request.data_classification.value),
                source="kernel_request",
                requires_consent=True,
                requires_redaction=False,
            ),
            event_source="MinimumKernelRunner",
            subject=subject,
            action=action,
            outcome=outcome,
            status="success" if severity == "info" else "failed",
            severity=severity,
            tool_call_ref=tool_call_ref,
            rollback_ref=rollback_ref,
            evidence_refs=evidence_refs or [],
            metadata={"kernel_task_type": request.task_type.value},
        )
        self.event_ledger.append_event(event)
        return event

    def _build_execution_contract(self, request: KernelTaskRequest, run_id: str) -> ExecutionContract:
        target = request.target_path or request.rollback_ref or "validate_only"
        return ExecutionContract(
            contract_id=f"ec_{run_id}",
            run_id=run_id,
            workspace_id=self._workspace_id(request.workspace_root),
            user_id=request.user_id,
            request_summary=request.user_request[:240],
            user_request=request.user_request,
            goal=f"Perform governed local/dev kernel task: {request.task_type.value}",
            deliverable=f"Local/dev workspace artifact mutation for {target}",
            mode=AgentMode.code,
            task_class=TaskClass.file_modification,
            risk_level=RiskLevel.high,
            autonomy_level=AutonomyLevel.L4_execute_reversible_trusted_action,
            grounding_mode=GroundingMode.local_document,
            acceptance_criteria=[
                "Execution Contract, Context Pack, Consent, Tool Broker, Event Ledger, File Manager, receipt, and rollback are used.",
                "Only an explicit local/dev workspace root may be mutated.",
            ],
            allowed_tools=[FILE_WRITE_TOOL_ID],
            canonical_files_to_update=[request.target_path] if request.target_path else [],
            approval_policy={"approval_required": True, "approval_ref": request.approval_ref},
            rollback_policy={"rollback_required": True},
            event_logging_policy={"required": True},
            idempotency_policy=IdempotencyPolicy(
                idempotency_key=request.idempotency_key or f"idem_{run_id}",
                operation_type=OperationType.file_write,
                retry_class=RetryClass.retry_with_same_idempotency_key,
                attempt_number=1,
                max_attempts=1,
                outcome_status=OutcomeStatus.not_started,
            ),
            actor_context=request.actor_context,
            data_classification=DataClassification(
                classification=ClassificationValue(request.data_classification.value),
                source="kernel_request",
                requires_consent=True,
            ),
            redaction_policy=RedactionPolicy(
                policy_id="kernel_redaction",
                surfaces=[RedactionSurface.event_ledger_payloads, RedactionSurface.receipts, RedactionSurface.memory_snippets],
                actions=[RedactionAction.mask, RedactionAction.store_by_reference],
            ),
            status=ContractStatus.executing,
        )

    def _build_context_pack(self, request: KernelTaskRequest, run_id: str, contract_id: str) -> ContextPack:
        return ContextPack(
            context_pack_id=f"cp_{run_id}",
            run_id=run_id,
            contract_id=contract_id,
            workspace_id=self._workspace_id(request.workspace_root),
            user_id=request.user_id,
            current_user_instruction=request.user_request,
            canonical_file_refs=[request.target_path] if request.target_path else [],
            tool_permissions=[FILE_WRITE_TOOL_ID],
            grounding_policy="local_dev_kernel_sources_only",
            evidence_requirements=["file_ref", "event_ref", "rollback_ref"],
            data_classification=request.data_classification.value,
            active_goal=f"Run {request.task_type.value}",
            tool_policy_summary="Local/dev file mutation must pass Tool Broker before File Manager apply.",
            permission_policy_summary="Consent grant and approval_ref are required for actual mutation.",
            token_budget=2048,
        )

    def _build_consent_ledger(self, request: KernelTaskRequest) -> ConsentLedger:
        ledger = self.consent_ledger or ConsentLedger()
        for grant in request.consent_grants:
            ledger.add_grant(grant)
        return ledger

    def _preview_consent(self, request: KernelTaskRequest, ledger: ConsentLedger):
        return ledger.evaluate(
            ConsentQuery(
                actor_id=request.actor_context.actor_id,
                action=self._permission_action(request.task_type),
                resource=FILE_WRITE_TOOL_ID,
                data_classification=request.data_classification,
                purpose=request.purpose,
                risk_level=PermissionRisk.high,
            )
        )

    def _build_tool_registry(self, workspace_root: str, *, dry_run: bool) -> ToolRegistry:
        registry = self.tool_registry or ToolRegistry()
        if registry.get_tool(FILE_WRITE_TOOL_ID) is None:
            registry.register_tool(
                ToolManifest(
                    tool_id=FILE_WRITE_TOOL_ID,
                    display_name="Local Dev File Write",
                    category=ToolCategory.file,
                    description="Inert policy manifest for LocalFileManager writes in explicit dev workspaces.",
                    execution_mode=ToolExecutionMode.local_dev,
                    risk_level=ToolRiskLevel.medium if dry_run else ToolRiskLevel.high,
                    permissions_required=[ToolPermissionKind.filesystem_write],
                    permission_manifest=ToolPermissionManifest(
                        required_permissions=[ToolPermissionKind.filesystem_write],
                        filesystem_roots=[str(Path(workspace_root).resolve())],
                    ),
                    data_boundaries=[DataBoundary.project_private],
                    requires_consent=True,
                    requires_approval=not dry_run,
                    supports_dry_run=True,
                    supports_rollback=True,
                    idempotency_required=True,
                    capability_flag="local_dev_file_write",
                    owner="core.kernel",
                    source="local",
                    version="0.1.0",
                )
            )
        return registry

    def _build_tool_request(self, request: KernelTaskRequest, run_id: str) -> ToolRequest:
        return ToolRequest(
            request_id=f"tr_{request.request_id}",
            run_id=run_id,
            step_id="kernel_file_write",
            tool_id=FILE_WRITE_TOOL_ID,
            actor_context=request.actor_context,
            requested_action=self._tool_action(request.task_type),
            purpose=request.purpose,
            input_summary=f"{request.task_type.value} for {request.target_path or request.rollback_ref}",
            input_refs=[request.target_path] if request.target_path else [],
            data_classification=request.data_classification,
            idempotency_key=request.idempotency_key,
            approval_ref=request.approval_ref,
            consent_refs=[grant.consent_id for grant in request.consent_grants],
            dry_run_requested=request.dry_run,
        )

    def _build_file_write_proposal(self, request: KernelTaskRequest, run_id: str) -> FileWriteProposal:
        return FileWriteProposal(
            proposal_id=f"fwp_{uuid.uuid4().hex[:10]}",
            run_id=run_id,
            actor_context=request.actor_context,
            target_path=request.target_path or "",
            purpose=request.purpose,
            new_content=request.new_content or "",
            expected_existing_hash=request.expected_existing_hash,
            file_kind=FileKind.artifact,
            sensitivity=FileSensitivity(request.data_classification.value),
            idempotency_key=request.idempotency_key,
            approval_ref=request.approval_ref,
        )

    def _write_memory(self, request: KernelTaskRequest, run_id: str, file_ref: str, rollback_ref: Optional[str]):
        content = (
            f"Recall only: M5 local/dev kernel changed {file_ref}. "
            "Memory is recall only, not authority; canonical files and the Event Ledger outrank it."
        )
        return self.memory_store.write_memory(
            MemoryWriteRequest(
                request_id=f"mwr_{request.request_id}",
                run_id=run_id,
                actor_context=request.actor_context,
                memory_type=MemoryType.artifact_summary,
                scope=MemoryScope.project,
                scope_id=self._workspace_id(request.workspace_root),
                user_id=request.user_id,
                content=content,
                summary=f"Kernel changed {file_ref}",
                tags=["m5", "kernel", *request.tags],
                source_refs=[
                    MemorySourceRef(
                        source_id=file_ref,
                        source_type="file_change",
                        file_ref=file_ref,
                        event_ref=rollback_ref,
                        trust_level="event_ledger_derived",
                    )
                ],
                authority=MemoryAuthority.event_ledger_derived,
                sensitivity=MemorySensitivity.project_private,
                idempotency_key=f"mem_{request.idempotency_key}",
            )
        )

    def _build_world_state(
        self,
        request: KernelTaskRequest,
        run_id: str,
        status: KernelTaskStatus,
        event_ids: list[str],
        rollback_ref: Optional[str],
        evidence_refs: list[str],
    ) -> StructuredWorldState:
        artifact_refs = [request.target_path] if request.target_path else evidence_refs
        step = WorldStateStep(
            step_id="kernel_file_mutation",
            step_type=request.task_type.value,
            tool_or_component_ref=FILE_WRITE_TOOL_ID,
            parameters_ref=request.target_path or request.rollback_ref,
            outcome=status.value,
            artifact_refs=artifact_refs,
            evidence_refs=evidence_refs,
            rollback_ref=rollback_ref,
            event_ids=event_ids,
        )
        now = utc_now()
        return StructuredWorldState(
            world_state_id=f"ws_{run_id}",
            run_id=run_id,
            current_phase=status.value,
            current_step=step.step_id,
            completed_steps=[step],
            active_constraints=["local_dev_only", "no_network", "no_models", "explicit_workspace_root_only"],
            artifact_refs=artifact_refs,
            evidence_refs=evidence_refs,
            rollback_refs=[rollback_ref] if rollback_ref else [],
            last_event_id=event_ids[-1] if event_ids else "none",
            created_at=now,
            updated_at=now,
        )

    def _file_manager(self, workspace_root: str) -> LocalFileManager:
        key = str(Path(workspace_root).resolve())
        if key not in self._file_managers:
            self._file_managers[key] = self.file_manager_factory(key)
        return self._file_managers[key]

    def _workspace_id(self, workspace_root: str) -> str:
        return f"workspace_{uuid.uuid5(uuid.NAMESPACE_URL, str(Path(workspace_root).resolve())).hex[:10]}"

    def _tool_action(self, task_type: KernelTaskType) -> str:
        if task_type == KernelTaskType.create_dev_file:
            return "create"
        if task_type == KernelTaskType.update_dev_file:
            return "update"
        return "write"

    def _permission_action(self, task_type: KernelTaskType) -> PermissionAction:
        if task_type == KernelTaskType.create_dev_file:
            return PermissionAction.create
        if task_type == KernelTaskType.update_dev_file:
            return PermissionAction.update
        return PermissionAction.write
