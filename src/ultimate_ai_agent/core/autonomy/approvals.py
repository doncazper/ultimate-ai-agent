from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.audit import (
    AutonomyAuditReplayView,
    validate_autonomy_audit_replay_view,
)
from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyRiskClass,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.sessions import (
    ScopedAutonomySessionScope,
    validate_scoped_autonomy_session_scope,
)


SCOPED_APPROVAL_BUNDLE_DOCS = [
    "docs/autonomy/SCOPED_APPROVAL_BUNDLES.md",
    "docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md",
    "docs/autonomy/SCOPED_APPROVAL_BUNDLE_NON_GOALS.md",
    "docs/autonomy/M66_TO_M67_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _ScopedApprovalBundleModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ScopedApprovalBundle(_ScopedApprovalBundleModel):
    bundle_ref: str
    source_scope: ScopedAutonomySessionScope
    audit_replay_view: AutonomyAuditReplayView
    approval_refs: list[str]
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    max_duration_seconds: int = Field(gt=0)
    risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    revocation_ref: str
    audit_ref: str
    replay_ref: str
    source_scope_ref: str
    audit_view_ref: str
    simulation_result_ref: str
    bundle_valid_for_review: bool = True
    review_only: bool = True
    deterministic: bool = True
    actor_bound: bool = True
    resource_bound: bool = True
    capability_bound: bool = True
    allowlist_bound: bool = True
    non_transferable: bool = True
    revocable: bool = True
    replay_safe: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    session_started: bool = False
    session_active: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_test_ref: str | None = None
    revoked: bool = False
    expired: bool = False
    replay_used: bool = False
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.bundle_ref, "bundle_ref"),
            (self.actor_ref, "actor_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.source_scope_ref, "source_scope_ref"),
            (self.audit_view_ref, "audit_view_ref"),
            (self.simulation_result_ref, "simulation_result_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for refs, field_name, reason in [
            (self.approval_refs, "approval_ref", "APPROVAL_BUNDLE_APPROVAL_REF_REQUIRED"),
            (self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED"),
            (self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED"),
            (self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED"),
        ]:
            if not refs:
                raise ValueError(reason)
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_scoped_approval_bundle(
    *,
    bundle_ref: str,
    source_scope: ScopedAutonomySessionScope,
    audit_replay_view: AutonomyAuditReplayView,
    approval_refs: list[str],
    actor_ref: str,
    resource_refs: list[str],
    capability_refs: list[str],
    allowlist_refs: list[str],
    max_duration_seconds: int,
    risk_class: AutonomyRiskClass,
    revocation_ref: str,
    audit_ref: str,
    replay_ref: str,
    approval_test_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ScopedApprovalBundle:
    validated_scope = validate_scoped_autonomy_session_scope(source_scope)
    validated_view = validate_autonomy_audit_replay_view(audit_replay_view)
    return validate_scoped_approval_bundle(
        ScopedApprovalBundle(
            bundle_ref=bundle_ref,
            source_scope=validated_scope,
            audit_replay_view=validated_view,
            approval_refs=approval_refs,
            actor_ref=actor_ref,
            resource_refs=resource_refs,
            capability_refs=capability_refs,
            allowlist_refs=allowlist_refs,
            max_duration_seconds=max_duration_seconds,
            risk_class=risk_class,
            revocation_ref=revocation_ref,
            audit_ref=audit_ref,
            replay_ref=replay_ref,
            source_scope_ref=validated_scope.scope_ref,
            audit_view_ref=validated_view.audit_view_ref,
            simulation_result_ref=validated_view.simulation_result_ref,
            bundle_valid_for_review=True,
            review_only=True,
            deterministic=True,
            actor_bound=True,
            resource_bound=True,
            capability_bound=True,
            allowlist_bound=True,
            non_transferable=True,
            revocable=True,
            replay_safe=True,
            approval_refs_are_identifiers_only=True,
            authority_granted=False,
            session_started=False,
            session_active=False,
            execution_performed=False,
            side_effects_performed=[],
            approval_test_ref=approval_test_ref,
            revoked=False,
            expired=False,
            replay_used=False,
            reason_codes=["M66_SCOPED_APPROVAL_BUNDLE_REVIEW_ONLY"],
            safe_summary=(
                "M66 groups exact scoped approval refs for review only; approval refs remain "
                "identifiers, no session starts, no authority is granted, and no execution occurs."
            ),
            metadata={} if metadata is None else metadata,
        )
    )


def validate_scoped_approval_bundle(bundle: ScopedApprovalBundle) -> ScopedApprovalBundle:
    validated = ScopedApprovalBundle.model_validate(bundle.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED") from exc
    try:
        source_scope = validate_scoped_autonomy_session_scope(validated.source_scope)
        audit_view = validate_autonomy_audit_replay_view(validated.audit_replay_view)
    except ValueError as exc:
        if "SECRET_LIKE_AUTONOMY_SESSION_CONTENT_DENIED" in str(exc):
            raise ValueError("SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED") from exc
        raise
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if any(ref.startswith("approval_test_") for ref in validated.approval_refs):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if len(validated.approval_refs) != len(set(validated.approval_refs)):
        raise ValueError("APPROVAL_BUNDLE_DUPLICATE_REF_DENIED")
    if validated.revoked:
        raise ValueError("APPROVAL_BUNDLE_REVOKED_DENIED")
    if validated.expired:
        raise ValueError("APPROVAL_BUNDLE_EXPIRED_DENIED")
    if validated.replay_used:
        raise ValueError("APPROVAL_BUNDLE_REPLAY_DENIED")
    for field_name, reason in _BUNDLE_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _BUNDLE_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    _validate_exact_bindings(validated, source_scope, audit_view)
    return validated


def _validate_exact_bindings(
    bundle: ScopedApprovalBundle,
    source_scope: ScopedAutonomySessionScope,
    audit_view: AutonomyAuditReplayView,
) -> None:
    if bundle.source_scope_ref != source_scope.scope_ref:
        raise ValueError("APPROVAL_BUNDLE_SCOPE_BINDING_MISMATCH_DENIED")
    if bundle.audit_view_ref != audit_view.audit_view_ref:
        raise ValueError("APPROVAL_BUNDLE_AUDIT_VIEW_BINDING_MISMATCH_DENIED")
    if bundle.simulation_result_ref != audit_view.simulation_result_ref:
        raise ValueError("APPROVAL_BUNDLE_SIMULATION_BINDING_MISMATCH_DENIED")
    if bundle.actor_ref != source_scope.actor_ref or bundle.actor_ref != audit_view.actor_ref:
        raise ValueError("APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED")
    if bundle.resource_refs != source_scope.resource_refs:
        raise ValueError("APPROVAL_BUNDLE_RESOURCE_BINDING_MISMATCH_DENIED")
    if bundle.capability_refs != source_scope.capability_refs:
        raise ValueError("APPROVAL_BUNDLE_CAPABILITY_BINDING_MISMATCH_DENIED")
    if bundle.allowlist_refs != source_scope.allowlist_refs:
        raise ValueError("APPROVAL_BUNDLE_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if bundle.max_duration_seconds != source_scope.max_duration_seconds:
        raise ValueError("APPROVAL_BUNDLE_DURATION_BINDING_MISMATCH_DENIED")
    if bundle.risk_class != source_scope.risk_class:
        raise ValueError("APPROVAL_BUNDLE_RISK_BINDING_MISMATCH_DENIED")
    if bundle.revocation_ref != source_scope.revocation_ref:
        raise ValueError("APPROVAL_BUNDLE_REVOCATION_BINDING_MISMATCH_DENIED")
    if bundle.audit_ref != source_scope.audit_ref or bundle.audit_ref != audit_view.audit_ref:
        raise ValueError("APPROVAL_BUNDLE_AUDIT_BINDING_MISMATCH_DENIED")
    if bundle.replay_ref != source_scope.replay_ref or bundle.replay_ref != audit_view.replay_ref:
        raise ValueError("APPROVAL_BUNDLE_REPLAY_BINDING_MISMATCH_DENIED")


_BUNDLE_REQUIRED_TRUE = [
    ("bundle_valid_for_review", "REVIEW_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("actor_bound", "ACTOR_BINDING_REQUIRED"),
    ("resource_bound", "RESOURCE_BINDING_REQUIRED"),
    ("capability_bound", "CAPABILITY_BINDING_REQUIRED"),
    ("allowlist_bound", "ALLOWLIST_REQUIRED"),
    ("non_transferable", "APPROVAL_BUNDLE_NON_TRANSFERABLE_REQUIRED"),
    ("revocable", "REVOCATION_REQUIRED"),
    ("replay_safe", "AUDIT_REPLAY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]

_BUNDLE_DENIALS = [
    ("authority_granted", "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ("session_started", "AUTONOMY_SESSION_START_DENIED"),
    ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
