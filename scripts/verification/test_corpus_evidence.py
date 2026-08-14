"""Content-bound evidence contracts for test-corpus retirements."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ASSERTION_EQUIVALENCE_REF_PATTERN = re.compile(
    r"assertion-equivalence-ref:sha256:[0-9a-f]{64}"
)
TEST_CORPUS_EVIDENCE_REF_PATTERN = re.compile(
    r"test-corpus-evidence-ref:sha256:[0-9a-f]{64}"
)
ASSERTION_REF_PATTERN = re.compile(r"assertion-ref:sha256:[0-9a-f]{64}")
TEST_RESULT_REF_PATTERN = re.compile(r"test-result-ref:sha256:[0-9a-f]{64}")
TEST_SOURCE_REF_PATTERN = re.compile(r"test-source-ref:sha256:[0-9a-f]{64}")
ASSERTION_EQUIVALENCE_SCHEMA = "uaa.test_corpus_assertion_equivalence.v1"
RETIREMENT_EVIDENCE_SCHEMA = "uaa.test_corpus_retirement_evidence.v1"
ASSERTION_EVIDENCE_SCHEMA = "uaa.test_corpus_assertion_evidence.v1"
TEST_RESULT_EVIDENCE_SCHEMA = "uaa.test_corpus_test_result_evidence.v1"
MAX_ARTIFACT_BYTES = 450_000
MAX_ARTIFACT_REFS = 64
UNSAFE_DURABLE_PROSE_PATTERNS = (
    re.compile(r"(?i)\braw[\s_-]?(?:prompt|response|provider|payload|log|path)\b"),
    re.compile(r"(?i)\b(?:username|hostname|serial)\b"),
    re.compile(r"(?i)\benv(?:ironment)?[\s_-]?dump\b"),
    re.compile(
        r"(?<![A-Za-z0-9:/])/(?!/)(?:[^\s/]+/)*[^\s/]+(?=$|\s)"
        r"|[A-Za-z]:[\\/]|\\\\[^\\]+\\"
    ),
)


class TestCorpusEvidenceError(RuntimeError):
    """Raised when retirement evidence is malformed or unbound."""


def retirement_artifact_ref(prefix: str, artifact: dict[str, Any]) -> str:
    if prefix not in {
        "assertion-ref",
        "assertion-equivalence-ref",
        "test-result-ref",
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


def _validate_safe_prose(value: object, *, label: str) -> None:
    if (
        not isinstance(value, str)
        or not 20 <= len(value.strip()) <= 500
        or any(ord(character) < 32 for character in value)
        or contains_secret_like(value)
        or contains_obvious_secret(value)
        or any(pattern.search(value) for pattern in UNSAFE_DURABLE_PROSE_PATTERNS)
    ):
        raise TestCorpusEvidenceError(f"retired test {label} is invalid")


def _validate_content_bound_evidence(
    value: object,
    *,
    pattern: re.Pattern[str],
    prefix: str,
    schema: str,
    label: str,
    replacement_refs: list[str],
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > MAX_ARTIFACT_REFS
        or any(not isinstance(item, dict) for item in value)
    ):
        raise TestCorpusEvidenceError(f"retired test {label} is invalid")
    refs: list[str] = []
    covered_replacements: set[str] = set()
    for item in value:
        if set(item) != {"artifact", "ref"}:
            raise TestCorpusEvidenceError(f"retired test {label} is invalid")
        artifact = item.get("artifact")
        ref = item.get("ref")
        expected_keys = {"schema_version", "replacement_ref", "source_ref"}
        if prefix == "test-result-ref":
            expected_keys.remove("replacement_ref")
            expected_keys.remove("source_ref")
            expected_keys.add("verified_refs")
            expected_keys.add("verification_envelope")
        if (
            not isinstance(artifact, dict)
            or set(artifact) != expected_keys
            or artifact.get("schema_version") != schema
            or (
                prefix == "assertion-ref"
                and artifact.get("replacement_ref") not in replacement_refs
            )
            or (
                prefix == "test-result-ref"
                and artifact.get("verified_refs") != replacement_refs
            )
        ):
            raise TestCorpusEvidenceError(f"retired test {label} is invalid")
        if prefix == "assertion-ref":
            replacement_ref = str(artifact.get("replacement_ref"))
            source_ref = artifact.get("source_ref")
            if (
                not isinstance(source_ref, str)
                or TEST_SOURCE_REF_PATTERN.fullmatch(source_ref) is None
                or source_ref != resolve_assertion_source_ref(replacement_ref)
            ):
                raise TestCorpusEvidenceError(f"retired test {label} is invalid")
            covered_replacements.add(replacement_ref)
        else:
            verification_envelope = artifact.get("verification_envelope")
            if not isinstance(verification_envelope, str):
                raise TestCorpusEvidenceError(f"retired test {label} is invalid")
            try:
                validate_verification_envelope(
                    verification_envelope,
                    replacement_refs,
                )
            except TestCorpusEvidenceError:
                raise
            except (TypeError, ValueError):
                raise TestCorpusEvidenceError(
                    f"retired test {label} is invalid"
                ) from None
        if (
            not isinstance(ref, str)
            or pattern.fullmatch(ref) is None
            or ref != retirement_artifact_ref(prefix, artifact)
        ):
            raise TestCorpusEvidenceError(f"retired test {label} is invalid")
        refs.append(ref)
    if len(refs) != len(set(refs)):
        raise TestCorpusEvidenceError(f"retired test {label} is invalid")
    if prefix == "assertion-ref" and covered_replacements != set(replacement_refs):
        raise TestCorpusEvidenceError(f"retired test {label} is invalid")
    return value


def _validate_retirement_record(
    record: object,
    *,
    validate_test_ref: Callable[[str], None],
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
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
    try:
        _validate_safe_prose(reason, label="reason")
    except TestCorpusEvidenceError:
        raise TestCorpusEvidenceError(f"retired test reason is too weak: {retired_ref}")

    expected_equivalence_keys = {
        "schema_version",
        "retired_ref",
        "replacement_refs",
        "preserved_assertion_evidence",
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
    _validate_content_bound_evidence(
        equivalence_artifact.get("preserved_assertion_evidence"),
        pattern=ASSERTION_REF_PATTERN,
        prefix="assertion-ref",
        schema=ASSERTION_EVIDENCE_SCHEMA,
        label="preserved assertion evidence",
        replacement_refs=replacements,
        resolve_assertion_source_ref=resolve_assertion_source_ref,
        validate_verification_envelope=validate_verification_envelope,
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
        "verification_evidence",
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
    _validate_content_bound_evidence(
        evidence_artifact.get("verification_evidence"),
        pattern=TEST_RESULT_REF_PATTERN,
        prefix="test-result-ref",
        schema=TEST_RESULT_EVIDENCE_SCHEMA,
        label="verification evidence",
        replacement_refs=replacements,
        resolve_assertion_source_ref=resolve_assertion_source_ref,
        validate_verification_envelope=validate_verification_envelope,
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
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
) -> dict[str, dict[str, Any]]:
    records = ledger.get("retirements")
    if not isinstance(records, list):
        raise TestCorpusEvidenceError("test-corpus retirements must be a list")
    by_retired_ref: dict[str, dict[str, Any]] = {}
    for raw_record in records:
        retired_ref, record = _validate_retirement_record(
            raw_record,
            validate_test_ref=validate_test_ref,
            resolve_assertion_source_ref=resolve_assertion_source_ref,
            validate_verification_envelope=validate_verification_envelope,
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
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
    base_ledger: dict[str, Any] | None = None,
) -> int:
    by_retired_ref = _validated_retirement_records(
        ledger,
        validate_test_ref=validate_test_ref,
        resolve_assertion_source_ref=resolve_assertion_source_ref,
        validate_verification_envelope=validate_verification_envelope,
    )
    historical = (
        _validated_retirement_records(
            base_ledger,
            validate_test_ref=validate_test_ref,
            resolve_assertion_source_ref=resolve_assertion_source_ref,
            validate_verification_envelope=validate_verification_envelope,
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
    if base_ledger is not None:
        unexpected = sorted(new_retired_refs - removed_refs)
        if unexpected:
            raise TestCorpusEvidenceError(
                f"retirement records do not match removed tests: {unexpected}"
            )

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

    resolved_active: set[str] = set()

    def reaches_active(ref: str, visiting: frozenset[str]) -> bool:
        if ref in current_refs:
            return True
        if ref in visiting or ref not in by_retired_ref:
            return False
        if ref in resolved_active:
            return True
        outcome = any(
            reaches_active(replacement, visiting | {ref})
            for replacement in by_retired_ref[ref]["replacement_refs"]
        )
        if outcome:
            resolved_active.add(ref)
        return outcome

    for retired_ref in by_retired_ref:
        if not reaches_active(retired_ref, frozenset()):
            raise TestCorpusEvidenceError(
                f"retired test has no active replacement: {retired_ref}"
            )

    unaccounted = sorted(removed_refs - set(by_retired_ref))
    if unaccounted:
        raise TestCorpusEvidenceError(
            f"removed tests lack retirement/replacement evidence: {unaccounted}"
        )
    return len(by_retired_ref)
