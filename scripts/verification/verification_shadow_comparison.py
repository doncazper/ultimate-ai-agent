#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.verification_contracts import (  # noqa: E402
    VerificationRiskTier,
    VerificationUnit,
)
from scripts.verification.verification_risk import (  # noqa: E402
    ChangeKind,
    ChangeRecord,
    normalize_repo_path,
)
from scripts.verification.verification_selection import select_verification  # noqa: E402


DEFAULT_BASELINE_PATH = ROOT / "docs/verification/selector_shadow_baseline.json"
BASELINE_SCHEMA_VERSION = "uaa_verification_selector_shadow_baseline.v1"
COMPARISON_SCHEMA_VERSION = "uaa_verification_selector_shadow_comparison.v1"
MAX_BASELINE_BYTES = 128 * 1024
MAX_CASES = 32
SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
BASELINE_FINGERPRINT_PREFIX = "shadow-baseline-fingerprint:sha256:"

ROOT_FIELDS = frozenset(
    {
        "schema_version",
        "baseline_ref",
        "comparison_posture",
        "source_ref",
        "cases",
        "fingerprint",
    }
)
CASE_FIELDS = frozenset(
    {
        "case_ref",
        "change_records",
        "unsafe_path_refs",
        "minimum_tier",
        "require_fail_closed",
        "require_full_gate",
        "required_proof_refs",
        "required_test_refs",
    }
)
CHANGE_FIELDS = frozenset({"kind", "path_refs"})


@dataclass(frozen=True)
class ShadowCaseResult:
    case_ref: str
    status: str
    actual_tier: str
    fail_closed: bool
    full_gate_required: bool
    missing_proof_refs: tuple[str, ...]
    missing_test_refs: tuple[str, ...]
    failure_refs: tuple[str, ...]
    selection_fingerprint: str

    def payload(self) -> dict[str, object]:
        return {
            "case_ref": self.case_ref,
            "status": self.status,
            "actual_tier": self.actual_tier,
            "fail_closed": self.fail_closed,
            "full_gate_required": self.full_gate_required,
            "missing_proof_refs": list(self.missing_proof_refs),
            "missing_test_refs": list(self.missing_test_refs),
            "failure_refs": list(self.failure_refs),
            "selection_fingerprint": self.selection_fingerprint,
        }


@dataclass(frozen=True)
class ShadowComparison:
    schema_version: str
    baseline_ref: str
    baseline_fingerprint: str
    status: str
    case_results: tuple[ShadowCaseResult, ...]
    redaction_status: str
    comparison_fingerprint: str

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "baseline_ref": self.baseline_ref,
            "baseline_fingerprint": self.baseline_fingerprint,
            "status": self.status,
            "case_results": [result.payload() for result in self.case_results],
            "redaction_status": self.redaction_status,
            "comparison_fingerprint": self.comparison_fingerprint,
        }


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def baseline_fingerprint(payload: dict[str, object]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "fingerprint"}
    return BASELINE_FINGERPRINT_PREFIX + hashlib.sha256(
        _canonical_bytes(unsigned)
    ).hexdigest()


def shadow_comparison_fingerprint(comparison: ShadowComparison) -> str:
    payload = comparison.payload()
    payload.pop("comparison_fingerprint")
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _safe_ref(value: object, *, label: str) -> str:
    if not isinstance(value, str) or SAFE_REF_PATTERN.fullmatch(value) is None:
        raise ValueError(f"SHADOW_BASELINE_{label}_INVALID")
    return value


def _safe_ref_tuple(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"SHADOW_BASELINE_{label}_INVALID")
    refs = tuple(_safe_ref(ref, label=label) for ref in value)
    if len(refs) != len(set(refs)):
        raise ValueError(f"SHADOW_BASELINE_{label}_DUPLICATE")
    return refs


def _reject_executable_content(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(token in key.lower() for token in ("command", "argv", "shell")):
                raise ValueError("SHADOW_BASELINE_EXECUTABLE_CONTENT_FORBIDDEN")
            _reject_executable_content(item)
    elif isinstance(value, list):
        for item in value:
            _reject_executable_content(item)
    elif isinstance(value, str) and value.startswith("command:"):
        raise ValueError("SHADOW_BASELINE_EXECUTABLE_CONTENT_FORBIDDEN")


def validate_baseline(payload: dict[str, object]) -> None:
    if set(payload) != ROOT_FIELDS:
        raise ValueError("SHADOW_BASELINE_ROOT_FIELDS_INVALID")
    if payload.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError("SHADOW_BASELINE_SCHEMA_INVALID")
    _safe_ref(payload.get("baseline_ref"), label="REF")
    if payload.get("comparison_posture") != (
        "legacy_lower_bound_proof_obligations_only"
    ):
        raise ValueError("SHADOW_BASELINE_POSTURE_INVALID")
    source_ref = payload.get("source_ref")
    if not isinstance(source_ref, str):
        raise ValueError("SHADOW_BASELINE_SOURCE_INVALID")
    normalize_repo_path(source_ref)
    _reject_executable_content(payload)

    cases = payload.get("cases")
    if not isinstance(cases, list) or not 0 < len(cases) <= MAX_CASES:
        raise ValueError("SHADOW_BASELINE_CASES_INVALID")
    case_refs: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != CASE_FIELDS:
            raise ValueError("SHADOW_BASELINE_CASE_FIELDS_INVALID")
        case_ref = _safe_ref(case.get("case_ref"), label="CASE_REF")
        if case_ref in case_refs:
            raise ValueError("SHADOW_BASELINE_CASE_REF_DUPLICATE")
        case_refs.add(case_ref)
        records = case.get("change_records")
        if not isinstance(records, list) or not records:
            raise ValueError("SHADOW_BASELINE_CHANGE_RECORDS_INVALID")
        for record in records:
            if not isinstance(record, dict) or set(record) != CHANGE_FIELDS:
                raise ValueError("SHADOW_BASELINE_CHANGE_FIELDS_INVALID")
            try:
                kind = ChangeKind(record.get("kind"))
            except (TypeError, ValueError) as exc:
                raise ValueError("SHADOW_BASELINE_CHANGE_KIND_INVALID") from exc
            path_refs = record.get("path_refs")
            if not isinstance(path_refs, list):
                raise ValueError("SHADOW_BASELINE_PATH_REFS_INVALID")
            parsed = ChangeRecord(kind, tuple(path_refs))
            parsed.validate()
        unsafe_paths = case.get("unsafe_path_refs")
        if not isinstance(unsafe_paths, list):
            raise ValueError("SHADOW_BASELINE_UNSAFE_PATHS_INVALID")
        for path in unsafe_paths:
            normalize_repo_path(path)
        try:
            VerificationRiskTier(case.get("minimum_tier"))
        except (TypeError, ValueError) as exc:
            raise ValueError("SHADOW_BASELINE_MINIMUM_TIER_INVALID") from exc
        if not isinstance(case.get("require_fail_closed"), bool) or not isinstance(
            case.get("require_full_gate"), bool
        ):
            raise ValueError("SHADOW_BASELINE_POSTURE_FIELDS_INVALID")
        _safe_ref_tuple(case.get("required_proof_refs"), label="PROOF_REFS")
        required_tests = case.get("required_test_refs")
        if not isinstance(required_tests, list):
            raise ValueError("SHADOW_BASELINE_TEST_REFS_INVALID")
        normalized_tests = tuple(normalize_repo_path(ref) for ref in required_tests)
        if len(normalized_tests) != len(set(normalized_tests)):
            raise ValueError("SHADOW_BASELINE_TEST_REFS_DUPLICATE")

    fingerprint = payload.get("fingerprint")
    if (
        not isinstance(fingerprint, str)
        or fingerprint != baseline_fingerprint(payload)
    ):
        raise ValueError("SHADOW_BASELINE_FINGERPRINT_INVALID")


def load_baseline(path: Path = DEFAULT_BASELINE_PATH) -> dict[str, object]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError("SHADOW_BASELINE_FILE_INVALID") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or not 0 < metadata.st_size <= MAX_BASELINE_BYTES
    ):
        raise ValueError("SHADOW_BASELINE_FILE_INVALID")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("SHADOW_BASELINE_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise ValueError("SHADOW_BASELINE_ROOT_INVALID")
    validate_baseline(payload)
    return payload


def _records(case: dict[str, object]) -> tuple[ChangeRecord, ...]:
    return tuple(
        ChangeRecord(
            kind=ChangeKind(record["kind"]),
            path_refs=tuple(record["path_refs"]),
        )
        for record in case["change_records"]
    )


def _compare_case(
    case: dict[str, object],
    *,
    verification_dag: tuple[VerificationUnit, ...],
    full_unit_refs: tuple[str, ...],
    repo: Path,
) -> ShadowCaseResult:
    case_ref = str(case["case_ref"])
    try:
        selection = select_verification(
            _records(case),
            verification_dag=verification_dag,
            full_unit_refs=full_unit_refs,
            repo=repo,
            unsafe_path_refs=tuple(case["unsafe_path_refs"]),
        )
    except ValueError:
        return ShadowCaseResult(
            case_ref=case_ref,
            status="failed",
            actual_tier="unknown",
            fail_closed=True,
            full_gate_required=True,
            missing_proof_refs=tuple(case["required_proof_refs"]),
            missing_test_refs=tuple(case["required_test_refs"]),
            failure_refs=("shadow-failure-ref:selection-error",),
            selection_fingerprint="0" * 64,
        )

    required_tier = VerificationRiskTier(case["minimum_tier"])
    missing_proof_refs = tuple(
        sorted(
            set(case["required_proof_refs"])
            - set(selection.coverage_proof_obligation_refs)
        )
    )
    missing_test_refs = tuple(
        sorted(set(case["required_test_refs"]) - set(selection.selected_test_refs))
    )
    failures: set[str] = set()
    if selection.risk_tier.rank < required_tier.rank:
        failures.add("shadow-failure-ref:risk-tier-weaker")
    if case["require_fail_closed"] and not selection.fail_closed:
        failures.add("shadow-failure-ref:fail-closed-lost")
    if case["require_full_gate"] and not selection.full_gate_required:
        failures.add("shadow-failure-ref:full-gate-lost")
    if missing_proof_refs:
        failures.add("shadow-failure-ref:proof-coverage-lost")
    if missing_test_refs:
        failures.add("shadow-failure-ref:test-ownership-lost")
    return ShadowCaseResult(
        case_ref=case_ref,
        status="failed" if failures else "passed",
        actual_tier=selection.risk_tier.value,
        fail_closed=selection.fail_closed,
        full_gate_required=selection.full_gate_required,
        missing_proof_refs=missing_proof_refs,
        missing_test_refs=missing_test_refs,
        failure_refs=tuple(sorted(failures)),
        selection_fingerprint=selection.selection_fingerprint,
    )


def compare_shadow_baseline(
    *,
    verification_dag: tuple[VerificationUnit, ...],
    full_unit_refs: tuple[str, ...],
    repo: Path,
    baseline: dict[str, object] | None = None,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
) -> ShadowComparison:
    baseline_payload = load_baseline(baseline_path) if baseline is None else baseline
    validate_baseline(baseline_payload)
    case_results = tuple(
        _compare_case(
            case,
            verification_dag=verification_dag,
            full_unit_refs=full_unit_refs,
            repo=repo,
        )
        for case in baseline_payload["cases"]
    )
    draft = ShadowComparison(
        schema_version=COMPARISON_SCHEMA_VERSION,
        baseline_ref=str(baseline_payload["baseline_ref"]),
        baseline_fingerprint=str(baseline_payload["fingerprint"]),
        status=(
            "passed"
            if all(result.status == "passed" for result in case_results)
            else "failed"
        ),
        case_results=case_results,
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        comparison_fingerprint="0" * 64,
    )
    return ShadowComparison(
        **{
            **draft.__dict__,
            "comparison_fingerprint": shadow_comparison_fingerprint(draft),
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare canonical risk selection with the bounded legacy lower bound."
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    from scripts.verification.ci_command_manifest import (  # noqa: PLC0415
        CI_JOB_GRAPH,
        VERIFICATION_DAG,
    )

    comparison = compare_shadow_baseline(
        verification_dag=VERIFICATION_DAG,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        repo=ROOT,
        baseline_path=args.baseline,
    )
    if args.json:
        print(json.dumps(comparison.payload(), indent=2, sort_keys=True))
    else:
        print("UAA bounded verification selector shadow comparison")
        print(f"Status: {comparison.status}")
        print(f"Cases: {len(comparison.case_results)}")
        for result in comparison.case_results:
            print(f"  {result.case_ref}: {result.status} ({result.actual_tier})")
    return 0 if comparison.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
