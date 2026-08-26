"""Versioned deterministic FIN-001 fixture-manifest loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ultimate_ai_agent.core.finance.models import (
    Book,
    FinanceSnapshot,
    FinancialAccount,
    JournalEntry,
    LegalEntity,
    _FinanceModel,
    stable_finance_ref,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


ROOT = Path(__file__).resolve().parents[4]
FINANCE_FIXTURE_MANIFEST_PATH = (
    ROOT / "docs" / "product" / "finance_fin001_fixture_manifest_v1.json"
)


class FinanceFixture(_FinanceModel):
    schema_version: Literal["uaa-finance-synthetic-fixture.v1"] = (
        "uaa-finance-synthetic-fixture.v1"
    )
    fixture_ref: str
    book: Book
    legal_entities: tuple[LegalEntity, ...] = Field(..., min_length=1, max_length=16)
    accounts: tuple[FinancialAccount, ...] = Field(..., min_length=2, max_length=128)
    journal_entries: tuple[JournalEntry, ...] = Field(..., min_length=1, max_length=512)
    deterministic: Literal[True] = True
    synthetic_only: Literal[True] = True
    arbitrary_values_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_fixture_graph(self) -> "FinanceFixture":
        bound = [
            self.book.fixture_ref,
            *(entity.fixture_ref for entity in self.legal_entities),
            *(account.fixture_ref for account in self.accounts),
            *(entry.fixture_ref for entry in self.journal_entries),
            *(
                posting.fixture_ref
                for entry in self.journal_entries
                for posting in entry.postings
            ),
        ]
        if any(ref != self.fixture_ref for ref in bound):
            raise ValueError("FINANCE_FIXTURE_BINDING_MISMATCH")
        FinanceSnapshot(
            repository_ref="repository-ref:finance:fixture-validation",
            revision=1,
            generation=1,
            fixture_manifest_ref="fixture-manifest-ref:finance:validation",
            applied_fixture_refs=(self.fixture_ref,),
            books=(self.book,),
            legal_entities=self.legal_entities,
            accounts=self.accounts,
            journal_entries=self.journal_entries,
        )
        return self


class FinanceFixtureManifest(_FinanceModel):
    schema_version: Literal["uaa-finance-synthetic-fixture-manifest.v1"] = (
        "uaa-finance-synthetic-fixture-manifest.v1"
    )
    manifest_ref: str
    fixtures: tuple[FinanceFixture, ...] = Field(..., min_length=1, max_length=64)
    deterministic: Literal[True] = True
    synthetic_only: Literal[True] = True
    arbitrary_values_allowed: Literal[False] = False
    real_financial_data_allowed: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "FinanceFixtureManifest":
        validate_task_ref(self.manifest_ref, "finance_fixture_manifest_ref")
        refs = [fixture.fixture_ref for fixture in self.fixtures]
        if len(refs) != len(set(refs)):
            raise ValueError("FINANCE_FIXTURE_REF_DUPLICATE")
        expected = stable_finance_ref(
            "fixture-manifest-ref:finance/FIN-001",
            self.model_dump(mode="json", exclude={"manifest_ref"}),
        )
        if self.manifest_ref != expected:
            raise ValueError("FINANCE_FIXTURE_MANIFEST_REF_INVALID")
        return self


def load_finance_fixture_manifest(
    path: Path = FINANCE_FIXTURE_MANIFEST_PATH,
) -> FinanceFixtureManifest:
    if path != FINANCE_FIXTURE_MANIFEST_PATH:
        raise ValueError("FINANCE_FIXTURE_MANIFEST_PATH_DENIED")
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("FINANCE_FIXTURE_MANIFEST_TOO_LARGE")
    return FinanceFixtureManifest.model_validate_json(raw)


def load_finance_fixture(fixture_ref: str) -> FinanceFixture:
    validate_task_ref(fixture_ref, "finance_fixture_ref")
    manifest = load_finance_fixture_manifest()
    for fixture in manifest.fixtures:
        if fixture.fixture_ref == fixture_ref:
            return fixture.model_copy(deep=True)
    raise ValueError("FINANCE_FIXTURE_REF_UNKNOWN")


def fixture_manifest_canonical_json(manifest: FinanceFixtureManifest) -> str:
    return json.dumps(
        manifest.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
