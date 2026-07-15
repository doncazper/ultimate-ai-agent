from __future__ import annotations

from scripts.verification import run_all_legacy
from scripts.verification import static_scan_policy


def test_mobile_sensor_guard_does_not_flag_verifier_literals() -> None:
    run_all_legacy.verify_no_mobile_native_or_sensor_implementation()
    assert run_all_legacy._is_exact_portable_evidence_keychain_helper_file(
        "tools/macos/portable-evidence-keychain-helper/Package.swift"
    )
    assert run_all_legacy._is_exact_matrix_session_keychain_helper_file(
        "tools/macos/matrix-session-keychain-helper/Package.swift"
    )
    assert not run_all_legacy._is_exact_portable_evidence_keychain_helper_file(
        "apps/mobile/Package.swift"
    )


def test_frontend_guard_does_not_misclassify_exact_desktop_helper() -> None:
    run_all_legacy.verify_m13_web_control_center_frontend_safety()


def test_openwebui_guard_does_not_flag_foundation_gate_policy_literals() -> None:
    run_all_legacy.verify_no_openwebui_runtime_or_config_implementation()


def test_control_center_guard_allows_safe_blocker_and_billing_reason_refs() -> None:
    run_all_legacy.verify_no_control_center_runtime_or_frontend_expansion()


def test_shell_guard_accepts_only_the_exact_sealed_backend_subprocess_profile() -> None:
    rel = "src/ultimate_ai_agent/core/sandbox_calculation/backend.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    run_all_legacy.verify_no_shell_execution_in_runtime()
    assert run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
        rel_path=rel,
        source=source,
        stripped_line="process: subprocess.Popen[bytes],",
    )
    assert not run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
        rel_path=rel,
        source=source + "\nsubprocess.call(['unsafe'])\n",
        stripped_line="subprocess.call(['unsafe'])",
    )


def test_shell_guard_accepts_only_exact_matrix_harness_subprocess_profile() -> None:
    rel = "src/ultimate_ai_agent/core/communications/matrix_harness/backend.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    assert run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
        rel_path=rel,
        source=source,
        stripped_line="process = subprocess.Popen(",
    )
    for drift in (
        "\nos.system('unsafe')\n",
        "\nsubprocess.call(['unsafe'])\n",
        "\nimport requests\n",
        "\nimport httpx\n",
    ):
        assert not run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
            rel_path=rel,
            source=source + drift,
            stripped_line="subprocess.Popen(",
        )


def test_shell_guard_accepts_only_exact_portable_evidence_helper_profile() -> None:
    rel = "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    assert run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
        rel_path=rel,
        source=source,
        stripped_line="stdout=subprocess.PIPE,",
    )
    for drift in (
        "\nos.system('unsafe')\n",
        "\nsubprocess.call(['unsafe'])\n",
        "\nimport requests\n",
        "\nimport httpx\n",
    ):
        assert not run_all_legacy._is_exact_governed_runtime_command_shell_scan_line(
            rel_path=rel,
            source=source + drift,
            stripped_line="subprocess.run(",
        )


def test_filesystem_guard_accepts_only_fixed_portable_evidence_helper_root() -> None:
    rel = "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    run_all_legacy.verify_no_broad_filesystem_scanning()
    assert run_all_legacy.is_exact_portable_evidence_helper_home_path(
        rel_path=rel,
        source=source,
        fragment="Path.home(",
    )
    assert not run_all_legacy.is_exact_portable_evidence_helper_home_path(
        rel_path=rel,
        source=source + '\nPath.home().rglob("*")\n',
        fragment="Path.home(",
    )


def test_filesystem_guard_accepts_only_bounded_matrix_session_runtime_roots() -> None:
    rel = "src/ultimate_ai_agent/core/communications/matrix_session/backend.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    for fragment in ("Path.home(", '.rglob("*")'):
        assert run_all_legacy.is_exact_matrix_session_bounded_filesystem_site(
            rel_path=rel,
            source=source,
            fragment=fragment,
        )
        assert not run_all_legacy.is_exact_matrix_session_bounded_filesystem_site(
            rel_path=rel,
            source=source + '\nPath.home().rglob("*")\n',
            fragment=fragment,
        )


def test_static_scan_allowlist_is_dependency_free_and_does_not_hide_web_adapters(
    monkeypatch,
) -> None:
    original_import = __import__

    def reject_package_import(name, *args, **kwargs):
        if name.startswith("ultimate_ai_agent"):
            raise AssertionError(
                "static allowlist must not import application dependencies"
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", reject_package_import)

    assert run_all_legacy._is_static_gate_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/criteria.py", set()
    )
    assert not run_all_legacy._is_static_gate_scan_allowed_file(
        "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py", set()
    )


def test_web_hybrid_static_scan_policy_keeps_exceptions_fragment_scoped() -> None:
    for rel in static_scan_policy.WEB_HYBRID_EXACT_ADAPTER_FILES:
        source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")
        assert not static_scan_policy.is_unapproved_static_fragment(
            rel=rel,
            fragment="network_call_performed=True",
            source=source,
        )
        assert static_scan_policy.is_unapproved_static_fragment(
            rel=rel,
            fragment="memory_write_performed=True",
            source=source + "\nmemory_write_performed=True\n",
        )


def test_web_hybrid_static_scan_policy_rejects_unreviewed_socket_call() -> None:
    rel = "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py"
    source = (run_all_legacy.ROOT / rel).read_text(encoding="utf-8")

    assert static_scan_policy.is_unapproved_static_fragment(
        rel=rel,
        fragment="socket.",
        source=source + "\ndef unreviewed_transport():\n    socket.socket()\n",
    )
