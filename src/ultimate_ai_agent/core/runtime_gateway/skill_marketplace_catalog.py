from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


class RuntimeSkillSourceKind(str, Enum):
    clawhub = "clawhub"
    hermes = "hermes"


class RuntimeSkillSourceRankSignal(str, Enum):
    weekly_trending = "weekly_trending"
    not_provided = "not_provided"


class RuntimeSkillSourceScoreSignal(str, Enum):
    stars = "stars"
    not_provided = "not_provided"


class RuntimeSkillMarketplaceSourceSnapshot(BaseModel):
    source_ref: str
    source_kind: RuntimeSkillSourceKind
    display_label: str
    captured_at: str
    source_version_ref: str
    record_count: int = Field(ge=0)
    rank_signal: RuntimeSkillSourceRankSignal
    score_signal: RuntimeSkillSourceScoreSignal
    live_fetch_performed: Literal[False] = False
    raw_payload_persisted: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_source(self) -> "RuntimeSkillMarketplaceSourceSnapshot":
        for value, field_name in (
            (self.source_ref, "source_ref"),
            (self.source_version_ref, "source_version_ref"),
        ):
            validate_execution_ref(value, field_name)
        for value, field_name in (
            (str(self.source_kind), "source_kind"),
            (self.display_label, "display_label"),
            (self.captured_at, "captured_at"),
            (str(self.rank_signal), "rank_signal"),
            (str(self.score_signal), "score_signal"),
        ):
            validate_safe_execution_text(value, field_name)
        expected_signals = {
            RuntimeSkillSourceKind.clawhub: (
                RuntimeSkillSourceRankSignal.weekly_trending,
                RuntimeSkillSourceScoreSignal.stars,
            ),
            RuntimeSkillSourceKind.hermes: (
                RuntimeSkillSourceRankSignal.not_provided,
                RuntimeSkillSourceScoreSignal.not_provided,
            ),
        }
        if (self.rank_signal, self.score_signal) != expected_signals[
            self.source_kind
        ]:
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SOURCE_SIGNAL_MISMATCH")
        return self


class RuntimeSkillMarketplaceCatalogEntry(BaseModel):
    skill_ref: str
    source_ref: str
    source_record_ref: str
    source_kind: RuntimeSkillSourceKind
    source_label: str
    slug: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=120)
    safe_summary: str = Field(min_length=1, max_length=320)
    category: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=40)
    license_label: str = Field(min_length=1, max_length=120)
    source_updated_at: str
    source_rank: int | None = Field(default=None, ge=1)
    rank_label: str
    star_count: int | None = Field(default=None, ge=0)
    download_count: int | None = Field(default=None, ge=0)
    install_count: int | None = Field(default=None, ge=0)
    comment_count: int | None = Field(default=None, ge=0)
    average_rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int | None = Field(default=None, ge=0)
    source_metadata_only: Literal[True] = True
    review_required: Literal[True] = True
    risk_level: Literal["unknown"] = "unknown"
    external_code_imported: Literal[False] = False
    execution_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "RuntimeSkillMarketplaceCatalogEntry":
        for value, field_name in (
            (self.skill_ref, "skill_ref"),
            (self.source_ref, "source_ref"),
            (self.source_record_ref, "source_record_ref"),
        ):
            validate_execution_ref(value, field_name)
        for value, field_name in (
            (str(self.source_kind), "source_kind"),
            (self.source_label, "source_label"),
            (self.slug, "slug"),
            (self.display_name, "display_name"),
            (self.safe_summary, "safe_summary"),
            (self.category, "category"),
            (self.version, "version"),
            (self.license_label, "license_label"),
            (self.source_updated_at, "source_updated_at"),
            (self.rank_label, "rank_label"),
        ):
            validate_safe_execution_text(value, field_name)
        if (self.average_rating is None) != (self.rating_count is None):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_RATING_PAIR_REQUIRED")
        if self.source_kind == RuntimeSkillSourceKind.hermes:
            unavailable_signals = (
                self.source_rank,
                self.star_count,
                self.download_count,
                self.install_count,
                self.comment_count,
                self.average_rating,
                self.rating_count,
            )
            if any(value is not None for value in unavailable_signals):
                raise ValueError(
                    "RUNTIME_SKILL_MARKETPLACE_HERMES_SIGNAL_NOT_PROVIDED"
                )
        if self.source_kind == RuntimeSkillSourceKind.clawhub and (
            self.average_rating is not None or self.rating_count is not None
        ):
            raise ValueError(
                "RUNTIME_SKILL_MARKETPLACE_CLAWHUB_RATING_NOT_DOCUMENTED"
            )
        return self


class RuntimeSkillMarketplaceCatalogSnapshot(BaseModel):
    schema_version: Literal["runtime_skill_marketplace_catalog_snapshot.v1"] = (
        "runtime_skill_marketplace_catalog_snapshot.v1"
    )
    snapshot_ref: str
    captured_at: str
    sources: list[RuntimeSkillMarketplaceSourceSnapshot] = Field(
        default_factory=list
    )
    entries: list[RuntimeSkillMarketplaceCatalogEntry] = Field(
        default_factory=list
    )
    entry_count: int = Field(ge=0)
    default_page_size: Literal[25] = 25
    pagination_supported: Literal[True] = True
    metadata_only: Literal[True] = True
    live_marketplace_fetch_performed: Literal[False] = False
    raw_marketplace_payload_persisted: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_snapshot(self) -> "RuntimeSkillMarketplaceCatalogSnapshot":
        validate_execution_ref(self.snapshot_ref, "snapshot_ref")
        validate_safe_execution_text(self.captured_at, "captured_at")
        if self.entry_count != len(self.entries):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_CATALOG_COUNT_MISMATCH")
        source_refs = {source.source_ref for source in self.sources}
        if len(source_refs) != len(self.sources):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SOURCE_REFS_NOT_UNIQUE")
        source_kinds = {source.source_kind for source in self.sources}
        if source_kinds != {
            RuntimeSkillSourceKind.clawhub,
            RuntimeSkillSourceKind.hermes,
        } or len(source_kinds) != len(self.sources):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SOURCE_KINDS_INVALID")
        if any(entry.source_ref not in source_refs for entry in self.entries):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SOURCE_REF_UNKNOWN")
        source_kind_by_ref = {
            source.source_ref: source.source_kind for source in self.sources
        }
        if any(
            source_kind_by_ref[entry.source_ref] != entry.source_kind
            for entry in self.entries
        ):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_ENTRY_SOURCE_MISMATCH")
        skill_refs = {entry.skill_ref for entry in self.entries}
        if len(skill_refs) != len(self.entries):
            raise ValueError("RUNTIME_SKILL_MARKETPLACE_SKILL_REFS_NOT_UNIQUE")
        for source in self.sources:
            actual_count = sum(
                entry.source_ref == source.source_ref for entry in self.entries
            )
            if source.record_count != actual_count:
                raise ValueError(
                    "RUNTIME_SKILL_MARKETPLACE_SOURCE_COUNT_MISMATCH"
                )
        return self


def build_runtime_skill_marketplace_catalog_snapshot(
) -> RuntimeSkillMarketplaceCatalogSnapshot:
    from ultimate_ai_agent.core.runtime_gateway.skill_marketplace_catalog_snapshot import (
        RUNTIME_SKILL_MARKETPLACE_CATALOG_SNAPSHOT,
    )

    return RuntimeSkillMarketplaceCatalogSnapshot(
        **RUNTIME_SKILL_MARKETPLACE_CATALOG_SNAPSHOT
    )
