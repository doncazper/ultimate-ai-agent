from __future__ import annotations

from types import SimpleNamespace

from scripts import verify_uaa_p1_087_1_local_launcher_boot_readiness as p1_087_1


def test_p1_087_1_verifier_passes_current_repo() -> None:
    assert p1_087_1.verify() == []


def test_p1_087_1_verifier_flags_missing_dual_surface_boot_contract() -> None:
    fake_launcher = SimpleNamespace(
        render_macos_launcher=lambda: "./scripts/dev/uaa start\n./scripts/dev/uaa ui\n",
        parse_args=lambda argv: SimpleNamespace(
            command=argv[0],
            target="openwebui" if argv[0] == "launch-ui" else None,
        ),
        service_config=lambda root, name: SimpleNamespace(name=name),
        status_for_service=lambda service: f"{service.name}: not running",
    )
    source = "def command_start(root): pass\n"

    failures = p1_087_1.verify(
        fake_launcher,
        launcher_source=source,
        check_docs=False,
    )

    assert any("macOS launcher missing './scripts/dev/uaa trial-boot'" in item for item in failures)
    assert any("first-party Control Center" in item for item in failures)
    assert any("launcher source missing 'def command_trial_boot'" in item for item in failures)
    assert any("openwebui status missing safe log ref" in item for item in failures)
