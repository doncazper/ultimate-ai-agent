from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.plugin_install_review import (
    PluginInstallReviewDecision,
    PluginInstallReviewDecisionStatus,
    validate_plugin_install_review_decision,
)


BUILTIN_PLUGIN_EXECUTION_SANDBOX_DOCS = [
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_POLICY.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_RECEIPT_PLAN.md",
    "docs/tooling/PLUGIN_EXECUTION_SANDBOX_NON_GOALS.md",
    "docs/tooling/M96_TO_M97_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class BuiltInPluginExecutionSandboxStatus(str, Enum):
    builtin_test_plugin_allowed = "builtin_test_plugin_allowed"
    denied = "denied"


class _BuiltInPluginExecutionSandboxModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BuiltInPluginExecutionSandboxPolicy(_BuiltInPluginExecutionSandboxModel):
    policy_ref: str = "plugin-execution-sandbox-policy:m96"
    capability_exists: bool = True
    disabled_by_default: bool = True
    builtin_test_plugin_only: bool = True
    sandbox_required: bool = True
    manifest_permissions_enforced: bool = True
    audit_receipt_required: bool = True
    revocation_required: bool = True
    deterministic_result_required: bool = True
    safe_refs_only_required: bool = True
    external_plugin_loading_allowed: bool = False
    marketplace_plugin_allowed: bool = False
    arbitrary_plugin_code_allowed: bool = False
    runtime_import_allowed: bool = False
    networked_plugin_fetch_allowed: bool = False
    plugin_secret_access_allowed: bool = False
    raw_plugin_payload_allowed: bool = False
    shell_execution_allowed: bool = False
    network_access_allowed: bool = False
    browser_automation_allowed: bool = False
    filesystem_mutation_allowed: bool = False
    model_provider_call_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_allowed: bool = False
    allowed_plugin_refs: tuple[str, ...] = ("plugin:m96-built-in-test-noop",)
    allowed_action_refs: tuple[str, ...] = ("plugin-action:m96-noop",)
    allowed_permission_refs: tuple[str, ...] = ("plugin-permission:m96-built-in-test-noop",)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        for ref in self.allowed_plugin_refs:
            _validate_m61_ref(ref, "allowed_plugin_ref")
        for ref in self.allowed_action_refs:
            _validate_m61_ref(ref, "allowed_action_ref")
        for ref in self.allowed_permission_refs:
            _validate_m61_ref(ref, "allowed_permission_ref")
        return self


class BuiltInPluginExecutionSandboxRequest(_BuiltInPluginExecutionSandboxModel):
    request_ref: str
    plugin_ref: str
    action_ref: str
    permission_ref: str
    actor_ref: str
    scope_ref: str
    sandbox_ref: str
    audit_ref: str
    revocation_ref: str
    install_review_decision_ref: str
    manifest_security_decision_ref: str
    manifest_ref: str
    plugin_version: str
    safe_input_summary: str
    install_review_decision: PluginInstallReviewDecision
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    external_plugin_requested: bool = False
    marketplace_plugin_requested: bool = False
    arbitrary_plugin_code_requested: bool = False
    runtime_import_requested: bool = False
    networked_plugin_fetch_requested: bool = False
    plugin_secret_access_requested: bool = False
    raw_plugin_payload_requested: bool = False
    shell_execution_requested: bool = False
    network_access_requested: bool = False
    browser_automation_requested: bool = False
    filesystem_mutation_requested: bool = False
    model_provider_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.plugin_ref, "plugin_ref"),
            (self.action_ref, "action_ref"),
            (self.permission_ref, "permission_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.sandbox_ref, "sandbox_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.install_review_decision_ref, "install_review_decision_ref"),
            (self.manifest_security_decision_ref, "manifest_security_decision_ref"),
            (self.manifest_ref, "manifest_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_version(self.plugin_version)
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            if self.approval_test_ref.startswith("approval_test"):
                raise ValueError("APPROVAL_TEST_REF_DENIED")
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        for ref in self.authority_refs:
            _validate_m61_ref(ref, "authority_ref")
        _validate_safe_payload(self.safe_input_summary)
        return self


class BuiltInPluginExecutionSandboxReceiptPlan(_BuiltInPluginExecutionSandboxModel):
    receipt_ref: str
    request_ref: str
    plugin_ref: str
    action_ref: str
    sandbox_ref: str
    audit_ref: str
    safe_output_ref: str
    store_safe_refs_only: bool = True
    store_raw_plugin_payload: bool = False
    store_secret_material: bool = False
    external_plugin_loaded: bool = False
    runtime_import_performed: bool = False
    network_fetch_performed: bool = False
    shell_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.request_ref, "request_ref"),
            (self.plugin_ref, "plugin_ref"),
            (self.action_ref, "action_ref"),
            (self.sandbox_ref, "sandbox_ref"),
            (self.audit_ref, "audit_ref"),
            (self.safe_output_ref, "safe_output_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class BuiltInPluginExecutionSandboxDecision(_BuiltInPluginExecutionSandboxModel):
    decision_ref: str
    request_ref: str
    plugin_ref: str
    action_ref: str
    permission_ref: str
    actor_ref: str
    scope_ref: str
    sandbox_ref: str
    audit_ref: str
    revocation_ref: str
    install_review_decision_ref: str
    manifest_security_decision_ref: str
    status: BuiltInPluginExecutionSandboxStatus
    capability_exists: bool = True
    disabled_by_default: bool = True
    builtin_test_plugin_only: bool = True
    sandbox_enforced: bool = True
    manifest_permissions_enforced: bool = True
    audit_receipt_created: bool = True
    revocation_bound: bool = True
    deterministic_result: bool = True
    safe_refs_only: bool = True
    built_in_test_plugin_invoked: bool = True
    external_plugin_loading_allowed: bool = False
    marketplace_plugin_allowed: bool = False
    arbitrary_plugin_code_allowed: bool = False
    runtime_import_allowed: bool = False
    networked_plugin_fetch_allowed: bool = False
    plugin_secret_access_allowed: bool = False
    raw_plugin_payload_allowed: bool = False
    shell_execution_allowed: bool = False
    network_access_allowed: bool = False
    browser_automation_allowed: bool = False
    filesystem_mutation_allowed: bool = False
    model_provider_call_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    receipt_plan: BuiltInPluginExecutionSandboxReceiptPlan
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.plugin_ref, "plugin_ref"),
            (self.action_ref, "action_ref"),
            (self.permission_ref, "permission_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.sandbox_ref, "sandbox_ref"),
            (self.audit_ref, "audit_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.install_review_decision_ref, "install_review_decision_ref"),
            (self.manifest_security_decision_ref, "manifest_security_decision_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_builtin_plugin_execution_sandbox_policy(
    policy: BuiltInPluginExecutionSandboxPolicy | None = None,
) -> BuiltInPluginExecutionSandboxPolicy:
    validated = BuiltInPluginExecutionSandboxPolicy.model_validate(
        (policy or BuiltInPluginExecutionSandboxPolicy()).model_dump(mode="python", round_trip=True)
    )
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.allowed_plugin_refs:
        raise ValueError("BUILTIN_PLUGIN_ALLOWLIST_REQUIRED")
    if len(set(validated.allowed_plugin_refs)) != len(validated.allowed_plugin_refs):
        raise ValueError("BUILTIN_PLUGIN_ALLOWLIST_DUPLICATE_DENIED")
    if not validated.allowed_action_refs:
        raise ValueError("PLUGIN_ACTION_ALLOWLIST_REQUIRED")
    if not validated.allowed_permission_refs:
        raise ValueError("PLUGIN_PERMISSION_ALLOWLIST_REQUIRED")
    _validate_safe_payload(validated.metadata)
    return validated


def validate_builtin_plugin_execution_sandbox_request(
    request: BuiltInPluginExecutionSandboxRequest,
    policy: BuiltInPluginExecutionSandboxPolicy | None = None,
) -> BuiltInPluginExecutionSandboxRequest:
    active_policy = validate_builtin_plugin_execution_sandbox_policy(policy)
    payload = request.model_dump(mode="python", round_trip=True)
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = BuiltInPluginExecutionSandboxRequest.model_validate(payload)
    install_decision = validate_plugin_install_review_decision(validated.install_review_decision)
    if install_decision.status != PluginInstallReviewDecisionStatus.install_review_ready_disabled:
        raise ValueError("PLUGIN_INSTALL_REVIEW_DECISION_REQUIRED")
    if validated.install_review_decision_ref != install_decision.decision_ref:
        raise ValueError("PLUGIN_INSTALL_REVIEW_BINDING_MISMATCH")
    if validated.manifest_security_decision_ref != install_decision.manifest_security_decision_ref:
        raise ValueError("PLUGIN_MANIFEST_SECURITY_BINDING_MISMATCH")
    if validated.manifest_ref != install_decision.manifest_ref:
        raise ValueError("PLUGIN_MANIFEST_BINDING_MISMATCH")
    if validated.plugin_ref != install_decision.plugin_ref:
        raise ValueError("PLUGIN_REF_BINDING_MISMATCH")
    if validated.plugin_version != install_decision.plugin_version:
        raise ValueError("PLUGIN_VERSION_BINDING_MISMATCH")
    if validated.actor_ref != install_decision.actor_ref:
        raise ValueError("PLUGIN_ACTOR_BINDING_MISMATCH")
    if validated.plugin_ref not in active_policy.allowed_plugin_refs:
        raise ValueError("EXTERNAL_PLUGIN_LOADING_DENIED")
    if validated.action_ref not in active_policy.allowed_action_refs:
        raise ValueError("PLUGIN_ACTION_NOT_ALLOWLISTED")
    if validated.permission_ref not in active_policy.allowed_permission_refs:
        raise ValueError("PLUGIN_MANIFEST_PERMISSION_DENIED")
    if validated.approval_ref:
        raise ValueError("APPROVAL_REF_NOT_PLUGIN_EXECUTION_AUTHORITY")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for ref in validated.authority_refs:
        if ref.startswith("approval_test"):
            raise ValueError("APPROVAL_TEST_REF_DENIED")
        if ref.split(":", 1)[0] in {
            "approval",
            "context-pack",
            "memory",
            "model",
            "openwebui",
            "task-plan",
            "tool-intent",
            "runtime",
        }:
            raise ValueError("AUTHORITY_REF_NOT_PLUGIN_EXECUTION_AUTHORITY")
    if validated.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    _validate_safe_payload(validated.metadata)
    return validated


def build_builtin_plugin_execution_sandbox_decision(
    request: BuiltInPluginExecutionSandboxRequest,
    policy: BuiltInPluginExecutionSandboxPolicy | None = None,
) -> BuiltInPluginExecutionSandboxDecision:
    active_policy = validate_builtin_plugin_execution_sandbox_policy(policy)
    validated_request = validate_builtin_plugin_execution_sandbox_request(request, active_policy)
    safe_output_ref = _invoke_builtin_test_plugin(validated_request.plugin_ref, validated_request.action_ref)
    receipt = BuiltInPluginExecutionSandboxReceiptPlan(
        receipt_ref=f"plugin-execution-sandbox-receipt:{_ref_suffix(validated_request.request_ref)}",
        request_ref=validated_request.request_ref,
        plugin_ref=validated_request.plugin_ref,
        action_ref=validated_request.action_ref,
        sandbox_ref=validated_request.sandbox_ref,
        audit_ref=validated_request.audit_ref,
        safe_output_ref=safe_output_ref,
    )
    return validate_builtin_plugin_execution_sandbox_decision(
        BuiltInPluginExecutionSandboxDecision(
            decision_ref=f"plugin-execution-sandbox-decision:{_ref_suffix(validated_request.request_ref)}",
            request_ref=validated_request.request_ref,
            plugin_ref=validated_request.plugin_ref,
            action_ref=validated_request.action_ref,
            permission_ref=validated_request.permission_ref,
            actor_ref=validated_request.actor_ref,
            scope_ref=validated_request.scope_ref,
            sandbox_ref=validated_request.sandbox_ref,
            audit_ref=validated_request.audit_ref,
            revocation_ref=validated_request.revocation_ref,
            install_review_decision_ref=validated_request.install_review_decision_ref,
            manifest_security_decision_ref=validated_request.manifest_security_decision_ref,
            status=BuiltInPluginExecutionSandboxStatus.builtin_test_plugin_allowed,
            receipt_plan=receipt,
            reason_codes=[
                "M96_BUILTIN_TEST_PLUGIN_SANDBOX_ALLOWED",
                "BUILTIN_TEST_PLUGIN_ONLY",
                "PLUGIN_MANIFEST_PERMISSIONS_ENFORCED",
                "NO_EXTERNAL_PLUGIN_LOADING",
                "NO_ARBITRARY_PLUGIN_CODE",
                "NO_NETWORKED_PLUGIN_FETCH",
                "M97_REMAINS_FUTURE",
            ],
            safe_summary=(
                "M96 allows only a deterministic built-in test plugin sandbox invocation with "
                "safe refs, manifest permission checks, audit receipt, revocation binding, and "
                "no external loading, arbitrary code, fetch, shell, network, memory, context, route, "
                "dependency, or production authority."
            ),
        )
    )


def validate_builtin_plugin_execution_sandbox_decision(
    decision: BuiltInPluginExecutionSandboxDecision,
) -> BuiltInPluginExecutionSandboxDecision:
    validated = BuiltInPluginExecutionSandboxDecision.model_validate(
        decision.model_dump(mode="python", round_trip=True)
    )
    for field_name, reason in _DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_builtin_plugin_execution_sandbox_receipt_plan(validated.receipt_plan)
    return validated


def _validate_builtin_plugin_execution_sandbox_receipt_plan(
    receipt_plan: BuiltInPluginExecutionSandboxReceiptPlan,
) -> BuiltInPluginExecutionSandboxReceiptPlan:
    validated = BuiltInPluginExecutionSandboxReceiptPlan.model_validate(
        receipt_plan.model_dump(mode="python", round_trip=True)
    )
    if not validated.store_safe_refs_only:
        raise ValueError("SAFE_REFS_ONLY_REQUIRED")
    for field_name, reason in _RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    return validated


def _invoke_builtin_test_plugin(plugin_ref: str, action_ref: str) -> str:
    if plugin_ref != "plugin:m96-built-in-test-noop" or action_ref != "plugin-action:m96-noop":
        raise ValueError("BUILTIN_TEST_PLUGIN_NOT_ALLOWLISTED")
    return "plugin-output:m96-built-in-test-noop-ok"


_POLICY_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("builtin_test_plugin_only", "BUILTIN_TEST_PLUGIN_ONLY_REQUIRED"),
    ("sandbox_required", "PLUGIN_SANDBOX_REQUIRED"),
    ("manifest_permissions_enforced", "PLUGIN_MANIFEST_PERMISSION_REQUIRED"),
    ("audit_receipt_required", "PLUGIN_AUDIT_RECEIPT_REQUIRED"),
    ("revocation_required", "PLUGIN_REVOCATION_REQUIRED"),
    ("deterministic_result_required", "DETERMINISTIC_PLUGIN_RESULT_REQUIRED"),
    ("safe_refs_only_required", "SAFE_REFS_ONLY_REQUIRED"),
]

_POLICY_DENIALS = [
    ("external_plugin_loading_allowed", "EXTERNAL_PLUGIN_LOADING_DENIED"),
    ("marketplace_plugin_allowed", "MARKETPLACE_PLUGIN_DENIED"),
    ("arbitrary_plugin_code_allowed", "ARBITRARY_PLUGIN_CODE_DENIED"),
    ("runtime_import_allowed", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("networked_plugin_fetch_allowed", "NETWORKED_PLUGIN_FETCH_DENIED"),
    ("plugin_secret_access_allowed", "PLUGIN_SECRET_ACCESS_DENIED"),
    ("raw_plugin_payload_allowed", "RAW_PLUGIN_PAYLOAD_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("network_access_allowed", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("filesystem_mutation_allowed", "FILESYSTEM_MUTATION_DENIED"),
    ("model_provider_call_allowed", "PROVIDER_MODEL_CALL_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_DENIALS = [
    ("external_plugin_requested", "EXTERNAL_PLUGIN_LOADING_DENIED"),
    ("marketplace_plugin_requested", "MARKETPLACE_PLUGIN_DENIED"),
    ("arbitrary_plugin_code_requested", "ARBITRARY_PLUGIN_CODE_DENIED"),
    ("runtime_import_requested", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("networked_plugin_fetch_requested", "NETWORKED_PLUGIN_FETCH_DENIED"),
    ("plugin_secret_access_requested", "PLUGIN_SECRET_ACCESS_DENIED"),
    ("raw_plugin_payload_requested", "RAW_PLUGIN_PAYLOAD_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
    ("model_provider_call_requested", "PROVIDER_MODEL_CALL_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_DECISION_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTS_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("builtin_test_plugin_only", "BUILTIN_TEST_PLUGIN_ONLY_REQUIRED"),
    ("sandbox_enforced", "PLUGIN_SANDBOX_REQUIRED"),
    ("manifest_permissions_enforced", "PLUGIN_MANIFEST_PERMISSION_REQUIRED"),
    ("audit_receipt_created", "PLUGIN_AUDIT_RECEIPT_REQUIRED"),
    ("revocation_bound", "PLUGIN_REVOCATION_REQUIRED"),
    ("deterministic_result", "DETERMINISTIC_PLUGIN_RESULT_REQUIRED"),
    ("safe_refs_only", "SAFE_REFS_ONLY_REQUIRED"),
    ("built_in_test_plugin_invoked", "BUILTIN_TEST_PLUGIN_INVOCATION_REQUIRED"),
]

_DECISION_DENIALS = [
    ("external_plugin_loading_allowed", "EXTERNAL_PLUGIN_LOADING_DENIED"),
    ("marketplace_plugin_allowed", "MARKETPLACE_PLUGIN_DENIED"),
    ("arbitrary_plugin_code_allowed", "ARBITRARY_PLUGIN_CODE_DENIED"),
    ("runtime_import_allowed", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("networked_plugin_fetch_allowed", "NETWORKED_PLUGIN_FETCH_DENIED"),
    ("plugin_secret_access_allowed", "PLUGIN_SECRET_ACCESS_DENIED"),
    ("raw_plugin_payload_allowed", "RAW_PLUGIN_PAYLOAD_DENIED"),
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("network_access_allowed", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("filesystem_mutation_allowed", "FILESYSTEM_MUTATION_DENIED"),
    ("model_provider_call_allowed", "PROVIDER_MODEL_CALL_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]

_RECEIPT_DENIALS = [
    ("store_raw_plugin_payload", "RAW_PLUGIN_PAYLOAD_DENIED"),
    ("store_secret_material", "PLUGIN_SECRET_ACCESS_DENIED"),
    ("external_plugin_loaded", "EXTERNAL_PLUGIN_LOADING_DENIED"),
    ("runtime_import_performed", "PLUGIN_RUNTIME_IMPORT_DENIED"),
    ("network_fetch_performed", "NETWORKED_PLUGIN_FETCH_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


def _validate_safe_version(value: str) -> None:
    if not value or "/" in value or "\\" in value or ":" in value:
        raise ValueError("PLUGIN_VERSION_INVALID")
    _validate_safe_payload(value)
