from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import ApprovalRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchRequest,
    AuthorityDomain,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.authority.contracts import authority_state_lock_manager
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityLatencyClass,
    CapabilityPrivacyLevel,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    ContextPolicy,
    QualitySignals,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepDefinition,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionManifest,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationResult,
    AuthorityMissionOrchestrationStepInput,
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.intent.reasoning_truth import (
    IntentAssessmentInput,
    IntentReasoningTruth,
    ReasoningStatement,
    ReasoningStatementKind,
    assess_intent,
)
from ultimate_ai_agent.core.planning.revisions import (
    PlanRevisionBinding,
    build_immutable_decomposition,
    build_immutable_decomposition_step,
    build_initial_plan_revision,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.control_center.founder_loop_mission_refs import (
    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
    FOUNDER_LOOP_FILESYSTEM_POLICY_REF,
    FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_OPAQUE_PATH_REF_VERSION,
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    filesystem_opaque_path_ref,
    normalize_relative_metadata_path,
)


FOUNDER_LOOP_PROPOSAL_LEDGER_FILE = "founder_loop_prepared_proposals.jsonl"
FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_BYTES = 1024 * 1024
FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_RECORDS = 256
FOUNDER_LOOP_PROPOSAL_LEDGER_LOCK_KEY = "founder-loop-prepared-proposals"


class _FounderLoopMissionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FounderLoopFilesystemTarget(_FounderLoopMissionModel):
    target_ref: str
    root_ref: str
    relative_path: str = Field(..., min_length=1, max_length=240)
    path_ref: str
    safe_label: str = Field(..., min_length=1, max_length=160)

    @model_validator(mode="after")
    def validate_target(self) -> "FounderLoopFilesystemTarget":
        for ref in (self.target_ref, self.root_ref, self.path_ref):
            validate_task_ref(ref, "founder_loop_filesystem_target_ref")
        validate_safe_task_text(self.safe_label, "founder_loop_filesystem_target_label")
        normalized, reasons = normalize_relative_metadata_path(self.relative_path)
        if reasons or normalized is None:
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_TARGET_PATH_INVALID")
        if self.path_ref != filesystem_opaque_path_ref(self.root_ref, normalized):
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_TARGET_PATH_REF_INVALID")
        return self


class FounderLoopFilesystemMissionRequest(_FounderLoopMissionModel):
    operator_request_ref: str
    intent_ref: str
    plan_lineage_ref: str
    plan_revision_ref: str
    proposal_ref: str
    mission_ref: str
    run_ref: str
    plan_ref: str
    step_ref: str
    target_ref: str
    lease_ref: str
    start_deadline: datetime
    safe_goal_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_request(self) -> "FounderLoopFilesystemMissionRequest":
        for field_name in (
            "operator_request_ref",
            "intent_ref",
            "plan_lineage_ref",
            "plan_revision_ref",
            "proposal_ref",
            "mission_ref",
            "run_ref",
            "plan_ref",
            "step_ref",
            "target_ref",
            "lease_ref",
        ):
            validate_task_ref(str(getattr(self, field_name)), field_name)
        validate_safe_task_text(self.safe_goal_summary, "safe_goal_summary")
        if self.start_deadline.tzinfo is None:
            raise ValueError("FOUNDER_LOOP_MISSION_DEADLINE_TIMEZONE_REQUIRED")
        return self


class FounderLoopPreparedProposalRecord(_FounderLoopMissionModel):
    sequence: int = Field(..., ge=1)
    request: FounderLoopFilesystemMissionRequest
    request_fingerprint_ref: str
    root_identity_ref: str
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str

    @model_validator(mode="after")
    def validate_record(self) -> "FounderLoopPreparedProposalRecord":
        for ref in (
            self.request_fingerprint_ref,
            self.root_identity_ref,
            self.previous_entry_hash_ref,
            self.entry_hash_ref,
        ):
            if ref is not None:
                validate_task_ref(ref, "founder_loop_prepared_record_ref")
        expected_fingerprint = _canonical_ref(
            "founder-loop-proposal-request-fingerprint-ref",
            self.request.model_dump(mode="json"),
        )
        if self.request_fingerprint_ref != expected_fingerprint:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_REQUEST_FINGERPRINT_INVALID")
        return self


def _prepared_record_entry_hash(
    record: FounderLoopPreparedProposalRecord,
) -> str:
    return _canonical_ref(
        "founder-loop-proposal-entry-hash-ref",
        record.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


class FounderLoopPreparedProposalStore:
    """Bounded safe-ref proposal recovery; target paths remain catalog-only."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.path = state_dir / FOUNDER_LOOP_PROPOSAL_LEDGER_FILE
        self._lock_manager = authority_state_lock_manager(str(state_dir.resolve()))

    def record(
        self,
        request: FounderLoopFilesystemMissionRequest,
        *,
        root_identity_ref: str,
    ) -> FounderLoopPreparedProposalRecord:
        validated = FounderLoopFilesystemMissionRequest.model_validate(
            request.model_dump(mode="python")
        )
        validate_task_ref(root_identity_ref, "founder_loop_root_identity_ref")
        with self._lock_manager.acquire(FOUNDER_LOOP_PROPOSAL_LEDGER_LOCK_KEY):
            records = self._load()
            existing = next(
                (
                    item
                    for item in records
                    if item.request.proposal_ref == validated.proposal_ref
                ),
                None,
            )
            if existing is not None:
                if (
                    existing.request != validated
                    or existing.root_identity_ref != root_identity_ref
                ):
                    raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_CONFLICT")
                return existing
            base = FounderLoopPreparedProposalRecord(
                sequence=len(records) + 1,
                request=validated,
                request_fingerprint_ref=_canonical_ref(
                    "founder-loop-proposal-request-fingerprint-ref",
                    validated.model_dump(mode="json"),
                ),
                root_identity_ref=root_identity_ref,
                previous_entry_hash_ref=(
                    records[-1].entry_hash_ref if records else None
                ),
                entry_hash_ref="founder-loop-proposal-entry-hash-ref:pending",
            )
            record = base.model_copy(
                update={"entry_hash_ref": _prepared_record_entry_hash(base)}
            )
            self._append(record)
            return record

    def get(self, proposal_ref: str) -> FounderLoopFilesystemMissionRequest | None:
        record = self.get_record(proposal_ref)
        return record.request.model_copy(deep=True) if record else None

    def get_record(self, proposal_ref: str) -> FounderLoopPreparedProposalRecord | None:
        validate_task_ref(proposal_ref, "founder_loop_proposal_ref")
        with self._lock_manager.acquire(FOUNDER_LOOP_PROPOSAL_LEDGER_LOCK_KEY):
            record = next(
                (
                    item
                    for item in self._load()
                    if item.request.proposal_ref == proposal_ref
                ),
                None,
            )
            return record.model_copy(deep=True) if record else None

    def _load(self) -> list[FounderLoopPreparedProposalRecord]:
        directory_fd = self._open_state_dir(create=False)
        if directory_fd is None:
            return []
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(
                FOUNDER_LOOP_PROPOSAL_LEDGER_FILE,
                flags,
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            try:
                self._assert_state_dir_binding(directory_fd)
            finally:
                os.close(directory_fd)
            return []
        except OSError as exc:
            os.close(directory_fd)
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_READ_FAILED") from exc
        try:
            self._assert_state_dir_binding(directory_fd)
            metadata = os.fstat(descriptor)
            path_metadata = os.stat(
                FOUNDER_LOOP_PROPOSAL_LEDGER_FILE,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
                or metadata.st_size > FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_BYTES
            ):
                raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID")
            payload = os.read(descriptor, FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
            os.close(directory_fd)
        return self._decode(payload)

    @staticmethod
    def _decode(payload: bytes) -> list[FounderLoopPreparedProposalRecord]:
        if len(payload) > FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_BYTES or (
            payload and not payload.endswith(b"\n")
        ):
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID") from exc
        if len(lines) > FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_RECORDS:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_LIMIT_EXCEEDED")
        records: list[FounderLoopPreparedProposalRecord] = []
        previous: str | None = None
        for sequence, line in enumerate(lines, 1):
            try:
                record = FounderLoopPreparedProposalRecord.model_validate_json(line)
            except ValueError as exc:
                raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID") from exc
            if (
                record.sequence != sequence
                or record.previous_entry_hash_ref != previous
                or record.entry_hash_ref != _prepared_record_entry_hash(record)
            ):
                raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID")
            records.append(record)
            previous = record.entry_hash_ref
        return records

    def _open_state_dir(self, *, create: bool) -> int | None:
        if create:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(self.state_dir, flags)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID") from exc
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            os.close(descriptor)
            raise ValueError("FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID")
        try:
            self._assert_state_dir_binding(descriptor)
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def _assert_state_dir_binding(self, descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        try:
            path_metadata = os.lstat(self.state_dir)
        except OSError as exc:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID") from exc
        if (
            not stat.S_ISDIR(path_metadata.st_mode)
            or stat.S_ISLNK(path_metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise ValueError("FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID")

    def _append(self, record: FounderLoopPreparedProposalRecord) -> None:
        if record.sequence > FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_RECORDS:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_LIMIT_EXCEEDED")
        directory_fd = self._open_state_dir(create=True)
        if directory_fd is None:
            raise ValueError("FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID")
        encoded = (record.model_dump_json() + "\n").encode("utf-8")
        flags = (
            os.O_RDWR
            | os.O_APPEND
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(
                FOUNDER_LOOP_PROPOSAL_LEDGER_FILE,
                flags,
                0o600,
                dir_fd=directory_fd,
            )
        except OSError as exc:
            os.close(directory_fd)
            raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_WRITE_FAILED") from exc
        try:
            self._assert_state_dir_binding(directory_fd)
            metadata = os.fstat(descriptor)
            path_metadata = os.stat(
                FOUNDER_LOOP_PROPOSAL_LEDGER_FILE,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
                or metadata.st_size + len(encoded)
                > FOUNDER_LOOP_PROPOSAL_LEDGER_MAX_BYTES
            ):
                raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_INVALID")
            existing = self._decode(os.pread(descriptor, metadata.st_size, 0))
            if (
                record.sequence != len(existing) + 1
                or record.previous_entry_hash_ref
                != (existing[-1].entry_hash_ref if existing else None)
                or record.entry_hash_ref != _prepared_record_entry_hash(record)
            ):
                raise ValueError("FOUNDER_LOOP_PROPOSAL_LEDGER_APPEND_INVALID")
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("proposal append failed")
                view = view[written:]
            os.fsync(descriptor)
            self._assert_state_dir_binding(directory_fd)
            os.fsync(directory_fd)
        finally:
            os.close(descriptor)
            os.close(directory_fd)


class FounderLoopMissionActionProposal(_FounderLoopMissionModel):
    proposal_ref: str
    intent_ref: str
    intent_fingerprint_ref: str
    plan_revision_ref: str
    plan_revision_fingerprint_ref: str
    mission_ref: str
    run_ref: str
    target_ref: str
    adapter_ref: Literal[
        "authority-adapter-ref:founder-loop-filesystem-metadata-v1"
    ] = FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF
    capability_ref: Literal[
        "authority-capability-ref:founder-loop-filesystem-metadata-v1"
    ] = FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF
    policy_decision_ref: str
    policy_posture: Literal["approval_required"] = "approval_required"
    approval_request_ref: str
    lease_ref: str
    safe_summary: str
    execution_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_proposal(self) -> "FounderLoopMissionActionProposal":
        for field_name, value in self.model_dump(mode="python").items():
            if field_name.endswith("_ref"):
                validate_task_ref(str(value), field_name)
        validate_safe_task_text(self.safe_summary, "founder_loop_proposal_summary")
        return self


class FounderLoopMissionMemoryCandidate(_FounderLoopMissionModel):
    memory_candidate_ref: str
    completion_ref: str
    source_refs: tuple[str, ...] = Field(..., min_length=1)
    review_status: Literal["review_required"] = "review_required"
    recall_only: Literal[True] = True
    accepted_as_truth: Literal[False] = False
    memory_write_performed: Literal[False] = False
    context_injection_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_candidate(self) -> "FounderLoopMissionMemoryCandidate":
        for ref in (
            self.memory_candidate_ref,
            self.completion_ref,
            *self.source_refs,
        ):
            validate_task_ref(ref, "founder_loop_memory_candidate_ref")
        return self


class FounderLoopMissionPrepared(_FounderLoopMissionModel):
    proposal: FounderLoopMissionActionProposal
    intent_truth: IntentReasoningTruth
    plan_revision: PlanRevisionBinding


class FounderLoopFilesystemMissionResult(_FounderLoopMissionModel):
    proposal: FounderLoopMissionActionProposal
    intent_truth: IntentReasoningTruth
    plan_revision: PlanRevisionBinding
    orchestration: AuthorityMissionOrchestrationResult
    completion: MissionCompletionManifest
    memory_candidate: FounderLoopMissionMemoryCandidate
    recorded_start_approval_validated: Literal[True] = True
    recorded_start_policy_rechecked: Literal[True] = True
    terminal_replay: bool
    replay_mints_current_authority: Literal[False] = False
    authority_minted_by_facade: Literal[False] = False
    raw_operator_input_persisted: Literal[False] = False
    raw_path_persisted: Literal[False] = False


class _PreparedInternal:
    def __init__(
        self,
        *,
        prepared: FounderLoopMissionPrepared,
        orchestration_request: AuthorityMissionOrchestrationRequest,
        approval_request: ApprovalRequest,
    ) -> None:
        self.prepared = prepared
        self.orchestration_request = orchestration_request
        self.approval_request = approval_request


def _canonical_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def build_founder_loop_filesystem_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="Founder Loop filesystem metadata",
        description="Inspect metadata for one predeclared repository artifact.",
        examples=["Inspect metadata for one predeclared artifact ref."],
        anti_examples=["Read content or inspect a caller-selected path."],
        input_schema={"type": "object", "required": ["target_ref"]},
        output_schema={"type": "object", "required": ["evidence_refs"]},
        input_modes=["safe_refs_only"],
        output_modes=["metadata_refs_only"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.low,
        authority_level=CapabilityAuthorityLevel.metadata_only,
        approval_required="Operator confirms the exact predeclared target.",
        deterministic=True,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_latency_class=CapabilityLatencyClass.interactive,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        allowed_coordination_modes=[CoordinationMode.workflow_node],
        concurrency_safe=False,
        context_policy=ContextPolicy(
            required_context_keys=["target_ref"],
            max_context_refs=4,
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=10,
            max_retries=0,
            max_concurrency=1,
            deterministic=True,
            estimated_cost_usd=0,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=False,
            approval_required=True,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            deny_if_deprecated=True,
            max_risk_level=RiskLevel.low,
            max_side_effect_level=SideEffectLevel.read,
        ),
        quality=QualitySignals(
            test_coverage_refs=["test-ref:founder-loop-filesystem-mission"],
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "adapter_ref": FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
            "safe_disable_ref": FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
            "policy_ref": FOUNDER_LOOP_FILESYSTEM_POLICY_REF,
            "broad_filesystem_access": False,
        },
    )


class GovernedFounderLoopFilesystemAdapter:
    def __init__(
        self,
        *,
        root: FilesystemSafeRoot,
        readiness: Callable[[], Literal["ready", "safe_disabled", "unknown"]],
    ) -> None:
        root_stat = os.lstat(root.root_path)
        if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_ROOT_NOT_READY")
        self._root = root
        self._root_identity = (root_stat.st_dev, root_stat.st_ino)
        self._readiness = readiness
        self._manifest = build_founder_loop_filesystem_capability_manifest()
        self._policy = PolicyEngine(default_max_risk=RiskLevel.low)
        self._inner = ToolRuntimeAuthorityDispatchAdapter(
            AuthorityDispatchAdapterDescriptor(
                adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                domain=AuthorityDomain.files,
                capability=AuthorityCapability.read,
                capability_ref=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
                tool_ref=FILESYSTEM_METADATA_TOOL_REF,
                approval_required=True,
                operation_count=1,
                estimated_cost_microusd=0,
                failure_cost_microusd=0,
                idempotent_replay_supported=False,
                rollback_ref="rollback-ref:filesystem-metadata-no-mutation",
                safe_disable_ref=FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
                safe_summary=(
                    "Inspect metadata for one injected predeclared repository target."
                ),
            ),
            safe_roots=[
                root.model_copy(
                    update={
                        "expected_device": root_stat.st_dev,
                        "expected_inode": root_stat.st_ino,
                    }
                )
            ],
            admission_validator_ref=(
                "admission-validator-ref:founder-loop-filesystem-metadata-v1"
            ),
            admission_validator=self._admission_reasons,
            evidence_ref_provider=self._policy_evidence_refs,
        )
        self._binding_ref = _canonical_ref(
            "adapter-binding-ref:founder-loop-filesystem-metadata",
            {
                "inner_binding_ref": self._inner.binding_ref,
                "root_ref": root.root_ref,
                "root_device": root_stat.st_dev,
                "root_inode": root_stat.st_ino,
            },
        )
        self._root_identity_ref = _canonical_ref(
            "root-identity-ref:founder-loop-filesystem-metadata",
            {
                "root_ref": root.root_ref,
                "device": root_stat.st_dev,
                "inode": root_stat.st_ino,
            },
        )

    @property
    def descriptor(self) -> AuthorityDispatchAdapterDescriptor:
        return self._inner.descriptor

    @property
    def binding_ref(self) -> str:
        return self._binding_ref

    @property
    def root_identity_ref(self) -> str:
        return self._root_identity_ref

    @property
    def runtime_adapter(self) -> ToolRuntimeAuthorityDispatchAdapter:
        return self._inner

    def _policy_decision_ref(self, request: AuthorityDispatchRequest) -> str:
        tool_request = ToolInvocationRequest.model_validate(
            request.tool_invocation_request
        )
        root_ref = tool_request.metadata.get("root_ref")
        relative_path = tool_request.metadata.get("relative_path")
        if not isinstance(root_ref, str) or not isinstance(relative_path, str):
            raise ValueError("FOUNDER_LOOP_POLICY_TARGET_BINDING_REQUIRED")
        normalized_path, path_reasons = normalize_relative_metadata_path(relative_path)
        if path_reasons or normalized_path is None:
            raise ValueError("FOUNDER_LOOP_POLICY_TARGET_BINDING_INVALID")
        target_ref = request.action_request.constraints.get("target_ref")
        if not isinstance(target_ref, str):
            raise ValueError("FOUNDER_LOOP_POLICY_TARGET_REF_REQUIRED")
        validate_task_ref(target_ref, "founder_loop_policy_target_ref")
        task = TaskEnvelope(
            task_id=request.run_ref,
            user_request="Inspect one predeclared metadata target.",
            objective="Return bounded metadata evidence only.",
            scope=[request.action_request.capability_ref or ""],
            out_of_scope=["content", "mutation", "network"],
            selected_capability_ids=[self._manifest.id],
            allowed_tool_ids=[FILESYSTEM_METADATA_TOOL_REF],
            acceptance_criteria=["Return safe refs and a terminal receipt."],
            budget={"operation_count": 1, "cost_microusd": 0},
            context={"target_ref": target_ref},
        )
        decision = self._policy.can_execute(
            self._manifest,
            task,
            {
                "allowed_capability_ids": [self._manifest.id],
                "max_risk_level": RiskLevel.low.value,
                "capability_health": {self._manifest.id: "healthy"},
                "coordination_mode": CoordinationMode.workflow_node.value,
            },
        )
        if decision.status != PolicyDecisionStatus.approval_required:
            raise ValueError("FOUNDER_LOOP_POLICY_APPROVAL_POSTURE_INVALID")
        return _canonical_ref(
            "policy-decision-ref:founder-loop-filesystem-metadata",
            {
                "decision": decision.model_dump(mode="json"),
                "scope": {
                    "dispatch_ref": request.dispatch_ref,
                    "run_ref": request.run_ref,
                    "lease_ref": request.lease_ref,
                    "idempotency_ref": request.idempotency_ref,
                    "action_ref": request.action_request.action_ref,
                    "domain": request.action_request.domain,
                    "capability": request.action_request.capability,
                    "capability_ref": request.action_request.capability_ref,
                    "adapter_ref": request.adapter_ref,
                    "resource_refs": sorted(request.action_request.resource_refs),
                    "constraint_claims": [
                        claim.model_dump(mode="json")
                        for claim in request.action_request.constraint_claims
                    ],
                    "mission_ref": request.action_request.constraints.get(
                        "mission_ref"
                    ),
                    "target_ref": request.action_request.constraints.get("target_ref"),
                    "plan_revision_fingerprint_ref": (
                        request.action_request.constraints.get(
                            "plan_revision_fingerprint_ref"
                        )
                    ),
                    "path_ref": filesystem_opaque_path_ref(root_ref, normalized_path),
                    "operation_count": request.operation_count,
                    "estimated_cost_microusd": request.estimated_cost_microusd,
                    "start_deadline": request.start_deadline.isoformat()
                    if request.start_deadline is not None
                    else None,
                },
            },
        )

    def _admission_reasons(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons: list[str] = []
        readiness = self._readiness()
        if readiness == "safe_disabled":
            reasons.append("reason-ref:founder-loop-filesystem:safe-disabled")
        elif readiness != "ready":
            reasons.append("reason-ref:founder-loop-filesystem:readiness-unknown")
        try:
            root_stat = os.lstat(self._root.root_path)
        except OSError:
            reasons.append("reason-ref:founder-loop-filesystem:root-unavailable")
        else:
            if (
                not stat.S_ISDIR(root_stat.st_mode)
                or stat.S_ISLNK(root_stat.st_mode)
                or (root_stat.st_dev, root_stat.st_ino) != self._root_identity
            ):
                reasons.append("reason-ref:founder-loop-filesystem:root-identity-drift")
        try:
            expected_policy_ref = self._policy_decision_ref(request)
        except ValueError:
            reasons.append("reason-ref:founder-loop-filesystem:policy-denied")
        else:
            if (
                request.action_request.constraints.get("policy_decision_ref")
                != expected_policy_ref
            ):
                reasons.append(
                    "reason-ref:founder-loop-filesystem:policy-binding-mismatch"
                )
        return list(dict.fromkeys(reasons))

    def _policy_evidence_refs(self, request: AuthorityDispatchRequest) -> list[str]:
        return [self._policy_decision_ref(request)]


class FounderLoopFilesystemMissionService:
    def __init__(
        self,
        *,
        state_dir: Path,
        root: FilesystemSafeRoot,
        targets: tuple[FounderLoopFilesystemTarget, ...],
        lease_store: AuthorityLeaseStore,
        approval_authority: LocalApprovalAuthority,
        readiness: Callable[[], Literal["ready", "safe_disabled", "unknown"]],
    ) -> None:
        if not targets:
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_TARGET_CATALOG_REQUIRED")
        if any(target.root_ref != root.root_ref for target in targets):
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_TARGET_ROOT_MISMATCH")
        self.targets = {target.target_ref: target for target in targets}
        if len(self.targets) != len(targets):
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_DUPLICATE_TARGET")
        self.approval_authority = approval_authority
        self.lease_store = lease_store
        self._proposal_store = FounderLoopPreparedProposalStore(state_dir)
        lane_adapter = GovernedFounderLoopFilesystemAdapter(
            root=root,
            readiness=readiness,
        )
        self._lane_adapter = lane_adapter
        dispatcher = AuthorityDispatcher(
            state_dir,
            adapters=[lane_adapter.runtime_adapter],
            lease_store=lease_store,
            approval_authority=approval_authority,
        )
        step_store = MissionStepStore(state_dir)
        self.orchestrator = SynchronousAuthorityMissionOrchestrator(
            runner=AuthorityMissionRunner(
                dispatcher=dispatcher,
                step_store=step_store,
            ),
            plan_store=DurableMissionPlanStore(state_dir),
        )
        self._prepared: dict[str, _PreparedInternal] = {}
        self._lock = threading.RLock()

    def prepared_proposal(
        self,
        proposal_ref: str,
    ) -> FounderLoopMissionPrepared | None:
        validate_task_ref(proposal_ref, "founder_loop_proposal_ref")
        with self._lock:
            internal = self._prepared.get(proposal_ref)
        if internal is not None:
            return internal.prepared
        recovered_record = self._proposal_store.get_record(proposal_ref)
        if recovered_record is None:
            return None
        self.prepare(recovered_record.request)
        with self._lock:
            internal = self._prepared.get(proposal_ref)
        return internal.prepared if internal is not None else None

    def prepared_request(
        self,
        proposal_ref: str,
    ) -> FounderLoopFilesystemMissionRequest | None:
        validate_task_ref(proposal_ref, "founder_loop_proposal_ref")
        record = self._proposal_store.get_record(proposal_ref)
        return record.request if record is not None else None

    def prepared_approval_request(
        self,
        proposal_ref: str,
    ) -> ApprovalRequest | None:
        self.prepared_proposal(proposal_ref)
        with self._lock:
            internal = self._prepared.get(proposal_ref)
        return (
            internal.approval_request.model_copy(deep=True)
            if internal is not None
            else None
        )

    def prepare(
        self,
        request: FounderLoopFilesystemMissionRequest,
    ) -> FounderLoopMissionPrepared:
        target = self.targets.get(request.target_ref)
        if target is None:
            raise ValueError("FOUNDER_LOOP_FILESYSTEM_TARGET_NOT_PREDECLARED")
        fact = ReasoningStatement(
            statement_ref=f"fact-ref:founder-loop-target:{hash_text(target.target_ref)}",
            kind=ReasoningStatementKind.fact,
            safe_summary="The operator selected one predeclared metadata-only target.",
            source_refs=(request.operator_request_ref,),
            evidence_refs=(target.target_ref,),
            review_required=False,
        )
        intent = assess_intent(
            request.safe_goal_summary,
            IntentAssessmentInput(
                intent_ref=request.intent_ref,
                safe_summary=request.safe_goal_summary,
                source_refs=(request.operator_request_ref,),
                evidence_refs=(target.target_ref,),
                facts=(fact,),
            ),
        )
        decomposition_step = build_immutable_decomposition_step(
            step_ref=request.step_ref,
            safe_summary="Inspect metadata for the selected predeclared target.",
            target_refs=(
                target.target_ref,
                f"target-path-binding-ref:sha256:{hash_text(target.path_ref)}",
            ),
            source_refs=(request.operator_request_ref, intent.intent_ref),
        )
        decomposition = build_immutable_decomposition(
            decomposition_ref=(
                f"decomposition-ref:founder-loop:{hash_text(request.plan_ref)}"
            ),
            intent_fingerprint_ref=intent.intent_fingerprint_ref,
            ordered_steps=(decomposition_step,),
        )
        revision = build_initial_plan_revision(
            lineage_ref=request.plan_lineage_ref,
            revision_ref=request.plan_revision_ref,
            reason_ref="reason-ref:founder-loop:initial-exact-metadata-plan",
            safe_reason="Create one immutable metadata-only mission step.",
            decomposition=decomposition,
        )
        dispatch_ref = mission_step_dispatch_ref(request.step_ref)
        idempotency_ref = mission_step_idempotency_ref(request.step_ref)
        cost_estimate = CostEstimate(
            estimate_id=f"cost-estimate:founder-loop:{hash_text(dispatch_ref)}",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0,
            estimated_token_cost_usd=0,
        )
        cost_budgets = [
            CostBudget(
                budget_id=f"cost-budget:founder-loop:{hash_text(request.run_ref)}",
                scope=BudgetScope.run,
                scope_id=request.run_ref,
                max_cost_usd=0,
                max_total_tokens=1,
            )
        ]
        provisional_action = AuthorityActionRequest(
            action_ref=mission_step_action_ref(request.step_ref),
            domain=AuthorityDomain.files,
            capability=AuthorityCapability.read,
            capability_ref=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
            adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
            resource_refs=[
                FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
                FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                target.target_ref,
                target.root_ref,
                target.path_ref,
                request.mission_ref,
            ],
            constraint_claims=[
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.operation_budget,
                    value=1,
                ),
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    value=0,
                ),
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.path_refs,
                    refs=[target.path_ref],
                ),
            ],
            constraints={
                "mission_ref": request.mission_ref,
                "target_ref": target.target_ref,
                "plan_revision_fingerprint_ref": revision.revision_fingerprint_ref,
            },
            safe_summary="Inspect one exact predeclared metadata target.",
        )
        exact_resource_refs = set(provisional_action.resource_refs)
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
                    if constraint.kind == AuthorityConstraintKind.resource_refs.value
                ),
                None,
            )
            if lease is not None
            else None
        )
        if (
            lease is None
            or lease.scope != "mission"
            or lease.mission_ref != request.mission_ref
            or resource_constraint is None
            or set(resource_constraint.allowed_refs) != exact_resource_refs
        ):
            raise ValueError("FOUNDER_LOOP_EXACT_MISSION_LEASE_SCOPE_REQUIRED")
        tool_request = ToolInvocationRequest(
            invocation_id=dispatch_ref,
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            tool_name=FILESYSTEM_METADATA_TOOL_NAME,
            invocation_kind=ToolInvocationKind.filesystem_metadata,
            replay_key=idempotency_ref,
            safe_summary="Inspect bounded metadata under an injected repository root.",
            input_refs=[target.target_ref, revision.revision_fingerprint_ref],
            metadata={
                "root_ref": target.root_ref,
                "relative_path": target.relative_path,
                "safe_path_ref_version": FILESYSTEM_OPAQUE_PATH_REF_VERSION,
            },
        )
        provisional_dispatch = AuthorityDispatchRequest(
            dispatch_ref=dispatch_ref,
            run_ref=request.run_ref,
            idempotency_ref=idempotency_ref,
            lease_ref=request.lease_ref,
            adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
            action_request=provisional_action,
            tool_invocation_request=tool_request.model_dump(mode="json"),
            operation_count=1,
            estimated_cost_microusd=0,
            cost_estimate=cost_estimate,
            cost_budgets=cost_budgets,
            cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(cost_estimate),
            cost_governor_decision_ref=(
                build_authority_dispatch_cost_governor_decision_ref(
                    cost_estimate,
                    cost_budgets,
                )
            ),
            cost_governor_allowed=True,
            start_deadline=request.start_deadline,
            safe_summary="Run one exact Founder Loop metadata mission step.",
        )
        policy_ref = self._lane_adapter._policy_decision_ref(  # noqa: SLF001
            provisional_dispatch
        )
        action = provisional_action.model_copy(
            update={
                "constraints": {
                    **provisional_action.constraints,
                    "policy_decision_ref": policy_ref,
                }
            }
        )
        dispatch = provisional_dispatch.model_copy(update={"action_request": action})
        approval_request = ApprovalRequest(
            approval_request_id=(
                f"approval-request-ref:founder-loop:{hash_text(request.proposal_ref)}"
            ),
            run_id=request.run_ref,
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=action.action_ref,
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="operator-ref:local-user",
                authority_source=AuthoritySource.explicit_user_request,
            ),
            requested_action=action.action_ref,
            purpose="Approve one exact predeclared metadata-only mission target.",
            risk_level=ApprovalRiskLevel.medium,
            data_classification=DataClassification(
                classification=ClassificationValue.system_internal,
                source="founder_loop_filesystem_mission",
                requires_redaction=True,
            ),
            resource_refs=[
                request.lease_ref,
                FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
                *action.resource_refs,
            ],
        )
        definition = MissionStepDefinition(
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            step_ref=request.step_ref,
            capability_ref=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
            adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
            lease_ref=request.lease_ref,
            deadline=request.start_deadline,
            safe_summary="Run one exact metadata-only Founder Loop mission step.",
        )
        orchestration_request = AuthorityMissionOrchestrationRequest(
            plan_ref=request.plan_ref,
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            steps=[
                AuthorityMissionOrchestrationStepInput(
                    definition=definition,
                    request=dispatch,
                )
            ],
            safe_summary="Run one bounded Founder Loop metadata mission.",
        )
        proposal = FounderLoopMissionActionProposal(
            proposal_ref=request.proposal_ref,
            intent_ref=intent.intent_ref,
            intent_fingerprint_ref=intent.intent_fingerprint_ref,
            plan_revision_ref=revision.revision_ref,
            plan_revision_fingerprint_ref=revision.revision_fingerprint_ref,
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            target_ref=target.target_ref,
            policy_decision_ref=policy_ref,
            approval_request_ref=approval_request.approval_request_id,
            lease_ref=request.lease_ref,
            safe_summary="Review one exact metadata-only mission proposal.",
        )
        prepared = FounderLoopMissionPrepared(
            proposal=proposal,
            intent_truth=intent,
            plan_revision=revision,
        )
        with self._lock:
            existing = self._prepared.get(proposal.proposal_ref)
            if existing is not None:
                if (
                    existing.prepared != prepared
                    or existing.orchestration_request != orchestration_request
                    or existing.approval_request != approval_request
                ):
                    raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_CONFLICT")
                return existing.prepared
            self._proposal_store.record(
                request,
                root_identity_ref=self._lane_adapter.root_identity_ref,
            )
            registered_request = self.approval_authority.create_request(
                approval_request
            )
            if registered_request != approval_request:
                raise ValueError("FOUNDER_LOOP_APPROVAL_REQUEST_CONFLICT")
            self._prepared[proposal.proposal_ref] = _PreparedInternal(
                prepared=prepared,
                orchestration_request=orchestration_request,
                approval_request=registered_request,
            )
        return prepared

    def execute(
        self,
        *,
        proposal_ref: str,
        approval_ref: str,
        owner_ref: str,
    ) -> FounderLoopFilesystemMissionResult:
        validate_task_ref(proposal_ref, "founder_loop_proposal_ref")
        validate_task_ref(approval_ref, "founder_loop_approval_ref")
        validate_task_ref(owner_ref, "founder_loop_owner_ref")
        with self._lock:
            internal = self._prepared.get(proposal_ref)
        if internal is None:
            recovered_record = self._proposal_store.get_record(proposal_ref)
            if recovered_record is None:
                raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_NOT_PREPARED")
            if (
                recovered_record.root_identity_ref
                != self._lane_adapter.root_identity_ref
            ):
                raise ValueError("FOUNDER_LOOP_FILESYSTEM_ROOT_IDENTITY_DRIFT")
            self.prepare(recovered_record.request)
            with self._lock:
                internal = self._prepared.get(proposal_ref)
            if internal is None:
                raise ValueError("FOUNDER_LOOP_MISSION_PROPOSAL_RECOVERY_FAILED")
        validation_request = internal.approval_request.to_validation_request(
            approval_ref
        )
        step = internal.orchestration_request.steps[0]
        dispatch = step.request.model_copy(
            update={"approval_validation_request": validation_request}
        )
        orchestration_request = internal.orchestration_request.model_copy(
            update={"steps": [step.model_copy(update={"request": dispatch})]}
        )
        orchestration = self.orchestrator.run(
            orchestration_request,
            owner_ref=owner_ref,
        )
        if (
            orchestration.status != "succeeded"
            or orchestration.completion_manifest_ref is None
            or orchestration.memory_candidate_ref is None
        ):
            raise ValueError("FOUNDER_LOOP_MISSION_DID_NOT_COMPLETE")
        completion = next(
            (
                item
                for item in self.orchestrator.completion_store.list_manifests()
                if item.completion_ref == orchestration.completion_manifest_ref
            ),
            None,
        )
        if completion is None:
            raise ValueError("FOUNDER_LOOP_MISSION_COMPLETION_EVIDENCE_REQUIRED")
        memory_candidate = FounderLoopMissionMemoryCandidate(
            memory_candidate_ref=completion.memory_candidate_ref,
            completion_ref=completion.completion_ref,
            source_refs=(
                completion.completion_ref,
                completion.plan_receipt_ref,
                *(item.dispatch_receipt_ref for item in completion.step_bindings),
            ),
        )
        return FounderLoopFilesystemMissionResult(
            proposal=internal.prepared.proposal,
            intent_truth=internal.prepared.intent_truth,
            plan_revision=internal.prepared.plan_revision,
            orchestration=orchestration,
            completion=completion,
            memory_candidate=memory_candidate,
            terminal_replay=orchestration.replayed_step_count > 0,
        )
