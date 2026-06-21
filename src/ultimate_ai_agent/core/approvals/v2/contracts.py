from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.v2.enums import (
    ActionIntentStatus,
    ActionKind,
    ActionPolicyMode,
    ActionRiskLevel,
    ActionSideEffectClass,
    ActorTrustLevel,
    ApprovalAuthorityV2Status,
    ApprovalBindingStatus,
    ApprovalDecisionStatus,
    ApprovalGrantStatus,
    ApprovalScopeKind,
    ResourceRefKind,
)
from ultimate_ai_agent.core.approvals.v2.validation import (
    assert_no_execution_authorized,
    assert_no_execution_performed,
    assert_no_raw_action_content,
    validate_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)
from ultimate_ai_agent.core.time import utc_now


class ActorRef(BaseModel):
    actor_ref: str = Field(..., min_length=1)
    trust_level: ActorTrustLevel = ActorTrustLevel.user
    safe_label: str = ""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_actor(self) -> Any:
        validate_action_ref(self.actor_ref, "actor_ref")
        if self.safe_label:
            validate_safe_action_text(self.safe_label, "safe_label")
        return self


class ActionRef(BaseModel):
    action_ref: str = Field(..., min_length=1)
    action_kind: ActionKind
    risk_level: ActionRiskLevel = ActionRiskLevel.low
    side_effect_class: ActionSideEffectClass = ActionSideEffectClass.none
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_action(self) -> Any:
        validate_action_ref(self.action_ref, "action_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        return self


class ResourceRef(BaseModel):
    resource_ref: str = Field(..., min_length=1)
    resource_kind: ResourceRefKind
    safe_label: str = ""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_resource(self) -> Any:
        validate_action_ref(self.resource_ref, "resource_ref")
        if self.safe_label:
            validate_safe_action_text(self.safe_label, "safe_label")
        return self


class ApprovalScope(BaseModel):
    scope_ref: str = Field(..., min_length=1)
    scope_kind: ApprovalScopeKind = ApprovalScopeKind.single_action
    actor_ref: str = Field(..., min_length=1)
    action_ref: str = Field(..., min_length=1)
    resource_ref: str = Field(..., min_length=1)
    expires_at: Optional[datetime] = None
    replay_nonce: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_scope(self) -> Any:
        allow_wildcard = self.scope_kind == ApprovalScopeKind.blocked_wildcard
        validate_action_ref(self.scope_ref, "scope_ref")
        validate_action_ref(self.actor_ref, "actor_ref", allow_wildcard=allow_wildcard)
        validate_action_ref(self.action_ref, "action_ref", allow_wildcard=allow_wildcard)
        validate_action_ref(self.resource_ref, "resource_ref", allow_wildcard=allow_wildcard)
        if self.replay_nonce:
            validate_action_ref(self.replay_nonce, "replay_nonce")
        return self


class ApprovalGrant(BaseModel):
    grant_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    action_ref: str = Field(..., min_length=1)
    resource_ref: str = Field(..., min_length=1)
    scope: ApprovalScope
    status: ApprovalGrantStatus = ApprovalGrantStatus.active_for_policy_only
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    replay_nonce: Optional[str] = None
    used_replay_nonces: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_grant(self) -> Any:
        allow_wildcard = self.scope.scope_kind == ApprovalScopeKind.blocked_wildcard
        for value, field_name in [
            (self.grant_ref, "grant_ref"),
            (self.actor_ref, "actor_ref"),
            (self.action_ref, "action_ref"),
            (self.resource_ref, "resource_ref"),
        ]:
            validate_action_ref(value, field_name, allow_wildcard=allow_wildcard)
        if self.replay_nonce:
            validate_action_ref(self.replay_nonce, "replay_nonce")
        for nonce in self.used_replay_nonces:
            validate_action_ref(nonce, "used_replay_nonce")
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class ActionIntent(BaseModel):
    intent_id: str = Field(..., min_length=1)
    actor: ActorRef
    action: ActionRef
    resource: ResourceRef
    status: ActionIntentStatus = ActionIntentStatus.policy_evaluation_requested
    safe_summary: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    consent_ref: Optional[str] = None
    input_refs: List[str] = Field(default_factory=list)
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intent(self) -> Any:
        validate_action_ref(self.intent_id, "intent_id")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_action_text(self.approval_ref, "approval_ref")
        if self.consent_ref:
            validate_action_ref(self.consent_ref, "consent_ref")
        for ref in self.input_refs:
            validate_action_ref(ref, "input_ref")
        assert_no_raw_action_content(
            self.contains_raw_prompt,
            self.contains_raw_model_output,
            self.contains_raw_file_content,
            self.contains_raw_transcript,
        )
        validate_safe_action_payload(self.metadata, "metadata")
        return self


class ActionPolicy(BaseModel):
    policy_ref: str = "action-policy:m28-default"
    mode: ActionPolicyMode = ActionPolicyMode.evaluation_only
    safe_summary: str = "M28 policy-only action evaluation."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        validate_action_ref(self.policy_ref, "policy_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        return self


class ApprovalAuthorityV2(BaseModel):
    authority_ref: str = "approval-authority-v2:m28"
    status: ApprovalAuthorityV2Status = ApprovalAuthorityV2Status.policy_only
    safe_summary: str = "M28 non-executing approval authority contract."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_authority(self) -> Any:
        validate_action_ref(self.authority_ref, "authority_ref")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        return self


class ApprovalReceiptPlan(BaseModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    decision_id: str = Field(..., min_length=1)
    intent_id: str = Field(..., min_length=1)
    grant_ref: Optional[str] = None
    execution_authorized: bool = False
    execution_performed: bool = False
    raw_content_stored: bool = False
    memory_write_performed: bool = False
    file_mutation_performed: bool = False
    network_call_performed: bool = False
    safe_summary: str = "Non-authoritative approval receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> Any:
        assert_no_execution_authorized(self.execution_authorized)
        assert_no_execution_performed(self.execution_performed)
        if self.raw_content_stored:
            raise ValueError("M28 approval receipt plans must not store raw content")
        if self.memory_write_performed:
            raise ValueError("M28 approval receipt plans must not write memory")
        if self.file_mutation_performed:
            raise ValueError("M28 approval receipt plans must not mutate files")
        if self.network_call_performed:
            raise ValueError("M28 approval receipt plans must not call networks")
        validate_safe_action_text(self.safe_summary, "safe_summary")
        for ref in [self.receipt_plan_ref, self.decision_id, self.intent_id, *self.metadata_refs]:
            validate_action_ref(ref, "metadata_ref")
        if self.grant_ref:
            validate_action_ref(self.grant_ref, "grant_ref")
        return self


class ActionPolicyDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    intent_id: str = Field(..., min_length=1)
    status: ApprovalDecisionStatus
    binding_status: ApprovalBindingStatus = ApprovalBindingStatus.bound
    allowed_for_policy: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    receipt_plan: Optional[ApprovalReceiptPlan] = None
    no_memory_write_performed: bool = True
    no_file_mutation_performed: bool = True
    no_tool_execution_performed: bool = True
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    no_event_ledger_mutation_performed: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        assert_no_execution_authorized(self.execution_authorized)
        assert_no_execution_performed(self.execution_performed)
        if not self.no_memory_write_performed:
            raise ValueError("M28 decisions must not write memory")
        if not self.no_file_mutation_performed:
            raise ValueError("M28 decisions must not mutate files")
        if not self.no_tool_execution_performed:
            raise ValueError("M28 decisions must not execute tools")
        if not self.no_network_call_performed:
            raise ValueError("M28 decisions must not call networks")
        if not self.no_model_call_performed:
            raise ValueError("M28 decisions must not call models")
        if not self.no_event_ledger_mutation_performed:
            raise ValueError("M28 decisions must not mutate Event Ledger")
        validate_action_ref(self.decision_id, "decision_id")
        validate_action_ref(self.intent_id, "intent_id")
        validate_safe_action_text(self.safe_message, "safe_message")
        return self


ApprovalDecision = ActionPolicyDecision


class ApprovalAuthorityV2Manifest(BaseModel):
    baseline_version: str = "0.32.0"
    contract_version: str = "m28-approval-authority-v2-action-policy"
    action_execution_enabled: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    memory_write_enabled: bool = False
    network_action_enabled: bool = False
    browser_action_enabled: bool = False
    mobile_action_enabled: bool = False
    remote_execution_enabled: bool = False
    plugin_enable_enabled: bool = False
    model_action_enabled: bool = False
    wildcard_approval_enabled: bool = False
    approval_test_refs_enabled: bool = False
    backend_execution_routes_added: bool = False
    control_center_execute_controls_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> Any:
        blocked_true_fields = [
            "action_execution_enabled",
            "execution_authorized",
            "execution_performed",
            "tool_execution_enabled",
            "filesystem_mutation_enabled",
            "memory_write_enabled",
            "network_action_enabled",
            "browser_action_enabled",
            "mobile_action_enabled",
            "remote_execution_enabled",
            "plugin_enable_enabled",
            "model_action_enabled",
            "wildcard_approval_enabled",
            "approval_test_refs_enabled",
            "backend_execution_routes_added",
            "control_center_execute_controls_enabled",
            "production_authority_enabled",
        ]
        for field_name in blocked_true_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M28")
        return self
