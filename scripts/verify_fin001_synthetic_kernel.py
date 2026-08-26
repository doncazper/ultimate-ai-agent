#!/usr/bin/env python3
"""Verify the bounded FIN-001 synthetic protected-book implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.finance.authority import (  # noqa: E402
    FINANCE_EXACT_AUTHORITY_BINDINGS,
    FINANCE_EXACT_TARGET_REF,
    build_finance_mutation_capability_manifest,
)
from ultimate_ai_agent.core.finance.authority_surfaces import (  # noqa: E402
    build_finance_synthetic_book_authority_mapping,
)
from ultimate_ai_agent.core.finance.fixtures import (  # noqa: E402
    load_finance_fixture,
    load_finance_fixture_manifest,
)


EXPECTED_MANIFEST_REF = (
    "fixture-manifest-ref:finance/FIN-001:sha256:"
    "b4d927f85c4b0edda60860be4387c7b9d3da1a4c23e00b18012708a61264833b"
)
EXPECTED_FLOWS = {
    "opening_balance",
    "transfer",
    "split",
    "adjustment",
    "reversal",
    "suspense",
}
REQUIRED_PATHS = (
    "src/ultimate_ai_agent/core/finance/models.py",
    "src/ultimate_ai_agent/core/finance/fixtures.py",
    "src/ultimate_ai_agent/core/finance/crypto.py",
    "src/ultimate_ai_agent/core/finance/repository.py",
    "src/ultimate_ai_agent/core/finance/authority.py",
    "src/ultimate_ai_agent/core/finance/service.py",
    "docs/product/finance_fin001_fixture_manifest_v1.json",
    "docs/product/UAA_FINANCE_FIN001_SYNTHETIC_KERNEL.md",
    "scripts/dev/uaa_finance.py",
    "tests/test_fin001_synthetic_kernel.py",
)


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_PATHS:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            failures.append(f"required regular file missing: {relative}")
    try:
        manifest = load_finance_fixture_manifest()
        fixture = load_finance_fixture(
            "fixture-ref:finance/FIN-001:balanced-local-book:v1"
        )
    except Exception as exc:
        failures.append(f"fixture validation failed: {type(exc).__name__}")
        return failures
    if manifest.manifest_ref != EXPECTED_MANIFEST_REF:
        failures.append("fixture manifest digest drifted")
    if len(manifest.fixtures) != 1:
        failures.append("fixture manifest must contain exactly one allowlisted fixture")
    if {entry.flow for entry in fixture.journal_entries} != EXPECTED_FLOWS:
        failures.append("required journal flow coverage drifted")
    if len(fixture.accounts) != 5 or len(fixture.journal_entries) != 6:
        failures.append("canonical fixture inventory drifted")

    expected_binding = (
        "workspace",
        "write",
        "session",
        "ask_before_changes",
        "authority-lane-ref:finance/FIN-001/synthetic-book-mutation",
        "capability-ref:finance/FIN-001/synthetic-book-mutation",
        "authority-adapter-ref:finance/FIN-001/synthetic-book-repository:v1",
        "tool-ref:finance/FIN-001/synthetic-book-mutation:v1",
    )
    if FINANCE_EXACT_AUTHORITY_BINDINGS != (expected_binding,):
        failures.append("exact Finance AuthorityLease binding drifted")
    if FINANCE_EXACT_TARGET_REF != (
        "target-ref:finance/FIN-001:protected-local-repository"
    ):
        failures.append("exact Finance target ref drifted")

    finance = build_finance_synthetic_book_authority_mapping()
    if finance.lane_ref != (
        "authority-lane-ref:finance/FIN-001/synthetic-book-mutation"
    ):
        failures.append("Finance authority lane registration drifted")
    elif finance.route_refs:
        failures.append("FIN-001 must not register an API route")
    manifest_contract = build_finance_mutation_capability_manifest()
    if (
        manifest_contract.provider_runtime_allowed
        or manifest_contract.browser_runtime_allowed
        or manifest_contract.connector_write_allowed
        or manifest_contract.memory_write_allowed
    ):
        failures.append("Finance capability runtime authority broadened")

    cli = (ROOT / "scripts/dev/uaa_finance.py").read_text(encoding="utf-8")
    for command in ("status", "prepare", "run", "inspect", "check", "export"):
        if f'"{command}"' not in cli:
            failures.append(f"CLI command missing: {command}")
    if (
        "--confirmed" not in cli
        or "issue_authority_lease_with_backend_approval" not in cli
    ):
        failures.append("CLI confirmation or backend lease approval gate missing")

    repository = (ROOT / "src/ultimate_ai_agent/core/finance/repository.py").read_text(
        encoding="utf-8"
    )
    for token in (
        "connection.serialize()",
        "FINANCE_STALE_REVISION",
        "FINANCE_IDEMPOTENCY_CONFLICT",
        "FINANCE_PREPERSIST_AUTHORITY_DRIFT",
        "FINANCE_REPOSITORY_CIPHERTEXT_DRIFT",
    ):
        if token not in repository:
            failures.append(f"repository invariant missing: {token}")
    return failures


def main() -> int:
    failures = verify()
    print(
        json.dumps(
            {
                "schema_version": "uaa-finance-fin001-verification.v1",
                "status": "verified" if not failures else "failed",
                "failure_count": len(failures),
                "failures": failures,
                "synthetic_only": True,
                "real_financial_data_allowed": False,
                "api_or_ui_route_added": False,
                "production_authority_granted": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
