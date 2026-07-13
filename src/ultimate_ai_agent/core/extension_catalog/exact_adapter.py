from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDispatchAdapterDescriptor,
    AuthorityDispatchAdapterResult,
    AuthorityDispatchRequest,
    AuthorityDomain,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    ToolRuntimeAuthorityDispatchAdapter,
    authority_dispatch_execution_ref,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate
from ultimate_ai_agent.core.extension_catalog.ecosystem import (
    validate_extension_catalog_entry_for_development,
)
from ultimate_ai_agent.core.extension_catalog.runtime import (
    build_default_inspectable_extension_catalog,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_NAME,
    FILESYSTEM_METADATA_TOOL_REF,
    FILESYSTEM_OPAQUE_PATH_REF_VERSION,
    FilesystemSafeRoot,
    ToolInvocationKind,
    ToolInvocationRequest,
    filesystem_opaque_path_ref,
    normalize_relative_metadata_path,
)


EXACT_EXTENSION_ADAPTER_SCHEMA_VERSION = "uaa-exact-extension-adapter.v1"
EXACT_EXTENSION_ADAPTER_CONTRACT_REF = "contract-ref:exact-extension-adapter:v1"
EXACT_EXTENSION_PACKAGE_REF = "extension-package:uaa-plugin-skill-boundary"
EXACT_EXTENSION_CATALOG_ENTRY_REF = (
    "inspectable-catalog-entry:uaa-plugin-skill-boundary"
)
EXACT_EXTENSION_MANIFEST_REF = "plugin-skill-manifest:uaa-plugin-skill-boundary"
EXACT_EXTENSION_VERSION_REF = "version:uaa-p1-024"
EXACT_EXTENSION_CAPABILITY_REF = "capability:extension-metadata-inspection"
EXACT_EXTENSION_ADAPTER_REF = (
    "authority-adapter-ref:exact-extension-metadata-inspection-v1"
)
EXACT_EXTENSION_REGISTRATION_REF = (
    "extension-adapter-registration:metadata-inspection-v1"
)
EXACT_EXTENSION_LANE_REF = "lane-ref:extension-metadata-inspection-exact-v1"
EXACT_EXTENSION_SAFE_DISABLE_REF = "safe-disable-ref:extension-metadata-inspection"
EXACT_EXTENSION_ROLLBACK_REF = "rollback-ref:extension-metadata-inspection:disable"
EXACT_EXTENSION_RECEIPT_CONTRACT_REF = (
    "receipt-contract-ref:authority-dispatch:exact-extension-v1"
)
EXACT_EXTENSION_IMPLEMENTATION_REF = (
    "adapter-implementation-ref:exact-extension-metadata-inspection-v1"
)
EXACT_EXTENSION_ADMISSION_REF = (
    "admission-validator-ref:exact-extension-metadata-inspection-v1"
)
EXACT_EXTENSION_MANIFEST_MAX_BYTES = 64 * 1024


class ExactExtensionCompatibilityStatus(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    unknown = "unknown"


class ExactExtensionConfigurationStatus(str, Enum):
    configured = "configured"
    not_configured = "not_configured"
    invalid = "invalid"
    unknown = "unknown"


class ExactExtensionHealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    stale = "stale"
    unknown = "unknown"


class ExactExtensionBudgetStatus(str, Enum):
    available = "available"
    constrained = "constrained"
    exhausted = "exhausted"
    unknown = "unknown"


class ExactExtensionSafeDisableStatus(str, Enum):
    inactive = "inactive"
    active = "active"
    unknown = "unknown"


class ExactExtensionKillSwitchStatus(str, Enum):
    inactive = "inactive"
    active = "active"
    unknown = "unknown"


class _ExactExtensionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=True,
    )


class ExactExtensionAdapterManifest(_ExactExtensionModel):
    schema_version: Literal["uaa-exact-extension-adapter.v1"] = (
        EXACT_EXTENSION_ADAPTER_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:exact-extension-adapter:v1"] = (
        EXACT_EXTENSION_ADAPTER_CONTRACT_REF
    )
    registration_ref: Literal[
        "extension-adapter-registration:metadata-inspection-v1"
    ] = EXACT_EXTENSION_REGISTRATION_REF
    package_ref: Literal["extension-package:uaa-plugin-skill-boundary"] = (
        EXACT_EXTENSION_PACKAGE_REF
    )
    catalog_entry_ref: Literal[
        "inspectable-catalog-entry:uaa-plugin-skill-boundary"
    ] = EXACT_EXTENSION_CATALOG_ENTRY_REF
    manifest_ref: Literal["plugin-skill-manifest:uaa-plugin-skill-boundary"] = (
        EXACT_EXTENSION_MANIFEST_REF
    )
    version_ref: Literal["version:uaa-p1-024"] = EXACT_EXTENSION_VERSION_REF
    capability_ref: Literal["capability:extension-metadata-inspection"] = (
        EXACT_EXTENSION_CAPABILITY_REF
    )
    adapter_ref: Literal[
        "authority-adapter-ref:exact-extension-metadata-inspection-v1"
    ] = EXACT_EXTENSION_ADAPTER_REF
    lane_ref: Literal["lane-ref:extension-metadata-inspection-exact-v1"] = (
        EXACT_EXTENSION_LANE_REF
    )
    implementation_ref: Literal[
        "adapter-implementation-ref:exact-extension-metadata-inspection-v1"
    ] = EXACT_EXTENSION_IMPLEMENTATION_REF
    authority_domain: Literal["files"] = "files"
    authority_capability: Literal["read"] = "read"
    tool_ref: Literal["tool:filesystem_metadata.v1"] = FILESYSTEM_METADATA_TOOL_REF
    side_effect_class: Literal["read_only_local"] = "read_only_local"
    target_scope: Literal["injected_safe_root_exact_path"] = (
        "injected_safe_root_exact_path"
    )
    approval_posture: Literal["current_policy_and_exact_lease"] = (
        "current_policy_and_exact_lease"
    )
    safe_disable_ref: Literal["safe-disable-ref:extension-metadata-inspection"] = (
        EXACT_EXTENSION_SAFE_DISABLE_REF
    )
    rollback_ref: Literal["rollback-ref:extension-metadata-inspection:disable"] = (
        EXACT_EXTENSION_ROLLBACK_REF
    )
    receipt_contract_ref: Literal[
        "receipt-contract-ref:authority-dispatch:exact-extension-v1"
    ] = EXACT_EXTENSION_RECEIPT_CONTRACT_REF
    provenance_ref: Literal["review:uaa-p1-024"] = "review:uaa-p1-024"
    validation_ref: Literal[
        "extension-developer-validation:uaa-plugin-skill-boundary"
    ] = "extension-developer-validation:uaa-plugin-skill-boundary"
    request_scoped_policy_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    exact_target_binding_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    kill_switch_check_required: Literal[True] = True
    safe_disable_check_required: Literal[True] = True
    idempotency_required: Literal[True] = True
    receipt_required: Literal[True] = True
    rollback_required: Literal[True] = True
    runtime_import_enabled: Literal[False] = False
    arbitrary_extension_code_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    environment_access_enabled: Literal[False] = False
    home_directory_access_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False
    safe_summary: str = Field(
        default=(
            "One repo-owned extension registration delegates exact safe-root "
            "metadata inspection to UAA's bounded core tool through the current "
            "AuthorityDispatcher; extension package code is never imported."
        ),
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "ExactExtensionAdapterManifest":
        refs = {
            "contract_ref": self.contract_ref,
            "registration_ref": self.registration_ref,
            "package_ref": self.package_ref,
            "catalog_entry_ref": self.catalog_entry_ref,
            "manifest_ref": self.manifest_ref,
            "version_ref": self.version_ref,
            "capability_ref": self.capability_ref,
            "adapter_ref": self.adapter_ref,
            "lane_ref": self.lane_ref,
            "implementation_ref": self.implementation_ref,
            "tool_ref": self.tool_ref,
            "safe_disable_ref": self.safe_disable_ref,
            "rollback_ref": self.rollback_ref,
            "receipt_contract_ref": self.receipt_contract_ref,
            "provenance_ref": self.provenance_ref,
            "validation_ref": self.validation_ref,
        }
        for field_name, value in refs.items():
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "exact_extension_manifest"
        )
        if self.registration_ref != EXACT_EXTENSION_REGISTRATION_REF:
            raise ValueError("EXACT_EXTENSION_REGISTRATION_NOT_ALLOWLISTED")
        exact_bindings = {
            "contract_ref": EXACT_EXTENSION_ADAPTER_CONTRACT_REF,
            "package_ref": EXACT_EXTENSION_PACKAGE_REF,
            "catalog_entry_ref": EXACT_EXTENSION_CATALOG_ENTRY_REF,
            "manifest_ref": EXACT_EXTENSION_MANIFEST_REF,
            "version_ref": EXACT_EXTENSION_VERSION_REF,
            "capability_ref": EXACT_EXTENSION_CAPABILITY_REF,
            "adapter_ref": EXACT_EXTENSION_ADAPTER_REF,
            "lane_ref": EXACT_EXTENSION_LANE_REF,
            "implementation_ref": EXACT_EXTENSION_IMPLEMENTATION_REF,
            "tool_ref": FILESYSTEM_METADATA_TOOL_REF,
            "safe_disable_ref": EXACT_EXTENSION_SAFE_DISABLE_REF,
            "rollback_ref": EXACT_EXTENSION_ROLLBACK_REF,
            "receipt_contract_ref": EXACT_EXTENSION_RECEIPT_CONTRACT_REF,
        }
        for field_name, expected_value in exact_bindings.items():
            if getattr(self, field_name) != expected_value:
                raise ValueError(f"EXACT_EXTENSION_{field_name.upper()}_MISMATCH")
        return self


class ExactExtensionRuntimePosture(_ExactExtensionModel):
    posture_ref: str = "extension-runtime-posture:metadata-inspection:configured"
    compatibility_status: ExactExtensionCompatibilityStatus = (
        ExactExtensionCompatibilityStatus.supported
    )
    configuration_status: ExactExtensionConfigurationStatus = (
        ExactExtensionConfigurationStatus.configured
    )
    health_status: ExactExtensionHealthStatus = ExactExtensionHealthStatus.healthy
    budget_status: ExactExtensionBudgetStatus = ExactExtensionBudgetStatus.available
    safe_disable_status: ExactExtensionSafeDisableStatus = (
        ExactExtensionSafeDisableStatus.inactive
    )
    kill_switch_status: ExactExtensionKillSwitchStatus = (
        ExactExtensionKillSwitchStatus.inactive
    )
    evidence_refs: list[str] = Field(
        default_factory=lambda: [
            "evidence-ref:exact-extension:manifest-pinned",
            "evidence-ref:exact-extension:core-tool-binding",
        ],
        min_length=1,
        max_length=16,
    )
    safe_summary: str = Field(
        default=(
            "Injected exact-extension observations are ready for one fresh "
            "request-scoped dispatcher evaluation; they grant no authority."
        ),
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_posture(self) -> "ExactExtensionRuntimePosture":
        validate_task_ref(self.posture_ref, "posture_ref")
        for ref in self.evidence_refs:
            validate_task_ref(ref, "evidence_ref")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        return self


class ExactExtensionAdapterReadModel(_ExactExtensionModel):
    schema_version: Literal["uaa-exact-extension-adapter-read-model.v1"] = (
        "uaa-exact-extension-adapter-read-model.v1"
    )
    manifest: ExactExtensionAdapterManifest
    runtime_posture: ExactExtensionRuntimePosture
    catalog_validation_status: Literal["validated_metadata_only"] = (
        "validated_metadata_only"
    )
    ready_for_request_scoped_evaluation: bool
    blocker_codes: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list, min_length=1)
    invocation_authorized: Literal[False] = False
    execution_performed: Literal[False] = False
    global_extension_runtime_enabled: Literal[False] = False
    arbitrary_runtime_import_enabled: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_read_model(self) -> "ExactExtensionAdapterReadModel":
        if self.ready_for_request_scoped_evaluation == bool(self.blocker_codes):
            raise ValueError("EXACT_EXTENSION_READINESS_BLOCKER_CONTRADICTION")
        return self


def build_default_exact_extension_adapter_manifest() -> ExactExtensionAdapterManifest:
    return ExactExtensionAdapterManifest()


def exact_extension_runtime_blocker_codes(
    posture: ExactExtensionRuntimePosture,
) -> list[str]:
    blockers: list[str] = []
    if (
        posture.compatibility_status
        != ExactExtensionCompatibilityStatus.supported.value
    ):
        blockers.append("EXTENSION_COMPATIBILITY_NOT_SUPPORTED")
    if (
        posture.configuration_status
        != ExactExtensionConfigurationStatus.configured.value
    ):
        blockers.append("EXTENSION_CONFIGURATION_NOT_READY")
    if posture.health_status != ExactExtensionHealthStatus.healthy.value:
        blockers.append("EXTENSION_HEALTH_NOT_READY")
    if posture.budget_status != ExactExtensionBudgetStatus.available.value:
        blockers.append("EXTENSION_BUDGET_NOT_AVAILABLE")
    if posture.safe_disable_status != ExactExtensionSafeDisableStatus.inactive.value:
        blockers.append("EXTENSION_SAFE_DISABLE_NOT_INACTIVE")
    if posture.kill_switch_status != ExactExtensionKillSwitchStatus.inactive.value:
        blockers.append("EXTENSION_KILL_SWITCH_NOT_INACTIVE")
    return blockers


def build_exact_extension_adapter_read_model(
    *,
    posture: ExactExtensionRuntimePosture | None = None,
) -> ExactExtensionAdapterReadModel:
    manifest = ExactExtensionAdapterManifest.model_validate(
        build_default_exact_extension_adapter_manifest().model_dump(mode="python")
    )
    catalog = build_default_inspectable_extension_catalog()
    entry = next(
        item
        for item in catalog.entries
        if item.catalog_entry_ref == manifest.catalog_entry_ref
    )
    validation = validate_extension_catalog_entry_for_development(entry)
    if validation.status != "validated_metadata_only":
        raise ValueError("EXACT_EXTENSION_CATALOG_VALIDATION_REQUIRED")
    observed = posture or ExactExtensionRuntimePosture()
    blockers = exact_extension_runtime_blocker_codes(observed)
    return ExactExtensionAdapterReadModel(
        manifest=manifest,
        runtime_posture=observed,
        ready_for_request_scoped_evaluation=not blockers,
        blocker_codes=blockers,
        reason_codes=[
            "EXACT_REPO_OWNED_ADAPTER_REGISTERED",
            "EXTENSION_PACKAGE_RUNTIME_IMPORT_NOT_USED",
            "REQUEST_SCOPED_AUTHORITY_REEVALUATION_REQUIRED",
        ],
        safe_summary=(
            "One exact repo-owned extension adapter is registered and ready only "
            "for fresh request-scoped policy, lease, target, budget, kill-switch, "
            "safe-disable, and idempotency evaluation."
            if not blockers
            else "Exact extension adapter observations fail closed; no invocation "
            "authority or general extension runtime is available."
        ),
    )


def load_exact_extension_adapter_manifest(path: Path) -> ExactExtensionAdapterManifest:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise ValueError("EXACT_EXTENSION_MANIFEST_NOT_FOUND") from exc
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("EXACT_EXTENSION_MANIFEST_SPECIAL_FILE_DENIED")
    if metadata.st_size > EXACT_EXTENSION_MANIFEST_MAX_BYTES:
        raise ValueError("EXACT_EXTENSION_MANIFEST_TOO_LARGE")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError("EXACT_EXTENSION_MANIFEST_OPEN_DENIED") from exc
    try:
        opened = os.fstat(descriptor)
        current = os.lstat(path)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
            or opened.st_size > EXACT_EXTENSION_MANIFEST_MAX_BYTES
        ):
            raise ValueError("EXACT_EXTENSION_MANIFEST_IDENTITY_DRIFT")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 16 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if remaining or len(payload) != opened.st_size:
            raise ValueError("EXACT_EXTENSION_MANIFEST_READ_INCOMPLETE")
    finally:
        os.close(descriptor)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("EXACT_EXTENSION_MANIFEST_JSON_INVALID") from exc
    if not isinstance(decoded, dict):
        raise ValueError("EXACT_EXTENSION_MANIFEST_OBJECT_REQUIRED")
    return ExactExtensionAdapterManifest.model_validate(decoded)


class ExactExtensionMetadataAuthorityAdapter:
    """One reviewed extension binding; never a generic package-code loader."""

    def __init__(
        self,
        *,
        safe_roots: Sequence[FilesystemSafeRoot],
        posture_provider: Callable[[], ExactExtensionRuntimePosture],
        manifest: ExactExtensionAdapterManifest | None = None,
    ) -> None:
        self.manifest = manifest or ExactExtensionAdapterManifest.model_validate(
            build_default_exact_extension_adapter_manifest().model_dump(mode="python")
        )
        self._posture_provider = posture_provider
        self._inner = ToolRuntimeAuthorityDispatchAdapter(
            AuthorityDispatchAdapterDescriptor(
                adapter_ref=self.manifest.adapter_ref,
                domain=AuthorityDomain.files,
                capability=AuthorityCapability.read,
                capability_ref=self.manifest.capability_ref,
                tool_ref=self.manifest.tool_ref,
                approval_required=False,
                idempotent_replay_supported=True,
                rollback_ref=self.manifest.rollback_ref,
                safe_disable_ref=self.manifest.safe_disable_ref,
                safe_summary=(
                    "Inspect one exact metadata target through a reviewed repo-owned "
                    "extension registration and the bounded core tool runtime."
                ),
            ),
            safe_roots=safe_roots,
        )

    @property
    def descriptor(self) -> AuthorityDispatchAdapterDescriptor:
        return self._inner.descriptor

    @property
    def binding_ref(self) -> str:
        payload = {
            "manifest": self.manifest.model_dump(mode="json"),
            "inner_binding_ref": self._inner.binding_ref,
            "admission_ref": EXACT_EXTENSION_ADMISSION_REF,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return f"adapter-binding-ref:exact-extension:sha256:{digest}"

    def validate_request(self, request: AuthorityDispatchRequest) -> list[str]:
        reasons = list(self._inner.validate_request(request))
        reasons.extend(self._exact_admission_reasons(request))
        return list(dict.fromkeys(reasons))

    def invoke(
        self, request: AuthorityDispatchRequest
    ) -> AuthorityDispatchAdapterResult:
        # Recheck injected dynamic posture after the durable start claim and before
        # the core tool call. A late safe-disable/kill switch fails without access.
        late_reasons = self._exact_admission_reasons(request)
        if late_reasons:
            digest = hashlib.sha256(request.dispatch_ref.encode()).hexdigest()
            return AuthorityDispatchAdapterResult(
                execution_ref=authority_dispatch_execution_ref(request),
                succeeded=False,
                actual_operation_count=1,
                actual_cost_microusd=0,
                actual_cost_ref=(f"actual-cost-ref:exact-extension:sha256:{digest}"),
                evidence_refs=[
                    f"evidence-ref:exact-extension-late-denial:sha256:{digest}"
                ],
                safe_output={
                    "status": "blocked",
                    "reason_codes": late_reasons,
                    "registration_ref": self.manifest.registration_ref,
                },
                safe_summary=(
                    "Exact extension invocation failed closed after a fresh dynamic "
                    "posture check and before metadata access."
                ),
            )
        result = self._inner.invoke(request)
        return AuthorityDispatchAdapterResult.model_validate(
            result.model_dump(mode="python")
            | {
                "evidence_refs": list(
                    dict.fromkeys(
                        [
                            *result.evidence_refs,
                            self.manifest.registration_ref,
                            self.manifest.validation_ref,
                            self.manifest.receipt_contract_ref,
                        ]
                    )
                ),
                "safe_output": {
                    **result.safe_output,
                    "extension_registration_ref": self.manifest.registration_ref,
                    "extension_package_ref": self.manifest.package_ref,
                    "extension_capability_ref": self.manifest.capability_ref,
                },
                "safe_summary": (
                    "Exact extension metadata inspection completed through the "
                    "bounded core tool; no extension package code was imported."
                ),
            }
        )

    def _exact_admission_reasons(
        self,
        request: AuthorityDispatchRequest,
    ) -> list[str]:
        reasons = self._runtime_posture_reason_refs()
        reasons.extend(self._catalog_binding_reason_refs())
        action = request.action_request
        required_resources = {
            self.manifest.registration_ref,
            self.manifest.package_ref,
            self.manifest.manifest_ref,
            self.manifest.version_ref,
            self.manifest.capability_ref,
        }
        if not required_resources.issubset(action.resource_refs):
            reasons.append("reason-ref:exact-extension:exact-resource-binding-required")
        if action.lane_ref != self.manifest.lane_ref:
            reasons.append("reason-ref:exact-extension:exact-lane-binding-required")
        if action.rollback_ref != self.manifest.rollback_ref:
            reasons.append("reason-ref:exact-extension:exact-rollback-binding-required")
        if action.safe_disable_ref != self.manifest.safe_disable_ref:
            reasons.append(
                "reason-ref:exact-extension:exact-safe-disable-binding-required"
            )
        metadata = request.tool_invocation_request.get("metadata", {})
        if not isinstance(metadata, dict):
            reasons.append("reason-ref:exact-extension:tool-metadata-invalid")
        else:
            expected_metadata = {
                "extension_registration_ref": self.manifest.registration_ref,
                "extension_package_ref": self.manifest.package_ref,
                "extension_manifest_ref": self.manifest.manifest_ref,
                "extension_version_ref": self.manifest.version_ref,
                "extension_capability_ref": self.manifest.capability_ref,
            }
            if any(
                metadata.get(key) != value for key, value in expected_metadata.items()
            ):
                reasons.append(
                    "reason-ref:exact-extension:tool-metadata-binding-required"
                )
        return list(dict.fromkeys(reasons))

    def _runtime_posture_reason_refs(self) -> list[str]:
        try:
            observed = self._posture_provider()
            posture = ExactExtensionRuntimePosture.model_validate(
                observed.model_dump(mode="python")
            )
        except Exception:
            return ["reason-ref:exact-extension:posture-provider-failed"]
        return [
            "reason-ref:exact-extension:" + code.lower().replace("_", "-")
            for code in exact_extension_runtime_blocker_codes(posture)
        ]

    def _catalog_binding_reason_refs(self) -> list[str]:
        try:
            entry = next(
                item
                for item in build_default_inspectable_extension_catalog().entries
                if item.catalog_entry_ref == self.manifest.catalog_entry_ref
            )
            validation = validate_extension_catalog_entry_for_development(entry)
        except Exception:
            return ["reason-ref:exact-extension:catalog-validation-failed"]
        if (
            validation.status != "validated_metadata_only"
            or validation.validation_ref != self.manifest.validation_ref
            or validation.package_ref != self.manifest.package_ref
            or validation.manifest_ref != self.manifest.manifest_ref
            or validation.version_ref != self.manifest.version_ref
        ):
            return ["reason-ref:exact-extension:catalog-binding-invalid"]
        return []


def build_exact_extension_metadata_dispatch_request(
    *,
    lease_ref: str,
    run_ref: str,
    request_ref: str,
    idempotency_ref: str,
    root_ref: str,
    relative_path: str,
    start_deadline: datetime | None = None,
) -> AuthorityDispatchRequest:
    for value, field_name in (
        (lease_ref, "lease_ref"),
        (run_ref, "run_ref"),
        (request_ref, "request_ref"),
        (idempotency_ref, "idempotency_ref"),
        (root_ref, "root_ref"),
    ):
        validate_task_ref(value, field_name)
    normalized_path, path_reasons = normalize_relative_metadata_path(relative_path)
    if path_reasons or normalized_path is None:
        raise ValueError("EXACT_EXTENSION_TARGET_PATH_INVALID")
    manifest = ExactExtensionAdapterManifest.model_validate(
        build_default_exact_extension_adapter_manifest().model_dump(mode="python")
    )
    path_ref = filesystem_opaque_path_ref(root_ref, normalized_path)
    dispatch_ref = f"authority-dispatch-ref:exact-extension:{request_ref}"
    tool_request = ToolInvocationRequest(
        invocation_id=dispatch_ref,
        tool_ref=FILESYSTEM_METADATA_TOOL_REF,
        tool_name=FILESYSTEM_METADATA_TOOL_NAME,
        invocation_kind=ToolInvocationKind.filesystem_metadata,
        replay_key=idempotency_ref,
        safe_summary=(
            "Inspect one exact metadata target through the reviewed extension adapter."
        ),
        input_refs=[request_ref],
        metadata_refs=[
            manifest.registration_ref,
            manifest.validation_ref,
        ],
        metadata={
            "root_ref": root_ref,
            "relative_path": normalized_path,
            "safe_path_ref_version": FILESYSTEM_OPAQUE_PATH_REF_VERSION,
            "extension_registration_ref": manifest.registration_ref,
            "extension_package_ref": manifest.package_ref,
            "extension_manifest_ref": manifest.manifest_ref,
            "extension_version_ref": manifest.version_ref,
            "extension_capability_ref": manifest.capability_ref,
        },
    )
    action = AuthorityActionRequest(
        action_ref=f"authority-action-ref:exact-extension:{request_ref}",
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
        capability_ref=manifest.capability_ref,
        lane_ref=manifest.lane_ref,
        adapter_ref=manifest.adapter_ref,
        resource_refs=[
            manifest.registration_ref,
            manifest.package_ref,
            manifest.manifest_ref,
            manifest.version_ref,
            manifest.capability_ref,
            root_ref,
            path_ref,
        ],
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.path_refs,
                refs=[path_ref],
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=1,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
        ],
        safe_summary=(
            "Run one exact read-only extension metadata inspection under an "
            "injected safe root."
        ),
        rollback_ref=manifest.rollback_ref,
        safe_disable_ref=manifest.safe_disable_ref,
    )
    estimate = CostEstimate(
        estimate_id=f"cost-estimate:exact-extension:{request_ref}",
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
    )
    budgets = [
        CostBudget(
            budget_id=f"cost-budget:exact-extension:{request_ref}",
            scope=BudgetScope.run,
            scope_id=run_ref,
            max_cost_usd=0.000001,
            max_total_tokens=1,
        )
    ]
    return AuthorityDispatchRequest(
        dispatch_ref=dispatch_ref,
        run_ref=run_ref,
        idempotency_ref=idempotency_ref,
        lease_ref=lease_ref,
        adapter_ref=manifest.adapter_ref,
        action_request=action,
        tool_invocation_request=tool_request.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=estimate,
        cost_budgets=budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(estimate),
        cost_governor_decision_ref=(
            build_authority_dispatch_cost_governor_decision_ref(estimate, budgets)
        ),
        cost_governor_allowed=True,
        start_deadline=start_deadline,
        safe_summary=(
            "Dispatch one exact extension metadata inspection with fresh authority "
            "and runtime posture evaluation."
        ),
    )
