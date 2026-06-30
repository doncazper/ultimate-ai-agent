from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.crm.contracts import (
    CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    CRM_COMMUNICATIONS_SPINE_CONTRACT_REF,
    CrmImplementationState,
    CrmWorkspaceKind,
    _deny_true_flags,
    _validate_no_private_or_secret_text,
    _validate_optional_ref_list,
    _validate_ref,
    _validate_ref_list,
    _validate_safe_text,
    build_crm_communications_spine_contract,
)


CRM_M1_FIXTURE_CONTRACT_REF = "contract-ref:crm-m1-fixture-only-vertical-shell:v1"
CRM_M1_FIXTURE_DOC_REF = "docs-ref:crm-m1-fixture-only-vertical-shell"
CRM_M1_FIXTURE_VERIFIER_REF = "script-ref:verify-crm-m1-fixture-only"

CRM_M1_REQUIRED_STATE_LABELS = [
    CrmImplementationState.fixture_only,
    CrmImplementationState.read_only,
    CrmImplementationState.proposal_only,
    CrmImplementationState.blocked,
]

CRM_M1_VERTICAL_ORDER = [
    CrmWorkspaceKind.real_estate,
    CrmWorkspaceKind.healthcare,
    CrmWorkspaceKind.finance_insurance,
    CrmWorkspaceKind.retail_ecommerce,
    CrmWorkspaceKind.professional_services,
]

CRM_M1_REQUIRED_BLOCKED_REFS = [
    *CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    "blocked-state-ref:crm-m1:no-control-center-route-yet",
    "blocked-state-ref:crm-m1:no-backend-read-model-yet",
    "blocked-state-ref:crm-m1:no-ui-runtime-authority",
]


class _CrmM1Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CrmM1FixtureLane(_CrmM1Model):
    lane_ref: str
    safe_label: str
    state: CrmImplementationState = CrmImplementationState.fixture_only
    item_refs: list[str]
    evidence_refs: list[str]

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmM1FixtureLane":
        _validate_ref(self.lane_ref, "lane_ref")
        _validate_safe_text(self.safe_label, "safe_label", max_chars=120)
        _validate_ref_list(self.item_refs, "item_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if self.state != CrmImplementationState.fixture_only:
            raise ValueError("CRM_M1_LANE_FIXTURE_ONLY_REQUIRED")
        return self


class CrmM1FixtureSection(_CrmM1Model):
    section_ref: str
    section_kind: Literal[
        "pipeline",
        "relationship_inspector",
        "work_queue",
        "communications_metadata",
        "evidence",
        "memory_provenance",
        "blocked_authority",
        "vertical_context",
    ]
    safe_label: str
    state: CrmImplementationState
    evidence_refs: list[str]
    blocked_authority_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmM1FixtureSection":
        _validate_ref(self.section_ref, "section_ref")
        _validate_safe_text(self.safe_label, "safe_label", max_chars=120)
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_optional_ref_list(
            self.blocked_authority_refs,
            "blocked_authority_refs",
        )
        if self.state not in CRM_M1_REQUIRED_STATE_LABELS:
            raise ValueError("CRM_M1_SECTION_STATE_LABEL_REQUIRED")
        return self


class CrmM1VerticalFixture(_CrmM1Model):
    workspace_kind: CrmWorkspaceKind
    source_m0_contract_ref: str = CRM_COMMUNICATIONS_SPINE_CONTRACT_REF
    source_preset_pack_ref: str
    safe_display_label: str
    state: CrmImplementationState = CrmImplementationState.fixture_only
    nav_refs: list[str]
    object_kind_refs: list[str]
    work_queue_refs: list[str]
    pipeline_refs: list[str]
    inspector_section_refs: list[str]
    state_labels: list[CrmImplementationState]
    pipeline_lanes: list[CrmM1FixtureLane]
    screen_sections: list[CrmM1FixtureSection]
    communications_metadata_refs: list[str]
    evidence_refs: list[str]
    memory_provenance_refs: list[str]
    next_safe_action_refs: list[str]
    blocked_authority_refs: list[str]
    fixture_only: bool = True
    backend_read_model_added: bool = False
    backend_route_added: bool = False
    control_center_route_added: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    contact_import_enabled: bool = False
    silent_identity_merge_enabled: bool = False
    provider_model_call_enabled: bool = False
    live_web_enabled: bool = False
    browser_runtime_enabled: bool = False
    hidden_context_injection_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmM1VerticalFixture":
        _validate_ref(self.source_m0_contract_ref, "source_m0_contract_ref")
        _validate_ref(self.source_preset_pack_ref, "source_preset_pack_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label", max_chars=120)
        for field_name in [
            "nav_refs",
            "object_kind_refs",
            "work_queue_refs",
            "pipeline_refs",
            "inspector_section_refs",
            "communications_metadata_refs",
            "evidence_refs",
            "memory_provenance_refs",
            "next_safe_action_refs",
            "blocked_authority_refs",
        ]:
            _validate_ref_list(getattr(self, field_name), field_name)
        if set(self.state_labels) != set(CRM_M1_REQUIRED_STATE_LABELS):
            raise ValueError("CRM_M1_VERTICAL_STATE_LABELS_REQUIRED")
        if self.state != CrmImplementationState.fixture_only:
            raise ValueError("CRM_M1_VERTICAL_FIXTURE_ONLY_STATE_REQUIRED")
        if not self.fixture_only:
            raise ValueError("CRM_M1_VERTICAL_FIXTURE_ONLY_REQUIRED")
        for ref in CRM_M1_REQUIRED_BLOCKED_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("CRM_M1_BLOCKED_AUTHORITY_REFS_REQUIRED")
        _deny_true_flags(self, CRM_M1_AUTHORITY_DENIALS)
        return self


class CrmM1FixtureMap(_CrmM1Model):
    contract_ref: str = CRM_M1_FIXTURE_CONTRACT_REF
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            CRM_M1_FIXTURE_DOC_REF,
            CRM_M1_FIXTURE_VERIFIER_REF,
        ]
    )
    source_m0_contract_ref: str = CRM_COMMUNICATIONS_SPINE_CONTRACT_REF
    state: CrmImplementationState = CrmImplementationState.fixture_only
    state_labels: list[CrmImplementationState] = Field(
        default_factory=lambda: list(CRM_M1_REQUIRED_STATE_LABELS)
    )
    verticals: list[CrmM1VerticalFixture]
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CRM_M1_REQUIRED_BLOCKED_REFS)
    )
    prompts_executed_refs: list[str] = Field(
        default_factory=lambda: [
            f"prompt-ref:crm-product-sequence:{index:02d}"
            for index in range(1, 13)
        ]
    )
    fixture_only: bool = True
    backend_read_model_added: bool = False
    backend_route_added: bool = False
    control_center_route_added: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    contact_import_enabled: bool = False
    silent_identity_merge_enabled: bool = False
    provider_model_call_enabled: bool = False
    live_web_enabled: bool = False
    browser_runtime_enabled: bool = False
    hidden_context_injection_enabled: bool = False
    public_beta_claimed: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmM1FixtureMap":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref_list(self.docs_refs, "docs_refs")
        _validate_ref(self.source_m0_contract_ref, "source_m0_contract_ref")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.prompts_executed_refs, "prompts_executed_refs")
        if self.state != CrmImplementationState.fixture_only:
            raise ValueError("CRM_M1_FIXTURE_MAP_STATE_REQUIRED")
        if set(self.state_labels) != set(CRM_M1_REQUIRED_STATE_LABELS):
            raise ValueError("CRM_M1_FIXTURE_MAP_STATE_LABELS_REQUIRED")
        if {vertical.workspace_kind for vertical in self.verticals} != set(CrmWorkspaceKind):
            raise ValueError("CRM_M1_ALL_VERTICALS_REQUIRED")
        if len(self.verticals) != len({vertical.workspace_kind for vertical in self.verticals}):
            raise ValueError("CRM_M1_DUPLICATE_VERTICAL_DENIED")
        if not self.fixture_only:
            raise ValueError("CRM_M1_FIXTURE_ONLY_REQUIRED")
        for ref in CRM_M1_REQUIRED_BLOCKED_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("CRM_M1_BLOCKED_AUTHORITY_REFS_REQUIRED")
        _deny_true_flags(self, CRM_M1_AUTHORITY_DENIALS)
        return self


def build_crm_m1_fixture_map() -> CrmM1FixtureMap:
    m0 = build_crm_communications_spine_contract()
    preset_by_kind = {preset.workspace_kind: preset for preset in m0.preset_packs}
    return CrmM1FixtureMap(
        verticals=[
            _vertical_fixture(kind, preset_by_kind[kind])
            for kind in CRM_M1_VERTICAL_ORDER
        ]
    )


def validate_crm_m1_fixture_map(
    fixture_map: CrmM1FixtureMap | dict[str, Any],
) -> CrmM1FixtureMap:
    payload = fixture_map.model_dump(mode="python") if isinstance(fixture_map, BaseModel) else dict(fixture_map)
    _reject_private_text(payload)
    validated = CrmM1FixtureMap.model_validate(payload)
    _reject_private_text(validated.model_dump(mode="python"))
    return validated


def _vertical_fixture(
    kind: CrmWorkspaceKind,
    preset: Any,
) -> CrmM1VerticalFixture:
    spec = _VERTICAL_SPECS[kind]
    ref_suffix = kind.value.replace("_", "-")
    evidence_ref = f"evidence-ref:crm-m1:{ref_suffix}:fixture-map"
    return CrmM1VerticalFixture(
        workspace_kind=kind,
        source_preset_pack_ref=preset.preset_pack_ref,
        safe_display_label=spec["label"],
        nav_refs=[preset.nav_ref, f"nav-ref:crm-m1:{ref_suffix}:workspace"],
        object_kind_refs=[
            *preset.object_kind_refs,
            *[f"object-kind-ref:crm-m1:{ref_suffix}:{item}" for item in spec["objects"]],
        ],
        work_queue_refs=[
            *preset.work_queue_refs,
            *[f"work-queue-ref:crm-m1:{ref_suffix}:{item}" for item in spec["queues"]],
        ],
        pipeline_refs=[
            *preset.pipeline_refs,
            *[f"pipeline-ref:crm-m1:{ref_suffix}:{item}" for item in spec["pipelines"]],
        ],
        inspector_section_refs=[
            *preset.inspector_section_refs,
            *[f"inspector-section-ref:crm-m1:{ref_suffix}:{item}" for item in spec["inspectors"]],
        ],
        state_labels=list(CRM_M1_REQUIRED_STATE_LABELS),
        pipeline_lanes=[
            CrmM1FixtureLane(
                lane_ref=f"pipeline-lane-ref:crm-m1:{ref_suffix}:{lane}",
                safe_label=lane.replace("-", " ").title(),
                item_refs=[f"pipeline-item-ref:crm-m1:{ref_suffix}:{lane}:sample"],
                evidence_refs=[evidence_ref],
            )
            for lane in spec["lanes"]
        ],
        screen_sections=[
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:pipeline",
                section_kind="pipeline",
                safe_label=spec["pipeline_label"],
                state=CrmImplementationState.fixture_only,
                evidence_refs=[evidence_ref],
            ),
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:relationship-inspector",
                section_kind="relationship_inspector",
                safe_label=spec["inspector_label"],
                state=CrmImplementationState.fixture_only,
                evidence_refs=[evidence_ref],
            ),
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:work-queue",
                section_kind="work_queue",
                safe_label=spec["queue_label"],
                state=CrmImplementationState.proposal_only,
                evidence_refs=[evidence_ref],
            ),
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:communications-metadata",
                section_kind="communications_metadata",
                safe_label="Communications metadata placeholders",
                state=CrmImplementationState.blocked,
                evidence_refs=[evidence_ref],
                blocked_authority_refs=[
                    "blocked-state-ref:crm-comms-m0:no-email-or-message-sends",
                    "blocked-state-ref:crm-comms-m0:no-calendar-writes",
                    "blocked-state-ref:crm-comms-m0:no-account-sync",
                ],
            ),
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:evidence",
                section_kind="evidence",
                safe_label="Evidence and memory provenance",
                state=CrmImplementationState.read_only,
                evidence_refs=[evidence_ref],
            ),
            CrmM1FixtureSection(
                section_ref=f"section-ref:crm-m1:{ref_suffix}:blocked-authority",
                section_kind="blocked_authority",
                safe_label="Blocked authority posture",
                state=CrmImplementationState.blocked,
                evidence_refs=[evidence_ref],
                blocked_authority_refs=list(CRM_M1_REQUIRED_BLOCKED_REFS),
            ),
        ],
        communications_metadata_refs=[
            f"communication-ref:crm-m1:{ref_suffix}:metadata-placeholder",
        ],
        evidence_refs=[evidence_ref],
        memory_provenance_refs=[
            f"memory-ref:crm-m1:{ref_suffix}:reviewed-recall-only",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:crm-m1:{ref_suffix}:review-fixture",
            f"next-safe-action-ref:crm-m1:{ref_suffix}:record-blockers",
        ],
        blocked_authority_refs=list(CRM_M1_REQUIRED_BLOCKED_REFS),
    )


def _reject_private_text(payload: Any) -> None:
    if isinstance(payload, str):
        _validate_no_private_or_secret_text(payload, "crm_m1_fixture")
    elif isinstance(payload, dict):
        for value in payload.values():
            _reject_private_text(value)
    elif isinstance(payload, list | tuple | set):
        for value in payload:
            _reject_private_text(value)


CRM_M1_AUTHORITY_DENIALS = [
    ("backend_read_model_added", "CRM_M1_BACKEND_READ_MODEL_DENIED"),
    ("backend_route_added", "CRM_M1_BACKEND_ROUTE_DENIED"),
    ("control_center_route_added", "CRM_M1_CONTROL_CENTER_ROUTE_DENIED"),
    ("connector_runtime_enabled", "CRM_M1_CONNECTOR_RUNTIME_DENIED"),
    ("connector_write_enabled", "CRM_M1_CONNECTOR_WRITE_DENIED"),
    ("account_sync_enabled", "CRM_M1_ACCOUNT_SYNC_DENIED"),
    ("send_enabled", "CRM_M1_SEND_DENIED"),
    ("calendar_write_enabled", "CRM_M1_CALENDAR_WRITE_DENIED"),
    ("contact_import_enabled", "CRM_M1_CONTACT_IMPORT_DENIED"),
    ("silent_identity_merge_enabled", "CRM_M1_SILENT_IDENTITY_MERGE_DENIED"),
    ("provider_model_call_enabled", "CRM_M1_PROVIDER_MODEL_DENIED"),
    ("live_web_enabled", "CRM_M1_LIVE_WEB_DENIED"),
    ("browser_runtime_enabled", "CRM_M1_BROWSER_RUNTIME_DENIED"),
    ("hidden_context_injection_enabled", "CRM_M1_CONTEXT_INJECTION_DENIED"),
    ("production_authority_enabled", "CRM_M1_PRODUCTION_AUTHORITY_DENIED"),
]


_VERTICAL_SPECS = {
    CrmWorkspaceKind.real_estate: {
        "label": "Real Estate Realtor",
        "objects": ["lead", "buyer", "seller", "listing", "showing", "offer", "closing"],
        "queues": ["follow-up", "showing-review", "offer-review", "closing-risk"],
        "pipelines": ["lead-to-closing"],
        "inspectors": ["relationship", "property-listing", "timeline", "blocked-authority"],
        "lanes": ["new-lead", "active-client", "showing", "offer", "closing"],
        "pipeline_label": "Lead to closing pipeline",
        "inspector_label": "Relationship and property inspector",
        "queue_label": "Follow-up and closing work queue",
    },
    CrmWorkspaceKind.healthcare: {
        "label": "Healthcare",
        "objects": ["referral", "intake", "care-team", "organization", "handoff"],
        "queues": ["referral-follow-up", "handoff-review", "consent-review"],
        "pipelines": ["referral-to-intake"],
        "inspectors": ["provider-relationship", "organization", "consent", "blocked-authority"],
        "lanes": ["new-referral", "intake-review", "coordination", "handoff"],
        "pipeline_label": "Referral and intake pipeline",
        "inspector_label": "Organization and provider relationship view",
        "queue_label": "Follow-up and handoff queue",
    },
    CrmWorkspaceKind.finance_insurance: {
        "label": "Finance Insurance",
        "objects": ["prospect", "household", "organization", "policy", "opportunity", "renewal"],
        "queues": ["renewal-review", "risk-review", "proposal-review"],
        "pipelines": ["opportunity-renewal"],
        "inspectors": ["relationship", "household-org", "compliance", "blocked-authority"],
        "lanes": ["prospect", "needs-review", "proposal", "renewal", "blocked"],
        "pipeline_label": "Opportunity and renewal pipeline",
        "inspector_label": "Relationship and household inspector",
        "queue_label": "Follow-up and review queue",
    },
    CrmWorkspaceKind.retail_ecommerce: {
        "label": "Retail E-commerce",
        "objects": ["customer-cohort", "order-metadata", "support-case", "campaign-proposal", "retention"],
        "queues": ["retention-follow-up", "support-review", "campaign-review"],
        "pipelines": ["customer-retention"],
        "inspectors": ["cohort", "relationship", "evidence", "blocked-authority"],
        "lanes": ["new-cohort", "at-risk", "proposal", "retention"],
        "pipeline_label": "Customer and opportunity pipeline",
        "inspector_label": "Cohort and relationship inspector",
        "queue_label": "Retention and follow-up work queue",
    },
    CrmWorkspaceKind.professional_services: {
        "label": "Professional Services",
        "objects": ["lead", "client", "project", "proposal", "commitment", "account-health"],
        "queues": ["promise-follow-up", "proposal-review", "account-health-review"],
        "pipelines": ["lead-proposal-project"],
        "inspectors": ["client", "stakeholder", "commitment", "blocked-authority"],
        "lanes": ["lead", "proposal", "active-project", "commitment", "needs-review"],
        "pipeline_label": "Lead proposal and project pipeline",
        "inspector_label": "Client and stakeholder relationship inspector",
        "queue_label": "Promise and follow-up work queue",
    },
}
