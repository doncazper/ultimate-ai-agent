from pathlib import Path

import pytest

from scripts import verify_tool_aware_cognition_plan as verifier


def test_tool_aware_cognition_plan_is_complete_and_queue_gated() -> None:
    result = verifier.verify()

    assert result == {
        "status": "passed",
        "phase_count": 9,
        "normal_chat_fast_path": True,
        "direct_chat_quality_non_inferiority": True,
        "local_model_preserved": True,
        "familiarity_states": 8,
        "goat_comparison_gate": True,
        "evaluation_governance": True,
        "reversible_rollout": True,
        "runtime_authority_added": False,
    }


@pytest.mark.parametrize(
    "fragment",
    (
        "`familiar_supported`",
        "`familiar_input_required`",
        "`familiar_unavailable`",
        "`familiar_requires_approval`",
        "`familiar_authority_blocked`",
        "`ambiguous`",
        "`novel_unsupported`",
        "`outcome_uncertain`",
    ),
)
def test_familiarity_contract_is_explicit(fragment: str) -> None:
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert fragment in text


def test_missing_queue_gate_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text("Queue entry without a Goat acceptance gate.", encoding="utf-8")
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="queue insertion is missing"):
        verifier.verify()


def test_self_authorizing_language_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        + "\nThis plan authorizes runtime model calls.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


def test_missing_structured_authority_denial_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "- connector writes;",
            "- connector mutations are outside this document;",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan authority boundary is missing"):
        verifier.verify()


def test_missing_production_authority_denial_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "- public release, production authority, or claims of human-like\n"
            "  self-awareness.",
            "- future distribution remains a separate decision.",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan authority boundary is missing"):
        verifier.verify()


def test_missing_phase_heading_fails_even_when_phase_token_remains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "### TAW-00 — Convergence ledger and evaluation baseline",
            "### Convergence ledger and evaluation baseline",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan phase headings is missing"):
        verifier.verify()


def test_fixed_one_pr_per_phase_policy_cannot_be_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "PR count follows contract and risk seams rather than a fixed",
            "Every phase always uses one separate pull request because a fixed",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_reordered_queue_gate_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text(
        verifier.QUEUE.read_text(encoding="utf-8")
        .replace(
            "3. At that pre-Goat boundary, execute TAW-00 through TAW-08",
            "4. At that pre-Goat boundary, execute TAW-00 through TAW-08",
        )
        .replace(
            "4. Run the final GoatCitadel comparison only after",
            "3. Run the final GoatCitadel comparison only after",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="ordered queue insertion is missing"):
        verifier.verify()


def test_missing_file_error_uses_repository_safe_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "operator-name" / "missing.md"
    monkeypatch.setattr(verifier, "PLAN", missing)

    with pytest.raises(RuntimeError) as raised:
        verifier.verify()

    assert str(tmp_path) not in str(raised.value)
    assert "required-ref:outside-repository" in str(raised.value)
