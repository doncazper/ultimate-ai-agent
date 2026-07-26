from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from scripts.verification.verification_contracts import VerificationRiskTier


RISK_MANIFEST_VERSION = "uaa_verification_risk_manifest.v1"
MAX_CHANGE_RECORDS = 512
MAX_UNSAFE_PATH_REFS = 512


class ChangeKind(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    TYPE_CHANGED = "type_changed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChangeRecord:
    kind: ChangeKind
    path_refs: tuple[str, ...]

    def validate(self) -> None:
        expected_count = (
            2 if self.kind in {ChangeKind.RENAMED, ChangeKind.COPIED} else 1
        )
        if len(self.path_refs) != expected_count:
            raise ValueError("VERIFICATION_CHANGE_RECORD_INVALID")
        for path in self.path_refs:
            normalize_repo_path(path)


@dataclass(frozen=True)
class RiskRule:
    rule_ref: str
    tier: VerificationRiskTier
    reason_ref: str
    surface_refs: tuple[str, ...]
    exact_paths: tuple[str, ...] = ()
    prefixes: tuple[str, ...] = ()
    suffixes: tuple[str, ...] = ()

    def matches(self, path: str) -> bool:
        if path in self.exact_paths:
            return True
        if not self.prefixes and not self.suffixes:
            return False
        prefix_match = not self.prefixes or any(
            path.startswith(prefix) for prefix in self.prefixes
        )
        suffix_match = not self.suffixes or any(
            path.endswith(suffix) for suffix in self.suffixes
        )
        return prefix_match and suffix_match


@dataclass(frozen=True)
class RiskSelection:
    tier: VerificationRiskTier
    change_records: tuple[ChangeRecord, ...]
    changed_path_refs: tuple[str, ...]
    matched_rule_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]
    surface_refs: tuple[str, ...]
    fail_closed: bool


CRITICAL_EXACT_PATHS = (
    "AGENTS.md",
    "Makefile",
    "SECURITY.md",
    "pyproject.toml",
    "uv.lock",
    "package-lock.json",
    "apps/control-center/package.json",
    "apps/control-center/package-lock.json",
    "apps/control-center/tsconfig.json",
    "apps/control-center/tsconfig.app.json",
    "apps/control-center/tsconfig.node.json",
    "apps/control-center/vite.config.ts",
    "scripts/run_foundation_gate.py",
    "scripts/verify_all.py",
    "scripts/verify_release_lanes.py",
    "scripts/verify_github_hosted_ci.py",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
)


RISK_RULES = (
    RiskRule(
        "risk-rule:release-critical-exact",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:release-critical",
        ("surface-ref:release",),
        exact_paths=CRITICAL_EXACT_PATHS,
    ),
    RiskRule(
        "risk-rule:verification-ci",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:verification-topology",
        ("surface-ref:verification", "surface-ref:ci"),
        prefixes=(".github/", "scripts/verification/", "docs/verification/"),
    ),
    RiskRule(
        "risk-rule:api-authority-boundary",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:api-authority-boundary",
        ("surface-ref:api", "surface-ref:security"),
        prefixes=("src/ultimate_ai_agent/api/",),
    ),
    RiskRule(
        "risk-rule:authority-security-execution",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:authority-security-execution",
        (
            "surface-ref:authority",
            "surface-ref:security",
            "surface-ref:execution",
        ),
        prefixes=(
            "src/ultimate_ai_agent/core/authority/",
            "src/ultimate_ai_agent/core/approvals/",
            "src/ultimate_ai_agent/core/execution/",
            "src/ultimate_ai_agent/core/gate/",
            "src/ultimate_ai_agent/core/policy/",
            "src/ultimate_ai_agent/core/security/",
            "src/ultimate_ai_agent/core/storage/",
            "src/ultimate_ai_agent/core/ledger/",
            "src/ultimate_ai_agent/core/web_access/",
            "src/ultimate_ai_agent/core/sandbox",
            "src/ultimate_ai_agent/core/evidence_signing/",
            "src/ultimate_ai_agent/core/communications/",
            "src/ultimate_ai_agent/api/idempotency.py",
            "src/ultimate_ai_agent/api/local_auth.py",
            "src/ultimate_ai_agent/api/rate_limits.py",
            "integrations/",
            "migrations/",
            "packaging/",
            "tools/macos/",
            "docs/api/",
            "docs/schemas/",
            "docs/network/",
        ),
        exact_paths=(
            "docs/capability_registry.md",
            "docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md",
        ),
    ),
    RiskRule(
        "risk-rule:persistence-exact",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:persistence",
        ("surface-ref:persistence",),
        exact_paths=(
            "src/ultimate_ai_agent/core/memory/store.py",
            "src/ultimate_ai_agent/core/memory/local_store.py",
            "src/ultimate_ai_agent/core/memory/l1_index.py",
            "src/ultimate_ai_agent/core/memory/l2_index.py",
            "src/ultimate_ai_agent/core/memory/l3_index.py",
            "src/ultimate_ai_agent/core/single_writer_lock.py",
        ),
    ),
    RiskRule(
        "risk-rule:governed-core-contracts",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:governed-core-contract",
        (
            "surface-ref:authority",
            "surface-ref:persistence",
            "surface-ref:providers",
            "surface-ref:extensions",
        ),
        prefixes=(
            "src/ultimate_ai_agent/core/memory/",
            "src/ultimate_ai_agent/core/providers/",
            "src/ultimate_ai_agent/core/extension_catalog/",
        ),
    ),
    RiskRule(
        "risk-rule:release-manifest",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:release-manifest",
        ("surface-ref:release",),
        prefixes=("docs/control_center/", "docs/roadmap/"),
        suffixes=("release_surface_manifest.json", "route_status_manifest.json"),
    ),
    RiskRule(
        "risk-rule:frontend-tooling",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:frontend-tooling",
        ("surface-ref:frontend", "surface-ref:dependencies"),
        prefixes=(
            "apps/control-center/tests/visual/",
            "apps/control-center/playwright",
        ),
    ),
    RiskRule(
        "risk-rule:api-and-frontend-contracts",
        VerificationRiskTier.TIER_2,
        "reason-ref:risk:bounded-contract",
        ("surface-ref:api", "surface-ref:frontend"),
        prefixes=(
            "apps/control-center/src/api/",
            "apps/control-center/src/hooks/",
        ),
    ),
    RiskRule(
        "risk-rule:bounded-frontend-behavior",
        VerificationRiskTier.TIER_2,
        "reason-ref:risk:bounded-frontend-behavior",
        ("surface-ref:frontend",),
        prefixes=("apps/control-center/src/",),
        suffixes=(".ts", ".tsx"),
    ),
    RiskRule(
        "risk-rule:bounded-python-core",
        VerificationRiskTier.TIER_2,
        "reason-ref:risk:bounded-core",
        ("surface-ref:python", "surface-ref:core"),
        exact_paths=(
            "src/ultimate_ai_agent/core/evals/capability_metrics.py",
            "src/ultimate_ai_agent/core/evals/capability_maturity.py",
            "src/ultimate_ai_agent/core/evals/regression.py",
        ),
    ),
    RiskRule(
        "risk-rule:shared-test-fixture",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:test-proof-changed",
        ("surface-ref:python-tests", "surface-ref:verification"),
        prefixes=("tests/fixtures/", "tests/conftest.py"),
    ),
    RiskRule(
        "risk-rule:python-test-proof",
        VerificationRiskTier.TIER_3,
        "reason-ref:risk:test-proof-changed",
        ("surface-ref:python-tests", "surface-ref:verification"),
        prefixes=("tests/test_",),
        suffixes=(".py",),
    ),
    RiskRule(
        "risk-rule:isolated-frontend-presentation",
        VerificationRiskTier.TIER_1,
        "reason-ref:risk:presentation",
        ("surface-ref:frontend",),
        exact_paths=("apps/control-center/src/styles.css",),
        prefixes=("apps/control-center/src/",),
        suffixes=(".css",),
    ),
    RiskRule(
        "risk-rule:inert-documentation",
        VerificationRiskTier.TIER_0,
        "reason-ref:risk:documentation",
        ("surface-ref:documentation",),
        exact_paths=("README.md", "VERSION.md"),
        prefixes=("docs/",),
        suffixes=(".md",),
    ),
    RiskRule(
        "risk-rule:inert-prompt-manifest",
        VerificationRiskTier.TIER_0,
        "reason-ref:risk:inert-prompt-bundle",
        ("surface-ref:documentation",),
        prefixes=("docs/prompts/",),
        suffixes=(".json",),
    ),
)


TIER_BASE_UNIT_REFS: dict[VerificationRiskTier, tuple[str, ...]] = {
    VerificationRiskTier.TIER_0: (
        "risk-diff-check",
        "risk-documentation",
        "risk-product-truth",
        "risk-redaction",
    ),
    VerificationRiskTier.TIER_1: (
        "risk-diff-check",
        "risk-product-truth",
        "risk-final-diff-audit",
    ),
    VerificationRiskTier.TIER_2: (
        "risk-diff-check",
        "risk-ruff",
        "risk-product-truth",
        "risk-redaction",
        "risk-final-diff-audit",
    ),
    VerificationRiskTier.TIER_3: (
        "risk-security-audit",
        "risk-final-diff-audit",
    ),
}


def normalize_repo_path(raw_path: str) -> str:
    if (
        not isinstance(raw_path, str)
        or not raw_path
        or len(raw_path) > 512
        or "\\" in raw_path
        or unicodedata.normalize("NFC", raw_path) != raw_path
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in raw_path
        )
    ):
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or ".." in path.parts
        or raw_path.startswith("./")
        or path.as_posix() != raw_path
        or any(
            not part or len(part) > 255 or part != part.strip() for part in path.parts
        )
    ):
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    return normalized


def _highest_tier(tiers: set[VerificationRiskTier]) -> VerificationRiskTier:
    return max(tiers, key=lambda tier: tier.rank)


def classify_changes(
    records: tuple[ChangeRecord, ...],
    *,
    force_full: bool = False,
    unsafe_path_refs: tuple[str, ...] = (),
) -> RiskSelection:
    if (
        len(records) > MAX_CHANGE_RECORDS
        or len(unsafe_path_refs) > MAX_UNSAFE_PATH_REFS
    ):
        raise ValueError("VERIFICATION_CHANGE_BOUND_EXCEEDED")
    normalized_unsafe = {normalize_repo_path(path) for path in unsafe_path_refs}
    if not records:
        tier = (
            VerificationRiskTier.TIER_3 if force_full else VerificationRiskTier.TIER_0
        )
        return RiskSelection(
            tier=tier,
            change_records=(),
            changed_path_refs=(),
            matched_rule_refs=("risk-rule:force-full",) if force_full else (),
            reason_refs=("reason-ref:risk:force-full",) if force_full else (),
            surface_refs=("surface-ref:release",) if force_full else (),
            fail_closed=force_full,
        )

    tiers: set[VerificationRiskTier] = set()
    rules: set[str] = set()
    reasons: set[str] = set()
    surfaces: set[str] = set()
    changed_paths: set[str] = set()
    observed_paths: set[str] = set()
    fail_closed = force_full
    for record in records:
        record.validate()
        for raw_path in record.path_refs:
            path = normalize_repo_path(raw_path)
            changed_paths.add(path)
            if path in observed_paths:
                tiers.add(VerificationRiskTier.TIER_3)
                reasons.add("reason-ref:risk:overlapping-change-records")
                fail_closed = True
            observed_paths.add(path)
            matches = tuple(rule for rule in RISK_RULES if rule.matches(path))
            if not matches:
                tiers.add(VerificationRiskTier.TIER_3)
                rules.add("risk-rule:unclassified")
                reasons.add("reason-ref:risk:unclassified-path")
                surfaces.add("surface-ref:unknown")
                fail_closed = True
                continue
            path_tiers = {rule.tier for rule in matches}
            tiers.add(_highest_tier(path_tiers))
            for rule in matches:
                rules.add(rule.rule_ref)
                reasons.add(rule.reason_ref)
                surfaces.update(rule.surface_refs)
            if len(path_tiers) > 1:
                tiers.add(VerificationRiskTier.TIER_3)
                reasons.add("reason-ref:risk:overlapping-rules-max-tier")
                fail_closed = True
            if path in normalized_unsafe:
                tiers.add(VerificationRiskTier.TIER_3)
                reasons.add("reason-ref:risk:unsafe-file-type")
                fail_closed = True
        if record.kind in {ChangeKind.DELETED, ChangeKind.RENAMED, ChangeKind.UNKNOWN}:
            tiers.add(VerificationRiskTier.TIER_3)
            reasons.add(f"reason-ref:risk:{record.kind.value}")
            fail_closed = True
        elif record.kind is ChangeKind.TYPE_CHANGED:
            tiers.add(VerificationRiskTier.TIER_3)
            reasons.add("reason-ref:risk:type-change")
            fail_closed = True

    if force_full:
        tiers.add(VerificationRiskTier.TIER_3)
        rules.add("risk-rule:force-full")
        reasons.add("reason-ref:risk:force-full")
        surfaces.add("surface-ref:release")
        fail_closed = True
    tier = _highest_tier(tiers)
    return RiskSelection(
        tier=tier,
        change_records=records,
        changed_path_refs=tuple(sorted(changed_paths)),
        matched_rule_refs=tuple(sorted(rules)),
        reason_refs=tuple(sorted(reasons)),
        surface_refs=tuple(sorted(surfaces)),
        fail_closed=fail_closed,
    )


def unit_refs_for_selection(
    selection: RiskSelection,
    *,
    full_unit_refs: tuple[str, ...],
) -> tuple[str, ...]:
    refs = set(TIER_BASE_UNIT_REFS[selection.tier])
    surfaces = set(selection.surface_refs)
    if selection.tier is VerificationRiskTier.TIER_3:
        refs.update(full_unit_refs)
    if "surface-ref:documentation" in surfaces:
        refs.add("risk-documentation")
    if (
        "surface-ref:frontend" in surfaces
        and selection.tier is not VerificationRiskTier.TIER_3
    ):
        refs.update(
            {
                "risk-frontend-typecheck",
                "risk-frontend-tests",
                "risk-frontend-build",
                "risk-frontend-safety",
            }
        )
    if (
        "surface-ref:python-tests" in surfaces
        and selection.tier is VerificationRiskTier.TIER_1
    ):
        refs.update({"risk-ruff", "risk-focused-pytest"})
    if (
        surfaces.intersection({"surface-ref:python", "surface-ref:core"})
        and selection.tier is VerificationRiskTier.TIER_2
    ):
        refs.add("risk-focused-pytest")
    if (
        "surface-ref:api" in surfaces
        and selection.tier is not VerificationRiskTier.TIER_3
    ):
        refs.update({"risk-openapi", "risk-api-safety"})
    return tuple(sorted(refs))


def audit_posture_for_tier(tier: VerificationRiskTier) -> str:
    return {
        VerificationRiskTier.TIER_0: "no_dedicated_audit",
        VerificationRiskTier.TIER_1: "one_scoped_ui_or_product_truth_audit",
        VerificationRiskTier.TIER_2: "one_final_scoped_diff_audit",
        VerificationRiskTier.TIER_3: "one_security_or_authority_and_one_final_diff_audit",
    }[tier]


def risk_definition_payload() -> dict[str, object]:
    return {
        "schema_version": RISK_MANIFEST_VERSION,
        "rules": [asdict(rule) for rule in RISK_RULES],
        "tier_base_unit_refs": {
            tier.value: list(refs) for tier, refs in TIER_BASE_UNIT_REFS.items()
        },
        "unknown_change_posture": VerificationRiskTier.TIER_3.value,
        "rename_delete_posture": VerificationRiskTier.TIER_3.value,
        "force_full_posture": VerificationRiskTier.TIER_3.value,
        "line_count_or_complexity_refactor_required": False,
        "redaction_status": "content_free_rules_and_repo_relative_paths_only",
    }


def risk_manifest_fingerprint() -> str:
    return hashlib.sha256(
        json.dumps(
            risk_definition_payload(), sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def change_fingerprint(records: tuple[ChangeRecord, ...]) -> str:
    return hashlib.sha256(
        json.dumps(
            [
                {"kind": record.kind.value, "path_refs": list(record.path_refs)}
                for record in records
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
