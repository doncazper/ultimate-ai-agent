from __future__ import annotations

import asyncio
import hashlib
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    DurableRunRecord,
    DurableRunState,
    DurableRunStorageDuplicateError,
    DurableRunTransitionKind,
    DurableRunTransitionRequest,
    DurableRunTransitionStatus,
    apply_durable_run_transition,
    build_durable_run_lifecycle_read_model,
    build_run_progress_read_model,
    build_run_attached_approval_queue_read_model,
    record_run_attached_approval_event,
    run_attached_approval_item_from_grant,
    run_attached_approval_item_from_request,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.observability import (
    build_safe_ref as build_observability_safe_ref,
    classify_duration,
    record_session_event,
)
from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityCallContext,
    CapabilityContract,
    DAGExecutionResult,
    DAGExecutionStatus,
    PlanValidationContext,
    PlanValidationResult,
    TaskDecompositionDurableBinding,
    TaskIntent,
    TaskPlan,
)
from ultimate_ai_agent.core.task_decomposition.decomposer import TaskDecomposer
from ultimate_ai_agent.core.task_decomposition.examples import (
    echo_summary_handler,
    validation_workflow_handler,
)
from ultimate_ai_agent.core.task_decomposition.executor import DAGExecutor
from ultimate_ai_agent.core.task_decomposition.learning import ReflectionStore
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry
from ultimate_ai_agent.core.task_decomposition.validator import PlanValidator
from ultimate_ai_agent.core.time import utc_now


DEFAULT_REGISTRY_PATH = ".uaa/task_decomposition_registry.json"
REGISTRY_SCHEMA_VERSION = "task-decomposition-registry/v1"
APPROVAL_STATE_SCHEMA_VERSION = "task-decomposition-approvals/v1"
AUDIT_SCHEMA_VERSION = "task-decomposition-audit/v1"

SAFE_HANDLER_REFS = {
    "example.echo_summary_handler": echo_summary_handler,
    "example.validation_workflow_handler": validation_workflow_handler,
}


class CapabilityRegistryStoreConfig(BaseModel):
    registry_path: str = DEFAULT_REGISTRY_PATH
    approval_state_path: Optional[str] = None
    audit_path: Optional[str] = None
    durable_run_path: Optional[str] = None
    create_if_missing: bool = True

    model_config = ConfigDict(extra="forbid")


class CapabilityProvenanceRecord(BaseModel):
    source: str = "local_registry"
    imported_by: str = "system"
    review_ref: Optional[str] = None
    signer_ref: Optional[str] = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")


class CapabilitySignatureRecord(BaseModel):
    algorithm: str = "sha256-local-manifest"
    digest: str = Field(..., min_length=1)
    verification_status: str = "tamper_evident_local"

    model_config = ConfigDict(extra="forbid")


class CapabilityRegistryDocumentEntry(BaseModel):
    contract: CapabilityContract
    provenance: CapabilityProvenanceRecord = Field(default_factory=CapabilityProvenanceRecord)
    signature: CapabilitySignatureRecord

    model_config = ConfigDict(extra="forbid")


class CapabilityRegistryDocument(BaseModel):
    schema_version: str = REGISTRY_SCHEMA_VERSION
    capabilities: list[CapabilityRegistryDocumentEntry] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionApprovalState(BaseModel):
    schema_version: str = APPROVAL_STATE_SCHEMA_VERSION
    requests: list[ApprovalRequest] = Field(default_factory=list)
    grants: list[ApprovalGrant] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"td_audit_{uuid.uuid4().hex[:16]}")
    event_type: str = Field(..., min_length=1)
    run_id: str = "task-decomposition-run:local"
    actor_id: str = "local_actor"
    status: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    capability_ids: list[str] = Field(default_factory=list)
    durable_run_ref: Optional[str] = None
    receipt_ref: Optional[str] = None
    replay_ref: Optional[str] = None
    rollback_ref: Optional[str] = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionAuditDocument(BaseModel):
    schema_version: str = AUDIT_SCHEMA_VERSION
    events: list[TaskDecompositionAuditEvent] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionApprovalGrantRequest(BaseModel):
    approval_request_id: str = Field(..., min_length=1)
    approved_by_actor_id: str = Field(..., min_length=1)
    expires_in_s: int = Field(default=3600, ge=60, le=86400)
    approved_actions: Optional[list[str]] = None
    approved_resource_refs: Optional[list[str]] = None

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionApprovalRevokeRequest(BaseModel):
    approval_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1, max_length=300)

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionStatus(BaseModel):
    status: str
    registry_path: str
    capability_count: int
    approval_request_count: int
    approval_grant_count: int
    audit_event_count: int
    safe_handler_refs: list[str]
    execution_modes_allowed: list[str]
    production_authority: bool = False
    unrestricted_external_execution: bool = False

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRateLimiter:
    def __init__(self, max_events: int = 600, window_s: float = 60.0) -> None:
        self.max_events = max_events
        self.window_s = window_s
        self._events: dict[str, list[float]] = {}
        self._lock = threading.RLock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            events = [stamp for stamp in self._events.get(key, []) if now - stamp <= self.window_s]
            if len(events) >= self.max_events:
                raise ValueError("TASK_DECOMPOSITION_RATE_LIMIT_EXCEEDED")
            events.append(now)
            self._events[key] = events


class TaskDecompositionRegisterRequest(BaseModel):
    contract: CapabilityContract
    handler_ref: Optional[str] = None
    persist: bool = True

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRequest(BaseModel):
    raw_request: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TaskPlanValidationRequest(BaseModel):
    plan: TaskPlan
    context: PlanValidationContext = Field(default_factory=PlanValidationContext)

    model_config = ConfigDict(extra="forbid")


class TaskPlanExecutionRequest(BaseModel):
    plan: TaskPlan
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)
    persist_reflections: bool = True
    idempotency_key: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRunRequest(BaseModel):
    raw_request: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)
    persist_reflections: bool = True
    idempotency_key: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TaskCapabilityApprovalRequestPayload(BaseModel):
    capability_id: str = Field(..., min_length=1)
    run_id: str = "task-decomposition-run:local"
    actor_id: str = "local_actor"

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRunResult(BaseModel):
    intent: TaskIntent
    plan: TaskPlan
    validation: PlanValidationResult
    execution: Optional[DAGExecutionResult] = None
    durable_binding: Optional[TaskDecompositionDurableBinding] = None

    model_config = ConfigDict(extra="forbid")


class CapabilityRegistryStore:
    def __init__(self, config: CapabilityRegistryStoreConfig | None = None) -> None:
        self.config = config or CapabilityRegistryStoreConfig()
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        return Path(self.config.registry_path)

    @property
    def approval_state_path(self) -> Path:
        if self.config.approval_state_path:
            return Path(self.config.approval_state_path)
        return self.path.with_suffix(".approvals.json")

    @property
    def audit_path(self) -> Path:
        if self.config.audit_path:
            return Path(self.config.audit_path)
        return self.path.with_suffix(".audit.json")

    @property
    def durable_run_path(self) -> Path:
        if self.config.durable_run_path:
            return Path(self.config.durable_run_path)
        return self.path.with_suffix(".runs.jsonl")

    def load(self) -> CapabilityRegistry:
        registry = CapabilityRegistry()
        if not self.path.exists():
            if not self.config.create_if_missing:
                raise FileNotFoundError(str(self.path))
            return registry
        payload = self._read_json(self.path)
        if isinstance(payload, list):
            registry.import_json(json.dumps(payload))
        elif isinstance(payload, dict) and payload.get("schema_version") == REGISTRY_SCHEMA_VERSION:
            document = CapabilityRegistryDocument.model_validate(payload)
            for entry in document.capabilities:
                self._verify_entry_signature(entry)
                registry.register(entry.contract)
        else:
            raise ValueError("TASK_DECOMPOSITION_REGISTRY_SCHEMA_UNSUPPORTED")
        self._attach_safe_handlers(registry)
        return registry

    def save(self, registry: CapabilityRegistry) -> None:
        entries = [
            self._document_entry(contract)
            for contract in sorted(
                (registry.get(card.id) for card in registry.cards()),
                key=lambda item: item.card.id if item else "",
            )
            if contract is not None
        ]
        document = CapabilityRegistryDocument(capabilities=entries)
        self._write_json(self.path, document.model_dump(mode="json"))

    def export_document(self, registry: CapabilityRegistry) -> CapabilityRegistryDocument:
        entries = [
            self._document_entry(contract)
            for contract in sorted(
                (registry.get(card.id) for card in registry.cards()),
                key=lambda item: item.card.id if item else "",
            )
            if contract is not None
        ]
        return CapabilityRegistryDocument(capabilities=entries)

    def ensure_example_registry(self) -> CapabilityRegistry:
        registry = self.load()
        from ultimate_ai_agent.core.task_decomposition.examples import (
            build_echo_tool_capability,
            build_validation_workflow_capability,
        )

        if registry.get("capability:example-echo-summary") is None:
            registry.register(build_echo_tool_capability(), echo_summary_handler)
        if registry.get("capability:example-validation-workflow") is None:
            registry.register(build_validation_workflow_capability(), validation_workflow_handler)
        self.save(registry)
        return registry

    def _attach_safe_handlers(self, registry: CapabilityRegistry) -> None:
        for card in registry.cards():
            contract = registry.get(card.id)
            if contract and contract.handler_ref in SAFE_HANDLER_REFS:
                registry.register_handler(card.id, SAFE_HANDLER_REFS[contract.handler_ref])

    def load_approval_state(self) -> TaskDecompositionApprovalState:
        if not self.approval_state_path.exists():
            return TaskDecompositionApprovalState()
        return TaskDecompositionApprovalState.model_validate(self._read_json(self.approval_state_path))

    def save_approval_state(self, state: TaskDecompositionApprovalState) -> None:
        self._write_json(self.approval_state_path, state.model_dump(mode="json"))

    def load_audit_events(self) -> list[TaskDecompositionAuditEvent]:
        if not self.audit_path.exists():
            return []
        return TaskDecompositionAuditDocument.model_validate(self._read_json(self.audit_path)).events

    def append_audit_event(self, event: TaskDecompositionAuditEvent) -> None:
        document = TaskDecompositionAuditDocument(events=[*self.load_audit_events(), event])
        self._write_json(self.audit_path, document.model_dump(mode="json"))

    def _document_entry(self, contract: CapabilityContract) -> CapabilityRegistryDocumentEntry:
        provenance = CapabilityProvenanceRecord()
        unsigned = {
            "contract": contract.model_dump(mode="json"),
            "provenance": provenance.model_dump(mode="json"),
        }
        signature = CapabilitySignatureRecord(digest=self._digest(unsigned))
        return CapabilityRegistryDocumentEntry(
            contract=contract,
            provenance=provenance,
            signature=signature,
        )

    def _verify_entry_signature(self, entry: CapabilityRegistryDocumentEntry) -> None:
        expected = self._digest(
            {
                "contract": entry.contract.model_dump(mode="json"),
                "provenance": entry.provenance.model_dump(mode="json"),
            }
        )
        if entry.signature.digest != expected:
            raise ValueError("TASK_DECOMPOSITION_REGISTRY_SIGNATURE_MISMATCH")

    def _digest(self, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def _read_json(self, path: Path) -> Any:
        with self._locked():
            return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Any) -> None:
        with self._locked():
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            temp_path.replace(path)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._lock:
            lock_path = self.path.with_suffix(".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                try:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                except (ImportError, OSError):
                    pass
                try:
                    yield
                finally:
                    try:
                        import fcntl

                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    except (ImportError, OSError):
                        pass


class TaskDecompositionService:
    def __init__(
        self,
        registry_store: CapabilityRegistryStore | None = None,
        registry: CapabilityRegistry | None = None,
        reflection_store: ReflectionStore | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
        rate_limiter: TaskDecompositionRateLimiter | None = None,
    ) -> None:
        self.registry_store = registry_store or CapabilityRegistryStore()
        self.registry = registry or self.registry_store.load()
        self.approval_authority = approval_authority or LocalApprovalAuthority()
        self.registry.approval_authority = self.approval_authority
        self.reflection_store = reflection_store or ReflectionStore()
        self.rate_limiter = rate_limiter or TaskDecompositionRateLimiter()
        self.durable_run_storage = AppendFirstRunStorage(self.registry_store.durable_run_path)
        self.validator = PlanValidator()
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._load_persisted_approval_state()

    @classmethod
    def from_env(cls) -> "TaskDecompositionService":
        path = os.environ.get("UAA_TASK_DECOMPOSITION_REGISTRY", DEFAULT_REGISTRY_PATH)
        return cls(registry_store=CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=path)))

    def latest_durable_run(self, run_id: str) -> DurableRunRecord | None:
        return self.durable_run_storage.latest_run_record(self._durable_run_id(run_id))

    def durable_run_lifecycle(
        self,
        run_id: str,
        *,
        include_receipts: bool = True,
        limit: int = 50,
    ) -> dict[str, Any] | None:
        model = build_durable_run_lifecycle_read_model(
            self.durable_run_storage,
            self._durable_run_id(run_id),
            include_receipts=include_receipts,
            limit=limit,
        )
        if model is None:
            return None
        return model.model_dump(mode="json")

    def durable_run_progress(
        self,
        run_id: str,
        *,
        limit: int = 50,
    ) -> dict[str, Any] | None:
        model = build_run_progress_read_model(
            self.durable_run_storage,
            self._durable_run_id(run_id),
            limit=limit,
        )
        if model is None:
            return None
        return model.model_dump(mode="json")

    def durable_binding(
        self,
        run_id: str,
        *,
        replay_validation_ref: str | None = None,
        duplicate_mutation_denied: bool = False,
    ) -> TaskDecompositionDurableBinding | None:
        record = self.latest_durable_run(run_id)
        if record is None:
            return None
        metadata = dict(record.metadata)
        return TaskDecompositionDurableBinding(
            run_id=record.run_id,
            durable_run_ref=self._durable_run_ref(record.run_id),
            state=record.state.value,
            generation=record.generation,
            audit_refs=list(record.audit_refs),
            receipt_refs=list(record.receipt_refs),
            replay_refs=list(record.replay_refs),
            rollback_refs=list(record.rollback_refs),
            evidence_refs=list(record.evidence_refs),
            approval_refs=list(metadata.get("approval_refs", [])),
            handler_refs=list(metadata.get("handler_refs", [])),
            idempotency_keys_seen=list(record.idempotency_keys_seen),
            restart_refs=list(record.restart_refs),
            replay_validation_ref=replay_validation_ref,
            duplicate_mutation_denied=duplicate_mutation_denied,
            safe_summary=record.safe_summary,
        )

    def record_restart_visibility(
        self,
        run_id: str,
        *,
        restart_ref: str | None = None,
    ) -> TaskDecompositionDurableBinding:
        record = self._ensure_durable_run(
            run_id,
            safe_summary="Task decomposition durable run is visible after restart.",
        )
        safe_restart_ref = restart_ref or self._new_ref("restart", run_id, "visible")
        if record.state == DurableRunState.running:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.recover_after_restart,
                safe_summary="Task decomposition durable run restart recovery was recorded.",
                restart_ref=safe_restart_ref,
            )
        else:
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition durable run restart visibility was recorded.",
                restart_ref=safe_restart_ref,
            )
        binding = self.durable_binding(record.run_id)
        if binding is None:
            raise ValueError("TASK_DECOMPOSITION_DURABLE_BINDING_MISSING")
        return binding

    def validate_replay(self, run_id: str) -> TaskDecompositionDurableBinding:
        record = self._ensure_durable_run(
            run_id,
            safe_summary="Task decomposition durable run replay validation is available.",
        )
        replay_validation_ref = self._new_ref("replay-validation", record.run_id, str(record.generation))
        record = self._append_durable_attachment(
            record,
            safe_summary="Task decomposition durable run replay validation was recorded.",
            replay_ref=replay_validation_ref,
        )
        binding = self.durable_binding(record.run_id, replay_validation_ref=replay_validation_ref)
        if binding is None:
            raise ValueError("TASK_DECOMPOSITION_DURABLE_BINDING_MISSING")
        return binding

    def catalog(self) -> list[dict[str, Any]]:
        return [card.model_dump(mode="json") for card in self.registry.cards()]

    def status(self) -> TaskDecompositionStatus:
        return TaskDecompositionStatus(
            status="ready",
            registry_path=str(self.registry_store.path),
            capability_count=len(self.registry.cards()),
            approval_request_count=len(self._approval_requests),
            approval_grant_count=len(self.approval_authority.list_grants()),
            audit_event_count=len(self.registry_store.load_audit_events()),
            safe_handler_refs=sorted(SAFE_HANDLER_REFS),
            execution_modes_allowed=["python_callable", "agent_as_tool", "workflow"],
        )

    def register(self, request: TaskDecompositionRegisterRequest) -> CapabilityContract:
        self._check_rate_limit("registry")
        if request.handler_ref and request.contract.handler_ref and request.handler_ref != request.contract.handler_ref:
            raise ValueError("TASK_DECOMPOSITION_HANDLER_REF_MISMATCH")
        handler_ref = request.handler_ref or request.contract.handler_ref or ""
        if handler_ref and handler_ref not in SAFE_HANDLER_REFS:
            raise ValueError("TASK_DECOMPOSITION_HANDLER_REF_NOT_ALLOWLISTED")
        handler = SAFE_HANDLER_REFS.get(handler_ref)
        contract_payload = request.contract
        if handler_ref and request.contract.handler_ref != handler_ref:
            contract_payload = request.contract.model_copy(update={"handler_ref": handler_ref})
        contract = self.registry.register(contract_payload, handler)
        if request.persist:
            self.registry_store.save(self.registry)
        self.record_audit_event(
            "capability_registered",
            status="succeeded",
            safe_summary="Capability contract registered in the task decomposition registry.",
            capability_ids=[contract.card.id],
        )
        return contract

    def ensure_examples(self) -> list[dict[str, Any]]:
        self._check_rate_limit("registry")
        self.registry = self.registry_store.ensure_example_registry()
        self.registry.approval_authority = self.approval_authority
        self.record_audit_event(
            "examples_initialized",
            status="succeeded",
            safe_summary="Example task decomposition capabilities are available.",
            capability_ids=[card["id"] for card in self.catalog()],
        )
        return self.catalog()

    def classify(self, request: TaskDecompositionRequest) -> TaskIntent:
        self._check_rate_limit(str(request.context.get("actor_id", "local_actor")))
        intent = TaskDecomposer(self.registry).classify_intent(request.raw_request, request.context)
        self.record_audit_event(
            "intent_classified",
            status="succeeded",
            safe_summary="Task request was classified into a structured intent.",
        )
        return intent

    def decompose(self, request: TaskDecompositionRequest) -> TaskDecompositionRunResult:
        self._check_rate_limit(str(request.context.get("actor_id", "local_actor")))
        decomposer = TaskDecomposer(self.registry, self.validator)
        intent = decomposer.classify_intent(request.raw_request, request.context)
        candidates = decomposer.retrieve_capabilities(intent)
        strategy = decomposer.select_strategy(intent, candidates)
        plan = decomposer.create_plan(intent, candidates, strategy)
        validation = decomposer.validate_plan(plan)
        record = self._ensure_durable_run(
            plan.plan_id,
            safe_summary="Task decomposition durable run was created for a validated plan.",
            handler_refs=self._handler_refs_for_plan(plan),
        )
        self._deny_duplicate_idempotency(record, request.idempotency_key, "decompose")
        if validation.valid:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.mark_ready,
                safe_summary="Task decomposition durable run is ready for reviewed execution.",
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "decompose", request.idempotency_key),
                handler_refs=self._handler_refs_for_plan(plan),
            )
        else:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.fail,
                safe_summary="Task decomposition durable run captured a validation failure.",
                failure_ref=self._new_ref("failure", record.run_id, "decompose"),
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "decompose", request.idempotency_key),
                handler_refs=self._handler_refs_for_plan(plan),
            )
        binding = self.durable_binding(record.run_id)
        self.record_audit_event(
            "plan_decomposed",
            run_id=plan.plan_id,
            status="succeeded" if validation.valid else "blocked",
            safe_summary="Task request was decomposed and validated.",
            reason_codes=validation.reason_codes,
            capability_ids=[node.selected_capability for node in plan.nodes if node.selected_capability],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return TaskDecompositionRunResult(intent=intent, plan=plan, validation=validation, durable_binding=binding)

    def validate_plan(self, request: TaskPlanValidationRequest) -> PlanValidationResult:
        self._check_rate_limit(request.context.call_context.actor_id)
        validation = self.validator.validate(request.plan, self.registry, request.context)
        record = self._ensure_durable_run(
            request.plan.plan_id,
            safe_summary="Task decomposition durable run was attached to plan validation.",
            handler_refs=self._handler_refs_for_plan(request.plan),
        )
        if validation.valid and record.state == DurableRunState.created:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.mark_ready,
                safe_summary="Task decomposition durable run is ready after plan validation.",
                handler_refs=self._handler_refs_for_plan(request.plan),
            )
        else:
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition durable plan validation was recorded.",
                handler_refs=self._handler_refs_for_plan(request.plan),
            )
        binding = self.durable_binding(record.run_id)
        self.record_audit_event(
            "plan_validated",
            run_id=request.plan.plan_id,
            status="succeeded" if validation.valid else "blocked",
            safe_summary="Task plan validation completed.",
            reason_codes=validation.reason_codes,
            capability_ids=[node.selected_capability for node in request.plan.nodes if node.selected_capability],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return validation

    def build_approval_request(self, request: TaskCapabilityApprovalRequestPayload) -> ApprovalRequest:
        self._check_rate_limit(request.actor_id)
        contract = self.registry.get(request.capability_id)
        if contract is None:
            raise KeyError("CAPABILITY_NOT_REGISTERED")
        durable_run_id = self._durable_run_id(request.run_id)
        approval_request_id = f"areq_{durable_run_id}_{request.capability_id}".replace(":", "_")
        if approval_request_id in self._approval_requests:
            return self._approval_requests[approval_request_id]
        approval_request = ApprovalRequest(
            approval_request_id=approval_request_id,
            run_id=durable_run_id,
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=request.capability_id,
            actor_context=ActorContext(
                actor_type=ActorType.orchestrator,
                actor_id=request.actor_id,
                authority_source=AuthoritySource.explicit_user_request,
            ),
            requested_action="invoke_capability",
            purpose=f"Approve local task decomposition capability {request.capability_id}.",
            risk_level=ApprovalRiskLevel(contract.card.risk_level.value),
            data_classification=self._data_classification(contract.data_sensitivity.value),
            resource_refs=[request.capability_id],
            tool_id=request.capability_id,
        )
        self.approval_authority.create_request(approval_request)
        self._approval_requests[approval_request.approval_request_id] = approval_request
        durable_attached = False
        try:
            record = self._ensure_durable_run(
                durable_run_id,
                safe_summary="Task decomposition durable run was attached to an approval request.",
            )
            approval_refs = [self._safe_external_ref("approval-request", approval_request.approval_request_id)]
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition approval request was bound to durable run truth.",
                idempotency_key=self._safe_ref(
                    "idempotency",
                    durable_run_id,
                    "approval-request-attachment",
                    approval_request.approval_request_id,
                ),
                approval_refs=approval_refs,
            )
            durable_attached = True
            self._record_approval_state_after_durable_attachment(
                record.run_id,
                run_attached_approval_item_from_request(
                    approval_request,
                    durable_attachment_status="attached",
                ),
                operation="approval-required",
            )
        except Exception:
            if not durable_attached:
                self._approval_requests.pop(approval_request.approval_request_id, None)
                self.approval_authority._requests.pop(approval_request.approval_request_id, None)
            raise
        binding = self.durable_binding(record.run_id)
        self.record_audit_event(
            "approval_requested",
            run_id=request.run_id,
            actor_id=request.actor_id,
            status="awaiting_approval",
            safe_summary="Capability approval request was created.",
            capability_ids=[request.capability_id],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return approval_request

    def grant_approval(self, request: TaskDecompositionApprovalGrantRequest) -> ApprovalGrant:
        self._check_rate_limit(request.approved_by_actor_id)
        if request.approval_request_id not in self._approval_requests:
            raise KeyError("APPROVAL_REQUEST_NOT_FOUND")
        grant = self.approval_authority.grant(
            request.approval_request_id,
            approved_by_actor_id=request.approved_by_actor_id,
            expires_at=utc_now() + timedelta(seconds=request.expires_in_s),
            approved_actions=request.approved_actions,
            approved_resource_refs=request.approved_resource_refs,
        )
        durable_attached = False
        try:
            record = self._ensure_durable_run(
                grant.run_id,
                safe_summary="Task decomposition durable run was attached to an approval grant.",
            )
            approval_refs = [self._safe_external_ref("approval", grant.approval_ref)]
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition approval grant was bound to durable run truth.",
                idempotency_key=self._safe_ref(
                    "idempotency",
                    grant.run_id,
                    "approval-grant-attachment",
                    grant.approval_ref,
                ),
                approval_refs=approval_refs,
            )
            durable_attached = True
            self._record_approval_state_after_durable_attachment(
                record.run_id,
                run_attached_approval_item_from_grant(
                    grant,
                    durable_attachment_status="attached",
                ),
                operation="approval-attached",
            )
        except Exception:
            if not durable_attached:
                self.approval_authority._grants.pop(grant.approval_ref, None)
            raise
        binding = self.durable_binding(record.run_id)
        self.record_audit_event(
            "approval_granted",
            run_id=grant.run_id,
            actor_id=grant.granted_to_actor_id,
            status="granted",
            safe_summary="Capability approval grant was captured for exact scoped validation.",
            capability_ids=[grant.subject_id],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return grant

    def revoke_approval(self, request: TaskDecompositionApprovalRevokeRequest) -> ApprovalGrant:
        self._check_rate_limit("approval_revocation")
        previous_grant = self.approval_authority.get_grant(request.approval_ref)
        revoked = self.approval_authority.revoke(request.approval_ref, request.reason)
        durable_attached = False
        try:
            record = self._ensure_durable_run(
                revoked.run_id,
                safe_summary="Task decomposition durable run was attached to approval revocation.",
            )
            approval_refs = [self._safe_external_ref("approval", revoked.approval_ref)]
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition approval revocation was bound to durable run truth.",
                idempotency_key=self._safe_ref(
                    "idempotency",
                    revoked.run_id,
                    "approval-revocation-attachment",
                    revoked.approval_ref,
                ),
                approval_refs=approval_refs,
            )
            durable_attached = True
            self._record_approval_state_after_durable_attachment(
                record.run_id,
                run_attached_approval_item_from_grant(
                    revoked,
                    durable_attachment_status="attached",
                ),
                operation="approval-revoked",
            )
        except Exception:
            if not durable_attached and previous_grant is not None:
                self.approval_authority._grants[previous_grant.approval_ref] = previous_grant
            raise
        binding = self.durable_binding(record.run_id)
        self.record_audit_event(
            "approval_revoked",
            run_id=revoked.run_id,
            actor_id=revoked.granted_to_actor_id,
            status="revoked",
            safe_summary="Capability approval grant was revoked.",
            capability_ids=[revoked.subject_id],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return revoked

    def approval_queue(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "requests": [request.model_dump(mode="json") for request in self._approval_requests.values()],
            "grants": [grant.model_dump(mode="json") for grant in self.approval_authority.list_grants()],
        }

    def run_attached_approval_queue(
        self,
        run_id: str | None = None,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        durable_run_id = self._durable_run_id(run_id) if run_id else None
        model = build_run_attached_approval_queue_read_model(
            approval_requests=self._approval_requests.values(),
            approval_grants=self.approval_authority.list_grants(durable_run_id),
            durable_run_storage=self.durable_run_storage,
            run_ref=durable_run_id,
            limit=limit,
        )
        return model.model_dump(mode="json")

    def audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        events = self.registry_store.load_audit_events()
        return [event.model_dump(mode="json") for event in events[-limit:]]

    def metrics(self) -> dict[str, Any]:
        return {
            "capabilities": {
                key: value.model_dump(mode="json")
                for key, value in self.registry.metrics().items()
            },
            "reflections": [record.model_dump(mode="json") for record in self.reflection_store.reflections()],
            "promotion_candidates": [
                candidate.model_dump(mode="json")
                for candidate in self.reflection_store.promotion_candidates()
            ],
            "audit_event_count": len(self.registry_store.load_audit_events()),
        }

    def export_registry_document(self) -> dict[str, Any]:
        document = self.registry_store.export_document(self.registry)
        return document.model_dump(mode="json")

    async def execute_plan(self, request: TaskPlanExecutionRequest) -> DAGExecutionResult:
        self._check_rate_limit(request.call_context.actor_id)
        if request.approval_grants:
            raise ValueError("TASK_DECOMPOSITION_INLINE_APPROVAL_GRANTS_DENIED")
        self.registry.approval_authority = self.approval_authority
        call_context = request.call_context.model_copy(update={"approved_capability_ids": []})
        record = self._ensure_durable_run(
            request.plan.plan_id,
            safe_summary="Task decomposition durable run was attached to plan execution.",
            approval_refs=self._approval_refs_for_context(call_context),
            handler_refs=self._handler_refs_for_plan(request.plan),
        )
        self._deny_duplicate_idempotency(record, request.idempotency_key, "execute")
        record = self._prepare_durable_run_for_execution(
            record,
            actor_id=call_context.actor_id,
            idempotency_key=request.idempotency_key,
            approval_refs=self._approval_refs_for_context(call_context),
            handler_refs=self._handler_refs_for_plan(request.plan),
        )
        execution_binding = self.durable_binding(record.run_id)
        record_session_event(
            fail_closed=False,
            session_id="task-decomposition-session:local",
            run_id=_safe_task_run_id(request.plan.plan_id),
            trace_id=build_observability_safe_ref("task-trace", request.plan.plan_id),
            span_id=build_observability_safe_ref("task-plan-execution", request.plan.plan_id),
            correlation_id=build_observability_safe_ref("task-correlation", request.plan.plan_id),
            service="task_decomposition",
            surface="task_decomposition",
            event_type="task.plan.execution_started",
            lifecycle_state="started",
            status="started",
            severity="info",
            safe_summary="Task plan execution started as a redacted summary.",
            reason_codes=["TASK_PLAN_EXECUTION_STARTED"],
            evidence_refs=list(execution_binding.evidence_refs if execution_binding else []),
            receipt_refs=list(execution_binding.receipt_refs if execution_binding else []),
            redaction_summary={
                "status": "summary_only",
                "input_values_stored": False,
                "output_values_stored": False,
            },
            metadata={
                "node_count": len(request.plan.nodes),
                "approval_ref_count": len(self._approval_refs_for_context(call_context)),
            },
        )
        result = await DAGExecutor(self.registry, self.validator).execute(request.plan, call_context)
        if request.persist_reflections:
            self.reflection_store.record_execution(request.plan, result)
        record = self._finish_durable_run_for_execution(
            record,
            result,
            approval_refs=self._approval_refs_for_context(call_context),
            handler_refs=self._handler_refs_for_plan(request.plan),
        )
        binding = self.durable_binding(record.run_id)
        result = result.model_copy(update={"durable_binding": binding})
        self._record_task_node_session_events(result, binding)
        self.record_audit_event(
            "plan_executed",
            run_id=request.plan.plan_id,
            actor_id=call_context.actor_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            safe_summary=result.safe_summary,
            reason_codes=result.reason_codes,
            capability_ids=[node.selected_capability for node in request.plan.nodes if node.selected_capability],
            durable_run_ref=binding.durable_run_ref if binding else None,
            receipt_ref=self._latest_ref(binding.receipt_refs if binding else []),
            replay_ref=self._latest_ref(binding.replay_refs if binding else []),
            rollback_ref=self._latest_ref(binding.rollback_refs if binding else []),
        )
        return result

    def execute_plan_sync(self, request: TaskPlanExecutionRequest) -> DAGExecutionResult:
        return asyncio.run(self.execute_plan(request))

    async def run(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        decomposed = self.decompose(
            TaskDecompositionRequest(
                raw_request=request.raw_request,
                context=request.context,
                idempotency_key=request.idempotency_key,
            )
        )
        if not decomposed.validation.valid:
            return decomposed
        execution = await self.execute_plan(
            TaskPlanExecutionRequest(
                plan=decomposed.plan,
                call_context=request.call_context,
                approval_grants=request.approval_grants,
                persist_reflections=request.persist_reflections,
                idempotency_key=request.idempotency_key,
            )
        )
        return decomposed.model_copy(update={"execution": execution, "durable_binding": execution.durable_binding})

    def run_sync(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        return asyncio.run(self.run(request))

    def _ensure_durable_run(
        self,
        run_id: str,
        *,
        safe_summary: str,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
    ) -> DurableRunRecord:
        durable_run_id = self._durable_run_id(run_id)
        existing = self.durable_run_storage.latest_run_record(durable_run_id)
        if existing is not None:
            return existing

        record = DurableRunRecord(
            run_id=durable_run_id,
            source_ref=self._safe_ref("task-decomposition-source", durable_run_id),
            state=DurableRunState.created,
            safe_summary=safe_summary,
            metadata=self._metadata_payload(approval_refs=approval_refs, handler_refs=handler_refs),
        )
        return self._append_durable_snapshot(
            record,
            idempotency_key=self._new_ref("idempotency", durable_run_id, "create"),
            audit_ref=self._new_ref("audit", durable_run_id, "create"),
            receipt_ref=self._new_ref("receipt", durable_run_id, "create"),
            replay_ref=self._new_ref("replay", durable_run_id, "create"),
            rollback_ref=self._new_ref("rollback", durable_run_id, "create"),
            evidence_refs=[self._new_ref("evidence", durable_run_id, "create")],
            safe_summary=safe_summary,
        )

    def _prepare_durable_run_for_execution(
        self,
        record: DurableRunRecord,
        *,
        actor_id: str,
        idempotency_key: str | None,
        approval_refs: list[str],
        handler_refs: list[str],
    ) -> DurableRunRecord:
        if record.state == DurableRunState.created:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.mark_ready,
                safe_summary="Task decomposition durable run is ready for plan execution.",
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        if record.state in {DurableRunState.blocked, DurableRunState.failed}:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.retry,
                safe_summary="Task decomposition durable run retry was recorded for reviewed execution.",
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        if record.state == DurableRunState.retry_pending:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.start,
                safe_summary="Task decomposition durable run moved from retry into reviewed execution.",
                actor_id=actor_id,
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "execute", idempotency_key),
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        elif record.state == DurableRunState.ready:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.start,
                safe_summary="Task decomposition durable run started a reviewed local execution step.",
                actor_id=actor_id,
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "execute", idempotency_key),
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        elif record.state == DurableRunState.paused:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.resume,
                safe_summary="Task decomposition durable run resumed for reviewed local execution.",
                actor_id=actor_id,
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "execute", idempotency_key),
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        elif record.state == DurableRunState.restart_recovery:
            record = self._transition_durable_run(
                record,
                DurableRunTransitionKind.start,
                safe_summary="Task decomposition durable run resumed after restart recovery.",
                actor_id=actor_id,
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "execute", idempotency_key),
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        else:
            record = self._append_durable_attachment(
                record,
                safe_summary="Task decomposition durable execution attempt was recorded without changing run state.",
                idempotency_key=self._explicit_idempotency_ref(record.run_id, "execute", idempotency_key),
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        return record

    def _finish_durable_run_for_execution(
        self,
        record: DurableRunRecord,
        result: DAGExecutionResult,
        *,
        approval_refs: list[str],
        handler_refs: list[str],
    ) -> DurableRunRecord:
        if result.status == DAGExecutionStatus.succeeded:
            return self._transition_durable_run(
                record,
                DurableRunTransitionKind.succeed,
                safe_summary="Task decomposition durable run completed successfully.",
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        if result.status == DAGExecutionStatus.awaiting_approval:
            return self._transition_durable_run(
                record,
                DurableRunTransitionKind.block,
                safe_summary="Task decomposition durable run is blocked on human approval.",
                approval_refs=approval_refs,
                handler_refs=handler_refs,
            )
        return self._transition_durable_run(
            record,
            DurableRunTransitionKind.fail,
            safe_summary="Task decomposition durable run captured a safe failure state.",
            failure_ref=self._new_ref("failure", record.run_id, "execution"),
            approval_refs=approval_refs,
            handler_refs=handler_refs,
        )

    def _transition_durable_run(
        self,
        record: DurableRunRecord,
        kind: DurableRunTransitionKind,
        *,
        safe_summary: str,
        actor_id: str = "local_actor",
        idempotency_key: str | None = None,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
        failure_ref: str | None = None,
        restart_ref: str | None = None,
    ) -> DurableRunRecord:
        effective_idempotency_key = idempotency_key or self._new_ref("idempotency", record.run_id, kind.value)
        transition_id = self._new_ref("durable-transition", record.run_id, kind.value)
        audit_ref = self._new_ref("audit", record.run_id, kind.value)
        receipt_ref = self._new_ref("receipt", record.run_id, kind.value)
        replay_ref = self._new_ref("replay", record.run_id, kind.value)
        rollback_ref = self._new_ref("rollback", record.run_id, kind.value)
        evidence_ref = self._new_ref("evidence", record.run_id, kind.value)
        request = DurableRunTransitionRequest(
            run_id=record.run_id,
            transition_id=transition_id,
            transition_kind=kind,
            idempotency_key=effective_idempotency_key,
            actor_ref=self._safe_external_ref("actor", actor_id),
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            replay_ref=replay_ref,
            rollback_ref=rollback_ref,
            safe_summary=safe_summary,
            evidence_refs=[evidence_ref],
            failure_ref=failure_ref,
            restart_ref=restart_ref,
            metadata_refs=[self._safe_ref("metadata", record.run_id, kind.value)],
            metadata=self._metadata_payload(approval_refs=approval_refs, handler_refs=handler_refs),
        )
        transition = apply_durable_run_transition(record, request)
        if transition.decision.status == DurableRunTransitionStatus.idempotent_replay:
            return record
        if transition.decision.status == DurableRunTransitionStatus.denied:
            if any("IDEMPOTENCY" in reason for reason in transition.decision.reason_codes):
                raise ValueError("TASK_DECOMPOSITION_IDEMPOTENCY_REPLAY_DENIED")
            return self._append_durable_attachment(
                record,
                safe_summary="Task decomposition durable state change was denied safely and recorded.",
                approval_refs=approval_refs,
                handler_refs=handler_refs,
                failure_ref=failure_ref,
                restart_ref=restart_ref,
            )

        next_record = self._merge_record_metadata(
            transition.record,
            approval_refs=approval_refs,
            handler_refs=handler_refs,
        )
        return self._append_durable_snapshot(
            next_record,
            idempotency_key=effective_idempotency_key,
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            replay_ref=replay_ref,
            rollback_ref=rollback_ref,
            evidence_refs=[evidence_ref],
            safe_summary=safe_summary,
        )

    def _append_durable_attachment(
        self,
        record: DurableRunRecord,
        *,
        safe_summary: str,
        idempotency_key: str | None = None,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
        failure_ref: str | None = None,
        restart_ref: str | None = None,
        replay_ref: str | None = None,
    ) -> DurableRunRecord:
        effective_idempotency_key = idempotency_key or self._new_ref("idempotency", record.run_id, "attachment")
        audit_ref = self._new_ref("audit", record.run_id, "attachment")
        receipt_ref = self._new_ref("receipt", record.run_id, "attachment")
        effective_replay_ref = replay_ref or self._new_ref("replay", record.run_id, "attachment")
        rollback_ref = self._new_ref("rollback", record.run_id, "attachment")
        evidence_ref = self._new_ref("evidence", record.run_id, "attachment")
        next_record = record.model_copy(
            update={
                "generation": record.generation + 1,
                "safe_summary": safe_summary,
                "idempotency_keys_seen": self._append_unique(
                    record.idempotency_keys_seen,
                    effective_idempotency_key,
                ),
                "audit_refs": self._append_unique(record.audit_refs, audit_ref),
                "receipt_refs": self._append_unique(record.receipt_refs, receipt_ref),
                "replay_refs": self._append_unique(record.replay_refs, effective_replay_ref),
                "rollback_refs": self._append_unique(record.rollback_refs, rollback_ref),
                "evidence_refs": self._append_unique(record.evidence_refs, evidence_ref),
                "failure_refs": self._append_unique(record.failure_refs, failure_ref),
                "restart_refs": self._append_unique(record.restart_refs, restart_ref),
                "metadata": self._merge_metadata(record.metadata, approval_refs=approval_refs, handler_refs=handler_refs),
            }
        )
        next_record = DurableRunRecord.model_validate(next_record.model_dump())
        return self._append_durable_snapshot(
            next_record,
            idempotency_key=effective_idempotency_key,
            audit_ref=audit_ref,
            receipt_ref=receipt_ref,
            replay_ref=effective_replay_ref,
            rollback_ref=rollback_ref,
            evidence_refs=[evidence_ref],
            safe_summary=safe_summary,
        )

    def _record_run_attached_approval_event(
        self,
        run_id: str,
        item: Any,
        *,
        operation: str,
    ) -> None:
        event_seed = self._safe_ref("run-approval-event", run_id, operation, item.item_ref)
        try:
            record_run_attached_approval_event(
                self.durable_run_storage,
                item,
                idempotency_key_ref=self._safe_ref("idempotency", event_seed),
                audit_ref=self._safe_ref("audit", event_seed),
                receipt_ref=self._safe_ref("receipt", event_seed),
                rollback_ref=self._safe_ref("rollback", event_seed),
            )
        except DurableRunStorageDuplicateError:
            return

    def _record_approval_state_after_durable_attachment(
        self,
        run_id: str,
        item: Any,
        *,
        operation: str,
    ) -> None:
        event_error: Exception | None = None
        save_error: Exception | None = None
        try:
            self._record_run_attached_approval_event(run_id, item, operation=operation)
        except Exception as exc:
            event_error = exc
        try:
            self._save_persisted_approval_state()
        except Exception as exc:
            save_error = exc
        if event_error is not None:
            raise event_error
        if save_error is not None:
            raise save_error

    def _append_durable_snapshot(
        self,
        record: DurableRunRecord,
        *,
        idempotency_key: str,
        audit_ref: str,
        receipt_ref: str,
        replay_ref: str,
        rollback_ref: str,
        evidence_refs: list[str],
        safe_summary: str,
    ) -> DurableRunRecord:
        try:
            self.durable_run_storage.append_run_record(
                record,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                receipt_ref=receipt_ref,
                rollback_ref=rollback_ref,
                safe_summary=safe_summary,
                evidence_refs=evidence_refs,
            )
            self.durable_run_storage.append_receipt_summary(
                run_id=record.run_id,
                receipt_ref=receipt_ref,
                idempotency_key=self._safe_ref("idempotency", idempotency_key, "receipt"),
                audit_ref=audit_ref,
                rollback_ref=rollback_ref,
                safe_summary="Task decomposition durable receipt summary recorded.",
                receipt_summary={
                    "run_id": record.run_id,
                    "state": record.state.value,
                    "audit_ref": audit_ref,
                    "receipt_ref": receipt_ref,
                    "replay_ref": replay_ref,
                    "rollback_ref": rollback_ref,
                    "safe_summary": safe_summary,
                    "no_runtime_authority": True,
                    "safe_ref_only": True,
                },
                evidence_refs=evidence_refs,
            )
        except DurableRunStorageDuplicateError as exc:
            raise ValueError("TASK_DECOMPOSITION_IDEMPOTENCY_REPLAY_DENIED") from exc
        latest = self.durable_run_storage.latest_run_record(record.run_id)
        if latest is None:
            raise ValueError("TASK_DECOMPOSITION_DURABLE_RUN_RECORD_MISSING")
        return latest

    def _deny_duplicate_idempotency(self, record: DurableRunRecord, idempotency_key: str | None, operation: str) -> None:
        if not idempotency_key:
            return
        safe_key = self._explicit_idempotency_ref(record.run_id, operation, idempotency_key)
        if safe_key in record.idempotency_keys_seen:
            raise ValueError("TASK_DECOMPOSITION_IDEMPOTENCY_REPLAY_DENIED")

    def _explicit_idempotency_ref(self, run_id: str, operation: str, idempotency_key: str | None) -> str | None:
        if not idempotency_key:
            return None
        return self._safe_ref("idempotency", run_id, operation, idempotency_key)

    def _durable_run_id(self, run_id: str) -> str:
        candidate = run_id or "task-decomposition-run:local"
        try:
            validate_execution_ref(candidate, "run_id")
            return candidate
        except ValueError:
            return self._safe_ref("task-decomposition-run", candidate)

    def _durable_run_ref(self, run_id: str) -> str:
        return self._safe_ref("durable-run", run_id)

    def _approval_refs_for_context(self, context: CapabilityCallContext) -> list[str]:
        refs = self._approval_refs_for_run(context.run_id)
        refs.extend(self._safe_external_ref("approval", ref) for ref in context.approval_refs.values())
        return self._append_unique([], *refs)

    def _approval_refs_for_run(self, run_id: str) -> list[str]:
        return [
            self._safe_external_ref("approval", grant.approval_ref)
            for grant in sorted(self.approval_authority.list_grants(run_id), key=lambda item: item.approval_ref)
        ]

    def _handler_refs_for_plan(self, plan: TaskPlan) -> list[str]:
        refs: list[str] = []
        for node in plan.nodes:
            if not node.selected_capability:
                continue
            contract = self.registry.get(node.selected_capability)
            if contract and contract.handler_ref:
                refs.append(self._safe_external_ref("handler", contract.handler_ref))
        return self._append_unique([], *refs)

    def _merge_record_metadata(
        self,
        record: DurableRunRecord,
        *,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
    ) -> DurableRunRecord:
        next_record = record.model_copy(
            update={"metadata": self._merge_metadata(record.metadata, approval_refs=approval_refs, handler_refs=handler_refs)}
        )
        return DurableRunRecord.model_validate(next_record.model_dump())

    def _metadata_payload(
        self,
        *,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
    ) -> dict[str, list[str]]:
        return self._merge_metadata({}, approval_refs=approval_refs, handler_refs=handler_refs)

    def _merge_metadata(
        self,
        metadata: dict[str, Any],
        *,
        approval_refs: list[str] | None = None,
        handler_refs: list[str] | None = None,
    ) -> dict[str, list[str]]:
        return {
            "approval_refs": self._append_unique(list(metadata.get("approval_refs", [])), *(approval_refs or [])),
            "handler_refs": self._append_unique(list(metadata.get("handler_refs", [])), *(handler_refs or [])),
        }

    def _safe_external_ref(self, prefix: str, value: str) -> str:
        return self._safe_ref(prefix, value)

    def _new_ref(self, prefix: str, *parts: str) -> str:
        return self._safe_ref(prefix, *parts, uuid.uuid4().hex)

    def _safe_ref(self, prefix: str, *parts: str) -> str:
        seed = "|".join(str(part) for part in parts if part is not None)
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
        ref = f"{prefix}:{digest}"
        validate_execution_ref(ref, "safe_ref")
        return ref

    def _append_unique(self, existing: list[str], *refs: str | None) -> list[str]:
        updated = list(existing)
        for ref in refs:
            if ref and ref not in updated:
                updated.append(ref)
        return updated

    def _latest_ref(self, refs: list[str]) -> str | None:
        return refs[-1] if refs else None

    def _check_rate_limit(self, key: str) -> None:
        self.rate_limiter.check(key)

    def _load_persisted_approval_state(self) -> None:
        state = self.registry_store.load_approval_state()
        for request in state.requests:
            self.approval_authority.create_request(request)
            self._approval_requests[request.approval_request_id] = request
        for grant in state.grants:
            self.approval_authority.load_grant_for_validation(grant)

    def _save_persisted_approval_state(self) -> None:
        self.registry_store.save_approval_state(
            TaskDecompositionApprovalState(
                requests=list(self._approval_requests.values()),
                grants=self.approval_authority.list_grants(),
            )
        )

    def record_audit_event(
        self,
        event_type: str,
        *,
        run_id: str = "task-decomposition-run:local",
        actor_id: str = "local_actor",
        status: str,
        safe_summary: str,
        reason_codes: list[str] | None = None,
        capability_ids: list[str | None] | None = None,
        durable_run_ref: str | None = None,
        receipt_ref: str | None = None,
        replay_ref: str | None = None,
        rollback_ref: str | None = None,
    ) -> TaskDecompositionAuditEvent:
        event = TaskDecompositionAuditEvent(
            event_type=event_type,
            run_id=run_id,
            actor_id=actor_id,
            status=status,
            safe_summary=safe_summary,
            reason_codes=reason_codes or [],
            capability_ids=[capability_id for capability_id in (capability_ids or []) if capability_id],
            durable_run_ref=durable_run_ref,
            receipt_ref=receipt_ref,
            replay_ref=replay_ref,
            rollback_ref=rollback_ref,
        )
        self.registry_store.append_audit_event(event)
        self._record_task_audit_session_event(event)
        return event

    def _record_task_audit_session_event(self, event: TaskDecompositionAuditEvent) -> None:
        session_status = _task_session_status(event.status)
        session_event_type = _task_session_event_type(event.event_type, session_status)
        severity = (
            "error"
            if session_status in {"failed", "timeout"}
            else "warning"
            if session_status in {"blocked", "denied", "waiting_approval"}
            else "info"
        )
        evidence_refs = [build_observability_safe_ref("task-audit", event.event_id)]
        for ref in [event.durable_run_ref, event.replay_ref, event.rollback_ref]:
            if ref:
                evidence_refs.append(ref)
        receipt_refs = [event.receipt_ref] if event.receipt_ref else []
        record_session_event(
            fail_closed=False,
            session_id="task-decomposition-session:local",
            run_id=_safe_task_run_id(event.run_id),
            trace_id=build_observability_safe_ref("task-trace", event.run_id),
            span_id=build_observability_safe_ref("task-span", event.event_id),
            correlation_id=build_observability_safe_ref("task-correlation", event.run_id),
            service="task_decomposition",
            surface="task_decomposition",
            event_type=session_event_type,
            lifecycle_state=_task_session_lifecycle(session_status),
            status=session_status,
            severity=severity,
            safe_summary=event.safe_summary,
            reason_codes=event.reason_codes or ["TASK_DECOMPOSITION_AUDIT_RECORDED"],
            evidence_refs=evidence_refs,
            receipt_refs=receipt_refs,
            redaction_summary={
                "status": "summary_only",
                "input_values_stored": False,
                "output_values_stored": False,
            },
            metadata={
                "audit_kind": event.event_type,
                "actor_ref": build_observability_safe_ref("actor", event.actor_id),
                "capability_refs": [
                    build_observability_safe_ref("capability", capability_id)
                    for capability_id in event.capability_ids
                ],
            },
        )

    def _record_task_node_session_events(
        self,
        result: DAGExecutionResult,
        binding: TaskDecompositionDurableBinding | None,
    ) -> None:
        latest_receipt_ref = self._latest_ref(binding.receipt_refs if binding else [])
        evidence_refs = list(binding.evidence_refs if binding else [])
        for record in result.node_records:
            if record.started_at is not None:
                record_session_event(
                    fail_closed=False,
                    session_id="task-decomposition-session:local",
                    run_id=_safe_task_run_id(result.plan_id),
                    trace_id=build_observability_safe_ref("task-trace", result.plan_id),
                    span_id=build_observability_safe_ref("task-node-start", result.plan_id, record.node_id),
                    parent_span_id=build_observability_safe_ref("task-span", result.plan_id),
                    correlation_id=build_observability_safe_ref("task-correlation", result.plan_id),
                    service="task_decomposition",
                    surface="task_decomposition",
                    event_type="task.node.started",
                    lifecycle_state="started",
                    status="started",
                    severity="info",
                    started_at=record.started_at,
                    safe_summary="Task node lifecycle started as a redacted summary.",
                    reason_codes=["TASK_NODE_STARTED"],
                    input_refs=[build_observability_safe_ref("task-node-input", result.plan_id, record.node_id)],
                    evidence_refs=evidence_refs,
                    receipt_refs=[latest_receipt_ref] if latest_receipt_ref else [],
                    redaction_summary={
                        "status": "summary_only",
                        "input_values_stored": False,
                        "output_values_stored": False,
                    },
                    metadata=_task_node_session_metadata(record.node_id, record.selected_capability),
                )
            terminal_type, terminal_status, lifecycle = _task_node_session_status(record.status.value)
            duration_ms = _task_node_duration_ms(record.started_at, record.completed_at)
            record_session_event(
                fail_closed=False,
                session_id="task-decomposition-session:local",
                run_id=_safe_task_run_id(result.plan_id),
                trace_id=build_observability_safe_ref("task-trace", result.plan_id),
                span_id=build_observability_safe_ref("task-node-finish", result.plan_id, record.node_id),
                parent_span_id=build_observability_safe_ref("task-node-start", result.plan_id, record.node_id),
                correlation_id=build_observability_safe_ref("task-correlation", result.plan_id),
                service="task_decomposition",
                surface="task_decomposition",
                event_type=terminal_type,
                lifecycle_state=classify_duration(duration_ms) if terminal_status == "succeeded" else lifecycle,
                status=terminal_status,
                severity="error" if terminal_status == "failed" else "warning" if terminal_status in {"skipped", "waiting_approval"} else "info",
                started_at=record.started_at,
                completed_at=record.completed_at,
                duration_ms=duration_ms,
                safe_summary=record.safe_summary,
                reason_codes=record.reason_codes or ["TASK_NODE_RECORDED"],
                output_refs=[
                    build_observability_safe_ref("task-node-output", result.plan_id, record.node_id)
                ]
                if terminal_status == "succeeded"
                else [],
                evidence_refs=evidence_refs,
                receipt_refs=[latest_receipt_ref] if latest_receipt_ref else [],
                redaction_summary={
                    "status": "summary_only",
                    "input_values_stored": False,
                    "output_values_stored": False,
                },
                metadata={
                    **_task_node_session_metadata(record.node_id, record.selected_capability),
                    "attempts": record.attempts,
                },
            )

    def _data_classification(self, sensitivity: str) -> DataClassification:
        mapping = {
            "public": ClassificationValue.public,
            "internal": ClassificationValue.system_internal,
            "private": ClassificationValue.project_private,
            "secret": ClassificationValue.credential_secret,
        }
        return DataClassification(
            classification=mapping.get(sensitivity, ClassificationValue.project_private),
            source="task_decomposition_capability",
            requires_consent=sensitivity in {"private", "secret"},
        )


def dump_json(data: Any) -> str:
    if isinstance(data, BaseModel):
        payload = data.model_dump(mode="json")
    else:
        payload = data
    return json.dumps(payload, indent=2, sort_keys=True)


def _task_session_event_type(audit_event_type: str, status: str) -> str:
    if audit_event_type == "plan_decomposed":
        return "task.plan.created"
    if audit_event_type == "plan_validated":
        return "task.plan.validated"
    if audit_event_type == "plan_executed":
        if status == "succeeded":
            return "task.plan.execution_completed"
        if status == "waiting_approval":
            return "task.plan.waiting_approval"
        return "task.plan.failed"
    if audit_event_type == "approval_requested":
        return "task.node.waiting_approval"
    return "task.audit.recorded"


def _task_session_status(status: str) -> str:
    normalized = status.lower()
    if normalized == "awaiting_approval":
        return "waiting_approval"
    if normalized in {"succeeded", "failed", "blocked", "denied", "skipped", "timeout"}:
        return normalized
    return "recorded"


def _task_session_lifecycle(status: str) -> str:
    if status == "waiting_approval":
        return "waiting_approval"
    if status in {"succeeded", "failed", "blocked", "denied", "skipped", "timeout"}:
        return status
    return "completed"


def _safe_task_run_id(run_id: str) -> str:
    if "/" in run_id or "\\" in run_id or len(run_id) > 160:
        return build_observability_safe_ref("task-run", run_id)
    return run_id


def _task_node_session_status(node_status: str) -> tuple[str, str, str]:
    if node_status == "succeeded":
        return "task.node.succeeded", "succeeded", "succeeded"
    if node_status == "skipped":
        return "task.node.skipped", "skipped", "skipped"
    if node_status == "awaiting_approval":
        return "task.node.waiting_approval", "waiting_approval", "waiting_approval"
    return "task.node.failed", "failed", "failed"


def _task_node_duration_ms(started_at: datetime | None, completed_at: datetime | None) -> float | None:
    if started_at is None or completed_at is None:
        return None
    return round(max((completed_at - started_at).total_seconds() * 1000, 0.0), 3)


def _task_node_session_metadata(node_id: str, capability_id: str | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "node_ref": build_observability_safe_ref("task-node", node_id),
    }
    if capability_id:
        metadata["capability_ref"] = build_observability_safe_ref("capability", capability_id)
    return metadata
