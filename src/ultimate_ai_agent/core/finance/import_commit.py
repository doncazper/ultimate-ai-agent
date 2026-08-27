"""Exact synthetic FIN-002 preview-to-repository commit contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.finance.import_preview import SyntheticImportPreview
from ultimate_ai_agent.core.finance.models import (
    FinanceImportCommitRecord,
    FinanceSnapshot,
    JournalEntry,
    Posting,
    PostingSide,
    stable_finance_ref,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)


FIN002_SYNTHETIC_IMPORT_COMMIT_CAPABILITY_REF = (
    "capability-ref:finance/FIN-002/synthetic-import-commit"
)
FIN002_SYNTHETIC_IMPORT_COMMIT_LANE_REF = (
    "authority-lane-ref:finance/FIN-002/synthetic-import-commit"
)
FIN002_SYNTHETIC_IMPORT_COMMIT_ADAPTER_REF = (
    "authority-adapter-ref:finance/FIN-002/protected-import-commit:v1"
)
FIN002_SYNTHETIC_IMPORT_COMMIT_TOOL_REF = (
    "tool-ref:finance/FIN-002/synthetic-import-commit:v1"
)
FIN002_IMPORT_SAFE_DISABLE_REF = (
    "safe-disable-ref:finance/FIN-002/synthetic-import-commit"
)
FIN002_IMPORT_ROLLBACK_CONTRACT_REF = (
    "rollback-contract-ref:finance/FIN-002/reversal-or-restore:v1"
)
FIN002_IMPORT_READINESS_REF = (
    "readiness-ref:finance/FIN-002/protected-synthetic-import-commit"
)
FIN002_IMPORT_BUDGET_REF = "budget-ref:finance/FIN-002:one-synthetic-import-commit"
FIN002_IMPORT_START_DEADLINE_REF = (
    "deadline-ref:finance/FIN-002:import-commit-prepared-window"
)
FIN002_IMPORT_KILL_SWITCH_REF = "kill-switch-ref:finance/FIN-002:local"
FIN002_IMPORT_EXACT_TARGET_REF = "target-ref:finance/FIN-002:protected-local-repository"
FIN002_SUSPENSE_ACCOUNT_REF = "financial-account-ref:finance:synthetic-suspense"


class FinanceImportCommitError(RuntimeError):
    """Content-free FIN-002 commit failure."""


def _posting(
    *,
    candidate_ref: str,
    account_ref: str,
    commodity_ref: str,
    side: PostingSide,
    amount_minor: int,
    fixture_ref: str,
) -> Posting:
    return Posting(
        posting_ref=stable_finance_ref(
            "posting-ref:finance/FIN-002:synthetic-import",
            {
                "candidate_ref": candidate_ref,
                "account_ref": account_ref,
                "side": side.value,
            },
        ),
        account_ref=account_ref,
        commodity_ref=commodity_ref,
        side=side,
        amount_minor=amount_minor,
        fixture_ref=fixture_ref,
    )


def build_import_commit_record(
    preview: SyntheticImportPreview,
    *,
    before: FinanceSnapshot,
) -> tuple[FinanceImportCommitRecord, tuple[JournalEntry, ...]]:
    """Map one current allowlisted preview to balanced suspense entries."""

    if not preview.candidates or preview.quarantines:
        raise FinanceImportCommitError("FIN002_IMPORT_PREVIEW_NOT_COMMITTABLE")
    accounts = {item.account_ref: item for item in before.accounts}
    suspense = accounts.get(FIN002_SUSPENSE_ACCOUNT_REF)
    if suspense is None or not suspense.active:
        raise FinanceImportCommitError("FIN002_IMPORT_SUSPENSE_ACCOUNT_UNAVAILABLE")

    entries: list[JournalEntry] = []
    for observation, candidate in zip(
        preview.observations, preview.candidates, strict=True
    ):
        source_account = accounts.get(candidate.account_ref)
        if (
            source_account is None
            or not source_account.active
            or source_account.book_ref != candidate.book_ref
            or source_account.commodity_ref != candidate.commodity_ref
            or suspense.book_ref != candidate.book_ref
            or suspense.commodity_ref != candidate.commodity_ref
            or observation.book_ref != candidate.book_ref
        ):
            raise FinanceImportCommitError("FIN002_IMPORT_ACCOUNT_BINDING_INVALID")
        if candidate.direction == "outflow":
            source_side, suspense_side = PostingSide.credit, PostingSide.debit
        else:
            source_side, suspense_side = PostingSide.debit, PostingSide.credit
        entries.append(
            JournalEntry(
                journal_entry_ref=stable_finance_ref(
                    "journal-entry-ref:finance/FIN-002:synthetic-import",
                    {"candidate_ref": candidate.candidate_ref},
                ),
                book_ref=candidate.book_ref,
                flow="suspense",
                fixture_ref=preview.fixture_ref,
                postings=(
                    _posting(
                        candidate_ref=candidate.candidate_ref,
                        account_ref=source_account.account_ref,
                        commodity_ref=candidate.commodity_ref,
                        side=source_side,
                        amount_minor=candidate.amount_minor,
                        fixture_ref=preview.fixture_ref,
                    ),
                    _posting(
                        candidate_ref=candidate.candidate_ref,
                        account_ref=suspense.account_ref,
                        commodity_ref=candidate.commodity_ref,
                        side=suspense_side,
                        amount_minor=candidate.amount_minor,
                        fixture_ref=preview.fixture_ref,
                    ),
                ),
            )
        )

    journal_refs = tuple(item.journal_entry_ref for item in entries)
    rollback_ref = stable_finance_ref(
        "rollback-ref:finance/FIN-002:synthetic-import-commit",
        {
            "before_snapshot_ref": before.snapshot_ref,
            "journal_entry_refs": list(journal_refs),
        },
    )
    payload = {
        "preview_ref": preview.preview_ref,
        "fixture_ref": preview.fixture_ref,
        "profile_ref": preview.profile_ref,
        "import_fixture_manifest_ref": preview.import_fixture_manifest_ref,
        "before_snapshot_ref": before.snapshot_ref,
        "before_revision": before.revision,
        "observation_refs": tuple(
            item.observation_ref for item in preview.observations
        ),
        "source_fingerprint_refs": tuple(
            item.source_fingerprint_ref for item in preview.observations
        ),
        "candidate_refs": tuple(item.candidate_ref for item in preview.candidates),
        "journal_entry_refs": journal_refs,
        "rollback_ref": rollback_ref,
    }
    provisional = FinanceImportCommitRecord.model_construct(
        commit_ref="import-commit-ref:finance/FIN-002:pending",
        **payload,
    )
    commit_ref = stable_finance_ref(
        "import-commit-ref:finance/FIN-002",
        provisional.model_dump(mode="json", exclude={"commit_ref"}),
    )
    return FinanceImportCommitRecord(commit_ref=commit_ref, **payload), tuple(entries)


class FinanceImportCommitProof(BaseModel):
    """Redacted exact before/after and rollback proof for one commit."""

    schema_version: Literal["uaa-finance-import-commit-proof.v1"] = (
        "uaa-finance-import-commit-proof.v1"
    )
    proof_ref: str
    mutation_receipt_ref: str
    commit_ref: str
    preview_ref: str
    fixture_ref: str
    before_snapshot_ref: str
    after_snapshot_ref: str
    before_revision: StrictInt = Field(..., ge=1)
    after_revision: StrictInt = Field(..., ge=2)
    candidate_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    journal_entry_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    rollback_ref: str
    replayed: StrictBool = False
    mutation_performed: Literal[True] = True
    synthetic_only: Literal[True] = True
    raw_source_content_included: Literal[False] = False
    arbitrary_operator_input_allowed: Literal[False] = False
    real_financial_data_included: Literal[False] = False
    connector_call_performed: Literal[False] = False
    ocr_performed: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_proof(self) -> "FinanceImportCommitProof":
        payload = self.model_dump(mode="json")
        for name, value in payload.items():
            if name.endswith("_ref"):
                validate_task_ref(str(value), f"finance_import_proof_{name}")
            elif name.endswith("_refs"):
                for ref in value:
                    validate_task_ref(str(ref), f"finance_import_proof_{name}")
        if self.after_revision != self.before_revision + 1:
            raise ValueError("FIN002_IMPORT_COMMIT_REVISION_MISMATCH")
        if len(self.candidate_refs) != len(self.journal_entry_refs):
            raise ValueError("FIN002_IMPORT_COMMIT_PROOF_COUNT_MISMATCH")
        expected = stable_finance_ref(
            "import-commit-proof-ref:finance/FIN-002",
            self.model_dump(mode="json", exclude={"proof_ref", "replayed"}),
        )
        if self.proof_ref != expected:
            raise ValueError("FIN002_IMPORT_COMMIT_PROOF_REF_INVALID")
        validate_safe_task_payload(payload, "finance_import_commit_proof")
        return self


def build_import_commit_proof(
    *,
    record: FinanceImportCommitRecord,
    mutation_receipt_ref: str,
    after_snapshot_ref: str,
    replayed: bool = False,
) -> FinanceImportCommitProof:
    payload = {
        "mutation_receipt_ref": mutation_receipt_ref,
        "commit_ref": record.commit_ref,
        "preview_ref": record.preview_ref,
        "fixture_ref": record.fixture_ref,
        "before_snapshot_ref": record.before_snapshot_ref,
        "after_snapshot_ref": after_snapshot_ref,
        "before_revision": record.before_revision,
        "after_revision": record.before_revision + 1,
        "candidate_refs": record.candidate_refs,
        "journal_entry_refs": record.journal_entry_refs,
        "rollback_ref": record.rollback_ref,
        "replayed": replayed,
    }
    provisional = FinanceImportCommitProof.model_construct(
        proof_ref="import-commit-proof-ref:finance/FIN-002:pending",
        **payload,
    )
    proof_ref = stable_finance_ref(
        "import-commit-proof-ref:finance/FIN-002",
        provisional.model_dump(mode="json", exclude={"proof_ref", "replayed"}),
    )
    return FinanceImportCommitProof(proof_ref=proof_ref, **payload)
