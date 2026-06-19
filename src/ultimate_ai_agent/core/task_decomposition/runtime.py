from __future__ import annotations

import asyncio
import hashlib
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityCallContext,
    CapabilityContract,
    DAGExecutionResult,
    PlanValidationContext,
    PlanValidationResult,
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
    def __init__(self, max_events: int = 600, window_s: float = 60.0):
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

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRunRequest(BaseModel):
    raw_request: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)
    persist_reflections: bool = True

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

    model_config = ConfigDict(extra="forbid")


class CapabilityRegistryStore:
    def __init__(self, config: CapabilityRegistryStoreConfig | None = None):
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
    ):
        self.registry_store = registry_store or CapabilityRegistryStore()
        self.registry = registry or self.registry_store.load()
        self.approval_authority = approval_authority or LocalApprovalAuthority()
        self.registry.approval_authority = self.approval_authority
        self.reflection_store = reflection_store or ReflectionStore()
        self.rate_limiter = rate_limiter or TaskDecompositionRateLimiter()
        self.validator = PlanValidator()
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._load_persisted_approval_state()

    @classmethod
    def from_env(cls) -> "TaskDecompositionService":
        path = os.environ.get("UAA_TASK_DECOMPOSITION_REGISTRY", DEFAULT_REGISTRY_PATH)
        return cls(registry_store=CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=path)))

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
        self.record_audit_event(
            "plan_decomposed",
            run_id=plan.plan_id,
            status="succeeded" if validation.valid else "blocked",
            safe_summary="Task request was decomposed and validated.",
            reason_codes=validation.reason_codes,
            capability_ids=[node.selected_capability for node in plan.nodes if node.selected_capability],
        )
        return TaskDecompositionRunResult(intent=intent, plan=plan, validation=validation)

    def validate_plan(self, request: TaskPlanValidationRequest) -> PlanValidationResult:
        self._check_rate_limit(request.context.call_context.actor_id)
        validation = self.validator.validate(request.plan, self.registry, request.context)
        self.record_audit_event(
            "plan_validated",
            run_id=request.plan.plan_id,
            status="succeeded" if validation.valid else "blocked",
            safe_summary="Task plan validation completed.",
            reason_codes=validation.reason_codes,
            capability_ids=[node.selected_capability for node in request.plan.nodes if node.selected_capability],
        )
        return validation

    def build_approval_request(self, request: TaskCapabilityApprovalRequestPayload) -> ApprovalRequest:
        self._check_rate_limit(request.actor_id)
        contract = self.registry.get(request.capability_id)
        if contract is None:
            raise KeyError("CAPABILITY_NOT_REGISTERED")
        approval_request = ApprovalRequest(
            approval_request_id=f"areq_{request.run_id}_{request.capability_id}".replace(":", "_"),
            run_id=request.run_id,
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
        self._save_persisted_approval_state()
        self.record_audit_event(
            "approval_requested",
            run_id=request.run_id,
            actor_id=request.actor_id,
            status="awaiting_approval",
            safe_summary="Capability approval request was created.",
            capability_ids=[request.capability_id],
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
        self._save_persisted_approval_state()
        self.record_audit_event(
            "approval_granted",
            run_id=grant.run_id,
            actor_id=grant.granted_to_actor_id,
            status="granted",
            safe_summary="Capability approval grant was captured for exact scoped validation.",
            capability_ids=[grant.subject_id],
        )
        return grant

    def revoke_approval(self, request: TaskDecompositionApprovalRevokeRequest) -> ApprovalGrant:
        self._check_rate_limit("approval_revocation")
        revoked = self.approval_authority.revoke(request.approval_ref, request.reason)
        self._save_persisted_approval_state()
        self.record_audit_event(
            "approval_revoked",
            run_id=revoked.run_id,
            actor_id=revoked.granted_to_actor_id,
            status="revoked",
            safe_summary="Capability approval grant was revoked.",
            capability_ids=[revoked.subject_id],
        )
        return revoked

    def approval_queue(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "requests": [request.model_dump(mode="json") for request in self._approval_requests.values()],
            "grants": [grant.model_dump(mode="json") for grant in self.approval_authority.list_grants()],
        }

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
        result = await DAGExecutor(self.registry, self.validator).execute(request.plan, call_context)
        if request.persist_reflections:
            self.reflection_store.record_execution(request.plan, result)
        self.record_audit_event(
            "plan_executed",
            run_id=request.plan.plan_id,
            actor_id=call_context.actor_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            safe_summary=result.safe_summary,
            reason_codes=result.reason_codes,
            capability_ids=[node.selected_capability for node in request.plan.nodes if node.selected_capability],
        )
        return result

    def execute_plan_sync(self, request: TaskPlanExecutionRequest) -> DAGExecutionResult:
        return asyncio.run(self.execute_plan(request))

    async def run(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        decomposed = self.decompose(TaskDecompositionRequest(raw_request=request.raw_request, context=request.context))
        if not decomposed.validation.valid:
            return decomposed
        execution = await self.execute_plan(
            TaskPlanExecutionRequest(
                plan=decomposed.plan,
                call_context=request.call_context,
                approval_grants=request.approval_grants,
                persist_reflections=request.persist_reflections,
            )
        )
        return decomposed.model_copy(update={"execution": execution})

    def run_sync(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        return asyncio.run(self.run(request))

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
    ) -> TaskDecompositionAuditEvent:
        event = TaskDecompositionAuditEvent(
            event_type=event_type,
            run_id=run_id,
            actor_id=actor_id,
            status=status,
            safe_summary=safe_summary,
            reason_codes=reason_codes or [],
            capability_ids=[capability_id for capability_id in (capability_ids or []) if capability_id],
        )
        self.registry_store.append_audit_event(event)
        return event

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
