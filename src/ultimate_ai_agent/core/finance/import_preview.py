"""Deterministic, synthetic-only CSV import preview contracts for FIN-002.

This slice accepts allowlisted repository fixtures by safe ref. It deliberately
has no file-path, byte-stream, persistence, OCR, connector, or real-data entry
point. Parsed row values are reduced to typed synthetic contracts; previews
persist no raw CSV content.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


FIN002_IMPORT_SCHEMA_VERSION = "finance-import-schema:v1"
FIN002_SYNTHETIC_CSV_PROFILE_REF = "import-profile-ref:finance/FIN-002:synthetic-csv:v1"
FIN002_EXACT_COLUMNS = (
    "row_ref",
    "date_ref",
    "direction",
    "amount_minor",
    "counterparty_ref",
    "memo_ref",
)
FIN002_MAX_FIXTURE_ROWS = 128
_SECRET_TOKEN_PREFIX = re.compile(
    r"(?i)(?:^|[:_-])(?:sk_(?:live|test)|gh[pousr]|akia|asia)[_-]?[a-z0-9]+"
)


class FinanceImportPreviewError(RuntimeError):
    """Content-free FIN-002 preview failure."""


class ImportDirection(str, Enum):
    inflow = "inflow"
    outflow = "outflow"


class QuarantineReason(str, Enum):
    invalid_ref = "invalid_ref"
    invalid_amount = "invalid_amount"
    invalid_direction = "invalid_direction"
    unsafe_cell = "unsafe_cell"


def _validate_refs(value: object) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"finance_import_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"finance_import_{name}")
            else:
                _validate_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested)


class _ImportModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def validate_safe_contract(self) -> "_ImportModel":
        payload = self.model_dump(mode="json")
        _validate_refs(payload)
        validate_safe_task_payload(payload, self.__class__.__name__)
        return self


class SyntheticCsvImportFixture(_ImportModel):
    schema_version: Literal["finance-import-schema:v1"] = FIN002_IMPORT_SCHEMA_VERSION
    fixture_ref: str
    profile_ref: Literal["import-profile-ref:finance/FIN-002:synthetic-csv:v1"] = (
        FIN002_SYNTHETIC_CSV_PROFILE_REF
    )
    book_ref: str
    account_ref: str
    commodity_ref: str
    csv_sha256_ref: str
    expected_row_count: StrictInt = Field(..., ge=1, le=FIN002_MAX_FIXTURE_ROWS)
    expected_accepted_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    expected_duplicate_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    expected_quarantine_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    synthetic_only: Literal[True] = True
    arbitrary_operator_input_allowed: Literal[False] = False


class SourceObservation(_ImportModel):
    schema_version: Literal["finance-import-schema:v1"] = FIN002_IMPORT_SCHEMA_VERSION
    observation_ref: str
    fixture_ref: str
    source_row_ref: str
    book_ref: str
    account_ref: str
    commodity_ref: str
    date_ref: str
    direction: ImportDirection
    amount_minor: StrictInt = Field(..., gt=0, le=10**15)
    counterparty_ref: str
    memo_ref: str
    source_fingerprint_ref: str
    synthetic_only: Literal[True] = True
    raw_source_content_persisted: Literal[False] = False


class TransactionCandidate(_ImportModel):
    schema_version: Literal["finance-import-schema:v1"] = FIN002_IMPORT_SCHEMA_VERSION
    candidate_ref: str
    observation_ref: str
    book_ref: str
    account_ref: str
    commodity_ref: str
    direction: ImportDirection
    amount_minor: StrictInt = Field(..., gt=0, le=10**15)
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    synthetic_only: Literal[True] = True
    commit_authority_granted: Literal[False] = False


class ImportQuarantine(_ImportModel):
    schema_version: Literal["finance-import-schema:v1"] = FIN002_IMPORT_SCHEMA_VERSION
    quarantine_ref: str
    fixture_ref: str
    row_position_ref: str
    reason: QuarantineReason
    raw_value_persisted: Literal[False] = False
    retry_authority_granted: Literal[False] = False


class ImportRollbackProof(_ImportModel):
    schema_version: Literal["finance-import-schema:v1"] = FIN002_IMPORT_SCHEMA_VERSION
    rollback_ref: str
    preview_ref: str
    affected_candidate_refs: tuple[str, ...] = Field(default=(), max_length=128)
    mutation_performed: Literal[False] = False
    persistent_state_changed: Literal[False] = False
    rollback_required: Literal[False] = False


def _preview_ref(
    *,
    fixture_ref: str,
    profile_ref: str,
    candidate_refs: tuple[str, ...],
    duplicate_fingerprint_refs: tuple[str, ...],
    quarantine_refs: tuple[str, ...],
) -> str:
    return stable_finance_ref(
        "import-preview-ref:finance/FIN-002",
        {
            "fixture_ref": fixture_ref,
            "profile_ref": profile_ref,
            "candidate_refs": list(candidate_refs),
            "duplicate_fingerprint_refs": list(duplicate_fingerprint_refs),
            "quarantine_refs": list(quarantine_refs),
        },
    )


def _rollback_ref(*, preview_ref: str, candidate_refs: tuple[str, ...]) -> str:
    return stable_finance_ref(
        "rollback-proof-ref:finance/FIN-002",
        {
            "preview_ref": preview_ref,
            "affected_candidate_refs": list(candidate_refs),
            "persistent_state_changed": False,
        },
    )


class SyntheticImportPreview(_ImportModel):
    schema_version: Literal["uaa-finance-synthetic-import-preview.v1"] = (
        "uaa-finance-synthetic-import-preview.v1"
    )
    preview_ref: str
    fixture_ref: str
    profile_ref: str
    observations: tuple[SourceObservation, ...] = Field(default=(), max_length=128)
    candidates: tuple[TransactionCandidate, ...] = Field(default=(), max_length=128)
    duplicate_fingerprint_refs: tuple[str, ...] = Field(default=(), max_length=128)
    quarantines: tuple[ImportQuarantine, ...] = Field(default=(), max_length=128)
    rollback_proof: ImportRollbackProof
    row_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    accepted_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    duplicate_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    quarantine_count: StrictInt = Field(..., ge=0, le=FIN002_MAX_FIXTURE_ROWS)
    synthetic_only: Literal[True] = True
    raw_source_content_included: Literal[False] = False
    arbitrary_operator_input_allowed: Literal[False] = False
    mutation_performed: Literal[False] = False
    commit_authority_granted: Literal[False] = False
    connector_authority_granted: Literal[False] = False
    ocr_authority_granted: Literal[False] = False
    real_financial_data_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_counts_and_bindings(self) -> "SyntheticImportPreview":
        if self.row_count != (
            self.accepted_count + self.duplicate_count + self.quarantine_count
        ):
            raise ValueError("FIN002_PREVIEW_COUNT_MISMATCH")
        if self.accepted_count != len(self.candidates):
            raise ValueError("FIN002_ACCEPTED_COUNT_MISMATCH")
        if len(self.observations) != len(self.candidates):
            raise ValueError("FIN002_OBSERVATION_COUNT_MISMATCH")
        if self.duplicate_count != len(self.duplicate_fingerprint_refs):
            raise ValueError("FIN002_DUPLICATE_COUNT_MISMATCH")
        if self.quarantine_count != len(self.quarantines):
            raise ValueError("FIN002_QUARANTINE_COUNT_MISMATCH")
        if self.rollback_proof.preview_ref != self.preview_ref:
            raise ValueError("FIN002_ROLLBACK_PREVIEW_BINDING_MISMATCH")
        if self.rollback_proof.affected_candidate_refs != tuple(
            candidate.candidate_ref for candidate in self.candidates
        ):
            raise ValueError("FIN002_ROLLBACK_CANDIDATE_BINDING_MISMATCH")
        observation_refs = tuple(item.observation_ref for item in self.observations)
        candidate_observation_refs = tuple(
            item.observation_ref for item in self.candidates
        )
        if observation_refs != candidate_observation_refs:
            raise ValueError("FIN002_CANDIDATE_OBSERVATION_BINDING_MISMATCH")
        for observation, candidate in zip(
            self.observations, self.candidates, strict=True
        ):
            if (
                candidate.book_ref != observation.book_ref
                or candidate.account_ref != observation.account_ref
                or candidate.commodity_ref != observation.commodity_ref
                or candidate.direction != observation.direction
                or candidate.amount_minor != observation.amount_minor
                or candidate.evidence_refs
                != (
                    observation.observation_ref,
                    observation.source_fingerprint_ref,
                )
            ):
                raise ValueError("FIN002_CANDIDATE_SOURCE_BINDING_MISMATCH")
        for refs, code in (
            (observation_refs, "FIN002_OBSERVATION_REF_DUPLICATE"),
            (
                tuple(item.source_fingerprint_ref for item in self.observations),
                "FIN002_SOURCE_FINGERPRINT_DUPLICATE",
            ),
            (
                tuple(item.candidate_ref for item in self.candidates),
                "FIN002_CANDIDATE_REF_DUPLICATE",
            ),
            (
                tuple(item.quarantine_ref for item in self.quarantines),
                "FIN002_QUARANTINE_REF_DUPLICATE",
            ),
        ):
            if len(refs) != len(set(refs)):
                raise ValueError(code)
        candidate_refs = tuple(item.candidate_ref for item in self.candidates)
        expected_preview_ref = _preview_ref(
            fixture_ref=self.fixture_ref,
            profile_ref=self.profile_ref,
            candidate_refs=candidate_refs,
            duplicate_fingerprint_refs=self.duplicate_fingerprint_refs,
            quarantine_refs=tuple(item.quarantine_ref for item in self.quarantines),
        )
        if self.preview_ref != expected_preview_ref:
            raise ValueError("FIN002_PREVIEW_REF_BINDING_MISMATCH")
        if self.rollback_proof.rollback_ref != _rollback_ref(
            preview_ref=self.preview_ref,
            candidate_refs=candidate_refs,
        ):
            raise ValueError("FIN002_ROLLBACK_REF_BINDING_MISMATCH")
        return self

    def redacted_read_model(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "preview_ref": self.preview_ref,
            "fixture_ref": self.fixture_ref,
            "profile_ref": self.profile_ref,
            "counts": {
                "rows": self.row_count,
                "accepted": self.accepted_count,
                "duplicates": self.duplicate_count,
                "quarantined": self.quarantine_count,
            },
            "candidate_refs": [item.candidate_ref for item in self.candidates],
            "duplicate_fingerprint_refs": list(self.duplicate_fingerprint_refs),
            "quarantines": [
                {
                    "quarantine_ref": item.quarantine_ref,
                    "row_position_ref": item.row_position_ref,
                    "reason": item.reason,
                }
                for item in self.quarantines
            ],
            "rollback_ref": self.rollback_proof.rollback_ref,
            "synthetic_only": True,
            "raw_source_content_included": False,
            "arbitrary_operator_input_allowed": False,
            "mutation_performed": False,
            "commit_authority_granted": False,
            "connector_authority_granted": False,
            "ocr_authority_granted": False,
            "real_financial_data_allowed": False,
        }


_SYNTHETIC_FIXTURE_CSV: dict[str, str] = {
    "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1": (
        "row_ref,date_ref,direction,amount_minor,counterparty_ref,memo_ref\n"
        "row-ref:finance/FIN-002:clean-1,date-ref:finance/FIN-002:day-1,outflow,1250,"
        "counterparty-ref:finance/FIN-002:vendor-a,memo-ref:finance/FIN-002:office-supply\n"
        "row-ref:finance/FIN-002:clean-2,date-ref:finance/FIN-002:day-2,inflow,4200,"
        "counterparty-ref:finance/FIN-002:client-a,memo-ref:finance/FIN-002:service-income\n"
    ),
    "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1": (
        "row_ref,date_ref,direction,amount_minor,counterparty_ref,memo_ref\n"
        "row-ref:finance/FIN-002:duplicate-1,date-ref:finance/FIN-002:day-3,outflow,875,"
        "counterparty-ref:finance/FIN-002:vendor-b,memo-ref:finance/FIN-002:software\n"
        "row-ref:finance/FIN-002:duplicate-2,date-ref:finance/FIN-002:day-3,outflow,875,"
        "counterparty-ref:finance/FIN-002:vendor-b,memo-ref:finance/FIN-002:software\n"
    ),
    "fixture-ref:finance/FIN-002:synthetic-csv-adversarial:v1": (
        "row_ref,date_ref,direction,amount_minor,counterparty_ref,memo_ref\n"
        "row-ref:finance/FIN-002:adversarial-1,date-ref:finance/FIN-002:day-4,outflow,0,"
        "counterparty-ref:finance/FIN-002:vendor-c,memo-ref:finance/FIN-002:zero-value\n"
        "row-ref:finance/FIN-002:adversarial-2,date-ref:finance/FIN-002:day-5,sideways,900,"
        "counterparty-ref:finance/FIN-002:vendor-d,memo-ref:finance/FIN-002:bad-direction\n"
        "row-ref:finance/FIN-002:adversarial-3,date-ref:finance/FIN-002:day-6,outflow,900,"
        "counterparty-ref:finance/FIN-002:vendor-e,=synthetic-formula\n"
    ),
}


_FIXTURE_EXPECTATIONS = {
    "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1": (2, 2, 0, 0),
    "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1": (2, 1, 1, 0),
    "fixture-ref:finance/FIN-002:synthetic-csv-adversarial:v1": (3, 0, 0, 3),
}


def _fixture_contract(fixture_ref: str) -> SyntheticCsvImportFixture:
    try:
        content = _SYNTHETIC_FIXTURE_CSV[fixture_ref]
        row_count, accepted, duplicate, quarantine = _FIXTURE_EXPECTATIONS[fixture_ref]
    except KeyError as exc:
        raise FinanceImportPreviewError("FIN002_FIXTURE_REF_UNKNOWN") from exc
    return SyntheticCsvImportFixture(
        fixture_ref=fixture_ref,
        book_ref="book-ref:finance:synthetic-primary",
        account_ref="financial-account-ref:finance:synthetic-cash",
        commodity_ref="commodity-ref:finance:USD",
        csv_sha256_ref=f"sha256:{hashlib.sha256(content.encode()).hexdigest()}",
        expected_row_count=row_count,
        expected_accepted_count=accepted,
        expected_duplicate_count=duplicate,
        expected_quarantine_count=quarantine,
    )


def load_synthetic_import_fixture_manifest() -> tuple[SyntheticCsvImportFixture, ...]:
    return tuple(_fixture_contract(ref) for ref in sorted(_SYNTHETIC_FIXTURE_CSV))


def synthetic_import_fixture_manifest_ref() -> str:
    return stable_finance_ref(
        "fixture-manifest-ref:finance/FIN-002",
        [
            item.model_dump(mode="json")
            for item in load_synthetic_import_fixture_manifest()
        ],
    )


def _row_position_ref(fixture_ref: str, position: int) -> str:
    return stable_finance_ref(
        "row-position-ref:finance/FIN-002",
        {"fixture_ref": fixture_ref, "position": position},
    )


def _quarantine(
    *, fixture_ref: str, position: int, reason: QuarantineReason
) -> ImportQuarantine:
    row_position_ref = _row_position_ref(fixture_ref, position)
    return ImportQuarantine(
        quarantine_ref=stable_finance_ref(
            "quarantine-ref:finance/FIN-002",
            {"row_position_ref": row_position_ref, "reason": reason.value},
        ),
        fixture_ref=fixture_ref,
        row_position_ref=row_position_ref,
        reason=reason,
    )


def _has_unsafe_cell(row: dict[str, str]) -> bool:
    return any(
        value.lstrip().startswith(("=", "+", "-", "@")) for value in row.values()
    )


def preview_synthetic_csv_fixture(
    fixture_ref: str,
    *,
    existing_fingerprint_refs: tuple[str, ...] = (),
) -> SyntheticImportPreview:
    """Preview one allowlisted fixture without accepting caller-supplied content."""

    fixture = _fixture_contract(fixture_ref)
    content = _SYNTHETIC_FIXTURE_CSV[fixture_ref]
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if tuple(reader.fieldnames or ()) != FIN002_EXACT_COLUMNS:
        raise FinanceImportPreviewError("FIN002_CSV_HEADER_MISMATCH")
    rows = list(reader)
    if not rows or len(rows) > FIN002_MAX_FIXTURE_ROWS:
        raise FinanceImportPreviewError("FIN002_CSV_ROW_COUNT_OUT_OF_RANGE")

    known_fingerprints = set(existing_fingerprint_refs)
    for ref in known_fingerprints:
        validate_task_ref(ref, "finance_import_existing_fingerprint_ref")
        validate_execution_ref(ref, "finance_import_existing_fingerprint_ref")
        if contains_obvious_secret(ref) or _SECRET_TOKEN_PREFIX.search(ref):
            raise ValueError("FIN002_EXISTING_FINGERPRINT_REF_UNSAFE")
    observations: list[SourceObservation] = []
    candidates: list[TransactionCandidate] = []
    duplicates: list[str] = []
    quarantines: list[ImportQuarantine] = []

    for position, row in enumerate(rows, start=1):
        if set(row) != set(FIN002_EXACT_COLUMNS) or None in row.values():
            quarantines.append(
                _quarantine(
                    fixture_ref=fixture_ref,
                    position=position,
                    reason=QuarantineReason.invalid_ref,
                )
            )
            continue
        if _has_unsafe_cell(row):
            quarantines.append(
                _quarantine(
                    fixture_ref=fixture_ref,
                    position=position,
                    reason=QuarantineReason.unsafe_cell,
                )
            )
            continue
        try:
            for name in ("row_ref", "date_ref", "counterparty_ref", "memo_ref"):
                validate_task_ref(row[name], f"finance_import_{name}")
        except ValueError:
            quarantines.append(
                _quarantine(
                    fixture_ref=fixture_ref,
                    position=position,
                    reason=QuarantineReason.invalid_ref,
                )
            )
            continue
        try:
            direction = ImportDirection(row["direction"])
        except ValueError:
            quarantines.append(
                _quarantine(
                    fixture_ref=fixture_ref,
                    position=position,
                    reason=QuarantineReason.invalid_direction,
                )
            )
            continue
        try:
            amount_minor = int(row["amount_minor"])
            if amount_minor <= 0 or amount_minor > 10**15:
                raise ValueError
        except ValueError:
            quarantines.append(
                _quarantine(
                    fixture_ref=fixture_ref,
                    position=position,
                    reason=QuarantineReason.invalid_amount,
                )
            )
            continue

        fingerprint_payload = {
            "fixture_profile_ref": fixture.profile_ref,
            "book_ref": fixture.book_ref,
            "account_ref": fixture.account_ref,
            "commodity_ref": fixture.commodity_ref,
            "date_ref": row["date_ref"],
            "direction": direction.value,
            "amount_minor": amount_minor,
            "counterparty_ref": row["counterparty_ref"],
            "memo_ref": row["memo_ref"],
        }
        fingerprint_ref = stable_finance_ref(
            "source-fingerprint-ref:finance/FIN-002", fingerprint_payload
        )
        if fingerprint_ref in known_fingerprints:
            duplicates.append(fingerprint_ref)
            continue
        known_fingerprints.add(fingerprint_ref)
        observation = SourceObservation(
            observation_ref=stable_finance_ref(
                "observation-ref:finance/FIN-002",
                {"fixture_ref": fixture_ref, "row_ref": row["row_ref"]},
            ),
            fixture_ref=fixture_ref,
            source_row_ref=row["row_ref"],
            book_ref=fixture.book_ref,
            account_ref=fixture.account_ref,
            commodity_ref=fixture.commodity_ref,
            date_ref=row["date_ref"],
            direction=direction,
            amount_minor=amount_minor,
            counterparty_ref=row["counterparty_ref"],
            memo_ref=row["memo_ref"],
            source_fingerprint_ref=fingerprint_ref,
        )
        observations.append(observation)
        candidates.append(
            TransactionCandidate(
                candidate_ref=stable_finance_ref(
                    "transaction-candidate-ref:finance/FIN-002",
                    {"observation_ref": observation.observation_ref},
                ),
                observation_ref=observation.observation_ref,
                book_ref=fixture.book_ref,
                account_ref=fixture.account_ref,
                commodity_ref=fixture.commodity_ref,
                direction=direction,
                amount_minor=amount_minor,
                evidence_refs=(observation.observation_ref, fingerprint_ref),
            )
        )

    candidate_refs = tuple(item.candidate_ref for item in candidates)
    preview_ref = _preview_ref(
        fixture_ref=fixture_ref,
        profile_ref=fixture.profile_ref,
        candidate_refs=candidate_refs,
        duplicate_fingerprint_refs=tuple(duplicates),
        quarantine_refs=tuple(item.quarantine_ref for item in quarantines),
    )
    rollback_proof = ImportRollbackProof(
        rollback_ref=_rollback_ref(
            preview_ref=preview_ref,
            candidate_refs=candidate_refs,
        ),
        preview_ref=preview_ref,
        affected_candidate_refs=candidate_refs,
    )
    result = SyntheticImportPreview(
        preview_ref=preview_ref,
        fixture_ref=fixture_ref,
        profile_ref=fixture.profile_ref,
        observations=tuple(observations),
        candidates=tuple(candidates),
        duplicate_fingerprint_refs=tuple(duplicates),
        quarantines=tuple(quarantines),
        rollback_proof=rollback_proof,
        row_count=len(rows),
        accepted_count=len(candidates),
        duplicate_count=len(duplicates),
        quarantine_count=len(quarantines),
    )
    expected = (
        fixture.expected_row_count,
        fixture.expected_accepted_count,
        fixture.expected_duplicate_count,
        fixture.expected_quarantine_count,
    )
    actual = (
        result.row_count,
        result.accepted_count,
        result.duplicate_count,
        result.quarantine_count,
    )
    if not existing_fingerprint_refs and actual != expected:
        raise FinanceImportPreviewError("FIN002_FIXTURE_EXPECTATION_MISMATCH")
    return result
