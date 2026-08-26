from __future__ import annotations

import hashlib
import re
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.crm.contracts import (
    _deny_true_flags,
    _validate_optional_ref_list,
    _validate_ref,
    _validate_ref_list,
    _validate_safe_text,
)


CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF = (
    "contract-ref:crm-social-relationship-projection:v1"
)
CRM_SOCIAL_RELATIONSHIP_PROJECTION_REF = (
    "projection-ref:crm-social-relationship-context:v1"
)
CRM_SOCIAL_RELATIONSHIP_OWNER_REF = "owner-ref:crm"
CRM_SOCIAL_RELATIONSHIP_SELECTION_RULE_REF = (
    "selection-rule-ref:crm-social:person-tag-social-context"
)
CRM_SOCIAL_RELATIONSHIP_SOURCE_POSTURE_REF = (
    "source-posture-ref:crm-social:reviewed-local"
)
CRM_SOCIAL_RELATIONSHIP_FRESHNESS_REF = (
    "freshness-ref:crm-social:derived-from-crm-snapshot"
)
CRM_SOCIAL_RELATIONSHIP_TAG = "social-context"
CRM_SOCIAL_RELATIONSHIP_CLI_REF = (
    "repo-local-command:uaa-crm:inspect-social-relationships"
)
CRM_SOCIAL_RELATIONSHIP_API_REF = "GET /control-center/crm/relationships"
CRM_SOCIAL_RELATIONSHIP_PAGE_LIMIT = 50
CRM_SOCIAL_RELATIONSHIP_REF_PAGE_LIMIT = 20

_UNSAFE_SUFFIX = re.compile(r"[^a-z0-9_.:-]+")


class _CrmSocialModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CrmSocialRelationshipProjectionItem(_CrmSocialModel):
    projection_item_ref: str
    relationship_ref: str
    person_ref: str
    organization_ref: str | None = None
    crm_deep_link_ref: str
    safe_display_label: str
    safe_summary: str
    why_shown: str
    health_state: str
    freshness_state: str
    evidence_refs: list[str] = Field(default_factory=list, max_length=20)
    memory_provenance_refs: list[str] = Field(default_factory=list, max_length=20)
    evidence_ref_total_count: int = Field(default=0, ge=0)
    evidence_refs_truncated: bool = False
    memory_provenance_ref_total_count: int = Field(default=0, ge=0)
    memory_provenance_refs_truncated: bool = False
    backend_owned: bool = True
    read_only: bool = True
    raw_content_included: bool = False
    connector_runtime_enabled: bool = False
    external_action_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmSocialRelationshipProjectionItem":
        for field_name in (
            "projection_item_ref",
            "relationship_ref",
            "person_ref",
            "crm_deep_link_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.organization_ref is not None:
            _validate_ref(self.organization_ref, "organization_ref")
        _validate_optional_ref_list(self.evidence_refs, "evidence_refs")
        _validate_optional_ref_list(
            self.memory_provenance_refs,
            "memory_provenance_refs",
        )
        if self.evidence_ref_total_count < len(self.evidence_refs):
            raise ValueError("CRM_SOCIAL_EVIDENCE_REF_TOTAL_COUNT_INVALID")
        if self.evidence_refs_truncated != (
            self.evidence_ref_total_count > len(self.evidence_refs)
        ):
            raise ValueError("CRM_SOCIAL_EVIDENCE_REF_TRUNCATION_DRIFT")
        if self.memory_provenance_ref_total_count < len(self.memory_provenance_refs):
            raise ValueError("CRM_SOCIAL_MEMORY_REF_TOTAL_COUNT_INVALID")
        if self.memory_provenance_refs_truncated != (
            self.memory_provenance_ref_total_count > len(self.memory_provenance_refs)
        ):
            raise ValueError("CRM_SOCIAL_MEMORY_REF_TRUNCATION_DRIFT")
        for field_name in (
            "safe_display_label",
            "safe_summary",
            "why_shown",
            "health_state",
            "freshness_state",
        ):
            _validate_safe_text(getattr(self, field_name), field_name)
        if not self.backend_owned or not self.read_only:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_OWNER_POSTURE_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("raw_content_included", "CRM_SOCIAL_RAW_CONTENT_DENIED"),
                (
                    "connector_runtime_enabled",
                    "CRM_SOCIAL_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    "external_action_enabled",
                    "CRM_SOCIAL_EXTERNAL_ACTION_DENIED",
                ),
            ],
        )
        return self


class CrmSocialRelationshipProjection(_CrmSocialModel):
    contract_ref: str = CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF
    projection_ref: str = CRM_SOCIAL_RELATIONSHIP_PROJECTION_REF
    owner_ref: str = CRM_SOCIAL_RELATIONSHIP_OWNER_REF
    selection_rule_ref: str = CRM_SOCIAL_RELATIONSHIP_SELECTION_RULE_REF
    source_posture_ref: str = CRM_SOCIAL_RELATIONSHIP_SOURCE_POSTURE_REF
    freshness_ref: str = CRM_SOCIAL_RELATIONSHIP_FRESHNESS_REF
    api_ref: str = CRM_SOCIAL_RELATIONSHIP_API_REF
    cli_ref: str = CRM_SOCIAL_RELATIONSHIP_CLI_REF
    items: list[CrmSocialRelationshipProjectionItem] = Field(
        default_factory=list,
        max_length=CRM_SOCIAL_RELATIONSHIP_PAGE_LIMIT,
    )
    total_item_count: int = Field(default=0, ge=0)
    returned_item_count: int = Field(default=0, ge=0)
    truncated: bool = False
    evidence_refs: list[str] = Field(
        default_factory=lambda: [
            "evidence-ref:social-foundation:crm-relationship-projection"
        ],
        max_length=20,
    )
    backend_owned: bool = True
    read_only: bool = True
    stable_deep_links: bool = True
    copies_relationship_truth: bool = False
    live_source_access_enabled: bool = False
    connector_runtime_enabled: bool = False
    provider_model_call_enabled: bool = False
    publishing_enabled: bool = False
    external_write_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmSocialRelationshipProjection":
        for field_name in (
            "contract_ref",
            "projection_ref",
            "owner_ref",
            "selection_rule_ref",
            "source_posture_ref",
            "freshness_ref",
            "cli_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        expected_metadata = {
            "contract_ref": CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF,
            "projection_ref": CRM_SOCIAL_RELATIONSHIP_PROJECTION_REF,
            "owner_ref": CRM_SOCIAL_RELATIONSHIP_OWNER_REF,
            "selection_rule_ref": CRM_SOCIAL_RELATIONSHIP_SELECTION_RULE_REF,
            "source_posture_ref": CRM_SOCIAL_RELATIONSHIP_SOURCE_POSTURE_REF,
            "freshness_ref": CRM_SOCIAL_RELATIONSHIP_FRESHNESS_REF,
            "cli_ref": CRM_SOCIAL_RELATIONSHIP_CLI_REF,
        }
        if any(
            getattr(self, field_name) != expected
            for field_name, expected in expected_metadata.items()
        ):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_OWNERSHIP_METADATA_DRIFT")
        if self.api_ref != CRM_SOCIAL_RELATIONSHIP_API_REF:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_API_REF_DRIFT")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if not self.backend_owned or not self.read_only or not self.stable_deep_links:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_SAFE_POSTURE_REQUIRED")
        _deny_true_flags(
            self,
            [
                (
                    "copies_relationship_truth",
                    "CRM_SOCIAL_RELATIONSHIP_COPY_DENIED",
                ),
                ("live_source_access_enabled", "CRM_SOCIAL_LIVE_SOURCE_DENIED"),
                (
                    "connector_runtime_enabled",
                    "CRM_SOCIAL_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    "provider_model_call_enabled",
                    "CRM_SOCIAL_PROVIDER_MODEL_DENIED",
                ),
                ("publishing_enabled", "CRM_SOCIAL_PUBLISHING_DENIED"),
                ("external_write_enabled", "CRM_SOCIAL_EXTERNAL_WRITE_DENIED"),
                (
                    "production_authority_enabled",
                    "CRM_SOCIAL_PRODUCTION_AUTHORITY_DENIED",
                ),
            ],
        )
        if len({item.relationship_ref for item in self.items}) != len(self.items):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_DUPLICATE_ITEM")
        if len({item.crm_deep_link_ref for item in self.items}) != len(self.items):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_DUPLICATE_DEEP_LINK")
        if self.returned_item_count != len(self.items):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_RETURNED_COUNT_DRIFT")
        if self.total_item_count < self.returned_item_count:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_TOTAL_COUNT_INVALID")
        if self.truncated != (self.total_item_count > self.returned_item_count):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_TRUNCATION_POSTURE_DRIFT")
        return self

    def validate_owner_links(
        self,
        *,
        people: Sequence[Any],
        organizations: Sequence[Any],
        relationships: Sequence[Any],
    ) -> None:
        person_by_ref = _unique_by_ref(
            people,
            "person_ref",
            "CRM_SOCIAL_PERSON_REF_DUPLICATE",
        )
        organization_by_ref = _unique_by_ref(
            organizations,
            "organization_ref",
            "CRM_SOCIAL_ORGANIZATION_REF_DUPLICATE",
        )
        relationship_by_ref = _unique_by_ref(
            relationships,
            "relationship_ref",
            "CRM_SOCIAL_RELATIONSHIP_REF_DUPLICATE",
        )
        expected_relationship_refs = _selected_relationship_refs(
            people=people,
            relationship_by_ref=relationship_by_ref,
        )
        expected_returned_refs = expected_relationship_refs[
            :CRM_SOCIAL_RELATIONSHIP_PAGE_LIMIT
        ]
        if [item.relationship_ref for item in self.items] != expected_returned_refs:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_INVENTORY_DRIFT")
        if self.total_item_count != len(expected_relationship_refs):
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_TOTAL_COUNT_DRIFT")
        for item in self.items:
            relationship = relationship_by_ref.get(item.relationship_ref)
            if relationship is None:
                raise ValueError("CRM_SOCIAL_RELATIONSHIP_LINK_MISSING")
            if _value(relationship, "person_ref") != item.person_ref:
                raise ValueError("CRM_SOCIAL_PERSON_LINK_MISMATCH")
            if _value(relationship, "organization_ref") != item.organization_ref:
                raise ValueError("CRM_SOCIAL_ORGANIZATION_LINK_MISMATCH")
            if item.person_ref not in person_by_ref:
                raise ValueError("CRM_SOCIAL_PERSON_LINK_MISSING")
            if (
                item.organization_ref is not None
                and item.organization_ref not in organization_by_ref
            ):
                raise ValueError("CRM_SOCIAL_ORGANIZATION_LINK_MISSING")
            expected_item = _projection_item_from_relationship(relationship)
            if item.model_dump(mode="json") != expected_item.model_dump(mode="json"):
                raise ValueError("CRM_SOCIAL_RELATIONSHIP_ITEM_TRUTH_DRIFT")


def build_crm_social_relationship_projection(
    *,
    people: Sequence[Any],
    organizations: Sequence[Any],
    relationships: Sequence[Any],
) -> CrmSocialRelationshipProjection:
    person_by_ref = _unique_by_ref(
        people,
        "person_ref",
        "CRM_SOCIAL_PERSON_REF_DUPLICATE",
    )
    _unique_by_ref(
        organizations,
        "organization_ref",
        "CRM_SOCIAL_ORGANIZATION_REF_DUPLICATE",
    )
    relationship_by_ref = _unique_by_ref(
        relationships,
        "relationship_ref",
        "CRM_SOCIAL_RELATIONSHIP_REF_DUPLICATE",
    )
    selected_relationship_refs = _selected_relationship_refs(
        people=people,
        relationship_by_ref=relationship_by_ref,
    )

    items: list[CrmSocialRelationshipProjectionItem] = []
    for relationship_ref in selected_relationship_refs[
        :CRM_SOCIAL_RELATIONSHIP_PAGE_LIMIT
    ]:
        relationship = relationship_by_ref.get(relationship_ref)
        if relationship is None:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_SELECTION_LINK_MISSING")
        person_ref = str(_value(relationship, "person_ref"))
        if person_ref not in person_by_ref:
            raise ValueError("CRM_SOCIAL_RELATIONSHIP_PERSON_MISSING")
        items.append(_projection_item_from_relationship(relationship))
    projection = CrmSocialRelationshipProjection(
        items=items,
        total_item_count=len(selected_relationship_refs),
        returned_item_count=len(items),
        truncated=len(selected_relationship_refs) > len(items),
    )
    projection.validate_owner_links(
        people=people,
        organizations=organizations,
        relationships=relationships,
    )
    return projection


def _value(item: Any, field_name: str) -> Any:
    if isinstance(item, dict):
        return item.get(field_name)
    return getattr(item, field_name)


def _unique_by_ref(
    items: Sequence[Any],
    field_name: str,
    duplicate_error: str,
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for item in items:
        item_ref = _value(item, field_name)
        if item_ref in result:
            raise ValueError(duplicate_error)
        result[item_ref] = item
    return result


def _selected_relationship_refs(
    *,
    people: Sequence[Any],
    relationship_by_ref: dict[Any, Any],
) -> list[str]:
    selected_relationship_refs: set[str] = set()
    for person in people:
        if CRM_SOCIAL_RELATIONSHIP_TAG not in set(_value(person, "tags") or []):
            continue
        person_ref = str(_value(person, "person_ref"))
        for relationship_ref in _value(person, "relationship_refs") or []:
            relationship = relationship_by_ref.get(relationship_ref)
            if relationship is None:
                raise ValueError("CRM_SOCIAL_RELATIONSHIP_SELECTION_LINK_MISSING")
            if _value(relationship, "person_ref") != person_ref:
                raise ValueError("CRM_SOCIAL_RELATIONSHIP_SELECTOR_OWNER_MISMATCH")
            selected_relationship_refs.add(str(relationship_ref))
    return sorted(selected_relationship_refs)


def _projection_item_from_relationship(
    relationship: Any,
) -> CrmSocialRelationshipProjectionItem:
    relationship_ref = str(_value(relationship, "relationship_ref"))
    evidence_refs = list(_value(relationship, "evidence_refs") or [])
    memory_provenance_refs = list(_value(relationship, "memory_provenance_refs") or [])
    suffix = _ref_suffix(relationship_ref)
    return CrmSocialRelationshipProjectionItem(
        projection_item_ref=f"projection-item-ref:crm-social:{suffix}",
        relationship_ref=relationship_ref,
        person_ref=str(_value(relationship, "person_ref")),
        organization_ref=_value(relationship, "organization_ref"),
        crm_deep_link_ref=f"control-center-deep-link-ref:crm:{suffix}",
        safe_display_label=str(_value(relationship, "safe_display_label")),
        safe_summary=str(_value(relationship, "safe_summary")),
        why_shown=(
            "Shown because CRM owns a reviewed relationship tagged for "
            "the Social relationship context projection."
        ),
        health_state=str(_value(relationship, "health_state")),
        freshness_state=str(_value(relationship, "stale_state")),
        evidence_refs=evidence_refs[:CRM_SOCIAL_RELATIONSHIP_REF_PAGE_LIMIT],
        evidence_ref_total_count=len(evidence_refs),
        evidence_refs_truncated=(
            len(evidence_refs) > CRM_SOCIAL_RELATIONSHIP_REF_PAGE_LIMIT
        ),
        memory_provenance_refs=memory_provenance_refs[
            :CRM_SOCIAL_RELATIONSHIP_REF_PAGE_LIMIT
        ],
        memory_provenance_ref_total_count=len(memory_provenance_refs),
        memory_provenance_refs_truncated=(
            len(memory_provenance_refs) > CRM_SOCIAL_RELATIONSHIP_REF_PAGE_LIMIT
        ),
    )


def _ref_suffix(value: str) -> str:
    normalized = _UNSAFE_SUFFIX.sub("-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("CRM_SOCIAL_RELATIONSHIP_REF_SUFFIX_INVALID")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{normalized[:80]}-{digest}"
