from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from scripts.verification.verification_contracts import (
    VerificationRiskTier,
    VerificationUnit,
    dependency_closed_unit_refs,
    validate_verification_dag,
)
from scripts.verification.verification_risk import (
    ChangeRecord,
    RiskSelection,
    classify_changes,
    normalize_repo_path,
    unit_refs_for_selection,
)


SCHEMA_VERSION = "uaa_verification_selection.v1"
MAX_OWNED_TEST_REFS = 256
SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")


@dataclass(frozen=True)
class TestOwnershipSelection:
    selected_test_refs: tuple[str, ...]
    missing_test_refs: tuple[str, ...]
    matched_ownership_rule_refs: tuple[str, ...]


@dataclass(frozen=True)
class VerificationSelection:
    schema_version: str
    risk_tier: VerificationRiskTier
    changed_path_refs: tuple[str, ...]
    matched_rule_refs: tuple[str, ...]
    escalation_reason_refs: tuple[str, ...]
    surface_refs: tuple[str, ...]
    selected_unit_refs: tuple[str, ...]
    selected_test_refs: tuple[str, ...]
    coverage_proof_obligation_refs: tuple[str, ...]
    matched_ownership_rule_refs: tuple[str, ...]
    fail_closed: bool
    full_gate_required: bool
    redaction_status: str
    selection_fingerprint: str

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "risk_tier": self.risk_tier.value,
            "changed_path_refs": list(self.changed_path_refs),
            "matched_rule_refs": list(self.matched_rule_refs),
            "escalation_reason_refs": list(self.escalation_reason_refs),
            "surface_refs": list(self.surface_refs),
            "selected_unit_refs": list(self.selected_unit_refs),
            "selected_test_refs": list(self.selected_test_refs),
            "coverage_proof_obligation_refs": list(
                self.coverage_proof_obligation_refs
            ),
            "matched_ownership_rule_refs": list(
                self.matched_ownership_rule_refs
            ),
            "fail_closed": self.fail_closed,
            "full_gate_required": self.full_gate_required,
            "redaction_status": self.redaction_status,
            "selection_fingerprint": self.selection_fingerprint,
        }

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("VERIFICATION_SELECTION_SCHEMA_INVALID")
        if not isinstance(self.risk_tier, VerificationRiskTier):
            raise ValueError("VERIFICATION_SELECTION_RISK_TIER_INVALID")
        for refs, label in (
            (self.matched_rule_refs, "risk rule"),
            (self.escalation_reason_refs, "escalation reason"),
            (self.surface_refs, "surface"),
            (self.selected_unit_refs, "verification unit"),
            (self.coverage_proof_obligation_refs, "coverage proof obligation"),
            (self.matched_ownership_rule_refs, "test ownership rule"),
        ):
            _validate_unique_safe_refs(refs, label=label)
        for path in (*self.changed_path_refs, *self.selected_test_refs):
            normalize_repo_path(path)
        if len(self.selected_test_refs) != len(set(self.selected_test_refs)):
            raise ValueError("VERIFICATION_SELECTION_TEST_REFS_DUPLICATE")
        if not isinstance(self.fail_closed, bool) or not isinstance(
            self.full_gate_required, bool
        ):
            raise ValueError("VERIFICATION_SELECTION_POSTURE_INVALID")
        if self.fail_closed and not self.full_gate_required:
            raise ValueError("VERIFICATION_SELECTION_FAIL_CLOSED_NOT_FULL")
        if (
            self.full_gate_required
            and self.risk_tier is not VerificationRiskTier.TIER_3
        ):
            raise ValueError("VERIFICATION_SELECTION_FULL_GATE_TIER_INVALID")
        if (
            self.redaction_status
            != "content_free_refs_and_repository_relative_paths_only"
        ):
            raise ValueError("VERIFICATION_SELECTION_REDACTION_INVALID")
        if not re.fullmatch(r"[0-9a-f]{64}", self.selection_fingerprint):
            raise ValueError("VERIFICATION_SELECTION_FINGERPRINT_INVALID")
        if self.selection_fingerprint != verification_selection_fingerprint(self):
            raise ValueError("VERIFICATION_SELECTION_FINGERPRINT_MISMATCH")


EXACT_SOURCE_TEST_OWNERSHIP: dict[str, tuple[str, ...]] = {
    "src/ultimate_ai_agent/core/evals/capability_metrics.py": (
        "tests/test_agent_capability_evaluation.py",
    ),
    "src/ultimate_ai_agent/core/evals/capability_maturity.py": (
        "tests/test_capability_maturity_integrity.py",
    ),
    "src/ultimate_ai_agent/core/evals/regression.py": (
        "tests/test_m56_agent_eval_regression_harness.py",
    ),
}

PREFIX_TEST_OWNERSHIP: tuple[
    tuple[str, tuple[str, ...], tuple[str, ...]], ...
] = (
    (
        "ownership-rule:authority",
        (
            "src/ultimate_ai_agent/core/authority/",
            "src/ultimate_ai_agent/core/approvals/",
            "src/ultimate_ai_agent/core/execution/",
            "src/ultimate_ai_agent/core/hygiene/",
        ),
        (
            "tests/test_authority_leases.py",
            "tests/test_authority_dispatcher.py",
        ),
    ),
    (
        "ownership-rule:api-contract",
        (
            "src/ultimate_ai_agent/api/",
            "docs/api/",
            "docs/schemas/api_",
            "tests/fixtures/api_route_",
        ),
        (
            "tests/test_api_manifest.py",
            "tests/test_api_route_inventory_fixture.py",
            "tests/test_openapi_contract.py",
        ),
    ),
    (
        "ownership-rule:web-hybrid",
        (
            "src/ultimate_ai_agent/core/web_access/",
            "docs/network/",
            "scripts/verify_web_hybrid",
            ".uaa/local-web-services/",
        ),
        (
            "tests/test_searxng_search.py",
            "tests/test_firecrawl_markdown.py",
            "tests/test_web_hybrid_execution.py",
        ),
    ),
    (
        "ownership-rule:memory",
        (
            "src/ultimate_ai_agent/core/memory/",
            "docs/memory/",
        ),
        (
            "tests/test_memory_store.py",
            "tests/test_memory_retrieval.py",
        ),
    ),
    (
        "ownership-rule:providers",
        ("src/ultimate_ai_agent/core/providers/",),
        (
            "tests/test_provider_manifests.py",
            "tests/test_provider_result_envelope.py",
        ),
    ),
    (
        "ownership-rule:extensions",
        (
            "src/ultimate_ai_agent/core/extension_catalog/",
            "docs/extensions/",
        ),
        (
            "tests/test_inspectable_extension_catalog.py",
            "tests/test_extension_catalog_storage_hardening.py",
        ),
    ),
)

API_PROOF_PATH_PREFIXES = (
    "src/ultimate_ai_agent/api/",
    "docs/api/",
    "docs/schemas/api_",
    "tests/fixtures/api_route_",
)
API_PROOF_EXACT_PATHS = frozenset(
    {
        "tests/test_api_manifest.py",
        "tests/test_api_route_inventory_fixture.py",
        "tests/test_openapi_contract.py",
    }
)

TIER_PROOF_OBLIGATIONS: dict[VerificationRiskTier, tuple[str, ...]] = {
    VerificationRiskTier.TIER_0: (
        "proof-obligation-ref:diff-integrity",
        "proof-obligation-ref:documentation-integrity",
        "proof-obligation-ref:product-truth",
        "proof-obligation-ref:security-redaction",
    ),
    VerificationRiskTier.TIER_1: (
        "proof-obligation-ref:diff-integrity",
        "proof-obligation-ref:product-truth",
        "proof-obligation-ref:final-diff-audit",
    ),
    VerificationRiskTier.TIER_2: (
        "proof-obligation-ref:diff-integrity",
        "proof-obligation-ref:python-lint",
        "proof-obligation-ref:product-truth",
        "proof-obligation-ref:security-redaction",
        "proof-obligation-ref:final-diff-audit",
    ),
    VerificationRiskTier.TIER_3: (
        "proof-obligation-ref:complete-pytest",
        "proof-obligation-ref:static-verification",
        "proof-obligation-ref:release-lanes",
        "proof-obligation-ref:foundation-gate",
        "proof-obligation-ref:security-audit",
        "proof-obligation-ref:final-diff-audit",
    ),
}


def _validate_unique_safe_refs(refs: tuple[str, ...], *, label: str) -> None:
    if len(refs) != len(set(refs)) or any(
        SAFE_REF_PATTERN.fullmatch(ref) is None for ref in refs
    ):
        raise ValueError(f"VERIFICATION_SELECTION_{label.upper().replace(' ', '_')}_INVALID")


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def verification_selection_fingerprint(selection: VerificationSelection) -> str:
    payload = selection.payload()
    payload.pop("selection_fingerprint")
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _safe_repository_root(repo: Path) -> None:
    try:
        metadata = repo.lstat()
    except OSError as exc:
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID") from exc
    if repo.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID")


def _safe_regular_repo_file(repo: Path, ref: str) -> bool:
    try:
        metadata = (repo / ref).lstat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _path_matches_prefix(path: str, prefix: str) -> bool:
    return path.startswith(prefix)


def select_owned_test_refs(
    paths: tuple[str, ...] | list[str],
    *,
    repo: Path,
) -> TestOwnershipSelection:
    _safe_repository_root(repo)
    normalized_paths = tuple(sorted({normalize_repo_path(path) for path in paths}))
    selected: set[str] = set()
    missing: set[str] = set()
    matched_rules: set[str] = set()

    for path in normalized_paths:
        candidates: set[str] = set()
        if path.startswith("tests/test_") and path.endswith(".py"):
            matched_rules.add("ownership-rule:direct-test")
            candidates.add(path)

        exact = EXACT_SOURCE_TEST_OWNERSHIP.get(path)
        if exact is not None:
            matched_rules.add("ownership-rule:exact-source")
            candidates.update(exact)

        for rule_ref, prefixes, test_refs in PREFIX_TEST_OWNERSHIP:
            if any(_path_matches_prefix(path, prefix) for prefix in prefixes):
                matched_rules.add(rule_ref)
                candidates.update(test_refs)

        if (
            not candidates
            and path.startswith("src/ultimate_ai_agent/")
            and path.endswith(".py")
        ):
            candidate = f"tests/test_{Path(path).stem}.py"
            matched_rules.add("ownership-rule:python-module-convention")
            candidates.add(candidate)

        for candidate in candidates:
            normalized_candidate = normalize_repo_path(candidate)
            if _safe_regular_repo_file(repo, normalized_candidate):
                selected.add(normalized_candidate)
            else:
                missing.add(normalized_candidate)

    if len(selected) + len(missing) > MAX_OWNED_TEST_REFS:
        raise ValueError("VERIFICATION_TEST_OWNERSHIP_BOUND_EXCEEDED")
    return TestOwnershipSelection(
        selected_test_refs=tuple(sorted(selected)),
        missing_test_refs=tuple(sorted(missing)),
        matched_ownership_rule_refs=tuple(sorted(matched_rules)),
    )


def _escalate_risk_selection(
    selection: RiskSelection,
    *,
    reason_ref: str,
    surface_ref: str,
) -> RiskSelection:
    return RiskSelection(
        tier=VerificationRiskTier.TIER_3,
        change_records=selection.change_records,
        changed_path_refs=selection.changed_path_refs,
        matched_rule_refs=tuple(
            sorted({*selection.matched_rule_refs, "risk-rule:selection-fail-closed"})
        ),
        reason_refs=tuple(sorted({*selection.reason_refs, reason_ref})),
        surface_refs=tuple(sorted({*selection.surface_refs, surface_ref})),
        fail_closed=True,
    )


def _coverage_proof_obligations(selection: RiskSelection) -> tuple[str, ...]:
    obligations = set(TIER_PROOF_OBLIGATIONS[selection.tier])
    surfaces = set(selection.surface_refs)
    paths = set(selection.changed_path_refs)

    if "surface-ref:documentation" in surfaces:
        obligations.add("proof-obligation-ref:documentation-integrity")
    if "surface-ref:frontend" in surfaces:
        obligations.update(
            {
                "proof-obligation-ref:typescript-typecheck",
                "proof-obligation-ref:frontend-unit-tests",
                "proof-obligation-ref:frontend-build",
                "proof-obligation-ref:frontend-safety",
            }
        )
    if surfaces.intersection({"surface-ref:python", "surface-ref:core"}):
        obligations.update(
            {
                "proof-obligation-ref:python-lint",
                "proof-obligation-ref:focused-pytest",
            }
        )
    if "surface-ref:python-tests" in surfaces:
        obligations.add("proof-obligation-ref:focused-pytest")
    if any(
        path in API_PROOF_EXACT_PATHS
        or any(path.startswith(prefix) for prefix in API_PROOF_PATH_PREFIXES)
        for path in paths
    ):
        obligations.update(
            {
                "proof-obligation-ref:api-contract-snapshot",
                "proof-obligation-ref:api-verifier-lane",
                "proof-obligation-ref:openapi-contract",
                "proof-obligation-ref:api-safety",
            }
        )
    return tuple(sorted(obligations))


def _build_selection(
    *,
    risk_selection: RiskSelection,
    selected_unit_refs: tuple[str, ...],
    ownership: TestOwnershipSelection,
) -> VerificationSelection:
    draft = VerificationSelection(
        schema_version=SCHEMA_VERSION,
        risk_tier=risk_selection.tier,
        changed_path_refs=risk_selection.changed_path_refs,
        matched_rule_refs=risk_selection.matched_rule_refs,
        escalation_reason_refs=risk_selection.reason_refs,
        surface_refs=risk_selection.surface_refs,
        selected_unit_refs=selected_unit_refs,
        selected_test_refs=ownership.selected_test_refs,
        coverage_proof_obligation_refs=_coverage_proof_obligations(risk_selection),
        matched_ownership_rule_refs=ownership.matched_ownership_rule_refs,
        fail_closed=risk_selection.fail_closed,
        full_gate_required=risk_selection.tier is VerificationRiskTier.TIER_3,
        redaction_status="content_free_refs_and_repository_relative_paths_only",
        selection_fingerprint="0" * 64,
    )
    result = VerificationSelection(
        **{
            **draft.__dict__,
            "selection_fingerprint": verification_selection_fingerprint(draft),
        }
    )
    result.validate()
    return result


def select_verification(
    change_records: tuple[ChangeRecord, ...],
    *,
    verification_dag: tuple[VerificationUnit, ...],
    full_unit_refs: tuple[str, ...],
    repo: Path,
    force_full: bool = False,
    unsafe_path_refs: tuple[str, ...] = (),
) -> VerificationSelection:
    _safe_repository_root(repo)
    validate_verification_dag(verification_dag)
    if len(full_unit_refs) != len(set(full_unit_refs)):
        raise ValueError("VERIFICATION_FULL_UNIT_REFS_DUPLICATE")
    known_unit_refs = {unit.unit_ref for unit in verification_dag}
    if unknown_full_refs := set(full_unit_refs) - known_unit_refs:
        raise ValueError(
            f"VERIFICATION_FULL_UNIT_REFS_UNKNOWN:{sorted(unknown_full_refs)}"
        )

    risk_selection = classify_changes(
        change_records,
        force_full=force_full,
        unsafe_path_refs=unsafe_path_refs,
    )
    ownership = select_owned_test_refs(
        risk_selection.changed_path_refs,
        repo=repo,
    )
    if ownership.missing_test_refs:
        risk_selection = _escalate_risk_selection(
            risk_selection,
            reason_ref="reason-ref:risk:missing-test-ownership",
            surface_ref="surface-ref:verification",
        )
        ownership = TestOwnershipSelection(
            selected_test_refs=(),
            missing_test_refs=ownership.missing_test_refs,
            matched_ownership_rule_refs=ownership.matched_ownership_rule_refs,
        )

    selected_unit_refs = unit_refs_for_selection(
        risk_selection,
        full_unit_refs=full_unit_refs,
    )
    if unknown_selected := set(selected_unit_refs) - known_unit_refs:
        raise ValueError(
            f"VERIFICATION_SELECTED_UNIT_REFS_UNKNOWN:{sorted(unknown_selected)}"
        )
    selected_unit_refs = dependency_closed_unit_refs(
        verification_dag,
        selected_unit_refs,
    )
    return _build_selection(
        risk_selection=risk_selection,
        selected_unit_refs=selected_unit_refs,
        ownership=ownership,
    )
