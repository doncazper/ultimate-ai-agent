"""Content-bound evidence contracts for test-corpus retirements."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any


ASSERTION_EQUIVALENCE_REF_PATTERN = re.compile(
    r"assertion-equivalence-ref:sha256:[0-9a-f]{64}"
)
TEST_CORPUS_EVIDENCE_REF_PATTERN = re.compile(
    r"test-corpus-evidence-ref:sha256:[0-9a-f]{64}"
)
ASSERTION_REF_PATTERN = re.compile(r"assertion-ref:sha256:[0-9a-f]{64}")
TEST_RESULT_REF_PATTERN = re.compile(r"test-result-ref:sha256:[0-9a-f]{64}")
ASSERTION_EQUIVALENCE_SCHEMA = "uaa.test_corpus_assertion_equivalence.v1"
RETIREMENT_EVIDENCE_SCHEMA = "uaa.test_corpus_retirement_evidence.v1"
MAX_ARTIFACT_BYTES = 50_000
MAX_ARTIFACT_REFS = 64


class TestCorpusEvidenceError(RuntimeError):
    """Raised when retirement evidence is malformed or unbound."""


def retirement_artifact_ref(prefix: str, artifact: dict[str, Any]) -> str:
    if prefix not in {
        "assertion-equivalence-ref",
        "test-corpus-evidence-ref",
    }:
        raise TestCorpusEvidenceError("retirement artifact ref prefix is invalid")
    encoded = json.dumps(
        artifact,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(encoded) > MAX_ARTIFACT_BYTES:
        raise TestCorpusEvidenceError("retirement artifact exceeds byte budget")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_artifact_ref_list(
    value: object,
    *,
    pattern: re.Pattern[str],
    label: str,
) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > MAX_ARTIFACT_REFS
        or any(not isinstance(item, str) for item in value)
        or len(value) != len(set(value))
        or any(pattern.fullmatch(item) is None for item in value)
    ):
        raise TestCorpusEvidenceError(f"retired test {label} are invalid")
    return value


def _validate_retirement_record(
    record: object,
    *,
    validate_test_ref: Callable[[str], None],
) -> tuple[str, dict[str, Any]]:
    if not isinstance(record, dict):
        raise TestCorpusEvidenceError("test-corpus retirement record must be an object")
    if set(record) != {
        "retired_ref",
        "replacement_refs",
        "reason",
        "assertion_equivalence_artifact",
        "assertion_equivalence_ref",
        "evidence_artifact",
        "evidence_ref",
    }:
        raise TestCorpusEvidenceError(
            "test-corpus retirement record fields are invalid"
        )
    retired_ref = record.get("retired_ref")
    replacements = record.get("replacement_refs")
    reason = record.get("reason")
    equivalence_artifact = record.get("assertion_equivalence_artifact")
    equivalence_ref = record.get("assertion_equivalence_ref")
    evidence_artifact = record.get("evidence_artifact")
    evidence_ref = record.get("evidence_ref")
    if not isinstance(retired_ref, str):
        raise TestCorpusEvidenceError("retired test ref is invalid")
    validate_test_ref(retired_ref)
    if (
        not isinstance(replacements, list)
        or not replacements
        or len(replacements) > MAX_ARTIFACT_REFS
        or any(not isinstance(item, str) for item in replacements)
        or len(replacements) != len(set(replacements))
    ):
        raise TestCorpusEvidenceError(
            f"replacement refs are invalid for retired test: {retired_ref}"
        )
    for replacement in replacements:
        try:
            validate_test_ref(replacement)
        except TestCorpusEvidenceError:
            raise TestCorpusEvidenceError(
                f"replacement refs are invalid for retired test: {retired_ref}"
            ) from None
    if (
        not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 500
        or any(ord(character) < 32 for character in reason)
    ):
        raise TestCorpusEvidenceError(f"retired test reason is too weak: {retired_ref}")

    expected_equivalence_keys = {
        "schema_version",
        "retired_ref",
        "replacement_refs",
        "preserved_assertion_refs",
    }
    if (
        not isinstance(equivalence_artifact, dict)
        or set(equivalence_artifact) != expected_equivalence_keys
        or equivalence_artifact.get("schema_version") != ASSERTION_EQUIVALENCE_SCHEMA
        or equivalence_artifact.get("retired_ref") != retired_ref
        or equivalence_artifact.get("replacement_refs") != replacements
    ):
        raise TestCorpusEvidenceError(
            f"retired test equivalence artifact is invalid: {retired_ref}"
        )
    _validate_artifact_ref_list(
        equivalence_artifact.get("preserved_assertion_refs"),
        pattern=ASSERTION_REF_PATTERN,
        label="preserved assertion refs",
    )
    if (
        not isinstance(equivalence_ref, str)
        or ASSERTION_EQUIVALENCE_REF_PATTERN.fullmatch(equivalence_ref) is None
        or equivalence_ref
        != retirement_artifact_ref(
            "assertion-equivalence-ref",
            equivalence_artifact,
        )
    ):
        raise TestCorpusEvidenceError(
            f"retired test equivalence ref is invalid: {retired_ref}"
        )

    expected_evidence_keys = {
        "schema_version",
        "retired_ref",
        "replacement_refs",
        "verification_refs",
    }
    if (
        not isinstance(evidence_artifact, dict)
        or set(evidence_artifact) != expected_evidence_keys
        or evidence_artifact.get("schema_version") != RETIREMENT_EVIDENCE_SCHEMA
        or evidence_artifact.get("retired_ref") != retired_ref
        or evidence_artifact.get("replacement_refs") != replacements
    ):
        raise TestCorpusEvidenceError(
            f"retired test evidence artifact is invalid: {retired_ref}"
        )
    _validate_artifact_ref_list(
        evidence_artifact.get("verification_refs"),
        pattern=TEST_RESULT_REF_PATTERN,
        label="verification refs",
    )
    if (
        not isinstance(evidence_ref, str)
        or TEST_CORPUS_EVIDENCE_REF_PATTERN.fullmatch(evidence_ref) is None
        or evidence_ref
        != retirement_artifact_ref(
            "test-corpus-evidence-ref",
            evidence_artifact,
        )
    ):
        raise TestCorpusEvidenceError(
            f"retired test evidence ref is invalid: {retired_ref}"
        )
    return retired_ref, record


def _validated_retirement_records(
    ledger: dict[str, Any],
    *,
    validate_test_ref: Callable[[str], None],
) -> dict[str, dict[str, Any]]:
    records = ledger.get("retirements")
    if not isinstance(records, list):
        raise TestCorpusEvidenceError("test-corpus retirements must be a list")
    by_retired_ref: dict[str, dict[str, Any]] = {}
    for raw_record in records:
        retired_ref, record = _validate_retirement_record(
            raw_record,
            validate_test_ref=validate_test_ref,
        )
        if retired_ref in by_retired_ref:
            raise TestCorpusEvidenceError(f"duplicate retired test ref: {retired_ref}")
        by_retired_ref[retired_ref] = record
    return by_retired_ref


def validate_retirements(
    current_refs: set[str],
    removed_refs: set[str],
    ledger: dict[str, Any],
    *,
    validate_test_ref: Callable[[str], None],
    base_ledger: dict[str, Any] | None = None,
) -> int:
    by_retired_ref = _validated_retirement_records(
        ledger,
        validate_test_ref=validate_test_ref,
    )
    historical = (
        _validated_retirement_records(
            base_ledger,
            validate_test_ref=validate_test_ref,
        )
        if base_ledger is not None
        else {}
    )
    for retired_ref, historical_record in historical.items():
        if by_retired_ref.get(retired_ref) != historical_record:
            raise TestCorpusEvidenceError(
                f"historical retirement record changed: {retired_ref}"
            )
    new_retired_refs = set(by_retired_ref) - set(historical)

    for retired_ref, record in by_retired_ref.items():
        if retired_ref in current_refs:
            raise TestCorpusEvidenceError(
                f"retired test is still active: {retired_ref}"
            )
        replacements = set(record["replacement_refs"])
        missing = sorted(replacements - current_refs - set(by_retired_ref))
        if missing:
            raise TestCorpusEvidenceError(
                f"retired test has missing replacements: {retired_ref}: {missing}"
            )
        if retired_ref in new_retired_refs and not replacements & current_refs:
            raise TestCorpusEvidenceError(
                f"retired test has no active replacement: {retired_ref}"
            )

    unaccounted = sorted(removed_refs - set(by_retired_ref))
    if unaccounted:
        raise TestCorpusEvidenceError(
            f"removed tests lack retirement/replacement evidence: {unaccounted}"
        )
    return len(by_retired_ref)
