from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


PRIVATE_BETA_READINESS_CONTRACT_REF = (
    "contract-ref:private-beta-readiness-gate:v1"
)

PrivateBetaReadinessSurface = Literal[
    "Today",
    "Morning Briefing",
    "Action Inbox",
    "Memory Review",
    "Evidence Timeline",
    "Chat/Plans Handoff",
    "Governed Code",
    "CRM-Lite Follow-Ups",
]

PrivateBetaReadinessGateState = Literal[
    "pass",
    "fail",
    "skipped",
    "blocked",
    "partial",
    "mock_only",
    "accepted_failure",
]

PRIVATE_BETA_READINESS_REQUIRED_SURFACES: list[PrivateBetaReadinessSurface] = [
    "Today",
    "Morning Briefing",
    "Action Inbox",
    "Memory Review",
    "Evidence Timeline",
    "Chat/Plans Handoff",
    "Governed Code",
    "CRM-Lite Follow-Ups",
]

PRIVATE_BETA_READINESS_ACCEPTANCE_STATES: list[PrivateBetaReadinessGateState] = [
    "pass",
    "fail",
    "skipped",
    "blocked",
    "partial",
    "mock_only",
    "accepted_failure",
]

PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS = [
    "criterion_ref",
    "surface",
    "gate_state",
    "safe_summary",
    "evidence_refs",
    "required_contract_refs",
    "acceptance_refs",
    "missing_evidence_refs",
    "blocked_state_refs",
    "next_safe_action",
]

PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-public-beta",
    "blocked-state:no-public-distribution",
    "blocked-state:no-production-readiness-claim",
    "blocked-state:no-production-authority",
    "blocked-state:no-broad-autonomy",
    "blocked-state:no-connector-write",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-account-sync",
    "blocked-state:no-crm-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-action-execution",
    "blocked-state:no-code-apply-execution",
]

_DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "broad_autonomy_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "code_apply_execution_enabled",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw source",
    "raw file",
    "raw_file",
    "raw log",
    "raw_log",
    "browser state",
    "shell history",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "token",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class PrivateBetaReadinessCriterion(BaseModel):
    contract_ref: str = PRIVATE_BETA_READINESS_CONTRACT_REF
    criterion_ref: str = Field(..., min_length=1)
    surface: PrivateBetaReadinessSurface
    gate_state: PrivateBetaReadinessGateState
    safe_summary: str = Field(..., min_length=1, max_length=420)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    required_contract_refs: list[str] = Field(default_factory=list, min_length=1)
    acceptance_refs: list[str] = Field(default_factory=list, min_length=1)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    local_private_only: bool = True
    safe_refs_only: bool = True
    review_required: bool = True
    evidence_required: bool = True
    redaction_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_criterion(self) -> "PrivateBetaReadinessCriterion":
        if self.contract_ref != PRIVATE_BETA_READINESS_CONTRACT_REF:
            raise ValueError("private beta readiness contract ref drifted")
        for field_name in ["contract_ref", "criterion_ref"]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "evidence_refs",
            "required_contract_refs",
            "acceptance_refs",
            "missing_evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "surface",
            "gate_state",
            "safe_summary",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        required_true = {
            "local_private_only": self.local_private_only,
            "safe_refs_only": self.safe_refs_only,
            "review_required": self.review_required,
            "evidence_required": self.evidence_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [name for name, value in required_true.items() if not value]
        if missing_true:
            raise ValueError(f"private beta readiness disabled {missing_true[0]}")
        missing_blocked = set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private beta readiness criterion missing blocked refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private beta readiness")
        return self


class PrivateBetaReadinessGate(BaseModel):
    contract_ref: str = PRIVATE_BETA_READINESS_CONTRACT_REF
    overall_gate_state: PrivateBetaReadinessGateState = "partial"
    status: str = "implemented_private_beta_readiness_gate_authority_blocked"
    evidence_packet_ref: str = "evidence-packet:private-beta-readiness:local-founder-loop"
    readiness_window_ref: str = "readiness-window:local-private-beta"
    required_surfaces: list[PrivateBetaReadinessSurface] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_SURFACES)
    )
    acceptance_states: list[PrivateBetaReadinessGateState] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_ACCEPTANCE_STATES)
    )
    acceptance_state_definitions: list[dict[str, str | bool]]
    required_ref_fields: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS)
    )
    criteria: list[PrivateBetaReadinessCriterion] = Field(
        default_factory=list, min_length=1
    )
    surface_bindings: list[dict[str, str]]
    authority_posture: dict[str, bool]
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS)
    )
    missing_evidence_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Run a local private beta rehearsal against safe refs, then record "
        "pass/fail/blocked evidence before any broader readiness claim."
    )
    local_private_only: bool = True
    safe_refs_only: bool = True
    review_required: bool = True
    evidence_required: bool = True
    redaction_required: bool = True
    private_beta_execution_authorized: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_gate(self) -> "PrivateBetaReadinessGate":
        _safe_ref(self.contract_ref, "contract_ref")
        _safe_ref(self.evidence_packet_ref, "evidence_packet_ref")
        _safe_ref(self.readiness_window_ref, "readiness_window_ref")
        _safe_text(self.status, "status")
        _safe_text(self.overall_gate_state, "overall_gate_state")
        _safe_text(self.next_safe_action, "next_safe_action")
        if self.contract_ref != PRIVATE_BETA_READINESS_CONTRACT_REF:
            raise ValueError("private beta readiness gate ref drifted")
        if self.required_surfaces != PRIVATE_BETA_READINESS_REQUIRED_SURFACES:
            raise ValueError("private beta readiness required surfaces drifted")
        if set(self.acceptance_states) != set(PRIVATE_BETA_READINESS_ACCEPTANCE_STATES):
            raise ValueError("private beta readiness acceptance states drifted")
        if self.required_ref_fields != PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS:
            raise ValueError("private beta readiness ref fields drifted")
        if {criterion.surface for criterion in self.criteria} != set(
            PRIVATE_BETA_READINESS_REQUIRED_SURFACES
        ):
            raise ValueError("private beta readiness criteria missing surfaces")
        for field_name in ["blocked_state_refs", "missing_evidence_refs"]:
            _safe_refs(getattr(self, field_name), field_name)
        for row in self.acceptance_state_definitions:
            for key, value in row.items():
                _safe_text(str(key), "acceptance_state_definition_key")
                _safe_text(str(value), "acceptance_state_definition_value")
        for binding in self.surface_bindings:
            for key, value in binding.items():
                _safe_text(str(key), "surface_binding_key")
                _safe_text(str(value), "surface_binding_value")
        missing_blocked = set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private beta readiness gate missing blocked refs")
        required_true = {
            "local_private_only": self.local_private_only,
            "safe_refs_only": self.safe_refs_only,
            "review_required": self.review_required,
            "evidence_required": self.evidence_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [name for name, value in required_true.items() if not value]
        if missing_true:
            raise ValueError(f"private beta readiness gate disabled {missing_true[0]}")
        if self.private_beta_execution_authorized:
            raise ValueError("private beta execution is not authorized by this gate")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private beta readiness")
            if self.authority_posture.get(flag) is not False:
                raise ValueError(f"authority posture enabled {flag}")
        for flag in [
            "local_private_only",
            "safe_refs_only",
            "review_required",
            "evidence_required",
            "redaction_required",
        ]:
            if self.authority_posture.get(flag) is not True:
                raise ValueError(f"authority posture missing {flag}")
        return self


def build_private_beta_readiness_gate() -> PrivateBetaReadinessGate:
    return PrivateBetaReadinessGate(
        acceptance_state_definitions=_acceptance_state_definitions(),
        criteria=_criteria(),
        surface_bindings=private_beta_readiness_surface_bindings(),
        authority_posture=private_beta_readiness_authority_posture(),
        missing_evidence_refs=[
            "missing-evidence-ref:private-beta:run-rehearsal-receipts",
            "missing-evidence-ref:private-beta:operator-review-notes",
            "missing-evidence-ref:private-beta:api-perimeter-hardening",
        ],
    )


def private_beta_readiness_authority_posture() -> dict[str, bool]:
    return {
        "local_private_only": True,
        "safe_refs_only": True,
        "review_required": True,
        "evidence_required": True,
        "redaction_required": True,
        "private_beta_execution_authorized": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_readiness_claim_enabled": False,
        "production_authority_enabled": False,
        "broad_autonomy_enabled": False,
        "connector_write_enabled": False,
        "provider_model_authority_allowed": False,
        "unrestricted_shell_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "remote_execution_enabled": False,
        "account_sync_enabled": False,
        "crm_write_enabled": False,
        "memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "approval_grant_capture_enabled": False,
        "action_execution_enabled": False,
        "code_apply_execution_enabled": False,
    }


def private_beta_readiness_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": _surface_state(surface),
            "feed_ref": f"private-beta-readiness:{_surface_slug(surface)}",
            "authority_boundary": (
                "Private beta readiness evidence is local safe-ref metadata only."
            ),
        }
        for surface in PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    ]


def _criteria() -> list[PrivateBetaReadinessCriterion]:
    rows = [
        (
            "Today",
            "partial",
            "Today can show the product spine, blockers, follow-ups, and readiness refs, but the gate still needs rehearsal receipts.",
            [
                "contract-ref:today-product-spine:v1",
                "contract-ref:evidence-history-grammar:v1",
            ],
        ),
        (
            "Morning Briefing",
            "mock_only",
            "Morning Briefing has a storage-backed skeleton and source-readiness blockers, not live source reads.",
            ["contract-ref:morning-briefing-source-readiness-missing"],
        ),
        (
            "Action Inbox",
            "partial",
            "Action Inbox can review envelopes and memory-derived proposals, while execution and approval capture remain blocked.",
            [
                "contract-ref:plans-action-envelope:v1",
                "contract-ref:memory-to-loop-binding:v1",
            ],
        ),
        (
            "Memory Review",
            "partial",
            "Memory Review shows source, provenance, quality, decision, and loop refs without writing memory or injecting context.",
            [
                "contract-ref:memory-review-decision:v1",
                "contract-ref:business-memory-quality-controls:v1",
                "contract-ref:cross-surface-memory-intake:v1",
            ],
        ),
        (
            "Evidence Timeline",
            "partial",
            "Evidence Timeline reads as history for proposed, approved, happened, changed, undoable, stale, and blocked states.",
            ["contract-ref:evidence-history-grammar:v1"],
        ),
        (
            "Chat/Plans Handoff",
            "partial",
            "Local Chat can produce runtime, auth, tool-denial, and handoff refs, but output is not authority.",
            [
                "contract-ref:chat-local-operator-surface:v1",
                "contract-ref:plans-action-envelope:v1",
            ],
        ),
        (
            "Governed Code",
            "partial",
            "Governed Code can propose repo-local safe diff refs with validation and rollback posture while apply stays blocked.",
            ["contract-ref:governed-code-workbench:v1"],
        ),
        (
            "CRM-Lite Follow-Ups",
            "blocked",
            "CRM-lite follow-ups can be represented as reviewed memory/action refs only; account sync and CRM writes remain blocked.",
            [
                "contract-ref:business-memory-quality-controls:v1",
                "contract-ref:memory-to-loop-binding:v1",
            ],
        ),
    ]
    criteria: list[PrivateBetaReadinessCriterion] = []
    for surface, state, summary, contract_refs in rows:
        surface_slug = _surface_slug(surface)
        criteria.append(
            PrivateBetaReadinessCriterion(
                criterion_ref=f"private-beta-readiness-criterion:{surface_slug}",
                surface=surface,  # type: ignore[arg-type]
                gate_state=state,  # type: ignore[arg-type]
                safe_summary=summary,
                evidence_refs=[f"evidence-ref:private-beta:{surface_slug}"],
                required_contract_refs=contract_refs,
                acceptance_refs=[
                    f"acceptance-ref:private-beta:{surface_slug}:{state}"
                ],
                missing_evidence_refs=[
                    f"missing-evidence-ref:private-beta:{surface_slug}:rehearsal"
                ],
                next_safe_action=(
                    "Collect local operator review evidence and keep blocked "
                    "authority refs visible before any readiness claim."
                ),
            )
        )
    return criteria


def _acceptance_state_definitions() -> list[dict[str, str | bool]]:
    return [
        {
            "state": "pass",
            "terminal": True,
            "definition": "Acceptance evidence is present and no blocker remains.",
        },
        {
            "state": "fail",
            "terminal": True,
            "definition": "Evidence contradicts the acceptance criterion.",
        },
        {
            "state": "skipped",
            "terminal": False,
            "definition": "Criterion was intentionally skipped with a safe reason.",
        },
        {
            "state": "blocked",
            "terminal": False,
            "definition": "Required evidence or authority boundary is missing.",
        },
        {
            "state": "partial",
            "terminal": False,
            "definition": "Some evidence exists, but beta-test proof is incomplete.",
        },
        {
            "state": "mock_only",
            "terminal": False,
            "definition": "Only mock or skeleton evidence exists.",
        },
        {
            "state": "accepted_failure",
            "terminal": True,
            "definition": "Known failure is accepted only with documented risk refs.",
        },
    ]


def _surface_state(surface: PrivateBetaReadinessSurface) -> str:
    state_by_surface = {
        "Today": "partial_spine_evidence_needs_rehearsal",
        "Morning Briefing": "mock_only_source_reads_blocked",
        "Action Inbox": "partial_reviewable_envelopes_execution_blocked",
        "Memory Review": "partial_review_only_memory_controls",
        "Evidence Timeline": "partial_history_grammar_present",
        "Chat/Plans Handoff": "partial_local_operator_handoff_refs",
        "Governed Code": "partial_repo_local_proposal_refs_apply_blocked",
        "CRM-Lite Follow-Ups": "blocked_no_crm_write_or_account_sync",
    }
    return state_by_surface[surface]


def _surface_slug(surface: str) -> str:
    return surface.lower().replace("/", "-").replace(" ", "-")


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe private beta text")
