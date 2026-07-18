#!/usr/bin/env python3
"""Verify Queue 01 item 08 without enabling browser authentication or sessions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 06 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    keychain = _read(
        "src/ultimate_ai_agent/core/governed_browser/browser_keychain.py",
        failures,
    )
    sessions = _read(
        "src/ultimate_ai_agent/core/governed_browser/origin_sessions.py",
        failures,
    )
    static_safety = _read(
        "src/ultimate_ai_agent/core/governed_browser/static_safety.py",
        failures,
    )
    helper = _read(
        "tools/macos/governed-browser-keychain-helper/"
        "Sources/UAAGovernedBrowserKeychainHelper/main.swift",
        failures,
    )
    helper_readme = _read(
        "tools/macos/governed-browser-keychain-helper/README.md",
        failures,
    )
    installer = _read(
        "scripts/dev/install_governed_browser_keychain_helper.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = "\n".join(
        (
            _read("tests/test_governed_browser_queue01_group06.py", failures),
            _read(
                "tests/test_governed_browser_queue01_group06_review_repairs.py",
                failures,
            ),
            _read("tests/test_governed_browser_keychain_adapter.py", failures),
        )
    )
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "keychain": (
            "MacOSGovernedBrowserKeychainAdapter",
            "GovernedBrowserCredentialRegistration",
            "GovernedBrowserKeychainOperationReceipt",
            "governed_browser_keychain_item_ref",
            "expected_helper_sha256",
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_INPUT_BYTES",
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES",
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_FINGERPRINT_MISMATCH",
            "GOVERNED_BROWSER_KEYCHAIN_ITEM_ALREADY_EXISTS",
            "credential_material_returned: Literal[False]",
            "browser_session_started: Literal[False]",
            "authentication_performed: Literal[False]",
            "network_call_performed: Literal[False]",
            "external_mutation_performed: Literal[False]",
            "execution_authority_granted: Literal[False]",
            "shell=False",
            "start_new_session=True",
        ),
        "sessions": (
            "GovernedBrowserOriginSessionRecipeRegistry",
            "GovernedBrowserOriginSessionStore",
            "ExactGovernedBrowserOriginSessionService",
            "GovernedExternalActionKernel",
            "prepared_inactive",
            "MAX_GOVERNED_BROWSER_SESSION_LIFETIME",
            "exact_authority_lease_required: Literal[True]",
            "approval_revalidation_required: Literal[True]",
            "budget_reservation_required: Literal[True]",
            "readiness_revalidation_required: Literal[True]",
            "human_presence_required: Literal[True]",
            "operation_authority_ref",
            "per_origin_isolation_required: Literal[True]",
            "browser_session_start_allowed: Literal[False]",
            "authentication_allowed: Literal[False]",
            "cookies_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "external_mutation_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
        ),
        "static_safety": (
            "is_exact_governed_browser_keychain_subprocess_site",
            "_ADAPTER_SOURCE_SHA256",
            "_UNRELATED_FORBIDDEN_MARKERS",
            "_REQUIRED_MARKERS",
        ),
        "helper": (
            "import Security",
            "kSecClassGenericPassword",
            "kSecAttrAccessibleWhenUnlockedThisDeviceOnly",
            "kSecAttrSynchronizable",
            "credentialMaterialReturned = false",
            "browserSessionStarted = false",
            "authenticationPerformed = false",
            "networkCallPerformed = false",
            "externalMutationPerformed = false",
            "executionAuthorityGranted = false",
            "HELPER_CREDENTIAL_ALREADY_EXISTS",
        ),
        "helper_readme": (
            "opaque",
            "does not start a browser",
            "authenticate a site",
        ),
        "installer": (
            "DEFAULT_INSTALL_ROOT",
            "helper_fingerprint_ref",
            "credential_material_included",
            "browser_session_authority_granted",
            "network_authority_granted",
            "external_mutation_authority_granted",
        ),
        "package": (
            "MacOSGovernedBrowserKeychainAdapter",
            "GovernedBrowserOriginSessionStore",
            "ExactGovernedBrowserOriginSessionService",
            "build_governed_browser_credential_registration",
            "build_governed_browser_origin_session_recipe",
        ),
        "tests": (
            "test_real_adapter_is_hash_pinned_bounded_and_never_returns_material",
            "test_adapter_rejects_tamper_symlink_invalid_response_and_immutable_buffer",
            "test_exact_per_origin_lifecycle_is_governed_content_free_and_inactive",
            "test_lifecycle_replay_is_at_most_once_and_suppresses_projection",
            "test_revoked_session_cannot_be_reopened_or_closed",
            "test_unknown_recipe_and_approval_identifier_alone_never_reach_keychain",
            "test_lifecycle_revalidation_denies_before_keychain",
            "test_scope_drift_external_target_and_helper_failure_fail_closed",
            "test_revoke_state_conflict_after_keychain_delete_is_ambiguous_and_no_retry",
            "test_lifecycle_approval_scope_binds_exactly_one_operation",
            "test_expired_prepare_is_blocked_before_keychain_or_state_write",
            "test_service_rejects_immutable_credential_buffer_without_masking_result",
            "test_missing_credential_probe_is_failed_not_ambiguous_and_not_retried",
            "test_native_helper_rejects_duplicate_stores",
            "test_non_mutating_keychain_preconditions_are_not_ambiguous",
            "test_expired_revalidation_persists_expiry_but_reports_failure",
            "test_installer_metadata_is_content_free_exact_and_rejects_unmanaged_pair",
        ),
        "doc": (
            "08. Real macOS Keychain opaque-handle adapter",
            "`implemented_inactive`",
            "per-origin session",
            "no browser session",
            "Queue 02",
        ),
    }
    values = {
        "keychain": keychain,
        "sessions": sessions,
        "static_safety": static_safety,
        "helper": helper,
        "helper_readme": helper_readme,
        "installer": installer,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 06 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–08", docs_index, "documentation index"),
        ("Queue 01 items 01–08", board, "current board"),
        ("Queue 01 items 01–08", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 06 {label} marker missing: {marker}")

    runtime_text = "\n".join((keychain, sessions, package)).lower()
    for fragment in (
        "import requests",
        "import httpx",
        "import playwright",
        "import selenium",
        "import browserbase",
        "import firecrawl",
        "path.home(",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 06 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 06 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 06 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 06 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [8],
                "classification": "implemented_inactive",
                "keychain_adapter": "real_macos_hash_pinned_helper",
                "credential_handle_mode": "opaque_exact_origin",
                "per_origin_session_lifecycle": "prepared_inactive_only",
                "browser_session_enabled": False,
                "authentication_enabled": False,
                "cookies_enabled": False,
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
