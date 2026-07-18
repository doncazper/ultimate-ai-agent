#!/usr/bin/env python3
"""Verify Queue 01 item 10 stays artifact-bound and externally inactive."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 08 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    transfers = _read(
        "src/ultimate_ai_agent/core/governed_browser/artifact_transfers.py",
        failures,
    )
    transaction = _read(
        "src/ultimate_ai_agent/core/governed_browser/transaction.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = _read(
        "tests/test_governed_browser_queue01_group08.py",
        failures,
    )
    tests += _read(
        "tests/test_governed_browser_queue01_group08_hardening.py",
        failures,
    )
    tests += _read(
        "tests/test_governed_browser_queue01_group08_review_repairs.py",
        failures,
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_readme = _read("docs/README.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "transfers": (
            "GovernedArtifactQuarantineStore",
            "GovernedArtifactTransferRecipeRegistry",
            "ExactGovernedArtifactTransferService",
            "GovernedExternalActionKernel",
            "MAX_GOVERNED_ARTIFACT_BYTES",
            "idempotency-ref:governed-artifact-transfer",
            "download_transaction_ref",
            "GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH",
            "GOVERNED_ARTIFACT_QUARANTINE_RESULT_SCOPE_MISMATCH",
            "GOVERNED_ARTIFACT_UPLOAD_PLAN_RESULT_SCOPE_MISMATCH",
            "AuthorityCapability.download",
            "AuthorityCapability.upload",
            "app_owned_quarantine_required: Literal[True]",
            "content_fingerprint_required_for_upload: Literal[True]",
            "quarantine_before_upload_required: Literal[True]",
            "live_download_allowed: Literal[False]",
            "live_upload_allowed: Literal[False]",
            "upload_body_materialization_allowed: Literal[False]",
            "browser_session_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "raw_path_recorded: Literal[False]",
            "raw_artifact_recorded: Literal[False]",
            "upload_performed: Literal[False]",
            "network_call_performed: Literal[False]",
            "os.O_EXCL",
            "O_NOFOLLOW",
        ),
        "transaction": (
            "def replay_if_terminal",
            "GOVERNED_EXTERNAL_ACTION_IDEMPOTENCY_CONFLICT",
            "len(lease.domains) == 1",
        ),
        "package": (
            "ExactGovernedArtifactTransferService",
            "GovernedArtifactQuarantineStore",
            "build_governed_artifact_transfer_recipe",
            "governed_artifact_transfer_schema_ref",
        ),
        "tests": (
            "test_bounded_download_is_quarantined_only_and_receipts_are_content_free",
            "test_download_replay_is_at_most_once_content_free_and_zeroizes_input",
            "test_upload_is_an_exact_fingerprinted_plan_from_quarantine_only",
            "test_upload_fails_closed_without_exact_quarantined_fingerprint",
            "test_unknown_recipe_and_operation_mismatch_are_truthfully_blocked",
            "test_approval_identifier_alone_and_broader_lease_grant_nothing",
            "test_shared_gates_block_before_quarantine_write",
            "test_invalid_download_payloads_fail_without_materialization",
            "test_raw_upload_payload_is_denied_and_zeroized_before_transaction",
            "test_exact_scope_real_targets_and_receipt_forgery_fail_closed",
            "test_quarantine_store_rejects_symlinks_substitution_and_unsafe_modes",
            "test_immutable_download_payload_is_rejected_before_transaction",
            "test_group08_verifier_passes_and_contains_no_raw_material",
        ),
        "doc": (
            "10. Download quarantine and exact artifact-bound upload plans",
            "`implemented_inactive`",
            "app-owned quarantine",
            "content fingerprint",
            "does not download",
            "does not upload",
            "Queue 02",
        ),
    }
    values = {
        "transfers": transfers,
        "transaction": transaction,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 08 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–10", docs_readme, "documentation README"),
        ("Queue 01 items 01–10", docs_index, "documentation index"),
        ("Queue 01 items 01–10", board, "current board"),
        ("Queue 01 items 01–10", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 08 {label} marker missing: {marker}")

    runtime_text = "\n".join((transfers, transaction, package)).lower()
    for fragment in (
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "from urllib import request",
        "import urllib3",
        "from urllib3 import",
        "import http.client",
        "from http import client",
        "import playwright",
        "from playwright import",
        "import selenium",
        "from selenium import",
        "import browserbase",
        "from browserbase import",
        "import firecrawl",
        "from firecrawl import",
        "import subprocess",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 08 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 08 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 08 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 08 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [10],
                "classification": "implemented_inactive",
                "app_owned_quarantine_enabled": True,
                "live_download_enabled": False,
                "upload_plan_enabled": True,
                "live_upload_enabled": False,
                "upload_body_materialization_enabled": False,
                "browser_session_enabled": False,
                "live_network_enabled": False,
                "real_external_targets_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
