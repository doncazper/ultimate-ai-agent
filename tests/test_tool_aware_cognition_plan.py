import json
from pathlib import Path

import pytest

from scripts import verify_tool_aware_cognition_plan as verifier


def test_tool_aware_cognition_plan_is_complete_and_queue_gated() -> None:
    result = verifier.verify()

    assert result == {
        "status": "passed",
        "documented_phase_count": 9,
        "normal_chat_fast_path_required": True,
        "direct_chat_quality_non_inferiority_required": True,
        "local_model_preservation_required": True,
        "documented_familiarity_state_count": 8,
        "goat_comparison_gate_documented": True,
        "evaluation_governance_required": True,
        "reversible_rollout_required": True,
        "structured_runtime_authority_added": False,
        "ordered_manifest_item_count": 11,
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


@pytest.mark.parametrize(
    "contradiction",
    (
        "Runtime model calls are now authorized.",
        "This program grants browser authority.",
        "Policy checks may be bypassed.",
        "Automatic skill execution is allowed.",
    ),
)
def test_equivalent_authority_contradictions_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contradiction: str,
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8") + f"\n{contradiction}\n",
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


def test_remaining_queue_manifest_order_and_hashes_are_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["items"][8], payload["items"][9] = (
        payload["items"][9],
        payload["items"][8],
    )
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="immutable sequence is invalid"):
        verifier.verify()


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.update({"extra": "not-allowed"}),
        lambda payload: payload["items"][0].update({"extra": "not-allowed"}),
        lambda payload: payload["items"][0].update({"position": True}),
        lambda payload: payload["items"][0].update({"title": 1}),
    ),
)
def test_remaining_queue_manifest_schema_and_types_are_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    mutation(payload)
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="manifest|sequence|types"):
        verifier.verify()


def test_structured_authority_boundary_cannot_enable_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["authority_boundary"]["runtime_model_or_provider_calls"] = True
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="enables authority"):
        verifier.verify()


def test_pre_goat_insertion_is_bound_to_exact_manifest_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["pre_goat_insertion"]["before_item_id"] = (
        "governed-self-improvement"
    )
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="pre-Goat insertion is invalid"):
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
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_invalid_utf8_error_uses_repository_safe_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corrupt = tmp_path / "operator-name" / "plan.md"
    corrupt.parent.mkdir()
    corrupt.write_bytes(b"\xff")
    monkeypatch.setattr(verifier, "PLAN", corrupt)

    with pytest.raises(RuntimeError) as raised:
        verifier.verify()

    assert str(tmp_path) not in str(raised.value)
    assert "required-ref:outside-repository" in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_remaining_queue_title_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["items"][0]["title"] = "A different title"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="immutable sequence is invalid"):
        verifier.verify()
