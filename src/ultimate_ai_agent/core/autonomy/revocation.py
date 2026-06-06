from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.approvals import (
    ScopedApprovalBundle,
    validate_scoped_approval_bundle,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


REVOCATION_KILL_SWITCH_DOCS = [
    "docs/autonomy/REVOCATION_KILL_SWITCH.md",
    "docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md",
    "docs/autonomy/REVOCATION_KILL_SWITCH_NON_GOALS.md",
    "docs/autonomy/M67_TO_M68_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _RevocationKillSwitchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RevocationKillSwitchRecord(_RevocationKillSwitchModel):
    revocation_record_ref: str
    approval_bundle: ScopedApprovalBundle
    approval_refs: list[str]
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    bundle_ref: str
    source_scope_ref: str
    audit_view_ref: str
    simulation_result_ref: str
    revocation_ref: str
    audit_ref: str
    replay_ref: str
    record_valid_for_review: bool = True
    review_only: bool = True
    deterministic: bool = True
    revocation_requested: bool = True
    kill_switch_requested: bool = True
    actor_bound: bool = True
    resource_bound: bool = True
    capability_bound: bool = True
    allowlist_bound: bool = True
    non_transferable: bool = True
    replay_safe: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    revocation_performed: bool = False
    kill_switch_activated: bool = False
    session_stopped: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    session_active: bool = False
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
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.revocation_record_ref, "revocation_record_ref"),
            (self.actor_ref, "actor_ref"),
            (self.bundle_ref, "bundle_ref"),
            (self.source_scope_ref, "source_scope_ref"),
            (self.audit_view_ref, "audit_view_ref"),
            (self.simulation_result_ref, "simulation_result_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for refs, field_name, reason in [
            (self.approval_refs, "approval_ref", "APPROVAL_REF_REQUIRED"),
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
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_revocation_kill_switch_record(
    *,
    revocation_record_ref: str,
    approval_bundle: ScopedApprovalBundle,
    actor_ref: str,
    resource_refs: list[str],
    capability_refs: list[str],
    allowlist_refs: list[str],
    bundle_ref: str,
    source_scope_ref: str,
    audit_view_ref: str,
    simulation_result_ref: str,
    revocation_ref: str,
    audit_ref: str,
    replay_ref: str,
    approval_test_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> RevocationKillSwitchRecord:
    validated_bundle = validate_scoped_approval_bundle(approval_bundle)
    return validate_revocation_kill_switch_record(
        RevocationKillSwitchRecord(
            revocation_record_ref=revocation_record_ref,
            approval_bundle=validated_bundle,
            approval_refs=list(validated_bundle.approval_refs),
            actor_ref=actor_ref,
            resource_refs=resource_refs,
            capability_refs=capability_refs,
            allowlist_refs=allowlist_refs,
            bundle_ref=bundle_ref,
            source_scope_ref=source_scope_ref,
            audit_view_ref=audit_view_ref,
            simulation_result_ref=simulation_result_ref,
            revocation_ref=revocation_ref,
            audit_ref=audit_ref,
            replay_ref=replay_ref,
            record_valid_for_review=True,
            review_only=True,
            deterministic=True,
            revocation_requested=True,
            kill_switch_requested=True,
            actor_bound=True,
            resource_bound=True,
            capability_bound=True,
            allowlist_bound=True,
            non_transferable=True,
            replay_safe=True,
            approval_refs_are_identifiers_only=True,
            authority_granted=False,
            revocation_performed=False,
            kill_switch_activated=False,
            session_stopped=False,
            execution_performed=False,
            side_effects_performed=[],
            approval_test_ref=approval_test_ref,
            reason_codes=["M67_REVOCATION_KILL_SWITCH_REVIEW_ONLY"],
            safe_summary=(
                "M67 records scoped revocation and kill-switch intent for review only; it does "
                "not revoke a live bundle, stop a session, activate a switch, grant authority, or execute."
            ),
            metadata={} if metadata is None else metadata,
        )
    )


def validate_revocation_kill_switch_record(
    record: RevocationKillSwitchRecord,
) -> RevocationKillSwitchRecord:
    validated = RevocationKillSwitchRecord.model_validate(record.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED") from exc
    try:
        bundle = validate_scoped_approval_bundle(validated.approval_bundle)
    except ValueError as exc:
        message = str(exc)
        if "SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED" in message:
            raise ValueError("SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED") from exc
        for upstream, local in _BUNDLE_REASON_TRANSLATIONS.items():
            if upstream in message:
                raise ValueError(local) from exc
        raise
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if any(ref.startswith("approval_test_") for ref in validated.approval_refs):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _REVOCATION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _REVOCATION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    _validate_revocation_bindings(validated, bundle)
    return validated


def _validate_revocation_bindings(
    record: RevocationKillSwitchRecord,
    bundle: ScopedApprovalBundle,
) -> None:
    if record.bundle_ref != bundle.bundle_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_BUNDLE_BINDING_MISMATCH_DENIED")
    if record.source_scope_ref != bundle.source_scope_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_SCOPE_BINDING_MISMATCH_DENIED")
    if record.audit_view_ref != bundle.audit_view_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_AUDIT_VIEW_BINDING_MISMATCH_DENIED")
    if record.simulation_result_ref != bundle.simulation_result_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_SIMULATION_BINDING_MISMATCH_DENIED")
    if record.actor_ref != bundle.actor_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_ACTOR_BINDING_MISMATCH_DENIED")
    if record.resource_refs != bundle.resource_refs:
        raise ValueError("REVOCATION_KILL_SWITCH_RESOURCE_BINDING_MISMATCH_DENIED")
    if record.capability_refs != bundle.capability_refs:
        raise ValueError("REVOCATION_KILL_SWITCH_CAPABILITY_BINDING_MISMATCH_DENIED")
    if record.allowlist_refs != bundle.allowlist_refs:
        raise ValueError("REVOCATION_KILL_SWITCH_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if record.approval_refs != bundle.approval_refs:
        raise ValueError("REVOCATION_KILL_SWITCH_APPROVAL_BINDING_MISMATCH_DENIED")
    if record.revocation_ref != bundle.revocation_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_REVOCATION_BINDING_MISMATCH_DENIED")
    if record.audit_ref != bundle.audit_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_AUDIT_BINDING_MISMATCH_DENIED")
    if record.replay_ref != bundle.replay_ref:
        raise ValueError("REVOCATION_KILL_SWITCH_REPLAY_BINDING_MISMATCH_DENIED")


_REVOCATION_REQUIRED_TRUE = [
    ("record_valid_for_review", "REVIEW_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("revocation_requested", "REVOCATION_REQUEST_REQUIRED"),
    ("kill_switch_requested", "KILL_SWITCH_REQUEST_REQUIRED"),
    ("actor_bound", "ACTOR_BINDING_REQUIRED"),
    ("resource_bound", "RESOURCE_BINDING_REQUIRED"),
    ("capability_bound", "CAPABILITY_BINDING_REQUIRED"),
    ("allowlist_bound", "ALLOWLIST_REQUIRED"),
    ("non_transferable", "REVOCATION_KILL_SWITCH_NON_TRANSFERABLE_REQUIRED"),
    ("replay_safe", "AUDIT_REPLAY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]


_REVOCATION_DENIALS = [
    ("authority_granted", "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ("revocation_performed", "REVOCATION_ACTION_DENIED"),
    ("kill_switch_activated", "KILL_SWITCH_ACTIVATION_DENIED"),
    ("session_stopped", "AUTONOMY_SESSION_STOP_DENIED"),
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
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


_BUNDLE_REASON_TRANSLATIONS = {
    "APPROVAL_BUNDLE_SCOPE_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_SCOPE_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_AUDIT_VIEW_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_AUDIT_VIEW_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_SIMULATION_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_SIMULATION_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_ACTOR_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_RESOURCE_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_RESOURCE_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_CAPABILITY_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_CAPABILITY_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_ALLOWLIST_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_ALLOWLIST_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_REVOCATION_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_REVOCATION_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_AUDIT_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_AUDIT_BINDING_MISMATCH_DENIED"
    ),
    "APPROVAL_BUNDLE_REPLAY_BINDING_MISMATCH_DENIED": (
        "REVOCATION_KILL_SWITCH_REPLAY_BINDING_MISMATCH_DENIED"
    ),
}
