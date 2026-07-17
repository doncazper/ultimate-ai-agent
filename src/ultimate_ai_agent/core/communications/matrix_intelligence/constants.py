from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_INTELLIGENCE_SCHEMA_VERSION = "uaa-matrix-intelligence.v1"
MATRIX_INTELLIGENCE_TARGET_REF = (
    "target-ref:communications:matrix-intelligence-exact-room"
)
MATRIX_INTELLIGENCE_PROVIDER_REF = "provider-ref:communications:matrix-local-core"
MATRIX_INTELLIGENCE_RUNTIME_REF = "runtime-ref:matrix-intelligence:local-core-v1"
MATRIX_INTELLIGENCE_BUDGET_REF = "budget-ref:matrix-intelligence:bounded-local-v1"
MATRIX_INTELLIGENCE_SAFE_DISABLE_REF = "safe-disable-ref:matrix-intelligence:enabled"
MATRIX_INTELLIGENCE_KILL_SWITCH_REF = "kill-switch-ref:matrix-intelligence:clear"
MATRIX_INTELLIGENCE_RETENTION_REF = "retention-ref:matrix-intelligence:bounded-v1"
MATRIX_INTELLIGENCE_DISCLOSURE_REF = "disclosure-ref:matrix-intelligence:local-only"
MATRIX_INTELLIGENCE_REDACTION_REF = "redaction-ref:matrix-intelligence:safe-v1"
MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS = 900
MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS = 1800
MATRIX_INTELLIGENCE_MAX_EVENTS = 64
MATRIX_INTELLIGENCE_MAX_TOKENS = 4096
MATRIX_INTELLIGENCE_MAX_BYTES = 262_144


class MatrixIntelligenceFamily(str, Enum):
    context_materialization = "context_materialization"
    provider_invocation = "provider_invocation"
    proposal_persistence = "proposal_persistence"
    attachment_analysis = "attachment_analysis"


class MatrixIntelligenceOperation(str, Enum):
    room_ai_policy_read = "room_ai_policy_read"
    room_ai_policy_write = "room_ai_policy_write"
    context_materialize = "context_materialize"
    proposal_read = "proposal_read"
    proposal_persist = "proposal_persist"
    proposal_delete = "proposal_delete"


READ_OPERATIONS = frozenset(
    {
        MatrixIntelligenceOperation.room_ai_policy_read,
        MatrixIntelligenceOperation.proposal_read,
    }
)
MUTATION_OPERATIONS = frozenset(
    {
        MatrixIntelligenceOperation.room_ai_policy_write,
        MatrixIntelligenceOperation.proposal_persist,
        MatrixIntelligenceOperation.proposal_delete,
    }
)
DESTRUCTIVE_OPERATIONS = frozenset({MatrixIntelligenceOperation.proposal_delete})


@dataclass(frozen=True)
class MatrixIntelligenceLane:
    operation: MatrixIntelligenceOperation
    family: MatrixIntelligenceFamily
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    side_effect_class: str


_FAMILIES = {
    MatrixIntelligenceOperation.room_ai_policy_read: (
        MatrixIntelligenceFamily.context_materialization
    ),
    MatrixIntelligenceOperation.room_ai_policy_write: (
        MatrixIntelligenceFamily.context_materialization
    ),
    MatrixIntelligenceOperation.context_materialize: (
        MatrixIntelligenceFamily.context_materialization
    ),
    MatrixIntelligenceOperation.proposal_read: (
        MatrixIntelligenceFamily.proposal_persistence
    ),
    MatrixIntelligenceOperation.proposal_persist: (
        MatrixIntelligenceFamily.proposal_persistence
    ),
    MatrixIntelligenceOperation.proposal_delete: (
        MatrixIntelligenceFamily.proposal_persistence
    ),
}


def _lane(operation: MatrixIntelligenceOperation) -> MatrixIntelligenceLane:
    destructive = operation in DESTRUCTIVE_OPERATIONS
    mutation = operation in MUTATION_OPERATIONS
    capability = (
        AuthorityCapability.destructive
        if destructive
        else AuthorityCapability.mutate
        if mutation
        else AuthorityCapability.read
    )
    slug = operation.value.replace("_", "-")
    return MatrixIntelligenceLane(
        operation=operation,
        family=_FAMILIES[operation],
        lane_ref=f"authority-lane-ref:matrix-intelligence-{slug}",
        capability_ref=f"authority-capability-ref:matrix-intelligence-{slug}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-intelligence-{slug}-v1",
        tool_ref=f"tool-ref:matrix-intelligence-{slug}-v1",
        tool_name=f"matrix_intelligence_{operation.value}",
        authority_domain=AuthorityDomain.messages,
        authority_capability=capability,
        required_mode=(
            TrustMode.full_machine_access_session
            if destructive
            else TrustMode.ask_before_changes
        ),
        side_effect_class=(
            "destructive_local_sensitive"
            if destructive
            else "local_sensitive"
        ),
    )


MATRIX_INTELLIGENCE_LANES = {
    operation: _lane(operation) for operation in MatrixIntelligenceOperation
}


def matrix_intelligence_lane(
    operation: MatrixIntelligenceOperation | str,
) -> MatrixIntelligenceLane:
    return MATRIX_INTELLIGENCE_LANES[MatrixIntelligenceOperation(operation)]


def matrix_intelligence_rollback_ref(
    operation: MatrixIntelligenceOperation | str,
) -> str:
    operation = MatrixIntelligenceOperation(operation)
    return (
        "rollback-ref:matrix-intelligence:proposal-delete-restore-unavailable"
        if operation == MatrixIntelligenceOperation.proposal_delete
        else f"rollback-readiness-ref:matrix-intelligence:{operation.value.replace('_', '-')}"
    )


__all__ = [
    "DESTRUCTIVE_OPERATIONS",
    "MATRIX_INTELLIGENCE_BUDGET_REF",
    "MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS",
    "MATRIX_INTELLIGENCE_DISCLOSURE_REF",
    "MATRIX_INTELLIGENCE_KILL_SWITCH_REF",
    "MATRIX_INTELLIGENCE_LANES",
    "MATRIX_INTELLIGENCE_MAX_BYTES",
    "MATRIX_INTELLIGENCE_MAX_EVENTS",
    "MATRIX_INTELLIGENCE_MAX_TOKENS",
    "MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS",
    "MATRIX_INTELLIGENCE_PROVIDER_REF",
    "MATRIX_INTELLIGENCE_REDACTION_REF",
    "MATRIX_INTELLIGENCE_RETENTION_REF",
    "MATRIX_INTELLIGENCE_RUNTIME_REF",
    "MATRIX_INTELLIGENCE_SAFE_DISABLE_REF",
    "MATRIX_INTELLIGENCE_SCHEMA_VERSION",
    "MATRIX_INTELLIGENCE_TARGET_REF",
    "MUTATION_OPERATIONS",
    "READ_OPERATIONS",
    "MatrixIntelligenceFamily",
    "MatrixIntelligenceLane",
    "MatrixIntelligenceOperation",
    "matrix_intelligence_lane",
    "matrix_intelligence_rollback_ref",
]
