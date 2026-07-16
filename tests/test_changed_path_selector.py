from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verification import changed_path_selector as selector


def test_selection_is_deterministic_and_deduplicated() -> None:
    first = selector.select_paths(
        ["README.md", "tests/test_api_manifest.py", "README.md"]
    )
    second = selector.select_paths(["tests/test_api_manifest.py", "README.md"])

    assert first == second
    assert first.changed_paths == ("README.md", "tests/test_api_manifest.py")
    assert first.status == "selected"
    assert first.tier == "affected"
    assert first.release_gate_equivalent is False


@pytest.mark.parametrize(
    ("path", "rule_ref"),
    [
        ("README.md", "rule-ref:documentation-product-truth"),
        ("src/ultimate_ai_agent/api/app.py", "rule-ref:api-openapi-routes"),
        ("apps/control-center/src/App.tsx", "rule-ref:control-center-frontend"),
        ("tests/test_api_manifest.py", "rule-ref:direct-test"),
        ("src/ultimate_ai_agent/core/memory/store.py", "rule-ref:memory-context"),
        ("src/ultimate_ai_agent/core/providers/contracts.py", "rule-ref:providers"),
        (
            "src/ultimate_ai_agent/core/extension_catalog/contracts.py",
            "rule-ref:extensions",
        ),
    ],
)
def test_known_paths_select_expected_rule(path: str, rule_ref: str) -> None:
    selection = selector.select_paths([path])

    assert rule_ref in selection.matched_rule_refs
    assert selection.status == "selected"
    assert not selection.unknown_paths


def test_unknown_path_fails_closed_to_full_local_gate() -> None:
    selection = selector.select_paths(["unclassified/new_surface.xyz"])

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert selection.unknown_paths == ("unclassified/new_surface.xyz",)
    assert selection.status == "full_gate_required"
    assert selection.fallback_reason_refs == ("reason-ref:verification:unknown-path",)


def test_critical_topology_change_fails_closed_to_full_local_gate() -> None:
    selection = selector.select_paths(["scripts/verification/api_lane.py"])

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert not selection.unknown_paths
    assert selection.fallback_reason_refs == (
        "reason-ref:verification:critical-topology-change",
    )


@pytest.mark.parametrize(
    "path",
    ["apps/control-center/package.json", "apps/control-center/package-lock.json"],
)
def test_frontend_dependency_manifest_fails_closed_to_full_gate(path: str) -> None:
    selection = selector.select_paths([path], tier="fast")

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert selection.status == "full_gate_required"
    assert selection.fallback_reason_refs == (
        "reason-ref:verification:critical-topology-change",
    )


@pytest.mark.parametrize("tier", ["fast", "affected"])
def test_verifier_measurement_artifact_selects_value_audit(tier: str) -> None:
    selection = selector.select_paths(
        ["docs/verification/verifier_value_measurements.json"],
        tier=tier,
    )

    assert selection.selected_command_refs == ("command-ref:verifier-value-audit",)
    assert selection.matched_rule_refs == ("rule-ref:verifier-value-measurement",)


@pytest.mark.parametrize(
    "path",
    ["", "./README.md", "../README.md", "/tmp/README.md", "bad\\path.py"],
)
def test_invalid_paths_are_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="VERIFICATION_CHANGED_PATH_INVALID"):
        selector.normalize_path(path)


def test_no_changes_is_explicit_and_safe() -> None:
    selection = selector.select_paths([])

    assert selection.status == "no_changes"
    assert selection.selected_command_refs == ()
    assert selection.release_gate_equivalent is False


def test_fast_tier_is_narrower_but_affected_tier_keeps_full_boundary_checks() -> None:
    fast = selector.select_paths(["apps/control-center/src/App.tsx"], tier="fast")
    affected = selector.select_paths(
        ["apps/control-center/src/App.tsx"], tier="affected"
    )

    assert fast.selected_command_refs == ("command-ref:frontend-safety",)
    assert "command-ref:frontend-check" in affected.selected_command_refs
    assert affected.release_gate_equivalent is False


def test_every_selected_rule_reference_exists() -> None:
    examples = [
        "README.md",
        "src/ultimate_ai_agent/api/app.py",
        "apps/control-center/src/App.tsx",
        "src/ultimate_ai_agent/core/authority/contracts.py",
        "src/ultimate_ai_agent/core/memory/store.py",
        "src/ultimate_ai_agent/core/providers/contracts.py",
        "src/ultimate_ai_agent/core/extension_catalog/contracts.py",
        "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
        "packaging/README.md",
        "tests/test_api_manifest.py",
    ]
    for path in examples:
        selection = selector.select_paths([path])
        assert selection.status in {"selected", "full_gate_required"}
        assert selection.selected_command_refs
        for command_ref in selection.selected_command_refs:
            assert (
                command_ref == "command-ref:ruff-changed"
                or command_ref in selector.COMMANDS
            )
        for test_ref in selection.selected_test_refs:
            assert (selector.ROOT / test_ref).is_file()


def test_missing_declared_test_ref_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        selector,
        "_rule_for_path",
        lambda _path, _tier, **_kwargs: (
            "rule-ref:broken",
            ("command-ref:ruff-changed",),
            ("tests/test_does_not_exist.py",),
        ),
    )

    selection = selector.select_paths(["README.md"])

    assert selection.status == "full_gate_required"
    assert selection.fallback_reason_refs == (
        "reason-ref:verification:missing-test-ref",
    )


def test_python_module_ownership_uses_the_exact_supplied_repository_root(
    tmp_path: Path,
) -> None:
    source_ref = "src/ultimate_ai_agent/core/example.py"
    test_ref = "tests/test_example.py"
    (tmp_path / source_ref).parent.mkdir(parents=True)
    (tmp_path / source_ref).write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / test_ref).parent.mkdir(parents=True)
    (tmp_path / test_ref).write_text("def test_value(): pass\n", encoding="utf-8")

    selection = selector.select_paths([source_ref], repo=tmp_path)

    assert selection.status == "selected"
    assert selection.selected_test_refs == (test_ref,)


def test_python_module_ownership_rejects_a_symlinked_test_ref(
    tmp_path: Path,
) -> None:
    source_ref = "src/ultimate_ai_agent/core/example.py"
    test_ref = "tests/test_example.py"
    (tmp_path / source_ref).parent.mkdir(parents=True)
    (tmp_path / source_ref).write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "outside.py").write_text("def test_value(): pass\n", encoding="utf-8")
    (tmp_path / test_ref).parent.mkdir(parents=True)
    (tmp_path / test_ref).symlink_to(tmp_path / "outside.py")

    selection = selector.select_paths([source_ref], repo=tmp_path)

    assert selection.status == "full_gate_required"
    assert selection.selected_test_refs == ()


def test_explicit_paths_are_unioned_with_git_and_cannot_hide_unknown(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        selector,
        "_git_paths",
        lambda _base_ref: (["unclassified/unsafe.xyz"], False),
    )

    assert selector.main(["--path", "README.md", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "full_gate_required"
    assert payload["changed_paths"] == ["README.md", "unclassified/unsafe.xyz"]


def test_name_status_parser_keeps_both_rename_paths_and_flags_deletes() -> None:
    paths, destructive = selector._parse_name_status(
        b"M\x00README.md\x00R100\x00old.py\x00new.py\x00D\x00gone.py\x00"
    )

    assert paths == {"README.md", "old.py", "new.py", "gone.py"}
    assert destructive is True


def test_rename_or_delete_forces_full_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(selector, "_git_paths", lambda _base_ref: (["README.md"], True))

    assert selector.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "full_gate_required"
    assert payload["fallback_reason_refs"] == ["reason-ref:verification:rename-delete"]


def test_json_execute_combination_is_rejected() -> None:
    with pytest.raises(SystemExit):
        selector.main(["--json", "--execute"])


def test_make_targets_do_not_interpolate_untrusted_selector_values() -> None:
    makefile = (Path(__file__).resolve().parents[1] / "Makefile").read_text(
        encoding="utf-8"
    )

    assert "VERIFY_PATHS" not in makefile
    assert "VERIFY_BASE_REF" not in makefile
    assert "VERIFY_PATH_ARGS" not in makefile
