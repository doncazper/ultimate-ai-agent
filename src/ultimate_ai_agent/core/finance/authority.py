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
        "safe-disable-ref:finance/FIN-001:synthetic-mutations"
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
        if self.operation == "create":
            if (
                self.fixture_ref is None
                or self.target_ref is not None
                or self.expected_revision != 0
            ):
                raise ValueError("FINANCE_CREATE_REQUEST_SCOPE_INVALID")
        else:
            if self.fixture_ref is not None:
                raise ValueError("FINANCE_NONCREATE_FIXTURE_REF_DENIED")
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
    resource_refs: tuple[str, ...] = Field(..., min_length=12, max_length=64)
    policy_revision_ref: Literal["policy-revision-ref:finance/FIN-001:v1"] = (
        FINANCE_POLICY_REVISION_REF
    )
    capability_ref: Literal[
        "capability-ref:finance/FIN-001/synthetic-book-mutation"
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF
    lane_ref: Literal["authority-lane-ref:finance/FIN-001/synthetic-book-mutation"] = (
        FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF
    )
    adapter_ref: Literal[
        "authority-adapter-ref:finance/FIN-001/synthetic-book-repository:v1"
    ] = FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF
    tool_ref: Literal["tool-ref:finance/FIN-001/synthetic-book-mutation:v1"] = (
        FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF
    )
    safe_disable_ref: Literal[
        "safe-disable-ref:finance/FIN-001:synthetic-mutations"
    ] = FINANCE_SAFE_DISABLE_REF
    rollback_ref: Literal["rollback-ref:finance/FIN-001:reversal-or-restore"] = (
        FINANCE_ROLLBACK_REF
    )
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


class FinanceMutationGate:
    def __init__(self, *, policy_engine: PolicyEngine | None = None) -> None:
        self.capability = build_finance_mutation_capability_manifest()
        self.policy = policy_engine or PolicyEngine(default_max_risk=RiskLevel.medium)

    def prepare(
        self,
        request: FinanceMutationRequest,
        *,
        now: datetime | None = None,
    ) -> FinanceMutationPreview:
        current = now or datetime.now(UTC)
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
                "capability_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            },
        )
        expected_approval_ref = stable_finance_ref(
            "approval-ref:finance/FIN-001",
            {
                "exact_scope_ref": exact_scope_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
            },
        )
        action_envelope_ref = stable_finance_ref(
            "action-envelope-ref:finance/FIN-001",
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
                "approval-request-ref:finance/FIN-001",
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
                "Approve one exact fixture-selected FIN-001 synthetic local mutation."
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
            tool_id=FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
            event_ref=action_envelope_ref,
            trace_id=request.request_ref,
            created_at=current,
            expires_at=expires_at,
            metadata={
                "policy_revision_ref": FINANCE_POLICY_REVISION_REF,
                "synthetic_fixture_only": True,
                "real_financial_data_allowed": False,
            },
        )
        payload = {
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "exact_scope_ref": exact_scope_ref,
            "action_envelope_ref": action_envelope_ref,
            "expected_approval_ref": expected_approval_ref,
            "approval_request": approval_request,
            "resource_refs": resource_refs,
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
            "policy-decision-ref:finance/FIN-001",
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
            "approval-decision-ref:finance/FIN-001",
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
            "authority-decision-ref:finance/FIN-001",
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
            "safe_disable_ref": FINANCE_SAFE_DISABLE_REF,
            "rollback_ref": FINANCE_ROLLBACK_REF,
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
        task = TaskEnvelope(
            task_id=request.request_ref,
            user_request="Apply one exact synthetic Finance fixture mutation.",
            objective="Return one content-free protected repository receipt.",
            scope=[FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF],
            out_of_scope=[
                "real financial data",
                "arbitrary financial values",
                "connector access",
                "payment or transfer",
                "filing or advice",
                "API or Control Center mutation",
            ],
            selected_capability_ids=[self.capability.id],
            allowed_tool_ids=[FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF],
            acceptance_criteria=[
                "Persist only the selected deterministic fixture under exact authority."
            ],
            budget={"operation_count": 1, "external_cost_microusd": 0},
            context={
                "policy_revision_ref": request.policy_revision_ref,
                "request_fingerprint_ref": preview.payload_fingerprint_ref,
                "idempotency_key": request.idempotency_ref,
            },
        )
        return self.policy.can_execute(
            self.capability,
            task,
            {
                "allowed_capability_ids": [self.capability.id],
                "max_risk_level": RiskLevel.medium.value,
                "capability_health": {self.capability.id: "healthy"},
                "coordination_mode": CoordinationMode.direct_tool.value,
                "policy_revision_ref": request.policy_revision_ref,
                "request_fingerprint_ref": preview.payload_fingerprint_ref,
                "idempotency_key": request.idempotency_ref,
            },
        )

    @staticmethod
    def _resource_refs(
        *,
        request: FinanceMutationRequest,
        payload_fingerprint_ref: str,
        exact_scope_ref: str,
        action_envelope_ref: str,
    ) -> tuple[str, ...]:
        refs = {
            FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
            FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
            FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
            request.repository_ref,
            request.request_ref,
            request.idempotency_ref,
            request.policy_revision_ref,
            payload_fingerprint_ref,
            exact_scope_ref,
            action_envelope_ref,
            FINANCE_SAFE_DISABLE_REF,
            FINANCE_ROLLBACK_REF,
            FINANCE_READINESS_REF,
            FINANCE_BUDGET_REF,
            FINANCE_START_DEADLINE_REF,
            FINANCE_KILL_SWITCH_REF,
            FINANCE_EXACT_TARGET_REF,
            f"finance-operation-ref:FIN-001:{request.operation}",
            f"finance-revision-ref:{request.expected_revision}",
        }
        if request.fixture_ref is not None:
            refs.add(request.fixture_ref)
        if request.target_ref is not None:
            refs.add(request.target_ref)
        return tuple(sorted(refs))

    @staticmethod
    def _exact_active_lease(
        preview: FinanceMutationPreview,
        leases: Sequence[AuthorityLease],
        *,
        now: datetime,
    ) -> AuthorityLease | None:
        expected_constraints = {
            "exact_lane_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
            "exact_capability_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            "exact_adapter_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
            "exact_tool_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
            "exact_request_fingerprint_ref": preview.payload_fingerprint_ref,
            "exact_start_deadline_ref": FINANCE_START_DEADLINE_REF,
            "exact_readiness_ref": FINANCE_READINESS_REF,
            "exact_budget_ref": FINANCE_BUDGET_REF,
            "exact_safe_disable_ref": FINANCE_SAFE_DISABLE_REF,
            "exact_rollback_ref": FINANCE_ROLLBACK_REF,
            "exact_kill_switch_ref": FINANCE_KILL_SWITCH_REF,
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
                and lease.safe_disable_ref == FINANCE_SAFE_DISABLE_REF
                and lease.rollback_ref == FINANCE_ROLLBACK_REF
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

    return AuthorityLeaseIssueRequest(
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=None,
        requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_finance_ref(
                    "authority-constraint-ref:finance/FIN-001:resources",
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
                    "authority-constraint-ref:finance/FIN-001:operations",
                    {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact synthetic Finance mutation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_finance_ref(
                    "authority-constraint-ref:finance/FIN-001:cost",
                    {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the exact local mutation to zero external cost.",
            ),
        ],
        constraints={
            "exact_lane_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_LANE_REF,
            "exact_capability_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_CAPABILITY_REF,
            "exact_adapter_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_ADAPTER_REF,
            "exact_tool_ref": FINANCE_SYNTHETIC_BOOK_MUTATION_TOOL_REF,
            "exact_request_fingerprint_ref": preview.payload_fingerprint_ref,
            "exact_start_deadline_ref": FINANCE_START_DEADLINE_REF,
            "exact_readiness_ref": FINANCE_READINESS_REF,
            "exact_budget_ref": FINANCE_BUDGET_REF,
            "exact_safe_disable_ref": FINANCE_SAFE_DISABLE_REF,
            "exact_rollback_ref": FINANCE_ROLLBACK_REF,
            "exact_kill_switch_ref": FINANCE_KILL_SWITCH_REF,
        },
        decision_reason_ref=stable_finance_ref(
            "decision-reason-ref:finance/FIN-001:lease",
            {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
        ),
        duration_minutes=FINANCE_APPROVAL_TTL_MINUTES,
        safe_summary=(
            "Issue one exact session-scoped lease for a synthetic FIN-001 mutation."
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
        safe_disable_ref=FINANCE_SAFE_DISABLE_REF,
        rollback_ref=FINANCE_ROLLBACK_REF,
        safe_summary=("Exact session lease for one fixture-selected FIN-001 mutation."),
    )
