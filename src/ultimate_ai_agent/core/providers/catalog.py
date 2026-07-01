from __future__ import annotations

from datetime import date
from enum import Enum
import re
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


PROVIDER_SETUP_GUIDE_ROUTE_REF = "GET /control-center/providers/setup-guide"
PROVIDER_CATALOG_LAST_VERIFIED_AT = date(2026, 6, 25)

SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
ENV_VAR_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:;()+#&%/|$'?-]{0,899}$")
LOCAL_PATH_RE = re.compile(r"(?i)(/Users/|/home/|[A-Za-z]:\\Users\\|\\\\Users\\\\|~/)")
UNSAFE_COPY_PATTERNS = (
    re.compile(r"(?i)\bpaste\s+(?:your\s+)?(?:api\s+)?key\b"),
    re.compile(r"(?i)\bsave\s+(?:your\s+)?(?:api\s+)?key\b"),
    re.compile(r"(?i)\btest\s+provider\b"),
    re.compile(r"(?i)\bconnect\s+provider\b"),
    re.compile(r"(?i)\binvoke\s+provider\b"),
    re.compile(r"(?i)\braw\s+prompt\b"),
    re.compile(r"(?i)\braw\s+response\b"),
    re.compile(r"(?i)\braw\s+provider\s+(?:payload|exchange|content)\b"),
    re.compile(r"(?i)\benvironment\s+dump\b"),
)
REQUIRED_AUTHORITY_BLOCKERS = {
    "PROVIDER_CREDENTIAL_COLLECTION_BLOCKED",
    "PROVIDER_VAULT_STORAGE_BLOCKED",
    "PROVIDER_CREDENTIAL_VALIDATION_BLOCKED",
    "PROVIDER_INVOCATION_BLOCKED",
    "PROVIDER_RESPONSE_PERSISTENCE_BLOCKED",
    "PROVIDER_AUTOMATIC_PRICING_REFRESH_BLOCKED",
    "PROVIDER_OUTPUT_NOT_AUTHORITY",
    "UNKNOWN_PAID_COST_REQUIRES_EXPLICIT_APPROVAL",
}


class ProviderCatalogProviderClass(str, Enum):
    direct_model_provider = "direct_model_provider"
    router_or_platform = "router_or_platform"
    cloud_or_enterprise_channel = "cloud_or_enterprise_channel"
    local_or_open_model_family = "local_or_open_model_family"


class ProviderCatalogAuthorityState(str, Enum):
    guidance_only = "guidance_only"
    credential_not_configured = "credential_not_configured"
    vault_blocked = "vault_blocked"
    validation_blocked = "validation_blocked"
    invocation_blocked = "invocation_blocked"
    blocked = "blocked"


class ProviderSourceKind(str, Enum):
    setup = "setup"
    api_docs = "api_docs"
    pricing = "pricing"
    billing = "billing"
    tokens = "tokens"
    models = "models"
    rate_limits = "rate_limits"
    cost_context = "cost_context"


class ProviderBillingPrerequisite(str, Enum):
    provider_account_required = "provider_account_required"
    provider_billing_required = "provider_billing_required"
    cloud_project_billing_required = "cloud_project_billing_required"
    router_credit_or_account_required = "router_credit_or_account_required"
    enterprise_account_or_cloud_billing_required = "enterprise_account_or_cloud_billing_required"
    local_hardware_or_hosting_costs = "local_hardware_or_hosting_costs"


class ProviderCostUnit(str, Enum):
    input_tokens = "input_tokens"
    cached_input_tokens = "cached_input_tokens"
    output_tokens = "output_tokens"
    reasoning_or_thinking_tokens = "reasoning_or_thinking_tokens"
    context_cache = "context_cache"
    batch_job = "batch_job"
    request_or_tool_add_on = "request_or_tool_add_on"
    image_audio_video = "image_audio_video"
    hardware_time = "hardware_time"
    rate_limit_or_quota = "rate_limit_or_quota"
    local_hardware = "local_hardware"


class _ProviderCatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True, hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class ProviderSourceRef(_ProviderCatalogModel):
    source_ref: str
    source_kind: ProviderSourceKind
    label: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    last_verified_at: date = PROVIDER_CATALOG_LAST_VERIFIED_AT
    reviewed_static_metadata: bool = True
    runtime_fetch_performed: bool = False
    provider_call_performed: bool = False
    not_authority: bool = True

    @model_validator(mode="after")
    def source_ref_must_be_static_metadata(self) -> "ProviderSourceRef":
        _validate_ref(self.source_ref, "source_ref")
        _validate_safe_text(self.label, "label", max_chars=120)
        _validate_https_source_url(self.url, "url")
        if not self.reviewed_static_metadata:
            raise ValueError("PROVIDER_SOURCE_REVIEWED_STATIC_METADATA_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("runtime_fetch_performed", "PROVIDER_SOURCE_RUNTIME_FETCH_DENIED"),
                ("provider_call_performed", "PROVIDER_SOURCE_PROVIDER_CALL_DENIED"),
            ],
        )
        if not self.not_authority:
            raise ValueError("PROVIDER_SOURCE_AUTHORITY_CLAIM_DENIED")
        return self


class BudgetPosture(_ProviderCatalogModel):
    budget_posture_ref: str = "provider-budget-posture:cost-literacy:unknown-paid-cost"
    state: Literal["approval_required_for_paid_or_unknown_cost"] = (
        "approval_required_for_paid_or_unknown_cost"
    )
    unknown_paid_cost_requires_explicit_approval: bool = True
    estimated_cost_above_budget_blocks_use: bool = True
    provider_model_refs_required: bool = True
    cost_estimate_ref_required: bool = True
    budget_decision_ref_required: bool = True
    receipt_ref_required: bool = True
    max_approved_usd_required: bool = True
    cost_governor_binding_required: bool = True
    provider_use_authority_granted: bool = False
    safe_summary: str = (
        "Paid or unknown provider costs require explicit approval, provider refs, cost estimate refs, "
        "budget decisions, and receipt refs before any future provider use."
    )

    @model_validator(mode="after")
    def budget_posture_must_block_unknown_paid_cost(self) -> "BudgetPosture":
        _validate_ref(self.budget_posture_ref, "budget_posture_ref")
        required = [
            self.unknown_paid_cost_requires_explicit_approval,
            self.estimated_cost_above_budget_blocks_use,
            self.provider_model_refs_required,
            self.cost_estimate_ref_required,
            self.budget_decision_ref_required,
            self.receipt_ref_required,
            self.max_approved_usd_required,
            self.cost_governor_binding_required,
        ]
        if not all(required):
            raise ValueError("PROVIDER_BUDGET_REQUIRED_GATE_DENIED")
        if self.provider_use_authority_granted:
            raise ValueError("PROVIDER_BUDGET_AUTHORITY_DENIED")
        _validate_safe_text(self.safe_summary, "safe_summary")
        return self


class ProviderAuthorityPosture(_ProviderCatalogModel):
    authority_ref: str
    authority_state: ProviderCatalogAuthorityState = ProviderCatalogAuthorityState.guidance_only
    credential_input_enabled: bool = False
    raw_key_storage_enabled: bool = False
    vault_storage_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    runtime_network_call_enabled: bool = False
    model_invocation_enabled: bool = False
    automatic_pricing_refresh_enabled: bool = False
    provider_response_persistence_enabled: bool = False
    provider_output_authority_enabled: bool = False
    provider_configuration_enabled: bool = False
    catalog_visibility_grants_authority: bool = False
    billing_authority_claimed: bool = False
    blocker_codes: list[str] = Field(default_factory=lambda: sorted(REQUIRED_AUTHORITY_BLOCKERS))
    safe_summary: str = (
        "Provider catalog visibility is guidance only; credentials, validation, invocation, billing authority, "
        "automatic pricing refresh, and provider output authority remain blocked."
    )

    @model_validator(mode="after")
    def authority_posture_must_remain_guidance_only(self) -> "ProviderAuthorityPosture":
        _validate_ref(self.authority_ref, "authority_ref")
        denied_flags = [
            self.credential_input_enabled,
            self.raw_key_storage_enabled,
            self.vault_storage_enabled,
            self.credential_validation_enabled,
            self.provider_sdk_call_enabled,
            self.runtime_network_call_enabled,
            self.model_invocation_enabled,
            self.automatic_pricing_refresh_enabled,
            self.provider_response_persistence_enabled,
            self.provider_output_authority_enabled,
            self.provider_configuration_enabled,
            self.catalog_visibility_grants_authority,
            self.billing_authority_claimed,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_CATALOG_AUTHORITY_DENIED")
        if self.authority_state != ProviderCatalogAuthorityState.guidance_only:
            raise ValueError("PROVIDER_CATALOG_AUTHORITY_STATE_DENIED")
        if not REQUIRED_AUTHORITY_BLOCKERS.issubset(set(self.blocker_codes)):
            raise ValueError("PROVIDER_CATALOG_AUTHORITY_BLOCKERS_REQUIRED")
        _validate_safe_text(self.safe_summary, "safe_summary")
        return self


class ProviderKeyInstruction(_ProviderCatalogModel):
    instruction_ref: str
    provider_ref: str
    env_var_styles: list[str] = Field(..., min_length=1)
    requires_api_key: bool = True
    setup_source_ref: str
    api_docs_source_ref: str
    safe_summary: str
    credential_input_enabled: bool = False
    raw_key_storage_enabled: bool = False
    vault_storage_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    credential_material_included: bool = False

    @model_validator(mode="after")
    def key_instruction_must_not_collect_keys(self) -> "ProviderKeyInstruction":
        _validate_ref(self.instruction_ref, "instruction_ref")
        _validate_ref(self.provider_ref, "provider_ref")
        _validate_ref(self.setup_source_ref, "setup_source_ref")
        _validate_ref(self.api_docs_source_ref, "api_docs_source_ref")
        if not self.env_var_styles:
            raise ValueError("PROVIDER_KEY_ENV_VAR_STYLE_REQUIRED")
        for env_var in self.env_var_styles:
            _validate_env_var_style(env_var)
        if (
            self.credential_input_enabled
            or self.raw_key_storage_enabled
            or self.vault_storage_enabled
            or self.credential_validation_enabled
            or self.provider_sdk_call_enabled
            or self.credential_material_included
        ):
            raise ValueError("PROVIDER_KEY_INSTRUCTION_AUTHORITY_DENIED")
        _validate_safe_text(self.safe_summary, "safe_summary")
        return self


class ProviderCostProfile(_ProviderCatalogModel):
    cost_profile_ref: str
    provider_ref: str
    pricing_source_ref: str
    billing_prerequisite: ProviderBillingPrerequisite
    cost_units: list[ProviderCostUnit] = Field(..., min_length=1)
    token_cost_notes: list[str] = Field(..., min_length=1)
    pricing_may_change: bool = True
    not_billing_authority: bool = True
    reviewed_static_metadata: bool = True
    synthetic_examples_only: bool = True
    live_price_amounts_included: bool = False
    automatic_pricing_fetch_enabled: bool = False
    runtime_cost_estimate_enabled: bool = False
    billing_account_authority_enabled: bool = False

    @model_validator(mode="after")
    def cost_profile_must_be_advisory_only(self) -> "ProviderCostProfile":
        _validate_ref(self.cost_profile_ref, "cost_profile_ref")
        _validate_ref(self.provider_ref, "provider_ref")
        _validate_ref(self.pricing_source_ref, "pricing_source_ref")
        if not self.pricing_may_change:
            raise ValueError("PROVIDER_COST_PRICING_MAY_CHANGE_REQUIRED")
        if not self.not_billing_authority:
            raise ValueError("PROVIDER_COST_NOT_BILLING_AUTHORITY_REQUIRED")
        if not self.reviewed_static_metadata or not self.synthetic_examples_only:
            raise ValueError("PROVIDER_COST_STATIC_SYNTHETIC_ONLY_REQUIRED")
        if (
            self.live_price_amounts_included
            or self.automatic_pricing_fetch_enabled
            or self.runtime_cost_estimate_enabled
            or self.billing_account_authority_enabled
        ):
            raise ValueError("PROVIDER_COST_AUTHORITY_DENIED")
        for note in self.token_cost_notes:
            _validate_safe_text(note, "token_cost_note")
        return self


class TokenCostExample(_ProviderCatalogModel):
    example_ref: str
    label: str
    workload_kind: Literal[
        "quick_chat",
        "crm_briefing",
        "long_document_review",
        "code_task",
        "batch_analysis",
    ]
    safe_summary: str
    cost_driver_notes: list[str] = Field(..., min_length=1)
    synthetic_only: bool = True
    no_live_price_amounts: bool = True
    not_cost_estimate: bool = True
    approval_required_for_paid_use: bool = True

    @model_validator(mode="after")
    def token_example_must_be_literacy_only(self) -> "TokenCostExample":
        _validate_ref(self.example_ref, "example_ref")
        _validate_safe_text(self.label, "label", max_chars=120)
        _validate_safe_text(self.safe_summary, "safe_summary")
        for note in self.cost_driver_notes:
            _validate_safe_text(note, "cost_driver_note")
        if not (
            self.synthetic_only
            and self.no_live_price_amounts
            and self.not_cost_estimate
            and self.approval_required_for_paid_use
        ):
            raise ValueError("PROVIDER_TOKEN_EXAMPLE_AUTHORITY_DENIED")
        return self


class ProviderSetupCard(_ProviderCatalogModel):
    provider_ref: str
    provider_label: str
    provider_class: ProviderCatalogProviderClass
    provider_manifest_ref: str
    setup_link: str
    api_docs_link: str
    pricing_link: str
    env_var_styles: list[str] = Field(..., min_length=1)
    billing_prerequisite: ProviderBillingPrerequisite
    token_cost_notes: list[str] = Field(..., min_length=1)
    authority_state: ProviderCatalogAuthorityState = ProviderCatalogAuthorityState.guidance_only
    last_verified_at: date = PROVIDER_CATALOG_LAST_VERIFIED_AT
    pricing_may_change: bool = True
    not_billing_authority: bool = True
    source_refs: list[ProviderSourceRef] = Field(..., min_length=3)
    key_instruction: ProviderKeyInstruction
    cost_profile: ProviderCostProfile
    authority_posture: ProviderAuthorityPosture
    setup_step_ref: str = "setup-step:provider-account-guidance"
    guidance_only: bool = True
    credential_input_enabled: bool = False
    raw_key_storage_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    automatic_pricing_refresh_enabled: bool = False
    provider_output_authority_enabled: bool = False

    @model_validator(mode="after")
    def card_must_be_complete_guidance_only(self) -> "ProviderSetupCard":
        _validate_ref(self.provider_ref, "provider_ref")
        _validate_safe_text(self.provider_label, "provider_label", max_chars=120)
        _validate_ref(self.provider_manifest_ref, "provider_manifest_ref")
        _validate_ref(self.setup_step_ref, "setup_step_ref")
        for url in [self.setup_link, self.api_docs_link, self.pricing_link]:
            _validate_https_source_url(url, "provider_link")
        for env_var in self.env_var_styles:
            _validate_env_var_style(env_var)
        if self.key_instruction.provider_ref != self.provider_ref:
            raise ValueError("PROVIDER_CARD_KEY_INSTRUCTION_REF_MISMATCH")
        if self.cost_profile.provider_ref != self.provider_ref:
            raise ValueError("PROVIDER_CARD_COST_PROFILE_REF_MISMATCH")
        if self.authority_posture.authority_ref != f"provider-authority:{self.provider_ref.split(':', 1)[1]}":
            raise ValueError("PROVIDER_CARD_AUTHORITY_REF_MISMATCH")
        source_kinds = {source.source_kind for source in self.source_refs}
        if not {ProviderSourceKind.setup, ProviderSourceKind.api_docs, ProviderSourceKind.pricing}.issubset(
            source_kinds
        ):
            raise ValueError("PROVIDER_CARD_REQUIRED_SOURCE_LINKS_MISSING")
        source_urls = {source.url for source in self.source_refs}
        if not {self.setup_link, self.api_docs_link, self.pricing_link}.issubset(source_urls):
            raise ValueError("PROVIDER_CARD_REQUIRED_LINKS_NOT_SOURCE_REFS")
        if self.key_instruction.env_var_styles != self.env_var_styles:
            raise ValueError("PROVIDER_CARD_ENV_VAR_STYLE_MISMATCH")
        if self.cost_profile.billing_prerequisite != self.billing_prerequisite:
            raise ValueError("PROVIDER_CARD_BILLING_PREREQUISITE_MISMATCH")
        if self.cost_profile.token_cost_notes != self.token_cost_notes:
            raise ValueError("PROVIDER_CARD_TOKEN_NOTES_MISMATCH")
        if self.authority_state != ProviderCatalogAuthorityState.guidance_only:
            raise ValueError("PROVIDER_CARD_AUTHORITY_STATE_DENIED")
        if not self.pricing_may_change or not self.not_billing_authority or not self.guidance_only:
            raise ValueError("PROVIDER_CARD_REQUIRED_ADVISORY_FLAGS_DENIED")
        denied_flags = [
            self.credential_input_enabled,
            self.raw_key_storage_enabled,
            self.credential_validation_enabled,
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.automatic_pricing_refresh_enabled,
            self.provider_output_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_CARD_RUNTIME_AUTHORITY_DENIED")
        for note in self.token_cost_notes:
            _validate_safe_text(note, "token_cost_note")
        return self


class ProviderCatalog(_ProviderCatalogModel):
    schema_version: Literal["uaa-provider-catalog-cost-literacy.v1"] = (
        "uaa-provider-catalog-cost-literacy.v1"
    )
    catalog_ref: str = "provider-catalog:cost-literacy:v1"
    route_ref: Literal[PROVIDER_SETUP_GUIDE_ROUTE_REF] = PROVIDER_SETUP_GUIDE_ROUTE_REF
    status: Literal["read_only_guidance"] = "read_only_guidance"
    source_posture: Literal["reviewed_static_timestamped_metadata"] = (
        "reviewed_static_timestamped_metadata"
    )
    last_verified_at: date = PROVIDER_CATALOG_LAST_VERIFIED_AT
    safe_summary: str = (
        "Provider setup guidance and cost literacy are read-only metadata. Credential collection, "
        "provider validation, model invocation, provider calls, and automatic pricing refresh remain blocked."
    )
    provider_cards: list[ProviderSetupCard] = Field(..., min_length=1)
    token_cost_examples: list[TokenCostExample] = Field(..., min_length=1)
    budget_posture: BudgetPosture = Field(default_factory=BudgetPosture)
    blocked_authorities: list[str] = Field(default_factory=lambda: sorted(REQUIRED_AUTHORITY_BLOCKERS))
    product_language_rules: list[str] = Field(
        default_factory=lambda: [
            "Provider guidance is not credential enrollment.",
            "Pricing guidance is not billing authority.",
            "Provider docs links are reviewed metadata, not runtime fetches.",
            "Provider output is never product truth or authority.",
        ]
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "safe_refs_only",
            "credential_values_omitted",
            "provider_payloads_omitted",
            "live_prices_omitted",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/control_center/PROVIDER_CATALOG_COST_LITERACY.md",
            "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: ["scripts/verify_provider_catalog_cost_literacy.py"]
    )
    no_credential_input: bool = True
    no_raw_key_storage: bool = True
    no_provider_validation: bool = True
    no_provider_sdk_calls: bool = True
    no_model_invocation: bool = True
    no_runtime_web_fetching: bool = True
    no_automatic_pricing_fetch: bool = True
    no_provider_output_authority: bool = True
    catalog_visibility_grants_authority: bool = False

    @model_validator(mode="after")
    def catalog_must_be_read_only_guidance(self) -> "ProviderCatalog":
        _validate_ref(self.catalog_ref, "catalog_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if len({card.provider_ref for card in self.provider_cards}) != len(self.provider_cards):
            raise ValueError("PROVIDER_CATALOG_DUPLICATE_PROVIDER_REFS_DENIED")
        if not REQUIRED_AUTHORITY_BLOCKERS.issubset(set(self.blocked_authorities)):
            raise ValueError("PROVIDER_CATALOG_BLOCKED_AUTHORITIES_REQUIRED")
        required_denials = [
            self.no_credential_input,
            self.no_raw_key_storage,
            self.no_provider_validation,
            self.no_provider_sdk_calls,
            self.no_model_invocation,
            self.no_runtime_web_fetching,
            self.no_automatic_pricing_fetch,
            self.no_provider_output_authority,
        ]
        if not all(required_denials):
            raise ValueError("PROVIDER_CATALOG_DENIAL_FLAGS_REQUIRED")
        if self.catalog_visibility_grants_authority:
            raise ValueError("PROVIDER_CATALOG_VISIBILITY_AUTHORITY_DENIED")
        for rule in self.product_language_rules:
            _validate_safe_text(rule, "product_language_rule")
        for ref in [*self.docs_refs, *self.verifier_refs]:
            _validate_doc_or_script_ref(ref)
        _reject_unsafe_payload(self.model_dump(mode="json"), "PROVIDER_CATALOG_UNSAFE_PAYLOAD_REJECTED")
        return self


def build_provider_catalog() -> ProviderCatalog:
    return ProviderCatalog(
        provider_cards=_provider_cards(),
        token_cost_examples=_token_cost_examples(),
    )


def build_provider_setup_guide_catalog() -> ProviderCatalog:
    return build_provider_catalog()


def _provider_cards() -> list[ProviderSetupCard]:
    return [
        _card(
            provider_slug="openai",
            label="OpenAI API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://platform.openai.com/api-keys",
            api_docs_link="https://developers.openai.com/api/reference/overview/",
            pricing_link="https://openai.com/api/pricing/",
            env_var_styles=["OPENAI_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "API usage is billed separately from ChatGPT subscriptions.",
                "Costs can vary by input output cached input reasoning and tool use.",
            ],
        ),
        _card(
            provider_slug="anthropic",
            label="Anthropic Claude API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://platform.claude.com/",
            api_docs_link="https://platform.claude.com/docs/en/api/overview",
            pricing_link="https://platform.claude.com/docs/en/about-claude/pricing",
            env_var_styles=["ANTHROPIC_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Claude subscription usage is separate from Claude API usage.",
                "Costs can vary by input output cache and model family.",
            ],
        ),
        _card(
            provider_slug="google-gemini",
            label="Google Gemini API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://aistudio.google.com/app/apikey",
            api_docs_link="https://ai.google.dev/gemini-api/docs",
            pricing_link="https://ai.google.dev/gemini-api/docs/pricing",
            env_var_styles=["GEMINI_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.cloud_project_billing_required,
            token_cost_notes=[
                "Keys are associated with Google Cloud projects and billing posture.",
                "Costs can vary by tokens context cache batch media and grounding features.",
            ],
            extra_sources=[
                (ProviderSourceKind.billing, "Google Gemini billing", "https://ai.google.dev/gemini-api/docs/billing"),
                (ProviderSourceKind.tokens, "Google Gemini tokens", "https://ai.google.dev/gemini-api/docs/tokens"),
            ],
        ),
        _card(
            provider_slug="xai",
            label="xAI Grok API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://x.ai/api",
            api_docs_link="https://docs.x.ai/overview",
            pricing_link="https://docs.x.ai/developers/pricing",
            env_var_styles=["XAI_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Costs can vary across chat coding image video voice and server side tools.",
                "Paid tool or search style add ons need explicit budget review before use.",
            ],
            extra_sources=[(ProviderSourceKind.models, "xAI models", "https://docs.x.ai/developers/models")],
        ),
        _card(
            provider_slug="mistral",
            label="Mistral API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://docs.mistral.ai/",
            api_docs_link="https://docs.mistral.ai/api/endpoint/chat",
            pricing_link="https://mistral.ai/pricing/",
            env_var_styles=["MISTRAL_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Costs can vary by token direction batch discounts prompt caching and model family.",
                "Open model availability does not make hosted API usage free.",
            ],
        ),
        _card(
            provider_slug="cohere",
            label="Cohere API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://docs.cohere.com/docs/rate-limits",
            api_docs_link="https://docs.cohere.com/reference/about",
            pricing_link="https://cohere.com/pricing",
            env_var_styles=["COHERE_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Trial keys and production keys can have different quota and billing posture.",
                "Costs can vary by model task family and rate limit tier.",
            ],
            extra_sources=[
                (ProviderSourceKind.rate_limits, "Cohere rate limits", "https://docs.cohere.com/docs/rate-limits")
            ],
        ),
        _card(
            provider_slug="deepseek",
            label="DeepSeek API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://api-docs.deepseek.com/",
            api_docs_link="https://api-docs.deepseek.com/api/deepseek-api",
            pricing_link="https://api-docs.deepseek.com/quick_start/pricing",
            env_var_styles=["DEEPSEEK_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Cache hit and cache miss pricing may differ.",
                "Reasoning and long context usage can change token spend materially.",
            ],
            extra_sources=[
                (ProviderSourceKind.tokens, "DeepSeek token usage", "https://api-docs.deepseek.com/quick_start/token_usage")
            ],
        ),
        _card(
            provider_slug="perplexity",
            label="Perplexity API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://docs.perplexity.ai/docs/admin/api-key-management",
            api_docs_link="https://docs.perplexity.ai/docs/getting-started/overview",
            pricing_link="https://docs.perplexity.ai/docs/getting-started/pricing",
            env_var_styles=["PERPLEXITY_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Search agent and tool invocation costs can be separate from token costs.",
                "Grounded answer features require cost and authority review before use.",
            ],
        ),
        _card(
            provider_slug="ai21",
            label="AI21 API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://docs.ai21.com/docs/create-api-key",
            api_docs_link="https://docs.ai21.com/home",
            pricing_link="https://docs.ai21.com/docs/usage-cost",
            env_var_styles=["AI21_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Trial credit expiration and billing requirements must be reviewed with provider docs.",
                "Usage cost can vary by task model and token volume.",
            ],
        ),
        _card(
            provider_slug="moonshot-kimi",
            label="Moonshot Kimi API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://platform.kimi.ai/docs/overview",
            api_docs_link="https://platform.kimi.ai/docs/overview",
            pricing_link="https://platform.kimi.ai/docs/pricing/chat",
            env_var_styles=["KIMI_API_KEY", "MOONSHOT_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Long context coding multimodal and thinking model usage can have different cost posture.",
                "Alternate env var names are labels only and no key value is collected here.",
            ],
        ),
        _card(
            provider_slug="zai-glm",
            label="Z.AI GLM API",
            provider_class=ProviderCatalogProviderClass.direct_model_provider,
            setup_link="https://docs.z.ai/guides/overview/quick-start",
            api_docs_link="https://docs.z.ai/guides/develop/http/introduction",
            pricing_link="https://docs.z.ai/guides/overview/pricing",
            env_var_styles=["ZAI_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Cached input pricing and coding plan subscription posture can differ.",
                "Provider plan labels are advisory metadata and not billing authority.",
            ],
        ),
        _card(
            provider_slug="openrouter",
            label="OpenRouter",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://openrouter.ai/docs/api/reference/authentication",
            api_docs_link="https://openrouter.ai/docs/api/reference/overview",
            pricing_link="https://openrouter.ai/pricing",
            env_var_styles=["OPENROUTER_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.router_credit_or_account_required,
            token_cost_notes=[
                "Routers can expose upstream providers fallback behavior privacy settings and credit limits.",
                "Router markups and upstream model pricing need explicit cost review.",
            ],
            extra_sources=[
                (ProviderSourceKind.models, "OpenRouter models guide", "https://openrouter.ai/docs/guides/overview/models")
            ],
        ),
        _card(
            provider_slug="together-ai",
            label="Together AI",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://docs.together.ai/docs/quickstart",
            api_docs_link="https://docs.together.ai/docs/quickstart",
            pricing_link="https://www.together.ai/pricing",
            env_var_styles=["TOGETHER_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Serverless inference batch fine tuning and dedicated endpoints can bill differently.",
                "Hosted open model usage still needs paid cost approval when applicable.",
            ],
        ),
        _card(
            provider_slug="fireworks-ai",
            label="Fireworks AI",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://docs.fireworks.ai/getting-started/quickstart",
            api_docs_link="https://docs.fireworks.ai/api-reference/introduction",
            pricing_link="https://fireworks.ai/pricing",
            env_var_styles=["FIREWORKS_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Serverless priority tiers deployments and model library usage can price differently.",
                "Deployment style must be reviewed before any future provider adapter is scoped.",
            ],
        ),
        _card(
            provider_slug="groq",
            label="Groq",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://console.groq.com/",
            api_docs_link="https://console.groq.com/docs/api-reference",
            pricing_link="https://groq.com/pricing",
            env_var_styles=["GROQ_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Fast inference open model catalog service tiers and quotas can affect spend.",
                "Rate limits are cost and reliability posture not runtime authority.",
            ],
            extra_sources=[
                (ProviderSourceKind.rate_limits, "Groq rate limits", "https://console.groq.com/docs/rate-limits")
            ],
        ),
        _card(
            provider_slug="replicate",
            label="Replicate",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://replicate.com/docs/topics/security/api-tokens",
            api_docs_link="https://replicate.com/docs/reference/http",
            pricing_link="https://replicate.com/pricing",
            env_var_styles=["REPLICATE_API_TOKEN"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Some workloads bill by hardware time rather than only input and output tokens.",
                "Media generation and hosted model runtime cost require exact future budget scope.",
            ],
        ),
        _card(
            provider_slug="cerebras",
            label="Cerebras Inference",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://inference-docs.cerebras.ai/introduction",
            api_docs_link="https://inference-docs.cerebras.ai/introduction",
            pricing_link="https://www.cerebras.ai/pricing",
            env_var_styles=["CEREBRAS_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Free developer and paid tiers can differ in token per day and quota posture.",
                "Cost and quota posture must be reviewed before any hosted inference use.",
            ],
            extra_sources=[(ProviderSourceKind.models, "Cerebras inference", "https://www.cerebras.ai/inference")],
        ),
        _card(
            provider_slug="sambanova",
            label="SambaNova Cloud",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://cloud.sambanova.ai/apis",
            api_docs_link="https://docs.sambanova.ai/docs/en/get-started/quickstart",
            pricing_link="https://cloud.sambanova.ai/plans/pricing",
            env_var_styles=["SAMBANOVA_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.provider_billing_required,
            token_cost_notes=[
                "Free credits key limits model choice and cloud versus stack deployment can change cost posture.",
                "Plans are provider metadata and not UAA billing authority.",
            ],
            extra_sources=[(ProviderSourceKind.billing, "SambaNova plans", "https://cloud.sambanova.ai/plans")],
        ),
        _card(
            provider_slug="nvidia-nim",
            label="NVIDIA NIM",
            provider_class=ProviderCatalogProviderClass.router_or_platform,
            setup_link="https://build.nvidia.com/settings/api-keys",
            api_docs_link="https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html",
            pricing_link="https://developer.nvidia.com/nim",
            env_var_styles=["NVIDIA_API_KEY"],
            billing_prerequisite=ProviderBillingPrerequisite.enterprise_account_or_cloud_billing_required,
            token_cost_notes=[
                "Cloud hosted NIM and local self hosted NIM have different cost and infrastructure posture.",
                "GPU hosting quota and enterprise terms need separate budget review.",
            ],
        ),
        _card(
            provider_slug="azure-openai",
            label="Azure OpenAI",
            provider_class=ProviderCatalogProviderClass.cloud_or_enterprise_channel,
            setup_link="https://learn.microsoft.com/en-us/azure/foundry/openai/reference",
            api_docs_link="https://learn.microsoft.com/en-us/azure/foundry/openai/reference",
            pricing_link="https://azure.microsoft.com/en-us/pricing/details/azure-openai/",
            env_var_styles=["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
            billing_prerequisite=ProviderBillingPrerequisite.enterprise_account_or_cloud_billing_required,
            token_cost_notes=[
                "Azure endpoint deployment name API key or Entra auth and regional quota are separate setup concerns.",
                "Pay as you go and provisioned throughput can have different cost posture.",
            ],
            extra_sources=[
                (
                    ProviderSourceKind.rate_limits,
                    "Azure OpenAI quotas and limits",
                    "https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits",
                )
            ],
        ),
        _card(
            provider_slug="aws-bedrock",
            label="AWS Bedrock",
            provider_class=ProviderCatalogProviderClass.cloud_or_enterprise_channel,
            setup_link="https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html",
            api_docs_link="https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-how.html",
            pricing_link="https://aws.amazon.com/bedrock/pricing/",
            env_var_styles=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
            billing_prerequisite=ProviderBillingPrerequisite.enterprise_account_or_cloud_billing_required,
            token_cost_notes=[
                "AWS credentials IAM and Bedrock API keys are separate setup modes.",
                "Provider and model specific pricing plus IAM posture need exact future scope.",
            ],
        ),
        _card(
            provider_slug="google-vertex-ai",
            label="Google Vertex AI Gemini Enterprise",
            provider_class=ProviderCatalogProviderClass.cloud_or_enterprise_channel,
            setup_link="https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/api-keys",
            api_docs_link="https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/api-keys",
            pricing_link="https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing",
            env_var_styles=["GOOGLE_APPLICATION_CREDENTIALS_REF", "GOOGLE_CLOUD_PROJECT"],
            billing_prerequisite=ProviderBillingPrerequisite.enterprise_account_or_cloud_billing_required,
            token_cost_notes=[
                "Google Cloud project billing account region quota and service account posture are separate concerns.",
                "Enterprise pricing can differ from Gemini Developer API pricing.",
            ],
        ),
        _card(
            provider_slug="meta-llama",
            label="Meta Llama local or hosted family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://www.llama.com/docs/overview/",
            api_docs_link="https://www.llama.com/docs/overview/",
            pricing_link="https://www.llama.com/",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Local open model use shifts cost to hardware storage power and hosting time.",
                "Hosted endpoints for open models still require provider budget review.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="qwen",
            label="Qwen local or hosted family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://qwen.readthedocs.io/",
            api_docs_link="https://qwen.readthedocs.io/",
            pricing_link="https://qwen.readthedocs.io/",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Local open model costs depend on hardware storage power and deployment shape.",
                "Any hosted Qwen endpoint remains a future provider adapter concern.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="mistral-open-models",
            label="Mistral open model family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://docs.mistral.ai/",
            api_docs_link="https://docs.mistral.ai/",
            pricing_link="https://mistral.ai/pricing/",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Open weights can be local but hosted API usage can still be paid.",
                "Local runtime authority remains separate from provider catalog visibility.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="deepseek-open-models",
            label="DeepSeek open model family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://api-docs.deepseek.com/",
            api_docs_link="https://api-docs.deepseek.com/",
            pricing_link="https://api-docs.deepseek.com/quick_start/pricing",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Open model local operation is not provider invocation authority.",
                "Hosted DeepSeek usage remains paid provider usage when applicable.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="gemma",
            label="Google Gemma local or hosted family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://ai.google.dev/gemma/docs",
            api_docs_link="https://ai.google.dev/gemma/docs",
            pricing_link="https://ai.google.dev/gemma/docs",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Local Gemma use depends on local runtime and hardware costs.",
                "Any hosted usage must route through a separately scoped provider channel.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="phi",
            label="Microsoft Phi local or hosted family",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://ai.azure.com/explore/models",
            api_docs_link="https://ai.azure.com/explore/models",
            pricing_link="https://azure.microsoft.com/en-us/pricing/details/azure-openai/",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Local Phi use depends on local runtime and hardware costs.",
                "Hosted Azure style usage has separate cloud billing and quota posture.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="gguf",
            label="GGUF local model files",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://huggingface.co/docs/hub/gguf",
            api_docs_link="https://huggingface.co/docs/hub/gguf",
            pricing_link="https://huggingface.co/pricing",
            env_var_styles=["UAA_LOCAL_MODEL_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "GGUF local operation shifts cost to storage hardware power and runtime maintenance.",
                "Model file provenance and local lifecycle authority remain separate gates.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="ollama",
            label="Ollama local runtime",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://ollama.com/download",
            api_docs_link="https://github.com/ollama/ollama/blob/main/docs/api.md",
            pricing_link="https://ollama.com/",
            env_var_styles=["OLLAMA_BASE_URL"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "Local runtime cost is hardware storage power and operator maintenance.",
                "Catalog visibility does not start Ollama or call a local model.",
            ],
            requires_api_key=False,
        ),
        _card(
            provider_slug="openwebui-compatible",
            label="OpenWebUI compatible local models",
            provider_class=ProviderCatalogProviderClass.local_or_open_model_family,
            setup_link="https://docs.openwebui.com/",
            api_docs_link="https://docs.openwebui.com/getting-started/api-endpoints/",
            pricing_link="https://docs.openwebui.com/",
            env_var_styles=["OPENWEBUI_CATALOG_REF"],
            billing_prerequisite=ProviderBillingPrerequisite.local_hardware_or_hosting_costs,
            token_cost_notes=[
                "OpenWebUI compatibility is local shell posture and not provider output authority.",
                "Any backing paid provider still needs exact cost and authority scope.",
            ],
            requires_api_key=False,
        ),
    ]


def _card(
    *,
    provider_slug: str,
    label: str,
    provider_class: ProviderCatalogProviderClass,
    setup_link: str,
    api_docs_link: str,
    pricing_link: str,
    env_var_styles: list[str],
    billing_prerequisite: ProviderBillingPrerequisite,
    token_cost_notes: list[str],
    requires_api_key: bool = True,
    extra_sources: list[tuple[ProviderSourceKind, str, str]] | None = None,
) -> ProviderSetupCard:
    provider_ref = f"provider-catalog:{provider_slug}"
    source_refs = [
        _source(provider_slug, ProviderSourceKind.setup, f"{label} setup", setup_link),
        _source(provider_slug, ProviderSourceKind.api_docs, f"{label} API docs", api_docs_link),
        _source(provider_slug, ProviderSourceKind.pricing, f"{label} pricing", pricing_link),
    ]
    for source_kind, source_label, url in extra_sources or []:
        source_refs.append(_source(provider_slug, source_kind, source_label, url))
    return ProviderSetupCard(
        provider_ref=provider_ref,
        provider_label=label,
        provider_class=provider_class,
        provider_manifest_ref=f"provider-manifest-ref:{provider_slug}:catalog-only",
        setup_link=setup_link,
        api_docs_link=api_docs_link,
        pricing_link=pricing_link,
        env_var_styles=env_var_styles,
        billing_prerequisite=billing_prerequisite,
        token_cost_notes=token_cost_notes,
        source_refs=source_refs,
        key_instruction=ProviderKeyInstruction(
            instruction_ref=f"provider-key-instruction:{provider_slug}",
            provider_ref=provider_ref,
            env_var_styles=env_var_styles,
            requires_api_key=requires_api_key,
            setup_source_ref=source_refs[0].source_ref,
            api_docs_source_ref=source_refs[1].source_ref,
            safe_summary=(
                "Use provider documentation to understand key setup. UAA stores no key value and performs no validation here."
            ),
        ),
        cost_profile=ProviderCostProfile(
            cost_profile_ref=f"provider-cost-profile:{provider_slug}",
            provider_ref=provider_ref,
            pricing_source_ref=source_refs[2].source_ref,
            billing_prerequisite=billing_prerequisite,
            cost_units=_cost_units(provider_class),
            token_cost_notes=token_cost_notes,
        ),
        authority_posture=ProviderAuthorityPosture(
            authority_ref=f"provider-authority:{provider_slug}",
        ),
    )


def _source(
    provider_slug: str,
    source_kind: ProviderSourceKind,
    label: str,
    url: str,
) -> ProviderSourceRef:
    return ProviderSourceRef(
        source_ref=f"provider-source:{provider_slug}:{source_kind.value}",
        source_kind=source_kind,
        label=label,
        url=url,
    )


def _cost_units(provider_class: ProviderCatalogProviderClass) -> list[ProviderCostUnit]:
    base_units = [
        ProviderCostUnit.input_tokens,
        ProviderCostUnit.output_tokens,
        ProviderCostUnit.rate_limit_or_quota,
    ]
    if provider_class == ProviderCatalogProviderClass.local_or_open_model_family:
        return [ProviderCostUnit.local_hardware, ProviderCostUnit.hardware_time, *base_units]
    if provider_class == ProviderCatalogProviderClass.router_or_platform:
        return [
            *base_units,
            ProviderCostUnit.request_or_tool_add_on,
            ProviderCostUnit.image_audio_video,
            ProviderCostUnit.hardware_time,
        ]
    if provider_class == ProviderCatalogProviderClass.cloud_or_enterprise_channel:
        return [
            *base_units,
            ProviderCostUnit.cached_input_tokens,
            ProviderCostUnit.context_cache,
            ProviderCostUnit.batch_job,
        ]
    return [
        *base_units,
        ProviderCostUnit.cached_input_tokens,
        ProviderCostUnit.reasoning_or_thinking_tokens,
        ProviderCostUnit.context_cache,
        ProviderCostUnit.batch_job,
        ProviderCostUnit.image_audio_video,
    ]


def _token_cost_examples() -> list[TokenCostExample]:
    return [
        TokenCostExample(
            example_ref="token-cost-example:quick-chat",
            label="Quick chat",
            workload_kind="quick_chat",
            safe_summary="A short chat usually spends on current input context and output tokens.",
            cost_driver_notes=[
                "Longer chat history can increase input token cost.",
                "Unknown paid cost still requires explicit approval before any future provider use.",
            ],
        ),
        TokenCostExample(
            example_ref="token-cost-example:crm-briefing",
            label="CRM briefing",
            workload_kind="crm_briefing",
            safe_summary="A briefing can spend on summarized records follow ups and generated output.",
            cost_driver_notes=[
                "CRM context must remain safe refs and reviewed local summaries.",
                "Provider generated recommendations are not product truth or authority.",
            ],
        ),
        TokenCostExample(
            example_ref="token-cost-example:long-document-review",
            label="Long document review",
            workload_kind="long_document_review",
            safe_summary="Large reviews can spend heavily on input tokens context windows and output detail.",
            cost_driver_notes=[
                "Chunking caching and batch pricing can change total cost.",
                "Document content must not become provider evidence without a separate scoped lane.",
            ],
        ),
        TokenCostExample(
            example_ref="token-cost-example:code-task",
            label="Code task",
            workload_kind="code_task",
            safe_summary="Code work can spend on repository summaries selected files reasoning tokens and patches.",
            cost_driver_notes=[
                "Tool execution and file mutation are separate authority lanes.",
                "Reasoning and long context models can materially change cost.",
            ],
        ),
        TokenCostExample(
            example_ref="token-cost-example:batch-analysis",
            label="Batch analysis",
            workload_kind="batch_analysis",
            safe_summary="Batch analysis can trade latency for provider specific batch pricing when scoped later.",
            cost_driver_notes=[
                "Batch jobs still need budget decisions receipt refs and provider refs.",
                "No batch provider work is enabled by this catalog.",
            ],
        ),
    ]


def _validate_ref(value: str, field_name: str) -> str:
    if not SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"PROVIDER_CATALOG_UNSAFE_{field_name.upper()}_REF")
    return value


def _validate_doc_or_script_ref(value: str) -> str:
    if not (
        value.startswith("docs/")
        and value.endswith(".md")
        or value.startswith("scripts/")
        and value.endswith(".py")
    ):
        raise ValueError("PROVIDER_CATALOG_DOC_OR_SCRIPT_REF_REQUIRED")
    if LOCAL_PATH_RE.search(value):
        raise ValueError("PROVIDER_CATALOG_LOCAL_PATH_REF_DENIED")
    return value


def _validate_safe_text(value: str, field_name: str, *, max_chars: int = 900) -> str:
    if len(value) > max_chars or not SAFE_TEXT_RE.fullmatch(value):
        raise ValueError(f"PROVIDER_CATALOG_UNSAFE_{field_name.upper()}_TEXT")
    if _contains_unsafe_text(value):
        raise ValueError(f"PROVIDER_CATALOG_FORBIDDEN_{field_name.upper()}_TEXT")
    return value


def _validate_env_var_style(value: str) -> str:
    if not ENV_VAR_RE.fullmatch(value):
        raise ValueError("PROVIDER_CATALOG_ENV_VAR_STYLE_INVALID")
    return value


def _validate_https_source_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"PROVIDER_CATALOG_{field_name.upper()}_HTTPS_URL_REQUIRED")
    if parsed.username or parsed.password:
        raise ValueError(f"PROVIDER_CATALOG_{field_name.upper()}_URL_CREDENTIALS_DENIED")
    if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        raise ValueError(f"PROVIDER_CATALOG_{field_name.upper()}_LOCALHOST_DENIED")
    return value


def _deny_true_flags(model: BaseModel, fields: list[tuple[str, str]]) -> None:
    for field_name, error_code in fields:
        if getattr(model, field_name):
            raise ValueError(error_code)


def _reject_unsafe_payload(payload: Any, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload) or _contains_unsafe_payload_text(payload):
        raise ValueError(error_code)


def _contains_unsafe_payload_text(payload: Any) -> bool:
    if isinstance(payload, str):
        return _contains_unsafe_text(payload)
    if isinstance(payload, dict):
        return any(_contains_unsafe_payload_text(value) for value in payload.values())
    if isinstance(payload, list | tuple | set):
        return any(_contains_unsafe_payload_text(value) for value in payload)
    return False


def _contains_unsafe_text(value: str) -> bool:
    if LOCAL_PATH_RE.search(value):
        return True
    return any(pattern.search(value) for pattern in UNSAFE_COPY_PATTERNS)
