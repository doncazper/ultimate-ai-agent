"""Strict synthetic accounting contracts for the FIN-001 first slice."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)


FINANCE_SCHEMA_VERSION = "finance-schema:v1"
FINANCE_SYNTHETIC_INPUT_POLICY_REF = (
    "policy-ref:finance/FIN-001:fixture-ref-allowlist-only:v1"
)


def stable_finance_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_refs(value: object, *, field_name: str = "finance_ref") -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"finance_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"finance_{name}")
            else:
                _validate_refs(nested, field_name=field_name)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested, field_name=field_name)


class _FinanceModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_safe_contract(self) -> "_FinanceModel":
        payload = self.model_dump(mode="json")
        _validate_refs(payload)
        validate_safe_task_payload(payload, self.__class__.__name__)
        return self


class AccountKind(str, Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    income = "income"
    expense = "expense"
    suspense = "suspense"


class PostingSide(str, Enum):
    debit = "debit"
    credit = "credit"


class JournalFlow(str, Enum):
    opening_balance = "opening_balance"
    transfer = "transfer"
    split = "split"
    reversal = "reversal"
    adjustment = "adjustment"
    suspense = "suspense"


class Book(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    book_ref: str
    legal_entity_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    default_commodity_ref: str
    fixture_ref: str
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False


class LegalEntity(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    legal_entity_ref: str
    book_ref: str
    entity_kind_ref: str
    fixture_ref: str
    synthetic_only: Literal[True] = True


class FinancialAccount(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    account_ref: str
    book_ref: str
    legal_entity_ref: str
    account_kind: AccountKind
    commodity_ref: str
    fixture_ref: str
    active: StrictBool = True
    synthetic_only: Literal[True] = True


class Posting(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    posting_ref: str
    account_ref: str
    commodity_ref: str
    side: PostingSide
    amount_minor: StrictInt = Field(..., gt=0, le=10**15)
    fixture_ref: str
    synthetic_only: Literal[True] = True

    @property
    def signed_amount_minor(self) -> int:
        return (
            self.amount_minor
            if self.side == PostingSide.debit.value
            else -self.amount_minor
        )


class JournalEntry(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    journal_entry_ref: str
    book_ref: str
    flow: JournalFlow
    fixture_ref: str
    postings: tuple[Posting, ...] = Field(..., min_length=2, max_length=128)
    reverses_journal_entry_ref: str | None = None
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_balanced_entry(self) -> "JournalEntry":
        posting_refs = [posting.posting_ref for posting in self.postings]
        if len(posting_refs) != len(set(posting_refs)):
            raise ValueError("FINANCE_POSTING_REF_DUPLICATE")
        balances: dict[str, int] = defaultdict(int)
        for posting in self.postings:
            balances[posting.commodity_ref] += posting.signed_amount_minor
        if any(balance != 0 for balance in balances.values()):
            raise ValueError("FINANCE_JOURNAL_ENTRY_UNBALANCED")
        if self.flow == JournalFlow.reversal.value:
            if self.reverses_journal_entry_ref is None:
                raise ValueError("FINANCE_REVERSAL_TARGET_REQUIRED")
        elif self.reverses_journal_entry_ref is not None:
            raise ValueError("FINANCE_REVERSAL_TARGET_DENIED")
        return self


class FinanceImportCommitRecord(_FinanceModel):
    """Content-free lineage for one committed FIN-002 synthetic preview."""

    schema_version: Literal["uaa-finance-import-commit-record.v1"] = (
        "uaa-finance-import-commit-record.v1"
    )
    commit_ref: str
    preview_ref: str
    fixture_ref: str
    profile_ref: str
    import_fixture_manifest_ref: str
    before_snapshot_ref: str
    before_revision: StrictInt = Field(..., ge=1)
    observation_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    source_fingerprint_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    candidate_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    journal_entry_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    rollback_ref: str
    synthetic_only: Literal[True] = True
    raw_source_content_persisted: Literal[False] = False
    real_financial_data_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_commit_binding(self) -> "FinanceImportCommitRecord":
        lengths = {
            len(self.observation_refs),
            len(self.source_fingerprint_refs),
            len(self.candidate_refs),
            len(self.journal_entry_refs),
        }
        if len(lengths) != 1:
            raise ValueError("FIN002_IMPORT_COMMIT_LINEAGE_COUNT_MISMATCH")
        for refs, code in (
            (self.observation_refs, "FIN002_IMPORT_OBSERVATION_REF_DUPLICATE"),
            (
                self.source_fingerprint_refs,
                "FIN002_IMPORT_SOURCE_FINGERPRINT_DUPLICATE",
            ),
            (self.candidate_refs, "FIN002_IMPORT_CANDIDATE_REF_DUPLICATE"),
            (self.journal_entry_refs, "FIN002_IMPORT_JOURNAL_REF_DUPLICATE"),
        ):
            if len(refs) != len(set(refs)):
                raise ValueError(code)
        expected_rollback_ref = stable_finance_ref(
            "rollback-ref:finance/FIN-002:synthetic-import-commit",
            {
                "before_snapshot_ref": self.before_snapshot_ref,
                "journal_entry_refs": list(self.journal_entry_refs),
            },
        )
        if self.rollback_ref != expected_rollback_ref:
            raise ValueError("FIN002_IMPORT_ROLLBACK_REF_INVALID")
        expected_commit_ref = stable_finance_ref(
            "import-commit-ref:finance/FIN-002",
            self.model_dump(mode="json", exclude={"commit_ref"}),
        )
        if self.commit_ref != expected_commit_ref:
            raise ValueError("FIN002_IMPORT_COMMIT_REF_INVALID")
        return self


class FinanceSnapshot(_FinanceModel):
    schema_version: Literal["finance-schema:v1"] = FINANCE_SCHEMA_VERSION
    repository_ref: str
    revision: StrictInt = Field(..., ge=0)
    generation: StrictInt = Field(..., ge=1)
    fixture_manifest_ref: str
    applied_fixture_refs: tuple[str, ...] = Field(default=(), max_length=64)
    books: tuple[Book, ...] = Field(default=(), max_length=16)
    legal_entities: tuple[LegalEntity, ...] = Field(default=(), max_length=64)
    accounts: tuple[FinancialAccount, ...] = Field(default=(), max_length=512)
    journal_entries: tuple[JournalEntry, ...] = Field(default=(), max_length=10_000)
    import_commits: tuple[FinanceImportCommitRecord, ...] = Field(
        default=(), max_length=10_000
    )
    safe_disable_enabled: StrictBool = True
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False
    connector_authority_granted: Literal[False] = False
    payment_authority_granted: Literal[False] = False
    filing_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_graph(self) -> "FinanceSnapshot":
        book_refs = [book.book_ref for book in self.books]
        entity_refs = [entity.legal_entity_ref for entity in self.legal_entities]
        account_refs = [account.account_ref for account in self.accounts]
        entry_refs = [entry.journal_entry_ref for entry in self.journal_entries]
        import_commit_refs = [item.commit_ref for item in self.import_commits]
        for refs, code in (
            (book_refs, "FINANCE_BOOK_REF_DUPLICATE"),
            (entity_refs, "FINANCE_ENTITY_REF_DUPLICATE"),
            (account_refs, "FINANCE_ACCOUNT_REF_DUPLICATE"),
            (entry_refs, "FINANCE_JOURNAL_ENTRY_REF_DUPLICATE"),
            (import_commit_refs, "FIN002_IMPORT_COMMIT_REF_DUPLICATE"),
        ):
            if len(refs) != len(set(refs)):
                raise ValueError(code)
        known_books = set(book_refs)
        known_entities = set(entity_refs)
        known_accounts = {account.account_ref: account for account in self.accounts}
        for entity in self.legal_entities:
            if entity.book_ref not in known_books:
                raise ValueError("FINANCE_ENTITY_BOOK_REF_UNKNOWN")
        for account in self.accounts:
            if account.book_ref not in known_books:
                raise ValueError("FINANCE_ACCOUNT_BOOK_REF_UNKNOWN")
            if account.legal_entity_ref not in known_entities:
                raise ValueError("FINANCE_ACCOUNT_ENTITY_REF_UNKNOWN")
        for entry in self.journal_entries:
            if entry.book_ref not in known_books:
                raise ValueError("FINANCE_ENTRY_BOOK_REF_UNKNOWN")
            for posting in entry.postings:
                account = known_accounts.get(posting.account_ref)
                if account is None:
                    raise ValueError("FINANCE_POSTING_ACCOUNT_REF_UNKNOWN")
                if account.book_ref != entry.book_ref:
                    raise ValueError("FINANCE_POSTING_BOOK_SCOPE_MISMATCH")
                if account.commodity_ref != posting.commodity_ref:
                    raise ValueError("FINANCE_POSTING_COMMODITY_MISMATCH")
        known_entries = set(entry_refs)
        entries_by_ref = {
            entry.journal_entry_ref: entry for entry in self.journal_entries
        }
        imported_observation_refs: set[str] = set()
        imported_fingerprint_refs: set[str] = set()
        imported_candidate_refs: set[str] = set()
        imported_journal_refs: set[str] = set()
        for record in self.import_commits:
            if record.before_revision >= self.revision:
                raise ValueError("FIN002_IMPORT_COMMIT_REVISION_INVALID")
            if record.fixture_ref not in self.applied_fixture_refs:
                raise ValueError("FIN002_IMPORT_FIXTURE_NOT_APPLIED")
            for refs, seen, duplicate_code in (
                (
                    record.observation_refs,
                    imported_observation_refs,
                    "FIN002_IMPORT_OBSERVATION_REUSED",
                ),
                (
                    record.source_fingerprint_refs,
                    imported_fingerprint_refs,
                    "FIN002_IMPORT_SOURCE_FINGERPRINT_REUSED",
                ),
                (
                    record.candidate_refs,
                    imported_candidate_refs,
                    "FIN002_IMPORT_CANDIDATE_REUSED",
                ),
                (
                    record.journal_entry_refs,
                    imported_journal_refs,
                    "FIN002_IMPORT_JOURNAL_REUSED",
                ),
            ):
                if seen.intersection(refs):
                    raise ValueError(duplicate_code)
                seen.update(refs)
            for journal_ref in record.journal_entry_refs:
                if journal_ref not in known_entries:
                    raise ValueError("FIN002_IMPORT_JOURNAL_REF_UNKNOWN")
                if entries_by_ref[journal_ref].fixture_ref != record.fixture_ref:
                    raise ValueError("FIN002_IMPORT_JOURNAL_FIXTURE_MISMATCH")
        reversed_targets: set[str] = set()
        for entry in self.journal_entries:
            if (
                entry.reverses_journal_entry_ref is not None
                and entry.reverses_journal_entry_ref not in known_entries
            ):
                raise ValueError("FINANCE_REVERSAL_TARGET_UNKNOWN")
            if entry.reverses_journal_entry_ref is None:
                continue
            if entry.reverses_journal_entry_ref in reversed_targets:
                raise ValueError("FINANCE_REVERSAL_TARGET_DUPLICATE")
            reversed_targets.add(entry.reverses_journal_entry_ref)
            target = entries_by_ref[entry.reverses_journal_entry_ref]
            expected = sorted(
                (
                    posting.account_ref,
                    posting.commodity_ref,
                    -posting.signed_amount_minor,
                )
                for posting in target.postings
            )
            actual = sorted(
                (
                    posting.account_ref,
                    posting.commodity_ref,
                    posting.signed_amount_minor,
                )
                for posting in entry.postings
            )
            if actual != expected:
                raise ValueError("FINANCE_REVERSAL_POSTINGS_MISMATCH")
        return self

    @property
    def snapshot_ref(self) -> str:
        return stable_finance_ref(
            "finance-snapshot-ref",
            self.model_dump(mode="json"),
        )

    def account_balances(self) -> dict[str, dict[str, int]]:
        balances: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for entry in self.journal_entries:
            for posting in entry.postings:
                balances[posting.account_ref][posting.commodity_ref] += (
                    posting.signed_amount_minor
                )
        return {
            account_ref: dict(sorted(by_commodity.items()))
            for account_ref, by_commodity in sorted(balances.items())
        }

    def redacted_read_model(self) -> dict[str, Any]:
        counts = {
            "books": len(self.books),
            "legal_entities": len(self.legal_entities),
            "accounts": len(self.accounts),
            "journal_entries": len(self.journal_entries),
            "postings": sum(len(entry.postings) for entry in self.journal_entries),
        }
        if self.import_commits:
            counts.update(
                {
                    "import_commits": len(self.import_commits),
                    "imported_observations": sum(
                        len(item.observation_refs) for item in self.import_commits
                    ),
                    "imported_candidates": sum(
                        len(item.candidate_refs) for item in self.import_commits
                    ),
                }
            )
        return {
            "schema_version": "uaa-finance-synthetic-read-model.v1",
            "repository_ref": self.repository_ref,
            "snapshot_ref": self.snapshot_ref,
            "finance_schema_ref": self.schema_version,
            "fixture_manifest_ref": self.fixture_manifest_ref,
            "applied_fixture_refs": list(self.applied_fixture_refs),
            "revision": self.revision,
            "generation": self.generation,
            "counts": counts,
            "balance_proof_ref": stable_finance_ref(
                "finance-balance-proof-ref",
                self.account_balances(),
            ),
            "safe_disable_enabled": self.safe_disable_enabled,
            "synthetic_only": True,
            "real_financial_data_included": False,
            "raw_financial_values_included": False,
            "connector_authority_granted": False,
            "payment_authority_granted": False,
            "filing_authority_granted": False,
        }
