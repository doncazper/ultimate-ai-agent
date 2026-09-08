from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
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
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


CHAT_WORKSPACE_CONTRACT_REF = "contract-ref:chat-content-free-workspace:v1"
CHAT_WORKSPACE_SOURCE = "python_core_chat_content_free_workspace"
CHAT_WORKSPACE_MAX_REQUEST_BYTES = 8 * 1024
CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH = 16
CHAT_WORKSPACE_MAX_REVISION = 2_147_483_647
CHAT_WORKSPACE_MAX_THREADS = 100
CHAT_WORKSPACE_MAX_MUTATION_RECORDS = 10_000
CHAT_WORKSPACE_MAX_ACTIVE_APPROVALS = 512
CHAT_WORKSPACE_APPROVAL_TTL_MINUTES = 5
CHAT_WORKSPACE_ROUTE_REFS = (
    "GET /control-center/chat/workspace",
    "POST /control-center/chat/threads/{thread_ref}/approval",
    "POST /control-center/chat/threads/{thread_ref}/draft-checkpoint",
    "POST /control-center/chat/threads/{thread_ref}/lifecycle",
)
CHAT_DRAFT_EMPTY_FINGERPRINT_REF = "draft-fingerprint-ref:chat:empty"
CHAT_DRAFT_FINGERPRINT_RE = re.compile(
    r"^draft-fingerprint-ref:chat:(?:empty|local-[0-9a-f]{32})$"
)
CHAT_THREAD_REF_RE = re.compile(r"^chat-thread:[A-Za-z0-9][A-Za-z0-9_.:@-]{0,187}$")
CHAT_DISPLAY_NAME_RE = re.compile(r"^Conversation [1-9][0-9]{0,5}$")
CHAT_WORKSPACE_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,199}$")
CHAT_WORKSPACE_BLOCKED_STATE_REFS = (
    "blocked-state:chat-workspace:no-draft-body-persistence",
    "blocked-state:chat-workspace:no-model-call",
    "blocked-state:chat-workspace:no-tool-execution",
    "blocked-state:chat-workspace:no-memory-write",
    "blocked-state:chat-workspace:no-connector-write",
    "blocked-state:chat-workspace:no-production-authority",
)
ChatWorkspaceMetadataRef = Annotated[str, Field(min_length=1, max_length=200)]


class ChatDraftCheckpointRequest(BaseModel):
    confirmed: Literal[True]
    expected_revision: int = Field(ge=0, le=CHAT_WORKSPACE_MAX_REVISION)
    draft_present: bool
    draft_character_count: int = Field(ge=0, le=32_000)
    draft_fingerprint_ref: str = Field(
        min_length=1,
        max_length=200,
        pattern=CHAT_DRAFT_FINGERPRINT_RE.pattern,
    )
    metadata_refs: list[ChatWorkspaceMetadataRef] = Field(
        default_factory=list,
        max_length=16,
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_checkpoint(self) -> "ChatDraftCheckpointRequest":
        validate_task_ref(self.draft_fingerprint_ref, "draft_fingerprint_ref")
        _validate_chat_workspace_metadata_refs(
            self.metadata_refs,
            expected_revision=self.expected_revision,
        )
        if self.draft_present:
            if self.draft_character_count == 0:
                raise ValueError("a present Chat draft must have a character count")
            if self.draft_fingerprint_ref == CHAT_DRAFT_EMPTY_FINGERPRINT_REF:
                raise ValueError("a present Chat draft must have a content fingerprint")
        elif (
            self.draft_character_count != 0
            or self.draft_fingerprint_ref != CHAT_DRAFT_EMPTY_FINGERPRINT_REF
        ):
            raise ValueError("an empty Chat draft must use the empty fingerprint")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_draft_checkpoint_request"
        )
        return self


class ChatThreadLifecycleRequest(BaseModel):
    confirmed: Literal[True]
    action: Literal["archive", "recover"]
    expected_revision: int = Field(ge=1, le=CHAT_WORKSPACE_MAX_REVISION)
    metadata_refs: list[ChatWorkspaceMetadataRef] = Field(
        default_factory=list,
        max_length=16,
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "ChatThreadLifecycleRequest":
        _validate_chat_workspace_metadata_refs(
            self.metadata_refs,
            expected_revision=self.expected_revision,
        )
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_thread_lifecycle_request"
        )
        return self


class ChatWorkspaceApprovalCaptureRequest(BaseModel):
    mutation_kind: Literal["draft_checkpoint", "lifecycle"]
    mutation_idempotency_key_ref: str = Field(min_length=1, max_length=200)
    draft_checkpoint: ChatDraftCheckpointRequest | None = None
    lifecycle: ChatThreadLifecycleRequest | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_capture(self) -> "ChatWorkspaceApprovalCaptureRequest":
        validate_chat_workspace_idempotency_ref(self.mutation_idempotency_key_ref)
        if self.mutation_kind == "draft_checkpoint":
            if self.draft_checkpoint is None or self.lifecycle is not None:
                raise ValueError(
                    "draft checkpoint approval must contain only its exact request"
                )
        elif self.lifecycle is None or self.draft_checkpoint is not None:
            raise ValueError("lifecycle approval must contain only its exact request")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_workspace_approval_capture_request"
        )
        return self

    def mutation_request(
        self,
    ) -> ChatDraftCheckpointRequest | ChatThreadLifecycleRequest:
        if self.mutation_kind == "draft_checkpoint":
            assert self.draft_checkpoint is not None
            return self.draft_checkpoint
        assert self.lifecycle is not None
        return self.lifecycle


class ChatThreadReadModel(BaseModel):
    contract_ref: str = CHAT_WORKSPACE_CONTRACT_REF
    thread_ref: str = Field(
        min_length=1,
        max_length=200,
        pattern=CHAT_THREAD_REF_RE.pattern,
    )
    display_name: str = Field(
        min_length=1,
        max_length=80,
        pattern=CHAT_DISPLAY_NAME_RE.pattern,
    )
    state: Literal["active", "archived"]
    revision: int = Field(ge=1, le=CHAT_WORKSPACE_MAX_REVISION)
    draft_present: bool
    draft_character_count: int = Field(ge=0, le=32_000)
    draft_fingerprint_ref: str = Field(
        min_length=1,
        max_length=200,
        pattern=CHAT_DRAFT_FINGERPRINT_RE.pattern,
    )
    draft_recovery_state: Literal["empty", "metadata_only_reentry_required"]
    draft_body_stored: bool = False
    created_at: str = Field(min_length=1, max_length=64)
    updated_at: str = Field(min_length=1, max_length=64)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_thread(self) -> "ChatThreadReadModel":
        if self.contract_ref != CHAT_WORKSPACE_CONTRACT_REF:
            raise ValueError("unexpected Chat workspace contract ref")
        for field_name in ("contract_ref", "thread_ref", "draft_fingerprint_ref"):
            validate_task_ref(getattr(self, field_name), field_name)
        validate_safe_task_text(self.display_name, "display_name")
        if self.draft_body_stored:
            raise ValueError("Chat workspace must not persist draft bodies")
        expected_recovery = (
            "metadata_only_reentry_required" if self.draft_present else "empty"
        )
        if self.draft_recovery_state != expected_recovery:
            raise ValueError("Chat draft recovery state does not match draft presence")
        if self.draft_present:
            if self.draft_character_count == 0:
                raise ValueError("a present Chat draft must have a character count")
            if self.draft_fingerprint_ref == CHAT_DRAFT_EMPTY_FINGERPRINT_REF:
                raise ValueError("a present Chat draft must have a content fingerprint")
        elif (
            self.draft_character_count != 0
            or self.draft_fingerprint_ref != CHAT_DRAFT_EMPTY_FINGERPRINT_REF
        ):
            raise ValueError("an empty Chat draft must use the empty fingerprint")
        created_at = _aware_datetime(self.created_at, "created_at")
        updated_at = _aware_datetime(self.updated_at, "updated_at")
        if updated_at < created_at:
            raise ValueError("Chat thread update cannot predate creation")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_thread_read_model"
        )
        return self


class ChatWorkspaceReadModel(BaseModel):
    schema_version: str = "chat-content-free-workspace.v1"
    contract_ref: str = CHAT_WORKSPACE_CONTRACT_REF
    source: str = CHAT_WORKSPACE_SOURCE
    status: Literal["safe_demo_ready", "workspace_ready"]
    threads: list[ChatThreadReadModel] = Field(default_factory=list, max_length=100)
    active_thread_ref: str | None = Field(default=None, max_length=200)
    route_refs: list[str] = Field(
        default_factory=lambda: list(CHAT_WORKSPACE_ROUTE_REFS),
        max_length=len(CHAT_WORKSPACE_ROUTE_REFS),
    )
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(CHAT_WORKSPACE_BLOCKED_STATE_REFS),
        max_length=len(CHAT_WORKSPACE_BLOCKED_STATE_REFS),
    )
    safe_summary: str = Field(min_length=1, max_length=500)
    next_safe_action: str = Field(min_length=1, max_length=300)
    draft_body_stored: bool = False
    model_call_enabled: bool = False
    send_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_workspace(self) -> "ChatWorkspaceReadModel":
        if self.contract_ref != CHAT_WORKSPACE_CONTRACT_REF:
            raise ValueError("unexpected Chat workspace contract ref")
        if self.source != CHAT_WORKSPACE_SOURCE:
            raise ValueError("unexpected Chat workspace source")
        validate_task_ref(self.contract_ref, "contract_ref")
        for value in self.blocked_state_refs:
            validate_task_ref(value, "blocked_state_refs")
        for value in self.route_refs:
            validate_safe_task_text(value, "route_refs")
        if tuple(self.route_refs) != CHAT_WORKSPACE_ROUTE_REFS:
            raise ValueError("Chat workspace route refs do not match the contract")
        if tuple(self.blocked_state_refs) != CHAT_WORKSPACE_BLOCKED_STATE_REFS:
            raise ValueError("Chat workspace blocked refs do not match the contract")
        thread_refs = [thread.thread_ref for thread in self.threads]
        if len(thread_refs) != len(set(thread_refs)):
            raise ValueError("Chat workspace thread refs must be unique")
        expected_status = "workspace_ready" if self.threads else "safe_demo_ready"
        if self.status != expected_status:
            raise ValueError("Chat workspace status does not match stored threads")
        if self.active_thread_ref is not None:
            validate_chat_thread_ref(self.active_thread_ref)
            if self.active_thread_ref not in {
                thread.thread_ref for thread in self.threads if thread.state == "active"
            }:
                raise ValueError(
                    "active Chat thread ref is not present in the workspace"
                )
        denied = (
            self.draft_body_stored,
            self.model_call_enabled,
            self.send_enabled,
            self.tool_execution_enabled,
            self.connector_write_enabled,
            self.production_authority_enabled,
        )
        if any(denied):
            raise ValueError("Chat workspace enabled denied authority")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.next_safe_action, "next_safe_action")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_workspace_read_model"
        )
        return self


class ChatCheckpointSnapshot(BaseModel):
    contract_ref: str = CHAT_WORKSPACE_CONTRACT_REF
    checkpoint_ref: str = Field(min_length=1, max_length=200)
    thread: ChatThreadReadModel

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_snapshot(self) -> "ChatCheckpointSnapshot":
        if self.contract_ref != CHAT_WORKSPACE_CONTRACT_REF:
            raise ValueError("unexpected Chat checkpoint snapshot contract ref")
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.checkpoint_ref, "checkpoint_ref")
        if self.thread.state != "active":
            raise ValueError("Chat checkpoint snapshot must bind active prior state")
        if self.checkpoint_ref != chat_workspace_checkpoint_ref(self.thread):
            raise ValueError("Chat checkpoint snapshot ref is not state-bound")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_checkpoint_snapshot"
        )
        return self


class ChatThreadMutationReceipt(BaseModel):
    contract_ref: str = CHAT_WORKSPACE_CONTRACT_REF
    mutation_kind: Literal["draft_checkpoint", "lifecycle"]
    lifecycle_action: Literal["archive", "recover"] | None = None
    thread: ChatThreadReadModel
    previous_checkpoint: ChatCheckpointSnapshot | None = None
    receipt_ref: str = Field(min_length=1, max_length=200)
    audit_ref: str = Field(min_length=1, max_length=200)
    evidence_ref: str = Field(min_length=1, max_length=200)
    idempotency_key_ref: str = Field(min_length=1, max_length=200)
    approval_idempotency_key_ref: str = Field(min_length=1, max_length=200)
    payload_fingerprint_ref: str = Field(min_length=1, max_length=200)
    approval_ref: str = Field(min_length=1, max_length=200)
    exact_approval_scope_ref: str = Field(min_length=1, max_length=200)
    approval_validation_ref: str = Field(min_length=1, max_length=200)
    safe_summary: str = Field(min_length=1, max_length=300)
    raw_draft_received: bool = False
    draft_body_stored: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    connector_write_performed: bool = False
    replayed: bool = False
    created_at: str = Field(
        default_factory=lambda: utc_now().isoformat(),
        min_length=1,
        max_length=64,
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "ChatThreadMutationReceipt":
        if self.contract_ref != CHAT_WORKSPACE_CONTRACT_REF:
            raise ValueError("unexpected Chat workspace receipt contract ref")
        for field_name in (
            "contract_ref",
            "receipt_ref",
            "audit_ref",
            "evidence_ref",
            "idempotency_key_ref",
            "approval_idempotency_key_ref",
            "payload_fingerprint_ref",
            "approval_ref",
            "exact_approval_scope_ref",
            "approval_validation_ref",
        ):
            validate_task_ref(getattr(self, field_name), field_name)
        validate_chat_workspace_idempotency_ref(self.idempotency_key_ref)
        validate_chat_workspace_idempotency_ref(self.approval_idempotency_key_ref)
        if self.mutation_kind == "draft_checkpoint" and self.lifecycle_action:
            raise ValueError("draft checkpoint cannot carry a lifecycle action")
        if self.mutation_kind == "lifecycle" and self.lifecycle_action is None:
            raise ValueError("lifecycle receipt must carry its exact action")
        if self.mutation_kind == "draft_checkpoint" and self.thread.state != "active":
            raise ValueError("draft checkpoint receipt must bind an active thread")
        if self.lifecycle_action == "archive" and self.thread.state != "archived":
            raise ValueError("archive receipt must bind an archived thread")
        if self.lifecycle_action == "recover" and self.thread.state != "active":
            raise ValueError("recover receipt must bind an active thread")
        if self.mutation_kind == "lifecycle" and self.previous_checkpoint is not None:
            raise ValueError("lifecycle receipt cannot carry a prior checkpoint")
        if self.mutation_kind == "draft_checkpoint":
            if self.thread.revision == 1:
                if self.previous_checkpoint is not None:
                    raise ValueError("first checkpoint cannot carry prior state")
            elif (
                self.previous_checkpoint is None
                or self.previous_checkpoint.thread.thread_ref != self.thread.thread_ref
                or self.previous_checkpoint.thread.revision != self.thread.revision - 1
            ):
                raise ValueError(
                    "checkpoint overwrite must bind the exact prior revision"
                )
        kind = self.lifecycle_action or self.mutation_kind
        expected_refs = {
            "receipt_ref": chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=self.thread.thread_ref,
                revision=self.thread.revision,
                suffix="receipt",
            ),
            "audit_ref": chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=self.thread.thread_ref,
                revision=self.thread.revision,
                suffix="audit",
            ),
            "evidence_ref": chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=self.thread.thread_ref,
                revision=self.thread.revision,
                suffix="evidence-ref",
            ),
        }
        for field_name, expected in expected_refs.items():
            if getattr(self, field_name) != expected:
                raise ValueError(f"Chat workspace {field_name} is not revision-bound")
        if not re.fullmatch(
            r"payload-fingerprint:chat-workspace:[0-9a-f]{64}",
            self.payload_fingerprint_ref,
        ):
            raise ValueError("Chat workspace payload fingerprint is invalid")
        expected_approval_refs = chat_workspace_approval_refs(
            mutation_kind=self.mutation_kind,
            lifecycle_action=self.lifecycle_action,
            thread_ref=self.thread.thread_ref,
            idempotency_key_ref=self.idempotency_key_ref,
            approval_idempotency_key_ref=self.approval_idempotency_key_ref,
            payload_fingerprint_ref=self.payload_fingerprint_ref,
        )
        for field_name in (
            "approval_ref",
            "exact_approval_scope_ref",
            "approval_validation_ref",
        ):
            if getattr(self, field_name) != expected_approval_refs[field_name]:
                raise ValueError(f"Chat workspace {field_name} is not request-bound")
        _aware_datetime(self.created_at, "created_at")
        if any(
            (
                self.raw_draft_received,
                self.draft_body_stored,
                self.model_call_performed,
                self.tool_execution_performed,
                self.connector_write_performed,
            )
        ):
            raise ValueError("Chat workspace receipt records denied behavior")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_thread_mutation_receipt"
        )
        return self


class ChatWorkspaceApprovalReceipt(BaseModel):
    contract_ref: str = CHAT_WORKSPACE_CONTRACT_REF
    mutation_kind: Literal["draft_checkpoint", "lifecycle"]
    lifecycle_action: Literal["archive", "recover"] | None = None
    thread_ref: str = Field(
        min_length=1,
        max_length=200,
        pattern=CHAT_THREAD_REF_RE.pattern,
    )
    idempotency_key_ref: str = Field(min_length=1, max_length=200)
    approval_idempotency_key_ref: str = Field(min_length=1, max_length=200)
    payload_fingerprint_ref: str = Field(min_length=1, max_length=200)
    approval_request_ref: str = Field(min_length=1, max_length=200)
    approval_ref: str = Field(min_length=1, max_length=200)
    exact_approval_scope_ref: str = Field(min_length=1, max_length=200)
    approval_validation_ref: str = Field(min_length=1, max_length=200)
    expires_at: str = Field(min_length=1, max_length=64)
    exact_scope_granted: bool = True
    mutation_performed: bool = False
    raw_draft_received: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_approval_receipt(self) -> "ChatWorkspaceApprovalReceipt":
        if self.contract_ref != CHAT_WORKSPACE_CONTRACT_REF:
            raise ValueError("unexpected Chat workspace approval contract ref")
        validate_chat_thread_ref(self.thread_ref)
        validate_chat_workspace_idempotency_ref(self.idempotency_key_ref)
        validate_chat_workspace_idempotency_ref(self.approval_idempotency_key_ref)
        if self.mutation_kind == "draft_checkpoint" and self.lifecycle_action:
            raise ValueError("draft approval cannot carry a lifecycle action")
        if self.mutation_kind == "lifecycle" and self.lifecycle_action is None:
            raise ValueError("lifecycle approval must carry its exact action")
        if not re.fullmatch(
            r"payload-fingerprint:chat-workspace:[0-9a-f]{64}",
            self.payload_fingerprint_ref,
        ):
            raise ValueError("Chat workspace payload fingerprint is invalid")
        expected = chat_workspace_approval_refs(
            mutation_kind=self.mutation_kind,
            lifecycle_action=self.lifecycle_action,
            thread_ref=self.thread_ref,
            idempotency_key_ref=self.idempotency_key_ref,
            approval_idempotency_key_ref=self.approval_idempotency_key_ref,
            payload_fingerprint_ref=self.payload_fingerprint_ref,
        )
        for field_name in (
            "approval_request_ref",
            "approval_ref",
            "exact_approval_scope_ref",
            "approval_validation_ref",
        ):
            if getattr(self, field_name) != expected[field_name]:
                raise ValueError(
                    f"Chat workspace approval {field_name} is not request-bound"
                )
        if not self.exact_scope_granted:
            raise ValueError("Chat workspace approval did not grant exact scope")
        if self.mutation_performed or self.raw_draft_received:
            raise ValueError(
                "Chat workspace approval capture performed denied behavior"
            )
        _aware_datetime(self.expires_at, "expires_at")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "chat_workspace_approval_receipt"
        )
        return self


def build_chat_workspace_read_model(
    threads: list[ChatThreadReadModel],
) -> ChatWorkspaceReadModel:
    active_thread_ref = next(
        (thread.thread_ref for thread in threads if thread.state == "active"),
        None,
    )
    return ChatWorkspaceReadModel(
        status="workspace_ready" if threads else "safe_demo_ready",
        threads=threads,
        active_thread_ref=active_thread_ref,
        safe_summary=(
            "Conversation organization and draft recovery metadata are owned by "
            "the Python core. Unsent draft bodies remain in the current browser "
            "session and are never sent to this route."
        ),
        next_safe_action=(
            "Start a draft without a model, or inspect local model readiness "
            "before requesting the separately governed redacted probe."
        ),
    )


def chat_workspace_payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"payload-fingerprint:chat-workspace:{digest}"


def chat_workspace_approval_refs(
    *,
    mutation_kind: Literal["draft_checkpoint", "lifecycle"],
    lifecycle_action: Literal["archive", "recover"] | None,
    thread_ref: str,
    idempotency_key_ref: str,
    approval_idempotency_key_ref: str,
    payload_fingerprint_ref: str,
) -> dict[str, str]:
    material = {
        "contract_ref": CHAT_WORKSPACE_CONTRACT_REF,
        "mutation_kind": mutation_kind,
        "lifecycle_action": lifecycle_action,
        "thread_ref": thread_ref,
        "idempotency_key_ref": idempotency_key_ref,
        "approval_idempotency_key_ref": approval_idempotency_key_ref,
        "payload_fingerprint_ref": payload_fingerprint_ref,
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "approval_idempotency_key_ref": approval_idempotency_key_ref,
        "approval_request_ref": (
            f"approval-request-ref:chat-workspace:sha256:{digest[:32]}"
        ),
        "approval_ref": f"approval-ref:chat-workspace:sha256:{digest[:32]}",
        "exact_approval_scope_ref": (
            f"approval-scope-ref:chat-workspace:sha256:{digest[:32]}"
        ),
        "approval_validation_ref": (
            f"approval-validation-ref:chat-workspace:sha256:{digest[:32]}"
        ),
        "event_ref": f"event-ref:chat-workspace-approval:sha256:{digest[:32]}",
        "run_ref": f"run-ref:chat-workspace:sha256:{digest[:32]}",
    }


def build_chat_workspace_approval_request(
    *,
    mutation_kind: Literal["draft_checkpoint", "lifecycle"],
    lifecycle_action: Literal["archive", "recover"] | None,
    thread_ref: str,
    idempotency_key_ref: str,
    approval_idempotency_key_ref: str,
    payload_fingerprint_ref: str,
) -> ApprovalRequest:
    refs = chat_workspace_approval_refs(
        mutation_kind=mutation_kind,
        lifecycle_action=lifecycle_action,
        thread_ref=thread_ref,
        idempotency_key_ref=idempotency_key_ref,
        approval_idempotency_key_ref=approval_idempotency_key_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    requested_action = (
        "chat_workspace_draft_checkpoint"
        if mutation_kind == "draft_checkpoint"
        else f"chat_workspace_{lifecycle_action}"
    )
    return ApprovalRequest(
        approval_request_id=refs["approval_request_ref"],
        run_id=refs["run_ref"],
        subject_type=ApprovalSubjectType.external_action,
        subject_id=thread_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=requested_action,
        purpose="Approve one exact content-free local Chat metadata mutation.",
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="chat_workspace_content_free_metadata",
            requires_redaction=True,
        ),
        resource_refs=[
            CHAT_WORKSPACE_CONTRACT_REF,
            thread_ref,
            idempotency_key_ref,
            approval_idempotency_key_ref,
            payload_fingerprint_ref,
            refs["exact_approval_scope_ref"],
        ],
        event_ref=refs["event_ref"],
        trace_id="trace-ref:chat-workspace:local-metadata-mutation",
    )


def validate_chat_thread_ref(thread_ref: str) -> None:
    validate_task_ref(thread_ref, "thread_ref")
    if CHAT_THREAD_REF_RE.fullmatch(thread_ref) is None:
        raise ValueError("thread_ref must be a bounded Chat workspace ref")


def validate_chat_workspace_idempotency_ref(idempotency_key_ref: str) -> None:
    if CHAT_WORKSPACE_IDEMPOTENCY_RE.fullmatch(idempotency_key_ref) is None:
        raise ValueError("idempotency_key_ref is not a bounded idempotency value")


def _validate_chat_workspace_metadata_refs(
    metadata_refs: list[str], *, expected_revision: int
) -> None:
    for value in metadata_refs:
        validate_task_ref(value, "metadata_refs")
    expected = [f"metadata-ref:chat-workspace:revision-{expected_revision}"]
    if metadata_refs and metadata_refs != expected:
        raise ValueError("Chat workspace metadata refs must bind the expected revision")


def chat_workspace_mutation_ref(
    *, kind: str, thread_ref: str, revision: int, suffix: str
) -> str:
    safe_thread = hashlib.sha256(thread_ref.encode("utf-8")).hexdigest()[:16]
    return f"{suffix}:chat-workspace:{kind}:{safe_thread}:revision-{revision}"


def chat_workspace_checkpoint_ref(thread: ChatThreadReadModel) -> str:
    payload = thread.model_dump(mode="json")
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"checkpoint-ref:chat-workspace:sha256:{digest}"


def _aware_datetime(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed
