from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_PROMPT_STABILITY_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-prompt-stability-tiers:v1"
)
RUNTIME_PROMPT_STABILITY_ROUTE_REF = "GET /api/runtime/prompt-stability-tiers"
RUNTIME_PROMPT_STABILITY_CLI_REF = "uaa runtime inspect-prompt-stability-tiers"
RUNTIME_PROMPT_STABILITY_SNAPSHOT_REF = (
    "prompt-stability-snapshot-ref:runtime:tier-contracts"
)
RUNTIME_PROMPT_STABILITY_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-23:prompt-stability-tiers"
)

RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:prompt-stability-no-hidden-prompt-injection",
    "blocked-authority:prompt-stability-no-raw-prompt-persistence",
    "blocked-authority:prompt-stability-no-raw-response-persistence",
    "blocked-authority:prompt-stability-no-provider-payload-persistence",
    "blocked-authority:prompt-stability-no-model-output-authority",
    "blocked-authority:prompt-stability-no-model-call",
    "blocked-authority:prompt-stability-no-context-injection",
    "blocked-authority:prompt-stability-no-provider-sdk-call",
    "blocked-authority:prompt-stability-no-cache-write",
    "blocked-authority:prompt-stability-no-production-authority",
]


class RuntimePromptStabilityTierKind(str, Enum):
    stable_identity_policy = "stable_identity_policy"
    durable_context_refs = "durable_context_refs"
    retrieval_refs = "retrieval_refs"
    volatile_runtime_state = "volatile_runtime_state"
    operator_turn_ref = "operator_turn_ref"


class RuntimePromptStabilityClass(str, Enum):
    stable_cache_candidate = "stable_cache_candidate"
    semi_stable_ref_set = "semi_stable_ref_set"
    volatile_no_cache = "volatile_no_cache"
    operator_scoped_no_cache = "operator_scoped_no_cache"


class RuntimePromptStabilityTier(BaseModel):
    tier_ref: str
    display_label: str
    tier_kind: RuntimePromptStabilityTierKind
    stability_class: RuntimePromptStabilityClass
    manifest_ref: str
    tier_hash_ref: str
    cache_policy_ref: str
    proof_ref: str = RUNTIME_PROMPT_STABILITY_PROOF_REF
    safe_summary: str
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    cache_candidate: bool = False
    cache_write_enabled: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    hidden_prompt_injection_enabled: bool = False
    context_injection_enabled: bool = False
    model_call_performed: bool = False
    provider_sdk_call_performed: bool = False
    model_output_authoritative: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_tier(self) -> "RuntimePromptStabilityTier":
        for value, field_name in [
            (self.tier_ref, "tier_ref"),
            (self.manifest_ref, "manifest_ref"),
            (self.tier_hash_ref, "tier_hash_ref"),
            (self.cache_policy_ref, "cache_policy_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("source_refs", "evidence_refs", "blocked_authority_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.tier_kind), "tier_kind"),
            (str(self.stability_class), "stability_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "cache_write_enabled": self.cache_write_enabled,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "hidden_prompt_injection_enabled": self.hidden_prompt_injection_enabled,
            "context_injection_enabled": self.context_injection_enabled,
            "model_call_performed": self.model_call_performed,
            "provider_sdk_call_performed": self.provider_sdk_call_performed,
            "model_output_authoritative": self.model_output_authoritative,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PROMPT_STABILITY_TIER_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if self.cache_candidate and self.stability_class in {
            RuntimePromptStabilityClass.volatile_no_cache.value,
            RuntimePromptStabilityClass.operator_scoped_no_cache.value,
        }:
            raise ValueError("RUNTIME_PROMPT_STABILITY_CACHE_CLASS_DENIED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_PROMPT_STABILITY_TIER_BLOCKERS_REQUIRED")
        return self


class RuntimePromptStabilityTiersReadModel(BaseModel):
    schema_version: str = "runtime_prompt_stability_tiers.v1"
    contract_ref: str = RUNTIME_PROMPT_STABILITY_CONTRACT_REF
    status: str = "read_only_prompt_contract_posture"
    snapshot_ref: str = RUNTIME_PROMPT_STABILITY_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-prompt-stability:pending"
    route_ref: str = RUNTIME_PROMPT_STABILITY_ROUTE_REF
    cli_ref: str = RUNTIME_PROMPT_STABILITY_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Prompt stability tiers separate durable policy, context refs, retrieval "
        "refs, volatile state, and operator turn refs without storing raw prompts."
    )
    tiers: list[RuntimePromptStabilityTier]
    tier_count: int = 0
    stable_cache_candidate_count: int = 0
    semi_stable_ref_set_count: int = 0
    volatile_no_cache_count: int = 0
    operator_scoped_no_cache_count: int = 0
    safe_prompt_manifest_required: bool = True
    prompt_hashes_required: bool = True
    redacted_receipt_required: bool = True
    proof_link_required: bool = True
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    provider_payload_persistence_enabled: bool = False
    hidden_prompt_injection_enabled: bool = False
    context_injection_enabled: bool = False
    model_call_enabled: bool = False
    provider_sdk_enabled: bool = False
    model_output_authority_enabled: bool = False
    cache_write_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_prompts_omitted",
                "raw_responses_omitted",
                "provider_payloads_omitted",
                "prompt_material_omitted",
                "operator_turn_text_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimePromptStabilityTiersReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.tier_count != len(self.tiers):
            raise ValueError("RUNTIME_PROMPT_STABILITY_TIER_COUNT_MISMATCH")
        class_counts = {
            RuntimePromptStabilityClass.stable_cache_candidate.value: (
                self.stable_cache_candidate_count
            ),
            RuntimePromptStabilityClass.semi_stable_ref_set.value: (
                self.semi_stable_ref_set_count
            ),
            RuntimePromptStabilityClass.volatile_no_cache.value: (
                self.volatile_no_cache_count
            ),
            RuntimePromptStabilityClass.operator_scoped_no_cache.value: (
                self.operator_scoped_no_cache_count
            ),
        }
        for stability_class, expected_count in class_counts.items():
            actual = len(
                [tier for tier in self.tiers if tier.stability_class == stability_class]
            )
            if expected_count != actual:
                raise ValueError("RUNTIME_PROMPT_STABILITY_CLASS_COUNT_MISMATCH")
        for required, name in [
            (self.safe_prompt_manifest_required, "safe_prompt_manifest_required"),
            (self.prompt_hashes_required, "prompt_hashes_required"),
            (self.redacted_receipt_required, "redacted_receipt_required"),
            (self.proof_link_required, "proof_link_required"),
        ]:
            if required is not True:
                raise ValueError(f"RUNTIME_PROMPT_STABILITY_{name.upper()}_DENIED")
        denied_flags = {
            "raw_prompt_persistence_enabled": self.raw_prompt_persistence_enabled,
            "raw_response_persistence_enabled": self.raw_response_persistence_enabled,
            "provider_payload_persistence_enabled": (
                self.provider_payload_persistence_enabled
            ),
            "hidden_prompt_injection_enabled": self.hidden_prompt_injection_enabled,
            "context_injection_enabled": self.context_injection_enabled,
            "model_call_enabled": self.model_call_enabled,
            "provider_sdk_enabled": self.provider_sdk_enabled,
            "model_output_authority_enabled": self.model_output_authority_enabled,
            "cache_write_enabled": self.cache_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PROMPT_STABILITY_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if RUNTIME_PROMPT_STABILITY_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_PROMPT_STABILITY_PROOF_REQUIRED")
        if set(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_PROMPT_STABILITY_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-prompt-stability:{digest}"


def _tier(
    *,
    slug: str,
    display_label: str,
    tier_kind: RuntimePromptStabilityTierKind,
    stability_class: RuntimePromptStabilityClass,
    safe_summary: str,
    source_refs: list[str],
    cache_candidate: bool,
) -> RuntimePromptStabilityTier:
    return RuntimePromptStabilityTier(
        tier_ref=f"prompt-stability-tier-ref:{slug}",
        display_label=display_label,
        tier_kind=tier_kind,
        stability_class=stability_class,
        manifest_ref=f"prompt-manifest-ref:runtime:{slug}",
        tier_hash_ref=f"prompt-tier-hash-ref:runtime:{slug}:redacted",
        cache_policy_ref=f"cache-policy-ref:prompt-stability:{slug}",
        safe_summary=safe_summary,
        source_refs=source_refs,
        evidence_refs=[f"evidence-ref:prompt-stability:{slug}"],
        blocked_authority_refs=list(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS),
        cache_candidate=cache_candidate,
    )


def _default_tiers() -> list[RuntimePromptStabilityTier]:
    return [
        _tier(
            slug="stable-identity-policy",
            display_label="Stable identity and policy",
            tier_kind=RuntimePromptStabilityTierKind.stable_identity_policy,
            stability_class=RuntimePromptStabilityClass.stable_cache_candidate,
            safe_summary=(
                "Stable identity and policy refs may be hash-addressed for future "
                "cache proof, but no prompt text is stored."
            ),
            source_refs=[
                "policy-ref:uaa:non-negotiable-invariants",
                "authority-profile-ref:runtime:sealed-default",
            ],
            cache_candidate=True,
        ),
        _tier(
            slug="durable-context-refs",
            display_label="Durable context refs",
            tier_kind=RuntimePromptStabilityTierKind.durable_context_refs,
            stability_class=RuntimePromptStabilityClass.semi_stable_ref_set,
            safe_summary=(
                "Context tier stores refs and why-included posture only; it does "
                "not inject context or persist raw source material."
            ),
            source_refs=[
                "context-pack-ref:prepared-turn:review-required",
                "proof-ref:runtime-context-references:phase-16",
            ],
            cache_candidate=True,
        ),
        _tier(
            slug="retrieval-refs",
            display_label="Retrieval refs",
            tier_kind=RuntimePromptStabilityTierKind.retrieval_refs,
            stability_class=RuntimePromptStabilityClass.semi_stable_ref_set,
            safe_summary=(
                "Retrieval tier is safe-ref posture only and grants no hidden "
                "retrieval, semantic provider call, or vector index authority."
            ),
            source_refs=[
                "search-ref:runtime-session-search:sample",
                "memory-ref:reviewed:operator-context",
            ],
            cache_candidate=True,
        ),
        _tier(
            slug="volatile-runtime-state",
            display_label="Volatile runtime state",
            tier_kind=RuntimePromptStabilityTierKind.volatile_runtime_state,
            stability_class=RuntimePromptStabilityClass.volatile_no_cache,
            safe_summary=(
                "Runtime state tier is volatile and no-cache; event previews stay "
                "bounded, stale, and redacted."
            ),
            source_refs=[
                "run-state-ref:runtime:approval-wait",
                "event-preview-ref:runtime-streaming-progress:stale",
            ],
            cache_candidate=False,
        ),
        _tier(
            slug="operator-turn-ref",
            display_label="Operator turn ref",
            tier_kind=RuntimePromptStabilityTierKind.operator_turn_ref,
            stability_class=RuntimePromptStabilityClass.operator_scoped_no_cache,
            safe_summary=(
                "Operator turn tier stores a safe turn ref and fingerprint only; "
                "raw operator text remains omitted."
            ),
            source_refs=[
                "turn-ref:prepared-turn:ephemeral",
                "content-fingerprint-ref:prepared-turn-content:required",
            ],
            cache_candidate=False,
        ),
    ]


def build_runtime_prompt_stability_tiers_read_model() -> (
    RuntimePromptStabilityTiersReadModel
):
    tiers = _default_tiers()
    model = RuntimePromptStabilityTiersReadModel(
        tiers=tiers,
        tier_count=len(tiers),
        stable_cache_candidate_count=len(
            [
                tier
                for tier in tiers
                if tier.stability_class
                == RuntimePromptStabilityClass.stable_cache_candidate.value
            ]
        ),
        semi_stable_ref_set_count=len(
            [
                tier
                for tier in tiers
                if tier.stability_class
                == RuntimePromptStabilityClass.semi_stable_ref_set.value
            ]
        ),
        volatile_no_cache_count=len(
            [
                tier
                for tier in tiers
                if tier.stability_class
                == RuntimePromptStabilityClass.volatile_no_cache.value
            ]
        ),
        operator_scoped_no_cache_count=len(
            [
                tier
                for tier in tiers
                if tier.stability_class
                == RuntimePromptStabilityClass.operator_scoped_no_cache.value
            ]
        ),
        blocked_authority_refs=list(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_PROMPT_STABILITY_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-23"],
        next_safe_action_refs=[
            "next-safe-action-ref:prompt-stability:add-safe-prompt-manifest",
            "next-safe-action-ref:prompt-stability:add-redacted-receipt",
            "next-safe-action-ref:prompt-stability:keep-raw-prompts-blocked",
        ],
    )
    model.snapshot_hash_ref = _hash_payload(
        [
            {
                "tier_ref": tier.tier_ref,
                "tier_kind": tier.tier_kind,
                "stability_class": tier.stability_class,
                "manifest_ref": tier.manifest_ref,
                "tier_hash_ref": tier.tier_hash_ref,
                "cache_policy_ref": tier.cache_policy_ref,
                "cache_candidate": tier.cache_candidate,
            }
            for tier in tiers
        ]
    )
    return RuntimePromptStabilityTiersReadModel(**model.model_dump(mode="json"))
