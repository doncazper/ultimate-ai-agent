from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_msg_mx_005_matrix_session.py"


def _load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location(
        "verify_msg_mx_005_matrix_session", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_matrix_adapter_node_contract_suite_passes() -> None:
    result = subprocess.run(
        ["npm", "--prefix", "integrations/matrix-client-adapter", "test"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, "Matrix adapter contract suite failed"


def test_msg_mx_005_verifier_passes_current_repository() -> None:
    verifier = _load_verifier()
    assert verifier.verify() == []


def test_msg_mx_005_verifier_runs_as_a_direct_repo_command() -> None:
    environment = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "scripts/verify_msg_mx_005_matrix_session.py"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, "direct MSG-MX-005 verifier failed"


def test_verifier_rejects_credential_bearing_native_helper_source() -> None:
    verifier = _load_verifier()
    failures = verifier._helper_failures(
        'operation == "version"\n'
        'let marker = "MATRIX_KEYCHAIN_CALLER_AUTH_REQUIRED"\n'
        "let credentialMaterialIncluded = false\n"
        "let executionAuthorityGranted = false\n"
        "import Security\n"
        "let leak = SecItemCopyMatching\n"
    )
    assert any("blocked credential behavior" in failure for failure in failures)


def test_lock_inventory_fails_closed_without_integrity_or_reviewed_license() -> None:
    verifier = _load_verifier()
    assert (
        verifier._lock_inventory(
            {
                "packages": {
                    "node_modules/example": {
                        "version": "1.0.0",
                        "license": "UNKNOWN",
                    }
                }
            }
        )
        == set()
    )
