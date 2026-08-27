"""Policy, approval, and exact AuthorityLease gate for FIN-001 mutations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    TrustMode,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityKind,
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
from ultimate_ai_agent.core.finance.repository import (
    FinanceMutationOperation,
    FinanceMutationPermit,
)
from ultimate_ai_agent.core.finance.import_commit import (
    FIN002_IMPORT_BUDGET_REF,
    FIN002_IMPORT_EXACT_TARGET_REF,
    FIN002_IMPORT_KILL_SWITCH_REF,
    FIN002_IMPORT_READINESS_REF,
    FIN002_IMPORT_ROLLBACK_CONTRACT_REF,
    FIN002_IMPORT_SAFE_DISABLE_REF,
    FIN002_IMPORT_START_DEADLINE_REF,
    FIN002_SYNTHETIC_IMPORT_COMMIT_ADAPTER_REF,
    FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF,
    FIN002_SYNTHETIC_IMPORT_COMMIT_LANE_REF,
    FIN002_SYNTHETIC_IMPORT_COMMIT_TOOL_REF,
)
from ultimate_ai_agent.core.finance.models import stable_finance_ref
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
    validate_task_ref,
)


FINANCE_POLICY_REVISION_REF = "policy-revision-ref:finance/FIN-001:v1"
FINANCE_SAFE_DISABLE_REF = "safe-disable-ref:finance/FIN-001:synthetic-mutations"
FINANCE_ROLLBACK_REF = "rollback-ref:finance/FIN-001:reversal-or-restore"
FINANCE_READINESS_REF = "readiness-ref:finance/FIN-001:protected-repository"
FINANCE_BUDGET_REF = "budget-ref:finance/FIN-001:one-synthetic-mutation"
FINANCE_START_DEADLINE_REF = "deadline-ref:finance/FIN-001:prepared-window"
FINANCE_KILL_SWITCH_REF = "kill-switch-ref:finance/FIN-001:local"
FINANCE_EXACT_TARGET_REF = "target-ref:finance/FIN-001:protected-local-repository"
FINANCE_APPROVAL_TTL_MINUTES = 15
FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF = (
    "tool-ref:finance/FIN-001/synthetic-book-mutation:v1"
)
FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF = (
    "authority-lane-ref:finance/FIN-001/synthetic-book-mutation"
)
FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF = (
    "capability-ref:finance/FIN-001/synthetic-book-mutation"
)
FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF = (
    "authority-adapter-ref:finance/FIN-001/synthetic-book-repository:v1"
)
FINANCE_EXACT_AUTHORITY_BINDINGS = (
    (
        "workspace",
        "write",
        "session",
        "ask_before_changes",
        FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
        FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
        FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
        FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
    ),
)


class FinanceAuthorityError(RuntimeError):
    """Safe, content-free mutation-gate failure."""


class FinanceMutationRequest(BaseModel):
    schema_version: Literal["uaa-finance-mutation-request.v1"] = (
        "uaa-finance-mutation-request.v1"
    )
    operation: FinanceMutationOperation
    repository_ref: str
    fixture_ref: str | None = None
    target_ref: str | None = None
    import_preview_ref: str | None = None
    import_profile_ref: str | None = None
    import_fixture_manifest_ref: str | None = None
    import_candidate_refs: tuple[str, ...] = Field(default=(), max_length=128)
    import_source_fingerprint_refs: tuple[str, ...] = Field(default=(), max_length=128)
    expected_revision: int = Field(..., ge=0)
    request_ref: str
    idempotency_ref: str
    policy_revision_ref: Literal["policy-revision-ref:finance/FIN-001:v1"] = (
        FINANCE_POLICY_REVISION_REF
    )
    approval_ref: str | None = None
    exact_scope_ref: str | None = None
    action_envelope_ref: str | None = None
    safe_disable_ref: Literal[
        "safe-disable-ref:finance/FIN-001:synthetic-mutations",
        "safe-disable-ref:finance/FIN-002/synthetic-import-commit",
    ] = FINANCE_SAFE_DISABLE_REF
    synthetic_fixture_only: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    real_financial_data_included: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_request(self) -> "FinanceMutationRequest":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref") and value is not None:
                validate_task_ref(str(value), f"finance_mutation_request_{name}")
            elif name.endswith("_refs"):
                for ref in value:
                    validate_task_ref(str(ref), f"finance_mutation_request_{name}")
        if self.operation == "create":
            if (
                self.fixture_ref is None
                or self.target_ref is not None
                or self.expected_revision != 0
                or self.import_preview_ref is not None
                or self.import_profile_ref is not None
                or self.import_fixture_manifest_ref is not None
                or self.import_candidate_refs
                or self.import_source_fingerprint_refs
                or self.safe_disable_ref != FINANCE_SAFE_DISABLE_REF
            ):
                raise ValueError("FINANCE_CREATE_REQUEST_SCOPE_INVALID")
        elif self.operation == "import_commit":
            if (
                self.fixture_ref is None
                or self.target_ref is not None
                or self.expected_revision < 1
                or self.import_preview_ref is None
                or self.import_profile_ref is None
                or self.import_fixture_manifest_ref is None
                or not self.import_candidate_refs
                or len(self.import_candidate_refs)
                != len(self.import_source_fingerprint_refs)
                or self.safe_disable_ref != FIN002_IMPORT_SAFE_DISABLE_REF
            ):
                raise ValueError("FIN002_IMPORT_COMMIT_REQUEST_SCOPE_INVALID")
        else:
            if self.fixture_ref is not None:
                raise ValueError("FINANCE_NONCREATE_FIXTURE_REF_DENIED")
            if (
                self.import_preview_ref is not None
                or self.import_profile_ref is not None
                or self.import_fixture_manifest_ref is not None
                or self.import_candidate_refs
                or self.import_source_fingerprint_refs
                or self.safe_disable_ref != FINANCE_SAFE_DISABLE_REF
            ):
                raise ValueError("FINANCE_NONIMPORT_BINDING_DENIED")
            if self.operation in {"backup", "restore"} and self.target_ref is None:
                raise ValueError("FINANCE_BACKUP_TARGET_REF_REQUIRED")
            if self.operation == "delete" and self.target_ref is not None:
                raise ValueError("FINANCE_DELETE_TARGET_REF_DENIED")
        validate_safe_task_payload(payload, "finance_mutation_request")
        return self

    def without_authority(self) -> dict[str, object]:
        return self.model_dump(
            mode="json",
            exclude={"approval_ref", "exact_scope_ref", "action_envelope_ref"},
        )


class FinanceMutationPreview(BaseModel):
    schema_version: Literal["uaa-finance-mutation-preview.v1"] = (
        "uaa-finance-mutation-preview.v1"
    )
    preview_ref: str
    payload_fingerprint_ref: str
    exact_scope_ref: str
    action_envelope_ref: str
    expected_approval_ref: str
    approval_request: ApprovalRequest
    resource_refs: tuple[str, ...] = Field(..., min_length=12, max_length=320)
    policy_revision_ref: Literal["policy-revision-ref:finance/FIN-001:v1"] = (
        FINANCE_POLICY_REVISION_REF
    )
    capability_ref: Literal[
        "capability-ref:finance/FIN-001/synthetic-book-mutation",
        "capability-ref:finance/FIN-002/synthetic-import-commit",
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF
    lane_ref: Literal[
        "authority-lane-ref:finance/FIN-001/synthetic-book-mutation",
        "authority-lane-ref:finance/FIN-002/synthetic-import-commit",
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF
    adapter_ref: Literal[
        "authority-adapter-ref:finance/FIN-001/synthetic-book-repository:v1",
        "authority-adapter-ref:finance/FIN-002/protected-import-commit:v1",
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF
    tool_ref: Literal[
        "tool-ref:finance/FIN-001/synthetic-book-mutation:v1",
        "tool-ref:finance/FIN-002/synthetic-import-commit:v1",
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF
    safe_disable_ref: Literal[
        "safe-disable-ref:finance/FIN-001:synthetic-mutations",
        "safe-disable-ref:finance/FIN-002/synthetic-import-commit",
    ] = FINANCE_SAFE_DISABLE_REF
    rollback_ref: Literal[
        "rollback-ref:finance/FIN-001:reversal-or-restore",
        "rollback-contract-ref:finance/FIN-002/reversal-or-restore:v1",
    ] = FINANCE_ROLLBACK_REF
    prepared_at: datetime
    expires_at: datetime
    mutation_performed: Literal[False] = False
    raw_financial_values_included: Literal[False] = False
    real_financial_data_included: Literal[False] = False
    product_runtime_authority_granted: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_preview(self) -> "FinanceMutationPreview":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref"):
                validate_task_ref(str(value), f"finance_preview_{name}")
            elif name.endswith("_refs"):
                for ref in value:
                    validate_task_ref(str(ref), f"finance_preview_{name}")
        if self.prepared_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("FINANCE_PREVIEW_TIMEZONE_REQUIRED")
        if self.expires_at <= self.prepared_at:
            raise ValueError("FINANCE_PREVIEW_EXPIRY_INVALID")
        if tuple(self.approval_request.resource_refs) != self.resource_refs:
            raise ValueError("FINANCE_PREVIEW_APPROVAL_RESOURCES_DRIFTED")
        expected_contract = (
            (
                FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF,
                FIN002_SYNTHETIC_IMPORT_COMMIT_LANE_REF,
                FIN002_SYNTHETIC_IMPORT_COMMIT_ADAPTER_REF,
                FIN002_SYNTHETIC_IMPORT_COMMIT_TOOL_REF,
                FIN002_IMPORT_SAFE_DISABLE_REF,
                FIN002_IMPORT_ROLLBACK_CONTRACT_REF,
            )
            if self.capability_ref == FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF
            else (
                FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
                FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
                FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
                FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
                FINANCE_SAFE_DISABLE_REF,
                FINANCE_ROLLBACK_REF,
            )
        )
        if (
            self.capability_ref,
            self.lane_ref,
            self.adapter_ref,
            self.tool_ref,
            self.safe_disable_ref,
            self.rollback_ref,
        ) != expected_contract:
            raise ValueError("FINANCE_PREVIEW_AUTHORITY_CONTRACT_MISMATCH")
        expected = stable_finance_ref(
            "finance-mutation-preview-ref",
            self.model_dump(mode="json", exclude={"preview_ref"}),
        )
        if self.preview_ref != expected:
            raise ValueError("FINANCE_MUTATION_PREVIEW_REF_INVALID")
        validate_safe_task_payload(payload, "finance_mutation_preview")
        return self


def build_finance_mutation_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id="finance.synthetic-book-mutation",
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="FIN-001 synthetic protected-book mutation",
        description=(
            "Apply one exact fixture-selected mutation to the protected synthetic book."
        ),
        owner="python-agent-core",
        tags=["finance", "synthetic", "local", "governed"],
        examples=["Create the exact allowlisted balanced synthetic book fixture."],
        anti_examples=[
            "Accept operator-provided amounts, counterparties, account data, or real records."
        ],
        input_schema={
            "type": "object",
            "required": [
                "operation",
                "repository_ref",
                "request_ref",
                "idempotency_ref",
            ],
            "properties": {
                "operation": {
                    "enum": [item.value for item in FinanceMutationOperation]
                },
                "repository_ref": {"type": "string"},
                "fixture_ref": {"type": ["string", "null"]},
                "target_ref": {"type": ["string", "null"]},
                "request_ref": {"type": "string"},
                "idempotency_ref": {"type": "string"},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["receipt_ref", "repository_ref"],
            "additionalProperties": False,
        },
        input_modes=["safe_refs_only", "fixture_ref_allowlist_only"],
        output_modes=["content_free_receipt"],
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
        authority_level=CapabilityAuthorityLevel.mutating,
        approval_required=True,
        deterministic=True,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.sensitive,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        auth_scopes=[],
        data_classes=["synthetic_finance_refs_only"],
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=[
                "policy_revision_ref",
                "request_fingerprint_ref",
                "idempotency_key",
            ],
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=60,
            max_retries=0,
            max_concurrency=1,
            deterministic=True,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=True,
            approval_required=True,
            max_risk_level=RiskLevel.medium,
            max_side_effect_level=SideEffectLevel.write,
        ),
        quality=QualitySignals(
            confidence_score=1.0,
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "capability_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            "fixture_ref_allowlist_only": True,
            "real_financial_data_allowed": False,
            "api_route_added": False,
            "control_center_action_added": False,
        },
    )


def build_finance_import_commit_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id="finance.synthetic-import-commit",
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="FIN-002 exact synthetic import commit",
        description=(
            "Commit one current allowlisted synthetic preview into the protected book."
        ),
        owner="python-agent-core",
        tags=["finance", "synthetic", "import", "local", "governed"],
        examples=["Commit the exact current clean synthetic CSV preview."],
        anti_examples=[
            "Accept a caller file, pasted content, real statement, or changed preview."
        ],
        input_schema={
            "type": "object",
            "required": [
                "operation",
                "repository_ref",
                "fixture_ref",
                "import_preview_ref",
                "import_profile_ref",
                "import_fixture_manifest_ref",
                "import_candidate_refs",
                "import_source_fingerprint_refs",
                "expected_revision",
                "safe_disable_ref",
                "request_ref",
                "idempotency_ref",
            ],
            "properties": {
                "operation": {"const": "import_commit"},
                "repository_ref": {"type": "string"},
                "fixture_ref": {"type": "string"},
                "import_preview_ref": {"type": "string"},
                "import_profile_ref": {"type": "string"},
                "import_fixture_manifest_ref": {"type": "string"},
                "import_candidate_refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 128,
                },
                "import_source_fingerprint_refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 128,
                },
                "expected_revision": {"type": "integer", "minimum": 1},
                "safe_disable_ref": {"const": FIN002_IMPORT_SAFE_DISABLE_REF},
                "request_ref": {"type": "string"},
                "idempotency_ref": {"type": "string"},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["receipt_ref", "commit_ref", "rollback_ref"],
            "additionalProperties": False,
        },
        input_modes=["safe_refs_only", "allowlisted_fixture_preview_only"],
        output_modes=["content_free_receipt", "redacted_commit_proof"],
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
        authority_level=CapabilityAuthorityLevel.mutating,
        approval_required=True,
        deterministic=True,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.sensitive,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        auth_scopes=[],
        data_classes=["synthetic_finance_refs_only"],
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        single_writer_required=True,
        context_policy=ContextPolicy(
            required_context_keys=[
                "policy_revision_ref",
                "request_fingerprint_ref",
                "idempotency_key",
            ],
            allow_memory_refs=False,
            allow_raw_content=False,
        ),
        runtime_policy=RuntimePolicy(
            timeout_seconds=60,
            max_retries=0,
            max_concurrency=1,
            deterministic=True,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=True,
            approval_required=True,
            max_risk_level=RiskLevel.medium,
            max_side_effect_level=SideEffectLevel.write,
        ),
        quality=QualitySignals(
            confidence_score=1.0,
            owner_reviewed=True,
            deprecated=False,
        ),
        metadata={
            "capability_ref": FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF,
            "fixture_ref_allowlist_only": True,
            "preview_revalidation_required": True,
            "fingerprint_census_revalidation_required": True,
            "real_financial_data_allowed": False,
            "api_route_added": False,
            "control_center_action_added": False,
        },
    )


class FinanceMutationGate:
    def __init__(self, *, policy_engine: PolicyEngine | None = None) -> None:
        self.capability = build_finance_mutation_capability_manifest()
        self.import_commit_capability = (
            build_finance_import_commit_capability_manifest()
        )
        self.policy = policy_engine or PolicyEngine(default_max_risk=RiskLevel.medium)

    def _authority_contract(self, request: FinanceMutationRequest) -> dict[str, object]:
        if request.operation == FinanceMutationOperation.import_commit.value:
            return {
                "program": "FIN-002",
                "capability": self.import_commit_capability,
                "capability_ref": FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF,
                "lane_ref": FIN002_SYNTHETIC_IMPORT_COMMIT_LANE_REF,
                "adapter_ref": FIN002_SYNTHETIC_IMPORT_COMMIT_ADAPTER_REF,
                "tool_ref": FIN002_SYNTHETIC_IMPORT_COMMIT_TOOL_REF,
                "safe_disable_ref": FIN002_IMPORT_SAFE_DISABLE_REF,
                "rollback_ref": FIN002_IMPORT_ROLLBACK_CONTRACT_REF,
                "readiness_ref": FIN002_IMPORT_READINESS_REF,
                "budget_ref": FIN002_IMPORT_BUDGET_REF,
                "start_deadline_ref": FIN002_IMPORT_START_DEADLINE_REF,
                "kill_switch_ref": FIN002_IMPORT_KILL_SWITCH_REF,
                "target_ref": FIN002_IMPORT_EXACT_TARGET_REF,
            }
        return {
            "program": "FIN-001",
            "capability": self.capability,
            "capability_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            "lane_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
            "adapter_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
            "tool_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
            "safe_disable_ref": FINANCE_SAFE_DISABLE_REF,
            "rollback_ref": FINANCE_ROLLBACK_REF,
            "readiness_ref": FINANCE_READINESS_REF,
            "budget_ref": FINANCE_BUDGET_REF,
            "start_deadline_ref": FINANCE_START_DEADLINE_REF,
            "kill_switch_ref": FINANCE_KILL_SWITCH_REF,
            "target_ref": FINANCE_EXACT_TARGET_REF,
        }

    def prepare(
        self,
        request: FinanceMutationRequest,
        *,
        now: datetime | None = None,
    ) -> FinanceMutationPreview:
        current = now or datetime.now(UTC)
        contract = self._authority_contract(request)
        if current.tzinfo is None:
            raise ValueError("FINANCE_TRUSTED_TIME_REQUIRED")
        payload_fingerprint_ref = stable_finance_ref(
            "finance-mutation-payload-ref",
            request.without_authority(),
        )
        exact_scope_ref = stable_finance_ref(
            "finance-mutation-scope-ref",
            {
                "operation": request.operation,
                "repository_ref": request.repository_ref,
                "fixture_ref": request.fixture_ref,
                "target_ref": request.target_ref,
                "expected_revision": request.expected_revision,
                "request_ref": request.request_ref,
                "idempotency_ref": request.idempotency_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "policy_revision_ref": request.policy_revision_ref,
                "capability_ref": contract["capability_ref"],
            },
        )
        expected_approval_ref = stable_finance_ref(
            f"approval-ref:finance/{contract['program']}",
            {
                "exact_scope_ref": exact_scope_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
            },
        )
        action_envelope_ref = stable_finance_ref(
            f"action-envelope-ref:finance/{contract['program']}",
            {
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
            },
        )
        resource_refs = self._resource_refs(
            request=request,
            payload_fingerprint_ref=payload_fingerprint_ref,
            exact_scope_ref=exact_scope_ref,
            action_envelope_ref=action_envelope_ref,
        )
        expires_at = current + timedelta(minutes=FINANCE_APPROVAL_TTL_MINUTES)
        approval_request = ApprovalRequest(
            approval_request_id=stable_finance_ref(
                f"approval-request-ref:finance/{contract['program']}",
                {
                    "request_ref": request.request_ref,
                    "exact_scope_ref": exact_scope_ref,
                },
            ),
            run_id=request.request_ref,
            subject_type=ApprovalSubjectType.kernel_task,
            subject_id=exact_scope_ref,
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="actor-ref:finance:local-operator",
                authority_source=AuthoritySource.manual_operator_action,
                created_at=current,
            ),
            requested_action=f"finance_synthetic_{request.operation}",
            purpose=(
                "Approve one exact fixture-selected protected synthetic Finance mutation."
            ),
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.regulated,
                source="source-ref:finance:synthetic-fixture-manifest",
                reason="Synthetic accounting records use the protected Finance boundary.",
                allowed_sinks=["sink-ref:finance:protected-local-repository"],
                forbidden_sinks=[
                    "sink-ref:finance:provider",
                    "sink-ref:finance:connector",
                    "sink-ref:finance:logs",
                ],
                requires_redaction=True,
                requires_consent=False,
                retention_policy="retention-ref:finance:synthetic-local-only",
            ),
            resource_refs=list(resource_refs),
            tool_id=str(contract["tool_ref"]),
            event_ref=action_envelope_ref,
            trace_id=request.request_ref,
            created_at=current,
            expires_at=expires_at,
            metadata={
                "policy_revision_ref": FINANCE_POLICY_REVISION_REF,
                "synthetic_fixture_only": True,
                "real_financial_data_allowed": False,
                "capability_ref": contract["capability_ref"],
            },
        )
        payload = {
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "exact_scope_ref": exact_scope_ref,
            "action_envelope_ref": action_envelope_ref,
            "expected_approval_ref": expected_approval_ref,
            "approval_request": approval_request,
            "resource_refs": resource_refs,
            "capability_ref": contract["capability_ref"],
            "lane_ref": contract["lane_ref"],
            "adapter_ref": contract["adapter_ref"],
            "tool_ref": contract["tool_ref"],
            "safe_disable_ref": contract["safe_disable_ref"],
            "rollback_ref": contract["rollback_ref"],
            "prepared_at": current,
            "expires_at": expires_at,
        }
        provisional = FinanceMutationPreview.model_construct(
            preview_ref="finance-mutation-preview-ref:pending",
            **payload,
        )
        preview_ref = stable_finance_ref(
            "finance-mutation-preview-ref",
            provisional.model_dump(mode="json", exclude={"preview_ref"}),
        )
        return FinanceMutationPreview(preview_ref=preview_ref, **payload)

    def authorize(
        self,
        request: FinanceMutationRequest,
        *,
        preview: FinanceMutationPreview,
        approval_authority: LocalApprovalAuthority,
        active_authority_leases: Sequence[AuthorityLease],
        now: datetime | None = None,
        safe_disable_engaged: bool = False,
        kill_switch_engaged: bool = False,
    ) -> FinanceMutationPermit:
        current = now or datetime.now(UTC)
        contract = self._authority_contract(request)
        expected = self.prepare(
            request,
            now=preview.prepared_at,
        )
        if preview != expected:
            raise FinanceAuthorityError("FINANCE_PREVIEW_BINDING_MISMATCH")
        if current.tzinfo is None or current > preview.expires_at:
            raise FinanceAuthorityError("FINANCE_PREVIEW_EXPIRED")
        if safe_disable_engaged:
            raise FinanceAuthorityError("FINANCE_SAFE_DISABLE_ENGAGED")
        if request.approval_ref != preview.expected_approval_ref:
            raise FinanceAuthorityError("FINANCE_APPROVAL_REF_MISMATCH")
        if request.exact_scope_ref != preview.exact_scope_ref:
            raise FinanceAuthorityError("FINANCE_EXACT_SCOPE_MISMATCH")
        if request.action_envelope_ref != preview.action_envelope_ref:
            raise FinanceAuthorityError("FINANCE_ACTION_ENVELOPE_MISMATCH")

        policy_decision = self._policy_decision(request, preview)
        policy_allows = (
            policy_decision.status == PolicyDecisionStatus.allowed
            and policy_decision.allowed
        )
        policy_requires_exact_approval = (
            policy_decision.status == PolicyDecisionStatus.approval_required
            and not policy_decision.allowed
            and policy_decision.requires_approval
        )
        if not policy_allows and not policy_requires_exact_approval:
            raise FinanceAuthorityError("FINANCE_POLICY_DENIED")
        policy_decision_ref = stable_finance_ref(
            f"policy-decision-ref:finance/{contract['program']}",
            {
                "decision": policy_decision.model_dump(mode="json"),
                "policy_revision_ref": FINANCE_POLICY_REVISION_REF,
                "payload_fingerprint_ref": preview.payload_fingerprint_ref,
            },
        )

        approval_authority.create_request(preview.approval_request)
        approval_decision = approval_authority.validate_at_trusted_time(
            preview.approval_request.to_validation_request(
                preview.expected_approval_ref
            ),
            current_time=current,
        )
        if not approval_decision.allowed:
            raise FinanceAuthorityError("FINANCE_LOCAL_APPROVAL_DENIED")
        approval_decision_ref = stable_finance_ref(
            f"approval-decision-ref:finance/{contract['program']}",
            {
                "approval_ref": preview.expected_approval_ref,
                "exact_scope_ref": preview.exact_scope_ref,
                "payload_fingerprint_ref": preview.payload_fingerprint_ref,
                "status": approval_decision.status,
                "allowed": approval_decision.allowed,
            },
        )

        if kill_switch_engaged or authority_lease_kill_switch_engaged():
            raise FinanceAuthorityError("FINANCE_EXACT_AUTHORITY_LEASE_DENIED")
        exact_lease = self._exact_active_lease(
            preview,
            active_authority_leases,
            now=current,
        )
        if exact_lease is None:
            raise FinanceAuthorityError("FINANCE_EXACT_AUTHORITY_LEASE_DENIED")
        authority_decision_ref = stable_finance_ref(
            f"authority-decision-ref:finance/{contract['program']}",
            {
                "lease_ref": exact_lease.lease_ref,
                "exact_scope_ref": preview.exact_scope_ref,
                "payload_fingerprint_ref": preview.payload_fingerprint_ref,
            },
        )

        payload = {
            "operation": request.operation,
            "repository_ref": request.repository_ref,
            "fixture_ref": request.fixture_ref,
            "target_ref": request.target_ref,
            "import_preview_ref": request.import_preview_ref,
            "import_profile_ref": request.import_profile_ref,
            "import_fixture_manifest_ref": request.import_fixture_manifest_ref,
            "import_candidate_refs": request.import_candidate_refs,
            "import_source_fingerprint_refs": request.import_source_fingerprint_refs,
            "expected_revision": request.expected_revision,
            "request_ref": request.request_ref,
            "idempotency_ref": request.idempotency_ref,
            "payload_fingerprint_ref": preview.payload_fingerprint_ref,
            "policy_decision_ref": policy_decision_ref,
            "approval_ref": preview.expected_approval_ref,
            "approval_decision_ref": approval_decision_ref,
            "authority_lease_ref": exact_lease.lease_ref,
            "authority_decision_ref": authority_decision_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "safe_disable_ref": contract["safe_disable_ref"],
            "rollback_ref": contract["rollback_ref"],
            "capability_ref": contract["capability_ref"],
        }
        provisional = FinanceMutationPermit.model_construct(
            permit_ref="finance-mutation-permit-ref:pending",
            **payload,
        )
        permit_ref = stable_finance_ref(
            "finance-mutation-permit-ref",
            provisional.model_dump(mode="json", exclude={"permit_ref"}),
        )
        return FinanceMutationPermit(permit_ref=permit_ref, **payload)

    def _policy_decision(
        self,
        request: FinanceMutationRequest,
        preview: FinanceMutationPreview,
    ):
        contract = self._authority_contract(request)
        capability = contract["capability"]
        task = TaskEnvelope(
            task_id=request.request_ref,
            user_request="Apply one exact synthetic Finance fixture mutation.",
            objective="Return one content-free protected repository receipt.",
            scope=[str(contract["capability_ref"])],
            out_of_scope=[
                "real financial data",
                "arbitrary financial values",
                "connector access",
                "payment or transfer",
                "filing or advice",
                "API or Control Center mutation",
            ],
            selected_capability_ids=[capability.id],
            allowed_tool_ids=[str(contract["tool_ref"])],
            acceptance_criteria=[
                "Persist only the exact current allowlisted synthetic fixture under exact authority."
            ],
            budget={"operation_count": 1, "external_cost_microusd": 0},
            context={
                "policy_revision_ref": request.policy_revision_ref,
                "request_fingerprint_ref": preview.payload_fingerprint_ref,
                "idempotency_key": request.idempotency_ref,
            },
        )
        return self.policy.can_execute(
            capability,
            task,
            {
                "allowed_capability_ids": [capability.id],
                "max_risk_level": RiskLevel.medium.value,
                "capability_health": {capability.id: "healthy"},
                "coordination_mode": CoordinationMode.direct_tool.value,
                "policy_revision_ref": request.policy_revision_ref,
                "request_fingerprint_ref": preview.payload_fingerprint_ref,
                "idempotency_key": request.idempotency_ref,
            },
        )

    def _resource_refs(
        self,
        *,
        request: FinanceMutationRequest,
        payload_fingerprint_ref: str,
        exact_scope_ref: str,
        action_envelope_ref: str,
    ) -> tuple[str, ...]:
        contract = self._authority_contract(request)
        refs = {
            str(contract["lane_ref"]),
            str(contract["capability_ref"]),
            str(contract["adapter_ref"]),
            str(contract["tool_ref"]),
            request.repository_ref,
            request.request_ref,
            request.idempotency_ref,
            request.policy_revision_ref,
            payload_fingerprint_ref,
            exact_scope_ref,
            action_envelope_ref,
            str(contract["safe_disable_ref"]),
            str(contract["rollback_ref"]),
            str(contract["readiness_ref"]),
            str(contract["budget_ref"]),
            str(contract["start_deadline_ref"]),
            str(contract["kill_switch_ref"]),
            str(contract["target_ref"]),
            f"finance-operation-ref:{contract['program']}:{request.operation}",
            f"finance-revision-ref:{request.expected_revision}",
        }
        if request.fixture_ref is not None:
            refs.add(request.fixture_ref)
        if request.target_ref is not None:
            refs.add(request.target_ref)
        for ref in (
            request.import_preview_ref,
            request.import_profile_ref,
            request.import_fixture_manifest_ref,
        ):
            if ref is not None:
                refs.add(ref)
        refs.update(request.import_candidate_refs)
        refs.update(request.import_source_fingerprint_refs)
        return tuple(sorted(refs))

    @staticmethod
    def _exact_active_lease(
        preview: FinanceMutationPreview,
        leases: Sequence[AuthorityLease],
        *,
        now: datetime,
    ) -> AuthorityLease | None:
        if preview.capability_ref == FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF:
            start_deadline_ref = FIN002_IMPORT_START_DEADLINE_REF
            readiness_ref = FIN002_IMPORT_READINESS_REF
            budget_ref = FIN002_IMPORT_BUDGET_REF
            kill_switch_ref = FIN002_IMPORT_KILL_SWITCH_REF
        else:
            start_deadline_ref = FINANCE_START_DEADLINE_REF
            readiness_ref = FINANCE_READINESS_REF
            budget_ref = FINANCE_BUDGET_REF
            kill_switch_ref = FINANCE_KILL_SWITCH_REF
        expected_constraints = {
            "exact_lane_ref": preview.lane_ref,
            "exact_capability_ref": preview.capability_ref,
            "exact_adapter_ref": preview.adapter_ref,
            "exact_tool_ref": preview.tool_ref,
            "exact_request_fingerprint_ref": preview.payload_fingerprint_ref,
            "exact_start_deadline_ref": start_deadline_ref,
            "exact_readiness_ref": readiness_ref,
            "exact_budget_ref": budget_ref,
            "exact_safe_disable_ref": preview.safe_disable_ref,
            "exact_rollback_ref": preview.rollback_ref,
            "exact_kill_switch_ref": kill_switch_ref,
        }
        store_constraint_keys = {
            "decision_reason_ref",
            "idempotency_ref",
            "approval_required",
            "approval_validated",
            "approval_ref",
            "approval_scope_ref",
            "approval_request_ref",
            "approval_status",
            "unsupported_adapters_execute",
        }
        for lease in leases:
            constraints = {
                AuthorityConstraintKind(item.kind): item
                for item in lease.authority_constraints
            }
            resources = constraints.get(AuthorityConstraintKind.resource_refs)
            operations = constraints.get(AuthorityConstraintKind.operation_budget)
            cost = constraints.get(AuthorityConstraintKind.cost_budget_microusd)
            domains = lease.model_dump(mode="json")["domains"]
            lease_constraint_keys = set(lease.constraints)
            required_constraints_match = all(
                lease.constraints.get(key) == value
                for key, value in expected_constraints.items()
            )
            extra_constraint_keys = lease_constraint_keys - set(expected_constraints)
            store_constraints_valid = not extra_constraint_keys or (
                extra_constraint_keys == store_constraint_keys
                and lease.constraints.get("approval_required") is True
                and lease.constraints.get("approval_validated") is True
                and lease.constraints.get("unsupported_adapters_execute") is False
                and lease.constraints.get("approval_status") == "approved"
            )
            if (
                lease.is_active(now=now)
                and lease.scope == AuthorityLeaseScope.session.value
                and lease.mode == TrustMode.ask_before_changes.value
                and domains == {"workspace": ["write"]}
                and required_constraints_match
                and store_constraints_valid
                and lease.safe_disable_ref == preview.safe_disable_ref
                and lease.rollback_ref == preview.rollback_ref
                and lease.kill_switch_ref
                in {None, "kill-switch-ref:authority-lease-local"}
                and not lease.unsupported_adapter_refs
                and set(constraints)
                == {
                    AuthorityConstraintKind.resource_refs,
                    AuthorityConstraintKind.operation_budget,
                    AuthorityConstraintKind.cost_budget_microusd,
                }
                and resources is not None
                and set(resources.allowed_refs) == set(preview.resource_refs)
                and len(resources.allowed_refs) == len(preview.resource_refs)
                and operations is not None
                and operations.maximum == 1
                and cost is not None
                and cost.maximum == 1
            ):
                return lease
        return None


def build_finance_lease_issue_request(
    preview: FinanceMutationPreview,
) -> AuthorityLeaseIssueRequest:
    """Build the exact session lease; issuing it remains approval-authority work."""

    if preview.capability_ref == FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF:
        program = "FIN-002"
        start_deadline_ref = FIN002_IMPORT_START_DEADLINE_REF
        readiness_ref = FIN002_IMPORT_READINESS_REF
        budget_ref = FIN002_IMPORT_BUDGET_REF
        kill_switch_ref = FIN002_IMPORT_KILL_SWITCH_REF
    else:
        program = "FIN-001"
        start_deadline_ref = FINANCE_START_DEADLINE_REF
        readiness_ref = FINANCE_READINESS_REF
        budget_ref = FINANCE_BUDGET_REF
        kill_switch_ref = FINANCE_KILL_SWITCH_REF

    return AuthorityLeaseIssueRequest(
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=None,
        requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_finance_ref(
                    f"authority-constraint-ref:finance/{program}:resources",
                    {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=list(preview.resource_refs),
                safe_summary=(
                    "Restrict the Finance lease to one exact synthetic mutation."
                ),
            ),
            AuthorityConstraint(
                constraint_ref=stable_finance_ref(
                    f"authority-constraint-ref:finance/{program}:operations",
                    {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact synthetic Finance mutation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_finance_ref(
                    f"authority-constraint-ref:finance/{program}:cost",
                    {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the exact local mutation to zero external cost.",
            ),
        ],
        constraints={
            "exact_lane_ref": preview.lane_ref,
            "exact_capability_ref": preview.capability_ref,
            "exact_adapter_ref": preview.adapter_ref,
            "exact_tool_ref": preview.tool_ref,
            "exact_request_fingerprint_ref": preview.payload_fingerprint_ref,
            "exact_start_deadline_ref": start_deadline_ref,
            "exact_readiness_ref": readiness_ref,
            "exact_budget_ref": budget_ref,
            "exact_safe_disable_ref": preview.safe_disable_ref,
            "exact_rollback_ref": preview.rollback_ref,
            "exact_kill_switch_ref": kill_switch_ref,
        },
        decision_reason_ref=stable_finance_ref(
            f"decision-reason-ref:finance/{program}:lease",
            {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
        ),
        duration_minutes=FINANCE_APPROVAL_TTL_MINUTES,
        safe_summary=(
            "Issue one exact session-scoped lease for a synthetic Finance mutation."
        ),
    )


def build_exact_finance_lease(
    preview: FinanceMutationPreview,
    *,
    lease_ref: str,
    issued_at: datetime,
    expires_at: datetime,
) -> AuthorityLease:
    request = build_finance_lease_issue_request(
        preview,
    )
    return AuthorityLease(
        lease_ref=lease_ref,
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        status=AuthorityLeaseStatus.active,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        authority_constraints=request.authority_constraints,
        constraints=request.constraints,
        issued_at=issued_at,
        expires_at=expires_at,
        safe_disable_ref=preview.safe_disable_ref,
        rollback_ref=preview.rollback_ref,
        safe_summary=("Exact session lease for one fixture-selected Finance mutation."),
    )
