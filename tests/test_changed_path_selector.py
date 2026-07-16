from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verification import changed_path_selector as selector
from scripts.verification import verification_selection


def test_selection_is_deterministic_and_deduplicated() -> None:
    first = selector.select_paths(
        ["README.md", "tests/test_api_manifest.py", "README.md"]
    )
    second = selector.select_paths(["tests/test_api_manifest.py", "README.md"])

    assert first == second
    assert first.changed_paths == ("README.md", "tests/test_api_manifest.py")
    assert first.status == "full_gate_required"
    assert first.risk_tier == "tier_3"
    assert first.release_gate_equivalent is False


@pytest.mark.parametrize(
    ("path", "rule_ref", "risk_tier", "status"),
    [
        ("README.md", "risk-rule:inert-documentation", "tier_0", "selected"),
        (
            "src/ultimate_ai_agent/api/app.py",
            "risk-rule:api-authority-boundary",
            "tier_3",
            "full_gate_required",
        ),
        (
            "apps/control-center/src/App.tsx",
            "risk-rule:bounded-frontend-behavior",
            "tier_2",
            "selected",
        ),
        (
            "tests/test_api_manifest.py",
            "risk-rule:python-test-proof",
            "tier_3",
            "full_gate_required",
        ),
        (
            "src/ultimate_ai_agent/core/memory/store.py",
            "risk-rule:persistence-exact",
            "tier_3",
            "full_gate_required",
        ),
        (
            "src/ultimate_ai_agent/core/providers/contracts.py",
            "risk-rule:governed-core-contracts",
            "tier_3",
            "full_gate_required",
        ),
        (
            "src/ultimate_ai_agent/core/extension_catalog/contracts.py",
            "risk-rule:governed-core-contracts",
            "tier_3",
            "full_gate_required",
        ),
    ],
)
def test_known_paths_select_canonical_risk_rule(
    path: str,
    rule_ref: str,
    risk_tier: str,
    status: str,
) -> None:
    selection = selector.select_paths([path])

    assert rule_ref in selection.matched_rule_refs
    assert selection.risk_tier == risk_tier
    assert selection.status == status
    assert not selection.unknown_paths


def test_unknown_path_fails_closed_to_full_local_gate() -> None:
    selection = selector.select_paths(["unclassified/new_surface.xyz"])

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert selection.unknown_paths == ("unclassified/new_surface.xyz",)
    assert selection.status == "full_gate_required"
    assert "reason-ref:risk:unclassified-path" in selection.fallback_reason_refs


def test_critical_topology_change_fails_closed_to_full_local_gate() -> None:
    selection = selector.select_paths(["scripts/verification/api_lane.py"])

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert not selection.unknown_paths
    assert "reason-ref:risk:verification-topology" in (
        selection.fallback_reason_refs
    )


@pytest.mark.parametrize(
    "path",
    ["apps/control-center/package.json", "apps/control-center/package-lock.json"],
)
def test_frontend_dependency_manifest_fails_closed_to_full_gate(path: str) -> None:
    selection = selector.select_paths([path], tier="fast")

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert selection.status == "full_gate_required"
    assert "reason-ref:risk:release-critical" in selection.fallback_reason_refs


@pytest.mark.parametrize("tier", ["fast", "affected"])
def test_verifier_measurement_artifact_is_verification_critical(tier: str) -> None:
    selection = selector.select_paths(
        ["docs/verification/verifier_value_measurements.json"],
        tier=tier,
    )

    assert selection.selected_command_refs == (selector.FULL_COMMAND_REF,)
    assert "risk-rule:verification-ci" in selection.matched_rule_refs
    assert selection.risk_tier == "tier_3"


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
    assert selection.risk_tier == "tier_0"
    assert selection.release_gate_equivalent is False


def test_fast_and_affected_are_compatibility_views_of_one_canonical_selection() -> None:
    fast = selector.select_paths(["apps/control-center/src/App.tsx"], tier="fast")
    affected = selector.select_paths(
        ["apps/control-center/src/App.tsx"], tier="affected"
    )

    assert fast.selected_unit_refs == affected.selected_unit_refs
    assert fast.selected_command_refs == affected.selected_command_refs
    assert fast.selected_test_refs == affected.selected_test_refs
    assert fast.selection_fingerprint == affected.selection_fingerprint


def test_clean_exact_selection_defers_merge_gate_typescript_resource() -> None:
    selection = selector.select_paths(["apps/control-center/src/App.tsx"])

    dirty_commands = selector._command_refs_for_execution(
        selection,
        exact_repository_state=False,
    )
    exact_commands = selector._command_refs_for_execution(
        selection,
        exact_repository_state=True,
    )

    assert "command:frontend.typecheck" in dirty_commands
    assert "command:frontend.typecheck" not in exact_commands
    assert "command:frontend.unit-tests" in exact_commands
    assert "command:frontend.vite-build" not in exact_commands
    assert "command:frontend.safety" in exact_commands


def test_merge_gate_exclusive_commands_are_derived_from_canonical_dag() -> None:
    exclusive = selector._merge_gate_exclusive_command_refs()

    assert "command:frontend.typecheck" in exclusive
    assert "command:frontend.check" in exclusive
    assert "command:pytest.sharded-suite" in exclusive
    assert "command:frontend.unit-tests" not in exclusive


def test_clean_exact_selection_defers_dependents_of_exclusive_resources() -> None:
    selection = selector.select_paths(["apps/control-center/src/App.tsx"])
    deferred = selector._merge_gate_deferred_command_refs(selection)

    assert "command:frontend.typecheck" in deferred
    assert "command:frontend.vite-build" in deferred
    assert "command:frontend.unit-tests" not in deferred
    assert "command:frontend.safety" not in deferred


def test_execution_fails_closed_when_repository_state_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selection = selector.select_paths(["README.md"])
    monkeypatch.setattr(
        selector,
        "_repository_matches_exact_head",
        lambda: None,
    )
    monkeypatch.setattr(
        selector.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail(
            "commands must not start without repository-state proof"
        ),
    )

    assert selector.execute_selection(selection) == 2
    assert (
        "reason-ref:verification:repository-state-unavailable"
        in capsys.readouterr().out
    )


def test_every_selected_command_reference_exists_in_canonical_registry() -> None:
    commands = selector.command_registry()
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
            assert command_ref == selector.FULL_COMMAND_REF or command_ref in commands
        for test_ref in selection.selected_test_refs:
            assert (selector.ROOT / test_ref).is_file()


def test_missing_declared_test_ref_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_ref = "src/ultimate_ai_agent/core/evals/capability_metrics.py"
    monkeypatch.setitem(
        verification_selection.EXACT_SOURCE_TEST_OWNERSHIP,
        source_ref,
        ("tests/test_does_not_exist.py",),
    )

    selection = selector.select_paths([source_ref])

    assert selection.status == "full_gate_required"
    assert "reason-ref:risk:missing-test-ownership" in (
        selection.fallback_reason_refs
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

    assert selection.status == "full_gate_required"
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
    assert "reason-ref:risk:missing-test-ownership" in (
        selection.fallback_reason_refs
    )


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
    assert "reason-ref:risk:force-full" in payload["fallback_reason_refs"]


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
