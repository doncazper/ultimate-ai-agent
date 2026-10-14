"""Exact policy, local approval and session lease for managed Finance setup."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
import json
import re
from typing import Literal

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
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    TrustMode,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_backend_approval_ref,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    FINANCE_MANAGED_SETUP_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.capabilities.enums import PolicyDecisionStatus, RiskLevel
from ultimate_ai_agent.core.capabilities.models import TaskEnvelope
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.finance.authority import (
    build_finance_mutation_capability_manifest,
)
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance_managed_profile import (
    FINANCE_EXPLICIT_ENV_NAMES,
    FINANCE_WORKSPACE_DISABLE_ENV,
    MANAGED_JSON_MAX_DEPTH,
    MANAGED_LAYOUT_REF,
    MANAGED_REPOSITORY_SLOT_REF,
    FinanceManagedProfileV1,
    FinanceManagedSetupIntentV1,
    ManagedPendingAttemptV1,
    managed_wire_payload,
    parse_managed_profile,
    parse_setup_intent,
    validate_managed_record,
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

MANAGED_SETUP_PREPARATION_MAX_BYTES = 128 * 1024
MANAGED_SETUP_POLICY_REF = "policy-revision-ref:finance/FIN-003:managed-setup:v1"
MANAGED_SETUP_APPROVER_REF = "actor-ref:finance:local-cli-operator"
_, _, _, _, LANE_REF, CAPABILITY_REF, ADAPTER_REF, TOOL_REF = (
    FINANCE_MANAGED_SETUP_EXACT_AUTHORITY_BINDINGS[0]
)
FIXED_CONSTRAINTS = {
    "exact_lane_ref": LANE_REF,
    "exact_capability_ref": CAPABILITY_REF,
    "exact_adapter_ref": ADAPTER_REF,
    "exact_tool_ref": TOOL_REF,
    "exact_policy_revision_ref": MANAGED_SETUP_POLICY_REF,
    "exact_layout_ref": MANAGED_LAYOUT_REF,
    "exact_target_ref": "target-ref:finance/FIN-003:managed-profile",
    "exact_start_deadline_ref": "deadline-ref:finance/FIN-003:managed-setup-window",
    "exact_readiness_ref": "readiness-ref:finance/FIN-003:verified-helper",
    "exact_budget_ref": "budget-ref:finance/FIN-003:one-managed-setup",
    "exact_safe_disable_ref": "safe-disable-ref:finance/FIN-003:managed-setup",
    "exact_rollback_ref": "rollback-ref:finance/FIN-003:discard-owned-incomplete",
    "exact_kill_switch_ref": "kill-switch-ref:finance/FIN-003:managed-setup",
}
_ERROR_SUFFIXES = {
    "REQUEST_INVALID",
    "PREPARATION_INVALID",
    "PREPARATION_TOO_LARGE",
    "PREPARATION_FILE_INVALID",
    "BUNDLE_FILE_INVALID",
    "PREPARATION_EXPIRED",
    "CONFIRMATION_REQUIRED",
    "EXPLICIT_CONFIGURATION_PRESENT",
    "SAFE_DISABLE_ENGAGED",
    "POLICY_DENIED",
    "APPROVAL_DENIED",
    "LEASE_DENIED",
    "SOURCE_UNAVAILABLE",
    "SOURCE_CHANGED",
    "STATE_INVALID",
    "STATE_CONFLICT",
    "CAPACITY_EXHAUSTED",
    "OWNERSHIP_UNVERIFIED",
    "MUTATION_INTERRUPTED",
    "REQUEST_FAILED",
}
ERROR_CODES = frozenset("FIN003_MANAGED_" + value for value in _ERROR_SUFFIXES)


class ManagedFinanceSetupError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code if code in ERROR_CODES else "FIN003_MANAGED_REQUEST_FAILED"
        super().__init__(self.code)


def fail(suffix: str) -> None:
    raise ManagedFinanceSetupError("FIN003_MANAGED_" + suffix)


def managed_setup_error_code(exc: Exception) -> str:
    return (
        exc.code
        if isinstance(exc, ManagedFinanceSetupError)
        else "FIN003_MANAGED_REQUEST_FAILED"
    )


def _json(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _ref(kind: str, payload: object) -> str:
    return stable_finance_ref("finance-managed-setup-" + kind + "-ref", payload)


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedFinanceSetupPreparation:
    intent: FinanceManagedSetupIntentV1
    desired_profile: FinanceManagedProfileV1 | None
    observed_state_ref: str
    observed_pending_attempt_ref: str | None
    preview_ref: str
    payload_fingerprint_ref: str
    exact_scope_ref: str
    action_envelope_ref: str
    expected_approval_ref: str
    requested_lease_ref: str
    approval_request: ApprovalRequest
    resource_refs: tuple[str, ...]
    prepared_at: datetime
    expires_at: datetime
    policy_revision_ref: str = MANAGED_SETUP_POLICY_REF
    schema_version: str = "uaa-finance-managed-setup-preview.v1"
    operator_confirmation_required: Literal[True] = True
    mutation_performed: Literal[False] = False

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        return preparation_payload(self)


def preparation_payload(
    preparation: ManagedFinanceSetupPreparation,
) -> dict[str, object]:
    value = {
        field.name: getattr(preparation, field.name) for field in fields(preparation)
    }
    value["intent"] = managed_wire_payload(preparation.intent)
    value["desired_profile"] = (
        managed_wire_payload(preparation.desired_profile)
        if preparation.desired_profile
        else None
    )
    value["approval_request"] = preparation.approval_request.model_dump(mode="json")
    value["resource_refs"] = list(preparation.resource_refs)
    value["prepared_at"] = preparation.prepared_at.isoformat()
    value["expires_at"] = preparation.expires_at.isoformat()
    return value


def _approval(intent, scope, action, approval_ref, resources, current, expires):
    return ApprovalRequest(
        approval_request_id=_ref("approval-request", {"scope": scope}),
        run_id=intent.request_ref,
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=scope,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor-ref:finance:local-operator",
            authority_source=AuthoritySource.manual_operator_action,
            created_at=current,
        ),
        requested_action="finance_managed_setup_" + intent.operation,
        purpose="Approve one exact synthetic Finance helper enrollment or owned incomplete discard.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.regulated,
            source="source-ref:finance:managed-setup",
            reason="Only content-free setup identities are recorded.",
            allowed_sinks=["sink-ref:finance:managed-local-profile"],
            forbidden_sinks=["sink-ref:finance:provider", "sink-ref:finance:logs"],
            requires_redaction=True,
            requires_consent=False,
            retention_policy="retention-ref:finance:managed-local-only",
        ),
        resource_refs=list(resources),
        tool_id=TOOL_REF,
        event_ref=action,
        trace_id=intent.request_ref,
        created_at=current,
        expires_at=expires,
        metadata={
            "policy_revision_ref": MANAGED_SETUP_POLICY_REF,
            "capability_ref": CAPABILITY_REF,
            "synthetic_only": True,
            "real_financial_data_allowed": False,
        },
    )


def build_preparation(
    intent: FinanceManagedSetupIntentV1,
    desired_profile: FinanceManagedProfileV1 | None,
    observed_state_ref: str,
    pending: ManagedPendingAttemptV1 | None,
    now: datetime,
) -> ManagedFinanceSetupPreparation:
    validate_managed_record(intent)
    if desired_profile is not None:
        validate_managed_record(desired_profile)
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        fail("PREPARATION_INVALID")
    now = now.astimezone(timezone.utc)
    expires = now + timedelta(minutes=15)
    pending_ref = pending.attempt_ref if pending else None
    window = {
        "intent": managed_wire_payload(intent),
        "observed_state_ref": observed_state_ref,
        "observed_pending_attempt_ref": pending_ref,
        "prepared_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    }
    lease = _ref("lease", window)
    scope = _ref(
        "scope", {**window, "lease": lease, "policy": MANAGED_SETUP_POLICY_REF}
    )
    approval_ref = _ref("approval", {"scope": scope})
    action = _ref("action", {"scope": scope, "approval": approval_ref})
    resources = set(FIXED_CONSTRAINTS.values()) | {
        MANAGED_REPOSITORY_SLOT_REF,
        intent.intent_ref,
        intent.payload_fingerprint_ref,
        _ref("request", {"value": intent.request_ref}),
        _ref("idempotency", {"value": intent.idempotency_ref}),
        intent.expected_state_ref,
        observed_state_ref,
        lease,
        scope,
        approval_ref,
        action,
        "finance-operation-ref:FIN-003:" + intent.operation,
    }
    for record in (intent, desired_profile, pending):
        if record is not None:
            # Finite nested records only; source/helper ownership is bound in their hash.
            for key, value in managed_wire_payload(record).items():
                if (
                    key.endswith("_ref")
                    and key not in {"request_ref", "idempotency_ref"}
                    and isinstance(value, str)
                ):
                    resources.add(value)
    if desired_profile:
        resources.update(
            (
                desired_profile.helper.helper_ref,
                desired_profile.helper.source.source_provenance_ref,
            )
        )
    if pending:
        resources.update(
            (
                pending.desired_profile.profile_ref,
                pending.desired_profile.helper.helper_ref,
                pending.desired_profile.helper.source.source_provenance_ref,
            )
        )
    refs = tuple(sorted(resources))
    if len(refs) > 64:
        fail("PREPARATION_INVALID")
    approval = _approval(intent, scope, action, approval_ref, refs, now, expires)
    values = dict(
        intent=intent,
        desired_profile=desired_profile,
        observed_state_ref=observed_state_ref,
        observed_pending_attempt_ref=pending_ref,
        payload_fingerprint_ref=intent.payload_fingerprint_ref,
        exact_scope_ref=scope,
        action_envelope_ref=action,
        expected_approval_ref=approval_ref,
        requested_lease_ref=lease,
        approval_request=approval,
        resource_refs=refs,
        prepared_at=now,
        expires_at=expires,
    )
    provisional = ManagedFinanceSetupPreparation(preview_ref="pending", **values)
    payload = preparation_payload(provisional)
    del payload["preview_ref"]
    return ManagedFinanceSetupPreparation(
        preview_ref=_ref("preview", payload), **values
    )


def _validate_shape(preparation: ManagedFinanceSetupPreparation) -> None:
    if (
        type(preparation.observed_state_ref) is not str
        or re.fullmatch(
            r"managed-finance-(?:absent-state|state)-ref:sha256:[0-9a-f]{64}",
            preparation.observed_state_ref,
        )
        is None
    ):
        fail("PREPARATION_INVALID")
    if preparation.observed_pending_attempt_ref is not None and (
        type(preparation.observed_pending_attempt_ref) is not str
        or re.fullmatch(
            r"managed-finance-attempt-ref:sha256:[0-9a-f]{64}",
            preparation.observed_pending_attempt_ref,
        )
        is None
    ):
        fail("PREPARATION_INVALID")
    for field_name, kind in (
        ("preview_ref", "preview"),
        ("exact_scope_ref", "scope"),
        ("action_envelope_ref", "action"),
        ("expected_approval_ref", "approval"),
        ("requested_lease_ref", "lease"),
    ):
        value = getattr(preparation, field_name)
        if (
            type(value) is not str
            or re.fullmatch(
                "finance-managed-setup-" + kind + r"-ref:sha256:[0-9a-f]{64}", value
            )
            is None
        ):
            fail("PREPARATION_INVALID")
    validate_managed_record(preparation.intent)
    if preparation.desired_profile:
        validate_managed_record(preparation.desired_profile)
    if (preparation.intent.operation == "enroll") != (
        preparation.desired_profile is not None
    ):
        fail("PREPARATION_INVALID")
    if (
        preparation.schema_version != "uaa-finance-managed-setup-preview.v1"
        or preparation.policy_revision_ref != MANAGED_SETUP_POLICY_REF
        or preparation.operator_confirmation_required is not True
        or preparation.mutation_performed is not False
        or preparation.payload_fingerprint_ref
        != preparation.intent.payload_fingerprint_ref
        or preparation.prepared_at.tzinfo is None
        or preparation.expires_at.tzinfo is None
        or preparation.prepared_at.utcoffset() != timedelta(0)
        or preparation.expires_at - preparation.prepared_at != timedelta(minutes=15)
        or len(preparation.resource_refs) > 64
        or tuple(sorted(set(preparation.resource_refs))) != preparation.resource_refs
        or any(
            not isinstance(ref, str) or not ref.isascii() or len(ref) > 200
            for ref in preparation.resource_refs
        )
    ):
        fail("PREPARATION_INVALID")
    expected_approval = _approval(
        preparation.intent,
        preparation.exact_scope_ref,
        preparation.action_envelope_ref,
        preparation.expected_approval_ref,
        preparation.resource_refs,
        preparation.prepared_at,
        preparation.expires_at,
    )
    if _json(preparation.approval_request.model_dump(mode="json")) != _json(
        expected_approval.model_dump(mode="json")
    ):
        fail("PREPARATION_INVALID")
    payload = preparation_payload(preparation)
    del payload["preview_ref"]
    if preparation.preview_ref != _ref("preview", payload):
        fail("PREPARATION_INVALID")


def serialize_managed_setup_preparation(
    preparation: ManagedFinanceSetupPreparation,
) -> bytes:
    try:
        _validate_shape(preparation)
        raw = _json(preparation_payload(preparation))
        if len(raw) > MANAGED_SETUP_PREPARATION_MAX_BYTES:
            fail("PREPARATION_TOO_LARGE")
        return raw
    except ManagedFinanceSetupError:
        raise
    except (ValueError, TypeError, AttributeError, RecursionError):
        fail("PREPARATION_INVALID")


def parse_managed_setup_preparation(raw: bytes) -> ManagedFinanceSetupPreparation:
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                fail("PREPARATION_INVALID")
            value[key] = item
        return value

    def depth(value, level=0):
        if level > MANAGED_JSON_MAX_DEPTH:
            fail("PREPARATION_INVALID")
        if isinstance(value, dict):
            for item in value.values():
                depth(item, level + 1)
        elif isinstance(value, list):
            for item in value:
                depth(item, level + 1)

    try:
        if type(raw) is not bytes:
            fail("PREPARATION_INVALID")
        if len(raw) > MANAGED_SETUP_PREPARATION_MAX_BYTES:
            fail("PREPARATION_TOO_LARGE")
        level, quoted, escaped = 0, False, False
        for byte in raw:
            if quoted:
                if escaped:
                    escaped = False
                elif byte == 92:
                    escaped = True
                elif byte == 34:
                    quoted = False
            elif byte == 34:
                quoted = True
            elif byte in (91, 123):
                level += 1
                if level > MANAGED_JSON_MAX_DEPTH:
                    fail("PREPARATION_INVALID")
            elif byte in (93, 125):
                level -= 1
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda _value: fail("PREPARATION_INVALID"),
        )
        depth(payload)
        if not isinstance(payload, dict) or set(payload) != {
            f.name for f in fields(ManagedFinanceSetupPreparation)
        }:
            fail("PREPARATION_INVALID")
        values = dict(payload)
        values["intent"] = parse_setup_intent(_json(payload["intent"]))
        values["desired_profile"] = (
            parse_managed_profile(_json(payload["desired_profile"]))
            if payload["desired_profile"] is not None
            else None
        )
        values["approval_request"] = ApprovalRequest.model_validate(
            payload["approval_request"]
        )
        values["resource_refs"] = tuple(payload["resource_refs"])
        values["prepared_at"] = datetime.fromisoformat(payload["prepared_at"])
        values["expires_at"] = datetime.fromisoformat(payload["expires_at"])
        preparation = ManagedFinanceSetupPreparation(**values)
        if serialize_managed_setup_preparation(preparation) != _json(payload):
            fail("PREPARATION_INVALID")
        return preparation
    except ManagedFinanceSetupError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        fail("PREPARATION_INVALID")


def require_environment(environ) -> None:
    if any(key in environ for key in FINANCE_EXPLICIT_ENV_NAMES):
        fail("EXPLICIT_CONFIGURATION_PRESENT")
    value = environ.get(FINANCE_WORKSPACE_DISABLE_ENV)
    if value is not None and value.strip().lower() not in {"0", "false", "no", "off"}:
        fail("SAFE_DISABLE_ENGAGED")
    if authority_lease_kill_switch_engaged():
        fail("SAFE_DISABLE_ENGAGED")


def setup_capability():
    # Reuse the mature deterministic local-write policy template, with a new exact identity.
    template = build_finance_mutation_capability_manifest()
    payload = template.model_dump(mode="python")
    payload.update(
        id="finance.managed-setup",
        name="Managed synthetic Finance setup",
        description="Enroll one verified helper profile or discard an owned incomplete attempt.",
        input_modes=["safe_refs_only"],
        data_classes=["finance_setup_refs_only"],
        examples=["Enroll the verified local helper for synthetic Finance."],
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {"operation": {"enum": ["enroll", "discard_incomplete"]}},
        },
        metadata={
            "capability_ref": CAPABILITY_REF,
            "synthetic_only": True,
            "real_financial_data_allowed": False,
            "api_route_added": False,
        },
    )
    return type(template).model_validate(payload)


def require_policy(preparation, policy: PolicyEngine) -> str:
    capability = setup_capability()
    context = {
        "policy_revision_ref": MANAGED_SETUP_POLICY_REF,
        "request_fingerprint_ref": preparation.payload_fingerprint_ref,
        "idempotency_key": preparation.intent.idempotency_ref,
    }
    task = TaskEnvelope(
        task_id=preparation.intent.request_ref,
        user_request="Perform one exact managed Finance setup operation.",
        objective="Record one content-free managed setup receipt.",
        scope=[CAPABILITY_REF],
        out_of_scope=[
            "Finance book or key creation",
            "real financial data",
            "helper execution",
        ],
        selected_capability_ids=[capability.id],
        allowed_tool_ids=[TOOL_REF],
        acceptance_criteria=[
            "Exact confirmed helper enrollment or owned incomplete discard."
        ],
        budget={"operation_count": 1, "external_cost_microusd": 0},
        context=context,
    )
    decision = policy.can_execute(
        capability,
        task,
        {
            **context,
            "allowed_capability_ids": [capability.id],
            "max_risk_level": RiskLevel.medium.value,
            "capability_health": {capability.id: "healthy"},
            "coordination_mode": "direct_tool",
        },
    )
    if not (
        (decision.status == PolicyDecisionStatus.allowed and decision.allowed)
        or (
            decision.status == PolicyDecisionStatus.approval_required
            and not decision.allowed
            and decision.requires_approval
        )
    ):
        fail("POLICY_DENIED")
    return _ref(
        "policy-decision",
        {
            "decision": decision.model_dump(mode="json"),
            "preview_ref": preparation.preview_ref,
        },
    )


def build_setup_lease_request(preparation) -> AuthorityLeaseIssueRequest:
    return AuthorityLeaseIssueRequest(
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=preparation.requested_lease_ref,
        requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=_ref("resources", {"preview": preparation.preview_ref}),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=list(preparation.resource_refs),
                safe_summary="Only the exact managed setup resources.",
            ),
            AuthorityConstraint(
                constraint_ref=_ref("operations", {"preview": preparation.preview_ref}),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="One exact managed setup operation.",
            ),
            AuthorityConstraint(
                constraint_ref=_ref("cost", {"preview": preparation.preview_ref}),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Zero external cost.",
            ),
        ],
        constraints={
            **FIXED_CONSTRAINTS,
            "exact_request_fingerprint_ref": preparation.payload_fingerprint_ref,
            "exact_operation_ref": "finance-operation-ref:FIN-003:"
            + preparation.intent.operation,
        },
        decision_reason_ref=_ref(
            "decision-reason", {"preview": preparation.preview_ref}
        ),
        duration_minutes=15,
        safe_summary="Issue one exact managed Finance setup lease.",
    )


def setup_lease_request_is_exact(request) -> bool:
    """Central admission remains narrower than generic workspace/write authority."""
    constraints = request.constraints
    kinds = {item.kind: item for item in request.authority_constraints}
    resources = kinds.get("resource_refs")
    operations = kinds.get("operation_budget")
    cost = kinds.get("cost_budget_microusd")
    return bool(
        request.duration_minutes == 15
        and request.mode == "ask_before_changes"
        and request.scope == "session"
        and request.mission_ref is None
        and request.operator_ref == "operator-ref:local-user"
        and request.requested_lease_ref
        and re.fullmatch(
            r"finance-managed-setup-lease-ref:sha256:[0-9a-f]{64}",
            request.requested_lease_ref,
        )
        and request.requested_domains == {"workspace": ["write"]}
        and set(constraints)
        == set(FIXED_CONSTRAINTS)
        | {"exact_request_fingerprint_ref", "exact_operation_ref"}
        and all(constraints.get(k) == v for k, v in FIXED_CONSTRAINTS.items())
        and isinstance(constraints.get("exact_request_fingerprint_ref"), str)
        and re.fullmatch(
            r"managed-finance-payload-ref:sha256:[0-9a-f]{64}",
            constraints["exact_request_fingerprint_ref"],
        )
        and constraints.get("exact_operation_ref")
        in {
            "finance-operation-ref:FIN-003:enroll",
            "finance-operation-ref:FIN-003:discard_incomplete",
        }
        and len(request.authority_constraints) == 3
        and set(kinds) == {"resource_refs", "operation_budget", "cost_budget_microusd"}
        and resources
        and resources.maximum is None
        and 1 <= len(resources.allowed_refs) <= 64
        and len(resources.allowed_refs) == len(set(resources.allowed_refs))
        and all(
            isinstance(ref, str) and ref.isascii() and len(ref) <= 200
            for ref in resources.allowed_refs
        )
        and (set(constraints.values()) | {request.requested_lease_ref}).issubset(
            resources.allowed_refs
        )
        and operations
        and operations.maximum == 1
        and not operations.allowed_refs
        and cost
        and cost.maximum == 1
        and not cost.allowed_refs
    )


def validate_current_authority(
    preparation,
    approvals: LocalApprovalAuthority,
    store,
    requirement,
    issued_lease,
    issue_idempotency_ref,
    now,
    policy,
    expected_grant_fingerprint=None,
):
    _validate_shape(preparation)
    if (
        now.tzinfo is None
        or not preparation.prepared_at <= now < preparation.expires_at
    ):
        fail("PREPARATION_EXPIRED")
    policy_ref = require_policy(preparation, policy)
    decision = approvals.validate_at_trusted_time(
        preparation.approval_request.to_validation_request(
            preparation.expected_approval_ref
        ),
        current_time=now,
    )
    grant = approvals.get_grant(preparation.expected_approval_ref)
    if not decision.allowed or grant is None:
        fail("APPROVAL_DENIED")
    fingerprint = _ref("approval-grant", grant.model_dump(mode="json"))
    if (
        expected_grant_fingerprint is not None
        and fingerprint != expected_grant_fingerprint
    ):
        fail("APPROVAL_DENIED")
    request = build_setup_lease_request(preparation)
    leases = [
        lease
        for lease in store.list_leases(active_only=False)
        if lease.lease_ref == preparation.requested_lease_ref
    ]
    if len(leases) != 1:
        fail("LEASE_DENIED")
    lease = leases[0]
    extras = {
        "decision_reason_ref": request.decision_reason_ref,
        "idempotency_ref": issue_idempotency_ref,
        "approval_required": True,
        "approval_validated": True,
        "approval_ref": build_authority_lease_backend_approval_ref(
            requirement, idempotency_ref=issue_idempotency_ref
        ),
        "approval_scope_ref": requirement.approval_scope_ref,
        "approval_request_ref": requirement.approval_request_ref,
        "approval_status": "approved",
        "unsupported_adapters_execute": False,
    }
    if (
        not lease.is_active(now=now)
        or lease.issued_at > now
        or lease.mode != "ask_before_changes"
        or lease.scope != "session"
        or lease.mission_ref is not None
        or lease.operator_ref != "operator-ref:local-user"
        or lease.domains != {"workspace": ["write"]}
        or lease.unsupported_adapter_refs
        or _json(lease.constraints) != _json({**request.constraints, **extras})
        or lease.authority_constraints != request.authority_constraints
        or lease.safe_disable_ref != FIXED_CONSTRAINTS["exact_safe_disable_ref"]
        or lease.rollback_ref != FIXED_CONSTRAINTS["exact_rollback_ref"]
        or lease.kill_switch_ref != "kill-switch-ref:authority-lease-local"
    ):
        fail("LEASE_DENIED")
    return {
        "policy_decision_ref": policy_ref,
        "approval_decision_ref": _ref(
            "approval-decision",
            {"preview": preparation.preview_ref, "grant": fingerprint},
        ),
        "approval_grant_fingerprint_ref": fingerprint,
        "authority_decision_ref": _ref(
            "authority-decision",
            {"preview": preparation.preview_ref, "lease": lease.lease_ref},
        ),
    }
