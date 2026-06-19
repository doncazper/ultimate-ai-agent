import subprocess
import sys

import scripts.verify_all as verify_all


def test_version_truth_checker_self_test():
    result = subprocess.run(
        [sys.executable, "scripts/release/check_version_truth.py", "--self-test"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "self-test passed" in result.stdout


def test_bump_version_self_test():
    result = subprocess.run(
        [sys.executable, "scripts/release/bump_version.py", "--self-test"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "self-test passed" in result.stdout


def test_current_version_truth_passes():
    result = subprocess.run(
        [sys.executable, "scripts/release/check_version_truth.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "VERSION, package metadata, current docs, and release packets agree" in result.stdout


def test_static_verifier_compares_reset_semver_numerically():
    assert verify_all._version_tuple("v0.100.0") > verify_all._version_tuple("v0.40.0")
